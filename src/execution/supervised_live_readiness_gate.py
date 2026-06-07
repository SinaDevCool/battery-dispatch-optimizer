from datetime import datetime

from src.execution.credential_readiness import get_route_credential_readiness
from src.execution.live_adapter_handshake import get_route_handshake_readiness
from src.execution.market_adapters.registry import list_market_adapters
from src.execution.market_connector_contract import get_connector_contract_summary
from src.execution.market_connector_sandbox_certification import (
    get_connector_sandbox_certification,
)
from src.execution.market_lifecycle import enrich_with_market_lifecycle


ROUTE_GATE_REQUIREMENTS = {
    "epex_day_ahead": {
        "credential_keys": ["EPEX_API_KEY", "EPEX_MEMBER_ID"],
        "required_controls": [
            "member_or_broker_route",
            "order_submission_api",
            "gate_closure_scheduler",
            "settlement_account_mapping",
            "human_approval_policy",
        ],
    },
    "epex_intraday_auction": {
        "credential_keys": ["EPEX_API_KEY", "EPEX_MEMBER_ID"],
        "required_controls": [
            "auction_product_mapping",
            "gate_closure_scheduler",
            "order_submission_api",
            "auction_award_import",
            "settlement_account_mapping",
            "human_approval_policy",
        ],
    },
    "epex_intraday_continuous": {
        "credential_keys": ["EPEX_API_KEY", "EPEX_MEMBER_ID"],
        "required_controls": [
            "live_order_book",
            "partial_fill_handler",
            "cancel_replace_controls",
            "liquidity_and_spread_limits",
            "intraday_rebalancing_supervisor",
            "human_approval_policy",
        ],
    },
    "regelleistung_fcr": {
        "credential_keys": ["REGELLEISTUNG_API_KEY", "TSO_PARTICIPANT_ID"],
        "required_controls": [
            "asset_prequalification",
            "symmetric_capacity_validation",
            "availability_telemetry",
            "capacity_award_import",
            "tso_settlement_mapping",
            "human_approval_policy",
        ],
    },
    "regelleistung_afrr": {
        "credential_keys": ["REGELLEISTUNG_API_KEY", "TSO_PARTICIPANT_ID"],
        "required_controls": [
            "asset_prequalification",
            "activation_telemetry",
            "capacity_reservation_controls",
            "energy_activation_accounting",
            "tso_settlement_mapping",
            "human_approval_policy",
        ],
    },
    "regelleistung_mfrr": {
        "credential_keys": ["REGELLEISTUNG_API_KEY", "TSO_PARTICIPANT_ID"],
        "required_controls": [
            "asset_prequalification",
            "manual_activation_workflow",
            "capacity_reservation_controls",
            "imbalance_settlement_mapping",
            "tso_settlement_mapping",
            "human_approval_policy",
        ],
    },
}


def build_supervised_live_readiness_gate(country="Germany"):
    gates = [
        evaluate_route_supervised_live_gate(adapter)
        for adapter in list_market_adapters(country=country)
        if adapter["adapter_id"] in ROUTE_GATE_REQUIREMENTS
    ]
    summary = summarize_supervised_live_gates(gates)
    return {
        "status": "ok",
        "country": country,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "supervised_live_gate_status": classify_portfolio_gate(summary),
        "summary": summary,
        "routes": gates,
        "recommended_actions": build_gate_recommended_actions(gates),
    }


def get_route_supervised_live_gate(adapter_id):
    adapter = next(
        (
            item
            for item in list_market_adapters(country="Germany")
            if item["adapter_id"] == adapter_id
        ),
        None,
    )
    if not adapter or adapter_id not in ROUTE_GATE_REQUIREMENTS:
        return {}

    return evaluate_route_supervised_live_gate(adapter)


def evaluate_route_supervised_live_gate(adapter):
    adapter_id = adapter["adapter_id"]
    requirements = ROUTE_GATE_REQUIREMENTS[adapter_id]
    contract = get_connector_contract_summary(adapter_id)
    sandbox = get_connector_sandbox_certification(adapter_id)
    lifecycle = enrich_with_market_lifecycle({**adapter})
    credential_readiness = get_route_credential_readiness(adapter_id)
    handshake_readiness = get_route_handshake_readiness(adapter_id)
    missing_credentials = credential_readiness.get("missing_env_keys", [])

    checks = [
        gate_check(
            "credentials_configured",
            not missing_credentials,
            "Exchange or TSO credentials are configured.",
            credential_readiness.get("onboarding_next_action")
            or f"Configure {', '.join(missing_credentials)}.",
            context={
                "missing_credentials": credential_readiness.get(
                    "missing_credentials",
                    [],
                ),
                "missing_env_keys": missing_credentials,
            },
        ),
        gate_check(
            "connector_contract_complete",
            not contract.get("missing_methods"),
            "Connector method contract is complete.",
            "Complete missing connector methods before supervised live trading.",
            context={"missing_methods": contract.get("missing_methods", [])},
        ),
        gate_check(
            "sandbox_certified_for_paper",
            bool(sandbox.get("certified_for_paper")),
            "Synthetic connector method chain passes.",
            "Rerun and fix sandbox connector certification.",
        ),
        gate_check(
            "live_adapter_handshake_ready",
            bool(handshake_readiness.get("route_handshake_ready")),
            "Dry-run live adapter handshake evidence is ready and no order submission is performed.",
            handshake_readiness.get("route_handshake_next_action")
            or "Run dry-run handshakes for market, EMS, data, and settlement adapters.",
            context={
                "route_handshake_status": handshake_readiness.get(
                    "route_handshake_status"
                ),
                "route_handshake_targets": handshake_readiness.get(
                    "route_handshake_targets",
                    [],
                ),
                "route_handshake_blockers": handshake_readiness.get(
                    "route_handshake_blockers",
                    [],
                ),
            },
        ),
        gate_check(
            "live_adapter_enabled",
            bool(adapter.get("live_submission")),
            "Live adapter wiring is enabled.",
            "Implement live adapter wiring but keep human gate mandatory.",
        ),
        gate_check(
            "market_lifecycle_configured",
            bool(lifecycle.get("market_lifecycle")),
            "Market lifecycle and gate closure metadata are configured.",
            "Configure market lifecycle, gate closure, and product timing.",
        ),
        gate_check(
            "human_approval_policy_active",
            "human_approval_policy" in requirements["required_controls"],
            "Human approval is required before supervised submission.",
            "Add human approval policy for supervised trading.",
        ),
        gate_check(
            "settlement_reference_mapped",
            "settlement_statement_id" in contract.get("raw_reference_fields", []),
            "Settlement statement reference is mapped in the connector contract.",
            "Map settlement statement identifiers for reconciliation evidence.",
        ),
        gate_check(
            "audit_capture_available",
            int(sandbox.get("audit_event_count", 0)) >= len(
                sandbox.get("sandbox_results", [])
            ),
            "Connector method calls emit audit events.",
            "Ensure every connector method writes an audit event.",
        ),
    ]
    passed_count = len([check for check in checks if check["status"] == "passed"])
    blockers = [
        check["required_action"]
        for check in checks
        if check["status"] == "blocked"
    ]
    gate_status = classify_route_gate(
        checks=checks,
        paper_certified=bool(sandbox.get("certified_for_paper")),
    )

    return {
        "adapter_id": adapter_id,
        "adapter_name": adapter.get("adapter_name"),
        "venue": adapter.get("venue"),
        "market_segment": adapter.get("market_segment"),
        "supervised_live_gate_status": gate_status,
        "route_credential_status": credential_readiness.get("credential_status"),
        "route_missing_credentials": credential_readiness.get("missing_credentials", []),
        "route_missing_env_keys": missing_credentials,
        "route_onboarding_next_action": credential_readiness.get(
            "onboarding_next_action"
        ),
        "route_handshake_status": handshake_readiness.get("route_handshake_status"),
        "route_handshake_targets": handshake_readiness.get(
            "route_handshake_targets",
            [],
        ),
        "route_handshake_blockers": handshake_readiness.get(
            "route_handshake_blockers",
            [],
        ),
        "route_handshake_next_action": handshake_readiness.get(
            "route_handshake_next_action"
        ),
        "route_handshake_ready": handshake_readiness.get("route_handshake_ready"),
        "supervised_live_candidate": gate_status == "supervised_live_candidate",
        "paper_ready_live_blocked": gate_status == "paper_ready_live_blocked",
        "supervised_live_blockers": blockers,
        "supervised_live_next_action": next_gate_action(gate_status, checks),
        "gate_check_count": len(checks),
        "gate_passed_count": passed_count,
        "gate_score": round(passed_count / max(len(checks), 1) * 100, 1),
        "supervised_live_checks": checks,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
    }


def gate_check(check, passed, passed_message, blocked_message, context=None):
    return {
        "check": check,
        "status": "passed" if passed else "blocked",
        "message": passed_message if passed else blocked_message,
        "required_action": None if passed else blocked_message,
        "context": context or {},
    }


def classify_route_gate(checks, paper_certified):
    if all(check["status"] == "passed" for check in checks):
        return "supervised_live_candidate"

    if paper_certified:
        return "paper_ready_live_blocked"

    return "blocked"


def next_gate_action(gate_status, checks):
    if gate_status == "supervised_live_candidate":
        return "Run supervised live dry run with human approval, strict limits, and audit capture."

    first_blocker = next(
        (check for check in checks if check["status"] == "blocked"),
        None,
    )
    if first_blocker:
        return first_blocker["required_action"]

    return "Review supervised live gate evidence."


def summarize_supervised_live_gates(gates):
    return {
        "supervised_live_gate_count": len(gates),
        "supervised_live_candidate_count": len(
            [
                gate
                for gate in gates
                if gate.get("supervised_live_candidate")
            ]
        ),
        "paper_ready_live_blocked_count": len(
            [
                gate
                for gate in gates
                if gate.get("paper_ready_live_blocked")
            ]
        ),
        "supervised_live_blocked_count": len(
            [
                gate
                for gate in gates
                if gate.get("supervised_live_gate_status") == "blocked"
            ]
        ),
        "average_gate_score": round(
            sum(gate.get("gate_score", 0) for gate in gates)
            / max(len(gates), 1),
            1,
        ),
    }


def classify_portfolio_gate(summary):
    if summary.get("supervised_live_candidate_count"):
        return "supervised_live_candidate_available"

    if summary.get("paper_ready_live_blocked_count"):
        return "paper_ready_live_blocked"

    return "supervised_live_blocked"


def build_gate_recommended_actions(gates):
    return [
        f"{gate['adapter_name']}: {gate['supervised_live_next_action']}"
        for gate in gates
        if not gate.get("supervised_live_candidate")
    ][:8]
