from datetime import datetime


def simulate_market_paper_execution(proposal, generated_at=None):
    generated_at = generated_at or datetime.now().isoformat(timespec="seconds")
    bid_package = proposal.get("bid_package") or {}
    orders = bid_package.get("orders") or proposal.get("bids") or proposal.get("orders") or []
    adapter_id = bid_package.get("adapter_id") or first_value(orders, "adapter_id")

    if adapter_id == "epex_intraday_continuous":
        result = simulate_epex_continuous(orders)
    elif adapter_id in ["regelleistung_fcr", "regelleistung_afrr", "regelleistung_mfrr"]:
        result = simulate_reserve_market(orders, adapter_id)
    else:
        result = simulate_epex_auction(orders, adapter_id)

    return {
        "adapter_id": adapter_id or "paper",
        "assumptions": result["assumptions"],
        "audit": [
            {
                "event": "market_specific_paper_execution",
                "actor": "market_paper_simulator",
                "status": result["status"],
                "note": result["audit_note"],
            }
        ],
        "awards": result["awards"],
        "fills": result["fills"],
        "generated_at": generated_at,
        "market_execution_model": result["market_execution_model"],
        "settlement_basis": result["settlement_basis"],
        "status": result["status"],
        "summary": result["summary"],
        "validation": result["validation"],
    }


def simulate_epex_auction(orders, adapter_id):
    fills = []
    awards = []
    clearing_price = estimate_auction_clearing_price(orders)

    for index, order in enumerate(energy_orders(orders)):
        side = order.get("side")
        limit_price = numeric(
            order.get("risk_adjusted_limit_price_eur_mwh")
            or order.get("limit_price_eur_mwh")
        )
        eligible = (
            side == "buy" and limit_price >= clearing_price
        ) or (
            side == "sell" and limit_price <= clearing_price
        )
        filled_volume = numeric(order.get("volume_mwh")) if eligible else 0.0
        notional = signed_notional(side=side, volume_mwh=filled_volume, price=clearing_price)
        status = "filled" if eligible else "rejected_price"

        fills.append(
            build_fill(
                order=order,
                index=index,
                filled_volume_mwh=filled_volume,
                fill_price_eur_mwh=clearing_price,
                notional_eur=notional,
                status=status,
                execution_detail="auction_clearing",
            )
        )
        awards.append(
            {
                "award_id": f"auction-award-{index + 1:03d}",
                "bid_id": order.get("bid_id") or order.get("order_id"),
                "clearing_price_eur_mwh": clearing_price,
                "market_product": order.get("market_product"),
                "status": "accepted" if eligible else "rejected",
            }
        )

    validation = validate_simulation(
        checks=[
            has_orders_check(orders),
            {
                "check": "auction_clearing_price",
                "status": "passed" if clearing_price is not None else "blocked",
                "message": "Indicative auction clearing price was derived from the package.",
            },
        ]
    )

    return {
        "assumptions": {
            "clearing_model": "median_risk_adjusted_limit_price",
            "clearing_price_eur_mwh": clearing_price,
            "fill_model": "accepted_if_buy_above_or_sell_below_clearing_price",
            "live_submission": False,
        },
        "audit_note": "Simulated EPEX auction acceptance using an indicative clearing price.",
        "awards": awards,
        "fills": fills,
        "market_execution_model": "epex_auction_clearing",
        "settlement_basis": "energy_auction_award",
        "status": "completed" if validation["status"] == "passed" else "blocked",
        "summary": summarize_energy_fills(fills),
        "validation": validation,
    }


def simulate_epex_continuous(orders):
    fills = []
    awards = []

    for index, order in enumerate(energy_orders(orders)):
        side = order.get("side")
        limit_price = numeric(
            order.get("risk_adjusted_limit_price_eur_mwh")
            or order.get("limit_price_eur_mwh")
        )
        spread = numeric(order.get("bid_ask_spread_eur_mwh")) or 3.5
        max_slippage = numeric(order.get("max_slippage_eur_mwh")) or 8.0
        execution_style = order.get("execution_style") or "do_not_cross"
        fill_ratio = continuous_fill_ratio(execution_style)
        fill_price = continuous_fill_price(
            side=side,
            limit_price=limit_price,
            spread=spread,
            max_slippage=max_slippage,
            execution_style=execution_style,
        )
        filled_volume = round(numeric(order.get("volume_mwh")) * fill_ratio, 4)
        status = "partial_fill" if 0 < fill_ratio < 1 else "filled" if fill_ratio else "resting"
        fills.append(
            build_fill(
                order=order,
                index=index,
                filled_volume_mwh=filled_volume,
                fill_price_eur_mwh=fill_price,
                notional_eur=signed_notional(side=side, volume_mwh=filled_volume, price=fill_price),
                status=status,
                execution_detail="continuous_limit_book",
            )
        )
        awards.append(
            {
                "award_id": f"continuous-fill-{index + 1:03d}",
                "bid_id": order.get("bid_id") or order.get("order_id"),
                "execution_style": execution_style,
                "fill_ratio": fill_ratio,
                "status": status,
            }
        )

    validation = validate_simulation(
        checks=[
            has_orders_check(orders),
            {
                "check": "cancel_replace_controls",
                "status": "passed"
                if all(order.get("cancel_replace_policy") for order in energy_orders(orders))
                else "review",
                "message": "Cancel/replace policy exists for continuous order simulation.",
            },
            {
                "check": "partial_fill_policy",
                "status": "passed"
                if all(order.get("partial_fill_policy") for order in energy_orders(orders))
                else "review",
                "message": "Partial-fill policy exists for continuous order simulation.",
            },
        ]
    )

    return {
        "assumptions": {
            "fill_model": "execution_style_fill_ratio",
            "live_submission": False,
            "price_model": "limit_price_adjusted_by_spread_and_slippage",
        },
        "audit_note": "Simulated EPEX continuous partial fills, slippage, and cancel/replace controls.",
        "awards": awards,
        "fills": fills,
        "market_execution_model": "epex_continuous_limit_book",
        "settlement_basis": "energy_partial_fill",
        "status": "completed" if validation["status"] == "passed" else "review",
        "summary": summarize_energy_fills(fills),
        "validation": validation,
    }


def simulate_reserve_market(orders, adapter_id):
    reserve_orders = [
        order for order in orders
        if order.get("bid_type") in ["capacity", "activation_energy"]
    ]
    awards = []
    fills = []
    capacity_price = reserve_capacity_price(adapter_id)

    for index, order in enumerate(reserve_orders):
        capacity_mw = numeric(order.get("capacity_mw") or order.get("linked_capacity_mw"))
        available = order.get("status") in ["draft", "placeholder"] and capacity_mw >= 0
        awarded_capacity = capacity_mw if available and order.get("bid_type") == "capacity" else 0.0
        notional = round(awarded_capacity * capacity_price, 2)
        award_status = "awarded" if awarded_capacity >= 1.0 else "not_awarded"

        awards.append(
            {
                "award_id": f"{adapter_id}-award-{index + 1:03d}",
                "bid_id": order.get("bid_id") or order.get("order_id"),
                "capacity_mw": round(awarded_capacity, 4),
                "capacity_price_eur_mw": capacity_price,
                "direction": order.get("direction"),
                "product": order.get("market_product"),
                "status": award_status if order.get("bid_type") == "capacity" else "activation_placeholder",
            }
        )

        if order.get("bid_type") == "capacity":
            fills.append(
                {
                    "bid_id": order.get("bid_id") or order.get("order_id"),
                    "capacity_mw": round(awarded_capacity, 4),
                    "delivery_time": order.get("delivery_time"),
                    "execution_detail": "reserve_capacity_award",
                    "fill_price_eur_mwh": None,
                    "filled_volume_mwh": 0.0,
                    "market_product_id": order.get("market_product_id"),
                    "notional_eur": notional,
                    "order_id": order.get("order_id"),
                    "paper_fill_id": f"reserve-paper-{index + 1:03d}",
                    "requested_volume_mwh": 0.0,
                    "side": "reserve",
                    "status": award_status,
                }
            )

    validation = validate_simulation(
        checks=[
            has_orders_check(reserve_orders),
            {
                "check": "reserve_capacity_award",
                "status": "passed"
                if any(award.get("status") == "awarded" for award in awards)
                else "review",
                "message": "At least one reserve capacity bid is awardable."
                if any(award.get("status") == "awarded" for award in awards)
                else "Reserve package has no awardable capacity above minimum size.",
            },
            {
                "check": "activation_energy_placeholder",
                "status": "review"
                if any(order.get("bid_type") == "activation_energy" for order in reserve_orders)
                else "passed",
                "message": "Activation energy rows are placeholders until activation-price logic is connected.",
            },
        ]
    )

    return {
        "assumptions": {
            "activation_model": "placeholder",
            "capacity_price_eur_mw": capacity_price,
            "fill_model": "capacity_award_if_minimum_power_met",
            "live_submission": False,
        },
        "audit_note": "Simulated reserve capacity awards and activation-energy placeholders.",
        "awards": awards,
        "fills": fills,
        "market_execution_model": f"{adapter_id}_capacity_award",
        "settlement_basis": "reserve_capacity_award",
        "status": "completed" if validation["status"] == "passed" else "review",
        "summary": summarize_reserve_awards(awards, fills),
        "validation": validation,
    }


def build_fill(
    order,
    index,
    filled_volume_mwh,
    fill_price_eur_mwh,
    notional_eur,
    status,
    execution_detail,
):
    return {
        "bid_id": order.get("bid_id") or order.get("order_id"),
        "delivery_end": order.get("delivery_end"),
        "delivery_start": order.get("delivery_start"),
        "delivery_time": order.get("delivery_time") or order.get("delivery_start"),
        "execution_detail": execution_detail,
        "fill_price_eur_mwh": fill_price_eur_mwh,
        "filled_volume_mwh": round(filled_volume_mwh, 4),
        "limit_price_eur_mwh": order.get("limit_price_eur_mwh"),
        "market_product_id": order.get("market_product_id"),
        "notional_eur": round(notional_eur, 2),
        "order_id": order.get("order_id"),
        "paper_fill_id": f"paper-fill-{index + 1:03d}",
        "requested_volume_mwh": order.get("volume_mwh"),
        "side": order.get("side"),
        "status": status,
    }


def summarize_energy_fills(fills):
    buy_cost = sum(
        abs(numeric(fill.get("notional_eur")))
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
        "accepted_order_count": len([fill for fill in fills if fill.get("status") in ["filled", "partial_fill"]]),
        "buy_cost_eur": round(buy_cost, 2),
        "filled_order_count": len([fill for fill in fills if numeric(fill.get("filled_volume_mwh")) > 0]),
        "order_count": len(fills),
        "paper_pnl_eur": round(paper_pnl, 2),
        "rejected_order_count": len([fill for fill in fills if fill.get("status") == "rejected_price"]),
        "sell_revenue_eur": round(sell_revenue, 2),
        "total_filled_mwh": round(sum(numeric(fill.get("filled_volume_mwh")) for fill in fills), 4),
    }


def summarize_reserve_awards(awards, fills):
    reserve_revenue = sum(numeric(fill.get("notional_eur")) for fill in fills)

    return {
        "accepted_order_count": len([award for award in awards if award.get("status") == "awarded"]),
        "awarded_capacity_mw": round(sum(numeric(award.get("capacity_mw")) for award in awards if award.get("status") == "awarded"), 4),
        "filled_order_count": len(fills),
        "order_count": len(awards),
        "paper_pnl_eur": round(reserve_revenue, 2),
        "reserve_revenue_eur": round(reserve_revenue, 2),
        "sell_revenue_eur": round(reserve_revenue, 2),
    }


def validate_simulation(checks):
    status = "blocked" if any(check["status"] == "blocked" for check in checks) else "passed"

    return {
        "checks": checks,
        "status": status,
    }


def has_orders_check(orders):
    return {
        "check": "has_orders",
        "status": "passed" if orders else "blocked",
        "message": "Market-specific paper simulation has order rows to evaluate."
        if orders
        else "No order rows are available for market-specific simulation.",
    }


def estimate_auction_clearing_price(orders):
    prices = sorted(
        numeric(
            order.get("risk_adjusted_limit_price_eur_mwh")
            or order.get("limit_price_eur_mwh")
        )
        for order in energy_orders(orders)
    )

    if not prices:
        return None

    midpoint = len(prices) // 2

    if len(prices) % 2:
        return round(prices[midpoint], 2)

    return round((prices[midpoint - 1] + prices[midpoint]) / 2, 2)


def continuous_fill_ratio(execution_style):
    if execution_style == "aggressive":
        return 0.85

    if execution_style == "passive":
        return 0.55

    return 0.25


def continuous_fill_price(side, limit_price, spread, max_slippage, execution_style):
    if execution_style == "aggressive":
        adjustment = min(spread / 2, max_slippage)
        return round(limit_price + adjustment if side == "buy" else limit_price - adjustment, 2)

    if execution_style == "passive":
        adjustment = spread / 2
        return round(limit_price - adjustment if side == "buy" else limit_price + adjustment, 2)

    return round(limit_price, 2)


def reserve_capacity_price(adapter_id):
    if adapter_id == "regelleistung_fcr":
        return 85.0

    if adapter_id == "regelleistung_afrr":
        return 65.0

    if adapter_id == "regelleistung_mfrr":
        return 48.0

    return 50.0


def signed_notional(side, volume_mwh, price):
    notional = numeric(volume_mwh) * numeric(price)

    if side == "buy":
        return -notional

    return notional


def energy_orders(orders):
    return [
        order for order in orders
        if order.get("side") in ["buy", "sell"]
    ]


def first_value(rows, key):
    for row in rows or []:
        if row.get(key):
            return row.get(key)

    return None


def numeric(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0



