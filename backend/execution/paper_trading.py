from datetime import datetime

from backend.db.repositories.execution_repository import (
    get_latest_execution_paper_trade,
    get_latest_execution_proposal,
    list_execution_paper_trades,
    save_execution_paper_trade,
)
from backend.execution.market_paper_simulator import simulate_market_paper_execution
from backend.execution.market_adapters.paper import PaperMarketAdapter
from backend.execution.pretrade_proposal import numeric


def build_paper_fills(orders):
    submitted_at = datetime.now().isoformat(timespec="seconds")

    return PaperMarketAdapter().submit_bids(
        bids=orders,
        submitted_at=submitted_at,
    )["fills"]


def summarize_paper_fills(fills, expected_pnl_eur):
    buy_cost = sum(
        numeric(fill.get("notional_eur"))
        for fill in fills
        if fill.get("side") == "buy"
    )

    sell_revenue = sum(
        numeric(fill.get("notional_eur"))
        for fill in fills
        if fill.get("side") == "sell"
    )

    paper_pnl = sell_revenue - buy_cost

    return {
        "order_count": len(fills),
        "filled_order_count": len(fills),
        "buy_cost_eur": round(buy_cost, 2),
        "sell_revenue_eur": round(sell_revenue, 2),
        "paper_pnl_eur": round(paper_pnl, 2),
        "expected_pnl_eur": round(expected_pnl_eur, 2),
        "paper_vs_expected_delta_eur": round(paper_pnl - expected_pnl_eur, 2),
    }


def run_execution_paper_trade(asset_id):
    latest_record = get_latest_execution_proposal(asset_id)

    if latest_record is None:
        raise FileNotFoundError(
            f"No execution proposal found for asset_id={asset_id}."
        )

    proposal = latest_record["payload"]
    orders = proposal.get("bids") or proposal.get("orders", [])

    if not orders:
        raise ValueError(
            "Latest execution proposal has no draft bids to paper trade."
        )

    generated_at = datetime.now().isoformat(timespec="seconds")
    expected_pnl = numeric(proposal.get("summary", {}).get("expected_pnl_eur"))

    simulation = simulate_market_paper_execution(
        proposal=proposal,
        generated_at=generated_at,
    )
    fills = simulation["fills"]
    summary = {
        **simulation["summary"],
        "expected_pnl_eur": round(expected_pnl, 2),
        "paper_vs_expected_delta_eur": round(
            numeric(simulation["summary"].get("paper_pnl_eur")) - expected_pnl,
            2,
        ),
    }
    bid_results = build_paper_bid_results(orders, fills)

    paper_trade = {
        "asset_id": asset_id,
        "execution_proposal_id": latest_record["execution_proposal_id"],
        "generated_at": generated_at,
        "mode": "paper_trading",
        "adapter_id": simulation["adapter_id"],
        "awards": simulation["awards"],
        "proposal_generated_at": proposal.get("generated_at"),
        "status": simulation["status"],
        "lifecycle_status": "paper_filled",
        "bid_lifecycle": build_paper_lifecycle(proposal),
        "market_execution_model": simulation["market_execution_model"],
        "settlement_basis": simulation["settlement_basis"],
        "summary": summary,
        "bids": bid_results,
        "fills": fills,
        "validation": simulation["validation"],
        "audit": simulation["audit"] + [
            {
                "event": "paper_trade_started",
                "actor": "backend",
                "status": "complete",
                "note": "Loaded latest backend execution proposal.",
            },
            {
                "event": "bids_submitted_to_paper_adapter",
                "actor": "market_paper_simulator",
                "status": simulation["status"],
                "note": "Submitted draft bids to the market-specific paper simulator.",
            },
            {
                "event": "pnl_calculated",
                "actor": "paper_trading_engine",
                "status": "complete",
                "note": "Calculated paper PnL and delta versus proposal PnL using market-specific execution evidence.",
            },
        ],
        "assumptions": simulation["assumptions"],
    }

    paper_trade_id = save_execution_paper_trade(paper_trade)
    paper_trade["paper_trade_id"] = paper_trade_id

    return paper_trade


def latest_execution_paper_trade(asset_id):
    latest_record = get_latest_execution_paper_trade(asset_id)

    if latest_record is None:
        return {
            "status": "not_found",
            "message": "No execution paper trade found. Run paper trading first.",
            "asset_id": asset_id,
            "paper_trade": None,
        }

    paper_trade = latest_record["payload"]
    paper_trade["paper_trade_id"] = latest_record["paper_trade_id"]

    return {
        "status": "ok",
        "asset_id": asset_id,
        "paper_trade": paper_trade,
    }


def execution_paper_trade_history(asset_id, limit=25):
    rows = list_execution_paper_trades(asset_id=asset_id, limit=limit)

    return {
        "status": "ok",
        "asset_id": asset_id,
        "paper_trades": rows,
    }


def build_paper_bid_results(orders, fills):
    fills_by_bid = {
        fill.get("bid_id") or fill.get("order_id"): fill
        for fill in fills
    }
    bid_results = []

    for order in orders:
        bid_id = order.get("bid_id") or order.get("order_id")
        fill = fills_by_bid.get(bid_id, {})

        bid_results.append(
            {
                **order,
                "bid_id": bid_id,
                "bid_status": "paper_filled",
                "lifecycle_status": "paper_filled",
                "submission_status": "paper_filled",
                "filled_volume_mwh": fill.get("filled_volume_mwh", 0.0),
                "fill_price_eur_mwh": fill.get("fill_price_eur_mwh"),
                "paper_fill_id": fill.get("paper_fill_id"),
                "paper_notional_eur": fill.get("notional_eur"),
            }
        )

    return bid_results


def build_paper_lifecycle(proposal):
    lifecycle = proposal.get("bid_lifecycle", [])

    if not lifecycle:
        return [
            {
                "step": "paper_submission",
                "label": "Paper submission",
                "status": "paper_filled",
                "owner": "paper_adapter",
            }
        ]

    status_by_step = {
        "paper_submission": "paper_filled",
        "live_submission": "disabled",
    }

    return [
        {
            **step,
            "status": status_by_step.get(step.get("step"), step.get("status")),
        }
        for step in lifecycle
    ]



