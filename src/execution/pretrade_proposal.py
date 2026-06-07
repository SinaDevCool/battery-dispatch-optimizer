from datetime import datetime

from src.assets.asset_loader import get_asset
from src.db.repositories.execution_repository import (
    get_latest_execution_proposal,
    list_execution_proposals,
    save_execution_proposal,
)
from src.db.repositories.signal_repository import list_signal_runs
from src.db.repositories.workflow_repository import get_latest_workflow_run
from src.backtesting.forecast_actual.forecast_confidence import (
    build_forecast_confidence,
)
from src.execution.bid_package_builder import build_market_bid_package
from src.services.asset_signal_store import load_asset_latest_signal


def build_execution_proposal(asset_id):
    from src.execution.multi_market_allocator import build_multi_market_allocation

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
    forecast_confidence = build_forecast_confidence(asset_id)
    market_allocation = build_multi_market_allocation(asset_id)
    selected_route = market_allocation.get("primary_market") or {}
    market_lifecycle = selected_route.get("market_lifecycle") or {}
    bid_package = build_market_bid_package(
        asset=asset,
        dispatch_rows=dispatch_rows,
        market=selected_route.get("market_name") or asset.market or "DE-LU day-ahead",
        forecast_confidence=forecast_confidence,
        market_lifecycle=market_lifecycle,
        selected_route=selected_route,
    )
    orders = bid_package["orders"]
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
        numeric(order.get("volume_mwh")) for order in orders
        if order.get("side") == "buy"
    )
    total_sell_mwh = sum(
        numeric(order.get("volume_mwh")) for order in orders
        if order.get("side") == "sell"
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
        "forecast_confidence": forecast_confidence,
        "market": selected_route.get("market_name") or asset.market or "DE-LU day-ahead",
        "market_allocation_status": market_allocation.get("allocation_status"),
        "market_lifecycle": market_lifecycle,
        "selected_market_route": selected_route,
        "bid_package": bid_package,
        "bid_package_status": bid_package.get("package_status"),
        "orders": orders,
        "bids": orders,
        "bid_lifecycle": build_bid_lifecycle(
            status=status,
            approval_status=approval_status,
            market_submission_enabled=False,
            paper_trade_status="not_run",
        ),
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
            "market_gate_closure": market_lifecycle.get("gate_closure_label"),
            "order_style": market_lifecycle.get("order_style"),
            "package_status": bid_package.get("package_status"),
            "package_validation_status": bid_package.get("validation", {}).get("status"),
            "reserve_order_count": bid_package.get("summary", {}).get("reserve_order_count"),
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


def build_orders(
    dispatch_rows,
    market,
    forecast_confidence=None,
    market_lifecycle=None,
    selected_route=None,
):
    orders = []
    confidence = forecast_confidence or {}
    lifecycle = market_lifecycle or {}
    route = selected_route or {}
    risk_policy = confidence.get("risk_policy", {})
    volume_multiplier = numeric(risk_policy.get("volume_multiplier")) or 1.0
    price_buffer = numeric(risk_policy.get("price_buffer_eur_per_mwh"))
    confidence_score = numeric(confidence.get("confidence_score"))
    confidence_band = confidence.get("confidence_band", "unknown")
    automation_eligibility = confidence.get("automation_eligibility", "paper_only")
    confidence_reason = confidence.get("reason", "Forecast confidence was not scored.")

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

        bid_id = f"bid-{index + 1:03d}"
        order_id = f"draft-{index + 1:03d}"
        limit_price = round(numeric(row.get("price")), 2)
        risk_adjusted_volume_mwh = round(volume_mwh * volume_multiplier, 4)
        risk_adjusted_volume_mw = round((volume_mwh / 0.25) * volume_multiplier, 4)
        risk_adjusted_limit_price = risk_adjusted_price(
            side=side,
            limit_price=limit_price,
            price_buffer=price_buffer,
        )

        orders.append(
            {
                "bid_id": bid_id,
                "order_id": order_id,
                "delivery_time": row.get("timestamp"),
                "delivery_start": row.get("timestamp"),
                "delivery_end": row.get("timestamp"),
                "market": market,
                "adapter_id": route.get("adapter_id"),
                "automation_lane": lifecycle.get("automation_lane"),
                "bid_granularity": lifecycle.get("bid_granularity"),
                "market_product_id": infer_market_product_id(market),
                "bid_type": "limit",
                "gate_closure_label": lifecycle.get("gate_closure_label"),
                "market_lifecycle_status": lifecycle.get("lifecycle_status"),
                "market_segment": route.get("market_segment"),
                "side": side,
                "volume_mw": round(volume_mwh / 0.25, 4),
                "volume_mwh": round(volume_mwh, 4),
                "energy_mwh": round(volume_mwh, 4),
                "limit_price_eur_mwh": limit_price,
                "price_limit_eur_mwh": limit_price,
                "forecast_confidence_score": round(confidence_score, 1),
                "forecast_confidence_band": confidence_band,
                "risk_adjusted_volume_mw": risk_adjusted_volume_mw,
                "risk_adjusted_volume_mwh": risk_adjusted_volume_mwh,
                "risk_adjusted_limit_price_eur_mwh": risk_adjusted_limit_price,
                "next_gate_closure_at": lifecycle.get("next_gate_closure_at"),
                "order_style": lifecycle.get("order_style"),
                "automation_eligibility": automation_eligibility,
                "confidence_reason": confidence_reason,
                "source_action": action,
                "source_dispatch_index": index,
                "status": "draft",
                "bid_status": "draft",
                "lifecycle_status": "draft",
                "approval_status": "requires_approval",
                "submission_status": "not_submitted",
                "risk_status": confidence_risk_status(confidence_band),
            }
        )

    return orders


def build_bid_lifecycle(
    status,
    approval_status,
    market_submission_enabled,
    paper_trade_status,
):
    risk_status = "blocked" if status == "blocked" else "risk_checked"
    approval_step = (
        "blocked"
        if approval_status == "blocked"
        else "approval_required"
    )
    live_submission_status = (
        "enabled"
        if market_submission_enabled
        else "disabled"
    )

    return [
        {
            "step": "draft_bids",
            "label": "Draft bids",
            "status": "complete",
            "owner": "execution_engine",
        },
        {
            "step": "risk_check",
            "label": "Risk check",
            "status": risk_status,
            "owner": "risk_engine",
        },
        {
            "step": "approval",
            "label": "Human approval",
            "status": approval_step,
            "owner": "operator",
        },
        {
            "step": "paper_submission",
            "label": "Paper submission",
            "status": paper_trade_status,
            "owner": "paper_adapter",
        },
        {
            "step": "live_submission",
            "label": "Live submission",
            "status": live_submission_status,
            "owner": "market_adapter",
        },
    ]


def infer_market_product_id(market):
    market_name = str(market or "").lower()

    if "intraday" in market_name:
        return "intraday_arbitrage"

    return "day_ahead_arbitrage"


def risk_adjusted_price(side, limit_price, price_buffer):
    if side == "buy":
        return round(limit_price - price_buffer, 2)

    return round(limit_price + price_buffer, 2)


def confidence_risk_status(confidence_band):
    if confidence_band == "high":
        return "passed"

    if confidence_band == "medium":
        return "review"

    return "restricted"


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
        [
            numeric(order.get("volume_mwh"))
            for order in orders
            if order.get("side") == "buy"
        ]
        or [0.0]
    )
    max_sell_mwh = max(
        [
            numeric(order.get("volume_mwh"))
            for order in orders
            if order.get("side") == "sell"
        ]
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
