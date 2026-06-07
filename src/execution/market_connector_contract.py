from datetime import datetime

from src.execution.market_adapters.registry import list_market_adapters


CONNECTOR_METHODS = [
    "validate_order_package",
    "submit_orders",
    "poll_acknowledgement",
    "poll_results",
    "cancel_replace",
    "ingest_settlement",
]


CONNECTOR_SPECS = {
    "epex_day_ahead": {
        "connector_family": "epex_auction",
        "implemented_methods": [
            "validate_order_package",
            "submit_orders",
            "poll_acknowledgement",
            "poll_results",
            "ingest_settlement",
        ],
        "missing_methods": ["cancel_replace"],
        "raw_reference_fields": [
            "member_id",
            "portfolio_id",
            "auction_id",
            "client_order_id",
            "market_order_id",
            "award_id",
            "settlement_statement_id",
        ],
        "next_action": (
            "Wire EPEX member or broker credentials, exchange submission endpoint, "
            "award import, and settlement statement mapping for day-ahead live trading."
        ),
    },
    "epex_intraday_auction": {
        "connector_family": "epex_auction",
        "implemented_methods": [
            "validate_order_package",
            "submit_orders",
            "poll_acknowledgement",
            "poll_results",
            "ingest_settlement",
        ],
        "missing_methods": ["cancel_replace"],
        "raw_reference_fields": [
            "member_id",
            "portfolio_id",
            "auction_id",
            "client_order_id",
            "market_order_id",
            "award_id",
            "settlement_statement_id",
        ],
        "next_action": (
            "Add EPEX intraday auction endpoint credentials, product mapping, "
            "gate scheduling, award ingestion, and settlement reconciliation."
        ),
    },
    "epex_intraday_continuous": {
        "connector_family": "epex_continuous",
        "implemented_methods": [
            "validate_order_package",
            "submit_orders",
            "poll_acknowledgement",
            "poll_results",
            "cancel_replace",
            "ingest_settlement",
        ],
        "missing_methods": [],
        "raw_reference_fields": [
            "member_id",
            "portfolio_id",
            "order_book_id",
            "client_order_id",
            "market_order_id",
            "trade_id",
            "cancel_replace_id",
            "settlement_statement_id",
        ],
        "next_action": (
            "Wire continuous market order book, partial-fill stream, "
            "cancel/replace endpoint, and intraday settlement evidence."
        ),
    },
    "regelleistung_fcr": {
        "connector_family": "regelleistung_capacity",
        "implemented_methods": [
            "validate_order_package",
            "submit_orders",
            "poll_acknowledgement",
            "poll_results",
            "ingest_settlement",
        ],
        "missing_methods": ["cancel_replace"],
        "raw_reference_fields": [
            "tso_participant_id",
            "prequalification_id",
            "tender_id",
            "capacity_bid_id",
            "award_id",
            "availability_record_id",
            "settlement_statement_id",
        ],
        "next_action": (
            "Connect regelleistung participant credentials, tender submission, "
            "capacity award import, availability evidence, and TSO settlement mapping."
        ),
    },
    "regelleistung_afrr": {
        "connector_family": "regelleistung_capacity_energy",
        "implemented_methods": [
            "validate_order_package",
            "submit_orders",
            "poll_acknowledgement",
            "poll_results",
            "cancel_replace",
            "ingest_settlement",
        ],
        "missing_methods": [],
        "raw_reference_fields": [
            "tso_participant_id",
            "prequalification_id",
            "capacity_tender_id",
            "energy_activation_id",
            "capacity_award_id",
            "activation_metering_id",
            "settlement_statement_id",
        ],
        "next_action": (
            "Wire aFRR tender, activation telemetry, capacity and energy result feeds, "
            "and settlement attribution before limited live automation."
        ),
    },
    "regelleistung_mfrr": {
        "connector_family": "regelleistung_capacity_energy",
        "implemented_methods": [
            "validate_order_package",
            "submit_orders",
            "poll_acknowledgement",
            "poll_results",
            "cancel_replace",
            "ingest_settlement",
        ],
        "missing_methods": [],
        "raw_reference_fields": [
            "tso_participant_id",
            "prequalification_id",
            "capacity_tender_id",
            "manual_activation_id",
            "capacity_award_id",
            "activation_metering_id",
            "settlement_statement_id",
        ],
        "next_action": (
            "Wire mFRR tender, activation workflow, imbalance accounting, "
            "award ingestion, and settlement attribution."
        ),
    },
}


class MarketConnector:
    live_submission = False

    def __init__(self, adapter):
        self.adapter = adapter
        self.adapter_id = adapter["adapter_id"]
        self.spec = CONNECTOR_SPECS.get(self.adapter_id, {})

    def validate_order_package(self, order_package):
        orders = extract_orders(order_package)
        status = "validated" if orders else "invalid"
        message = (
            f"{len(orders)} order(s) match the connector contract."
            if orders
            else "No orders were available for connector validation."
        )
        return self.connector_result(
            method="validate_order_package",
            status=status,
            message=message,
            audit_status="passed" if orders else "blocked",
            order_count=len(orders),
        )

    def submit_orders(self, order_package):
        return self.preview_result(
            method="submit_orders",
            order_package=order_package,
            message="Submission contract is mapped, but live market credentials are not enabled.",
        )

    def poll_acknowledgement(self, submission_reference):
        return self.preview_result(
            method="poll_acknowledgement",
            message="Acknowledgement polling contract is mapped for market receipt evidence.",
            raw_market_references=normalize_reference(submission_reference),
        )

    def poll_results(self, submission_reference):
        return self.preview_result(
            method="poll_results",
            message="Result polling contract is mapped for award, fill, and rejection evidence.",
            raw_market_references=normalize_reference(submission_reference),
        )

    def cancel_replace(self, order_reference, replacement_order=None):
        if "cancel_replace" in self.spec.get("missing_methods", []):
            return self.connector_result(
                method="cancel_replace",
                status="not_supported",
                message="This route is auction-style; cancel/replace is not exposed as a live trading method.",
                raw_market_references=normalize_reference(order_reference),
            )

        return self.preview_result(
            method="cancel_replace",
            message="Cancel/replace contract is mapped, but live market credentials are not enabled.",
            raw_market_references=normalize_reference(order_reference),
            replacement_order=replacement_order or {},
        )

    def ingest_settlement(self, settlement_payload):
        return self.preview_result(
            method="ingest_settlement",
            message="Settlement ingestion contract is mapped for variance attribution.",
            raw_market_references=normalize_reference(settlement_payload),
        )

    def preview_result(self, method, message, order_package=None, **extra):
        orders = extract_orders(order_package or {})
        submitted_order_ids = [
            order.get("order_id") or order.get("bid_id") or f"{self.adapter_id}_{index}"
            for index, order in enumerate(orders, start=1)
        ]
        return self.connector_result(
            method=method,
            status="preview_only",
            message=message,
            audit_status="blocked",
            submitted_order_ids=submitted_order_ids,
            **extra,
        )

    def connector_result(
        self,
        method,
        status,
        message,
        audit_status="recorded",
        submitted_order_ids=None,
        accepted_orders=None,
        rejected_orders=None,
        fills=None,
        awards=None,
        raw_market_references=None,
        **extra,
    ):
        generated_at = datetime.now().isoformat(timespec="seconds")
        return {
            "adapter_id": self.adapter_id,
            "adapter_name": self.adapter.get("adapter_name"),
            "method": method,
            "status": status,
            "live_submission": self.live_submission,
            "generated_at": generated_at,
            "message": message,
            "submitted_order_ids": submitted_order_ids or [],
            "accepted_orders": accepted_orders or [],
            "rejected_orders": rejected_orders or [],
            "fills": fills or [],
            "awards": awards or [],
            "raw_market_references": raw_market_references or {},
            "audit_events": [
                {
                    "event": method,
                    "status": audit_status,
                    "recorded_at": generated_at,
                    "message": message,
                }
            ],
            **extra,
        }

    def contract_summary(self):
        implemented_methods = self.spec.get("implemented_methods", [])
        missing_methods = self.spec.get("missing_methods", [])
        live_enabled_methods = []
        preview_methods = [
            method
            for method in implemented_methods
            if method not in live_enabled_methods
        ]
        status = classify_contract_status(
            implemented_methods=implemented_methods,
            missing_methods=missing_methods,
            live_enabled_methods=live_enabled_methods,
        )
        return {
            "adapter_id": self.adapter_id,
            "adapter_name": self.adapter.get("adapter_name"),
            "connector_family": self.spec.get("connector_family", "market"),
            "connector_contract_status": status,
            "connector_methods": CONNECTOR_METHODS,
            "implemented_methods": implemented_methods,
            "preview_methods": preview_methods,
            "missing_methods": missing_methods,
            "live_enabled_methods": live_enabled_methods,
            "live_method_count": len(live_enabled_methods),
            "method_coverage": round(
                len(implemented_methods) / max(len(CONNECTOR_METHODS), 1) * 100,
                1,
            ),
            "raw_reference_fields": self.spec.get("raw_reference_fields", []),
            "contract_next_action": self.spec.get(
                "next_action",
                "Define route-specific connector contract methods.",
            ),
        }


def build_connector_contract_readiness(country="Germany"):
    connectors = [
        get_market_connector(adapter["adapter_id"]).contract_summary()
        for adapter in list_market_adapters(country=country)
        if adapter.get("adapter_id") in CONNECTOR_SPECS
    ]
    summary = summarize_contracts(connectors)
    return {
        "status": "ok",
        "country": country,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "contract_status": classify_portfolio_contract_status(summary),
        "summary": summary,
        "connectors": connectors,
    }


def get_connector_contract_summary(adapter_id):
    connector = get_market_connector(adapter_id)
    if not connector:
        return {}

    return connector.contract_summary()


def get_market_connector(adapter_id):
    adapter = next(
        (
            item
            for item in list_market_adapters(country="Germany")
            if item["adapter_id"] == adapter_id
        ),
        None,
    )
    if not adapter or adapter_id not in CONNECTOR_SPECS:
        return None

    return MarketConnector(adapter)


def summarize_contracts(connectors):
    return {
        "connector_contract_count": len(connectors),
        "preview_contract_ready_count": count_contract_status(
            connectors,
            "preview_contract_ready",
        ),
        "partial_contract_count": count_contract_status(
            connectors,
            "partial_contract",
        ),
        "live_contract_ready_count": count_contract_status(
            connectors,
            "live_contract_ready",
        ),
        "average_method_coverage": round(
            sum(connector.get("method_coverage", 0) for connector in connectors)
            / max(len(connectors), 1),
            1,
        ),
        "missing_method_count": sum(
            len(connector.get("missing_methods", [])) for connector in connectors
        ),
    }


def classify_contract_status(
    implemented_methods,
    missing_methods,
    live_enabled_methods,
):
    if len(live_enabled_methods) == len(CONNECTOR_METHODS):
        return "live_contract_ready"

    if not missing_methods and set(implemented_methods) == set(CONNECTOR_METHODS):
        return "preview_contract_ready"

    if implemented_methods:
        return "partial_contract"

    return "not_configured"


def classify_portfolio_contract_status(summary):
    if summary.get("live_contract_ready_count"):
        return "live_contract_available"

    if summary.get("preview_contract_ready_count"):
        return "preview_contracts_available"

    if summary.get("partial_contract_count"):
        return "partial_contracts_available"

    return "not_configured"


def count_contract_status(connectors, status):
    return len(
        [
            connector
            for connector in connectors
            if connector.get("connector_contract_status") == status
        ]
    )


def extract_orders(order_package):
    if not order_package:
        return []

    for key in ["orders", "bids", "market_bids", "order_package"]:
        value = order_package.get(key) if isinstance(order_package, dict) else None
        if isinstance(value, list):
            return value

    if isinstance(order_package, list):
        return order_package

    return []


def normalize_reference(reference):
    if isinstance(reference, dict):
        return reference

    if reference is None:
        return {}

    return {"reference": reference}
