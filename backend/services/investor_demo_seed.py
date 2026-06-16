import json
from datetime import datetime, timezone
from typing import Any, Callable

from backend.api.routes.asset_signals import run_asset_latest_signal
from backend.api.routes.scenarios import (
    run_latest_asset_price_stress_tests,
    run_latest_asset_scenarios,
)
from backend.db.repositories.asset_repository import list_asset_records
from backend.execution.approval_workflow import approve_execution_proposal
from backend.execution.market_submission import run_demo_market_submission
from backend.execution.paper_trading import run_execution_paper_trade
from backend.execution.pretrade_proposal import build_execution_proposal
from backend.revenue.revenue_stack_runner import run_asset_revenue_stack
from backend.services.asset_cockpit_service import build_asset_cockpit
from backend.services.asset_workflow_service import run_asset_audited_workflow
from backend.services.demo_portfolio_service import seed_demo_forecasts
from backend.settlement.settlement_reconciliation import run_settlement_reconciliation
from backend.telemetry.asset_telemetry import save_demo_asset_telemetry


def seed_investor_demo(
    asset_id: str | None = None,
    optimizer_engine: str = "rule_based_v1",
):
    assets = select_demo_assets(asset_id)
    forecast_seed = safe_step("global_demo_forecasts", seed_demo_forecasts)
    results = [
        seed_investor_demo_asset(
            asset["asset_id"],
            optimizer_engine=optimizer_engine,
        )
        for asset in assets
    ]

    return {
        "status": classify_seed_status(results),
        "message": "Investor demo seed completed.",
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "optimizer_engine": optimizer_engine,
        "asset_count": len(results),
        "forecast_seed": forecast_seed,
        "assets": results,
        "summary": {
            "ready_asset_count": sum(
                1 for result in results if result["seed_status"] == "ready"
            ),
            "partial_asset_count": sum(
                1 for result in results if result["seed_status"] == "partial"
            ),
            "failed_asset_count": sum(
                1 for result in results if result["seed_status"] == "failed"
            ),
        },
    }


def seed_investor_demo_asset(asset_id: str, optimizer_engine: str):
    steps = {
        "signal": safe_step(
            "signal",
            run_asset_latest_signal,
            asset_id,
            optimizer_engine,
        ),
        "revenue_stack": safe_step(
            "revenue_stack",
            run_asset_revenue_stack,
            asset_id,
            optimizer_engine,
        ),
        "scenarios": safe_step(
            "scenarios",
            run_latest_asset_scenarios,
            asset_id,
        ),
        "stress": safe_step(
            "stress",
            run_latest_asset_price_stress_tests,
            asset_id,
        ),
        "workflow": safe_step(
            "workflow",
            run_asset_audited_workflow,
            asset_id,
            optimizer_engine,
        ),
        "execution_proposal": safe_step(
            "execution_proposal",
            build_execution_proposal,
            asset_id,
        ),
        "approval": safe_step("approval", approve_execution_proposal, asset_id),
        "paper_trade": safe_step(
            "paper_trade",
            run_execution_paper_trade,
            asset_id,
        ),
        "demo_submission": safe_step(
            "demo_submission",
            run_demo_market_submission,
            asset_id,
        ),
        "settlement": safe_step(
            "settlement",
            run_settlement_reconciliation,
            asset_id,
        ),
        "telemetry": safe_step("telemetry", save_demo_asset_telemetry, asset_id),
        "report": safe_step("report", generate_asset_report, asset_id),
        "cockpit": safe_step("cockpit", build_asset_cockpit, asset_id),
    }

    return {
        "asset_id": asset_id,
        "seed_status": classify_asset_seed_status(steps),
        "ready_for_demo": all(
            steps[step]["status"] == "ok"
            for step in [
                "signal",
                "revenue_stack",
                "scenarios",
                "stress",
                "workflow",
                "execution_proposal",
                "paper_trade",
                "settlement",
                "report",
            ]
        ),
        "steps": steps,
    }


def select_demo_assets(asset_id: str | None = None):
    assets = list_asset_records()
    if asset_id:
        selected = [asset for asset in assets if asset.get("asset_id") == asset_id]
        if not selected:
            raise ValueError(f"Unknown asset_id={asset_id}.")
        return selected

    return [
        asset
        for asset in assets
        if asset.get("data_mode") == "mock" or asset.get("data_source") == "local_seed_demo"
    ]


def generate_asset_report(asset_id: str):
    from backend.api.routes.reports import generate_asset_monthly_report

    return generate_asset_monthly_report(asset_id)


def safe_step(label: str, fn: Callable[..., Any], *args):
    try:
        payload = fn(*args)
    except Exception as error:
        return {
            "status": "error",
            "message": f"{label} failed: {error}",
        }

    return {
        "status": normalize_payload_status(payload),
        "summary": summarize_payload(payload),
    }


def normalize_payload_status(payload: Any):
    if not isinstance(payload, dict):
        return "ok"

    status = str(payload.get("status") or "ok")
    if status in {
        "approved",
        "completed",
        "demo_settled",
        "draft",
        "ok",
        "paper_reconciled",
        "settled",
        "submitted",
    }:
        return "ok"

    return status


def summarize_payload(payload: Any):
    if not isinstance(payload, dict):
        return str(payload)

    keys = [
        "status",
        "message",
        "asset_id",
        "report_name",
        "viewer_route",
        "workflow_run_id",
        "execution_proposal_id",
        "paper_trade_id",
        "settlement_id",
        "signal_file",
    ]
    summary = {key: payload.get(key) for key in keys if payload.get(key) is not None}

    if "workflow_run" in payload and isinstance(payload["workflow_run"], dict):
        summary["workflow_run_id"] = payload["workflow_run"].get("workflow_run_id")
    if "paper_trade" in payload and isinstance(payload["paper_trade"], dict):
        summary["paper_trade_id"] = payload["paper_trade"].get("paper_trade_id")
    if "settlement" in payload and isinstance(payload["settlement"], dict):
        summary["settlement_id"] = payload["settlement"].get("settlement_id")
    if "proposal" in payload and isinstance(payload["proposal"], dict):
        summary["execution_proposal_id"] = payload["proposal"].get(
            "execution_proposal_id"
        )

    return summary or {"keys": sorted(payload.keys())[:12]}


def classify_asset_seed_status(steps: dict[str, dict[str, Any]]):
    critical_steps = [
        "signal",
        "revenue_stack",
        "scenarios",
        "stress",
        "workflow",
        "execution_proposal",
        "paper_trade",
        "settlement",
        "report",
    ]
    critical_ok = [
        steps[step]["status"] == "ok"
        for step in critical_steps
    ]
    if all(critical_ok):
        return "ready"
    if any(critical_ok):
        return "partial"
    return "failed"


def classify_seed_status(results: list[dict[str, Any]]):
    if not results:
        return "not_found"
    if all(result["seed_status"] == "ready" for result in results):
        return "ok"
    if any(result["seed_status"] in {"ready", "partial"} for result in results):
        return "partial"
    return "error"


def seed_investor_demo_json(asset_id: str | None = None, optimizer_engine: str = "rule_based_v1"):
    return json.dumps(
        seed_investor_demo(asset_id=asset_id, optimizer_engine=optimizer_engine),
        indent=2,
        default=str,
    )
