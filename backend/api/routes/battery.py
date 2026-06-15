from datetime import datetime

from fastapi import APIRouter

from backend.api.schemas import (
    BacktestRequest,
    BacktestResponse,
    BatteryConfigResponse,
    BatterySignalRequest,
    BatterySignalResponse,
)
from backend.backtesting.metrics import calculate_backtest_metrics
from backend.config.battery_config import DEFAULT_BATTERY_CONFIG, DEFAULT_STRATEGY_CONFIG
from backend.config.client_config import load_client_config
from backend.config.paths import FORECAST_FILE, LATEST_SIGNAL_FILE, SIGNAL_RUNS_DIR
from backend.optimization.optimizer_registry import list_optimizer_engines
from backend.services.asset_dispatch_service import (
    add_asset_dispatch_validation,
    apply_grid_connection_limits,
    build_asset_signal_metadata,
    dispatch_default_asset,
)
from backend.services.asset_signal_store import save_asset_signal
from backend.services.signal_service import (
    add_signal_metadata,
    load_latest_signal,
    save_signal_outputs,
)
from backend.signals.explanation_engine import explain_battery_signal
from backend.signals.risk_engine import build_risk_flags
from backend.signals.signal_engine import generate_battery_signal
from backend.storage import get_storage_client


router = APIRouter()


@router.get("/battery/optimizers")
def battery_optimizers():
    return {
        "status": "ok",
        "default_optimizer": "rule_based_v1",
        "available_optimizers": list_optimizer_engines(),
    }


@router.get("/battery/config", response_model=BatteryConfigResponse)
def battery_config():
    return {
        "battery_config": DEFAULT_BATTERY_CONFIG,
        "strategy_config": DEFAULT_STRATEGY_CONFIG,
    }


@router.get("/battery/constraints")
def battery_constraints():
    try:
        client_config = load_client_config()
    except FileNotFoundError as error:
        return {
            "status": "not_found",
            "message": str(error),
        }

    battery_config = apply_grid_connection_limits(
        client_config["battery_config"],
        client_config.get("grid_connection", {}),
    )
    grid_connection = client_config.get("grid_connection", {})

    capacity_mwh = battery_config["capacity_mwh"]
    initial_soc_mwh = battery_config["initial_soc_mwh"]
    min_soc_mwh = battery_config["min_soc_mwh"]
    max_charge_power_mw = battery_config["max_charge_power_mw"]
    max_discharge_power_mw = battery_config["max_discharge_power_mw"]

    usable_capacity_mwh = capacity_mwh - min_soc_mwh
    initial_usable_soc_mwh = initial_soc_mwh - min_soc_mwh

    charge_duration_hours = capacity_mwh / max_charge_power_mw
    discharge_duration_hours = usable_capacity_mwh / max_discharge_power_mw

    return {
        "status": "ok",
        "capacity_mwh": capacity_mwh,
        "usable_capacity_mwh": round(usable_capacity_mwh, 4),
        "initial_usable_soc_mwh": round(initial_usable_soc_mwh, 4),
        "min_soc_mwh": min_soc_mwh,
        "initial_soc_mwh": initial_soc_mwh,
        "max_charge_power_mw": max_charge_power_mw,
        "max_discharge_power_mw": max_discharge_power_mw,
        "grid_connection": grid_connection,
        "constraints_source": "asset_aware_grid_connection",
        "charge_duration_hours": round(charge_duration_hours, 4),
        "discharge_duration_hours": round(discharge_duration_hours, 4),
    }


@router.post("/battery/signal", response_model=BatterySignalResponse)
def battery_signal(request: BatterySignalRequest):
    price_data = [
        {
            "timestamp": item.timestamp,
            "price": item.price,
        }
        for item in request.price_data
    ]

    battery_config = None
    strategy_config = None

    if request.battery_config is not None:
        battery_config = request.battery_config.model_dump()

    if request.strategy_config is not None:
        strategy_config = request.strategy_config.model_dump()

    return generate_battery_signal(
        price_data=price_data,
        battery_config=battery_config,
        strategy_config=strategy_config,
    )


@router.get("/battery/signal/latest")
def latest_battery_signal():
    signal_file = LATEST_SIGNAL_FILE
    storage = get_storage_client()

    if not storage.exists(signal_file):
        return {
            "status": "not_found",
            "message": "No latest battery signal found. Run /workflow/run-daily or archive/manual_scripts/run_daily_signal.py first.",
        }

    signal = load_latest_signal(signal_file)

    return {
        "status": "ok",
        "signal_file": str(signal_file),
        "data": signal,
    }


@router.get("/battery/signal/latest/explanation")
def latest_battery_signal_explanation():
    signal_file = LATEST_SIGNAL_FILE
    storage = get_storage_client()

    if not storage.exists(signal_file):
        return {
            "status": "not_found",
            "message": "No latest battery signal found. Run the daily workflow first.",
        }

    signal = load_latest_signal(signal_file)

    forecast_df = None

    if storage.exists(FORECAST_FILE):
        forecast_df = storage.read_dataframe(FORECAST_FILE)

    return explain_battery_signal(signal, forecast_df=forecast_df)


@router.get("/battery/signal/latest/risks")
def latest_battery_signal_risks():
    signal_file = LATEST_SIGNAL_FILE
    storage = get_storage_client()

    if not storage.exists(signal_file):
        return {
            "status": "not_found",
            "message": "No latest battery signal found. Run the daily workflow first.",
            "risks": [],
        }

    signal = load_latest_signal(signal_file)

    forecast_df = None

    if storage.exists(FORECAST_FILE):
        forecast_df = storage.read_dataframe(FORECAST_FILE)

    risks = build_risk_flags(signal, forecast_df=forecast_df)

    return {
        "status": "ok",
        "risks": risks,
    }


@router.post("/battery/signal/run-latest")
def run_latest_battery_signal(optimizer_engine: str = "rule_based_v1"):
    try:
        forecast_file = FORECAST_FILE
        storage = get_storage_client()

        if not storage.exists(forecast_file):
            return {
                "status": "not_found",
                "message": f"Forecast file not found: {forecast_file}",
            }

        asset_dispatch_result = dispatch_default_asset(
            forecast_file=forecast_file,
            optimizer_engine=optimizer_engine,
        )
        dispatch_result = asset_dispatch_result.dispatch_result

        generated_at = datetime.now()

        result = add_signal_metadata(
            signal_result=dispatch_result.signal_result,
            source="processed_forecast_csv",
            forecast_model="processed_forecast_csv",
            target_date=None,
            forecast_file=forecast_file,
            generated_at=generated_at,
            extra_metadata=build_asset_signal_metadata(asset_dispatch_result),
        )
        result = add_asset_dispatch_validation(
            signal_result=result,
            asset_dispatch_result=asset_dispatch_result,
        )

        saved_signal_files = save_signal_outputs(
            signal_result=result,
            target_date=None,
        )
        saved_asset_signal_files = save_asset_signal(
            signal_result=result,
            asset_id=asset_dispatch_result.asset.asset_id,
            target_date=None,
        )

        return {
            "status": "ok",
            "message": "Latest battery signal generated successfully.",
            "signal_file": str(saved_signal_files["signal_file"]),
            "run_history_file": str(saved_signal_files["run_history_file"]),
            "asset_latest_signal_file": str(
                saved_asset_signal_files["asset_latest_signal_file"]
            ),
            "asset_run_file": str(saved_asset_signal_files["asset_run_file"]),
            "signal_id": saved_asset_signal_files["signal_id"],
            "optimizer_engine": dispatch_result.optimizer_engine,
            "asset_id": asset_dispatch_result.asset.asset_id,
            "market_profile_id": asset_dispatch_result.asset.market_profile_id,
            "assumption_risk_flags": asset_dispatch_result.assumption_risk_flags,
            "validation": result["validation"],
            "data": result,
        }

    except FileNotFoundError as error:
        return {
            "status": "not_found",
            "message": str(error),
        }

    except Exception as error:
        return {
            "status": "error",
            "message": f"Could not generate latest battery signal: {error}",
        }


@router.get("/battery/signal/history")
def battery_signal_history():
    run_history_dir = SIGNAL_RUNS_DIR
    storage = get_storage_client()
    run_files = storage.list_files(run_history_dir, "*_battery_signal.json")

    if not run_files:
        return {
            "status": "not_found",
            "message": "No run history found.",
            "runs": [],
        }

    runs = []

    for file_path in run_files:
        status = storage.file_status(file_path)
        runs.append(
            {
                "file_name": file_path.name,
                "file_path": str(file_path),
                "last_modified": status["last_modified"],
                "size_bytes": status["size_bytes"],
            }
        )

    return {
        "status": "ok",
        "runs": runs,
    }


@router.get("/battery/signal/history/{file_name}")
def get_battery_signal_history_file(file_name: str):
    run_history_dir = SIGNAL_RUNS_DIR
    run_file = run_history_dir / file_name
    storage = get_storage_client()

    if not storage.exists(run_file):
        return {
            "status": "not_found",
            "message": f"Run history file not found: {file_name}",
        }

    if run_file.suffix != ".json":
        return {
            "status": "invalid_file",
            "message": "Only JSON run history files can be loaded.",
        }

    data = storage.read_json(run_file)

    return {
        "status": "ok",
        "file_name": file_name,
        "data": data,
    }


@router.post("/battery/backtest", response_model=BacktestResponse)
def battery_backtest(request: BacktestRequest):
    price_data = [
        {
            "timestamp": item.timestamp,
            "price": item.price,
        }
        for item in request.price_data
    ]

    battery_config = None
    strategy_config = None

    if request.battery_config is not None:
        battery_config = request.battery_config.model_dump()

    if request.strategy_config is not None:
        strategy_config = request.strategy_config.model_dump()

    result = generate_battery_signal(
        price_data=price_data,
        battery_config=battery_config,
        strategy_config=strategy_config,
    )

    metrics = calculate_backtest_metrics(result["dispatch"])

    return {
        "summary": metrics,
        "dispatch": result["dispatch"],
    }



