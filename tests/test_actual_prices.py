import pandas as pd

from src.backtesting.forecast_actual.actual_price_loader import (
    load_actual_price_dataframe,
)


def test_load_actual_price_dataframe_with_actual_price_column(tmp_path):
    actual_file = tmp_path / "actual_prices.csv"
    pd.DataFrame(
        [
            {
                "timestamp": "2026-01-01 00:00:00",
                "actual_price": 50.0,
            },
            {
                "timestamp": "2026-01-01 01:00:00",
                "actual_price": 40.0,
            },
        ]
    ).to_csv(actual_file, index=False)

    df = load_actual_price_dataframe(actual_file=actual_file)

    assert list(df.columns) == ["timestamp", "actual_price"]
    assert len(df) == 2
    assert df["actual_price"].tolist() == [50.0, 40.0]


def test_load_actual_price_dataframe_accepts_price_alias(tmp_path):
    actual_file = tmp_path / "actual_prices.csv"
    pd.DataFrame(
        [
            {
                "timestamp": "2026-01-01 00:00:00",
                "price": 55.0,
            },
        ]
    ).to_csv(actual_file, index=False)

    df = load_actual_price_dataframe(actual_file=actual_file)

    assert list(df.columns) == ["timestamp", "actual_price"]
    assert df.iloc[0]["actual_price"] == 55.0
