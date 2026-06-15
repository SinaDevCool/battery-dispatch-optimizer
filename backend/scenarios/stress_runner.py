from copy import deepcopy

from backend.config.battery_config import DEFAULT_BATTERY_CONFIG, DEFAULT_STRATEGY_CONFIG
from backend.config.commercial_config import DEFAULT_COMMERCIAL_CONFIG
from backend.signals.signal_engine import generate_battery_signal


def apply_price_stress(price_data, mode, value):
    stressed_data = deepcopy(price_data)

    for row in stressed_data:
        price = float(row["price"])

        if mode == "add":
            row["price"] = price + value

        elif mode == "multiply":
            row["price"] = price * value

        elif mode == "floor":
            row["price"] = max(price, value)

        elif mode == "cap":
            row["price"] = min(price, value)

        else:
            raise ValueError(f"Unsupported stress mode: {mode}")

    return stressed_data


def summarize_stress_result(name, result):
    summary = result["summary"]

    return {
        "scenario_name": name,
        "signal": summary["signal"],
        "opportunity_level": summary["opportunity_level"],
        "total_pnl_eur": summary["total_pnl_eur"],
        "profit_per_mw_day": summary["profit_per_mw_day"],
        "charge_hours": summary["charge_hours"],
        "discharge_hours": summary["discharge_hours"],
    }


def run_price_stress_tests(
    price_data,
    battery_config=None,
    strategy_config=None,
    commercial_config=None,
):
    if battery_config is None:
        battery_config = DEFAULT_BATTERY_CONFIG

    if strategy_config is None:
        strategy_config = DEFAULT_STRATEGY_CONFIG

    if commercial_config is None:
        commercial_config = DEFAULT_COMMERCIAL_CONFIG

    stress_cases = [
        {
            "name": "Base case",
            "mode": "add",
            "value": 0,
        },
        {
            "name": "Prices +20 EUR/MWh",
            "mode": "add",
            "value": 20,
        },
        {
            "name": "Prices -20 EUR/MWh",
            "mode": "add",
            "value": -20,
        },
        {
            "name": "Prices 20% higher",
            "mode": "multiply",
            "value": 1.2,
        },
        {
            "name": "Prices 20% lower",
            "mode": "multiply",
            "value": 0.8,
        },
        {
            "name": "Negative prices floored at 0",
            "mode": "floor",
            "value": 0,
        },
        {
            "name": "Peak prices capped at 80",
            "mode": "cap",
            "value": 80,
        },
    ]

    results = []

    for stress_case in stress_cases:
        stressed_price_data = apply_price_stress(
            price_data=price_data,
            mode=stress_case["mode"],
            value=stress_case["value"],
        )

        signal_result = generate_battery_signal(
            price_data=stressed_price_data,
            battery_config=battery_config,
            strategy_config=strategy_config,
            commercial_config=commercial_config,
        )

        results.append(
            summarize_stress_result(
                name=stress_case["name"],
                result=signal_result,
            )
        )

    return results


