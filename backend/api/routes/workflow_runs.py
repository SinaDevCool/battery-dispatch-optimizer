from fastapi import APIRouter

from backend.api.schemas import ApiResponse
from backend.services.asset_workflow_service import (
    asset_workflow_run_detail,
    asset_workflow_run_history,
    latest_asset_workflow_run,
    run_asset_audited_workflow,
)


router = APIRouter()


@router.post("/assets/{asset_id}/workflow-runs/run", response_model=ApiResponse)
def run_asset_workflow(asset_id: str, optimizer_engine: str = "rule_based_v1"):
    try:
        return run_asset_audited_workflow(
            asset_id=asset_id,
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
            "message": f"Could not run audited workflow: {error}",
        }


@router.get("/assets/{asset_id}/workflow-runs/latest", response_model=ApiResponse)
def latest_asset_workflow(asset_id: str):
    return latest_asset_workflow_run(asset_id)


@router.get("/assets/{asset_id}/workflow-runs", response_model=ApiResponse)
def asset_workflow_history(asset_id: str, limit: int = 25):
    return asset_workflow_run_history(asset_id=asset_id, limit=limit)


@router.get(
    "/assets/{asset_id}/workflow-runs/{workflow_run_id}",
    response_model=ApiResponse,
)
def asset_workflow_detail(asset_id: str, workflow_run_id: int):
    return asset_workflow_run_detail(
        asset_id=asset_id,
        workflow_run_id=workflow_run_id,
    )



