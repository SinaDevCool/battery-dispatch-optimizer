from datetime import datetime

from backend.assets.asset_loader import get_asset
from backend.db.repositories.forecast_repository import get_latest_forecast_snapshot
from backend.db.repositories.workflow_repository import (
    get_latest_workflow_run,
    get_workflow_run,
    list_workflow_runs,
    save_workflow_run,
)
from backend.revenue.revenue_stack_runner import run_asset_revenue_stack
from backend.services.asset_dispatch_service import (
    add_asset_dispatch_validation,
    build_asset_signal_metadata,
    dispatch_asset,
)
from backend.services.asset_signal_store import save_asset_signal
from backend.services.business_decision_service import build_business_decision
from backend.services.signal_service import add_signal_metadata


def run_asset_audited_workflow(asset_id, optimizer_engine="rule_based_v1"):
    started_at = datetime.now().isoformat(timespec="seconds")
    asset = get_asset(asset_id)

    asset_dispatch_result = dispatch_asset(
        asset=asset,
        optimizer_engine=optimizer_engine,
    )
    dispatch_result = asset_dispatch_result.dispatch_result

    forecast_snapshot = get_latest_forecast_snapshot(
        forecast_file=asset_dispatch_result.forecast_file,
    )

    signal_result = add_signal_metadata(
        signal_result=dispatch_result.signal_result,
        source=resolve_forecast_provider(forecast_snapshot),
        forecast_model=resolve_forecast_model(forecast_snapshot),
        target_date=resolve_target_date(forecast_snapshot),
        forecast_file=asset_dispatch_result.forecast_file,
        extra_metadata=build_asset_signal_metadata(asset_dispatch_result),
    )
    signal_result = add_asset_dispatch_validation(
        signal_result=signal_result,
        asset_dispatch_result=asset_dispatch_result,
    )

    saved_signal = save_asset_signal(
        signal_result=signal_result,
        asset_id=asset_id,
        target_date=resolve_target_date(forecast_snapshot),
    )

    revenue_stack = run_asset_revenue_stack(
        asset_id=asset_id,
        optimizer_engine=optimizer_engine,
    )
    decision = build_business_decision(asset_id)
    completed_at = datetime.now().isoformat(timespec="seconds")
    summary = signal_result.get("summary", {})

    workflow_run = {
        "asset_id": asset_id,
        "status": "ok",
        "started_at": started_at,
        "completed_at": completed_at,
        "optimizer_engine": optimizer_engine,
        "forecast_snapshot_id": (
            forecast_snapshot or {}
        ).get("forecast_snapshot_id"),
        "signal_id": saved_signal["signal_id"],
        "revenue_stack_id": revenue_stack.get("revenue_stack_id"),
        "decision_id": decision.get("decision_id"),
        "target_date": resolve_target_date(forecast_snapshot),
        "forecast_provider": resolve_forecast_provider(forecast_snapshot),
        "forecast_model": resolve_forecast_model(forecast_snapshot),
        "recommendation_status": decision.get("recommendation_status"),
        "expected_pnl_eur": decision.get("expected_pnl_eur"),
        "signal_summary": summary,
        "revenue_summary": {
            "total_estimated_revenue_eur": revenue_stack.get(
                "total_estimated_revenue_eur"
            ),
            "estimated_product_count": revenue_stack.get(
                "estimated_product_count"
            ),
            "product_count": revenue_stack.get("product_count"),
        },
        "decision": decision,
        "validation": signal_result.get("validation", {}),
        "assumption_risk_flags": asset_dispatch_result.assumption_risk_flags,
    }

    workflow_run_id = save_workflow_run(workflow_run)
    workflow_run["workflow_run_id"] = workflow_run_id

    return {
        "status": "ok",
        "message": "Audited asset workflow completed successfully.",
        "asset_id": asset_id,
        "workflow_run": workflow_run,
    }


def latest_asset_workflow_run(asset_id):
    run = get_latest_workflow_run(asset_id)

    if run is None:
        return {
            "status": "not_found",
            "message": f"No workflow run found for asset: {asset_id}",
            "asset_id": asset_id,
            "workflow_run": None,
        }

    return {
        "status": "ok",
        "asset_id": asset_id,
        "workflow_run": run["payload"],
    }


def asset_workflow_run_history(asset_id, limit=25):
    return {
        "status": "ok",
        "asset_id": asset_id,
        "workflow_runs": list_workflow_runs(asset_id=asset_id, limit=limit),
    }


def asset_workflow_run_detail(asset_id, workflow_run_id):
    run = get_workflow_run(workflow_run_id)

    if run is None or run["asset_id"] != asset_id:
        return {
            "status": "not_found",
            "message": f"Workflow run not found: {workflow_run_id}",
            "asset_id": asset_id,
            "workflow_run": None,
        }

    return {
        "status": "ok",
        "asset_id": asset_id,
        "workflow_run": run["payload"],
    }


def resolve_forecast_provider(forecast_snapshot):
    if forecast_snapshot:
        return forecast_snapshot.get("forecast_provider") or "local_saved_forecast"

    return "asset_forecast_file"


def resolve_forecast_model(forecast_snapshot):
    if forecast_snapshot:
        return forecast_snapshot.get("forecast_model") or "asset_forecast_file"

    return "asset_forecast_file"


def resolve_target_date(forecast_snapshot):
    if forecast_snapshot:
        return forecast_snapshot.get("target_date")

    return None



