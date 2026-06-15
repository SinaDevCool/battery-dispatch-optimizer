from fastapi import APIRouter

from backend.api.schemas import BatterySignalRequest
from backend.config.client_config import load_client_config
from backend.config.paths import (
    FORECAST_FILE,
    PRICE_STRESS_RESULTS_FILE,
    SCENARIO_RESULTS_FILE,
)
from backend.forecasts.forecast_loader import load_forecast_price_data
from backend.markets.data_loader import load_price_data_for_optimizer
from backend.scenarios.scenario_runner import run_scenarios
from backend.scenarios.stress_runner import run_price_stress_tests
from backend.storage import get_storage_client


router = APIRouter()


@router.post("/scenarios/run")
def run_battery_scenarios(request: BatterySignalRequest):
    price_data = [
        {
            "timestamp": item.timestamp,
            "price": item.price,
        }
        for item in request.price_data
    ]

    scenario_results = run_scenarios(price_data)

    output_file = SCENARIO_RESULTS_FILE
    get_storage_client().write_json(output_file, scenario_results)

    return {
        "status": "ok",
        "results": scenario_results,
        "output_file": str(output_file),
    }


@router.post("/scenarios/run-latest")
def run_latest_scenarios():
    forecast_file = FORECAST_FILE
    output_file = SCENARIO_RESULTS_FILE
    storage = get_storage_client()

    if not storage.exists(forecast_file):
        return {
            "status": "not_found",
            "message": f"Forecast file not found: {forecast_file}",
        }

    price_data = load_forecast_price_data(forecast_file)

    scenario_results = run_scenarios(price_data)

    storage.write_json(output_file, scenario_results)

    return {
        "status": "ok",
        "message": "Scenario analysis completed successfully.",
        "scenario_file": str(output_file),
        "results": scenario_results,
    }


@router.get("/scenarios/latest")
def latest_scenarios():
    scenario_file = SCENARIO_RESULTS_FILE
    storage = get_storage_client()

    if not storage.exists(scenario_file):
        return {
            "status": "not_found",
            "message": "No scenario results found. Run /scenarios/run first.",
        }

    results = storage.read_json(scenario_file)

    return {
        "status": "ok",
        "scenario_file": str(scenario_file),
        "results": results,
    }


@router.post("/stress/run-latest")
def run_latest_price_stress_tests():
    forecast_file = FORECAST_FILE
    output_file = PRICE_STRESS_RESULTS_FILE
    storage = get_storage_client()

    if not storage.exists(forecast_file):
        return {
            "status": "not_found",
            "message": f"Forecast file not found: {forecast_file}",
        }

    try:
        client_config = load_client_config()
    except FileNotFoundError as error:
        return {
            "status": "not_found",
            "message": str(error),
        }

    price_data = load_price_data_for_optimizer(
        forecast_file,
        price_column="forecast_price",
    )

    stress_results = run_price_stress_tests(
        price_data=price_data,
        battery_config=client_config["battery_config"],
        strategy_config=client_config["strategy_config"],
        commercial_config=client_config.get("commercial_config"),
    )

    storage.write_json(output_file, stress_results)

    return {
        "status": "ok",
        "message": "Price stress tests completed successfully.",
        "stress_file": str(output_file),
        "results": stress_results,
    }


@router.get("/stress/latest")
def latest_price_stress_tests():
    stress_file = PRICE_STRESS_RESULTS_FILE
    storage = get_storage_client()

    if not storage.exists(stress_file):
        return {
            "status": "not_found",
            "message": "No price stress results found. Run /stress/run-latest first.",
        }

    results = storage.read_json(stress_file)

    return {
        "status": "ok",
        "stress_file": str(stress_file),
        "results": results,
    }



