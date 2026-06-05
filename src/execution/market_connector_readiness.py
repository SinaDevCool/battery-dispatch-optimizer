import os
from datetime import datetime

from src.config.paths import ACTUAL_PRICE_FILE, FORECAST_FILE
from src.execution.market_adapters.registry import list_market_adapters
from src.storage import get_storage_client


CONNECTOR_REQUIREMENTS = {
    "epex_day_ahead": {
        "automation_blocking_level": "supervised_auto",
        "credential_keys": ["EPEX_API_KEY", "EPEX_MEMBER_ID"],
        "family": "wholesale",
        "integration_type": "market_connector",
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
        "automation_blocking_level": "supervised_auto",
        "credential_keys": ["EPEX_API_KEY", "EPEX_MEMBER_ID"],
        "family": "wholesale",
        "integration_type": "market_connector",
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
        "automation_blocking_level": "live_auto_limited",
        "credential_keys": ["EPEX_API_KEY", "EPEX_MEMBER_ID"],
        "family": "wholesale",
        "integration_type": "market_connector",
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
        "automation_blocking_level": "supervised_auto",
        "credential_keys": ["REGELLEISTUNG_API_KEY", "TSO_PARTICIPANT_ID"],
        "family": "ancillary",
        "integration_type": "market_connector",
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
        "automation_blocking_level": "live_auto_limited",
        "credential_keys": ["REGELLEISTUNG_API_KEY", "TSO_PARTICIPANT_ID"],
        "family": "ancillary",
        "integration_type": "market_connector",
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
        "automation_blocking_level": "live_auto_limited",
        "credential_keys": ["REGELLEISTUNG_API_KEY", "TSO_PARTICIPANT_ID"],
        "family": "ancillary",
        "integration_type": "market_connector",
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


DATA_INTEGRATION_REQUIREMENTS = [
    {
        "adapter_id": "forecast_provider",
        "adapter_name": "Forecast provider",
        "automation_blocking_level": "paper_trading",
        "credential_keys": ["ENTSOE_API_TOKEN"],
        "family": "data",
        "integration_type": "data_feed",
        "priority": 0,
        "production_controls": [
            "provider_failover",
            "forecast_quality_monitoring",
            "forecast_versioning",
        ],
        "storage_file": FORECAST_FILE,
        "venue": "forecast",
        "market_segment": "forecast_feed",
        "next_connection_action": "Connect live forecast provider credentials and validate forecast-vs-actual performance.",
    },
    {
        "adapter_id": "actual_price_feed",
        "adapter_name": "Actual price feed",
        "automation_blocking_level": "supervised_auto",
        "credential_keys": ["ENTSOE_API_TOKEN"],
        "family": "data",
        "integration_type": "data_feed",
        "priority": 0.5,
        "production_controls": [
            "actual_price_backfill",
            "imbalance_price_mapping",
            "data_freshness_monitoring",
        ],
        "storage_file": ACTUAL_PRICE_FILE,
        "venue": "market_data",
        "market_segment": "actual_prices",
        "next_connection_action": "Connect actual price ingestion and reconcile forecasts against realized prices.",
    },
    {
        "adapter_id": "asset_telemetry",
        "adapter_name": "Asset telemetry / EMS",
        "automation_blocking_level": "live_auto_limited",
        "credential_keys": ["EMS_API_URL", "EMS_API_TOKEN"],
        "family": "asset",
        "integration_type": "asset_integration",
        "priority": 0.7,
        "production_controls": [
            "soc_stream",
            "availability_stream",
            "dispatch_acknowledgement",
            "schedule_deviation_monitoring",
        ],
        "venue": "asset",
        "market_segment": "telemetry",
        "next_connection_action": "Integrate EMS telemetry for SOC, availability, dispatch acknowledgement, and deviation monitoring.",
    },
    {
        "adapter_id": "settlement_evidence",
        "adapter_name": "Settlement evidence",
        "automation_blocking_level": "live_auto_limited",
        "credential_keys": [],
        "family": "settlement",
        "integration_type": "settlement_feed",
        "priority": 7,
        "production_controls": [
            "market_award_import",
            "metered_delivery_import",
            "settlement_statement_mapping",
            "variance_attribution",
        ],
        "venue": "backoffice",
        "market_segment": "settlement",
        "next_connection_action": "Connect settlement, award, and metered-delivery evidence for automated variance feedback.",
    },
]


def market_connector_readiness(country="Germany"):
    adapters = [
        adapter
        for adapter in list_market_adapters(country=country)
        if adapter.get("environment") not in ["paper", "demo"]
    ]
    connectors = [build_connector_readiness(adapter) for adapter in adapters]
    integrations = [build_data_integration_readiness(item) for item in DATA_INTEGRATION_REQUIREMENTS]
    all_integrations = integrations + connectors
    summary = summarize_connectors(all_integrations)

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
        "integrations": sorted(
            all_integrations,
            key=lambda connector: connector.get("priority", 99),
        ),
        "recommended_actions": build_recommended_actions(all_integrations),
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
        "automation_blocking_level": requirements.get(
            "automation_blocking_level",
            "live_auto_limited",
        ),
        "credential_status": credential_status,
        "credential_keys": credential_keys,
        "family": requirements.get("family", "market"),
        "integration_type": requirements.get("integration_type", "market_connector"),
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


def build_data_integration_readiness(integration):
    credential_keys = integration.get("credential_keys", [])
    missing_credentials = [
        key for key in credential_keys if not os.getenv(key)
    ]
    storage_file = integration.get("storage_file")
    storage = get_storage_client()
    local_evidence_available = bool(storage_file and storage.exists(storage_file))
    credential_status = (
        "configured"
        if credential_keys and not missing_credentials
        else "not_required"
        if not credential_keys
        else "missing"
    )
    preview_available = local_evidence_available or not credential_keys
    live_submission = False
    missing_controls = []

    if missing_credentials:
        missing_controls.append("credentials")

    if storage_file and not local_evidence_available:
        missing_controls.append("local_evidence_file")

    missing_controls.extend(integration.get("production_controls", []))
    readiness_tier = classify_data_readiness_tier(
        local_evidence_available=local_evidence_available,
        missing_credentials=missing_credentials,
        production_controls=integration.get("production_controls", []),
    )

    return {
        "adapter_id": integration["adapter_id"],
        "adapter_name": integration["adapter_name"],
        "automation_blocking_level": integration["automation_blocking_level"],
        "connection_status": (
            "preview_available" if preview_available else "planned"
        ),
        "country": "Germany",
        "credential_keys": credential_keys,
        "credential_status": credential_status,
        "environment": "data",
        "family": integration["family"],
        "integration_type": integration["integration_type"],
        "live_submission": live_submission,
        "market_segment": integration["market_segment"],
        "missing_controls": dedupe(missing_controls),
        "missing_credentials": missing_credentials,
        "next_connection_action": integration["next_connection_action"],
        "next_integration_action": next_data_integration_action(
            integration=integration,
            local_evidence_available=local_evidence_available,
            missing_credentials=missing_credentials,
        ),
        "paper_supported": preview_available,
        "preview_available": preview_available,
        "priority": integration["priority"],
        "production_readiness_tier": readiness_tier,
        "readiness_score": score_data_integration(
            local_evidence_available=local_evidence_available,
            missing_credentials=missing_credentials,
            production_controls=integration.get("production_controls", []),
        ),
        "venue": integration["venue"],
    }


def classify_data_readiness_tier(
    local_evidence_available,
    missing_credentials,
    production_controls,
):
    if missing_credentials:
        return "credentials_required"

    if local_evidence_available and not production_controls:
        return "production_ready"

    if local_evidence_available:
        return "preview_ready"

    return "integration_required"


def score_data_integration(
    local_evidence_available,
    missing_credentials,
    production_controls,
):
    score = 0

    if local_evidence_available:
        score += 45

    if not missing_credentials:
        score += 25

    if not production_controls:
        score += 30

    return score


def next_data_integration_action(
    integration,
    local_evidence_available,
    missing_credentials,
):
    if missing_credentials:
        return f"Configure {', '.join(missing_credentials)} and validate live data access."

    if not local_evidence_available and integration.get("storage_file"):
        return "Run data ingestion and validate local evidence availability."

    return integration.get("next_connection_action")


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
        "ancillary_count": count_by_family(connectors, "ancillary"),
        "data_feed_count": count_by_type(connectors, "data_feed"),
        "epex_count": len(
            [
                connector
                for connector in connectors
                if connector.get("adapter_id", "").startswith("epex_")
            ]
        ),
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
        "live_auto_blocking_count": count_by_blocking_level(
            connectors,
            "live_auto_limited",
        ),
        "supervised_auto_blocking_count": count_by_blocking_level(
            connectors,
            "supervised_auto",
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


def count_by_family(connectors, family):
    return len(
        [
            connector
            for connector in connectors
            if connector.get("family") == family
        ]
    )


def count_by_type(connectors, integration_type):
    return len(
        [
            connector
            for connector in connectors
            if connector.get("integration_type") == integration_type
        ]
    )


def count_by_blocking_level(connectors, blocking_level):
    return len(
        [
            connector
            for connector in connectors
            if connector.get("automation_blocking_level") == blocking_level
            and connector.get("production_readiness_tier") != "production_ready"
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
