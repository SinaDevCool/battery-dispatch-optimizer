from datetime import datetime

from fastapi import APIRouter

from src.assets.asset_loader import get_asset
from src.services.asset_dispatch_service import (
    add_asset_dispatch_validation,
    build_asset_signal_metadata,
    dispatch_asset,
)
from src.services.asset_signal_store import (
    list_asset_signal_history,
    load_asset_latest_signal,
    load_asset_signal_run,
    save_asset_signal,
)
from src.services.signal_service import add_signal_metadata


router = APIRouter()


@router.post("/assets/{asset_id}/signal/run-latest")
def run_asset_latest_signal(asset_id: str, optimizer_engine: str = "rule_based_v1"):
    try:
        asset = get_asset(asset_id)
        asset_dispatch_result = dispatch_asset(
            asset=asset,
            optimizer_engine=optimizer_engine,
        )
    except ValueError as error:
        return {
            "status": "not_found",
            "message": str(error),
        }
    except FileNotFoundError as error:
        return {
            "status": "not_found",
            "message": str(error),
        }
    except Exception as error:
        return {
            "status": "error",
            "message": f"Could not generate asset signal: {error}",
        }

    dispatch_result = asset_dispatch_result.dispatch_result
    generated_at = datetime.now()

    signal_result = add_signal_metadata(
        signal_result=dispatch_result.signal_result,
        source="asset_forecast_file",
        forecast_model="asset_forecast_file",
        target_date=None,
        forecast_file=asset_dispatch_result.forecast_file,
        generated_at=generated_at,
        extra_metadata=build_asset_signal_metadata(asset_dispatch_result),
    )
    signal_result = add_asset_dispatch_validation(
        signal_result=signal_result,
        asset_dispatch_result=asset_dispatch_result,
    )

    saved_files = save_asset_signal(
        signal_result=signal_result,
        asset_id=asset_id,
    )

    return {
        "status": "ok",
        "message": "Asset battery signal generated successfully.",
        "asset_id": asset_id,
        "optimizer_engine": dispatch_result.optimizer_engine,
        "asset_latest_signal_file": str(saved_files["asset_latest_signal_file"]),
        "asset_run_file": str(saved_files["asset_run_file"]),
        "assumption_risk_flags": asset_dispatch_result.assumption_risk_flags,
        "validation": signal_result["validation"],
        "data": signal_result,
    }


@router.get("/assets/{asset_id}/signal/latest")
def latest_asset_signal(asset_id: str):
    return load_asset_latest_signal(asset_id)


@router.get("/assets/{asset_id}/signal/history")
def asset_signal_history(asset_id: str):
    return list_asset_signal_history(asset_id)


@router.get("/assets/{asset_id}/signal/history/{file_name}")
def asset_signal_history_run(asset_id: str, file_name: str):
    return load_asset_signal_run(asset_id, file_name)
