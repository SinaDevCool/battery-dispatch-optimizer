from datetime import datetime

from backend.backtesting.forecast_actual.forecast_confidence import (
    build_forecast_confidence,
)
from backend.execution.automation_control import automation_control_status
from backend.execution.market_connector_readiness import market_connector_readiness
from backend.execution.multi_market_allocator import build_multi_market_allocation
from backend.execution.strategy_intent import build_strategy_intent


def build_live_trading_readiness(asset_id, country="Germany"):
    allocation = build_multi_market_allocation(asset_id=asset_id)
    control = automation_control_status(asset_id=asset_id, allocation=allocation)
    connectors = market_connector_readiness(country=country, asset_id=asset_id)
    confidence = build_forecast_confidence(asset_id)
    intent = build_strategy_intent(asset_id)

    route_rows = build_route_readiness_rows(
        asset_id=asset_id,
        allocation=allocation,
        connectors=connectors,
        control=control,
        country=country,
    )
    route_summary = summarize_routes(route_rows)
    score = score_go_live_readiness(
        allocation=allocation,
        confidence=confidence,
        connectors=connectors,
        control=control,
        route_summary=route_summary,
    )
    recommendation = classify_mode_recommendation(
        control=control,
        route_summary=route_summary,
        score=score,
    )
    runbook = build_go_live_runbook(
        control=control,
        route_rows=route_rows,
        route_summary=route_summary,
    )

    return {
        "status": "ok",
        "asset_id": asset_id,
        "country": country,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "live_trading_readiness_score": score,
        "mode_recommendation": recommendation,
        "go_live_status": classify_go_live_status(recommendation),
        "next_best_action": next_best_action(control=control, runbook=runbook),
        "route_readiness": route_rows,
        "runbook": runbook,
        "summary": {
            **route_summary,
            "automation_mode": control.get("automation_mode"),
            "control_blocker_count": len(control.get("blockers", [])),
            "forecast_confidence_score": confidence.get("confidence_score"),
            "forecast_confidence_band": confidence.get("confidence_band"),
            "handshake_ready_count": (connectors.get("summary") or {}).get(
                "handshake_ready_count",
                0,
            ),
            "handshake_target_count": (connectors.get("summary") or {}).get(
                "handshake_target_count",
                0,
            ),
            "strategy_mode": intent.get("strategy_mode"),
        },
        "evidence": {
            "automation_control": {
                "automation_mode": control.get("automation_mode"),
                "live_trading_allowed": control.get("live_trading_allowed"),
                "next_automation_action": control.get("next_automation_action"),
                "readiness_score": control.get("readiness_score"),
                "readiness_status": control.get("readiness_status"),
            },
            "allocation": allocation.get("summary", {}),
            "connector_readiness": connectors.get("summary", {}),
            "strategy_intent": {
                "strategy_mode": intent.get("strategy_mode"),
                "confidence": intent.get("confidence", {}),
            },
        },
    }


def build_route_readiness_rows(asset_id, allocation, connectors, control, country):
    connector_by_adapter = {
        row.get("adapter_id"): row
        for row in connectors.get("integrations", [])
    }
    control_blockers = control.get("blockers", [])
    control_live_allowed = bool(control.get("live_trading_allowed"))
    control_supervised_allowed = bool(control.get("supervised_trading_allowed"))
    control_paper_allowed = bool(control.get("paper_trading_allowed"))

    rows = []
    for route in allocation.get("allocation", []):
        connector = connector_by_adapter.get(route.get("adapter_id"), {})
        blockers = route_blockers(route=route, connector=connector)
        mode = classify_route_mode(
            blockers=blockers,
            connector=connector,
            control_live_allowed=control_live_allowed,
            control_paper_allowed=control_paper_allowed,
            control_supervised_allowed=control_supervised_allowed,
            route=route,
        )
        score = score_route(route=route, connector=connector, blockers=blockers, mode=mode)
        next_action = route_next_action(
            blockers=blockers,
            control_blockers=control_blockers,
            mode=mode,
            route=route,
        )
        unlock_action = build_route_unlock_action(
            asset_id=asset_id,
            blockers=blockers,
            connector=connector,
            country=country,
            mode=mode,
            next_action=next_action,
            route=route,
        )
        rows.append(
            {
                "adapter_id": route.get("adapter_id"),
                "market_name": route.get("market_name"),
                "venue": route.get("venue"),
                "market_segment": route.get("market_segment"),
                "commercial_product_id": route.get("commercial_product_id"),
                "expected_revenue_eur": route.get("expected_revenue_eur"),
                "allocated_power_mw": route.get("allocated_power_mw"),
                "mode": mode,
                "readiness_score": score,
                "recommendation_status": route.get("recommendation_status"),
                "live_submission": bool(route.get("live_submission")),
                "connector_tier": route.get("connector_readiness_tier")
                or connector.get("production_readiness_tier"),
                "market_gate_status": route.get("market_gate_status"),
                "trading_clock_status": route.get("trading_clock_status"),
                "next_gate_closure_at": route.get("next_gate_closure_at"),
                "blocker_count": len(blockers),
                "blocking_reasons": blockers[:5],
                "next_action": next_action,
                "unlock_action": unlock_action,
                "unlock_category": unlock_action.get("category"),
                "unlock_label": unlock_action.get("label"),
                "unlock_owner": unlock_action.get("owner"),
                "unlock_severity": unlock_action.get("severity"),
            }
        )

    return sorted(
        rows,
        key=lambda row: (
            mode_rank(row.get("mode")),
            numeric(row.get("readiness_score")),
            numeric(row.get("expected_revenue_eur")),
        ),
        reverse=True,
    )


def classify_route_mode(
    blockers,
    connector,
    control_live_allowed,
    control_paper_allowed,
    control_supervised_allowed,
    route,
):
    if blockers:
        return "blocked"

    tier = connector.get("production_readiness_tier") or route.get(
        "connector_readiness_tier"
    )
    gate_status = route.get("market_gate_status")

    if (
        control_live_allowed
        and route.get("live_submission")
        and gate_status in ["live_ready", "supervised_ready"]
        and tier in ["live_ready", "production_ready", "supervised_live_ready"]
    ):
        return "live_ready"

    if control_supervised_allowed and gate_status in ["supervised_ready", "live_ready"]:
        return "supervised_ready"

    if control_paper_allowed and route.get("recommendation_status") != "excluded":
        return "paper_ready"

    return "advisory_only"


def route_blockers(route, connector):
    blockers = []
    blockers.extend(route.get("blocking_reasons", []) or [])

    if route.get("recommendation_status") == "excluded":
        blockers.append(route.get("operator_next_action") or "Route is excluded.")

    if route.get("market_gate_status") == "blocked":
        blockers.append(
            route.get("market_gate_next_action")
            or "Market gate blocks this route."
        )

    if connector.get("automation_blocking_level") in [
        "live_auto_limited",
        "supervised_auto",
    ]:
        if connector.get("missing_credentials"):
            blockers.append(
                "Missing live route credentials: "
                + ", ".join(connector.get("missing_credentials", [])[:3])
            )

    return dedupe(blockers)


def route_next_action(blockers, control_blockers, mode, route):
    if blockers:
        return blockers[0]

    if mode == "live_ready":
        return route.get("next_deadline_action") or "Eligible for limited live auto submission."

    if mode == "supervised_ready":
        return "Use this route for supervised auto trading after human gate clearance."

    if mode == "paper_ready":
        return "Run paper trading and settlement feedback before supervised live."

    if control_blockers:
        return (
            control_blockers[0].get("message")
            or "Clear automation blockers before escalating this route."
        )

    return route.get("operator_next_action") or "Keep route under automated monitoring."


def build_route_unlock_action(asset_id, blockers, connector, country, mode, next_action, route):
    primary_blocker = blockers[0] if blockers else ""
    category = classify_unlock_category(
        blocker=primary_blocker,
        connector=connector,
        mode=mode,
        route=route,
    )

    action_map = {
        "credentials": {
            "href": "/settings",
            "label": "Configure market credentials",
            "owner": "integration_admin",
            "severity": "critical",
        },
        "handshake": {
            "href": "/execution/market-connectors",
            "label": "Run live handshake drill",
            "owner": "integration_admin",
            "resolution_endpoint": (
                f"/execution/market-connectors/live-handshake/run?"
                f"asset_id={asset_id}&country={country}"
            ),
            "severity": "high",
        },
        "market_gate": {
            "href": "/execution/market-allocation",
            "label": "Resolve market gate",
            "owner": "market_operator",
            "severity": "high",
        },
        "commercial_eligibility": {
            "href": "/revenue",
            "label": "Review commercial eligibility",
            "owner": "commercial_optimizer",
            "severity": "high",
        },
        "paper_trade": {
            "href": "/execution/simulation",
            "label": "Run paper trading",
            "owner": "paper_adapter",
            "resolution_endpoint": f"/assets/{asset_id}/execution/paper-trade/run",
            "severity": "medium",
        },
        "settlement": {
            "href": "/execution/settlement",
            "label": "Reconcile settlement feedback",
            "owner": "settlement_engine",
            "resolution_endpoint": f"/assets/{asset_id}/settlement/reconcile",
            "severity": "medium",
        },
        "human_gate": {
            "href": "/execution/risk-approval",
            "label": "Request human approval",
            "owner": "approval_gate",
            "resolution_endpoint": f"/assets/{asset_id}/execution/approval/request",
            "severity": "medium",
        },
        "forecast_confidence": {
            "href": "/forecasts",
            "label": "Validate forecast confidence",
            "owner": "forecast_engine",
            "severity": "high",
        },
        "telemetry": {
            "href": "/execution/audit",
            "label": "Refresh asset telemetry",
            "owner": "asset_operator",
            "resolution_endpoint": f"/assets/{asset_id}/telemetry/demo",
            "severity": "high",
        },
        "monitor": {
            "href": "/execution",
            "label": "Monitor route",
            "owner": "automation_control",
            "severity": "low",
        },
    }

    action = action_map.get(category, action_map["monitor"])

    return {
        "adapter_id": route.get("adapter_id"),
        "auto_resolvable": bool(action.get("resolution_endpoint")),
        "category": category,
        "href": action.get("href"),
        "label": action.get("label"),
        "message": next_action,
        "owner": action.get("owner"),
        "resolution_endpoint": action.get("resolution_endpoint"),
        "severity": action.get("severity"),
    }


def classify_unlock_category(blocker, connector, mode, route):
    text = " ".join(
        [
            str(blocker or ""),
            " ".join(connector.get("missing_credentials", []) or []),
            " ".join(route.get("missing_connector_controls", []) or []),
            str(route.get("market_gate_next_action") or ""),
            str(route.get("operator_next_action") or ""),
        ]
    ).lower()

    if "credential" in text or "env" in text or "secret" in text:
        return "credentials"

    if "handshake" in text or "adapter" in text or "connector" in text:
        return "handshake"

    if "gate" in text or "closure" in text or "market access" in text:
        return "market_gate"

    if "commercial" in text or "revenue allocation" in text or "product" in text:
        return "commercial_eligibility"

    if "paper" in text or mode == "paper_ready":
        return "paper_trade"

    if "settlement" in text or "reconcile" in text:
        return "settlement"

    if "approval" in text or "human" in text:
        return "human_gate"

    if "forecast" in text or "confidence" in text:
        return "forecast_confidence"

    if "telemetry" in text or "ems" in text:
        return "telemetry"

    if mode in ["live_ready", "supervised_ready"]:
        return "monitor"

    return "market_gate"


def score_route(route, connector, blockers, mode):
    if blockers:
        return 0.0

    score = numeric(route.get("allocation_score")) * 0.35
    score += numeric(route.get("connector_readiness_score")) * 0.2
    score += numeric(route.get("market_gate_score")) * 0.2
    score += numeric(route.get("risk_score")) * 0.15
    score += min(numeric(route.get("expected_revenue_eur")) / 20.0, 10.0)

    if connector.get("production_readiness_tier") in [
        "production_ready",
        "live_ready",
        "supervised_live_ready",
    ]:
        score += 5.0

    if mode == "live_ready":
        score += 10.0
    elif mode == "supervised_ready":
        score += 6.0
    elif mode == "paper_ready":
        score += 3.0

    return round(min(max(score, 0.0), 100.0), 1)


def summarize_routes(rows):
    return {
        "route_count": len(rows),
        "live_ready_route_count": count_mode(rows, "live_ready"),
        "supervised_ready_route_count": count_mode(rows, "supervised_ready"),
        "paper_ready_route_count": count_mode(rows, "paper_ready"),
        "advisory_route_count": count_mode(rows, "advisory_only"),
        "blocked_route_count": count_mode(rows, "blocked"),
        "best_route": rows[0].get("market_name") if rows else None,
        "best_route_mode": rows[0].get("mode") if rows else None,
    }


def score_go_live_readiness(allocation, confidence, connectors, control, route_summary):
    score = 0.0
    score += numeric(control.get("readiness_score")) * 0.25
    score += numeric((allocation.get("summary") or {}).get("readiness_score")) * 0.15
    score += numeric(confidence.get("confidence_score")) * 0.15
    score += numeric((connectors.get("summary") or {}).get("average_readiness_score")) * 0.2

    if route_summary.get("live_ready_route_count"):
        score += 20.0
    elif route_summary.get("supervised_ready_route_count"):
        score += 12.0
    elif route_summary.get("paper_ready_route_count"):
        score += 6.0

    score -= min(len(control.get("blockers", [])) * 4.0, 25.0)
    return round(min(max(score, 0.0), 100.0), 1)


def classify_mode_recommendation(control, route_summary, score):
    if route_summary.get("live_ready_route_count") and control.get("live_trading_allowed"):
        return "limited_live_auto"

    if route_summary.get("supervised_ready_route_count"):
        return "supervised_auto"

    if route_summary.get("paper_ready_route_count"):
        return "paper_trading"

    if score >= 45:
        return "advisory_only"

    return "blocked"


def classify_go_live_status(recommendation):
    return {
        "limited_live_auto": "go_live_ready",
        "supervised_auto": "supervised_ready",
        "paper_trading": "paper_ready",
        "advisory_only": "advisory_only",
        "blocked": "blocked",
    }.get(recommendation, "blocked")


def build_go_live_runbook(control, route_rows, route_summary):
    blockers = control.get("blockers", [])
    remediation = control.get("remediation_queue", [])
    next_action = control.get("next_automation_action") or {}
    best_route = route_rows[0] if route_rows else {}

    steps = [
        runbook_step(
            "market_route",
            "Select live-capable route",
            "passed" if route_summary.get("live_ready_route_count") else "blocked",
            best_route.get("next_action") or "Clear route blockers before live trading.",
            "/execution/market-allocation",
        ),
        runbook_step(
            "connector_handshake",
            "Validate market connector handshake",
            "passed"
            if best_route.get("mode") in ["live_ready", "supervised_ready"]
            else "blocked",
            "Run route handshake drills and configure missing env values.",
            "/execution/market-connectors",
        ),
        runbook_step(
            "risk_policy",
            "Clear risk and automation policy",
            "passed" if not blockers else "blocked",
            (blockers[0].get("message") if blockers else "Risk policy is clear."),
            "/execution/risk-approval",
        ),
        runbook_step(
            "paper_feedback",
            "Validate paper and settlement feedback",
            "passed"
            if control.get("evidence", {}).get("paper_trade_id")
            else "blocked",
            "Run paper trading and reconcile settlement feedback before live escalation.",
            "/execution/simulation",
        ),
        runbook_step(
            "live_action",
            "Execute next automated action",
            "passed" if control.get("live_trading_allowed") else "blocked",
            next_action.get("message") or "No automation action evaluated.",
            "/execution",
        ),
    ]

    return {
        "steps": steps,
        "blockers": blockers[:8],
        "remediation_queue": remediation[:8],
    }


def runbook_step(step_id, label, status, next_action, href):
    return {
        "step_id": step_id,
        "label": label,
        "status": status,
        "next_action": next_action,
        "href": href,
    }


def next_best_action(control, runbook):
    remediation = runbook.get("remediation_queue") or []
    if remediation:
        item = remediation[0]
        return {
            "label": item.get("required_action") or item.get("message"),
            "owner": item.get("source") or "automation_control",
            "href": item.get("evidence_link") or "/execution",
            "auto_resolvable": bool(item.get("auto_resolvable")),
            "resolution_endpoint": item.get("resolution_endpoint"),
        }

    action = control.get("next_automation_action") or {}
    return {
        "label": action.get("message") or action.get("label") or "Monitor automation.",
        "owner": action.get("owner") or "automation_control",
        "href": "/execution",
        "auto_resolvable": False,
        "resolution_endpoint": None,
    }


def count_mode(rows, mode):
    return sum(1 for row in rows if row.get("mode") == mode)


def mode_rank(mode):
    return {
        "live_ready": 5,
        "supervised_ready": 4,
        "paper_ready": 3,
        "advisory_only": 2,
        "blocked": 1,
    }.get(mode, 0)


def numeric(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def dedupe(items):
    seen = set()
    result = []

    for item in items:
        if not item or item in seen:
            continue
        seen.add(item)
        result.append(item)

    return result



