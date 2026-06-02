from fastapi import APIRouter

from src.db.repositories.revenue_repository import (
    get_revenue_stack_run,
    list_revenue_product_results,
    list_revenue_stack_runs,
)
from src.db.repositories.signal_repository import (
    get_signal_run,
    list_signal_runs,
)


router = APIRouter()


@router.get("/assets/{asset_id}/signals")
def asset_signal_runs(asset_id: str, limit: int = 50):
    runs = list_signal_runs(asset_id=asset_id, limit=limit)

    return {
        "status": "ok",
        "asset_id": asset_id,
        "run_count": len(runs),
        "runs": runs,
    }


@router.get("/assets/{asset_id}/signals/{signal_id}")
def asset_signal_run(asset_id: str, signal_id: int):
    run = get_signal_run(signal_id)

    if run is None or run["asset_id"] != asset_id:
        return {
            "status": "not_found",
            "message": f"Signal run not found for asset {asset_id}: {signal_id}",
        }

    return {
        "status": "ok",
        "asset_id": asset_id,
        "signal": run,
    }


@router.get("/assets/{asset_id}/revenue-stack/runs")
def asset_revenue_stack_runs(asset_id: str, limit: int = 50):
    runs = list_revenue_stack_runs(asset_id=asset_id, limit=limit)

    return {
        "status": "ok",
        "asset_id": asset_id,
        "run_count": len(runs),
        "runs": runs,
    }


@router.get("/assets/{asset_id}/revenue-stack/runs/{revenue_stack_id}")
def asset_revenue_stack_run(asset_id: str, revenue_stack_id: int):
    run = get_revenue_stack_run(revenue_stack_id)

    if run is None or run["asset_id"] != asset_id:
        return {
            "status": "not_found",
            "message": (
                f"Revenue stack run not found for asset "
                f"{asset_id}: {revenue_stack_id}"
            ),
        }

    products = list_revenue_product_results(revenue_stack_id)

    return {
        "status": "ok",
        "asset_id": asset_id,
        "revenue_stack": run,
        "products": products,
    }
