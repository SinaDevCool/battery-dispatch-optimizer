from fastapi import APIRouter

from backend.api.schemas import ApiResponse
from backend.settlement.settlement_reconciliation import (
    latest_settlement_reconciliation,
    run_settlement_reconciliation,
    settlement_reconciliation_history,
)


router = APIRouter()


@router.post(
    "/assets/{asset_id}/settlement/reconcile",
    response_model=ApiResponse,
)
def reconcile_asset_settlement(asset_id: str):
    try:
        return run_settlement_reconciliation(asset_id)
    except FileNotFoundError as error:
        return {
            "status": "not_found",
            "asset_id": asset_id,
            "message": str(error),
        }
    except Exception as error:
        return {
            "status": "error",
            "asset_id": asset_id,
            "message": f"Could not reconcile settlement: {error}",
        }


@router.get(
    "/assets/{asset_id}/settlement/latest",
    response_model=ApiResponse,
)
def latest_asset_settlement(asset_id: str):
    return latest_settlement_reconciliation(asset_id)


@router.get(
    "/assets/{asset_id}/settlement/runs",
    response_model=ApiResponse,
)
def asset_settlement_history(asset_id: str, limit: int = 25):
    return settlement_reconciliation_history(asset_id=asset_id, limit=limit)



