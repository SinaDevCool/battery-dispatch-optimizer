import pandas as pd

from backend.markets.market_profile_loader import get_default_market_profile


def build_forecast_quality_features(
    forecast_df,
    price_column="forecast_price",
    market_profile=None,
):
    if market_profile is None:
        market_profile = get_default_market_profile()

    expected_intervals = int(market_profile.get("expected_intervals_per_day", 24))
    market_time_unit_minutes = int(market_profile.get("market_time_unit_minutes", 60))

    required_columns = ["timestamp", price_column]

    missing_columns = [
        column for column in required_columns
        if column not in forecast_df.columns
    ]

    if missing_columns:
        return {
            "status": "invalid",
            "missing_columns": missing_columns,
            "row_count": len(forecast_df),
            "valid_row_count": 0,
            "expected_intervals_per_day": expected_intervals,
            "market_time_unit_minutes": market_time_unit_minutes,
        }

    df = forecast_df.copy()

    df["timestamp"] = pd.to_datetime(
        df["timestamp"],
        errors="coerce",
    )

    df[price_column] = pd.to_numeric(
        df[price_column],
        errors="coerce",
    )

    invalid_timestamps = int(df["timestamp"].isna().sum())
    missing_prices = int(df[price_column].isna().sum())
    duplicate_timestamps = int(df["timestamp"].duplicated().sum())

    valid_df = df.dropna(subset=["timestamp", price_column])
    valid_df = valid_df.sort_values("timestamp")

    if valid_df.empty:
        return {
            "status": "invalid",
            "missing_columns": [],
            "row_count": len(df),
            "valid_row_count": 0,
            "invalid_timestamps": invalid_timestamps,
            "missing_prices": missing_prices,
            "duplicate_timestamps": duplicate_timestamps,
            "expected_intervals_per_day": expected_intervals,
            "market_time_unit_minutes": market_time_unit_minutes,
        }

    price_series = valid_df[price_column]

    return {
        "status": "ok",
        "missing_columns": [],
        "row_count": int(len(df)),
        "valid_row_count": int(len(valid_df)),
        "expected_intervals_per_day": expected_intervals,
        "market_time_unit_minutes": market_time_unit_minutes,
        "is_full_market_day": int(len(valid_df)) == expected_intervals,
        "interval_gap_count": _count_interval_gaps(
            valid_df["timestamp"],
            market_time_unit_minutes,
        ),
        "first_timestamp": str(valid_df["timestamp"].iloc[0]),
        "last_timestamp": str(valid_df["timestamp"].iloc[-1]),
        "invalid_timestamps": invalid_timestamps,
        "missing_prices": missing_prices,
        "duplicate_timestamps": duplicate_timestamps,
        "min_price": round(float(price_series.min()), 2),
        "max_price": round(float(price_series.max()), 2),
        "average_price": round(float(price_series.mean()), 2),
        "median_price": round(float(price_series.median()), 2),
        "price_std": round(float(price_series.std()), 2),
        "price_spread": round(float(price_series.max() - price_series.min()), 2),
        "negative_price_hours": int((price_series < 0).sum()),
        "high_price_hours": int((price_series >= 80).sum()),
        "low_price_hours": int((price_series <= 20).sum()),
    }


def _count_interval_gaps(timestamp_series, market_time_unit_minutes):
    if len(timestamp_series) < 2:
        return 0

    expected_delta = pd.Timedelta(minutes=market_time_unit_minutes)
    deltas = timestamp_series.sort_values().diff().dropna()

    return int((deltas != expected_delta).sum())



