from datetime import datetime

from backend.assets.asset_loader import get_asset
from backend.api.routes.forecast_actual import asset_forecast_confidence
from backend.api.routes.revenue import latest_asset_revenue_stack_allocation
from backend.api.routes.settlement import latest_asset_settlement
from backend.api.routes.summaries import asset_revenue_summary
from backend.execution.market_connector_readiness import market_connector_readiness
from backend.services.demo_evidence import is_demo_asset


PRIORITY_DOMAINS = [
    "revenue_proof",
    "settlement_proof",
    "market_readiness",
    "forecast_trust",
]


def build_priority_gap_analysis(asset_id, evidence_mode="live"):
    evidence_mode = normalize_evidence_mode(evidence_mode)
    asset = safe_call(lambda: get_asset(asset_id))
    revenue = safe_call(lambda: asset_revenue_summary(asset_id))
    revenue_allocation = safe_call(lambda: latest_asset_revenue_stack_allocation(asset_id))
    settlement = safe_call(lambda: latest_asset_settlement(asset_id))
    market = safe_call(lambda: market_connector_readiness(country="Germany", asset_id=asset_id))
    forecast = safe_call(lambda: asset_forecast_confidence(asset_id))

    live_gaps = [
        build_revenue_gap(revenue=revenue, revenue_allocation=revenue_allocation),
        build_settlement_gap(settlement=settlement, asset=asset),
        build_market_gap(market=market, asset=asset),
        build_forecast_gap(forecast=forecast),
    ]
    gaps = apply_mock_evidence_mode(live_gaps) if evidence_mode == "mock" else live_gaps
    gaps = sorted(gaps, key=lambda gap: severity_rank(gap["severity"]), reverse=True)
    open_gaps = [gap for gap in gaps if gap["status"] not in ["ready", "demo_ready"]]
    production_gaps = [gap for gap in gaps if gap["status"] != "ready"]
    live_production_gaps = [gap for gap in live_gaps if gap["status"] != "ready"]
    top_gap = open_gaps[0] if open_gaps else gaps[0]

    return {
        "status": "ok",
        "asset_id": asset_id,
        "evidence_mode": evidence_mode,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "summary": {
            "domain_count": len(PRIORITY_DOMAINS),
            "open_gap_count": len(open_gaps),
            "production_gap_count": len(production_gaps),
            "live_production_gap_count": len(live_production_gaps),
            "ready_domain_count": len(gaps) - len(open_gaps),
            "highest_severity": top_gap["severity"],
            "top_gap_id": top_gap["gap_id"],
            "top_gap_title": top_gap["title"],
            "business_answer": build_business_answer(
                evidence_mode=evidence_mode,
                open_gaps=open_gaps,
                production_gaps=production_gaps,
                live_production_gaps=live_production_gaps,
                top_gap=top_gap,
            ),
        },
        "gaps": gaps,
        "evidence_modes": build_evidence_modes(gaps),
        "revenue_opportunities": build_revenue_opportunities(revenue, revenue_allocation),
        "settlement_explainer": build_settlement_explainer(settlement),
        "connector_onboarding": build_connector_onboarding(market),
        "persona_playbooks": build_persona_playbooks(gaps),
        "source_context": {
            "revenue_status": revenue.get("status"),
            "settlement_status": settlement.get("status"),
            "market_status": market.get("connector_status") or market.get("status"),
            "forecast_status": forecast.get("status"),
        },
    }


def build_evidence_modes(gaps):
    modes = []
    for gap_item in gaps:
        status = gap_item["status"]
        if status == "ready":
            mode = "mock_ready_or_production_ready"
            production_state = "production-ready if source evidence is production; demo-ready if source is mock"
        elif status == "demo_ready":
            mode = "mock_demo_ready"
            production_state = "production upgrade required"
        else:
            mode = "evidence_gap_open"
            production_state = "demo and production evidence incomplete"

        modes.append(
            {
                "domain": gap_item["domain"],
                "current_mode": mode,
                "status": status,
                "source_page": gap_item["source_page"],
                "source_route": gap_item["source_route"],
                "production_state": production_state,
                "production_upgrade": production_upgrade_for_gap(gap_item["gap_id"]),
                "agent_language": evidence_mode_language(gap_item),
            }
        )

    return modes


def build_revenue_opportunities(revenue, revenue_allocation):
    revenue_stack = revenue.get("revenue_stack") or {}
    products = revenue_stack.get("products") or revenue_stack.get("results") or []
    allocation_rows = revenue_allocation.get("allocation") or revenue_allocation.get("results") or []
    excluded_rows = revenue_allocation.get("excluded_products") or []
    allocated_ids = {row.get("product_id") for row in allocation_rows}
    allocated_by_product = {
        row.get("product_id"): row for row in allocation_rows
    }
    excluded_by_product = {
        row.get("product_id"): row for row in excluded_rows
    }
    rows = []

    for product in products:
        product_id = product.get("product_id")
        allocation = allocated_by_product.get(product_id)
        excluded = excluded_by_product.get(product_id)
        evidence_mode = "mock_demo" if str(product.get("source", "")).startswith("mock_") else "modelled"
        if product.get("source") == "dispatch_optimizer":
            evidence_mode = "optimizer_modelled"

        if allocation:
            recommendation = "Use in current revenue stack."
            allocation_status = "allocated"
        elif excluded:
            recommendation = excluded.get("exclusion_reason") or "Not selected by allocation constraints."
            allocation_status = "excluded"
        else:
            recommendation = "Keep as optional upside until allocation is refreshed."
            allocation_status = "not_allocated"

        rows.append(
            {
                "product_id": product_id,
                "status": product.get("status"),
                "eligibility_status": product.get("eligibility_status"),
                "evidence_mode": evidence_mode,
                "estimated_revenue_eur": product.get("estimated_revenue_eur"),
                "allocated_revenue_eur": (allocation or {}).get("expected_revenue_eur"),
                "allocation_status": allocation_status,
                "business_meaning": revenue_product_meaning(product_id, allocation_status),
                "next_action": recommendation,
                "production_upgrade": revenue_product_production_upgrade(product_id),
            }
        )

    rows = sorted(rows, key=lambda row: numeric(row.get("estimated_revenue_eur")), reverse=True)
    total_visible = sum_numeric(row.get("estimated_revenue_eur") for row in rows)
    total_allocated = sum_numeric(row.get("allocated_revenue_eur") for row in rows)

    return {
        "status": "ok" if rows else "not_found",
        "business_answer": (
            f"The demo revenue stack has {len(rows)} product(s), "
            f"{round(total_visible, 2)} EUR visible opportunity, and "
            f"{round(total_allocated, 2)} EUR allocated under current battery constraints."
        ),
        "highest_value_product": rows[0] if rows else None,
        "rows": rows,
    }


def build_settlement_explainer(settlement):
    payload = settlement.get("settlement") or {}
    summary = payload.get("summary") or {}
    variance_drivers = payload.get("variance_drivers") or []
    expected = numeric(summary.get("expected_pnl_eur"))
    paper = numeric(summary.get("paper_pnl_eur"))
    realized = summary.get("realized_pnl_eur")
    realized_text = realized if realized is not None else "not available"
    paper_delta = round(paper - expected, 2)

    if not payload:
        short_answer = "Settlement proof has not been generated yet."
    elif realized is None:
        short_answer = (
            "The demo has paper settlement evidence, but production settlement still needs realized records."
        )
    else:
        short_answer = (
            f"Settlement can be explained: expected PnL is {round(expected, 2)}, "
            f"paper PnL is {round(paper, 2)}, and realized PnL is {realized_text}."
        )

    return {
        "status": payload.get("status") or settlement.get("status"),
        "short_answer": short_answer,
        "expected_pnl_eur": summary.get("expected_pnl_eur"),
        "paper_pnl_eur": summary.get("paper_pnl_eur"),
        "realized_pnl_eur": realized,
        "paper_delta_eur": summary.get("paper_delta_eur", paper_delta),
        "primary_variance_driver": payload.get("primary_variance_driver"),
        "human_variance_explanation": build_variance_explanation(variance_drivers),
        "next_action": (payload.get("recommended_actions") or ["Attach production settlement records."])[0],
        "production_record_needed": [
            "exchange award or execution confirmation",
            "metered delivery record",
            "settlement statement",
            "variance attribution against the forecast and bid package",
        ],
        "variance_drivers": variance_drivers[:5],
    }


def build_connector_onboarding(market):
    integrations = market.get("integrations") or []
    rows = []
    for route in sorted(integrations, key=lambda item: numeric(item.get("priority", 99))):
        if route.get("production_readiness_tier") == "production_ready":
            continue

        missing_credentials = route.get("missing_credentials") or route.get("route_missing_env_keys") or []
        rows.append(
            {
                "adapter_id": route.get("adapter_id"),
                "adapter_name": route.get("adapter_name"),
                "family": route.get("family"),
                "current_mode": "paper_or_preview" if route.get("paper_supported") else "planned",
                "production_readiness_tier": route.get("production_readiness_tier"),
                "readiness_score": route.get("readiness_score"),
                "first_credential": missing_credentials[0] if missing_credentials else "-",
                "missing_credentials": missing_credentials[:5],
                "next_action": route.get("next_integration_action") or route.get("next_connection_action"),
                "business_value": connector_business_value(route),
            }
        )

    first = rows[0] if rows else None
    return {
        "status": "production_ready" if not rows else "onboarding_required",
        "business_answer": (
            f"Configure {first['adapter_name']} first: {first['next_action']}"
            if first
            else "All configured routes are production-ready."
        ),
        "rows": rows[:8],
    }


def build_persona_playbooks(gaps):
    top_by_id = {gap["gap_id"]: gap for gap in gaps}
    return [
        playbook(
            "asset_owner",
            "What should I tell the owner this week?",
            "Use revenue and settlement evidence; separate demo-ready proof from production records.",
            top_by_id.get("revenue_proof"),
        ),
        playbook(
            "investor_lender",
            "Is this bankable or still mock-backed?",
            "Focus on revenue durability, forecast trust, downside proof, and production settlement gaps.",
            top_by_id.get("settlement_proof"),
        ),
        playbook(
            "trading_desk",
            "Can I trade, paper trade, or wait?",
            "Use forecast trust, market readiness, and settlement evidence to choose paper, supervised, or hold.",
            top_by_id.get("market_readiness"),
        ),
        playbook(
            "market_operations",
            "Which connector should I configure first?",
            "Prioritize the first route that unlocks forecast, market, or settlement evidence.",
            top_by_id.get("market_readiness"),
        ),
        playbook(
            "risk_compliance",
            "Can this decision be defended?",
            "Check whether evidence is mock-ready, demo-ready, or production-ready before approval.",
            top_by_id.get("settlement_proof"),
        ),
    ]


def build_revenue_gap(revenue, revenue_allocation):
    summary = revenue.get("summary") or {}
    revenue_stack = revenue.get("revenue_stack") or {}
    products = revenue_stack.get("products") or revenue_stack.get("results") or []
    blocked_products = [
        product
        for product in products
        if product.get("eligibility_status") == "not_eligible"
        or product.get("status") in ["blocked", "missing_forecast"]
        or bool(product.get("blocking_reasons"))
    ]
    review_products = [
        product
        for product in products
        if product.get("status") in ["assumption_required", "review"]
        or bool(product.get("missing_inputs"))
        or bool(product.get("review_warnings"))
    ]
    blocked_value = sum_numeric(product.get("estimated_revenue_eur") for product in blocked_products)
    total_revenue = numeric(summary.get("total_estimated_revenue_eur"))
    allocation_available = bool(summary.get("allocation_available"))
    missing_inputs = dedupe(
        input_name
        for product in [*blocked_products, *review_products]
        for input_name in (product.get("missing_inputs") or [])
    )
    top_products = sorted(
        [*blocked_products, *review_products],
        key=lambda product: numeric(product.get("estimated_revenue_eur")),
        reverse=True,
    )[:5]

    open_issue_count = len(blocked_products) + len(review_products)
    status = "ready" if open_issue_count == 0 and allocation_available else "review"
    severity = "high" if blocked_products else "medium" if review_products or not allocation_available else "low"

    if blocked_products:
        title = f"{len(blocked_products)} revenue product(s) are blocked"
    elif review_products:
        title = f"{len(review_products)} revenue product(s) need assumptions"
    elif not allocation_available:
        title = "Revenue allocation has not been generated"
    else:
        title = "Revenue proof is ready"

    return gap(
        gap_id="revenue_proof",
        domain="Revenue proof",
        title=title,
        severity=severity,
        status=status,
        why_it_matters=(
            "Owners and investors need to know which revenue is real, which value is only modelled, "
            "and which products are blocked before trusting the commercial story."
        ),
        business_impact=(
            f"Current modelled revenue is {round(total_revenue, 2)} EUR. "
            f"Blocked products carry {round(blocked_value, 2)} EUR of visible blocked value; "
            "products with no estimate may hide additional upside."
        ),
        current_evidence=[
            f"{summary.get('eligible_product_count', 0)} of {summary.get('product_count', len(products))} products are eligible.",
            f"{summary.get('blocked_product_count', len(blocked_products))} products are blocked.",
            f"{summary.get('review_product_count', len(review_products))} products need review.",
        ],
        missing_evidence=missing_inputs
        or [
            "Product-level unblock reason and revenue-at-risk estimate.",
            "Revenue allocation evidence across eligible markets.",
        ],
        next_action=(
            "Open Revenue Assurance, resolve the product blockers with the largest commercial impact, "
            "then run revenue allocation."
        ),
        source_page="Revenue Assurance",
        source_route="/revenue",
        source_endpoint="/assets/{asset_id}/revenue-summary",
        owner_personas=["asset_owner", "revenue_analyst", "executive", "investor_lender"],
        related_rows=[product_summary(product) for product in top_products],
        metrics={
            "total_estimated_revenue_eur": total_revenue,
            "blocked_visible_value_eur": round(blocked_value, 2),
            "blocked_product_count": len(blocked_products),
            "review_product_count": len(review_products),
            "allocation_available": allocation_available,
            "allocation_status": revenue_allocation.get("status"),
        },
    )


def build_settlement_gap(settlement, asset=None):
    settlement_payload = settlement.get("settlement") or {}
    settlement_status = settlement_payload.get("status") or settlement.get("status")
    summary = settlement_payload.get("summary") or {}
    variance_drivers = settlement_payload.get("variance_drivers") or []
    evidence_status = settlement_payload.get("evidence_status") or {}
    missing_evidence = [
        label.replace("_", " ")
        for label, value in evidence_status.items()
        if value in ["missing", "not_found", None]
    ]
    material_drivers = [
        driver for driver in variance_drivers if driver.get("severity") in ["medium", "high"]
    ]

    demo_asset = is_demo_asset(asset) if not isinstance(asset, dict) else False
    realized_available = evidence_status.get("realized_dispatch") not in ["missing", "not_found", None]

    if settlement.get("status") != "ok" or not settlement_payload:
        status = "blocked"
        severity = "high"
        title = "Settlement evidence has not been generated"
        missing_evidence = ["proposal, paper trade, and settlement reconciliation run"]
    elif demo_asset and realized_available:
        status = "demo_ready"
        severity = "medium" if material_drivers else "low"
        title = "Mock settlement proof is complete; production settlement still needs real records"
    elif settlement_status != "settled":
        status = "review"
        severity = "high" if material_drivers else "medium"
        title = "Settlement is not fully proven against realized evidence"
    elif material_drivers:
        status = "review"
        severity = "medium"
        title = "Settlement has material variance drivers"
    else:
        status = "ready"
        severity = "low"
        title = "Settlement proof is ready"

    return gap(
        gap_id="settlement_proof",
        domain="Settlement proof",
        title=title,
        severity=severity,
        status=status,
        why_it_matters=(
            "Commercial users need to separate modelled revenue from paper execution and realized settlement "
            "before reporting value externally."
        ),
        business_impact=(
            f"Expected PnL is {summary.get('expected_pnl_eur', '-')}; "
            f"paper PnL is {summary.get('paper_pnl_eur', '-')}; "
            f"realized PnL is {summary.get('realized_pnl_eur', '-')}. "
            f"Primary variance driver: {settlement_payload.get('primary_variance_driver', 'not available')}."
        ),
        current_evidence=[
            f"Settlement status: {settlement_status or 'not available'}",
            f"Paper delta: {summary.get('paper_delta_eur', '-')}",
            f"Realized delta: {summary.get('realized_delta_eur', '-')}",
        ],
        missing_evidence=missing_evidence
        or [driver.get("message") for driver in material_drivers]
        or ["No material settlement evidence gap detected."],
        next_action=(
            (settlement_payload.get("recommended_actions") or [None])[0]
            or "Keep settlement reconciliation attached to the audit packet."
        ),
        source_page="Settlement Evidence",
        source_route="/execution/settlement",
        source_endpoint="/assets/{asset_id}/settlement/latest",
        owner_personas=["asset_owner", "investor_lender", "client_success", "risk_compliance"],
        related_rows=variance_drivers[:5],
        metrics={
            "expected_pnl_eur": summary.get("expected_pnl_eur"),
            "paper_pnl_eur": summary.get("paper_pnl_eur"),
            "realized_pnl_eur": summary.get("realized_pnl_eur"),
            "paper_delta_eur": summary.get("paper_delta_eur"),
            "realized_delta_eur": summary.get("realized_delta_eur"),
        },
    )


def build_market_gap(market, asset=None):
    summary = market.get("summary") or {}
    integrations = market.get("integrations") or []
    blocked_routes = [
        route
        for route in integrations
        if route.get("production_readiness_tier") != "production_ready"
    ]
    top_routes = sorted(
        blocked_routes,
        key=lambda route: (
            numeric(route.get("priority", 99)),
            -numeric(route.get("readiness_score")),
        ),
    )[:5]
    production_ready_count = int(summary.get("production_ready_count") or 0)
    credential_blocked = int(summary.get("credential_blocked_route_count") or 0)
    live_submission = int(summary.get("live_submission_count") or 0)

    demo_asset = is_demo_asset(asset) if not isinstance(asset, dict) else False
    preview_or_paper_count = int(summary.get("preview_ready_count") or 0) + len(
        [route for route in integrations if route.get("paper_supported")]
    )

    if demo_asset and preview_or_paper_count:
        status = "demo_ready"
        severity = "medium"
        title = "Mock market readiness is available; production route is not connected"
    elif production_ready_count == 0:
        status = "blocked"
        severity = "high"
        title = "No production-ready market route is available"
    elif blocked_routes:
        status = "review"
        severity = "medium"
        title = "Some market routes still need production evidence"
    else:
        status = "ready"
        severity = "low"
        title = "Market readiness is production-ready"

    missing_controls = dedupe(
        control
        for route in top_routes
        for control in [
            *(route.get("missing_controls") or []),
            *(route.get("missing_credentials") or []),
            *(route.get("route_missing_env_keys") or []),
        ]
    )[:8]

    return gap(
        gap_id="market_readiness",
        domain="Market readiness",
        title=title,
        severity=severity,
        status=status,
        why_it_matters=(
            "A profitable signal does not create tradable value until the relevant exchange, data, telemetry, "
            "and settlement routes are credentialed and operationally controlled."
        ),
        business_impact=(
            f"{production_ready_count} of {summary.get('connector_count', len(integrations))} routes are production-ready. "
            f"{preview_or_paper_count} route(s) have demo, paper, or preview evidence. "
            f"{credential_blocked} routes are credential-blocked and {live_submission} routes support live submission."
        ),
        current_evidence=[
            f"Connector status: {market.get('connector_status', '-')}",
            f"Average readiness score: {summary.get('average_readiness_score', '-')}",
            f"Missing credentials: {summary.get('missing_credential_count', '-')}",
        ],
        missing_evidence=missing_controls
        or ["Market credentials, handshake evidence, and production controls."],
        next_action=(
            (market.get("recommended_actions") or [None])[0]
            or "Complete the highest-priority market connector controls."
        ),
        source_page="Market Access & Data",
        source_route="/execution/market-connectors",
        source_endpoint="/execution/market-connectors/readiness?country=Germany&asset_id={asset_id}",
        owner_personas=["market_operations", "trading_desk", "automation_operator", "risk_compliance"],
        related_rows=[market_route_summary(route) for route in top_routes],
        metrics={
            "connector_count": summary.get("connector_count"),
            "production_ready_count": production_ready_count,
            "credential_blocked_route_count": credential_blocked,
            "live_submission_count": live_submission,
            "average_readiness_score": summary.get("average_readiness_score"),
        },
    )


def build_forecast_gap(forecast):
    score = numeric(forecast.get("confidence_score"))
    band = forecast.get("confidence_band") or "unknown"
    eligibility = forecast.get("automation_eligibility")
    status = "ready" if band == "high" else "review" if band == "medium" else "blocked"
    severity = "low" if band == "high" else "medium" if band == "medium" else "high"
    evidence = forecast.get("evidence") or []

    if forecast.get("status") == "insufficient_history":
        title = "Forecast trust needs actual-price history"
        missing_evidence = ["forecast-vs-actual performance runs", "actual price evidence"]
    elif band == "low":
        title = "Forecast confidence is too low for normal automation"
        missing_evidence = ["lower forecast error", "variance explanation", "more recent performance runs"]
    elif band == "medium":
        title = "Forecast can be used with reduced bid sizing"
        missing_evidence = ["additional realized performance before full-size bidding"]
    else:
        title = "Forecast trust is ready"
        missing_evidence = ["No material forecast gap detected."]

    return gap(
        gap_id="forecast_trust",
        domain="Forecast trust",
        title=title,
        severity=severity,
        status=status,
        why_it_matters=(
            "Forecast confidence should directly control bid size and automation mode, because forecast error "
            "can turn a good dispatch plan into poor execution."
        ),
        business_impact=(
            f"Forecast confidence is {band} ({score}/100). "
            f"Automation eligibility is {eligibility or 'not available'}."
        ),
        current_evidence=[
            forecast.get("reason") or "No forecast confidence reason returned.",
            f"Run count: {forecast.get('run_count', 0)}",
            f"Risk policy: {forecast.get('risk_policy', {})}",
        ],
        missing_evidence=missing_evidence,
        next_action=(
            "Run forecast-vs-actual backtesting and keep automation in paper or reduced-size mode until confidence improves."
            if status != "ready"
            else "Keep forecast-vs-actual monitoring current."
        ),
        source_page="Forecast Trust",
        source_route="/forecasts",
        source_endpoint="/assets/{asset_id}/forecast-confidence",
        owner_personas=["forecast_quant", "trading_desk", "automation_operator", "executive"],
        related_rows=evidence[:5],
        metrics={
            "confidence_score": score,
            "confidence_band": band,
            "automation_eligibility": eligibility,
            "run_count": forecast.get("run_count", 0),
            "volume_multiplier": (forecast.get("risk_policy") or {}).get("volume_multiplier"),
            "price_buffer_eur_per_mwh": (forecast.get("risk_policy") or {}).get("price_buffer_eur_per_mwh"),
        },
    )


def gap(
    gap_id,
    domain,
    title,
    severity,
    status,
    why_it_matters,
    business_impact,
    current_evidence,
    missing_evidence,
    next_action,
    source_page,
    source_route,
    source_endpoint,
    owner_personas,
    related_rows,
    metrics,
):
    return {
        "gap_id": gap_id,
        "domain": domain,
        "title": title,
        "severity": severity,
        "status": status,
        "why_it_matters": why_it_matters,
        "business_impact": business_impact,
        "current_evidence": [item for item in current_evidence if item],
        "missing_evidence": [item for item in missing_evidence if item],
        "next_action": next_action,
        "source_page": source_page,
        "source_route": source_route,
        "source_endpoint": source_endpoint,
        "owner_personas": owner_personas,
        "related_rows": related_rows,
        "metrics": metrics,
    }


def build_business_answer(evidence_mode, open_gaps, production_gaps, live_production_gaps, top_gap):
    if evidence_mode == "mock":
        if live_production_gaps:
            return (
                "Mock Data mode has a complete simulated evidence chain for product walkthroughs, "
                "client-style explanations, and agent interaction. Live Data mode is available as a "
                "separate production validation view for real connectors, telemetry, and settlement records."
            )
        return (
            "Mock Data mode has a complete simulated evidence chain, and the same domains are also "
            "clear under the current live-readiness checks."
        )

    if not open_gaps:
        if production_gaps:
            return (
                "The current platform evidence chain is complete enough for a client-style review. "
                f"{len(production_gaps)} domain(s) still need production connectors or real records before live use."
            )
        return "The four highest-value evidence domains are ready for the next review."

    return (
        f"There are {len(open_gaps)} priority gap(s). The first one to fix is "
        f"{top_gap['domain'].lower()}: {top_gap['title'].lower()}. "
        f"Next action: {top_gap['next_action']}"
    )


def normalize_evidence_mode(evidence_mode):
    mode = str(evidence_mode or "live").strip().lower()
    if mode in ["mock", "demo", "simulated", "simulation"]:
        return "mock"
    return "live"


def apply_mock_evidence_mode(gaps):
    return [mock_gap(gap_item) for gap_item in gaps]


def mock_gap(gap_item):
    simulated_evidence = {
        "revenue_proof": [
            "Simulated revenue stack is generated for all configured products.",
            "Mock allocation is available for the current battery constraints.",
            "Product-level assumptions are explainable in Revenue Assurance.",
        ],
        "settlement_proof": [
            "Mock proposal, paper execution, and settlement reconciliation are available.",
            "Simulated variance drivers are attached for explainability.",
            "The report can show expected, paper, and simulated realized PnL.",
        ],
        "market_readiness": [
            "Mock market routes are available for preview and paper execution.",
            "Simulated connector readiness explains which live credential would replace each mock source.",
            "The agent can discuss market access without claiming live submission.",
        ],
        "forecast_trust": [
            "Mock forecast-vs-actual evidence is available for confidence scoring.",
            "Bid-sizing guidance can be explained from simulated forecast error.",
            "The production upgrade path is official actual-price ingestion.",
        ],
    }
    titles = {
        "revenue_proof": "Mock revenue proof is complete",
        "settlement_proof": "Mock settlement proof is complete",
        "market_readiness": "Mock market readiness is complete",
        "forecast_trust": "Mock forecast trust proof is complete",
    }
    gap_id = gap_item.get("gap_id")
    return {
        **gap_item,
        "title": titles.get(gap_id, f"Mock {gap_item.get('domain', 'evidence')} is complete"),
        "severity": "low",
        "status": "ready",
        "current_evidence": simulated_evidence.get(gap_id, gap_item.get("current_evidence") or []),
        "missing_evidence": [
            "No mock evidence is missing. Switch to Live Data mode to check production connectors and real records."
        ],
        "next_action": (
            "Use the mock evidence in the walkthrough, then switch to Live Data mode before making production claims."
        ),
        "metrics": {
            **(gap_item.get("metrics") or {}),
            "mock_evidence_complete": True,
            "live_status_before_mock_override": gap_item.get("status"),
        },
    }


def playbook(persona_id, question, answer_strategy, gap_item):
    return {
        "persona_id": persona_id,
        "question": question,
        "answer_strategy": answer_strategy,
        "default_short_answer": (
            f"Start with {gap_item['domain'].lower()}: {gap_item['title']}"
            if gap_item
            else "No material gap is visible for this persona."
        ),
        "evidence_to_use": (
            [
                gap_item["business_impact"],
                gap_item["next_action"],
                f"Check {gap_item['source_page']} ({gap_item['source_route']}).",
            ]
            if gap_item
            else []
        ),
    }


def production_upgrade_for_gap(gap_id):
    mapping = {
        "revenue_proof": "Replace mock revenue assumptions with exchange prices, product prequalification, dispatch telemetry, and settlement-backed revenue.",
        "settlement_proof": "Connect award, meter, and settlement statement records for realized revenue proof.",
        "market_readiness": "Configure market/data credentials, run connector handshakes, and certify supervised live submission.",
        "forecast_trust": "Replace mock actual prices with official actual-price ingestion and continuous forecast-vs-actual monitoring.",
    }
    return mapping.get(gap_id, "Replace mock evidence with production source records.")


def evidence_mode_language(gap_item):
    if gap_item["status"] == "demo_ready":
        return f"{gap_item['domain']} is demo-ready, but production evidence is still required."
    if gap_item["status"] == "ready":
        return f"{gap_item['domain']} is ready for the current evidence mode."
    return f"{gap_item['domain']} still has an open evidence gap: {gap_item['title']}"


def revenue_product_meaning(product_id, allocation_status):
    if allocation_status == "allocated":
        return "Included in the current value stack."
    if product_id in ["fcr_capacity", "afrr_capacity", "mfrr_capacity"]:
        return "Ancillary-services upside exists, but battery capacity allocation or production proof may limit it."
    if product_id == "intraday_arbitrage":
        return "Intraday upside is useful as optional trading flexibility."
    if product_id == "imbalance_avoidance":
        return "Imbalance value reduces downside rather than only adding merchant upside."
    return "Revenue route is available for commercial review."


def revenue_product_production_upgrade(product_id):
    mapping = {
        "day_ahead_arbitrage": "Use exchange day-ahead prices, executed orders, fees, telemetry, and settlement.",
        "intraday_arbitrage": "Use intraday order book/liquidity, execution cost, and fill evidence.",
        "fcr_capacity": "Use FCR price curves, prequalification certificate, availability telemetry, and TSO settlement.",
        "afrr_capacity": "Use aFRR price curves, prequalification evidence, activation assumptions, and TSO settlement.",
        "mfrr_capacity": "Use mFRR price curves, activation workflow, BRP evidence, and TSO settlement.",
        "imbalance_avoidance": "Use imbalance prices, schedule deviations, and BRP settlement records.",
    }
    return mapping.get(product_id, "Replace mock assumption with production market and settlement evidence.")


def build_variance_explanation(variance_drivers):
    if not variance_drivers:
        return "No material variance driver is visible."

    return " ".join(
        str(driver.get("message") or driver.get("driver"))
        for driver in variance_drivers[:3]
    )


def connector_business_value(route):
    family = route.get("family")
    if family == "data":
        return "Unlocks forecast trust, settlement comparison, and automation confidence."
    if family == "ancillary":
        return "Unlocks reserve revenue and ancillary-service market access."
    if str(route.get("adapter_id", "")).startswith("epex"):
        return "Unlocks German day-ahead or intraday trading route evidence."
    return "Unlocks production evidence for automated trading."


def product_summary(product):
    return {
        "product_id": product.get("product_id"),
        "status": product.get("status"),
        "eligibility_status": product.get("eligibility_status"),
        "estimated_revenue_eur": product.get("estimated_revenue_eur"),
        "blocking_reasons": product.get("blocking_reasons") or [],
        "missing_inputs": product.get("missing_inputs") or [],
        "review_warnings": product.get("review_warnings") or [],
    }


def market_route_summary(route):
    return {
        "adapter_id": route.get("adapter_id"),
        "adapter_name": route.get("adapter_name"),
        "production_readiness_tier": route.get("production_readiness_tier"),
        "readiness_score": route.get("readiness_score"),
        "missing_controls": route.get("missing_controls") or [],
        "missing_credentials": route.get("missing_credentials") or [],
        "next_integration_action": route.get("next_integration_action"),
    }


def safe_call(builder):
    try:
        return builder()
    except Exception as error:
        return {
            "status": "error",
            "message": str(error),
        }


def severity_rank(severity):
    return {
        "low": 1,
        "medium": 2,
        "high": 3,
    }.get(severity, 0)


def numeric(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def sum_numeric(values):
    return round(sum(numeric(value) for value in values), 2)


def dedupe(values):
    seen = set()
    result = []
    for value in values:
        if not value:
            continue
        text = str(value)
        if text in seen:
            continue
        seen.add(text)
        result.append(text)
    return result
