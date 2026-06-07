from datetime import datetime


EPEX_DE_LU_BIDDING_ZONE = "DE_LU"
DEFAULT_EPEX_CURRENCY = "EUR"
MINIMUM_RESERVE_POWER_MW = 1.0


def build_market_bid_package(
    asset,
    dispatch_rows,
    market,
    forecast_confidence=None,
    market_lifecycle=None,
    selected_route=None,
):
    route = selected_route or {}
    lifecycle = market_lifecycle or {}
    adapter_id = route.get("adapter_id") or lifecycle.get("adapter_id")
    generated_at = datetime.now().isoformat(timespec="seconds")

    if adapter_id == "epex_day_ahead":
        orders = build_epex_auction_orders(
            dispatch_rows=dispatch_rows,
            market=market,
            confidence=forecast_confidence,
            lifecycle=lifecycle,
            route=route,
            product_resolver=infer_day_ahead_product,
            package_market_product_id="day_ahead_arbitrage",
            package_order_type="auction_limit_curve",
            package_prefix="epex-da",
        )
    elif adapter_id == "epex_intraday_auction":
        orders = build_epex_auction_orders(
            dispatch_rows=dispatch_rows,
            market=market,
            confidence=forecast_confidence,
            lifecycle=lifecycle,
            route=route,
            product_resolver=lambda *_: "INTRADAY_AUCTION_15_MIN",
            package_market_product_id="intraday_arbitrage",
            package_order_type="auction_limit_order",
            package_prefix="epex-ida",
        )
    elif adapter_id == "epex_intraday_continuous":
        orders = build_epex_continuous_orders(
            dispatch_rows=dispatch_rows,
            market=market,
            confidence=forecast_confidence,
            lifecycle=lifecycle,
            route=route,
        )
    elif adapter_id == "regelleistung_fcr":
        orders = build_fcr_capacity_package(asset=asset, lifecycle=lifecycle, route=route)
    elif adapter_id == "regelleistung_afrr":
        orders = build_balancing_capacity_energy_package(
            asset=asset,
            lifecycle=lifecycle,
            route=route,
            market=market,
            product_prefix="AFRR",
            package_prefix="afrr",
            activation_mode="automatic",
            reservation_share_key="afrr_energy_reservation_share",
            default_reservation_share=0.25,
        )
    elif adapter_id == "regelleistung_mfrr":
        orders = build_balancing_capacity_energy_package(
            asset=asset,
            lifecycle=lifecycle,
            route=route,
            market=market,
            product_prefix="MFRR",
            package_prefix="mfrr",
            activation_mode="manual",
            reservation_share_key="mfrr_energy_reservation_share",
            default_reservation_share=0.2,
        )
    else:
        orders = build_epex_auction_orders(
            dispatch_rows=dispatch_rows,
            market=market,
            confidence=forecast_confidence,
            lifecycle=lifecycle,
            route=route,
            product_resolver=infer_day_ahead_product,
            package_market_product_id=infer_market_product_id(market),
            package_order_type=lifecycle.get("order_style") or "limit_order",
            package_prefix="generic",
        )

    validation = validate_bid_package(
        adapter_id=adapter_id,
        lifecycle=lifecycle,
        orders=orders,
    )

    return {
        "adapter_id": adapter_id,
        "asset_id": asset.asset_id,
        "bid_package_id": f"pkg-{asset.asset_id}-{adapter_id or 'generic'}-{generated_at}",
        "generated_at": generated_at,
        "market": market,
        "market_segment": route.get("market_segment"),
        "order_style": lifecycle.get("order_style"),
        "package_status": "draft_ready" if validation["status"] == "passed" else "draft_blocked",
        "submission_mode": "preview_only",
        "summary": summarize_package(orders=orders, validation=validation),
        "validation": validation,
        "orders": orders,
    }


def build_epex_auction_orders(
    dispatch_rows,
    market,
    confidence,
    lifecycle,
    route,
    product_resolver,
    package_market_product_id,
    package_order_type,
    package_prefix,
):
    orders = []
    shared = shared_forecast_controls(confidence)

    for index, row in enumerate(dispatch_rows or []):
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

        delivery_start = row.get("timestamp")
        delivery_end = row.get("delivery_end") or delivery_start
        limit_price = round(numeric(row.get("price")), 2)
        risk_adjusted_volume_mwh = round(volume_mwh * shared["volume_multiplier"], 4)
        risk_adjusted_volume_mw = round((volume_mwh / 0.25) * shared["volume_multiplier"], 4)
        risk_adjusted_limit_price = risk_adjusted_price(
            side=side,
            limit_price=limit_price,
            price_buffer=shared["price_buffer"],
        )

        orders.append(
            build_common_order(
                bid_id=f"bid-{index + 1:03d}",
                order_id=f"{package_prefix}-draft-{index + 1:03d}",
                adapter_id=route.get("adapter_id"),
                market=market,
                lifecycle=lifecycle,
                route=route,
                market_product_id=package_market_product_id,
                market_product=product_resolver(delivery_start, delivery_end),
                package_order_type=package_order_type,
                package_schema_version="market_bid_package.v1",
                side=side,
                volume_mwh=volume_mwh,
                volume_mw=volume_mwh / 0.25,
                limit_price=limit_price,
                risk_adjusted_volume_mwh=risk_adjusted_volume_mwh,
                risk_adjusted_volume_mw=risk_adjusted_volume_mw,
                risk_adjusted_limit_price=risk_adjusted_limit_price,
                forecast_controls=shared,
                source_action=action,
                source_dispatch_index=index,
                delivery_start=delivery_start,
                delivery_end=delivery_end,
                venue="EPEX SPOT",
                bidding_zone=EPEX_DE_LU_BIDDING_ZONE,
                currency=DEFAULT_EPEX_CURRENCY,
                time_in_force="AUCTION",
            )
        )

    return orders


def build_epex_continuous_orders(dispatch_rows, market, confidence, lifecycle, route):
    orders = build_epex_auction_orders(
        dispatch_rows=dispatch_rows,
        market=market,
        confidence=confidence,
        lifecycle=lifecycle,
        route=route,
        product_resolver=lambda *_: "INTRADAY_CONTINUOUS_15_MIN",
        package_market_product_id="intraday_arbitrage",
        package_order_type="continuous_limit_order",
        package_prefix="epex-idc",
    )

    for order in orders:
        order.update(
            {
                "cancel_replace_policy": "cancel_replace_if_price_moves_more_than_max_slippage",
                "execution_style": infer_execution_style(order),
                "max_slippage_eur_mwh": 8.0,
                "partial_fill_policy": "allow_partial_with_residual_reprice",
                "time_in_force": "GOOD_FOR_SESSION",
            }
        )

    return orders


def build_fcr_capacity_package(asset, lifecycle, route):
    capability = build_reserve_capability(asset)
    capacity_mw = round_down_to_tenth(capability["available_symmetric_power_mw"])

    if capacity_mw <= 0:
        return []

    return [
        build_reserve_order(
            asset_id=asset.asset_id,
            adapter_id=route.get("adapter_id"),
            lifecycle=lifecycle,
            route=route,
            reserve_bid_id="fcr-capacity-001",
            market_product_id="fcr_capacity",
            product="FCR_CAPACITY",
            direction="symmetric",
            capacity_mw=capacity_mw,
            package_order_type="capacity_auction_offer",
            activation_mode="automatic_frequency_containment",
            status="draft",
        )
    ]


def build_balancing_capacity_energy_package(
    asset,
    lifecycle,
    route,
    market,
    product_prefix,
    package_prefix,
    activation_mode,
    reservation_share_key,
    default_reservation_share,
):
    capability = build_reserve_capability(asset)
    commercial_config = asset.commercial_config or {}
    reserve_share = numeric(commercial_config.get(reservation_share_key)) or default_reservation_share
    positive_capacity = round_down_to_tenth(capability["positive_capacity_mw"])
    negative_capacity = round_down_to_tenth(capability["negative_capacity_mw"])
    reserved_capacity = round(max(positive_capacity, negative_capacity) * reserve_share, 4)

    return [
        build_reserve_order(
            asset_id=asset.asset_id,
            adapter_id=route.get("adapter_id"),
            lifecycle=lifecycle,
            route=route,
            reserve_bid_id=f"{package_prefix}-positive-capacity-001",
            market_product_id=f"{package_prefix}_capacity",
            product=f"{product_prefix}_CAPACITY_POSITIVE",
            direction="positive",
            capacity_mw=positive_capacity,
            package_order_type="capacity_offer",
            activation_mode=activation_mode,
            status="draft" if positive_capacity >= MINIMUM_RESERVE_POWER_MW else "not_available",
            reserve_share=reserve_share,
            reserved_capacity_mw=reserved_capacity,
        ),
        build_reserve_order(
            asset_id=asset.asset_id,
            adapter_id=route.get("adapter_id"),
            lifecycle=lifecycle,
            route=route,
            reserve_bid_id=f"{package_prefix}-negative-capacity-001",
            market_product_id=f"{package_prefix}_capacity",
            product=f"{product_prefix}_CAPACITY_NEGATIVE",
            direction="negative",
            capacity_mw=negative_capacity,
            package_order_type="capacity_offer",
            activation_mode=activation_mode,
            status="draft" if negative_capacity >= MINIMUM_RESERVE_POWER_MW else "not_available",
            reserve_share=reserve_share,
            reserved_capacity_mw=reserved_capacity,
        ),
        build_activation_placeholder(
            asset_id=asset.asset_id,
            adapter_id=route.get("adapter_id"),
            lifecycle=lifecycle,
            route=route,
            reserve_bid_id=f"{package_prefix}-positive-energy-001",
            market=market,
            market_product_id=f"{package_prefix}_activation_energy",
            product=f"{product_prefix}_ENERGY_POSITIVE",
            direction="positive",
            linked_capacity_mw=positive_capacity,
            activation_mode=activation_mode,
        ),
        build_activation_placeholder(
            asset_id=asset.asset_id,
            adapter_id=route.get("adapter_id"),
            lifecycle=lifecycle,
            route=route,
            reserve_bid_id=f"{package_prefix}-negative-energy-001",
            market=market,
            market_product_id=f"{package_prefix}_activation_energy",
            product=f"{product_prefix}_ENERGY_NEGATIVE",
            direction="negative",
            linked_capacity_mw=negative_capacity,
            activation_mode=activation_mode,
        ),
    ]


def build_common_order(
    bid_id,
    order_id,
    adapter_id,
    market,
    lifecycle,
    route,
    market_product_id,
    market_product,
    package_order_type,
    package_schema_version,
    side,
    volume_mwh,
    volume_mw,
    limit_price,
    risk_adjusted_volume_mwh,
    risk_adjusted_volume_mw,
    risk_adjusted_limit_price,
    forecast_controls,
    source_action,
    source_dispatch_index,
    delivery_start,
    delivery_end,
    venue,
    bidding_zone,
    currency,
    time_in_force,
):
    return {
        "adapter_id": adapter_id,
        "approval_status": "requires_approval",
        "automation_eligibility": forecast_controls["automation_eligibility"],
        "automation_lane": lifecycle.get("automation_lane"),
        "bid_granularity": lifecycle.get("bid_granularity"),
        "bid_id": bid_id,
        "bid_status": "draft",
        "bid_type": "limit",
        "bidding_zone": bidding_zone,
        "confidence_reason": forecast_controls["confidence_reason"],
        "currency": currency,
        "delivery_end": delivery_end,
        "delivery_start": delivery_start,
        "delivery_time": delivery_start,
        "energy_mwh": round(volume_mwh, 4),
        "forecast_confidence_band": forecast_controls["confidence_band"],
        "forecast_confidence_score": round(forecast_controls["confidence_score"], 1),
        "gate_closure_label": lifecycle.get("gate_closure_label"),
        "lifecycle_status": "draft",
        "limit_price_eur_mwh": round(limit_price, 2),
        "market": market,
        "market_lifecycle_status": lifecycle.get("lifecycle_status"),
        "market_product": market_product,
        "market_product_id": market_product_id,
        "market_segment": route.get("market_segment"),
        "next_gate_closure_at": lifecycle.get("next_gate_closure_at"),
        "order_id": order_id,
        "order_style": lifecycle.get("order_style"),
        "package_order_type": package_order_type,
        "package_schema_version": package_schema_version,
        "price_limit_eur_mwh": round(limit_price, 2),
        "risk_adjusted_limit_price_eur_mwh": risk_adjusted_limit_price,
        "risk_adjusted_volume_mw": risk_adjusted_volume_mw,
        "risk_adjusted_volume_mwh": risk_adjusted_volume_mwh,
        "risk_status": confidence_risk_status(forecast_controls["confidence_band"]),
        "side": side,
        "source_action": source_action,
        "source_dispatch_index": source_dispatch_index,
        "status": "draft",
        "submission_status": "not_submitted",
        "time_in_force": time_in_force,
        "venue": venue,
        "volume_mw": round(volume_mw, 4),
        "volume_mwh": round(volume_mwh, 4),
    }


def build_reserve_order(
    asset_id,
    adapter_id,
    lifecycle,
    route,
    reserve_bid_id,
    market_product_id,
    product,
    direction,
    capacity_mw,
    package_order_type,
    activation_mode,
    status,
    reserve_share=None,
    reserved_capacity_mw=None,
):
    return {
        "adapter_id": adapter_id,
        "approval_status": "requires_approval",
        "automation_lane": lifecycle.get("automation_lane"),
        "bid_granularity": lifecycle.get("bid_granularity"),
        "bid_id": reserve_bid_id,
        "bid_status": status,
        "bid_type": "capacity",
        "capacity_mw": round(capacity_mw, 4),
        "direction": direction,
        "energy_mwh": 0,
        "gate_closure_label": lifecycle.get("gate_closure_label"),
        "lifecycle_status": status,
        "market": route.get("market_name"),
        "market_lifecycle_status": lifecycle.get("lifecycle_status"),
        "market_product": product,
        "market_product_id": market_product_id,
        "market_segment": route.get("market_segment"),
        "minimum_power_mw": MINIMUM_RESERVE_POWER_MW,
        "next_gate_closure_at": lifecycle.get("next_gate_closure_at"),
        "order_id": reserve_bid_id,
        "order_style": lifecycle.get("order_style"),
        "package_order_type": package_order_type,
        "package_schema_version": "market_bid_package.v1",
        "reserve_share": reserve_share,
        "reserved_capacity_mw": reserved_capacity_mw,
        "side": "reserve",
        "status": status,
        "submission_status": "not_submitted",
        "venue": "regelleistung.net",
        "volume_mw": round(capacity_mw, 4),
        "volume_mwh": 0,
        "activation_mode": activation_mode,
        "asset_id": asset_id,
    }


def build_activation_placeholder(
    asset_id,
    adapter_id,
    lifecycle,
    route,
    reserve_bid_id,
    market,
    market_product_id,
    product,
    direction,
    linked_capacity_mw,
    activation_mode,
):
    return {
        "activation_energy_price_eur_mwh": None,
        "activation_mode": activation_mode,
        "activation_policy": "requires_activation_price_model",
        "adapter_id": adapter_id,
        "approval_status": "requires_approval",
        "automation_lane": lifecycle.get("automation_lane"),
        "bid_granularity": lifecycle.get("bid_granularity"),
        "bid_id": reserve_bid_id,
        "bid_status": "placeholder",
        "bid_type": "activation_energy",
        "direction": direction,
        "energy_mwh": 0,
        "gate_closure_label": lifecycle.get("gate_closure_label"),
        "lifecycle_status": "placeholder",
        "linked_capacity_mw": round(linked_capacity_mw, 4),
        "market": market,
        "market_lifecycle_status": lifecycle.get("lifecycle_status"),
        "market_product": product,
        "market_product_id": market_product_id,
        "market_segment": route.get("market_segment"),
        "next_gate_closure_at": lifecycle.get("next_gate_closure_at"),
        "order_id": reserve_bid_id,
        "order_style": lifecycle.get("order_style"),
        "package_order_type": "activation_energy_placeholder",
        "package_schema_version": "market_bid_package.v1",
        "side": "reserve",
        "status": "placeholder",
        "submission_status": "not_submitted",
        "venue": "regelleistung.net",
        "volume_mw": 0,
        "volume_mwh": 0,
        "asset_id": asset_id,
    }


def build_reserve_capability(asset):
    battery_config = asset.battery_config or {}
    grid_connection = asset.grid_connection or {}
    max_charge_power_mw = numeric(
        battery_config.get("max_charge_power_mw")
        or battery_config.get("power_mw")
    )
    max_discharge_power_mw = numeric(
        battery_config.get("max_discharge_power_mw")
        or battery_config.get("power_mw")
    )
    capacity_mwh = numeric(battery_config.get("capacity_mwh"))
    min_soc_mwh = numeric(battery_config.get("min_soc_mwh"))
    soc_mwh = capacity_mwh * 0.5 if capacity_mwh else 0.0
    grid_import_limit_mw = numeric(
        grid_connection.get("max_import_mw")
        or grid_connection.get("connection_capacity_mw")
        or max_charge_power_mw
    )
    grid_export_limit_mw = numeric(
        grid_connection.get("max_export_mw")
        or grid_connection.get("connection_capacity_mw")
        or max_discharge_power_mw
    )
    upward_energy_mwh = max(soc_mwh - min_soc_mwh, 0.0)
    downward_energy_mwh = max(capacity_mwh - soc_mwh, 0.0)
    positive_capacity_mw = min(
        max_discharge_power_mw,
        grid_export_limit_mw,
        upward_energy_mwh,
    )
    negative_capacity_mw = min(
        max_charge_power_mw,
        grid_import_limit_mw,
        downward_energy_mwh,
    )
    available_symmetric_power_mw = min(positive_capacity_mw, negative_capacity_mw)

    return {
        "available_symmetric_power_mw": round(max(available_symmetric_power_mw, 0.0), 4),
        "negative_capacity_mw": round(max(negative_capacity_mw, 0.0), 4),
        "positive_capacity_mw": round(max(positive_capacity_mw, 0.0), 4),
    }


def validate_bid_package(adapter_id, lifecycle, orders):
    checks = [
        {
            "check": "has_market_route",
            "status": "passed" if adapter_id else "blocked",
            "message": "A market adapter route is selected for this package."
            if adapter_id
            else "No market adapter route is selected.",
        },
        {
            "check": "has_orders",
            "status": "passed" if orders else "blocked",
            "message": "The package contains market-native order rows."
            if orders
            else "The package has no tradable order rows.",
        },
        {
            "check": "lifecycle_configured",
            "status": "passed" if lifecycle.get("order_style") else "blocked",
            "message": "Market lifecycle and order style are configured."
            if lifecycle.get("order_style")
            else "Market lifecycle order style is missing.",
        },
        {
            "check": "gate_clock",
            "status": "review"
            if lifecycle.get("trading_clock_status") in ["urgent", "closed"]
            else "passed",
            "message": lifecycle.get("next_deadline_action")
            or "Gate timing is available for automation.",
        },
    ]
    status = "blocked" if any(check["status"] == "blocked" for check in checks) else "passed"

    return {
        "status": status,
        "checks": checks,
    }


def summarize_package(orders, validation):
    buy_orders = [order for order in orders if order.get("side") == "buy"]
    sell_orders = [order for order in orders if order.get("side") == "sell"]
    reserve_orders = [order for order in orders if order.get("side") == "reserve"]

    return {
        "buy_order_count": len(buy_orders),
        "order_count": len(orders),
        "reserve_order_count": len(reserve_orders),
        "sell_order_count": len(sell_orders),
        "total_buy_mwh": round(sum(numeric(order.get("volume_mwh")) for order in buy_orders), 4),
        "total_reserve_mw": round(sum(numeric(order.get("capacity_mw") or order.get("linked_capacity_mw")) for order in reserve_orders), 4),
        "total_sell_mwh": round(sum(numeric(order.get("volume_mwh")) for order in sell_orders), 4),
        "validation_status": validation["status"],
    }


def infer_day_ahead_product(delivery_start, delivery_end):
    if delivery_start and delivery_end and delivery_start != delivery_end:
        return "DAY_AHEAD_HOUR"

    return "DAY_AHEAD_15_MIN"


def infer_market_product_id(market):
    market_name = str(market or "").lower()

    if "intraday" in market_name:
        return "intraday_arbitrage"

    return "day_ahead_arbitrage"


def infer_execution_style(order):
    confidence_band = order.get("forecast_confidence_band")
    risk_status = order.get("risk_status")

    if confidence_band == "high" and risk_status == "passed":
        return "aggressive"

    if confidence_band == "medium":
        return "passive"

    return "do_not_cross"


def shared_forecast_controls(confidence):
    confidence = confidence or {}
    risk_policy = confidence.get("risk_policy", {})

    return {
        "automation_eligibility": confidence.get("automation_eligibility", "paper_only"),
        "confidence_band": confidence.get("confidence_band", "unknown"),
        "confidence_reason": confidence.get("reason", "Forecast confidence was not scored."),
        "confidence_score": numeric(confidence.get("confidence_score")),
        "price_buffer": numeric(risk_policy.get("price_buffer_eur_per_mwh")),
        "volume_multiplier": numeric(risk_policy.get("volume_multiplier")) or 1.0,
    }


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


def round_down_to_tenth(value):
    return int(max(value, 0.0) * 10) / 10


def numeric(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0
