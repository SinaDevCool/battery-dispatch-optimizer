from __future__ import annotations

import json
from typing import Any

from backend.data_environment import current_data_mode, normalize_data_mode


MODE_AWARE_TABLES = {
    "forecast_snapshots": "forecast_snapshot_id",
    "signal_runs": "signal_id",
    "revenue_stack_runs": "revenue_stack_id",
    "revenue_product_results": "revenue_product_id",
    "forecast_actual_runs": "forecast_actual_id",
    "business_decisions": "decision_id",
    "workflow_runs": "workflow_run_id",
    "execution_proposals": "execution_proposal_id",
    "execution_paper_trades": "paper_trade_id",
    "settlement_reconciliation_runs": "settlement_reconciliation_id",
    "asset_telemetry_snapshots": "telemetry_id",
    "execution_market_submissions": "market_submission_id",
    "execution_approvals": "approval_id",
    "automation_policies": "automation_policy_id",
    "automation_events": "automation_event_id",
    "official_api_evidence": "evidence_id",
}


def active_data_mode() -> str:
    return normalize_data_mode(current_data_mode())


def payload_data_mode(payload: dict[str, Any] | None, fallback: str | None = None) -> str:
    payload = payload or {}
    metadata = payload.get("metadata") or {}
    asset_value_context = payload.get("asset_value_context") or {}
    return normalize_data_mode(
        payload.get("data_mode")
        or metadata.get("data_mode")
        or asset_value_context.get("data_mode")
        or fallback
        or active_data_mode()
    )


def row_payload_data_mode(row: dict[str, Any], fallback: str | None = None) -> str:
    payload_json = row.get("payload_json")
    if not payload_json:
        return normalize_data_mode(row.get("data_mode") or fallback or active_data_mode())

    try:
        payload = json.loads(payload_json)
    except (TypeError, ValueError):
        payload = {}

    return payload_data_mode(payload, fallback=row.get("data_mode") or fallback)


def mode_where_clause(alias: str | None = None) -> str:
    prefix = f"{alias}." if alias else ""
    return f"({prefix}data_mode = ?)"


def mode_value(data_mode: str | None = None) -> str:
    return normalize_data_mode(data_mode or active_data_mode())


def add_data_mode_to_payload(payload: dict[str, Any], data_mode: str | None = None) -> dict[str, Any]:
    payload["data_mode"] = mode_value(data_mode)
    payload.setdefault("metadata", {})
    if isinstance(payload["metadata"], dict):
        payload["metadata"].setdefault("data_mode", mode_value(data_mode))
    return payload
