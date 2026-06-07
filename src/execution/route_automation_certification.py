from datetime import datetime

from src.db.repositories.execution_repository import list_automation_event_payloads
from src.execution.credential_readiness import get_route_credential_readiness
from src.execution.live_adapter_handshake import HANDSHAKE_DRILL_EVENT_TYPE, get_route_handshake_readiness
from src.execution.market_adapters.registry import list_market_adapters
from src.execution.market_connector_contract import get_connector_contract_summary
from src.execution.market_connector_sandbox_certification import (
    get_connector_sandbox_certification,
)
from src.execution.official_api_compliance import get_route_official_api_compliance
from src.execution.supervised_live_readiness_gate import get_route_supervised_live_gate


CERTIFICATION_STAGES = [
    "not_configured",
    "ready_for_drill",
    "drill_failed",
    "certified_for_paper",
    "certified_for_supervised",
    "certified_for_live",
]


def build_route_automation_certification(asset_id="default_site", country="Germany"):
    routes = [
        certify_route_for_automation(adapter=adapter, asset_id=asset_id)
        for adapter in list_market_adapters(country=country)
        if adapter.get("adapter_id", "").startswith(("epex_", "regelleistung_"))
    ]
    summary = summarize_route_certifications(routes)
    return {
        "status": "ok",
        "asset_id": asset_id,
        "country": country,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "route_certification_status": classify_portfolio_certification(summary),
        "summary": summary,
        "routes": routes,
        "recommended_actions": build_certification_actions(routes),
    }


def get_route_automation_certification(adapter_id, asset_id="default_site"):
    adapter = next(
        (
            item
            for item in list_market_adapters(country="Germany")
            if item.get("adapter_id") == adapter_id
        ),
        None,
    )
    if not adapter:
        return {}

    return certify_route_for_automation(adapter=adapter, asset_id=asset_id)


def certify_route_for_automation(adapter, asset_id="default_site"):
    adapter_id = adapter["adapter_id"]
    credentials = get_route_credential_readiness(adapter_id)
    contract = get_connector_contract_summary(adapter_id)
    sandbox = get_connector_sandbox_certification(adapter_id)
    supervised_gate = get_route_supervised_live_gate(adapter_id)
    handshake = get_route_handshake_readiness(adapter_id)
    official_api = get_route_official_api_compliance(adapter_id)
    latest_drill = latest_route_drill(asset_id=asset_id, route_id=adapter_id)
    blockers = certification_blockers(
        adapter=adapter,
        credentials=credentials,
        contract=contract,
        sandbox=sandbox,
        supervised_gate=supervised_gate,
        handshake=handshake,
        official_api=official_api,
        latest_drill=latest_drill,
    )
    stage = classify_route_certification_stage(
        adapter=adapter,
        credentials=credentials,
        contract=contract,
        sandbox=sandbox,
        supervised_gate=supervised_gate,
        handshake=handshake,
        official_api=official_api,
        latest_drill=latest_drill,
        blockers=blockers,
    )
    score = score_route_certification(
        credentials=credentials,
        contract=contract,
        sandbox=sandbox,
        supervised_gate=supervised_gate,
        handshake=handshake,
        official_api=official_api,
        latest_drill=latest_drill,
        stage=stage,
    )

    return {
        "adapter_id": adapter_id,
        "adapter_name": adapter.get("adapter_name"),
        "market_segment": adapter.get("market_segment"),
        "venue": adapter.get("venue"),
        "route_certification_stage": stage,
        "route_certification_status": stage,
        "route_certification_score": score,
        "route_certification_rank": CERTIFICATION_STAGES.index(stage),
        "certified_for_paper": stage in [
            "certified_for_paper",
            "certified_for_supervised",
            "certified_for_live",
        ],
        "certified_for_supervised": stage in [
            "certified_for_supervised",
            "certified_for_live",
        ],
        "certified_for_live": stage == "certified_for_live",
        "latest_route_drill_at": latest_drill.get("created_at"),
        "latest_route_drill_status": latest_drill.get("status"),
        "latest_route_drill_event_id": latest_drill.get("automation_event_id"),
        "latest_route_drill_target_count": latest_drill.get("target_count"),
        "route_certification_blockers": blockers,
        "route_certification_next_action": next_certification_action(
            stage=stage,
            blockers=blockers,
            handshake=handshake,
            latest_drill=latest_drill,
            sandbox=sandbox,
            supervised_gate=supervised_gate,
        ),
        "route_certification_evidence": {
            "credential_status": credentials.get("credential_status"),
            "missing_env_keys": credentials.get("missing_env_keys", []),
            "connector_contract_status": contract.get("connector_contract_status"),
            "missing_methods": contract.get("missing_methods", []),
            "sandbox_certification_status": sandbox.get("sandbox_certification_status"),
            "supervised_live_gate_status": supervised_gate.get("supervised_live_gate_status"),
            "route_handshake_status": handshake.get("route_handshake_status"),
            "route_handshake_ready": handshake.get("route_handshake_ready"),
            "latest_route_drill_status": latest_drill.get("status"),
            "order_submission_performed": latest_drill.get("order_submission_performed"),
            "official_api_compliance_status": official_api.get(
                "official_api_compliance_status"
            ),
            "official_system": official_api.get("official_system"),
        },
        **official_api,
    }


def latest_route_drill(asset_id, route_id):
    events = list_automation_event_payloads(
        asset_id=asset_id,
        event_type=HANDSHAKE_DRILL_EVENT_TYPE,
        limit=50,
    )
    for event in events:
        payload = event.get("payload") or {}
        if payload.get("route_id") != route_id:
            continue
        summary = payload.get("summary") or {}
        return {
            "automation_event_id": event.get("automation_event_id"),
            "created_at": event.get("created_at"),
            "status": event.get("status"),
            "target_count": summary.get("target_count"),
            "passed_count": summary.get("passed_count"),
            "blocked_count": summary.get("blocked_count"),
            "order_submission_performed": payload.get(
                "order_submission_performed",
                False,
            ),
        }

    return {}


def certification_blockers(
    adapter,
    credentials,
    contract,
    sandbox,
    supervised_gate,
    handshake,
    official_api,
    latest_drill,
):
    blockers = []
    missing_env_keys = credentials.get("missing_env_keys", [])
    missing_methods = contract.get("missing_methods", [])

    if missing_env_keys:
        blockers.append(f"Configure route credentials: {', '.join(missing_env_keys)}.")

    if missing_methods:
        blockers.append(f"Complete connector methods: {', '.join(missing_methods)}.")

    if not sandbox.get("certified_for_paper"):
        blockers.append(
            sandbox.get("next_certification_action")
            or "Pass sandbox connector certification for automated paper trading."
        )

    if not handshake.get("route_handshake_ready"):
        blockers.extend(handshake.get("route_handshake_blockers", []))

    if latest_drill.get("status") == "blocked":
        blockers.append("Latest route-specific no-order handshake drill failed.")

    if latest_drill.get("order_submission_performed"):
        blockers.append("Latest route drill attempted order submission and cannot certify automation.")

    if not adapter.get("live_submission"):
        blockers.append("Live submission adapter is not enabled.")

    if official_api.get("official_api_compliance_status") != "compliant":
        blockers.extend(official_api.get("official_api_blockers", []))

    if supervised_gate.get("supervised_live_gate_status") == "blocked":
        blockers.extend(supervised_gate.get("supervised_live_blockers", []))

    return dedupe(blockers)


def classify_route_certification_stage(
    adapter,
    credentials,
    contract,
    sandbox,
    supervised_gate,
    handshake,
    official_api,
    latest_drill,
    blockers,
):
    if official_api.get("official_api_compliance_status") != "compliant":
        return "not_configured"

    if sandbox.get("certified_for_live") and supervised_gate.get(
        "supervised_live_candidate"
    ):
        return "certified_for_live"

    if supervised_gate.get("supervised_live_candidate") and handshake.get(
        "route_handshake_ready"
    ):
        return "certified_for_supervised"

    if sandbox.get("certified_for_paper") and handshake.get("route_handshake_ready"):
        return "certified_for_paper"

    if latest_drill.get("status") == "blocked":
        return "drill_failed"

    if (
        not credentials.get("missing_env_keys")
        and not contract.get("missing_methods")
        and sandbox.get("certified_for_paper")
    ):
        return "ready_for_drill"

    return "not_configured"


def score_route_certification(
    credentials,
    contract,
    sandbox,
    supervised_gate,
    handshake,
    official_api,
    latest_drill,
    stage,
):
    score = {
        "not_configured": 10,
        "ready_for_drill": 55,
        "drill_failed": 45,
        "certified_for_paper": 70,
        "certified_for_supervised": 90,
        "certified_for_live": 100,
    }[stage]

    if not credentials.get("missing_env_keys"):
        score += 5

    if not contract.get("missing_methods"):
        score += 5

    if sandbox.get("certified_for_paper"):
        score += 5

    if handshake.get("route_handshake_ready"):
        score += 5

    if latest_drill.get("status") == "passed":
        score += 5

    if supervised_gate.get("supervised_live_candidate"):
        score += 5

    if official_api.get("official_api_compliance_status") == "compliant":
        score += 10

    return min(score, 100)


def next_certification_action(stage, blockers, handshake, latest_drill, sandbox, supervised_gate):
    if stage == "certified_for_live":
        return "Route is live-certified; continue monitoring live orders, settlement, and kill-switch evidence."

    if stage == "certified_for_supervised":
        return "Run supervised live dry run with human approval, strict limits, and audit capture."

    if stage == "certified_for_paper":
        return (
            supervised_gate.get("supervised_live_next_action")
            or "Clear supervised-live blockers before enabling market submission."
        )

    if stage == "ready_for_drill":
        return "Run a route-specific no-order live adapter handshake drill."

    if stage == "drill_failed":
        return (
            handshake.get("route_handshake_next_action")
            or "Fix failed handshake target and rerun the route drill."
        )

    if sandbox.get("next_certification_action"):
        return sandbox.get("next_certification_action")

    if blockers:
        return blockers[0]

    return "Complete connector configuration and rerun route certification."


def summarize_route_certifications(routes):
    return {
        "route_certification_count": len(routes),
        "not_configured_count": count_stage(routes, "not_configured"),
        "ready_for_drill_count": count_stage(routes, "ready_for_drill"),
        "drill_failed_count": count_stage(routes, "drill_failed"),
        "paper_certified_route_count": count_stage(routes, "certified_for_paper"),
        "supervised_certified_route_count": count_stage(
            routes,
            "certified_for_supervised",
        ),
        "live_certified_route_count": count_stage(routes, "certified_for_live"),
        "certified_route_count": len(
            [
                route
                for route in routes
                if route.get("route_certification_stage")
                in [
                    "certified_for_paper",
                    "certified_for_supervised",
                    "certified_for_live",
                ]
            ]
        ),
        "average_route_certification_score": round(
            sum(route.get("route_certification_score", 0) for route in routes)
            / max(len(routes), 1),
            1,
        ),
    }


def classify_portfolio_certification(summary):
    if summary.get("live_certified_route_count"):
        return "live_certified_route_available"

    if summary.get("supervised_certified_route_count"):
        return "supervised_certified_route_available"

    if summary.get("paper_certified_route_count"):
        return "paper_certified_route_available"

    if summary.get("ready_for_drill_count"):
        return "routes_ready_for_drill"

    if summary.get("drill_failed_count"):
        return "route_drill_failed"

    return "routes_not_configured"


def build_certification_actions(routes):
    actions = [
        f"{route['adapter_id']}: {route['route_certification_next_action']}"
        for route in routes
        if route.get("route_certification_stage") != "certified_for_live"
    ]
    return actions[:8] or ["Continue live route monitoring and settlement feedback."]


def count_stage(routes, stage):
    return len(
        [
            route
            for route in routes
            if route.get("route_certification_stage") == stage
        ]
    )


def dedupe(items):
    seen = set()
    result = []
    for item in items:
        if not item or item in seen:
            continue
        seen.add(item)
        result.append(item)
    return result
