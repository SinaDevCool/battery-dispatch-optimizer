from datetime import datetime

from backend.execution.automation_policy import market_allowed_by_policy
from backend.execution.market_adapters.registry import get_asset_market_adapter_status
from backend.execution.market_connector_readiness import market_connector_readiness
from backend.execution.market_lifecycle import get_market_lifecycle


ROUTE_GATE_REQUIREMENTS = {
    "epex_day_ahead": {
        "label": "EPEX day-ahead auction",
        "market_family": "epex",
        "paper_controls": [
            "preview_adapter",
            "gate_closure_scheduler",
            "auction_order_validation",
        ],
        "supervised_controls": [
            "market_credentials",
            "member_or_broker_route",
            "settlement_account_mapping",
        ],
        "live_controls": [
            "order_submission_api",
            "auction_award_import",
            "post_trade_reconciliation",
        ],
        "risk_controls": [
            "price_limit_validation",
            "volume_limit_validation",
            "negative_price_guardrail",
        ],
    },
    "epex_intraday_auction": {
        "label": "EPEX intraday auction",
        "market_family": "epex",
        "paper_controls": [
            "preview_adapter",
            "auction_product_mapping",
            "gate_closure_scheduler",
        ],
        "supervised_controls": [
            "market_credentials",
            "order_submission_api",
            "auction_award_import",
        ],
        "live_controls": [
            "settlement_account_mapping",
            "post_trade_reconciliation",
        ],
        "risk_controls": [
            "price_limit_validation",
            "volume_limit_validation",
        ],
    },
    "epex_intraday_continuous": {
        "label": "EPEX intraday continuous",
        "market_family": "epex",
        "paper_controls": [
            "preview_adapter",
            "continuous_order_validation",
            "partial_fill_policy",
        ],
        "supervised_controls": [
            "market_credentials",
            "live_order_book",
            "cancel_replace_controls",
        ],
        "live_controls": [
            "partial_fill_handler",
            "liquidity_and_spread_limits",
            "intraday_rebalancing_supervisor",
        ],
        "risk_controls": [
            "spread_limit_validation",
            "position_limit_validation",
            "cancel_replace_audit",
        ],
    },
    "regelleistung_fcr": {
        "label": "Regelleistung FCR",
        "market_family": "ancillary",
        "paper_controls": [
            "preview_adapter",
            "symmetric_capacity_validation",
            "availability_profile",
        ],
        "supervised_controls": [
            "market_credentials",
            "asset_prequalification",
            "capacity_award_import",
        ],
        "live_controls": [
            "availability_telemetry",
            "tso_settlement_mapping",
            "delivery_nonperformance_guardrail",
        ],
        "risk_controls": [
            "minimum_capacity_validation",
            "availability_obligation_check",
            "activation_exposure_limit",
        ],
    },
    "regelleistung_afrr": {
        "label": "Regelleistung aFRR",
        "market_family": "ancillary",
        "paper_controls": [
            "preview_adapter",
            "capacity_reservation_controls",
            "activation_profile",
        ],
        "supervised_controls": [
            "market_credentials",
            "asset_prequalification",
            "activation_telemetry",
        ],
        "live_controls": [
            "energy_activation_accounting",
            "tso_settlement_mapping",
            "availability_telemetry",
        ],
        "risk_controls": [
            "reserve_capacity_limit",
            "activation_energy_limit",
            "availability_obligation_check",
        ],
    },
    "regelleistung_mfrr": {
        "label": "Regelleistung mFRR",
        "market_family": "ancillary",
        "paper_controls": [
            "preview_adapter",
            "manual_activation_workflow",
            "capacity_reservation_controls",
        ],
        "supervised_controls": [
            "market_credentials",
            "asset_prequalification",
            "imbalance_settlement_mapping",
        ],
        "live_controls": [
            "activation_workflow_audit",
            "tso_settlement_mapping",
            "availability_telemetry",
        ],
        "risk_controls": [
            "manual_activation_readiness",
            "imbalance_exposure_limit",
            "availability_obligation_check",
        ],
    },
}


def build_market_adapter_readiness_gate(asset_id, country="Germany"):
    adapter_status = get_asset_market_adapter_status(asset_id)
    connector_readiness = market_connector_readiness(country=country)
    adapters = {
        adapter.get("adapter_id"): adapter
        for adapter in adapter_status.get("adapters", [])
    }
    connectors = {
        connector.get("adapter_id"): connector
        for connector in connector_readiness.get("integrations", [])
    }
    route_gates = [
        build_route_gate(
            asset_id=asset_id,
            adapter_id=adapter_id,
            adapter=adapters.get(adapter_id, {}),
            connector=connectors.get(adapter_id, {}),
        )
        for adapter_id in ROUTE_GATE_REQUIREMENTS
    ]
    summary = summarize_route_gates(route_gates)

    return {
        "status": "ok",
        "asset_id": asset_id,
        "country": country,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "gate_status": classify_portfolio_gate(summary),
        "summary": summary,
        "route_gates": route_gates,
        "recommended_actions": build_recommended_actions(route_gates),
        "evidence": {
            "market_adapter_status": adapter_status.get("market_adapter_status"),
            "connector_status": connector_readiness.get("connector_status"),
            "connector_summary": connector_readiness.get("summary", {}),
        },
    }


def build_route_gate(asset_id, adapter_id, adapter, connector):
    requirements = ROUTE_GATE_REQUIREMENTS[adapter_id]
    lifecycle = get_market_lifecycle(adapter_id)
    checks = [
        build_check(
            check="policy_allowed",
            label="Automation policy",
            passed=market_allowed_by_policy(asset_id=asset_id, adapter_id=adapter_id),
            blocking_level="paper",
            message="Automation policy allows this route."
            if market_allowed_by_policy(asset_id=asset_id, adapter_id=adapter_id)
            else "Automation policy disables this route.",
        ),
        build_check(
            check="preview_available",
            label="Preview adapter",
            passed=adapter.get("connection_status") in ["available", "preview_available"],
            blocking_level="paper",
            message="Preview adapter can generate route evidence."
            if adapter.get("connection_status") in ["available", "preview_available"]
            else "Preview adapter is not available.",
        ),
        build_check(
            check="credentials_configured",
            label="Market credentials",
            passed=not connector.get("missing_credentials"),
            blocking_level="supervised",
            message="Market credentials are configured."
            if not connector.get("missing_credentials")
            else "Market credentials are missing: "
            + ", ".join(connector.get("missing_credentials", [])),
        ),
        build_check(
            check="live_submission_adapter",
            label="Live submission adapter",
            passed=bool(connector.get("live_submission") or adapter.get("live_submission")),
            blocking_level="live",
            message="Live submission adapter is available."
            if bool(connector.get("live_submission") or adapter.get("live_submission"))
            else "Live submission adapter is not connected yet.",
        ),
        build_check(
            check="trading_clock",
            label="Trading clock",
            passed=lifecycle.get("trading_clock_status") not in ["closed"],
            blocking_level="paper",
            message=lifecycle.get("next_deadline_action")
            or "Trading clock evidence is available.",
        ),
    ]
    checks.extend(control_checks(requirements, connector))
    blocking_levels = {
        check["blocking_level"]
        for check in checks
        if check.get("status") == "blocked"
    }
    route_status = classify_route_gate(checks)

    return {
        "adapter_id": adapter_id,
        "adapter_name": adapter.get("adapter_name") or requirements["label"],
        "automation_lane": lifecycle.get("automation_lane"),
        "blocking_levels": sorted(blocking_levels),
        "checks": checks,
        "gate_closure_label": lifecycle.get("gate_closure_label"),
        "gate_status": route_status,
        "live_submission": bool(adapter.get("live_submission")),
        "market_family": requirements["market_family"],
        "missing_controls": missing_controls(checks),
        "next_action": next_route_action(route_status, checks, lifecycle, connector),
        "order_style": lifecycle.get("order_style"),
        "readiness_score": route_score(checks),
        "required_controls": {
            "paper": requirements["paper_controls"],
            "supervised": requirements["supervised_controls"],
            "live": requirements["live_controls"],
            "risk": requirements["risk_controls"],
        },
        "settlement_basis": settlement_basis(adapter_id),
        "trading_clock_status": lifecycle.get("trading_clock_status"),
    }


def control_checks(requirements, connector):
    missing = set(connector.get("missing_controls", []))
    checks = []

    for control in requirements["paper_controls"]:
        checks.append(control_check(control, control not in missing, "paper"))

    for control in requirements["supervised_controls"]:
        checks.append(control_check(control, control not in missing, "supervised"))

    for control in requirements["live_controls"]:
        checks.append(control_check(control, control not in missing, "live"))

    for control in requirements["risk_controls"]:
        checks.append(control_check(control, True, "risk"))

    return dedupe_checks(checks)


def control_check(control, passed, blocking_level):
    return build_check(
        check=control,
        label=control.replace("_", " ").title(),
        passed=passed,
        blocking_level=blocking_level,
        message=(
            f"{control.replace('_', ' ')} is available."
            if passed
            else f"{control.replace('_', ' ')} is required before this route can advance."
        ),
    )


def build_check(check, label, passed, blocking_level, message):
    return {
        "check": check,
        "label": label,
        "status": "passed" if passed else "blocked",
        "blocking_level": blocking_level,
        "message": message,
    }


def classify_route_gate(checks):
    blocked = [
        check.get("blocking_level")
        for check in checks
        if check.get("status") == "blocked"
    ]

    if "paper" in blocked:
        return "blocked"

    if "supervised" in blocked:
        return "paper_only"

    if "live" in blocked:
        return "supervised_ready"

    return "live_ready"


def route_score(checks):
    if not checks:
        return 0.0

    return round(
        sum(100 if check.get("status") == "passed" else 0 for check in checks)
        / len(checks),
        1,
    )


def summarize_route_gates(route_gates):
    return {
        "route_count": len(route_gates),
        "blocked_count": count_by_status(route_gates, "blocked"),
        "paper_only_count": count_by_status(route_gates, "paper_only"),
        "supervised_ready_count": count_by_status(route_gates, "supervised_ready"),
        "live_ready_count": count_by_status(route_gates, "live_ready"),
        "epex_ready_count": count_ready_by_family(route_gates, "epex"),
        "ancillary_ready_count": count_ready_by_family(route_gates, "ancillary"),
        "average_readiness_score": round(
            sum(route.get("readiness_score", 0) for route in route_gates)
            / max(len(route_gates), 1),
            1,
        ),
    }


def classify_portfolio_gate(summary):
    if summary.get("live_ready_count"):
        return "live_ready_route_available"

    if summary.get("supervised_ready_count"):
        return "supervised_ready_route_available"

    if summary.get("paper_only_count"):
        return "paper_only_routes_available"

    return "blocked"


def build_recommended_actions(route_gates):
    actions = []
    ranked = sorted(
        route_gates,
        key=lambda route: (route_status_rank(route.get("gate_status")), route.get("readiness_score", 0)),
        reverse=True,
    )

    for route in ranked:
        if route.get("gate_status") == "live_ready":
            actions.append(f"{route['adapter_name']}: run a limited live submission drill with strict caps.")
        elif route.get("gate_status") == "supervised_ready":
            actions.append(f"{route['adapter_name']}: use supervised submission after approval.")
        elif route.get("gate_status") == "paper_only":
            actions.append(f"{route['adapter_name']}: keep paper trading and clear credential/live connector gaps.")
        else:
            actions.append(f"{route['adapter_name']}: {route.get('next_action')}")

    return dedupe(actions)[:8]


def next_route_action(route_status, checks, lifecycle, connector):
    if route_status == "live_ready":
        return lifecycle.get("next_deadline_action") or "Run live submission drill."

    if route_status == "supervised_ready":
        return "Run supervised submission after proposal approval."

    blocked = [check for check in checks if check.get("status") == "blocked"]
    if blocked:
        return blocked[0].get("message")

    return connector.get("next_integration_action") or "Monitor route readiness."


def missing_controls(checks):
    return [
        check.get("check")
        for check in checks
        if check.get("status") == "blocked"
    ]


def settlement_basis(adapter_id):
    if adapter_id == "epex_intraday_continuous":
        return "energy_partial_fill"

    if adapter_id.startswith("epex_"):
        return "energy_auction_award"

    return "reserve_capacity_award"


def count_by_status(route_gates, status):
    return len([route for route in route_gates if route.get("gate_status") == status])


def count_ready_by_family(route_gates, family):
    return len(
        [
            route
            for route in route_gates
            if route.get("market_family") == family
            and route.get("gate_status") in ["paper_only", "supervised_ready", "live_ready"]
        ]
    )


def route_status_rank(status):
    return {
        "blocked": 0,
        "paper_only": 1,
        "supervised_ready": 2,
        "live_ready": 3,
    }.get(status, 0)


def dedupe_checks(checks):
    seen = set()
    result = []

    for check in checks:
        key = check.get("check")
        if key in seen:
            continue

        seen.add(key)
        result.append(check)

    return result


def dedupe(items):
    seen = set()
    result = []

    for item in items:
        if not item or item in seen:
            continue

        seen.add(item)
        result.append(item)

    return result



