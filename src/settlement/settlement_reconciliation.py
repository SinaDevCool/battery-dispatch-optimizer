from datetime import datetime

from src.backtesting.forecast_actual.forecast_actual_runner import (
    load_latest_forecast_actual_result,
)
from src.db.repositories.execution_repository import (
    get_latest_execution_paper_trade,
    get_latest_execution_proposal,
)
from src.db.repositories.settlement_repository import (
    get_latest_settlement_reconciliation,
    list_settlement_reconciliations,
    save_settlement_reconciliation_run,
)


def run_settlement_reconciliation(asset_id):
    proposal_record = get_latest_execution_proposal(asset_id)
    paper_record = get_latest_execution_paper_trade(asset_id)
    forecast_actual = load_latest_forecast_actual_result(asset_id)

    if proposal_record is None:
        raise FileNotFoundError(
            f"No execution proposal found for asset_id={asset_id}."
        )

    proposal = proposal_record["payload"]
    paper_trade = (paper_record or {}).get("payload")
    realized_dispatch = forecast_actual.get("realized_dispatch", {})

    expected_pnl = numeric(proposal.get("summary", {}).get("expected_pnl_eur"))
    paper_pnl = resolve_paper_pnl(paper_trade)
    realized_pnl = resolve_realized_pnl(realized_dispatch)
    paper_delta = None if paper_pnl is None else round(paper_pnl - expected_pnl, 2)
    realized_delta = (
        None if realized_pnl is None else round(realized_pnl - expected_pnl, 2)
    )

    variance_drivers = build_variance_drivers(
        forecast_actual=forecast_actual,
        paper_delta=paper_delta,
        paper_trade=paper_trade,
        realized_delta=realized_delta,
        realized_dispatch=realized_dispatch,
    )
    primary_driver = variance_drivers[0]["driver"] if variance_drivers else "none"
    status = classify_status(
        paper_trade=paper_trade,
        realized_dispatch=realized_dispatch,
    )

    result = {
        "status": status,
        "asset_id": asset_id,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "primary_variance_driver": primary_driver,
        "links": {
            "execution_proposal_id": proposal_record["execution_proposal_id"],
            "paper_trade_id": (paper_record or {}).get("paper_trade_id"),
            "forecast_actual_id": forecast_actual.get("forecast_actual_id"),
        },
        "summary": {
            "expected_pnl_eur": round(expected_pnl, 2),
            "paper_pnl_eur": paper_pnl,
            "realized_pnl_eur": realized_pnl,
            "paper_delta_eur": paper_delta,
            "realized_delta_eur": realized_delta,
        },
        "variance_drivers": variance_drivers,
        "evidence_status": {
            "execution_proposal": "available",
            "paper_trade": "available" if paper_trade else "missing",
            "forecast_actual": forecast_actual.get("status", "not_found"),
            "realized_dispatch": realized_dispatch.get("status", "not_found"),
        },
        "recommended_actions": build_recommended_actions(
            status=status,
            variance_drivers=variance_drivers,
        ),
    }

    reconciliation_id = save_settlement_reconciliation_run(result)
    result["settlement_reconciliation_id"] = reconciliation_id

    return result


def latest_settlement_reconciliation(asset_id):
    latest = get_latest_settlement_reconciliation(asset_id)

    if latest is None:
        return {
            "status": "not_found",
            "message": (
                "No settlement reconciliation found. Run reconciliation after "
                "a proposal, paper trade, and optional forecast-vs-actual run."
            ),
            "asset_id": asset_id,
            "settlement": None,
        }

    return {
        "status": "ok",
        "asset_id": asset_id,
        "settlement": latest["payload"],
    }


def settlement_reconciliation_history(asset_id, limit=25):
    return {
        "status": "ok",
        "asset_id": asset_id,
        "settlements": list_settlement_reconciliations(
            asset_id=asset_id,
            limit=limit,
        ),
    }


def resolve_paper_pnl(paper_trade):
    if not paper_trade:
        return None

    return round(numeric(paper_trade.get("summary", {}).get("paper_pnl_eur")), 2)


def resolve_realized_pnl(realized_dispatch):
    if realized_dispatch.get("status") != "ok":
        return None

    return round(numeric(realized_dispatch.get("realized_pnl_eur")), 2)


def build_variance_drivers(
    forecast_actual,
    paper_delta,
    paper_trade,
    realized_delta,
    realized_dispatch,
):
    drivers = []

    if paper_trade is None:
        drivers.append(
            {
                "driver": "paper_trade_missing",
                "severity": "medium",
                "message": "No paper trade is available for execution PnL comparison.",
            }
        )
    elif abs(numeric(paper_delta)) > 1:
        drivers.append(
            {
                "driver": "paper_execution_delta",
                "severity": classify_delta_severity(paper_delta),
                "message": (
                    "Paper execution PnL differs from the proposal expectation."
                ),
                "delta_eur": paper_delta,
            }
        )

    if forecast_actual.get("status") != "ok":
        drivers.append(
            {
                "driver": "actual_price_missing",
                "severity": "medium",
                "message": "Forecast-vs-actual evidence is not available yet.",
            }
        )
    elif realized_dispatch.get("status") != "ok":
        drivers.append(
            {
                "driver": "realized_dispatch_unavailable",
                "severity": "medium",
                "message": realized_dispatch.get(
                    "message",
                    "Realized dispatch replay could not be calculated.",
                ),
            }
        )
    elif abs(numeric(realized_delta)) > 1:
        drivers.append(
            {
                "driver": "forecast_realization_delta",
                "severity": classify_delta_severity(realized_delta),
                "message": (
                    "Actual-price replay differs from the proposal expectation."
                ),
                "delta_eur": realized_delta,
            }
        )

    if not drivers:
        drivers.append(
            {
                "driver": "within_tolerance",
                "severity": "low",
                "message": "Paper and realized PnL are within the current tolerance.",
            }
        )

    return drivers


def classify_status(paper_trade, realized_dispatch):
    if paper_trade is None:
        return "needs_paper_trade"

    if realized_dispatch.get("status") == "ok":
        return "settled"

    return "paper_reconciled"


def classify_delta_severity(delta):
    absolute_delta = abs(numeric(delta))

    if absolute_delta >= 1000:
        return "high"

    if absolute_delta >= 100:
        return "medium"

    return "low"


def build_recommended_actions(status, variance_drivers):
    actions = []
    driver_ids = {driver["driver"] for driver in variance_drivers}

    if status == "needs_paper_trade":
        actions.append("Run paper trading before presenting execution quality.")

    if "actual_price_missing" in driver_ids:
        actions.append("Run forecast-vs-actual backtesting when actual prices are available.")

    if "forecast_realization_delta" in driver_ids:
        actions.append("Review forecast error and update confidence before live automation.")

    if "paper_execution_delta" in driver_ids:
        actions.append("Review bid price assumptions and simulated fill logic.")

    if not actions:
        actions.append("Keep reconciliation evidence attached to the trading audit packet.")

    return actions


def numeric(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0
