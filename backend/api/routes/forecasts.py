from pathlib import Path

import pandas as pd
from fastapi import APIRouter

from backend.api.common import file_status, validate_forecast_dataframe
from backend.api.schemas import (
    ActualPriceStatusResponse,
    ApiResponse,
    BatterySignalRequest,
    ForecastPreviewResponse,
    ForecastProfitabilityResponse,
    ForecastStatusResponse,
)
from backend.assets.asset_loader import get_asset
from backend.config.client_config import load_client_config
from backend.config.paths import (
    ACTUAL_PRICE_FILE,
    FORECAST_FILE,
    LATEST_SIGNAL_FILE,
    SCENARIO_RESULTS_FILE,
)
from backend.features.forecast_quality_features import build_forecast_quality_features
from backend.features.negative_price_features import build_negative_price_features
from backend.forecasts.entsoe_forecast_provider import (
    EntsoeForecastError,
    build_next_day_entsoe_forecast,
)
from backend.forecasts.forecast_comparison import compare_forecast_profitability
from backend.forecasts.forecast_loader import load_forecast_price_data
from backend.forecasts.forecast_registry import get_forecast_files
from backend.forecasts.inhouse_forecast_provider import build_next_day_inhouse_forecast
from backend.markets.actual_price_provider import (
    ActualPriceDataError,
    build_entsoe_actual_day_ahead_prices,
)
from backend.markets.market_profile_loader import get_default_market_profile
from backend.scenarios.scenario_runner import run_scenarios
from backend.services.forecast_service import save_forecast_dataframe
from backend.services.investor_evidence import build_forecast_proof
from backend.services.asset_provenance import attach_asset_provenance
from backend.services.signal_service import save_signal_outputs
from backend.signals.signal_engine import generate_battery_signal
from backend.storage import get_storage_client


router = APIRouter()


@router.post("/data/update-actual-prices")
def update_actual_day_ahead_prices(
    target_date: str | None = None,
    country_code: str = "DE_LU",
):
    actual_file = ACTUAL_PRICE_FILE
    storage = get_storage_client()

    try:
        df = build_entsoe_actual_day_ahead_prices(
            target_date=target_date,
            country_code=country_code,
        )

    except ValueError as error:
        return {
            "status": "missing_token",
            "message": str(error),
        }

    except (ActualPriceDataError, EntsoeForecastError) as error:
        return {
            "status": "not_found",
            "message": str(error),
            "actual_file": str(actual_file),
        }

    except Exception as error:
        return {
            "status": "error",
            "message": f"Could not update actual day-ahead prices: {error}",
            "actual_file": str(actual_file),
        }

    if df is None or df.empty:
        return {
            "status": "not_found",
            "message": "No actual day-ahead price data returned.",
            "actual_file": str(actual_file),
        }

    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    df["actual_price"] = pd.to_numeric(
        df["actual_price"],
        errors="coerce",
    )

    df = df.dropna(subset=["timestamp", "actual_price"])
    df = df.drop_duplicates(subset=["timestamp"])
    df = df.sort_values("timestamp")

    if df.empty:
        return {
            "status": "invalid",
            "message": "Actual price data was returned, but no valid timestamp and price rows were available.",
            "actual_file": str(actual_file),
        }

    storage.write_dataframe(actual_file, df)

    target_delivery_date = str(df["timestamp"].dt.date.iloc[0])

    return {
        "status": "ok",
        "message": "Actual day-ahead prices updated successfully.",
        "target_date": target_delivery_date,
        "actual_file": str(actual_file),
        "rows": len(df),
        "columns": df.columns.tolist(),
        "actual_provider": "entsoe",
        "actual_market": "day_ahead",
    }


@router.get(
    "/data/actual-prices/status",
    response_model=ActualPriceStatusResponse,
)
def actual_day_ahead_price_status():
    actual_file = ACTUAL_PRICE_FILE
    storage = get_storage_client()

    if not storage.exists(actual_file):
        return {
            "status": "not_found",
            "message": f"Actual price file not found: {actual_file}",
            "actual_file": file_status(actual_file),
        }

    df = storage.read_dataframe(actual_file)

    if df.empty:
        return {
            "status": "empty",
            "message": "Actual price file exists but is empty.",
            "actual_file": file_status(actual_file),
        }

    if "timestamp" not in df.columns or "actual_price" not in df.columns:
        return {
            "status": "invalid",
            "message": "Actual price file must contain timestamp and actual_price columns.",
            "actual_file": file_status(actual_file),
            "columns": df.columns.tolist(),
        }

    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    df["actual_price"] = pd.to_numeric(df["actual_price"], errors="coerce")

    invalid_timestamps = int(df["timestamp"].isna().sum())
    missing_prices = int(df["actual_price"].isna().sum())
    valid_df = df.dropna(subset=["timestamp", "actual_price"])

    if valid_df.empty:
        return {
            "status": "invalid",
            "message": "Actual price file contains no valid timestamp and price rows.",
            "actual_file": file_status(actual_file),
            "rows": len(df),
            "invalid_timestamps": invalid_timestamps,
            "missing_prices": missing_prices,
        }

    return {
        "status": "ok",
        "actual_file": file_status(actual_file),
        "rows": len(df),
        "valid_rows": len(valid_df),
        "columns": df.columns.tolist(),
        "first_timestamp": str(valid_df["timestamp"].min()),
        "last_timestamp": str(valid_df["timestamp"].max()),
        "min_actual_price": round(float(valid_df["actual_price"].min()), 4),
        "max_actual_price": round(float(valid_df["actual_price"].max()), 4),
        "average_actual_price": round(float(valid_df["actual_price"].mean()), 4),
        "invalid_timestamps": invalid_timestamps,
        "missing_prices": missing_prices,
    }

@router.post("/data/update-entsoe", response_model=ApiResponse)
def update_entsoe_data():
    forecast_file = FORECAST_FILE
    storage = get_storage_client()

    try:
        df = build_next_day_entsoe_forecast()

    except ValueError as error:
        return {
            "status": "missing_token",
            "message": str(error),
        }

    except EntsoeForecastError as error:
        if storage.exists(forecast_file):
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

    storage.write_dataframe(forecast_file, df)

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
    storage = get_storage_client()

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

    storage.write_dataframe(forecast_file, df)

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
    save_signal_outputs(signal_result, signal_file=signal_file)

    scenario_results = run_scenarios(price_data)

    scenario_file = SCENARIO_RESULTS_FILE
    storage.write_json(scenario_file, scenario_results)

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


@router.get("/forecast/status", response_model=ForecastStatusResponse)
def forecast_status():
    return build_forecast_status(FORECAST_FILE)


@router.get(
    "/assets/{asset_id}/forecast/status",
    response_model=ForecastStatusResponse,
)
def asset_forecast_status(asset_id: str):
    try:
        asset = get_asset(asset_id)
    except ValueError as error:
        return {
            "status": "not_found",
            "message": str(error),
        }

    status = build_forecast_status(Path(asset.forecast_file or FORECAST_FILE))

    return attach_asset_provenance({
        "asset_id": asset_id,
        **status,
        "forecast_proof": build_forecast_proof(asset=asset.to_dict(), status=status),
    }, asset, kind="forecast_status", source_file=status.get("forecast_file"))


def build_forecast_status(forecast_file):
    storage = get_storage_client()

    if not storage.exists(forecast_file):
        return {
            "status": "not_found",
            "message": f"Forecast file not found: {forecast_file}",
        }

    df = storage.read_dataframe(forecast_file)
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


@router.get("/forecast/preview", response_model=ForecastPreviewResponse)
def forecast_preview():
    return build_forecast_preview(FORECAST_FILE)


@router.get(
    "/assets/{asset_id}/forecast/preview",
    response_model=ForecastPreviewResponse,
)
def asset_forecast_preview(asset_id: str):
    try:
        asset = get_asset(asset_id)
    except ValueError as error:
        return {
            "status": "not_found",
            "message": str(error),
        }

    preview = {
        "asset_id": asset_id,
        **build_forecast_preview(Path(asset.forecast_file or FORECAST_FILE)),
    }
    return attach_asset_provenance(
        preview,
        asset,
        kind="forecast_preview",
        source_file=preview.get("forecast_file"),
    )


def build_forecast_preview(forecast_file):
    storage = get_storage_client()

    if not storage.exists(forecast_file):
        return {
            "status": "not_found",
            "message": f"Forecast file not found: {forecast_file}",
        }

    df = storage.read_dataframe(forecast_file)

    if df.empty:
        return {
            "status": "empty",
            "message": "Forecast file exists but is empty.",
            "forecast_file": str(forecast_file),
        }

    market_profile = get_default_market_profile()
    expected_intervals = int(market_profile.get("expected_intervals_per_day", 24))
    preview_rows = df.head(expected_intervals).copy()

    return {
        "status": "ok",
        "forecast_file": str(forecast_file),
        "rows": len(df),
        "columns": df.columns.tolist(),
        "market_profile_id": market_profile["market_profile_id"],
        "expected_intervals_per_day": expected_intervals,
        "market_time_unit_minutes": market_profile["market_time_unit_minutes"],
        "preview": preview_rows.to_dict(orient="records"),
    }


@router.post(
    "/forecasts/compare-profitability",
    response_model=ForecastProfitabilityResponse,
)
def run_forecast_profitability_comparison():
    output_file = Path("data/outputs/forecast_profitability_comparison.json")
    storage = get_storage_client()

    forecast_files = get_forecast_files()

    results = compare_forecast_profitability(forecast_files)

    storage.write_json(output_file, results)

    return {
        "status": "ok",
        "message": "Forecast profitability comparison completed successfully.",
        "comparison_file": str(output_file),
        "forecast_sources": list(forecast_files.keys()),
        "results": results,
    }


@router.get(
    "/forecasts/compare-profitability/latest",
    response_model=ForecastProfitabilityResponse,
)
def latest_forecast_profitability_comparison():
    comparison_file = Path("data/outputs/forecast_profitability_comparison.json")
    storage = get_storage_client()

    if not storage.exists(comparison_file):
        return {
            "status": "not_found",
            "message": "No forecast profitability comparison found. Run /forecasts/compare-profitability first.",
            "results": [],
        }

    results = storage.read_json(comparison_file)

    return {
        "status": "ok",
        "comparison_file": str(comparison_file),
        "results": results,
    }


@router.get("/features/forecast")
def forecast_features():
    forecast_file = FORECAST_FILE
    storage = get_storage_client()

    if not storage.exists(forecast_file):
        return {
            "status": "not_found",
            "message": f"Forecast file not found: {forecast_file}",
        }

    df = storage.read_dataframe(forecast_file)

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

    start_time = pd.Timestamp.now().normalize() + pd.Timedelta(days=1)

    prices = [
        42, 38, 30, 22, 15, 8,
        12, 28, 55, 72, 85, 92,
        88, 75, 60, 48, 52, 70,
        96, 120, 110, 82, 58, 45,
    ]

    rows = []

    for hour, price in enumerate(prices):
        for quarter in range(4):
            rows.append(
                {
                    "timestamp": (
                        start_time
                        + pd.Timedelta(hours=hour)
                        + pd.Timedelta(minutes=15 * quarter)
                    ),
                    "forecast_price": price,
                    "forecast_provider": "demo",
                    "forecast_model": "demo_base_15min",
                    "market_profile_id": "de_lu_day_ahead",
                    "market_time_unit_minutes": 15,
                }
            )

    df = pd.DataFrame(rows)
    save_forecast_dataframe(df, forecast_file)

    return {
        "status": "ok",
        "message": "Demo forecast created successfully.",
        "forecast_file": str(forecast_file),
        "rows": len(df),
        "forecast_provider": "demo",
        "forecast_model": "demo_base_15min",
    }


@router.post("/forecast/demo-high-spread")
def create_demo_high_spread_forecast():
    forecast_file = Path("data/processed/demo_high_spread_forecast.csv")

    start_time = pd.Timestamp.now().normalize() + pd.Timedelta(days=1)

    prices = [
        55, 48, 40, 28, 12, -5,
        -8, 20, 58, 85, 110, 125,
        118, 95, 72, 55, 62, 88,
        130, 155, 145, 100, 75, 60,
    ]

    rows = []

    for hour, price in enumerate(prices):
        for quarter in range(4):
            rows.append(
                {
                    "timestamp": (
                        start_time
                        + pd.Timedelta(hours=hour)
                        + pd.Timedelta(minutes=15 * quarter)
                    ),
                    "forecast_price": price,
                    "forecast_provider": "demo_high_spread",
                    "forecast_model": "demo_high_spread_15min",
                    "market_profile_id": "de_lu_day_ahead",
                    "market_time_unit_minutes": 15,
                }
            )

    df = pd.DataFrame(rows)
    save_forecast_dataframe(df, forecast_file)

    return {
        "status": "ok",
        "message": "Demo high-spread forecast created successfully.",
        "forecast_file": str(forecast_file),
        "rows": len(df),
        "forecast_provider": "demo_high_spread",
        "forecast_model": "demo_high_spread_15min",
    }


@router.post("/forecast/inhouse-placeholder")
def create_inhouse_placeholder_forecast():
    forecast_file = Path("data/processed/inhouse_placeholder_forecast.csv")

    df = build_next_day_inhouse_forecast()
    save_forecast_dataframe(df, forecast_file)

    return {
        "status": "ok",
        "message": "In-house placeholder forecast created successfully.",
        "forecast_file": str(forecast_file),
        "rows": len(df),
        "forecast_provider": "inhouse_placeholder",
        "forecast_model": "inhouse_placeholder_v0",
    }




