from fastapi import APIRouter

from backend.api.schemas import BatterySignalRequest
from backend.assets.asset_loader import get_asset
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
from backend.services.asset_output_paths import (
    asset_price_stress_results_file,
    asset_scenario_results_file,
    build_asset_output_envelope,
    extract_metadata,
    extract_results,
)
from backend.services.investor_evidence import build_scenario_proof, build_stress_proof
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
        "scenario_proof": build_scenario_proof(results=scenario_results),
    }


@router.post("/assets/{asset_id}/scenarios/run-latest")
def run_latest_asset_scenarios(asset_id: str):
    try:
        asset = get_asset(asset_id)
    except ValueError as error:
        return {
            "status": "not_found",
            "message": str(error),
            "asset_id": asset_id,
        }

    forecast_file = asset.forecast_file or FORECAST_FILE
    output_file = asset_scenario_results_file(asset_id)
    storage = get_storage_client()

    if not storage.exists(forecast_file):
        return {
            "status": "not_found",
            "message": f"Forecast file not found: {forecast_file}",
            "asset_id": asset_id,
        }

    price_data = load_forecast_price_data(forecast_file)
    scenario_results = run_scenarios(
        price_data,
        strategy_config=asset.strategy_config,
        commercial_config=asset.commercial_config,
        asset=asset,
        forecast_file=forecast_file,
    )
    output_payload = build_asset_output_envelope(
        asset=asset.to_dict(),
        forecast_file=str(forecast_file),
        kind="scenario_results",
        results=scenario_results,
    )
    storage.write_json(output_file, output_payload)

    return {
        "status": "ok",
        "asset_id": asset_id,
        "message": "Selected-asset scenario analysis completed successfully.",
        "scenario_file": str(output_file),
        "metadata": output_payload["metadata"],
        "results": scenario_results,
        "scenario_proof": build_scenario_proof(
            asset=asset.to_dict(),
            forecast_file=str(forecast_file),
            results=scenario_results,
        ),
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

    results_payload = storage.read_json(scenario_file)
    results = extract_results(results_payload)

    return {
        "status": "ok",
        "scenario_file": str(scenario_file),
        "metadata": extract_metadata(results_payload),
        "results": results,
        "scenario_proof": build_scenario_proof(results=results),
    }


@router.get("/assets/{asset_id}/scenarios/latest")
def latest_asset_scenarios(asset_id: str):
    try:
        asset = get_asset(asset_id)
    except ValueError as error:
        return {
            "status": "not_found",
            "message": str(error),
            "asset_id": asset_id,
        }

    scenario_file = asset_scenario_results_file(asset_id)
    storage = get_storage_client()

    if not storage.exists(scenario_file):
        return {
            "status": "not_found",
            "message": "No scenario results found. Run selected-asset scenarios first.",
            "asset_id": asset_id,
            "scenario_file": str(scenario_file),
        }

    results_payload = storage.read_json(scenario_file)
    results = extract_results(results_payload)
    forecast_file = asset.forecast_file or FORECAST_FILE

    return {
        "status": "ok",
        "asset_id": asset_id,
        "scenario_file": str(scenario_file),
        "metadata": extract_metadata(results_payload),
        "results": results,
        "scenario_proof": build_scenario_proof(
            asset=asset.to_dict(),
            forecast_file=str(forecast_file),
            results=results,
        ),
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
        "stress_proof": build_stress_proof(results=stress_results),
    }


@router.post("/assets/{asset_id}/stress/run-latest")
def run_latest_asset_price_stress_tests(asset_id: str):
    try:
        asset = get_asset(asset_id)
    except ValueError as error:
        return {
            "status": "not_found",
            "message": str(error),
            "asset_id": asset_id,
        }

    forecast_file = asset.forecast_file or FORECAST_FILE
    output_file = asset_price_stress_results_file(asset_id)
    storage = get_storage_client()

    if not storage.exists(forecast_file):
        return {
            "status": "not_found",
            "message": f"Forecast file not found: {forecast_file}",
            "asset_id": asset_id,
        }

    try:
        client_config = load_client_config()
    except FileNotFoundError as error:
        return {
            "status": "not_found",
            "message": str(error),
            "asset_id": asset_id,
        }

    price_data = load_price_data_for_optimizer(
        forecast_file,
        price_column="forecast_price",
    )
    asset_payload = asset.to_dict()
    stress_results = run_price_stress_tests(
        price_data=price_data,
        battery_config=asset_payload.get("battery_config") or client_config["battery_config"],
        strategy_config=asset_payload.get("strategy_config") or client_config["strategy_config"],
        commercial_config=asset_payload.get("commercial_config")
        or client_config.get("commercial_config"),
        asset=asset,
        forecast_file=forecast_file,
    )
    output_payload = build_asset_output_envelope(
        asset=asset_payload,
        forecast_file=str(forecast_file),
        kind="price_stress_results",
        results=stress_results,
    )
    storage.write_json(output_file, output_payload)

    return {
        "status": "ok",
        "asset_id": asset_id,
        "message": "Selected-asset price stress tests completed successfully.",
        "stress_file": str(output_file),
        "metadata": output_payload["metadata"],
        "results": stress_results,
        "stress_proof": build_stress_proof(
            asset=asset_payload,
            forecast_file=str(forecast_file),
            results=stress_results,
        ),
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

    results_payload = storage.read_json(stress_file)
    results = extract_results(results_payload)

    return {
        "status": "ok",
        "stress_file": str(stress_file),
        "metadata": extract_metadata(results_payload),
        "results": results,
        "stress_proof": build_stress_proof(results=results),
    }


@router.get("/assets/{asset_id}/stress/latest")
def latest_asset_price_stress_tests(asset_id: str):
    try:
        asset = get_asset(asset_id)
    except ValueError as error:
        return {
            "status": "not_found",
            "message": str(error),
            "asset_id": asset_id,
        }

    stress_file = asset_price_stress_results_file(asset_id)
    storage = get_storage_client()

    if not storage.exists(stress_file):
        return {
            "status": "not_found",
            "message": "No price stress results found. Run selected-asset stress tests first.",
            "asset_id": asset_id,
            "stress_file": str(stress_file),
        }

    results_payload = storage.read_json(stress_file)
    results = extract_results(results_payload)
    forecast_file = asset.forecast_file or FORECAST_FILE

    return {
        "status": "ok",
        "asset_id": asset_id,
        "stress_file": str(stress_file),
        "metadata": extract_metadata(results_payload),
        "results": results,
        "stress_proof": build_stress_proof(
            asset=asset.to_dict(),
            forecast_file=str(forecast_file),
            results=results,
        ),
    }
