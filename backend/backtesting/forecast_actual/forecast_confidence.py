from backend.backtesting.forecast_actual.forecast_performance_repository import (
    list_forecast_performance_runs,
)


def build_forecast_confidence(asset_id, limit=10):
    runs = list_forecast_performance_runs(asset_id=asset_id, limit=limit)

    if not runs:
        return build_fallback_confidence(asset_id)

    scored_runs = [score_forecast_run(run) for run in runs]
    average_score = sum(run["score"] for run in scored_runs) / len(scored_runs)
    score = round(max(0.0, min(100.0, average_score)), 1)
    band = classify_confidence_band(score)

    return {
        "status": "ok",
        "asset_id": asset_id,
        "confidence_score": score,
        "confidence_band": band,
        "run_count": len(scored_runs),
        "automation_eligibility": automation_eligibility(band),
        "risk_policy": build_risk_policy(score=score, band=band),
        "reason": build_reason(scored_runs=scored_runs, band=band),
        "evidence": scored_runs,
    }


def build_fallback_confidence(asset_id):
    score = 45.0
    band = classify_confidence_band(score)

    return {
        "status": "insufficient_history",
        "asset_id": asset_id,
        "confidence_score": score,
        "confidence_band": band,
        "run_count": 0,
        "automation_eligibility": "paper_only",
        "risk_policy": build_risk_policy(score=score, band=band),
        "reason": (
            "No forecast-vs-actual runs are available yet; bids are sized "
            "conservatively and automation stays paper-only."
        ),
        "evidence": [],
    }


def score_forecast_run(run):
    mae = numeric(run.get("mae_eur_per_mwh"))
    rmse = numeric(run.get("rmse_eur_per_mwh"))
    revenue_delta = abs(numeric(run.get("revenue_delta_eur")))
    predicted_pnl = abs(numeric(run.get("predicted_pnl_eur")))

    mae_penalty = min(mae * 1.5, 35.0)
    rmse_penalty = min(rmse, 30.0)
    revenue_penalty = min(revenue_delta / max(predicted_pnl, 1.0) * 30.0, 30.0)
    score = 100.0 - mae_penalty - rmse_penalty - revenue_penalty

    return {
        "forecast_actual_id": run.get("forecast_actual_id"),
        "generated_at": run.get("generated_at"),
        "forecast_provider": run.get("forecast_provider"),
        "forecast_model": run.get("forecast_model"),
        "mae_eur_per_mwh": run.get("mae_eur_per_mwh"),
        "rmse_eur_per_mwh": run.get("rmse_eur_per_mwh"),
        "revenue_delta_eur": run.get("revenue_delta_eur"),
        "score": round(max(0.0, min(100.0, score)), 1),
    }


def classify_confidence_band(score):
    if score >= 80:
        return "high"

    if score >= 60:
        return "medium"

    return "low"


def automation_eligibility(band):
    if band == "high":
        return "supervised_live_candidate"

    if band == "medium":
        return "human_approval_required"

    return "paper_only"


def build_risk_policy(score, band):
    if band == "high":
        volume_multiplier = 1.0
        price_buffer_eur_per_mwh = 0.0
    elif band == "medium":
        volume_multiplier = 0.75
        price_buffer_eur_per_mwh = 2.0
    else:
        volume_multiplier = 0.5
        price_buffer_eur_per_mwh = 5.0

    return {
        "volume_multiplier": volume_multiplier,
        "price_buffer_eur_per_mwh": price_buffer_eur_per_mwh,
        "confidence_score": score,
        "confidence_band": band,
    }


def build_reason(scored_runs, band):
    latest = scored_runs[0] if scored_runs else {}

    if band == "high":
        return "Recent forecast-vs-actual evidence supports full bid sizing."

    if band == "medium":
        return (
            "Forecast evidence is usable, but bid volume and price are "
            "adjusted until more realized performance is available."
        )

    if latest:
        return (
            "Forecast confidence is low based on recent error and revenue "
            "variance; bids are reduced and automation remains blocked."
        )

    return "Forecast confidence is low because no performance evidence exists."


def numeric(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0



