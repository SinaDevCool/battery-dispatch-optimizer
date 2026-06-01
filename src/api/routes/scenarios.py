import json

from fastapi import APIRouter

from src.api.schemas import BatterySignalRequest
from src.config.client_config import load_client_config
from src.config.paths import (
    FORECAST_FILE,
    PRICE_STRESS_RESULTS_FILE,
    SCENARIO_RESULTS_FILE,
)
from src.forecasts.forecast_loader import load_forecast_price_data
from src.markets.data_loader import load_price_data_for_optimizer
from src.scenarios.scenario_runner import run_scenarios
from src.scenarios.stress_runner import run_price_stress_tests


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
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, "w", encoding="utf-8") as file:
        json.dump(scenario_results, file, indent=2)

    return {
        "status": "ok",
        "results": scenario_results,
        "output_file": str(output_file),
    }


@router.post("/scenarios/run-latest")
def run_latest_scenarios():
    forecast_file = FORECAST_FILE
    output_file = SCENARIO_RESULTS_FILE

    if not forecast_file.exists():
        return {
            "status": "not_found",
            "message": f"Forecast file not found: {forecast_file}",
        }

    price_data = load_forecast_price_data(forecast_file)

    scenario_results = run_scenarios(price_data)

    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, "w", encoding="utf-8") as file:
        json.dump(scenario_results, file, indent=2)

    return {
        "status": "ok",
        "message": "Scenario analysis completed successfully.",
        "scenario_file": str(output_file),
        "results": scenario_results,
    }


@router.get("/scenarios/latest")
def latest_scenarios():
    scenario_file = SCENARIO_RESULTS_FILE

    if not scenario_file.exists():
        return {
            "status": "not_found",
            "message": "No scenario results found. Run /scenarios/run first.",
        }

    with open(scenario_file, "r", encoding="utf-8") as file:
        results = json.load(file)

    return {
        "status": "ok",
        "scenario_file": str(scenario_file),
        "results": results,
    }


@router.post("/stress/run-latest")
def run_latest_price_stress_tests():
    forecast_file = FORECAST_FILE
    output_file = PRICE_STRESS_RESULTS_FILE

    if not forecast_file.exists():
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

    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, "w", encoding="utf-8") as file:
        json.dump(stress_results, file, indent=2)

    return {
        "status": "ok",
        "message": "Price stress tests completed successfully.",
        "stress_file": str(output_file),
        "results": stress_results,
    }


@router.get("/stress/latest")
def latest_price_stress_tests():
    stress_file = PRICE_STRESS_RESULTS_FILE

    if not stress_file.exists():
        return {
            "status": "not_found",
            "message": "No price stress results found. Run /stress/run-latest first.",
        }

    with open(stress_file, "r", encoding="utf-8") as file:
        results = json.load(file)

    return {
        "status": "ok",
        "stress_file": str(stress_file),
        "results": results,
    }
