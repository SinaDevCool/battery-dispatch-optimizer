import pandas as pd
import pytest

from backend.features.forecast_quality_features import build_forecast_quality_features
from backend.features.market_features import build_daily_market_features
from backend.features.negative_price_features import build_negative_price_features
from backend.features.renewable_features import (
    add_renewable_pressure_labels,
    build_renewable_forecast_features,
)


def test_forecast_quality_features_valid_forecast():
    df = pd.DataFrame(
        {
            "timestamp": [
                "2026-01-01 00:00:00",
                "2026-01-01 01:00:00",
                "2026-01-01 02:00:00",
            ],
            "forecast_price": [40, -5, 100],
        }
    )

    result = build_forecast_quality_features(df)

    assert result["status"] == "ok"
    assert result["row_count"] == 3
    assert result["negative_price_hours"] == 1
    assert result["min_price"] == -5.0
    assert result["max_price"] == 100.0


def test_forecast_quality_features_missing_column():
    df = pd.DataFrame(
        {
            "timestamp": ["2026-01-01 00:00:00"],
        }
    )

    result = build_forecast_quality_features(df)

    assert result["status"] == "invalid"
    assert "forecast_price" in result["missing_columns"]


def test_daily_market_features():
    df = pd.DataFrame(
        {
            "date": ["2026-01-01", "2026-01-01", "2026-01-01"],
            "timestamp": [
                "2026-01-01 00:00:00",
                "2026-01-01 01:00:00",
                "2026-01-01 02:00:00",
            ],
            "price": [40, -5, 100],
        }
    )

    result = build_daily_market_features(df)

    assert len(result) == 1
    assert result.loc[0, "negative_price_hours"] == 1
    assert result.loc[0, "low_price_hours"] == 1
    assert result.loc[0, "high_price_hours"] == 1
    assert result.loc[0, "cheapest_hour"] == 1
    assert result.loc[0, "most_expensive_hour"] == 2


def test_negative_price_features():
    df = pd.DataFrame(
        {
            "timestamp": [
                "2026-01-01 00:00:00",
                "2026-01-01 01:00:00",
                "2026-01-01 02:00:00",
                "2026-01-01 05:00:00",
            ],
            "price": [-2, -5, 20, -1],
        }
    )

    result = build_negative_price_features(df)

    assert result["negative_price_hours"] == 3
    assert result["min_negative_price"] == -5.0
    assert result["longest_negative_event_hours"] == 2


def test_renewable_forecast_features():
    df = pd.DataFrame(
        {
            "solar_forecast": [10, 20, 30],
            "wind_forecast": [5, 10, 15],
        }
    )

    result = build_renewable_forecast_features(df)

    assert result["status"] == "ok"
    assert result["avg_renewables_forecast"] == 30.0
    assert result["max_renewables_forecast"] == 45.0


def test_renewable_pressure_labels():
    df = pd.DataFrame(
        {
            "solar_forecast": [10, 20, 30, 40],
            "wind_forecast": [10, 20, 30, 40],
        }
    )

    result = add_renewable_pressure_labels(df)

    assert "renewable_pressure" in result.columns
    assert set(result["renewable_pressure"]).issubset(
        {"low", "normal", "high", "unknown"}
    )


