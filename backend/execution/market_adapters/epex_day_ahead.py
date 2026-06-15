from datetime import datetime, time

from backend.execution.market_adapters.base import MarketAdapter
from backend.execution.pretrade_proposal import numeric


EPEX_DE_LU_BIDDING_ZONE = "DE_LU"
EPEX_DAY_AHEAD_GATE_CLOSURE = "12:00 Europe/Berlin D-1"


class EpexDayAheadAdapter(MarketAdapter):
    adapter_id = "epex_day_ahead"
    live_submission = False

    def submit_bids(self, bids, submitted_at):
        preview = build_epex_day_ahead_preview(
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


def build_epex_day_ahead_preview(bids, generated_at=None):
    generated_at = generated_at or datetime.now().isoformat(timespec="seconds")
    orders = [
        build_epex_order(bid=bid, index=index)
        for index, bid in enumerate(bids or [])
    ]
    validation = validate_epex_orders(orders)
    status = "ready_for_broker_submission" if validation["status"] == "passed" else "invalid"

    return {
        "status": status,
        "adapter_id": EpexDayAheadAdapter.adapter_id,
        "adapter_name": "EPEX SPOT Day-Ahead",
        "venue": "EPEX SPOT",
        "market_segment": "day_ahead",
        "bidding_zone": EPEX_DE_LU_BIDDING_ZONE,
        "environment": "preview",
        "live_submission": False,
        "gate_closure": EPEX_DAY_AHEAD_GATE_CLOSURE,
        "generated_at": generated_at,
        "summary": summarize_orders(orders, validation),
        "validation": validation,
        "orders": orders,
        "audit": [
            {
                "event": "epex_day_ahead_mapping",
                "actor": "epex_day_ahead_adapter",
                "status": validation["status"],
                "note": "Mapped internal execution bids into EPEX Day-Ahead order preview rows. Live submission is disabled.",
            }
        ],
    }


def build_epex_order(bid, index):
    side = bid.get("side")
    delivery_start = bid.get("delivery_start") or bid.get("delivery_time")
    delivery_end = bid.get("delivery_end") or delivery_start
    volume_mw = numeric(
        bid.get("risk_adjusted_volume_mw")
        or bid.get("volume_mw")
    )
    price = numeric(
        bid.get("risk_adjusted_limit_price_eur_mwh")
        or bid.get("limit_price_eur_mwh")
        or bid.get("price_limit_eur_mwh")
    )

    return {
        "exchange_order_id": f"epex-da-preview-{index + 1:03d}",
        "source_bid_id": bid.get("bid_id") or bid.get("order_id"),
        "portfolio": bid.get("asset_id") or "default_site",
        "venue": "EPEX SPOT",
        "market_segment": "day_ahead",
        "bidding_zone": EPEX_DE_LU_BIDDING_ZONE,
        "delivery_start": delivery_start,
        "delivery_end": delivery_end,
        "product": infer_epex_product(delivery_start, delivery_end),
        "side": "BUY" if side == "buy" else "SELL" if side == "sell" else side,
        "order_type": "LIMIT",
        "quantity_mw": round(volume_mw, 4),
        "limit_price_eur_mwh": round(price, 2),
        "time_in_force": "AUCTION",
        "currency": "EUR",
        "status": "preview",
        "live_submission": False,
    }


def infer_epex_product(delivery_start, delivery_end):
    start = parse_datetime(delivery_start)
    end = parse_datetime(delivery_end)

    if start and end and start != end:
        minutes = int((end - start).total_seconds() / 60)
    else:
        minutes = 15

    return "DAY_AHEAD_HOUR" if minutes >= 60 else "DAY_AHEAD_15_MIN"


def validate_epex_orders(orders):
    checks = []

    checks.append(
        {
            "check": "has_orders",
            "status": "passed" if orders else "blocked",
            "message": "At least one EPEX Day-Ahead order preview row exists."
            if orders
            else "No orders are available for EPEX Day-Ahead preview.",
        }
    )

    invalid_zone = [
        order for order in orders
        if order.get("bidding_zone") != EPEX_DE_LU_BIDDING_ZONE
    ]
    checks.append(
        {
            "check": "bidding_zone",
            "status": "passed" if not invalid_zone else "blocked",
            "message": "All orders target the Germany/Luxembourg DE_LU bidding zone."
            if not invalid_zone
            else "One or more orders do not target DE_LU.",
        }
    )

    checks.append(validate_delivery_times(orders))
    checks.append(validate_sides(orders))
    checks.append(validate_quantities(orders))
    checks.append(validate_prices(orders))
    checks.append(validate_gate_closure())

    status = "blocked" if any(check["status"] == "blocked" for check in checks) else "passed"

    return {
        "status": status,
        "checks": checks,
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
        "message": "All orders are within conservative EPEX preview price bounds."
        if not invalid
        else "One or more orders are outside conservative EPEX preview price bounds.",
    }


def validate_gate_closure():
    now = datetime.now()
    is_before_noon = now.time() < time(12, 0)

    return {
        "check": "auction_gate_closure",
        "status": "passed" if is_before_noon else "review",
        "message": "Current local time is before the indicative D-1 noon gate closure."
        if is_before_noon
        else "Current local time is after the indicative D-1 noon gate closure; operator review is required.",
        "context": {
            "gate_closure": EPEX_DAY_AHEAD_GATE_CLOSURE,
            "local_time": now.isoformat(timespec="seconds"),
        },
    }


def summarize_orders(orders, validation):
    buy_orders = [order for order in orders if order.get("side") == "BUY"]
    sell_orders = [order for order in orders if order.get("side") == "SELL"]

    return {
        "order_count": len(orders),
        "buy_order_count": len(buy_orders),
        "sell_order_count": len(sell_orders),
        "total_buy_mw": round(sum(numeric(order.get("quantity_mw")) for order in buy_orders), 4),
        "total_sell_mw": round(sum(numeric(order.get("quantity_mw")) for order in sell_orders), 4),
        "validation_status": validation["status"],
        "live_submission": False,
    }


def parse_datetime(value):
    if not value:
        return None

    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None



