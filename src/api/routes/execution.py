from fastapi import APIRouter

from src.api.schemas import ApiResponse
from src.execution.pretrade_proposal import (
    build_execution_proposal,
    execution_proposal_history,
    latest_execution_proposal,
)


router = APIRouter()


@router.post(
    "/assets/{asset_id}/execution/proposal/build",
    response_model=ApiResponse,
)
def build_asset_execution_proposal(asset_id: str):
    try:
        proposal = build_execution_proposal(asset_id)
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
            "message": f"Could not build execution proposal: {error}",
        }

    return {
        "status": "ok",
        "asset_id": asset_id,
        "proposal": proposal,
    }


@router.get(
    "/assets/{asset_id}/execution/proposal/latest",
    response_model=ApiResponse,
)
def latest_asset_execution_proposal(asset_id: str):
    return latest_execution_proposal(asset_id)


@router.get(
    "/assets/{asset_id}/execution/proposals",
    response_model=ApiResponse,
)
def asset_execution_proposals(asset_id: str, limit: int = 25):
    return execution_proposal_history(asset_id=asset_id, limit=limit)
