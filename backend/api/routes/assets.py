from fastapi import APIRouter

from backend.api.schemas import ApiResponse, AssetListResponse
from backend.assets.portfolio_runner import (
    load_latest_portfolio_results,
    run_portfolio_dispatch,
)
from backend.db.repositories.asset_repository import list_asset_records
from backend.services.asset_cockpit_service import build_asset_cockpit
from backend.services.data_completeness_service import build_asset_data_completeness
from backend.services.demo_portfolio_service import run_complete_demo_portfolio


router = APIRouter()


@router.get("/assets", response_model=AssetListResponse)
def list_assets():
    assets = list_asset_records()

    return {
        "status": "ok",
        "asset_count": len(assets),
        "assets": assets,
    }


@router.get("/assets/{asset_id}/data-completeness", response_model=ApiResponse)
def asset_data_completeness(asset_id: str):
    try:
        return build_asset_data_completeness(asset_id)
    except ValueError as error:
        return {
            "status": "not_found",
            "message": str(error),
        }


@router.get("/assets/{asset_id}/cockpit", response_model=ApiResponse)
def asset_cockpit(asset_id: str):
    try:
        return build_asset_cockpit(asset_id)
    except ValueError as error:
        return {
            "status": "not_found",
            "message": str(error),
        }
    except Exception as error:
        return {
            "status": "error",
            "message": f"Could not build asset cockpit: {error}",
        }


@router.post("/demo/portfolio/run", response_model=ApiResponse)
def run_demo_portfolio(
    asset_id: str = "default_site",
    optimizer_engine: str = "rule_based_v1",
):
    try:
        return run_complete_demo_portfolio(
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
            "message": f"Could not run complete demo portfolio: {error}",
        }


@router.post("/portfolio/run-daily", response_model=ApiResponse)
def run_portfolio_daily(optimizer_engine: str = "rule_based_v1"):
    return run_portfolio_dispatch(optimizer_engine=optimizer_engine)


@router.get("/portfolio/latest", response_model=ApiResponse)
def latest_portfolio_results():
    return load_latest_portfolio_results()



