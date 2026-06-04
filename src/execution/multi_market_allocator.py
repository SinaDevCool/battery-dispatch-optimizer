from datetime import datetime

from src.backtesting.forecast_actual.forecast_confidence import (
    build_forecast_confidence,
)
from src.execution.approval_workflow import latest_execution_approval
from src.execution.automation_policy import market_allowed_by_policy
from src.execution.epex_day_ahead_preview import latest_epex_day_ahead_preview
from src.execution.epex_intraday_auction_preview import (
    latest_epex_intraday_auction_preview,
)
from src.execution.epex_intraday_continuous_preview import (
    latest_epex_intraday_continuous_preview,
)
from src.execution.execution_readiness import build_execution_readiness
from src.execution.market_adapters.registry import get_asset_market_adapter_status
from src.execution.regelleistung_afrr_preview import latest_regelleistung_afrr_preview
from src.execution.regelleistung_fcr_preview import latest_regelleistung_fcr_preview
from src.execution.regelleistung_mfrr_preview import latest_regelleistung_mfrr_preview
from src.revenue.revenue_stack_allocator import (
    load_latest_revenue_stack_allocation,
    run_revenue_stack_allocation,
)


MARKET_ALLOCATION_MAP = [
    {
        "adapter_id": "epex_day_ahead",
        "market_name": "EPEX SPOT Day-Ahead",
        "market_segment": "day_ahead",
        "venue": "EPEX SPOT",
        "commercial_product_id": "day_ahead_arbitrage",
        "execution_role": "base_schedule",
        "preview_loader": latest_epex_day_ahead_preview,
    },
    {
        "adapter_id": "epex_intraday_auction",
        "market_name": "EPEX SPOT Intraday Auction",
        "market_segment": "intraday_auction",
        "venue": "EPEX SPOT",
        "commercial_product_id": "intraday_arbitrage",
        "execution_role": "schedule_refinement",
        "preview_loader": latest_epex_intraday_auction_preview,
    },
    {
        "adapter_id": "epex_intraday_continuous",
        "market_name": "EPEX SPOT Intraday Continuous",
        "market_segment": "intraday_continuous",
        "venue": "EPEX SPOT",
        "commercial_product_id": "intraday_arbitrage",
        "execution_role": "rebalancing",
        "preview_loader": latest_epex_intraday_continuous_preview,
    },
    {
        "adapter_id": "regelleistung_fcr",
        "market_name": "Regelleistung FCR",
        "market_segment": "balancing_capacity",
        "venue": "regelleistung.net",
        "commercial_product_id": "fcr_capacity",
        "execution_role": "reserve_capacity",
        "preview_loader": latest_regelleistung_fcr_preview,
    },
    {
        "adapter_id": "regelleistung_afrr",
        "market_name": "Regelleistung aFRR",
        "market_segment": "balancing_capacity_energy",
        "venue": "regelleistung.net",
        "commercial_product_id": "afrr_capacity",
        "execution_role": "reserve_capacity_energy",
        "preview_loader": latest_regelleistung_afrr_preview,
    },
    {
        "adapter_id": "regelleistung_mfrr",
        "market_name": "Regelleistung mFRR",
        "market_segment": "balancing_capacity_energy",
        "venue": "regelleistung.net",
        "commercial_product_id": "mfrr_capacity",
        "execution_role": "manual_reserve_capacity_energy",
        "preview_loader": latest_regelleistung_mfrr_preview,
    },
]


def build_multi_market_allocation(asset_id, refresh_revenue_stack=False):
    revenue_allocation = load_or_run_revenue_allocation(
        asset_id=asset_id,
        refresh_revenue_stack=refresh_revenue_stack,
    )
    readiness = build_execution_readiness(asset_id)
    adapter_status = get_asset_market_adapter_status(asset_id)
    forecast_confidence = build_forecast_confidence(asset_id)
    approval = latest_execution_approval(asset_id)

    adapters_by_id = {
        adapter.get("adapter_id"): adapter
        for adapter in adapter_status.get("adapters", [])
    }
    allocation_by_product = {
        row.get("product_id"): row
        for row in revenue_allocation.get("allocation", [])
    }
    excluded_by_product = {
        row.get("product_id"): row
        for row in revenue_allocation.get("excluded_products", [])
    }

    candidates = [
        build_market_candidate(
            asset_id=asset_id,
            market=market,
            adapter=adapters_by_id.get(market["adapter_id"], {}),
            commercial_allocation=allocation_by_product.get(
                market["commercial_product_id"]
            ),
            excluded_commercial_product=excluded_by_product.get(
                market["commercial_product_id"]
            ),
            readiness=readiness,
            forecast_confidence=forecast_confidence,
            approval=approval,
        )
        for market in MARKET_ALLOCATION_MAP
    ]

    ranked_candidates = sorted(
        candidates,
        key=lambda candidate: candidate["allocation_score"],
        reverse=True,
    )
    eligible_candidates = [
        candidate
        for candidate in ranked_candidates
        if candidate["recommendation_status"] != "excluded"
    ]
    primary = eligible_candidates[0] if eligible_candidates else None
    secondary = eligible_candidates[1] if len(eligible_candidates) > 1 else None
    excluded = [
        candidate
        for candidate in ranked_candidates
        if candidate["recommendation_status"] == "excluded"
    ]

    return {
        "status": "ok",
        "asset_id": asset_id,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "allocation_status": classify_allocation_status(
            primary=primary,
            readiness=readiness,
        ),
        "primary_market": compact_market(primary),
        "secondary_market": compact_market(secondary),
        "summary": {
            "candidate_market_count": len(ranked_candidates),
            "eligible_market_count": len(eligible_candidates),
            "excluded_market_count": len(excluded),
            "total_allocated_power_mw": round(
                sum(
                    numeric(candidate.get("allocated_power_mw"))
                    for candidate in eligible_candidates
                ),
                4,
            ),
            "total_expected_revenue_eur": round(
                sum(
                    numeric(candidate.get("expected_revenue_eur"))
                    for candidate in eligible_candidates
                ),
                2,
            ),
            "readiness_status": readiness.get("readiness_status"),
            "readiness_score": readiness.get("readiness_score"),
            "forecast_confidence_band": forecast_confidence.get(
                "confidence_band"
            ),
            "forecast_confidence_score": forecast_confidence.get(
                "confidence_score"
            ),
            "approval_status": extract_approval_status(approval),
        },
        "allocation": ranked_candidates,
        "excluded_markets": excluded,
        "recommended_actions": build_recommended_actions(
            primary=primary,
            secondary=secondary,
            excluded=excluded,
            readiness=readiness,
            adapter_status=adapter_status,
            forecast_confidence=forecast_confidence,
        ),
        "evidence": {
            "revenue_allocation_status": revenue_allocation.get("status"),
            "revenue_allocation_count": revenue_allocation.get(
                "allocation_count",
                len(revenue_allocation.get("allocation", [])),
            ),
            "market_adapter_status": adapter_status.get(
                "market_adapter_status"
            ),
            "readiness_evidence": readiness.get("evidence", {}),
            "forecast_confidence_status": forecast_confidence.get("status"),
        },
    }


def load_or_run_revenue_allocation(asset_id, refresh_revenue_stack):
    if refresh_revenue_stack:
        return run_revenue_stack_allocation(asset_id=asset_id)

    allocation = load_latest_revenue_stack_allocation(asset_id)

    if allocation.get("status") == "ok":
        return allocation

    return run_revenue_stack_allocation(asset_id=asset_id)


def build_market_candidate(
    asset_id,
    market,
    adapter,
    commercial_allocation,
    excluded_commercial_product,
    readiness,
    forecast_confidence,
    approval,
):
    preview = load_preview(asset_id=asset_id, loader=market["preview_loader"])
    validation = (preview.get("preview") or {}).get("validation", {})
    preview_status = (preview.get("preview") or {}).get("status") or preview.get(
        "status"
    )
    blocking_reasons = []

    if not commercial_allocation:
        reason = (
            excluded_commercial_product or {}
        ).get("exclusion_reason") or "No commercial revenue allocation exists for this market product."
        blocking_reasons.append(reason)

    if not market_allowed_by_policy(asset_id=asset_id, adapter_id=market["adapter_id"]):
        blocking_reasons.append("Market is disabled by automation policy.")

    if preview.get("status") not in ["ok", "preview_error"]:
        blocking_reasons.append(preview.get("message") or "No market preview is available.")

    if validation.get("status") == "blocked" or preview_status == "not_ready":
        blocking_reasons.append("Market preview validation is blocked.")

    if adapter.get("connection_status") not in ["available", "preview_available"]:
        blocking_reasons.append("Market adapter is not available for preview or submission.")

    readiness_status = readiness.get("readiness_status")
    if readiness_status == "blocked":
        blocking_reasons.append("Execution readiness is blocked.")

    allocated_power_mw = numeric(
        (commercial_allocation or {}).get("allocated_power_mw")
    )
    allocated_energy_mwh = numeric(
        (commercial_allocation or {}).get("allocated_energy_mwh")
    )
    expected_revenue_eur = numeric(
        (commercial_allocation or {}).get("expected_revenue_eur")
    )
    score = score_market_candidate(
        expected_revenue_eur=expected_revenue_eur,
        allocated_power_mw=allocated_power_mw,
        readiness=readiness,
        forecast_confidence=forecast_confidence,
        validation=validation,
        adapter=adapter,
        approval=approval,
        blocking_reasons=blocking_reasons,
    )
    recommendation_status = classify_candidate_status(
        score=score,
        blocking_reasons=blocking_reasons,
        readiness_status=readiness_status,
    )

    return {
        "adapter_id": market["adapter_id"],
        "market_name": market["market_name"],
        "venue": market["venue"],
        "market_segment": market["market_segment"],
        "commercial_product_id": market["commercial_product_id"],
        "execution_role": market["execution_role"],
        "recommendation_status": recommendation_status,
        "allocation_score": score,
        "expected_revenue_eur": round(expected_revenue_eur, 2),
        "allocated_power_mw": round(allocated_power_mw, 4),
        "allocated_energy_mwh": round(allocated_energy_mwh, 4),
        "risk_score": build_risk_score(
            readiness=readiness,
            forecast_confidence=forecast_confidence,
            validation=validation,
            blocking_reasons=blocking_reasons,
        ),
        "preview_status": preview_status,
        "preview_validation_status": validation.get("status"),
        "adapter_connection_status": adapter.get("connection_status"),
        "adapter_credential_status": adapter.get("credential_status"),
        "live_submission": bool(adapter.get("live_submission")),
        "operator_next_action": operator_next_action(
            recommendation_status=recommendation_status,
            market_name=market["market_name"],
            blocking_reasons=blocking_reasons,
            adapter=adapter,
        ),
        "blocking_reasons": dedupe(blocking_reasons),
        "commercial_allocation_reason": (commercial_allocation or {}).get(
            "allocation_reason"
        ),
    }


def load_preview(asset_id, loader):
    try:
        return loader(asset_id)
    except (FileNotFoundError, ValueError) as error:
        return {
            "status": "not_found",
            "message": str(error),
            "preview": None,
        }
    except Exception as error:
        return {
            "status": "preview_error",
            "message": f"Could not build market preview: {error}",
            "preview": {
                "status": "not_ready",
                "validation": {
                    "status": "blocked",
                    "checks": [
                        {
                            "check": "preview_generation",
                            "status": "blocked",
                            "message": str(error),
                        }
                    ],
                },
            },
        }


def score_market_candidate(
    expected_revenue_eur,
    allocated_power_mw,
    readiness,
    forecast_confidence,
    validation,
    adapter,
    approval,
    blocking_reasons,
):
    if blocking_reasons:
        return 0.0

    revenue_component = min(expected_revenue_eur / 1000.0, 45.0)
    capacity_component = min(allocated_power_mw * 3.0, 20.0)
    readiness_component = numeric(readiness.get("readiness_score")) * 0.2
    confidence_component = numeric(
        forecast_confidence.get("confidence_score")
    ) * 0.15
    validation_component = 10.0 if validation.get("status") == "passed" else 4.0
    adapter_component = (
        8.0
        if adapter.get("connection_status") == "available"
        else 5.0
        if adapter.get("connection_status") == "preview_available"
        else 0.0
    )
    approval_component = 7.0 if extract_approval_status(approval) == "approved" else 3.0

    return round(
        min(
            100.0,
            revenue_component
            + capacity_component
            + readiness_component
            + confidence_component
            + validation_component
            + adapter_component
            + approval_component,
        ),
        1,
    )


def build_risk_score(readiness, forecast_confidence, validation, blocking_reasons):
    score = 100.0
    score -= (100.0 - numeric(readiness.get("readiness_score"))) * 0.35
    score -= (100.0 - numeric(forecast_confidence.get("confidence_score"))) * 0.3

    if validation.get("status") != "passed":
        score -= 20.0

    score -= min(len(blocking_reasons) * 20.0, 60.0)

    return round(max(0.0, min(100.0, score)), 1)


def classify_candidate_status(score, blocking_reasons, readiness_status):
    if blocking_reasons:
        return "excluded"

    if readiness_status == "operator_review_required":
        return "operator_review"

    if score >= 70:
        return "recommended"

    return "watchlist"


def classify_allocation_status(primary, readiness):
    if not primary:
        return "blocked"

    if primary.get("recommendation_status") == "recommended":
        return "recommended"

    if readiness.get("readiness_status") == "operator_review_required":
        return "operator_review_required"

    return "watchlist"


def compact_market(candidate):
    if not candidate:
        return None

    return {
        "adapter_id": candidate.get("adapter_id"),
        "market_name": candidate.get("market_name"),
        "market_segment": candidate.get("market_segment"),
        "recommendation_status": candidate.get("recommendation_status"),
        "allocation_score": candidate.get("allocation_score"),
        "allocated_power_mw": candidate.get("allocated_power_mw"),
        "allocated_energy_mwh": candidate.get("allocated_energy_mwh"),
        "expected_revenue_eur": candidate.get("expected_revenue_eur"),
        "operator_next_action": candidate.get("operator_next_action"),
    }


def build_recommended_actions(
    primary,
    secondary,
    excluded,
    readiness,
    adapter_status,
    forecast_confidence,
):
    actions = []

    if primary:
        actions.append(
            f"Use {primary['market_name']} as the primary execution path in supervised mode."
        )

    if secondary:
        actions.append(
            f"Keep {secondary['market_name']} as the secondary route for re-optimization or fallback."
        )

    if readiness.get("readiness_status") != "supervised_ready":
        actions.extend(readiness.get("recommended_actions", []))

    if forecast_confidence.get("automation_eligibility") != "supervised_live_candidate":
        actions.append(
            "Keep sizing conservative until forecast-vs-actual evidence supports live automation."
        )

    if not adapter_status.get("live_submission_enabled"):
        actions.append(
            adapter_status.get("next_connection_action")
            or "Connect live market credentials before enabling submission."
        )

    if excluded:
        actions.append(
            "Review excluded markets before promising multi-market optimization externally."
        )

    return dedupe(actions)


def operator_next_action(
    recommendation_status,
    market_name,
    blocking_reasons,
    adapter,
):
    if recommendation_status == "recommended":
        return f"Prepare supervised bid review for {market_name}."

    if recommendation_status == "operator_review":
        return f"Review readiness evidence before selecting {market_name}."

    if blocking_reasons:
        return blocking_reasons[0]

    return adapter.get("next_connection_action") or "Monitor market readiness."


def extract_approval_status(approval):
    payload = (approval or {}).get("approval") or approval or {}
    return payload.get("status")


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
