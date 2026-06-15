from backend.db.repositories.workflow_repository import get_latest_workflow_run
from backend.execution.pretrade_proposal import latest_execution_proposal
from backend.revenue.revenue_stack_allocator import load_latest_revenue_stack_allocation
from backend.revenue.revenue_stack_runner import load_latest_asset_revenue_stack
from backend.services.asset_signal_store import load_asset_latest_signal
from backend.services.business_decision_service import get_or_build_latest_business_decision
from backend.services.data_completeness_service import build_asset_data_completeness


def build_asset_cockpit(asset_id):
    signal = load_asset_latest_signal(asset_id)
    revenue_stack = load_latest_asset_revenue_stack(asset_id)
    revenue_allocation = load_latest_revenue_stack_allocation(asset_id)
    decision = get_or_build_latest_business_decision(asset_id)
    workflow_run = get_latest_workflow_run(asset_id)
    execution = latest_execution_proposal(asset_id)
    completeness = build_asset_data_completeness(asset_id)

    signal_data = signal.get("data", {}) if signal.get("status") == "ok" else {}
    summary = signal_data.get("summary", {})
    metadata = signal_data.get("metadata", {})
    revenue_products = resolve_revenue_products(revenue_stack)
    latest_execution = (
        execution.get("proposal")
        if execution.get("status") == "ok"
        else None
    )

    return {
        "status": "ok",
        "asset_id": asset_id,
        "cockpit": {
            "asset_id": asset_id,
            "latest_signal": signal,
            "signal_summary": summary,
            "signal_metadata": metadata,
            "dispatch": signal_data.get("dispatch", []),
            "revenue_stack": revenue_stack,
            "revenue_products": revenue_products,
            "revenue_allocation": revenue_allocation,
            "business_decision": decision,
            "workflow_run": (workflow_run or {}).get("payload"),
            "execution_proposal": latest_execution,
            "data_completeness": completeness,
            "business_kpis": build_business_kpis(
                summary=summary,
                revenue_stack=revenue_stack,
                revenue_products=revenue_products,
                decision=decision,
                completeness=completeness,
            ),
            "enterprise_maturity": build_enterprise_maturity(
                summary=summary,
                metadata=metadata,
                revenue_stack=revenue_stack,
                revenue_products=revenue_products,
                decision=decision,
                workflow_run=workflow_run,
                execution=latest_execution,
                completeness=completeness,
            ),
            "recommended_next_actions": build_next_actions(
                completeness=completeness,
                execution=latest_execution,
                signal_summary=summary,
            ),
        },
    }


def resolve_revenue_products(revenue_stack):
    if revenue_stack.get("results"):
        return revenue_stack.get("results", [])

    if revenue_stack.get("products"):
        return revenue_stack.get("products", [])

    return []


def build_business_kpis(
    summary,
    revenue_stack,
    revenue_products,
    decision,
    completeness,
):
    return {
        "signal": summary.get("signal", "-"),
        "opportunity_level": summary.get("opportunity_level", "-"),
        "expected_pnl_eur": numeric(summary.get("total_pnl_eur")),
        "profit_per_mw_day": numeric(summary.get("profit_per_mw_day")),
        "modelled_revenue_eur": numeric(
            revenue_stack.get("total_estimated_revenue_eur")
        ),
        "revenue_product_count": len(revenue_products),
        "decision_status": decision.get("recommendation_status", "-"),
        "decision_expected_pnl_eur": numeric(decision.get("expected_pnl_eur")),
        "data_completeness_score": completeness.get("score", 0),
        "data_readiness": completeness.get("readiness", "-"),
    }


def build_next_actions(completeness, execution, signal_summary):
    actions = list(completeness.get("next_actions", []))

    if signal_summary.get("signal") != "ACTION":
        actions.append("Refresh forecast or run forecast comparison before dispatch.")

    if execution is None:
        actions.append("Build pre-trade proposal to convert dispatch into draft orders.")

    if not actions:
        actions.append("Review proposed orders and keep execution in advisory mode.")

    return dedupe(actions)


def build_enterprise_maturity(
    summary,
    metadata,
    revenue_stack,
    revenue_products,
    decision,
    workflow_run,
    execution,
    completeness,
):
    score = 0
    strengths = []
    gaps = []
    next_actions = []

    forecast_source = (
        metadata.get("forecast_provider")
        or metadata.get("forecast_model")
        or metadata.get("source")
    )
    expected_pnl = numeric(summary.get("total_pnl_eur"))
    product_count = len(revenue_products)
    completeness_score = numeric(completeness.get("score"))
    decision_payload = decision.get("decision", {})
    proposal_orders = execution.get("orders", []) if execution else []
    automation_blockers = execution.get("automation_blockers", []) if execution else []

    if forecast_source:
        score += 10
        strengths.append("Forecast lineage is visible to the business user.")

        if forecast_source not in {"local_saved_forecast", "demo", "processed_forecast_csv"}:
            score += 5
            strengths.append("Forecast is connected to a named external or model provider.")
        else:
            gaps.append("Forecast still needs live-market validation and actual-price backtesting.")
            next_actions.append("Run forecast-vs-actual backtests before treating the model as trusted.")
    else:
        gaps.append("Forecast lineage is missing.")
        next_actions.append("Persist every forecast as a provider/model snapshot.")

    if summary.get("signal") == "ACTION" and expected_pnl > 0:
        score += 15
        strengths.append("The optimizer converts forecast data into a positive dispatch decision.")
    elif summary:
        score += 6
        gaps.append("Latest signal does not currently create a positive dispatch case.")
    else:
        gaps.append("No latest dispatch signal is available.")
        next_actions.append("Generate an asset-level signal from the selected forecast.")

    if product_count:
        score += 15
        strengths.append(f"{product_count} revenue product(s) are assessed beyond simple arbitrage.")
    else:
        gaps.append("Revenue stack is not populated for this asset.")
        next_actions.append("Run revenue stack modelling for merchant, ancillary, and hedge cases.")

    if decision_payload.get("eeg_eligible") or decision.get("recommendation_status"):
        score += 10
        strengths.append("Commercial recommendation is linked to regulatory and product evidence.")
    else:
        gaps.append("Regulatory evidence is not linked to the commercial decision.")

    if workflow_run:
        score += 10
        strengths.append("A workflow audit record links forecast, signal, revenue, and decision outputs.")
    else:
        gaps.append("No end-to-end workflow audit run is linked.")
        next_actions.append("Run an audited workflow to create client-facing evidence.")

    if completeness_score >= 80:
        score += 10
        strengths.append("Evidence readiness is high enough for management review.")
    elif completeness_score:
        score += round(completeness_score / 10, 1)
        gaps.append("Evidence readiness is incomplete.")
        next_actions.extend(completeness.get("next_actions", []))
    else:
        gaps.append("Evidence readiness has not been scored.")

    if proposal_orders:
        score += 8
        strengths.append("Dispatch can be translated into draft market-order proposals.")
    else:
        gaps.append("No pre-trade proposal exists for the latest signal.")
        next_actions.append("Build a pre-trade proposal after each dispatch signal.")

    if automation_blockers:
        gaps.append("Automated trading blockers remain before live market submission.")
        next_actions.append("Connect market API, telemetry, approvals, and order guardrails.")
    else:
        score += 7
        strengths.append("No automation blockers are currently reported.")

    if decision_payload.get("hedged_revenue_eur") is not None:
        score += 5
        strengths.append("Hedging economics are visible beside merchant revenue.")
    else:
        gaps.append("Hedged revenue is not yet part of the operating recommendation.")
        next_actions.append("Compare merchant dispatch with floor, tolling, and availability contracts.")

    score = min(round(score, 1), 100)

    return {
        "score": score,
        "level": enterprise_level(score),
        "display_level": enterprise_display_level(score),
        "automation_readiness": automation_readiness(execution),
        "bankability_evidence_count": len(strengths),
        "differentiation_score": min(score + 10 if workflow_run else score, 100),
        "strengths": dedupe(strengths)[:8],
        "gaps": dedupe(gaps)[:8],
        "next_moat_actions": dedupe(next_actions)[:8],
        "competitor_positioning": (
            "Differentiates through auditable forecast-to-decision evidence, "
            "Germany-specific regulatory context, and hedge-aware commercial posture. "
            "Live trading integration is still required before claiming automated market operation."
        ),
    }


def enterprise_level(score):
    if score >= 85:
        return "automation_candidate"

    if score >= 70:
        return "bankable_advisory"

    if score >= 50:
        return "commercial_prototype"

    return "research_mode"


def enterprise_display_level(score):
    if score >= 85:
        return "Automation candidate"

    if score >= 70:
        return "Bankable advisory"

    if score >= 50:
        return "Commercial prototype"

    return "Research mode"


def automation_readiness(execution):
    if not execution:
        return "proposal_missing"

    if execution.get("automation_blockers"):
        return "blocked"

    if execution.get("approval_status") == "requires_approval":
        return "human_approval_required"

    return "ready_for_adapter"


def numeric(value):
    try:
        return round(float(value), 2)
    except (TypeError, ValueError):
        return 0.0


def dedupe(values):
    seen = set()
    result = []

    for value in values:
        if value in seen:
            continue

        seen.add(value)
        result.append(value)

    return result



