from datetime import datetime, timezone

import pandas as pd

from src.forecasts.entsoe_forecast_provider import (
    DEFAULT_COUNTRY_CODE,
    EntsoeForecastError,
    get_entsoe_client,
    save_series_or_df,
)
from src.markets.market_profile_loader import get_default_market_profile


class ActualPriceDataError(RuntimeError):
    pass


def build_entsoe_actual_day_ahead_prices(
    target_date=None,
    country_code=DEFAULT_COUNTRY_CODE,
):
    client = get_entsoe_client()
    market_profile = get_default_market_profile()
    market_time_unit_minutes = int(market_profile["market_time_unit_minutes"])
    resample_frequency = f"{market_time_unit_minutes}min"

    if target_date is None:
        start = pd.Timestamp.now(tz="Europe/Brussels").normalize() - pd.Timedelta(days=1)
    else:
        start = pd.Timestamp(target_date, tz="Europe/Brussels").normalize()

    end = start + pd.Timedelta(days=1)

    try:
        data = client.query_day_ahead_prices(
            country_code,
            start=start,
            end=end,
        )
    except Exception as error:
        raise ActualPriceDataError(
            f"Could not retrieve ENTSO-E actual day-ahead prices: {error}"
        ) from error

    actual_df = save_series_or_df(data, "actual_price")

    if actual_df is None or actual_df.empty:
        raise ActualPriceDataError(
            "No ENTSO-E actual day-ahead price data was retrieved. "
            "The API may be unreachable, the token may be invalid, "
            "or prices may not be available for the requested delivery day."
        )

    actual_df = actual_df.sort_values("timestamp").reset_index(drop=True)
    actual_df = (
        actual_df
        .set_index("timestamp")
        .resample(resample_frequency)
        .mean(numeric_only=True)
        .reset_index()
    )

    actual_df["actual_price"] = pd.to_numeric(
        actual_df["actual_price"],
        errors="coerce",
    )
    actual_df = actual_df.dropna(subset=["timestamp", "actual_price"])
    actual_df = actual_df.drop_duplicates(subset=["timestamp"])
    actual_df = actual_df.sort_values("timestamp").reset_index(drop=True)

    if actual_df.empty:
        raise ActualPriceDataError(
            "ENTSO-E actual price data contains no valid timestamp and price rows."
        )

    actual_df["hour"] = actual_df["timestamp"].dt.hour
    actual_df["date"] = actual_df["timestamp"].dt.date.astype(str)
    actual_df["actual_provider"] = "entsoe"
    actual_df["actual_market"] = "day_ahead"
    actual_df["market_profile_id"] = market_profile["market_profile_id"]
    actual_df["market_time_unit_minutes"] = market_time_unit_minutes
    actual_df["created_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")

    required_columns = [
        "timestamp",
        "actual_price",
        "hour",
        "date",
        "actual_provider",
        "actual_market",
        "market_profile_id",
        "market_time_unit_minutes",
        "created_at",
    ]

    for column in required_columns:
        if column not in actual_df.columns:
            actual_df[column] = None

    return actual_df[required_columns]
