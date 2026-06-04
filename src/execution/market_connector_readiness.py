import os
from datetime import datetime

from src.execution.market_adapters.registry import list_market_adapters


CONNECTOR_REQUIREMENTS = {
    "epex_day_ahead": {
        "credential_keys": ["EPEX_API_KEY", "EPEX_MEMBER_ID"],
        "production_controls": [
            "member_or_broker_route",
            "order_submission_api",
            "gate_closure_scheduler",
            "settlement_account_mapping",
            "cancel_replace_controls",
        ],
        "priority": 1,
    },
    "epex_intraday_auction": {
        "credential_keys": ["EPEX_API_KEY", "EPEX_MEMBER_ID"],
        "production_controls": [
            "auction_product_mapping",
            "gate_closure_scheduler",
            "order_submission_api",
            "auction_award_import",
            "settlement_account_mapping",
        ],
        "priority": 2,
    },
    "epex_intraday_continuous": {
        "credential_keys": ["EPEX_API_KEY", "EPEX_MEMBER_ID"],
        "production_controls": [
            "live_order_book",
            "partial_fill_handler",
            "cancel_replace_controls",
            "liquidity_and_spread_limits",
            "intraday_rebalancing_supervisor",
        ],
        "priority": 3,
    },
    "regelleistung_fcr": {
        "credential_keys": ["REGELLEISTUNG_API_KEY", "TSO_PARTICIPANT_ID"],
        "production_controls": [
            "asset_prequalification",
            "symmetric_capacity_validation",
            "availability_telemetry",
            "capacity_award_import",
            "tso_settlement_mapping",
        ],
        "priority": 4,
    },
    "regelleistung_afrr": {
        "credential_keys": ["REGELLEISTUNG_API_KEY", "TSO_PARTICIPANT_ID"],
        "production_controls": [
            "asset_prequalification",
            "activation_telemetry",
            "capacity_reservation_controls",
            "energy_activation_accounting",
            "tso_settlement_mapping",
        ],
        "priority": 5,
    },
    "regelleistung_mfrr": {
        "credential_keys": ["REGELLEISTUNG_API_KEY", "TSO_PARTICIPANT_ID"],
        "production_controls": [
            "asset_prequalification",
            "manual_activation_workflow",
            "capacity_reservation_controls",
            "imbalance_settlement_mapping",
            "tso_settlement_mapping",
        ],
        "priority": 6,
    },
}


def market_connector_readiness(country="Germany"):
    adapters = [
        adapter
        for adapter in list_market_adapters(country=country)
        if adapter.get("environment") not in ["paper", "demo"]
    ]
    connectors = [build_connector_readiness(adapter) for adapter in adapters]
    summary = summarize_connectors(connectors)

    return {
        "status": "ok",
        "country": country,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "connector_status": classify_portfolio_status(summary),
        "summary": summary,
        "connectors": sorted(
            connectors,
            key=lambda connector: connector.get("priority", 99),
        ),
        "recommended_actions": build_recommended_actions(connectors),
    }


def build_connector_readiness(adapter):
    requirements = CONNECTOR_REQUIREMENTS.get(adapter["adapter_id"], {})
    credential_keys = requirements.get("credential_keys", [])
    missing_credentials = [
        key for key in credential_keys if not os.getenv(key)
    ]
    credential_status = (
        "configured"
        if credential_keys and not missing_credentials
        else adapter.get("credential_status")
    )
    preview_available = adapter.get("connection_status") in [
        "available",
        "preview_available",
    ]
    live_submission = bool(adapter.get("live_submission")) and not missing_credentials
    missing_controls = []

    if not preview_available:
        missing_controls.append("preview_adapter")

    if missing_credentials:
        missing_controls.append("market_credentials")

    if not adapter.get("live_submission"):
        missing_controls.append("live_submission_adapter")

    missing_controls.extend(requirements.get("production_controls", []))
    readiness_tier = classify_readiness_tier(
        adapter=adapter,
        missing_credentials=missing_credentials,
        preview_available=preview_available,
        live_submission=live_submission,
    )

    return {
        **adapter,
        "credential_status": credential_status,
        "credential_keys": credential_keys,
        "missing_credentials": missing_credentials,
        "preview_available": preview_available,
        "paper_supported": True,
        "live_submission": live_submission,
        "missing_controls": dedupe(missing_controls),
        "production_readiness_tier": readiness_tier,
        "readiness_score": score_connector(
            preview_available=preview_available,
            missing_credentials=missing_credentials,
            live_submission=live_submission,
        ),
        "priority": requirements.get("priority", 99),
        "next_integration_action": next_integration_action(
            adapter=adapter,
            missing_credentials=missing_credentials,
            live_submission=live_submission,
            readiness_tier=readiness_tier,
        ),
    }


def classify_readiness_tier(
    adapter,
    missing_credentials,
    preview_available,
    live_submission,
):
    if live_submission and not missing_credentials:
        return "production_ready"

    if missing_credentials:
        return "credentials_required"

    if preview_available and adapter.get("connection_status") == "preview_available":
        return "preview_ready"

    if preview_available:
        return "paper_or_demo_ready"

    return "integration_required"


def score_connector(preview_available, missing_credentials, live_submission):
    score = 0

    if preview_available:
        score += 35

    if not missing_credentials:
        score += 25

    if live_submission:
        score += 40

    return score


def summarize_connectors(connectors):
    return {
        "connector_count": len(connectors),
        "preview_ready_count": count_by_tier(connectors, "preview_ready"),
        "credentials_required_count": count_by_tier(connectors, "credentials_required"),
        "production_ready_count": count_by_tier(connectors, "production_ready"),
        "live_submission_count": len(
            [connector for connector in connectors if connector.get("live_submission")]
        ),
        "average_readiness_score": round(
            sum(connector.get("readiness_score", 0) for connector in connectors)
            / max(len(connectors), 1),
            1,
        ),
    }


def classify_portfolio_status(summary):
    if summary["production_ready_count"]:
        return "supervised_live_route_available"

    if summary["credentials_required_count"] == summary["connector_count"]:
        return "credentials_required"

    if summary["preview_ready_count"]:
        return "preview_and_paper_ready"

    return "integration_required"


def build_recommended_actions(connectors):
    actions = []

    for connector in connectors:
        if connector["production_readiness_tier"] == "production_ready":
            continue

        actions.append(
            f"{connector['adapter_name']}: {connector['next_integration_action']}"
        )

    if not actions:
        actions.append("Begin supervised live submission dry run with strict operator approval.")

    return actions[:8]


def next_integration_action(
    adapter,
    missing_credentials,
    live_submission,
    readiness_tier,
):
    if missing_credentials:
        return f"Configure {', '.join(missing_credentials)} and validate member or TSO access."

    if not live_submission:
        return adapter.get("next_connection_action") or "Implement live submission adapter."

    if readiness_tier == "production_ready":
        return "Run supervised live submission readiness drill."

    return "Complete connector integration controls."


def count_by_tier(connectors, tier):
    return len(
        [
            connector
            for connector in connectors
            if connector.get("production_readiness_tier") == tier
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
