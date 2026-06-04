from datetime import datetime

from src.execution.market_adapters.base import MarketAdapter
from src.execution.market_adapters.epex_day_ahead import parse_datetime
from src.execution.pretrade_proposal import numeric


EPEX_DE_LU_BIDDING_ZONE = "DE_LU"
DEFAULT_BID_ASK_SPREAD_EUR_MWH = 3.5
DEFAULT_MAX_SLIPPAGE_EUR_MWH = 8.0


class EpexIntradayContinuousAdapter(MarketAdapter):
    adapter_id = "epex_intraday_continuous"
    live_submission = False

    def submit_bids(self, bids, submitted_at):
        preview = build_epex_intraday_continuous_preview(
            bids=bids,
            generated_at=submitted_at,
        )

        return {
            "adapter_id": self.adapter_id,
            "status": preview["status"],
            "submitted_at": submitted_at,
            "live_submission": self.live_submission,
            "summary": preview["summary"],
            "bids": preview["orders"],
            "validation": preview["validation"],
        }


def build_epex_intraday_continuous_preview(
    bids,
    generated_at=None,
    bid_ask_spread_eur_mwh=DEFAULT_BID_ASK_SPREAD_EUR_MWH,
    max_slippage_eur_mwh=DEFAULT_MAX_SLIPPAGE_EUR_MWH,
):
    generated_at = generated_at or datetime.now().isoformat(timespec="seconds")
    orders = [
        build_continuous_order(
            bid=bid,
            index=index,
            bid_ask_spread_eur_mwh=bid_ask_spread_eur_mwh,
            max_slippage_eur_mwh=max_slippage_eur_mwh,
        )
        for index, bid in enumerate(bids or [])
    ]
    validation = validate_continuous_orders(orders)
    status = "ready_for_trader_review" if validation["status"] == "passed" else "invalid"

    return {
        "status": status,
        "adapter_id": EpexIntradayContinuousAdapter.adapter_id,
        "adapter_name": "EPEX SPOT Intraday Continuous",
        "venue": "EPEX SPOT",
        "market_segment": "intraday_continuous",
        "bidding_zone": EPEX_DE_LU_BIDDING_ZONE,
        "environment": "preview",
        "live_submission": False,
        "generated_at": generated_at,
        "assumptions": {
            "bid_ask_spread_eur_mwh": bid_ask_spread_eur_mwh,
            "max_slippage_eur_mwh": max_slippage_eur_mwh,
            "partial_fill_policy": "allow_partial_with_residual_reprice",
            "cancel_replace_policy": "cancel_replace_if_price_moves_more_than_max_slippage",
        },
        "summary": summarize_orders(orders, validation),
        "validation": validation,
        "orders": orders,
        "audit": [
            {
                "event": "epex_intraday_continuous_mapping",
                "actor": "epex_intraday_continuous_adapter",
                "status": validation["status"],
                "note": "Mapped internal execution bids into EPEX Intraday Continuous order intents. Live submission is disabled.",
            }
        ],
    }


def build_continuous_order(
    bid,
    index,
    bid_ask_spread_eur_mwh,
    max_slippage_eur_mwh,
):
    side = bid.get("side")
    delivery_start = bid.get("delivery_start") or bid.get("delivery_time")
    delivery_end = bid.get("delivery_end") or delivery_start
    limit_price = numeric(
        bid.get("risk_adjusted_limit_price_eur_mwh")
        or bid.get("limit_price_eur_mwh")
        or bid.get("price_limit_eur_mwh")
    )
    quantity_mw = numeric(
        bid.get("risk_adjusted_volume_mw")
        or bid.get("volume_mw")
    )
    execution_style = infer_execution_style(bid)
    reference_price = build_reference_price(
        side=side,
        limit_price=limit_price,
        bid_ask_spread_eur_mwh=bid_ask_spread_eur_mwh,
        execution_style=execution_style,
    )

    return {
        "exchange_order_id": f"epex-idc-preview-{index + 1:03d}",
        "source_bid_id": bid.get("bid_id") or bid.get("order_id"),
        "portfolio": bid.get("asset_id") or "default_site",
        "venue": "EPEX SPOT",
        "market_segment": "intraday_continuous",
        "bidding_zone": EPEX_DE_LU_BIDDING_ZONE,
        "delivery_start": delivery_start,
        "delivery_end": delivery_end,
        "product": "INTRADAY_CONTINUOUS_15_MIN",
        "side": "BUY" if side == "buy" else "SELL" if side == "sell" else side,
        "order_type": "LIMIT",
        "execution_style": execution_style,
        "quantity_mw": round(quantity_mw, 4),
        "limit_price_eur_mwh": round(limit_price, 2),
        "reference_price_eur_mwh": round(reference_price, 2),
        "bid_ask_spread_eur_mwh": bid_ask_spread_eur_mwh,
        "max_slippage_eur_mwh": max_slippage_eur_mwh,
        "partial_fill_policy": "allow_partial_with_residual_reprice",
        "cancel_replace_policy": "cancel_replace_if_price_moves_more_than_max_slippage",
        "time_in_force": "GOOD_FOR_SESSION",
        "currency": "EUR",
        "status": "preview",
        "live_submission": False,
    }


def infer_execution_style(bid):
    confidence_band = bid.get("forecast_confidence_band")
    risk_status = bid.get("risk_status")

    if confidence_band == "high" and risk_status == "passed":
        return "aggressive"

    if confidence_band == "medium":
        return "passive"

    return "do_not_cross"


def build_reference_price(
    side,
    limit_price,
    bid_ask_spread_eur_mwh,
    execution_style,
):
    half_spread = bid_ask_spread_eur_mwh / 2

    if execution_style == "aggressive":
        return limit_price + half_spread if side == "buy" else limit_price - half_spread

    if execution_style == "passive":
        return limit_price - half_spread if side == "buy" else limit_price + half_spread

    return limit_price


def validate_continuous_orders(orders):
    checks = [
        {
            "check": "has_orders",
            "status": "passed" if orders else "blocked",
            "message": "At least one EPEX Intraday Continuous order intent exists."
            if orders
            else "No orders are available for Intraday Continuous preview.",
        },
        validate_bidding_zone(orders),
        validate_delivery_times(orders),
        validate_time_to_delivery(orders),
        validate_sides(orders),
        validate_quantities(orders),
        validate_prices(orders),
        validate_spread_assumptions(orders),
        validate_partial_fill_policy(orders),
        validate_cancel_replace_policy(orders),
    ]
    status = "blocked" if any(check["status"] == "blocked" for check in checks) else "passed"

    return {
        "status": status,
        "checks": checks,
    }


def validate_bidding_zone(orders):
    invalid = [
        order for order in orders
        if order.get("bidding_zone") != EPEX_DE_LU_BIDDING_ZONE
    ]

    return {
        "check": "bidding_zone",
        "status": "passed" if not invalid else "blocked",
        "message": "All orders target the Germany/Luxembourg DE_LU bidding zone."
        if not invalid
        else "One or more orders do not target DE_LU.",
    }


def validate_delivery_times(orders):
    invalid = [
        order for order in orders
        if parse_datetime(order.get("delivery_start")) is None
    ]

    return {
        "check": "delivery_times",
        "status": "passed" if not invalid else "blocked",
        "message": "All orders have parseable delivery timestamps."
        if not invalid
        else "One or more orders have invalid delivery timestamps.",
    }


def validate_time_to_delivery(orders):
    missing = [
        order for order in orders
        if parse_datetime(order.get("delivery_start")) is None
    ]

    return {
        "check": "time_to_delivery",
        "status": "review" if not missing else "blocked",
        "message": "Time-to-delivery needs live clock and exchange session checks before automation."
        if not missing
        else "Time-to-delivery cannot be evaluated for invalid delivery timestamps.",
    }


def validate_sides(orders):
    invalid = [
        order for order in orders
        if order.get("side") not in ["BUY", "SELL"]
    ]

    return {
        "check": "side",
        "status": "passed" if not invalid else "blocked",
        "message": "All orders use BUY or SELL side."
        if not invalid
        else "One or more orders have invalid side values.",
    }


def validate_quantities(orders):
    invalid = [
        order for order in orders
        if numeric(order.get("quantity_mw")) <= 0
    ]

    return {
        "check": "quantity",
        "status": "passed" if not invalid else "blocked",
        "message": "All orders have positive MW quantity."
        if not invalid
        else "One or more orders have non-positive MW quantity.",
    }


def validate_prices(orders):
    invalid = [
        order for order in orders
        if not -500 <= numeric(order.get("limit_price_eur_mwh")) <= 4000
    ]

    return {
        "check": "price_limits",
        "status": "passed" if not invalid else "blocked",
        "message": "All orders are within conservative continuous market price bounds."
        if not invalid
        else "One or more orders are outside conservative continuous market price bounds.",
    }


def validate_spread_assumptions(orders):
    invalid = [
        order for order in orders
        if numeric(order.get("bid_ask_spread_eur_mwh")) <= 0
        or numeric(order.get("max_slippage_eur_mwh")) <= 0
    ]

    return {
        "check": "spread_and_slippage",
        "status": "passed" if not invalid else "blocked",
        "message": "Bid/ask spread and max slippage assumptions are configured."
        if not invalid
        else "Spread or slippage assumptions are missing.",
    }


def validate_partial_fill_policy(orders):
    invalid = [
        order for order in orders
        if not order.get("partial_fill_policy")
    ]

    return {
        "check": "partial_fill_policy",
        "status": "passed" if not invalid else "blocked",
        "message": "Partial-fill policy is configured for all order intents."
        if not invalid
        else "Partial-fill policy is missing.",
    }


def validate_cancel_replace_policy(orders):
    invalid = [
        order for order in orders
        if not order.get("cancel_replace_policy")
    ]

    return {
        "check": "cancel_replace_policy",
        "status": "passed" if not invalid else "blocked",
        "message": "Cancel/replace policy is configured for all order intents."
        if not invalid
        else "Cancel/replace policy is missing.",
    }


def summarize_orders(orders, validation):
    buy_orders = [order for order in orders if order.get("side") == "BUY"]
    sell_orders = [order for order in orders if order.get("side") == "SELL"]
    aggressive = [
        order for order in orders
        if order.get("execution_style") == "aggressive"
    ]
    passive = [
        order for order in orders
        if order.get("execution_style") == "passive"
    ]
    do_not_cross = [
        order for order in orders
        if order.get("execution_style") == "do_not_cross"
    ]

    return {
        "order_count": len(orders),
        "buy_order_count": len(buy_orders),
        "sell_order_count": len(sell_orders),
        "aggressive_order_count": len(aggressive),
        "passive_order_count": len(passive),
        "do_not_cross_order_count": len(do_not_cross),
        "total_buy_mw": round(sum(numeric(order.get("quantity_mw")) for order in buy_orders), 4),
        "total_sell_mw": round(sum(numeric(order.get("quantity_mw")) for order in sell_orders), 4),
        "validation_status": validation["status"],
        "live_submission": False,
    }
