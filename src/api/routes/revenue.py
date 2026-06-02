from fastapi import APIRouter

from src.revenue.revenue_stack_runner import (
    load_latest_asset_revenue_stack,
    run_asset_revenue_stack,
)


router = APIRouter()


@router.post("/assets/{asset_id}/revenue-stack/run")
def run_asset_revenue_stack_endpoint(
    asset_id: str,
    optimizer_engine: str = "rule_based_v1",
):
    try:
        return run_asset_revenue_stack(
            asset_id=asset_id,
            optimizer_engine=optimizer_engine,
        )
    except ValueError as error:
        return {
            "status": "not_found",
            "message": str(error),
        }
    except Exception as error:
        return {
            "status": "error",
            "message": f"Could not run revenue stack: {error}",
        }


@router.get("/assets/{asset_id}/revenue-stack/latest")
def latest_asset_revenue_stack(asset_id: str):
    return load_latest_asset_revenue_stack(asset_id)
