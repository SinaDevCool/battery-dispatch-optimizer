from fastapi import APIRouter

from backend.api.schemas import (
    ApiResponse,
    GridFeeSensitivityResponse,
    HedgingRevenueResponse,
    RevenueAllocationResponse,
    RevenueStackResponse,
)
from backend.assets.asset_loader import get_asset
from backend.energy_accounting.energy_origin_ledger import build_energy_origin_ledger
from backend.grid_fees.germany_grid_fee_model import build_germany_grid_fee_sensitivity
from backend.hedging.revenue_contracts import build_hedged_revenue_view
from backend.revenue.revenue_stack_allocator import (
    load_latest_revenue_stack_allocation,
    run_revenue_stack_allocation,
)
from backend.revenue.revenue_stack_runner import (
    load_latest_asset_revenue_stack,
    run_asset_revenue_stack,
)
from backend.services.asset_provenance import attach_asset_provenance
from backend.services.asset_signal_store import load_asset_latest_signal


router = APIRouter()


@router.post(
    "/assets/{asset_id}/revenue-stack/run",
    response_model=RevenueStackResponse,
)
def run_asset_revenue_stack_endpoint(
    asset_id: str,
    optimizer_engine: str = "rule_based_v1",
):
    try:
        result = run_asset_revenue_stack(
            asset_id=asset_id,
            optimizer_engine=optimizer_engine,
        )
        return attach_asset_provenance(
            result,
            get_asset(asset_id),
            artifact="latest_revenue_stack.json",
            kind="revenue_stack",
            extra={"optimizer_engine": optimizer_engine},
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


@router.get(
    "/assets/{asset_id}/revenue-stack/latest",
    response_model=RevenueStackResponse,
)
def latest_asset_revenue_stack(asset_id: str):
    result = load_latest_asset_revenue_stack(asset_id)
    try:
        return attach_asset_provenance(
            result,
            get_asset(asset_id),
            artifact="latest_revenue_stack.json",
            kind="revenue_stack",
            extra={"optimizer_engine": result.get("optimizer_engine")},
        )
    except ValueError:
        return result


@router.post(
    "/assets/{asset_id}/revenue-stack/allocate",
    response_model=RevenueAllocationResponse,
)
def allocate_asset_revenue_stack(
    asset_id: str,
    optimizer_engine: str = "rule_based_v1",
    refresh_revenue_stack: bool = False,
):
    try:
        result = run_revenue_stack_allocation(
            asset_id=asset_id,
            optimizer_engine=optimizer_engine,
            refresh_revenue_stack=refresh_revenue_stack,
        )
        return attach_asset_provenance(
            result,
            get_asset(asset_id),
            artifact="latest_revenue_stack_allocation.json",
            kind="revenue_allocation",
            extra={"optimizer_engine": optimizer_engine},
        )
    except ValueError as error:
        return {
            "status": "not_found",
            "message": str(error),
        }
    except Exception as error:
        return {
            "status": "error",
            "message": f"Could not allocate revenue stack: {error}",
        }


@router.get(
    "/assets/{asset_id}/revenue-stack/allocation/latest",
    response_model=RevenueAllocationResponse,
)
def latest_asset_revenue_stack_allocation(asset_id: str):
    result = load_latest_revenue_stack_allocation(asset_id)
    try:
        return attach_asset_provenance(
            result,
            get_asset(asset_id),
            artifact="latest_revenue_stack_allocation.json",
            kind="revenue_allocation",
        )
    except ValueError:
        return result


@router.get(
    "/assets/{asset_id}/grid-fees/germany/sensitivity",
    response_model=GridFeeSensitivityResponse,
)
def asset_germany_grid_fee_sensitivity(asset_id: str):
    try:
        asset = get_asset(asset_id)
    except ValueError as error:
        return {
            "status": "not_found",
            "message": str(error),
        }

    latest_signal = load_asset_latest_signal(asset_id)
    dispatch_rows = []

    if latest_signal.get("status") == "ok":
        dispatch_rows = latest_signal.get("data", {}).get("dispatch", [])

    result = build_germany_grid_fee_sensitivity(
        asset=asset,
        dispatch_rows=dispatch_rows,
    )
    result["signal_status"] = latest_signal.get("status")

    return attach_asset_provenance(
        result,
        asset,
        kind="grid_fee_sensitivity",
        source_file=((latest_signal.get("data") or {}).get("metadata") or {}).get("forecast_file"),
    )


@router.get("/assets/{asset_id}/energy-origin/latest", response_model=ApiResponse)
def asset_energy_origin_ledger(asset_id: str):
    try:
        asset = get_asset(asset_id)
    except ValueError as error:
        return {
            "status": "not_found",
            "message": str(error),
        }

    latest_signal = load_asset_latest_signal(asset_id)

    if latest_signal.get("status") != "ok":
        return {
            "status": "not_found",
            "message": "No latest asset signal found. Run an asset signal first.",
            "asset_id": asset_id,
        }

    dispatch_rows = latest_signal.get("data", {}).get("dispatch", [])

    ledger = build_energy_origin_ledger(
        asset=asset,
        dispatch_rows=dispatch_rows,
    )
    return attach_asset_provenance(
        ledger,
        asset,
        kind="energy_origin_ledger",
        source_file=((latest_signal.get("data") or {}).get("metadata") or {}).get("forecast_file"),
    )


@router.get(
    "/assets/{asset_id}/hedging/revenue",
    response_model=HedgingRevenueResponse,
)
def asset_hedged_revenue_view(asset_id: str):
    try:
        asset = get_asset(asset_id)
    except ValueError as error:
        return {
            "status": "not_found",
            "message": str(error),
        }

    merchant_revenue = infer_latest_merchant_revenue(asset_id)

    result = build_hedged_revenue_view(
        asset=asset,
        merchant_revenue_eur=merchant_revenue,
    )
    return attach_asset_provenance(
        result,
        asset,
        kind="hedging_revenue",
        extra={"merchant_revenue_eur": merchant_revenue},
    )


def infer_latest_merchant_revenue(asset_id):
    revenue_stack = load_latest_asset_revenue_stack(asset_id)

    if revenue_stack.get("status") == "ok":
        return revenue_stack.get("total_estimated_revenue_eur", 0.0)

    latest_signal = load_asset_latest_signal(asset_id)

    if latest_signal.get("status") == "ok":
        return latest_signal.get("data", {}).get("summary", {}).get(
            "total_pnl_eur",
            0.0,
        )

    return 0.0



