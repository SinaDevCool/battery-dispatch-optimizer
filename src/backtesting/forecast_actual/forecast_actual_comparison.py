import math

import pandas as pd

from src.backtesting.forecast_actual.timestamps import normalize_market_timestamps


def compare_forecast_to_actual(forecast_df, actual_df):
    forecast = forecast_df.copy()
    actual = actual_df.copy()

    forecast["timestamp"] = normalize_market_timestamps(forecast["timestamp"])
    actual["timestamp"] = normalize_market_timestamps(actual["timestamp"])

    forecast["forecast_price"] = pd.to_numeric(
        forecast["forecast_price"],
        errors="coerce",
    )
    actual["actual_price"] = pd.to_numeric(
        actual["actual_price"],
        errors="coerce",
    )

    merged = forecast[["timestamp", "forecast_price"]].merge(
        actual[["timestamp", "actual_price"]],
        on="timestamp",
        how="inner",
    )

    if merged.empty:
        return {
            "status": "no_overlap",
            "message": "Forecast and actual price files have no overlapping timestamps.",
            "metrics": empty_metrics(),
            "rows": [],
        }

    merged["error_eur_per_mwh"] = (
        merged["forecast_price"] - merged["actual_price"]
    )
    merged["absolute_error_eur_per_mwh"] = merged["error_eur_per_mwh"].abs()
    merged["squared_error"] = merged["error_eur_per_mwh"] ** 2

    mae = float(merged["absolute_error_eur_per_mwh"].mean())
    rmse = math.sqrt(float(merged["squared_error"].mean()))
    bias = float(merged["error_eur_per_mwh"].mean())

    return {
        "status": "ok",
        "metrics": {
            "row_count": int(len(merged)),
            "mae_eur_per_mwh": round(mae, 4),
            "rmse_eur_per_mwh": round(rmse, 4),
            "bias_eur_per_mwh": round(bias, 4),
            "max_absolute_error_eur_per_mwh": round(
                float(merged["absolute_error_eur_per_mwh"].max()),
                4,
            ),
            "min_forecast_price": round(float(merged["forecast_price"].min()), 4),
            "max_forecast_price": round(float(merged["forecast_price"].max()), 4),
            "min_actual_price": round(float(merged["actual_price"].min()), 4),
            "max_actual_price": round(float(merged["actual_price"].max()), 4),
        },
        "rows": records_to_json_safe(merged),
    }


def empty_metrics():
    return {
        "row_count": 0,
        "mae_eur_per_mwh": None,
        "rmse_eur_per_mwh": None,
        "bias_eur_per_mwh": None,
        "max_absolute_error_eur_per_mwh": None,
        "min_forecast_price": None,
        "max_forecast_price": None,
        "min_actual_price": None,
        "max_actual_price": None,
    }


def records_to_json_safe(df):
    records = []

    for row in df.to_dict("records"):
        cleaned_row = {}

        for key, value in row.items():
            if key == "squared_error":
                continue

            if key == "timestamp":
                cleaned_row[key] = str(value)
            elif hasattr(value, "item"):
                cleaned_row[key] = value.item()
            else:
                cleaned_row[key] = value

        records.append(cleaned_row)

    return records
