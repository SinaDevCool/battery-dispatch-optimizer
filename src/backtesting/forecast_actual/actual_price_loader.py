from pathlib import Path

import pandas as pd

from src.backtesting.forecast_actual.timestamps import normalize_market_timestamps
from src.config.paths import ACTUAL_PRICE_FILE


def load_actual_price_dataframe(
    actual_file=ACTUAL_PRICE_FILE,
    price_column="actual_price",
):
    actual_file = Path(actual_file)

    if not actual_file.exists():
        raise FileNotFoundError(f"Actual price file not found: {actual_file}")

    df = pd.read_csv(actual_file)

    if "timestamp" not in df.columns:
        raise ValueError("Actual price file must contain a timestamp column.")

    if price_column not in df.columns:
        if "price" in df.columns:
            price_column = "price"
        elif "actual_price_eur_per_mwh" in df.columns:
            price_column = "actual_price_eur_per_mwh"
        else:
            raise ValueError(
                "Actual price file must contain actual_price, "
                "actual_price_eur_per_mwh, or price column."
            )

    df = df.copy()
    df["timestamp"] = normalize_market_timestamps(df["timestamp"])
    df[price_column] = pd.to_numeric(df[price_column], errors="coerce")
    df = df.dropna(subset=["timestamp", price_column])
    df = df.drop_duplicates(subset=["timestamp"])
    df = df.sort_values("timestamp").reset_index(drop=True)
    df = df.rename(columns={price_column: "actual_price"})

    return df[["timestamp", "actual_price"]]
