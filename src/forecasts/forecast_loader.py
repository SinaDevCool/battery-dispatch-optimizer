from pathlib import Path

import pandas as pd


def load_next_day_forecast(
    forecast_file=Path("data/processed/latest_price_forecast.csv"),
    price_column="forecast_price",
):
    if not forecast_file.exists():
        raise FileNotFoundError(
            f"Forecast file not found: {forecast_file}. "
            "Create this CSV first with timestamp and forecast_price columns."
        )

    df = pd.read_csv(forecast_file)

    if "timestamp" not in df.columns:
        raise ValueError("Forecast file must contain a timestamp column.")

    if price_column not in df.columns:
        if "price" in df.columns:
            price_column = "price"
        else:
            raise ValueError(
                f"Forecast file must contain {price_column} or price column."
            )

    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    df[price_column] = pd.to_numeric(df[price_column], errors="coerce")

    df = df.dropna(subset=["timestamp", price_column])
    df = df.sort_values("timestamp")

    price_data = []

    for _, row in df.iterrows():
        price_data.append(
            {
                "timestamp": str(row["timestamp"]),
                "price": float(row[price_column]),
            }
        )

    return price_data