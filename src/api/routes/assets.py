from fastapi import APIRouter

from src.assets.asset_loader import load_assets
from src.assets.portfolio_runner import (
    load_latest_portfolio_results,
    run_portfolio_dispatch,
)


router = APIRouter()


@router.get("/assets")
def list_assets():
    assets = load_assets()

    return {
        "status": "ok",
        "asset_count": len(assets),
        "assets": [asset.to_dict() for asset in assets],
    }


@router.post("/portfolio/run-daily")
def run_portfolio_daily(optimizer_engine: str = "rule_based_v1"):
    return run_portfolio_dispatch(optimizer_engine=optimizer_engine)


@router.get("/portfolio/latest")
def latest_portfolio_results():
    return load_latest_portfolio_results()
