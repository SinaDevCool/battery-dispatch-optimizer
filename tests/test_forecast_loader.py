from pathlib import Path

import pandas as pd
import pytest

from src.forecasts.forecast_loader import (
    forecast_dataframe_to_price_data,
    load_forecast_dataframe,
    load_forecast_price_data,
    normalize_forecast_dataframe,
)


def test_normalize_forecast_dataframe_with_forecast_price():
    df = pd.DataFrame(
        {
            "timestamp": [
                "2026-01-01 02:00:00",
                "2026-01-01 01:00:00",
                "bad timestamp",
            ],
            "forecast_price": [100, 50, 10],
        }
    )

    normalized_df, price_column = normalize_forecast_dataframe(df)

    assert price_column == "forecast_price"
    assert len(normalized_df) == 2
    assert normalized_df.iloc[0]["forecast_price"] == 50


def test_normalize_forecast_dataframe_falls_back_to_price_column():
    df = pd.DataFrame(
        {
            "timestamp": ["2026-01-01 00:00:00"],
            "price": [42],
        }
    )

    normalized_df, price_column = normalize_forecast_dataframe(df)

    assert price_column == "price"
    assert normalized_df.iloc[0]["price"] == 42


def test_forecast_dataframe_to_price_data():
    df = pd.DataFrame(
        {
            "timestamp": ["2026-01-01 00:00:00"],
            "forecast_price": [42],
        }
    )

    price_data = forecast_dataframe_to_price_data(df)

    assert price_data == [
        {
            "timestamp": "2026-01-01 00:00:00",
            "price": 42.0,
        }
    ]


def test_load_forecast_dataframe(tmp_path):
    forecast_file = tmp_path / "forecast.csv"

    pd.DataFrame(
        {
            "timestamp": ["2026-01-01 00:00:00"],
            "forecast_price": [42],
        }
    ).to_csv(forecast_file, index=False)

    df = load_forecast_dataframe(forecast_file)

    assert len(df) == 1
    assert "forecast_price" in df.columns


def test_load_forecast_price_data_missing_file():
    with pytest.raises(FileNotFoundError):
        load_forecast_price_data(Path("missing_forecast_file.csv"))