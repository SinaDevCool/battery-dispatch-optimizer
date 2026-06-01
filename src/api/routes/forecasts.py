import json
from pathlib import Path

import pandas as pd
from fastapi import APIRouter

from src.api.common import validate_forecast_dataframe
from src.api.schemas import BatterySignalRequest
from src.config.client_config import load_client_config
from src.config.paths import (
    FORECAST_FILE,
    LATEST_SIGNAL_FILE,
    SCENARIO_RESULTS_FILE,
)
from src.features.forecast_quality_features import build_forecast_quality_features
from src.features.negative_price_features import build_negative_price_features
from src.forecasts.entsoe_forecast_provider import (
    EntsoeForecastError,
    build_next_day_entsoe_forecast,
)
from src.forecasts.forecast_comparison import compare_forecast_profitability
from src.forecasts.forecast_loader import load_forecast_price_data
from src.forecasts.forecast_registry import get_forecast_files
from src.forecasts.inhouse_forecast_provider import build_next_day_inhouse_forecast
from src.scenarios.scenario_runner import run_scenarios
from src.signals.signal_engine import generate_battery_signal


router = APIRouter()


@router.post("/data/update-entsoe")
def update_entsoe_data():
    forecast_file = FORECAST_FILE
    forecast_file.parent.mkdir(parents=True, exist_ok=True)

    try:
        df = build_next_day_entsoe_forecast()

    except ValueError as error:
        return {
            "status": "missing_token",
            "message": str(error),
        }

    except EntsoeForecastError as error:
        if forecast_file.exists():
            return {
                "status": "fallback",
                "message": (
                    f"{error} Existing local forecast file was kept, "
                    "so the dashboard can continue in local CSV mode."
                ),
                "forecast_file": str(forecast_file),
            }

        return {
            "status": "not_found",
            "message": str(error),
        }

    except Exception as error:
        return {
            "status": "error",
            "message": f"Could not update ENTSO-E forecast: {error}",
        }

    if df is None or df.empty:
        return {
            "status": "not_found",
            "message": "No ENTSO-E forecast data returned.",
        }

    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    df["forecast_price"] = pd.to_numeric(
        df["forecast_price"],
        errors="coerce",
    )

    df = df.dropna(subset=["timestamp", "forecast_price"])
    df = df.drop_duplicates(subset=["timestamp"])
    df = df.sort_values("timestamp")

    if df.empty:
        return {
            "status": "invalid",
            "message": "ENTSO-E forecast was returned, but no valid timestamp and price rows were available.",
        }

    df.to_csv(forecast_file, index=False)

    target_date = str(df["timestamp"].dt.date.iloc[0])

    return {
        "status": "ok",
        "message": "ENTSO-E forecast data updated successfully.",
        "target_date": target_date,
        "forecast_file": str(forecast_file),
        "rows": len(df),
        "columns": df.columns.tolist(),
        "forecast_provider": "entsoe",
        "forecast_model": "entsoe_day_ahead",
    }


@router.post("/forecast/upload")
def upload_forecast(request: BatterySignalRequest):
    forecast_file = FORECAST_FILE
    forecast_file.parent.mkdir(parents=True, exist_ok=True)

    rows = []

    for item in request.price_data:
        rows.append(
            {
                "timestamp": item.timestamp,
                "forecast_price": item.price,
            }
        )

    df = pd.DataFrame(rows)
    is_valid, validation_message = validate_forecast_dataframe(df)

    if not is_valid:
        return {
            "status": "invalid",
            "message": validation_message,
            "forecast_file": str(forecast_file),
            "rows": len(df),
        }

    df.to_csv(forecast_file, index=False)

    try:
        client_config = load_client_config()
    except FileNotFoundError as error:
        return {
            "status": "ok",
            "message": "Forecast uploaded successfully, but signal was not generated because client config is missing.",
            "forecast_file": str(forecast_file),
            "rows": len(df),
            "signal": None,
            "error": str(error),
        }

    price_data = load_forecast_price_data(forecast_file)

    signal_result = generate_battery_signal(
        price_data=price_data,
        battery_config=client_config["battery_config"],
        strategy_config=client_config["strategy_config"],
    )

    signal_file = LATEST_SIGNAL_FILE
    signal_file.parent.mkdir(parents=True, exist_ok=True)

    with open(signal_file, "w", encoding="utf-8") as file:
        json.dump(signal_result, file, indent=2)

    scenario_results = run_scenarios(price_data)

    scenario_file = SCENARIO_RESULTS_FILE
    scenario_file.parent.mkdir(parents=True, exist_ok=True)

    with open(scenario_file, "w", encoding="utf-8") as file:
        json.dump(scenario_results, file, indent=2)

    return {
        "status": "ok",
        "message": "Forecast uploaded, battery signal generated, and scenarios completed successfully.",
        "forecast_file": str(forecast_file),
        "signal_file": str(signal_file),
        "scenario_file": str(scenario_file),
        "rows": len(df),
        "signal": signal_result,
        "scenarios": scenario_results,
    }


@router.get("/forecast/status")
def forecast_status():
    forecast_file = FORECAST_FILE

    if not forecast_file.exists():
        return {
            "status": "not_found",
            "message": f"Forecast file not found: {forecast_file}",
        }

    df = pd.read_csv(forecast_file)
    features = build_forecast_quality_features(df)

    if features["status"] != "ok":
        return {
            "status": features["status"],
            "message": "Forecast quality check failed.",
            "forecast_file": str(forecast_file),
            **features,
        }

    return {
        "status": "ok",
        "forecast_file": str(forecast_file),
        **features,
    }


@router.get("/forecast/preview")
def forecast_preview():
    forecast_file = FORECAST_FILE

    if not forecast_file.exists():
        return {
            "status": "not_found",
            "message": f"Forecast file not found: {forecast_file}",
        }

    df = pd.read_csv(forecast_file)

    if df.empty:
        return {
            "status": "empty",
            "message": "Forecast file exists but is empty.",
            "forecast_file": str(forecast_file),
        }

    preview_rows = df.head(24).copy()

    return {
        "status": "ok",
        "forecast_file": str(forecast_file),
        "rows": len(df),
        "columns": df.columns.tolist(),
        "preview": preview_rows.to_dict(orient="records"),
    }


@router.post("/forecasts/compare-profitability")
def run_forecast_profitability_comparison():
    output_file = Path("data/outputs/forecast_profitability_comparison.json")
    output_file.parent.mkdir(parents=True, exist_ok=True)

    forecast_files = get_forecast_files()

    results = compare_forecast_profitability(forecast_files)

    with open(output_file, "w", encoding="utf-8") as file:
        json.dump(results, file, indent=2)

    return {
        "status": "ok",
        "message": "Forecast profitability comparison completed successfully.",
        "comparison_file": str(output_file),
        "forecast_sources": list(forecast_files.keys()),
        "results": results,
    }


@router.get("/forecasts/compare-profitability/latest")
def latest_forecast_profitability_comparison():
    comparison_file = Path("data/outputs/forecast_profitability_comparison.json")

    if not comparison_file.exists():
        return {
            "status": "not_found",
            "message": "No forecast profitability comparison found. Run /forecasts/compare-profitability first.",
            "results": [],
        }

    with open(comparison_file, "r", encoding="utf-8") as file:
        results = json.load(file)

    return {
        "status": "ok",
        "comparison_file": str(comparison_file),
        "results": results,
    }


@router.get("/features/forecast")
def forecast_features():
    forecast_file = FORECAST_FILE

    if not forecast_file.exists():
        return {
            "status": "not_found",
            "message": f"Forecast file not found: {forecast_file}",
        }

    df = pd.read_csv(forecast_file)

    quality_features = build_forecast_quality_features(
        df,
        price_column="forecast_price",
    )

    negative_features = build_negative_price_features(
        df,
        price_column="forecast_price",
    )

    return {
        "status": "ok",
        "forecast_file": str(forecast_file),
        "quality_features": quality_features,
        "negative_price_features": negative_features,
    }


@router.post("/forecast/demo")
def create_demo_forecast():
    forecast_file = FORECAST_FILE
    forecast_file.parent.mkdir(parents=True, exist_ok=True)

    start_time = pd.Timestamp.now().normalize() + pd.Timedelta(days=1)

    prices = [
        42, 38, 30, 22, 15, 8,
        12, 28, 55, 72, 85, 92,
        88, 75, 60, 48, 52, 70,
        96, 120, 110, 82, 58, 45,
    ]

    rows = []

    for hour, price in enumerate(prices):
        rows.append(
            {
                "timestamp": start_time + pd.Timedelta(hours=hour),
                "forecast_price": price,
                "forecast_provider": "demo",
                "forecast_model": "demo_base",
            }
        )

    df = pd.DataFrame(rows)
    df.to_csv(forecast_file, index=False)

    return {
        "status": "ok",
        "message": "Demo forecast created successfully.",
        "forecast_file": str(forecast_file),
        "rows": len(df),
        "forecast_provider": "demo",
        "forecast_model": "demo_base",
    }


@router.post("/forecast/demo-high-spread")
def create_demo_high_spread_forecast():
    forecast_file = Path("data/processed/demo_high_spread_forecast.csv")
    forecast_file.parent.mkdir(parents=True, exist_ok=True)

    start_time = pd.Timestamp.now().normalize() + pd.Timedelta(days=1)

    prices = [
        55, 48, 40, 28, 12, -5,
        -8, 20, 58, 85, 110, 125,
        118, 95, 72, 55, 62, 88,
        130, 155, 145, 100, 75, 60,
    ]

    rows = []

    for hour, price in enumerate(prices):
        rows.append(
            {
                "timestamp": start_time + pd.Timedelta(hours=hour),
                "forecast_price": price,
                "forecast_provider": "demo_high_spread",
                "forecast_model": "demo_high_spread",
            }
        )

    df = pd.DataFrame(rows)
    df.to_csv(forecast_file, index=False)

    return {
        "status": "ok",
        "message": "Demo high-spread forecast created successfully.",
        "forecast_file": str(forecast_file),
        "rows": len(df),
        "forecast_provider": "demo_high_spread",
        "forecast_model": "demo_high_spread",
    }


@router.post("/forecast/inhouse-placeholder")
def create_inhouse_placeholder_forecast():
    forecast_file = Path("data/processed/inhouse_placeholder_forecast.csv")
    forecast_file.parent.mkdir(parents=True, exist_ok=True)

    df = build_next_day_inhouse_forecast()
    df.to_csv(forecast_file, index=False)

    return {
        "status": "ok",
        "message": "In-house placeholder forecast created successfully.",
        "forecast_file": str(forecast_file),
        "rows": len(df),
        "forecast_provider": "inhouse_placeholder",
        "forecast_model": "inhouse_placeholder_v0",
    }
