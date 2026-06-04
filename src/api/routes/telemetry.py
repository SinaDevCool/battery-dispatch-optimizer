from fastapi import APIRouter

from src.api.schemas import ApiResponse
from src.telemetry.asset_telemetry import (
    latest_asset_telemetry,
    save_demo_asset_telemetry,
    telemetry_history,
)


router = APIRouter()


@router.post("/assets/{asset_id}/telemetry/demo", response_model=ApiResponse)
def seed_demo_telemetry(asset_id: str):
    try:
        telemetry = save_demo_asset_telemetry(asset_id)
    except ValueError as error:
        return {
            "status": "not_found",
            "asset_id": asset_id,
            "message": str(error),
        }

    return {
        "status": "ok",
        "asset_id": asset_id,
        "telemetry": telemetry,
    }


@router.get("/assets/{asset_id}/telemetry/latest", response_model=ApiResponse)
def latest_telemetry(asset_id: str):
    return latest_asset_telemetry(asset_id)


@router.get("/assets/{asset_id}/telemetry/history", response_model=ApiResponse)
def asset_telemetry_history(asset_id: str, limit: int = 25):
    return telemetry_history(asset_id=asset_id, limit=limit)
