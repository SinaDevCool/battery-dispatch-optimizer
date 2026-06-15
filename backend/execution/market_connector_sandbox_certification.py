from datetime import datetime

from backend.execution.market_adapters.registry import list_market_adapters
from backend.execution.market_connector_contract import (
    CONNECTOR_METHODS,
    get_market_connector,
)
from backend.execution.official_api_compliance import get_route_official_api_compliance


def build_connector_sandbox_certification(country="Germany"):
    certifications = [
        certify_connector_in_sandbox(adapter)
        for adapter in list_market_adapters(country=country)
        if get_market_connector(adapter["adapter_id"])
    ]
    summary = summarize_certifications(certifications)
    return {
        "status": "ok",
        "country": country,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "sandbox_certification_status": classify_portfolio_certification(summary),
        "summary": summary,
        "certifications": certifications,
    }


def get_connector_sandbox_certification(adapter_id):
    adapter = next(
        (
            item
            for item in list_market_adapters(country="Germany")
            if item["adapter_id"] == adapter_id
        ),
        None,
    )
    if not adapter:
        return {}

    connector = get_market_connector(adapter_id)
    if not connector:
        return {}

    return certify_connector_in_sandbox(adapter)


def certify_connector_in_sandbox(adapter):
    connector = get_market_connector(adapter["adapter_id"])
    order_package = synthetic_order_package(adapter)
    submission_reference = synthetic_submission_reference(adapter)
    settlement_payload = synthetic_settlement_payload(adapter)
    results = [
        connector.validate_order_package(order_package),
        connector.submit_orders(order_package),
        connector.poll_acknowledgement(submission_reference),
        connector.poll_results(submission_reference),
        connector.cancel_replace(
            submission_reference,
            replacement_order=synthetic_replacement_order(adapter),
        ),
        connector.ingest_settlement(settlement_payload),
    ]
    required_results = [
        result
        for result in results
        if result["method"] not in connector.spec.get("missing_methods", [])
    ]
    paper_passed = all(
        result["status"] in ["validated", "preview_only"]
        for result in required_results
    )
    live_ready = bool(adapter.get("live_submission")) and not connector.spec.get(
        "missing_methods"
    )
    official_api_compliance = get_route_official_api_compliance(adapter["adapter_id"])
    blocked_reasons = certification_blockers(
        adapter=adapter,
        connector=connector,
        paper_passed=paper_passed,
        official_api_compliance=official_api_compliance,
    )
    certification_status = classify_certification_status(
        paper_passed=paper_passed and not blocked_reasons,
        live_ready=live_ready,
        blocked_reasons=blocked_reasons,
    )

    return {
        "adapter_id": adapter["adapter_id"],
        "adapter_name": adapter.get("adapter_name"),
        "venue": adapter.get("venue"),
        "market_segment": adapter.get("market_segment"),
        "connector_family": connector.spec.get("connector_family"),
        "sandbox_certification_status": certification_status,
        "certified_for_paper": paper_passed and not blocked_reasons,
        "certified_for_supervised_live": live_ready and paper_passed and not blocked_reasons,
        "certified_for_live": False,
        "method_count": len(CONNECTOR_METHODS),
        "passed_method_count": len(
            [
                result
                for result in required_results
                if result["status"] in ["validated", "preview_only"]
            ]
        ),
        "missing_method_count": len(connector.spec.get("missing_methods", [])),
        "blocked_reasons": blocked_reasons,
        "next_certification_action": next_certification_action(
            adapter=adapter,
            connector=connector,
            paper_passed=paper_passed,
            live_ready=live_ready,
        ),
        "synthetic_order_count": len(order_package["orders"]),
        "sandbox_results": certification_result_rows(results),
        "audit_event_count": sum(len(result.get("audit_events", [])) for result in results),
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        **official_api_compliance,
    }


def synthetic_order_package(adapter):
    adapter_id = adapter["adapter_id"]
    market_segment = adapter.get("market_segment")
    venue = adapter.get("venue")

    if adapter_id.startswith("regelleistung_"):
        orders = [
            {
                "order_id": f"{adapter_id}_sandbox_capacity_1",
                "product_id": adapter.get("supported_products", ["capacity"])[0],
                "side": "sell_capacity",
                "capacity_mw": 1,
                "availability_percent": 95,
                "limit_price_eur_mw": 10,
            }
        ]
    elif adapter_id == "epex_intraday_continuous":
        orders = [
            {
                "order_id": f"{adapter_id}_sandbox_buy_1",
                "product_id": "intraday_continuous_15_min",
                "side": "buy",
                "volume_mwh": 0.25,
                "limit_price_eur_mwh": 25,
            },
            {
                "order_id": f"{adapter_id}_sandbox_sell_1",
                "product_id": "intraday_continuous_15_min",
                "side": "sell",
                "volume_mwh": 0.25,
                "limit_price_eur_mwh": 85,
            },
        ]
    else:
        orders = [
            {
                "order_id": f"{adapter_id}_sandbox_buy_1",
                "product_id": adapter.get("supported_products", ["day_ahead_hourly"])[0],
                "side": "buy",
                "volume_mwh": 1,
                "limit_price_eur_mwh": 20,
            },
            {
                "order_id": f"{adapter_id}_sandbox_sell_1",
                "product_id": adapter.get("supported_products", ["day_ahead_hourly"])[0],
                "side": "sell",
                "volume_mwh": 1,
                "limit_price_eur_mwh": 80,
            },
        ]

    return {
        "adapter_id": adapter_id,
        "venue": venue,
        "market_segment": market_segment,
        "simulation_mode": "sandbox_certification",
        "orders": orders,
    }


def synthetic_submission_reference(adapter):
    adapter_id = adapter["adapter_id"]
    return {
        "adapter_id": adapter_id,
        "client_submission_id": f"{adapter_id}_sandbox_submission",
        "market_order_id": f"{adapter_id}_sandbox_market_order",
        "market_reference_status": "synthetic",
    }


def synthetic_replacement_order(adapter):
    return {
        "order_id": f"{adapter['adapter_id']}_sandbox_replace_1",
        "limit_price_eur_mwh": 50,
        "reason": "sandbox_cancel_replace_validation",
    }


def synthetic_settlement_payload(adapter):
    return {
        "adapter_id": adapter["adapter_id"],
        "settlement_statement_id": f"{adapter['adapter_id']}_sandbox_settlement",
        "expected_pnl_eur": 100,
        "realized_pnl_eur": 100,
        "variance_eur": 0,
    }


def certification_result_rows(results):
    return [
        {
            "method": result["method"],
            "status": result["status"],
            "message": result["message"],
            "submitted_order_ids": result.get("submitted_order_ids", []),
            "raw_market_references": result.get("raw_market_references", {}),
        }
        for result in results
    ]


def certification_blockers(adapter, connector, paper_passed, official_api_compliance=None):
    blockers = []
    official_api_compliance = official_api_compliance or {}

    if not paper_passed:
        blockers.append("Sandbox method chain did not pass for all required connector methods.")

    missing_methods = connector.spec.get("missing_methods", [])
    if missing_methods:
        blockers.append(
            f"Missing connector method(s): {', '.join(missing_methods)}."
        )

    if not adapter.get("live_submission"):
        blockers.append("Live submission adapter is not enabled.")

    if adapter.get("credential_status") == "missing":
        blockers.append("Market credentials are not configured.")

    if official_api_compliance.get("official_api_compliance_status") != "compliant":
        blockers.extend(official_api_compliance.get("official_api_blockers", []))

    return blockers


def classify_certification_status(paper_passed, live_ready, blocked_reasons):
    if live_ready and paper_passed and not blocked_reasons:
        return "certified_for_supervised_live"

    if paper_passed:
        return "certified_for_paper"

    return "blocked"


def next_certification_action(adapter, connector, paper_passed, live_ready):
    if not paper_passed:
        return "Fix sandbox method failures before this route can be used for automated paper trading."

    if connector.spec.get("missing_methods"):
        return connector.spec.get("next_action")

    if not live_ready:
        return (
            "Connect credentials and live adapter wiring, then rerun sandbox certification "
            "before supervised market submission."
        )

    return "Run supervised live submission dry run with strict audit capture."


def summarize_certifications(certifications):
    return {
        "sandbox_certification_count": len(certifications),
        "paper_certified_count": len(
            [
                item
                for item in certifications
                if item.get("certified_for_paper")
            ]
        ),
        "supervised_live_certified_count": len(
            [
                item
                for item in certifications
                if item.get("certified_for_supervised_live")
            ]
        ),
        "live_certified_count": len(
            [
                item
                for item in certifications
                if item.get("certified_for_live")
            ]
        ),
        "blocked_certification_count": len(
            [
                item
                for item in certifications
                if item.get("sandbox_certification_status") == "blocked"
            ]
        ),
        "average_passed_method_count": round(
            sum(item.get("passed_method_count", 0) for item in certifications)
            / max(len(certifications), 1),
            1,
        ),
    }


def classify_portfolio_certification(summary):
    if summary.get("live_certified_count"):
        return "live_certified_route_available"

    if summary.get("supervised_live_certified_count"):
        return "supervised_live_certified_route_available"

    if summary.get("paper_certified_count"):
        return "paper_certified_routes_available"

    return "sandbox_blocked"



