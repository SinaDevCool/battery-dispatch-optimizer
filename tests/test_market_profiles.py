import pandas as pd

from backend.features.forecast_quality_features import build_forecast_quality_features
from backend.markets.market_profile_loader import get_default_market_profile


def test_default_market_profile_is_germany_day_ahead():
    profile = get_default_market_profile()

    assert profile["market_profile_id"] == "de_lu_day_ahead"
    assert profile["bidding_zone"] == "DE_LU"
    assert profile["market_time_unit_minutes"] == 15
    assert profile["expected_intervals_per_day"] == 96


def test_forecast_quality_uses_germany_15_minute_expectations():
    start = pd.Timestamp("2026-01-01 00:00:00")

    forecast_df = pd.DataFrame(
        {
            "timestamp": [
                start + pd.Timedelta(minutes=15 * index)
                for index in range(96)
            ],
            "forecast_price": [50.0] * 96,
        }
    )

    features = build_forecast_quality_features(forecast_df)

    assert features["status"] == "ok"
    assert features["expected_intervals_per_day"] == 96
    assert features["market_time_unit_minutes"] == 15
    assert features["is_full_market_day"] is True
    assert features["interval_gap_count"] == 0



