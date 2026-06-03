from datetime import datetime

from src.assets.asset_loader import get_asset
from src.db.repositories.execution_repository import (
    get_latest_execution_proposal,
    list_execution_proposals,
    save_execution_proposal,
)
from src.db.repositories.signal_repository import list_signal_runs
from src.db.repositories.workflow_repository import get_latest_workflow_run
from src.services.asset_signal_store import load_asset_latest_signal


def build_execution_proposal(asset_id):
    asset = get_asset(asset_id)
    latest_signal = load_asset_latest_signal(asset_id)

    if latest_signal.get("status") != "ok":
        raise FileNotFoundError(
            f"No latest signal found for asset: {asset_id}. Run an audited workflow or asset signal first."
        )

    signal_data = latest_signal.get("data", {})
    dispatch_rows = signal_data.get("dispatch", [])
    summary = signal_data.get("summary", {})
    metadata = signal_data.get("metadata", {})
    signal_run = get_latest_signal_run(asset_id)
    workflow_run = get_latest_workflow_run(asset_id)
    orders = build_orders(
        dispatch_rows=dispatch_rows,
        market=asset.market or "DE-LU day-ahead",
    )
    risk_checks = build_risk_checks(
        asset=asset,
        orders=orders,
        summary=summary,
        dispatch_rows=dispatch_rows,
    )
    automation_blockers = build_execution_blockers()
    hard_blockers = [
        check["message"]
        for check in risk_checks
        if check["status"] in ["blocked", "breach"]
        and check["check"] not in ["market_api_connection", "human_approval"]
    ]

    status = "blocked" if hard_blockers else "draft"
    approval_status = "blocked" if hard_blockers else "requires_approval"
    total_buy_mwh = sum(
        order["volume_mwh"] for order in orders
        if order["side"] == "buy"
    )
    total_sell_mwh = sum(
        order["volume_mwh"] for order in orders
        if order["side"] == "sell"
    )
    expected_pnl = numeric(summary.get("total_pnl_eur"))
    max_daily_loss = resolve_max_daily_loss(asset)

    proposal = {
        "status": status,
        "asset_id": asset_id,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "approval_status": approval_status,
        "execution_mode": "advisory",
        "market_submission_enabled": False,
        "signal_id": (signal_run or {}).get("signal_id"),
        "workflow_run_id": (workflow_run or {}).get("workflow_run_id"),
        "target_date": metadata.get("target_date"),
        "forecast_provider": metadata.get("forecast_provider") or metadata.get("source"),
        "forecast_model": metadata.get("forecast_model"),
        "market": asset.market or "DE-LU day-ahead",
        "orders": orders,
        "risk_checks": risk_checks,
        "automation_blockers": automation_blockers,
        "blockers": hard_blockers,
        "summary": {
            "order_count": len(orders),
            "total_buy_mwh": round(total_buy_mwh, 4),
            "total_sell_mwh": round(total_sell_mwh, 4),
            "expected_pnl_eur": round(expected_pnl, 2),
            "profit_per_mw_day": numeric(summary.get("profit_per_mw_day")),
            "max_daily_loss_eur": max_daily_loss,
        },
        "audit": build_audit_events(
            has_signal=True,
            order_count=len(orders),
            status=status,
            blockers=hard_blockers,
        ),
    }

    proposal_id = save_execution_proposal(proposal)
    proposal["execution_proposal_id"] = proposal_id

    return proposal


def latest_execution_proposal(asset_id):
    latest = get_latest_execution_proposal(asset_id)

    if latest is None:
        return {
            "status": "not_found",
            "message": f"No execution proposal found for asset: {asset_id}",
            "asset_id": asset_id,
            "proposal": None,
        }

    return {
        "status": "ok",
        "asset_id": asset_id,
        "proposal": latest["payload"],
    }


def execution_proposal_history(asset_id, limit=25):
    return {
        "status": "ok",
        "asset_id": asset_id,
        "proposals": list_execution_proposals(asset_id=asset_id, limit=limit),
    }


def build_orders(dispatch_rows, market):
    orders = []

    for index, row in enumerate(dispatch_rows):
        action = row.get("action")

        if action not in ["charge", "discharge"]:
            continue

        side = "buy" if action == "charge" else "sell"
        volume_mwh = abs(
            numeric(row.get("grid_energy_mwh"))
            or numeric(row.get("battery_energy_mwh"))
        )

        if volume_mwh <= 0:
            continue

        orders.append(
            {
                "order_id": f"draft-{index + 1:03d}",
                "delivery_time": row.get("timestamp"),
                "market": market,
                "side": side,
                "volume_mwh": round(volume_mwh, 4),
                "price_limit_eur_mwh": round(numeric(row.get("price")), 2),
                "source_action": action,
                "source_dispatch_index": index,
                "status": "draft",
            }
        )

    return orders


def build_risk_checks(asset, orders, summary, dispatch_rows):
    commercial_config = asset.commercial_config or {}
    grid_connection = asset.grid_connection or {}
    battery_config = asset.battery_config or {}
    expected_pnl = numeric(summary.get("total_pnl_eur"))
    max_daily_loss = resolve_max_daily_loss(asset)
    max_import_mw = numeric(grid_connection.get("max_import_mw"))
    max_export_mw = numeric(grid_connection.get("max_export_mw"))
    min_soc_mwh = numeric(battery_config.get("min_soc_mwh"))
    max_buy_mwh = max(
        [order["volume_mwh"] for order in orders if order["side"] == "buy"]
        or [0.0]
    )
    max_sell_mwh = max(
        [order["volume_mwh"] for order in orders if order["side"] == "sell"]
        or [0.0]
    )
    min_observed_soc = min(
        [numeric(row.get("soc_mwh")) for row in dispatch_rows]
        or [0.0]
    )

    checks = [
        {
            "check": "signal_has_active_orders",
            "status": "passed" if orders else "blocked",
            "message": (
                "Active charge/discharge intervals converted to draft orders."
                if orders
                else "No active dispatch intervals were available for order proposal."
            ),
        },
        {
            "check": "max_daily_loss",
            "status": "passed" if expected_pnl >= -max_daily_loss else "breach",
            "message": (
                "Expected PnL is within the configured daily loss guardrail."
                if expected_pnl >= -max_daily_loss
                else "Expected PnL breaches the configured daily loss guardrail."
            ),
            "context": {
                "expected_pnl_eur": expected_pnl,
                "max_daily_loss_eur": max_daily_loss,
            },
        },
        {
            "check": "grid_import_limit",
            "status": classify_limit_check(max_import_mw, max_buy_mwh),
            "message": "Largest buy order is checked against grid import capability.",
            "context": {
                "largest_buy_mwh": max_buy_mwh,
                "max_import_mw": max_import_mw,
            },
        },
        {
            "check": "grid_export_limit",
            "status": classify_limit_check(max_export_mw, max_sell_mwh),
            "message": "Largest sell order is checked against grid export capability.",
            "context": {
                "largest_sell_mwh": max_sell_mwh,
                "max_export_mw": max_export_mw,
            },
        },
        {
            "check": "minimum_soc_reserve",
            "status": "passed" if min_observed_soc >= min_soc_mwh else "breach",
            "message": (
                "Dispatch keeps SOC at or above the configured minimum reserve."
                if min_observed_soc >= min_soc_mwh
                else "Dispatch falls below the configured minimum SOC reserve."
            ),
            "context": {
                "min_observed_soc_mwh": min_observed_soc,
                "min_soc_mwh": min_soc_mwh,
            },
        },
        {
            "check": "market_api_connection",
            "status": "blocked",
            "message": "No live market API adapter is connected yet.",
        },
        {
            "check": "human_approval",
            "status": "required",
            "message": "Human approval is required before any market submission.",
        },
    ]

    if commercial_config.get("auto_trading_enabled"):
        checks.append(
            {
                "check": "auto_trading",
                "status": "blocked",
                "message": "Auto-trading flag is set, but order submission controls are not implemented.",
            }
        )

    return checks


def build_execution_blockers():
    return [
        "Market API adapter is not connected.",
        "Live asset telemetry is not connected.",
        "Human approval capture is not implemented.",
        "Automated order limits and cancellation controls are not implemented.",
    ]


def build_audit_events(has_signal, order_count, status, blockers):
    return [
        {
            "event": "Signal loaded",
            "actor": "optimizer",
            "status": "complete" if has_signal else "pending",
            "note": "Latest asset signal was used as the source for this proposal.",
        },
        {
            "event": "Draft orders generated",
            "actor": "execution_engine",
            "status": "complete" if order_count else "pending",
            "note": f"{order_count} draft order(s) generated from dispatch intervals.",
        },
        {
            "event": "Pre-trade checks",
            "actor": "risk_engine",
            "status": status,
            "note": (
                "Execution proposal has blockers."
                if blockers
                else "Execution proposal is ready for human approval."
            ),
        },
        {
            "event": "Market submission",
            "actor": "market_adapter",
            "status": "disabled",
            "note": "No exchange, trader, or balancing-market API adapter is connected.",
        },
    ]


def get_latest_signal_run(asset_id):
    runs = list_signal_runs(asset_id=asset_id, limit=1)

    if not runs:
        return None

    return runs[0]


def classify_limit_check(configured_limit, largest_order):
    if configured_limit <= 0:
        return "review"

    if largest_order <= configured_limit:
        return "passed"

    return "breach"


def resolve_max_daily_loss(asset):
    commercial_config = asset.commercial_config or {}

    return numeric(commercial_config.get("max_daily_loss_eur")) or 2500.0


def numeric(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0
