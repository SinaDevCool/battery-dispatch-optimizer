import pandas as pd


def merge_market_and_renewables(
    spot_df,
    solar_df=None,
    wind_df=None,
    online_solar_df=None,
    online_wind_onshore_df=None,
    online_wind_offshore_df=None,
):
    market_df = spot_df.copy()

    dataframes_to_merge = [
        solar_df,
        wind_df,
        online_solar_df,
        online_wind_onshore_df,
        online_wind_offshore_df,
    ]

    for df_part in dataframes_to_merge:
        if df_part is not None and not df_part.empty:
            market_df = market_df.merge(df_part, on="timestamp", how="left")

    if "online_wind_onshore" in market_df.columns and "online_wind_offshore" in market_df.columns:
        market_df["online_wind_total"] = market_df[
            ["online_wind_onshore", "online_wind_offshore"]
        ].sum(axis=1, min_count=1)

    if "solar_forecast" in market_df.columns and "wind_forecast" in market_df.columns:
        market_df["renewables_forecast_total"] = market_df[
            ["solar_forecast", "wind_forecast"]
        ].sum(axis=1, min_count=1)

    if "online_solar" in market_df.columns and "online_wind_total" in market_df.columns:
        market_df["online_renewables_total"] = market_df[
            ["online_solar", "online_wind_total"]
        ].sum(axis=1, min_count=1)

    market_df = market_df.sort_values("timestamp").reset_index(drop=True)

    return market_df


def calculate_price_renewables_correlation(market_df):
    correlation_cols = [
        "price",
        "solar_forecast",
        "wind_forecast",
        "online_solar",
        "online_wind_onshore",
        "online_wind_offshore",
        "renewables_forecast_total",
        "online_renewables_total",
    ]

    available_cols = [col for col in correlation_cols if col in market_df.columns]

    correlation_input = market_df[available_cols].copy()

    for col in available_cols:
        correlation_input[col] = pd.to_numeric(correlation_input[col], errors="coerce")

    correlation_input = correlation_input.dropna(subset=["price"])

    return correlation_input.corr()


def build_renewable_risk_buckets(market_df, bucket_count=10):
    required_cols = [
        "price",
        "is_negative_price",
        "renewables_forecast_total",
    ]

    for col in required_cols:
        if col not in market_df.columns:
            raise ValueError(f"Missing required column: {col}")

    clean_df = market_df.dropna(
        subset=["price", "renewables_forecast_total"]
    ).copy()

    clean_df["renewables_bucket"] = pd.qcut(
        clean_df["renewables_forecast_total"],
        q=bucket_count,
        duplicates="drop",
    )

    risk_by_bucket = (
        clean_df
        .groupby("renewables_bucket", observed=False)
        .agg(
            hours=("price", "count"),
            negative_price_hours=("is_negative_price", "sum"),
            avg_price=("price", "mean"),
            avg_renewables=("renewables_forecast_total", "mean"),
        )
        .reset_index()
    )

    risk_by_bucket["negative_price_risk_percent"] = (
        risk_by_bucket["negative_price_hours"] / risk_by_bucket["hours"] * 100
    )

    return risk_by_bucket.round(2)