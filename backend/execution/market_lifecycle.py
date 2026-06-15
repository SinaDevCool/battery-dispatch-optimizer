from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo


MARKET_TIMEZONE = ZoneInfo("Europe/Berlin")


MARKET_LIFECYCLE_SPECS = {
    "epex_day_ahead": {
        "automation_lane": "supervised_auction",
        "bid_granularity": "15_min_and_hourly",
        "delivery_model": "next_day_schedule",
        "gate_closure_label": "D-1 12:00 Europe/Berlin",
        "gate_closure_time": time(12, 0),
        "gate_rule": "daily_prior_day",
        "order_style": "auction_limit_curve",
        "required_evidence": [
            "forecast_snapshot",
            "asset_telemetry",
            "market_access",
            "risk_limits",
            "settlement_account",
        ],
        "supported_order_types": ["buy_limit", "sell_limit", "block"],
    },
    "epex_intraday_auction": {
        "automation_lane": "supervised_auction",
        "bid_granularity": "15_min",
        "delivery_model": "same_day_and_next_day_refinement",
        "gate_closure_label": "Configurable intraday auction gate",
        "gate_closure_time": time(15, 0),
        "gate_rule": "daily_same_day",
        "order_style": "auction_limit_orders",
        "required_evidence": [
            "updated_forecast_snapshot",
            "day_ahead_position",
            "asset_telemetry",
            "risk_limits",
            "auction_product_mapping",
        ],
        "supported_order_types": ["buy_limit", "sell_limit"],
    },
    "epex_intraday_continuous": {
        "automation_lane": "limited_live_rebalancing",
        "bid_granularity": "15_min_and_hourly",
        "delivery_model": "rolling_same_day_rebalance",
        "gate_closure_label": "Rolling close before delivery",
        "gate_rule": "rolling_delivery",
        "order_style": "continuous_limit_order_book",
        "required_evidence": [
            "latest_position",
            "live_order_book",
            "asset_telemetry",
            "liquidity_limits",
            "cancel_replace_controls",
        ],
        "rolling_gate_offset_minutes": 5,
        "supported_order_types": ["buy_limit", "sell_limit", "cancel_replace"],
    },
    "regelleistung_fcr": {
        "automation_lane": "supervised_capacity_auction",
        "bid_granularity": "4_hour_blocks",
        "delivery_model": "reserve_capacity",
        "gate_closure_label": "D-1 08:00 Europe/Berlin",
        "gate_closure_time": time(8, 0),
        "gate_rule": "daily_prior_day",
        "order_style": "capacity_auction",
        "required_evidence": [
            "asset_prequalification",
            "availability_forecast",
            "symmetric_capacity_check",
            "tso_access",
            "settlement_mapping",
        ],
        "supported_order_types": ["capacity_offer"],
    },
    "regelleistung_afrr": {
        "automation_lane": "limited_live_balancing",
        "bid_granularity": "15_min_and_4_hour_blocks",
        "delivery_model": "capacity_and_energy_activation",
        "gate_closure_label": "Configurable aFRR capacity and energy gates",
        "gate_closure_time": time(9, 0),
        "gate_rule": "daily_prior_day",
        "order_style": "capacity_and_energy_offer",
        "required_evidence": [
            "asset_prequalification",
            "activation_telemetry",
            "availability_forecast",
            "capacity_reservation",
            "tso_settlement_mapping",
        ],
        "supported_order_types": ["capacity_offer", "energy_price_update"],
    },
    "regelleistung_mfrr": {
        "automation_lane": "supervised_manual_activation",
        "bid_granularity": "15_min_and_4_hour_blocks",
        "delivery_model": "manual_reserve_capacity_energy",
        "gate_closure_label": "Configurable mFRR capacity and energy gates",
        "gate_closure_time": time(9, 0),
        "gate_rule": "daily_prior_day",
        "order_style": "capacity_and_manual_energy_offer",
        "required_evidence": [
            "asset_prequalification",
            "manual_activation_workflow",
            "availability_forecast",
            "imbalance_settlement_mapping",
            "tso_settlement_mapping",
        ],
        "supported_order_types": ["capacity_offer", "manual_activation_offer"],
    },
}


def get_market_lifecycle(adapter_id, now=None):
    spec = MARKET_LIFECYCLE_SPECS.get(adapter_id)

    if not spec:
        return {
            "adapter_id": adapter_id,
            "lifecycle_status": "unconfigured",
            "trading_clock_status": "unconfigured",
            "next_deadline_action": "Configure market lifecycle rules before automated trading.",
            "required_evidence": [],
            "supported_order_types": [],
        }

    current_time = normalize_now(now)
    gate = next_gate_closure(spec=spec, now=current_time)
    minutes_to_gate = (
        round((gate - current_time).total_seconds() / 60.0, 1)
        if gate
        else None
    )
    trading_clock_status = classify_trading_clock(minutes_to_gate)

    return {
        "adapter_id": adapter_id,
        "automation_lane": spec["automation_lane"],
        "bid_granularity": spec["bid_granularity"],
        "delivery_model": spec["delivery_model"],
        "gate_closure_label": spec["gate_closure_label"],
        "lifecycle_status": classify_lifecycle_status(trading_clock_status),
        "minutes_to_gate_closure": minutes_to_gate,
        "next_deadline_action": next_deadline_action(
            adapter_id=adapter_id,
            spec=spec,
            trading_clock_status=trading_clock_status,
            minutes_to_gate=minutes_to_gate,
        ),
        "next_gate_closure_at": (
            gate.isoformat(timespec="seconds") if gate else None
        ),
        "order_style": spec["order_style"],
        "required_evidence": spec["required_evidence"],
        "supported_order_types": spec["supported_order_types"],
        "trading_clock_status": trading_clock_status,
    }


def enrich_with_market_lifecycle(row):
    lifecycle = get_market_lifecycle(row.get("adapter_id"))

    return {
        **row,
        "automation_lane": lifecycle.get("automation_lane"),
        "bid_granularity": lifecycle.get("bid_granularity"),
        "gate_closure_label": lifecycle.get("gate_closure_label"),
        "lifecycle_status": lifecycle.get("lifecycle_status"),
        "market_lifecycle": lifecycle,
        "minutes_to_gate_closure": lifecycle.get("minutes_to_gate_closure"),
        "next_deadline_action": lifecycle.get("next_deadline_action"),
        "next_gate_closure_at": lifecycle.get("next_gate_closure_at"),
        "order_style": lifecycle.get("order_style"),
        "required_evidence": lifecycle.get("required_evidence", []),
        "supported_order_types": lifecycle.get("supported_order_types", []),
        "trading_clock_status": lifecycle.get("trading_clock_status"),
    }


def summarize_market_lifecycles(rows):
    lifecycles = [
        row.get("market_lifecycle") or get_market_lifecycle(row.get("adapter_id"))
        for row in rows
    ]

    return {
        "configured_market_lifecycle_count": len(
            [
                lifecycle
                for lifecycle in lifecycles
                if lifecycle.get("lifecycle_status") != "unconfigured"
            ]
        ),
        "urgent_gate_count": len(
            [
                lifecycle
                for lifecycle in lifecycles
                if lifecycle.get("trading_clock_status") == "urgent"
            ]
        ),
        "closed_gate_count": len(
            [
                lifecycle
                for lifecycle in lifecycles
                if lifecycle.get("trading_clock_status") == "closed"
            ]
        ),
        "next_gate_closure_at": next_market_gate(lifecycles),
    }


def next_gate_closure(spec, now):
    gate_rule = spec.get("gate_rule")

    if gate_rule == "rolling_delivery":
        return next_rolling_gate(spec=spec, now=now)

    gate_time = spec.get("gate_closure_time")
    if not gate_time:
        return None

    candidate = datetime.combine(now.date(), gate_time, tzinfo=MARKET_TIMEZONE)
    if candidate <= now:
        candidate = candidate + timedelta(days=1)

    return candidate


def next_rolling_gate(spec, now):
    offset = int(spec.get("rolling_gate_offset_minutes", 0))
    minute = ((now.minute // 15) + 1) * 15
    delivery = now.replace(second=0, microsecond=0)

    if minute >= 60:
        delivery = delivery.replace(minute=0) + timedelta(hours=1)
    else:
        delivery = delivery.replace(minute=minute)

    gate = delivery - timedelta(minutes=offset)
    if gate <= now:
        gate = gate + timedelta(minutes=15)

    return gate


def normalize_now(now):
    if now is None:
        return datetime.now(tz=MARKET_TIMEZONE)

    if now.tzinfo is None:
        return now.replace(tzinfo=MARKET_TIMEZONE)

    return now.astimezone(MARKET_TIMEZONE)


def classify_trading_clock(minutes_to_gate):
    if minutes_to_gate is None:
        return "unconfigured"

    if minutes_to_gate < 0:
        return "closed"

    if minutes_to_gate <= 30:
        return "urgent"

    if minutes_to_gate <= 180:
        return "same_session"

    if minutes_to_gate <= 1440:
        return "today"

    return "scheduled"


def classify_lifecycle_status(trading_clock_status):
    if trading_clock_status == "unconfigured":
        return "unconfigured"

    if trading_clock_status == "closed":
        return "gate_closed"

    if trading_clock_status == "urgent":
        return "deadline_critical"

    return "tradable_window"


def next_deadline_action(adapter_id, spec, trading_clock_status, minutes_to_gate):
    if trading_clock_status == "unconfigured":
        return "Configure gate closure and order lifecycle rules."

    if trading_clock_status == "closed":
        return "Do not submit new orders; reconcile and prepare the next tradable window."

    if trading_clock_status == "urgent":
        return (
            f"Freeze bid changes for {adapter_id}; only risk-reducing automation should continue."
        )

    if trading_clock_status == "same_session":
        return (
            f"Complete proposal, paper validation, and approval before the {spec['gate_closure_label']} gate."
        )

    return (
        f"Prepare {spec['order_style']} package and monitor evidence before gate closure."
    )


def next_market_gate(lifecycles):
    gates = [
        lifecycle.get("next_gate_closure_at")
        for lifecycle in lifecycles
        if lifecycle.get("next_gate_closure_at")
    ]

    return sorted(gates)[0] if gates else None



