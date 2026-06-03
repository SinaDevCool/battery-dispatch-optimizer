from datetime import datetime

from src.assets.asset_loader import get_asset
from src.db.repositories.business_decision_repository import (
    get_latest_business_decision,
    list_business_decisions,
    save_business_decision,
)
from src.db.repositories.revenue_repository import get_revenue_stack_run
from src.db.repositories.signal_repository import get_signal_run, list_signal_runs
from src.hedging.revenue_contracts import build_hedged_revenue_view
from src.markets.products.product_registry import build_asset_product_eligibility_list
from src.regulatory.eeg_compliance_checker import check_eeg_compliance


def build_business_decision(asset_id):
    asset = get_asset(asset_id)
    signal_runs = list_signal_runs(asset_id=asset_id, limit=1)
    latest_signal_run = signal_runs[0] if signal_runs else None
    signal_payload = None

    if latest_signal_run:
        signal_payload = get_signal_run(latest_signal_run["signal_id"])["payload"]

    revenue_stack = load_latest_revenue_stack_payload(asset_id)
    summary = (signal_payload or {}).get("summary", {})
    metadata = (signal_payload or {}).get("metadata", {})

    expected_pnl = numeric(summary.get("total_pnl_eur"))
    profit_per_mw_day = numeric(summary.get("profit_per_mw_day"))
    merchant_revenue = infer_merchant_revenue(expected_pnl, revenue_stack)
    hedge_view = build_hedged_revenue_view(
        asset=asset,
        merchant_revenue_eur=merchant_revenue,
    )
    hedge_summary = hedge_view.get("summary", {})
    eeg = normalize_eeg_compliance(check_eeg_compliance(asset))
    eligibility = build_asset_product_eligibility_list(asset)

    decision = make_decision(
        asset_id=asset_id,
        eeg=eeg,
        eligibility=eligibility,
        expected_pnl=expected_pnl,
        hedge_summary=hedge_summary,
        metadata=metadata,
        profit_per_mw_day=profit_per_mw_day,
        revenue_stack=revenue_stack,
        signal_payload=signal_payload,
    )

    decision_id = save_business_decision(asset_id, decision)
    decision["decision_id"] = decision_id

    return decision


def get_or_build_latest_business_decision(asset_id):
    latest = get_latest_business_decision(asset_id)

    if latest is not None:
        return latest["payload"]

    return build_business_decision(asset_id)


def list_business_decision_history(asset_id, limit=25):
    return list_business_decisions(asset_id=asset_id, limit=limit)


def load_latest_revenue_stack_payload(asset_id):
    from src.db.repositories.revenue_repository import list_revenue_stack_runs

    runs = list_revenue_stack_runs(asset_id=asset_id, limit=1)

    if not runs:
        return None

    return get_revenue_stack_run(runs[0]["revenue_stack_id"])["payload"]


def infer_merchant_revenue(expected_pnl, revenue_stack):
    if revenue_stack:
        return numeric(revenue_stack.get("total_estimated_revenue_eur"))

    return expected_pnl


def make_decision(
    asset_id,
    eeg,
    eligibility,
    expected_pnl,
    hedge_summary,
    metadata,
    profit_per_mw_day,
    revenue_stack,
    signal_payload,
):
    eligible_products = [
        item for item in eligibility
        if item.get("eligible")
    ]
    blockers = []
    actions = []
    forecast_provider = metadata.get("forecast_provider") or metadata.get("source")
    forecast_model = metadata.get("forecast_model")

    if signal_payload is None:
        blockers.append("No persisted signal run exists for this asset.")

    if revenue_stack is None:
        blockers.append("No persisted revenue stack run exists for this asset.")

    if forecast_provider == "local_saved_forecast":
        blockers.append("Latest persisted signal used a local saved forecast fallback.")

    if not eeg.get("eeg_eligible"):
        blockers.append("EEG eligibility or energy-origin treatment needs review.")

    if not eligible_products:
        blockers.append("No eligible market products are confirmed for this asset.")

    blockers.append("Market API, live telemetry, approval capture, and order limits are not connected.")

    if expected_pnl > 0:
        actions.append("Dispatch day-ahead arbitrage as the primary advisory strategy.")
    else:
        actions.append("Keep asset available and refresh forecast inputs before dispatch.")

    if numeric(hedge_summary.get("hedged_revenue_eur")) > 0:
        actions.append("Show hedge floor separately from merchant upside.")
    else:
        actions.append("Add a hedge floor scenario before presenting revenue certainty.")

    if revenue_stack:
        actions.append("Use persisted revenue stack output for commercial comparison.")
    else:
        actions.append("Run revenue stack to quantify non-day-ahead product options.")

    if expected_pnl > 0 and eeg.get("eeg_eligible"):
        title = "Run day-ahead arbitrage, keep hedge floor visible, defer automated execution"
        status = "advisory_ready"
        readiness = "Commercial advisory ready"
    elif expected_pnl > 0:
        title = "Use dispatch as commercial upside, clear regulatory blockers before execution"
        status = "commercial_review"
        readiness = "Needs commercial review"
    else:
        title = "Do not dispatch; refresh forecast and preserve optionality"
        status = "no_trade"
        readiness = "No trade"

    return {
        "status": "ok",
        "asset_id": asset_id,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "recommendation_title": title,
        "recommendation_status": status,
        "readiness": readiness,
        "description": build_description(expected_pnl, revenue_stack, eeg),
        "expected_pnl_eur": round(expected_pnl, 2),
        "profit_per_mw_day": round(profit_per_mw_day, 2),
        "hedged_revenue_eur": round(numeric(hedge_summary.get("hedged_revenue_eur")), 2),
        "merchant_upside_eur": round(numeric(hedge_summary.get("merchant_upside_eur")), 2),
        "residual_exposure_eur": round(numeric(hedge_summary.get("residual_exposure_eur")), 2),
        "forecast_provider": forecast_provider,
        "forecast_model": forecast_model,
        "eligible_product_count": len(eligible_products),
        "revenue_stack_available": revenue_stack is not None,
        "signal_available": signal_payload is not None,
        "eeg_eligible": bool(eeg.get("eeg_eligible")),
        "recommended_actions": actions,
        "blockers": blockers,
        "decision_basis": {
            "forecast_provider": forecast_provider,
            "forecast_model": forecast_model,
            "target_date": metadata.get("target_date"),
            "signal": (signal_payload or {}).get("summary", {}).get("signal"),
            "opportunity_level": (signal_payload or {}).get("summary", {}).get("opportunity_level"),
            "eligible_products": [
                item.get("product", {}).get("product_id")
                for item in eligible_products
            ],
        },
    }


def build_description(expected_pnl, revenue_stack, eeg):
    if expected_pnl > 0 and eeg.get("eeg_eligible"):
        return (
            "The latest persisted signal supports merchant day-ahead dispatch. "
            "Use hedge assumptions for revenue certainty and keep reserve/auto-trading advisory until live execution controls are connected."
        )

    if expected_pnl > 0:
        return (
            "The latest persisted signal has positive economics, but regulatory or commercial assumptions need review before execution."
        )

    if revenue_stack:
        return (
            "The latest persisted revenue stack exists, but the current signal does not justify active dispatch."
        )

    return "The database does not yet contain enough persisted runs to recommend dispatch."


def numeric(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def normalize_eeg_compliance(eeg):
    eeg_support_risk = eeg.get("eeg_support_risk")
    status = eeg.get("status")
    storage_classification = eeg.get("storage_classification", {})
    eeg_eligible = status == "ready" and eeg_support_risk != "high"

    return {
        **eeg,
        "eeg_eligible": eeg_eligible,
        "green_colocation": (
            storage_classification.get("storage_mode") == "pure_green_colocated"
        ),
        "mixed_origin_risk": eeg_support_risk,
    }
