from datetime import datetime

from backend.db.repositories.execution_repository import (
    get_latest_execution_paper_trade,
    get_latest_execution_proposal,
)
from backend.db.repositories.settlement_repository import (
    get_latest_settlement_reconciliation,
)
from backend.execution.automation_control import automation_control_status
from backend.execution.automation_guardrails import latest_automation_guardrails
from backend.execution.multi_market_allocator import build_multi_market_allocation
from backend.revenue.revenue_stack_runner import load_latest_asset_revenue_stack
from backend.services.asset_signal_store import load_asset_latest_signal


def build_strategy_intent(asset_id):
    signal = load_asset_latest_signal(asset_id)
    revenue_stack = load_latest_asset_revenue_stack(asset_id)
    allocation = build_multi_market_allocation(asset_id)
    guardrails = latest_automation_guardrails(asset_id)
    control = automation_control_status(
        asset_id,
        allocation=allocation,
        guardrails=guardrails,
    )
    proposal_record = get_latest_execution_proposal(asset_id)
    paper_trade_record = get_latest_execution_paper_trade(asset_id)
    settlement_record = get_latest_settlement_reconciliation(asset_id)

    signal_summary = ((signal.get("data") or {}).get("summary") or {})
    revenue_products = revenue_stack.get("products") or revenue_stack.get("results") or []
    proposal = (proposal_record or {}).get("payload") or {}
    paper_trade = (paper_trade_record or {}).get("payload") or {}
    settlement = (settlement_record or {}).get("payload") or {}
    primary_market = allocation.get("primary_market")
    secondary_market = allocation.get("secondary_market")
    target_markets = build_target_markets(
        allocation=allocation,
        primary_market=primary_market,
        secondary_market=secondary_market,
    )
    strategy_mode = classify_strategy_mode(
        allocation=allocation,
        control=control,
        guardrails=guardrails,
        revenue_products=revenue_products,
        signal_summary=signal_summary,
        target_markets=target_markets,
    )
    dispatch_bias = classify_dispatch_bias(
        control=control,
        signal_summary=signal_summary,
        strategy_mode=strategy_mode,
    )
    confidence = score_strategy_confidence(
        allocation=allocation,
        control=control,
        guardrails=guardrails,
        paper_trade=paper_trade,
        proposal=proposal,
        settlement=settlement,
        signal=signal,
    )
    blocking_evidence = build_blocking_evidence(
        allocation=allocation,
        control=control,
        guardrails=guardrails,
    )
    recommended_next_action = build_recommended_next_action(
        blocking_evidence=blocking_evidence,
        control=control,
        confidence=confidence,
        proposal=proposal,
        strategy_mode=strategy_mode,
    )

    return {
        "status": "ok",
        "asset_id": asset_id,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "strategy_mode": strategy_mode,
        "dispatch_bias": dispatch_bias,
        "confidence": confidence,
        "target_markets": target_markets,
        "market_intent": build_market_intent(
            primary_market=primary_market,
            secondary_market=secondary_market,
            strategy_mode=strategy_mode,
        ),
        "why": build_strategy_reasons(
            allocation=allocation,
            control=control,
            confidence=confidence,
            primary_market=primary_market,
            revenue_products=revenue_products,
            signal_summary=signal_summary,
            strategy_mode=strategy_mode,
        ),
        "blocking_evidence": blocking_evidence,
        "recommended_next_action": recommended_next_action,
        "evidence": {
            "automation_mode": control.get("automation_mode"),
            "automation_policy_decision": control.get("policy_decision"),
            "forecast_confidence_score": allocation.get("summary", {}).get(
                "forecast_confidence_score"
            ),
            "forecast_confidence_band": allocation.get("summary", {}).get(
                "forecast_confidence_band"
            ),
            "guardrail_summary": guardrails.get("summary", {}),
            "paper_trade_id": (paper_trade_record or {}).get("paper_trade_id"),
            "proposal_id": (proposal_record or {}).get("execution_proposal_id"),
            "revenue_stack_status": revenue_stack.get("status"),
            "settlement_reconciliation_id": (settlement_record or {}).get(
                "settlement_reconciliation_id"
            ),
            "signal_status": signal.get("status"),
        },
    }


def build_target_markets(allocation, primary_market, secondary_market):
    targets = []

    for index, market in enumerate([primary_market, secondary_market]):
        if not market:
            continue

        targets.append(
            {
                "adapter_id": market.get("adapter_id"),
                "allocated_power_mw": market.get("allocated_power_mw"),
                "expected_revenue_eur": market.get("expected_revenue_eur"),
                "market_name": market.get("market_name"),
                "market_segment": market.get("market_segment"),
                "rank": index + 1,
                "role": "primary" if index == 0 else "secondary",
                "status": market.get("recommendation_status"),
            }
        )

    if targets:
        return targets

    return [
        {
            "adapter_id": market.get("adapter_id"),
            "allocated_power_mw": market.get("allocated_power_mw"),
            "expected_revenue_eur": market.get("expected_revenue_eur"),
            "market_name": market.get("market_name"),
            "market_segment": market.get("market_segment"),
            "rank": index + 1,
            "role": "watchlist",
            "status": market.get("recommendation_status"),
        }
        for index, market in enumerate(allocation.get("allocation", [])[:3])
    ]


def classify_strategy_mode(
    allocation,
    control,
    guardrails,
    revenue_products,
    signal_summary,
    target_markets,
):
    if control.get("automation_mode") == "live_auto_blocked":
        if has_data_blocker(control):
            return "data_recovery"
        return "risk_off"

    if guardrails.get("automation_status") == "blocked":
        return "risk_off"

    if not target_markets or allocation.get("allocation_status") == "blocked":
        return "data_recovery"

    ancillary_revenue = product_revenue(revenue_products, ["fcr", "afrr", "mfrr"])
    wholesale_revenue = product_revenue(revenue_products, ["day_ahead", "intraday"])
    primary_adapter = str(target_markets[0].get("adapter_id") or "")

    if primary_adapter.startswith("regelleistung_") or ancillary_revenue > wholesale_revenue * 1.15:
        return "ancillary_priority"

    if ancillary_revenue > 0 and wholesale_revenue > 0:
        return "hybrid_stack"

    if str(signal_summary.get("signal")).upper() == "ACTION":
        return "arbitrage"

    return "risk_off"


def classify_dispatch_bias(control, signal_summary, strategy_mode):
    if strategy_mode in ["risk_off", "data_recovery"]:
        return "hold"

    if strategy_mode == "ancillary_priority":
        return "reserve_capacity"

    charged = numeric(signal_summary.get("charged_mwh"))
    discharged = numeric(signal_summary.get("discharged_mwh"))

    if control.get("automation_mode") in ["advisory_only", "live_auto_blocked"]:
        return "hold"

    if charged > discharged * 1.1:
        return "charge"

    if discharged > charged * 1.1:
        return "discharge"

    return "hold"


def score_strategy_confidence(
    allocation,
    control,
    guardrails,
    paper_trade,
    proposal,
    settlement,
    signal,
):
    score = 45.0
    allocation_summary = allocation.get("summary", {})
    guardrail_summary = guardrails.get("summary", {})

    score += numeric(allocation_summary.get("forecast_confidence_score")) * 0.25
    score += numeric(control.get("readiness_score")) * 0.2
    score += 10.0 if signal.get("status") == "ok" else -20.0
    score += 8.0 if proposal else -8.0
    score += 8.0 if paper_trade else -6.0
    score += 5.0 if settlement else 0.0
    score -= numeric(guardrail_summary.get("blocked")) * 18.0
    score -= numeric(guardrail_summary.get("review")) * 8.0
    score -= len(control.get("blockers", [])) * 4.0

    value = round(max(0.0, min(100.0, score)), 1)

    return {
        "score": value,
        "band": confidence_band(value),
        "automation_eligible": value >= 70 and not control.get("blockers"),
    }


def build_blocking_evidence(allocation, control, guardrails):
    rows = []

    for blocker in control.get("blockers", []):
        rows.append(
            {
                "source": blocker.get("source"),
                "status": blocker.get("status", "blocked"),
                "message": blocker.get("message"),
                "required_action": blocker.get("message"),
            }
        )

    for item in control.get("remediation_queue", []):
        if item.get("auto_resolvable"):
            continue

        rows.append(
            {
                "source": item.get("source"),
                "status": item.get("severity", "blocked"),
                "message": item.get("message"),
                "required_action": item.get("required_action"),
            }
        )

    for market in allocation.get("excluded_markets", [])[:3]:
        rows.append(
            {
                "source": market.get("adapter_id"),
                "status": "excluded",
                "message": "; ".join(market.get("blocking_reasons", [])),
                "required_action": market.get("operator_next_action"),
            }
        )

    for guardrail in guardrails.get("guardrails", []):
        if guardrail.get("status") in ["blocked", "review"]:
            rows.append(
                {
                    "source": guardrail.get("guardrail"),
                    "status": guardrail.get("status"),
                    "message": guardrail.get("message"),
                    "required_action": guardrail.get("message"),
                }
            )

    return dedupe_rows(rows)


def build_recommended_next_action(
    blocking_evidence,
    confidence,
    control,
    proposal,
    strategy_mode,
):
    next_action = control.get("next_automation_action", {})

    if strategy_mode == "data_recovery":
        return {
            "action": "restore_data_quality",
            "label": "Restore data quality",
            "message": "Refresh stale or missing forecast, price, telemetry, or settlement evidence before trading.",
            "owner": "data_ops",
        }

    if strategy_mode == "risk_off":
        return {
            "action": next_action.get("action", "clear_blockers"),
            "label": next_action.get("label", "Clear Blockers"),
            "message": next_action.get("message") or "Keep the asset out of automated trading until blockers clear.",
            "owner": next_action.get("owner", "automation_control"),
        }

    if not proposal:
        return {
            "action": "build_proposal",
            "label": "Build Proposal",
            "message": "Convert strategy intent into the next automated bid proposal.",
            "owner": "execution_engine",
        }

    if confidence.get("automation_eligible"):
        return {
            "action": next_action.get("action", "run_paper_trade"),
            "label": next_action.get("label", "Run Paper Trade"),
            "message": next_action.get("message") or "Validate the strategy with paper execution before escalation.",
            "owner": next_action.get("owner", "paper_adapter"),
        }

    return {
        "action": "improve_confidence",
        "label": "Improve Confidence",
        "message": "Keep the strategy in paper or supervised mode until forecast, guardrail, and market evidence improves.",
        "owner": "strategy_engine",
    }


def build_market_intent(primary_market, secondary_market, strategy_mode):
    return {
        "primary_adapter_id": (primary_market or {}).get("adapter_id"),
        "primary_market": (primary_market or {}).get("market_name"),
        "secondary_adapter_id": (secondary_market or {}).get("adapter_id"),
        "secondary_market": (secondary_market or {}).get("market_name"),
        "stacking_intent": "stack_markets" if strategy_mode == "hybrid_stack" else "single_route",
    }


def build_strategy_reasons(
    allocation,
    control,
    confidence,
    primary_market,
    revenue_products,
    signal_summary,
    strategy_mode,
):
    reasons = [
        f"Strategy mode is {strategy_mode.replace('_', ' ')}.",
        f"Automation mode is {str(control.get('automation_mode')).replace('_', ' ')}.",
        f"Intent confidence is {confidence.get('band')} at {confidence.get('score')}.",
    ]

    if primary_market:
        reasons.append(
            f"Primary route is {primary_market.get('market_name')} with {primary_market.get('expected_revenue_eur')} EUR expected revenue."
        )

    if str(signal_summary.get("signal")).upper() == "ACTION":
        reasons.append("Latest dispatch signal is actionable.")

    best_product = best_revenue_product(revenue_products)
    if best_product:
        reasons.append(
            f"Highest revenue product is {best_product.get('product_id') or best_product.get('market')}."
        )

    if allocation.get("excluded_markets"):
        reasons.append(
            f"{len(allocation.get('excluded_markets', []))} market route(s) remain excluded by readiness or connector gates."
        )

    return reasons


def has_data_blocker(control):
    return any(
        blocker.get("source") == "freshness"
        for blocker in control.get("blockers", [])
    )


def product_revenue(products, keywords):
    total = 0.0

    for product in products:
        product_id = str(product.get("product_id") or product.get("market") or "").lower()
        if any(keyword in product_id for keyword in keywords):
            total += numeric(
                product.get("risk_adjusted_revenue_eur")
                or product.get("estimated_revenue_eur")
                or product.get("revenue_eur")
            )

    return total


def best_revenue_product(products):
    if not products:
        return None

    return max(
        products,
        key=lambda product: numeric(
            product.get("risk_adjusted_revenue_eur")
            or product.get("estimated_revenue_eur")
            or product.get("revenue_eur")
        ),
    )


def confidence_band(score):
    if score >= 75:
        return "high"

    if score >= 55:
        return "medium"

    if score >= 35:
        return "low"

    return "blocked"


def dedupe_rows(rows):
    seen = set()
    result = []

    for row in rows:
        key = (row.get("source"), row.get("status"), row.get("message"))
        if not row.get("message") or key in seen:
            continue

        seen.add(key)
        result.append(row)

    return result


def numeric(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0



