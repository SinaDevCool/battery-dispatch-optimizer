import os
from datetime import datetime, timezone

import pandas as pd
import requests
from entsoe import EntsoePandasClient

from backend.markets.market_profile_loader import get_default_market_profile


DEFAULT_COUNTRY_CODE = "DE_LU"


class EntsoeForecastError(RuntimeError):
    pass


def get_entsoe_client():
    token = os.environ.get("ENTSOE_API_KEY") or os.environ.get("ENTSOE_TOKEN")

    if not token:
        raise ValueError(
            "Missing ENTSO-E API token. Set ENTSOE_API_KEY in your environment."
        )

    session = build_entsoe_requests_session()

    return EntsoePandasClient(api_key=token, session=session)


def build_entsoe_requests_session():
    session = requests.Session()
    verify_ssl = os.environ.get("ENTSOE_VERIFY_SSL", "true").lower()
    ca_bundle = (
        os.environ.get("ENTSOE_CA_BUNDLE")
        or os.environ.get("REQUESTS_CA_BUNDLE")
        or os.environ.get("SSL_CERT_FILE")
    )

    if ca_bundle:
        session.verify = ca_bundle
    elif verify_ssl in ["0", "false", "no", "off"]:
        session.verify = False

        try:
            import urllib3

            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        except Exception:
            pass

    return session


def save_series_or_df(data, value_name):
    if data is None:
        return None

    if isinstance(data, pd.Series):
        df = data.to_frame(name=value_name)
    else:
        df = data.copy()

    df = df.reset_index()

    if df.empty:
        return None

    first_col = df.columns[0]
    df = df.rename(columns={first_col: "timestamp"})

    value_cols = [
        column for column in df.columns
        if column != "timestamp"
    ]

    if not value_cols:
        return None

    df = df[["timestamp", value_cols[0]]].rename(
        columns={value_cols[0]: value_name}
    )

    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    df[value_name] = pd.to_numeric(df[value_name], errors="coerce")

    df = df.dropna(subset=["timestamp"])
    df = df.drop_duplicates(subset=["timestamp"])
    df = df.sort_values("timestamp")

    return df


def safe_query(value_name, query_func, *args, **kwargs):
    try:
        data = query_func(*args, **kwargs)
        return save_series_or_df(data, value_name)
    except Exception:
        return None


def merge_forecast_column(base_df, source_df):
    if source_df is None or source_df.empty:
        return base_df

    if base_df is None:
        return source_df

    return base_df.merge(source_df, on="timestamp", how="outer")


def build_next_day_entsoe_forecast(country_code=DEFAULT_COUNTRY_CODE):
    client = get_entsoe_client()
    market_profile = get_default_market_profile()
    market_time_unit_minutes = int(market_profile["market_time_unit_minutes"])
    resample_frequency = f"{market_time_unit_minutes}min"

    today = pd.Timestamp.now(tz="Europe/Brussels").normalize()
    start = today + pd.Timedelta(days=1)
    end = today + pd.Timedelta(days=2)

    day_ahead_prices = safe_query(
        "forecast_price",
        client.query_day_ahead_prices,
        country_code,
        start=start,
        end=end,
    )

    if day_ahead_prices is None or day_ahead_prices.empty:
        raise EntsoeForecastError(
            "No ENTSO-E day-ahead price data was retrieved. "
            "The API may be unreachable, the token may be invalid, "
            "or prices may not be available for the requested window."
        )

    forecast_df = day_ahead_prices.copy()

    optional_sources = [
        safe_query(
            "load_forecast",
            client.query_load_forecast,
            country_code,
            start=start,
            end=end,
        ),
        safe_query(
            "generation_forecast",
            client.query_generation_forecast,
            country_code,
            start=start,
            end=end,
        ),
        safe_query(
            "forecast_solar",
            client.query_wind_and_solar_forecast,
            country_code,
            start=start,
            end=end,
            psr_type="B16",
        ),
        safe_query(
            "wind_onshore_forecast",
            client.query_wind_and_solar_forecast,
            country_code,
            start=start,
            end=end,
            psr_type="B19",
        ),
        safe_query(
            "wind_offshore_forecast",
            client.query_wind_and_solar_forecast,
            country_code,
            start=start,
            end=end,
            psr_type="B18",
        ),
    ]

    for source_df in optional_sources:
        forecast_df = merge_forecast_column(forecast_df, source_df)

    forecast_df = forecast_df.sort_values("timestamp").reset_index(drop=True)

    forecast_df = (
        forecast_df
        .set_index("timestamp")
        .resample(resample_frequency)
        .mean(numeric_only=True)
        .reset_index()
    )

    forecast_df["forecast_price"] = pd.to_numeric(
        forecast_df["forecast_price"],
        errors="coerce",
    )

    forecast_df = forecast_df.dropna(subset=["timestamp", "forecast_price"])

    if forecast_df.empty:
        raise EntsoeForecastError(
            "ENTSO-E forecast contains no valid timestamp and price rows."
        )

    if "forecast_solar" not in forecast_df.columns:
        forecast_df["forecast_solar"] = 0.0

    wind_columns = [
        column for column in ["wind_onshore_forecast", "wind_offshore_forecast"]
        if column in forecast_df.columns
    ]

    if wind_columns:
        forecast_df["forecast_wind"] = forecast_df[wind_columns].fillna(0).sum(axis=1)
    else:
        forecast_df["forecast_wind"] = 0.0

    forecast_df["forecast_renewables_total"] = (
        forecast_df["forecast_solar"].fillna(0)
        + forecast_df["forecast_wind"].fillna(0)
    )

    forecast_df["hour"] = forecast_df["timestamp"].dt.hour
    forecast_df["date"] = forecast_df["timestamp"].dt.date.astype(str)
    forecast_df["forecast_provider"] = "entsoe"
    forecast_df["forecast_model"] = "entsoe_day_ahead"
    forecast_df["market_profile_id"] = market_profile["market_profile_id"]
    forecast_df["market_time_unit_minutes"] = market_time_unit_minutes
    forecast_df["created_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")

    required_columns = [
        "timestamp",
        "forecast_price",
        "load_forecast",
        "generation_forecast",
        "forecast_solar",
        "forecast_wind",
        "forecast_renewables_total",
        "hour",
        "date",
        "forecast_provider",
        "forecast_model",
        "market_profile_id",
        "market_time_unit_minutes",
        "created_at",
    ]

    for column in required_columns:
        if column not in forecast_df.columns:
            forecast_df[column] = None

    return forecast_df[required_columns]



