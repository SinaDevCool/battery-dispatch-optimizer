from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from src.config.paths import FORECAST_FILE
from src.forecasts.entsoe_forecast_provider import (
    EntsoeForecastError,
    build_next_day_entsoe_forecast,
)


@dataclass
class ForecastLoadResult:
    dataframe: pd.DataFrame
    source: str
    model: str
    target_date: str
    warning: str | None = None


def normalize_forecast_dataframe(forecast_df):
    df = forecast_df.copy()

    if "timestamp" not in df.columns:
        raise ValueError("Forecast must contain a timestamp column.")

    if "forecast_price" not in df.columns:
        raise ValueError("Forecast must contain a forecast_price column.")

    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    df["forecast_price"] = pd.to_numeric(
        df["forecast_price"],
        errors="coerce",
    )

    df = df.dropna(subset=["timestamp", "forecast_price"])
    df = df.drop_duplicates(subset=["timestamp"])
    df = df.sort_values("timestamp")
    df = df.reset_index(drop=True)

    if df.empty:
        raise ValueError("Forecast contains no valid timestamp and price rows.")

    return df


def save_forecast_dataframe(forecast_df, forecast_file=FORECAST_FILE):
    forecast_file = Path(forecast_file)
    forecast_file.parent.mkdir(parents=True, exist_ok=True)

    df = normalize_forecast_dataframe(forecast_df)
    df.to_csv(forecast_file, index=False)

    return df


def load_local_forecast_dataframe(forecast_file=FORECAST_FILE):
    forecast_file = Path(forecast_file)

    if not forecast_file.exists():
        raise FileNotFoundError(f"Forecast file not found: {forecast_file}")

    forecast_df = pd.read_csv(forecast_file)

    return normalize_forecast_dataframe(forecast_df)


def load_next_day_forecast_with_fallback(forecast_file=FORECAST_FILE):
    try:
        forecast_df = build_next_day_entsoe_forecast()
        forecast_df = save_forecast_dataframe(forecast_df, forecast_file)
        target_date = str(forecast_df["timestamp"].dt.date.iloc[0])

        return ForecastLoadResult(
            dataframe=forecast_df,
            source="entsoe",
            model="entsoe_day_ahead",
            target_date=target_date,
            warning=None,
        )

    except EntsoeForecastError as error:
        forecast_file = Path(forecast_file)

        if not forecast_file.exists():
            raise

        forecast_df = load_local_forecast_dataframe(forecast_file)
        target_date = str(forecast_df["timestamp"].dt.date.iloc[0])

        return ForecastLoadResult(
            dataframe=forecast_df,
            source="local_saved_forecast",
            model="local_saved_forecast",
            target_date=target_date,
            warning=f"{error} Existing local forecast file was used instead.",
        )
