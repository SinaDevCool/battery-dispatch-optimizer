from copy import deepcopy
from dataclasses import is_dataclass, replace
from types import SimpleNamespace

from backend.config.battery_config import DEFAULT_BATTERY_CONFIG, DEFAULT_STRATEGY_CONFIG
from backend.config.commercial_config import DEFAULT_COMMERCIAL_CONFIG
from backend.services.asset_physics import apply_asset_physics
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
    row = {
        "scenario_name": name,
        "investor_case": result.get("investor_case"),
        "stress_category": result.get("stress_category"),
        "signal": summary["signal"],
        "opportunity_level": summary["opportunity_level"],
        "total_pnl_eur": summary["total_pnl_eur"],
        "profit_per_mw_day": summary["profit_per_mw_day"],
        "charge_hours": summary["charge_hours"],
        "discharge_hours": summary["discharge_hours"],
        "charged_mwh": summary.get("charged_mwh"),
        "discharged_mwh": summary.get("discharged_mwh"),
        "throughput_mwh": summary.get("throughput_mwh"),
    }
    physics = result.get("asset_physics") or {}
    if physics:
        row["physics_model"] = physics.get("physics_model")
    if "renewable_charge_mwh" in summary:
        row["renewable_charge_mwh"] = summary["renewable_charge_mwh"]
        row["renewable_charge_share"] = summary.get("renewable_charge_share")
    if "peak_shaved_mwh" in summary:
        row["peak_shaved_mwh"] = summary["peak_shaved_mwh"]
    return row


def apply_battery_stress(battery_config, multiplier):
    stressed_config = deepcopy(battery_config)

    for key in [
        "capacity_mwh",
        "initial_soc_mwh",
        "max_charge_power_mw",
        "max_discharge_power_mw",
    ]:
        if key in stressed_config and stressed_config[key] is not None:
            stressed_config[key] = float(stressed_config[key]) * multiplier

    if "min_soc_mwh" in stressed_config and stressed_config["min_soc_mwh"] is not None:
        stressed_config["min_soc_mwh"] = min(
            float(stressed_config["min_soc_mwh"]),
            float(stressed_config.get("capacity_mwh") or stressed_config["min_soc_mwh"]),
        )

    return stressed_config


def run_price_stress_tests(
    price_data,
    battery_config=None,
    strategy_config=None,
    commercial_config=None,
    asset=None,
    forecast_file=None,
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
            "investor_case": "Base case",
            "stress_category": "baseline",
            "mode": "add",
            "value": 0,
        },
        {
            "name": "Low-price downside",
            "investor_case": "Low-price case",
            "stress_category": "market_downside",
            "mode": "multiply",
            "value": 0.8,
        },
        {
            "name": "High-volatility upside",
            "investor_case": "High-volatility upside",
            "stress_category": "market_upside",
            "mode": "multiply",
            "value": 1.2,
        },
        {
            "name": "Dispatch underperformance",
            "investor_case": "Dispatch underperformance",
            "stress_category": "operational_downside",
            "mode": "add",
            "value": 0,
            "battery_multiplier": 0.85,
        },
        {
            "name": "Battery degradation / availability reduction",
            "investor_case": "Battery degradation / availability reduction",
            "stress_category": "degradation_availability",
            "mode": "add",
            "value": 0,
            "battery_multiplier": 0.75,
        },
        {
            "name": "Negative prices floored at 0",
            "investor_case": "Negative-price floor",
            "stress_category": "price_shape",
            "mode": "floor",
            "value": 0,
        },
        {
            "name": "Peak prices capped at 80",
            "investor_case": "Capped upside",
            "stress_category": "price_shape",
            "mode": "cap",
            "value": 80,
        },
    ]
    stress_cases.extend(asset_specific_stress_cases(asset))

    results = []

    for stress_case in stress_cases:
        stressed_price_data = apply_price_stress(
            price_data=price_data,
            mode=stress_case["mode"],
            value=stress_case["value"],
        )
        stressed_battery_config = apply_battery_stress(
            battery_config,
            stress_case.get("battery_multiplier", 1),
        )

        signal_result = generate_battery_signal(
            price_data=stressed_price_data,
            battery_config=stressed_battery_config,
            strategy_config=strategy_config,
            commercial_config=commercial_config,
        )
        if asset is not None and forecast_file is not None:
            stress_asset = asset_with_battery_config(asset, stressed_battery_config)
            signal_result = apply_asset_physics(
                asset=stress_asset,
                signal_result=signal_result,
                forecast_file=forecast_file,
            )
        signal_result["investor_case"] = stress_case["investor_case"]
        signal_result["stress_category"] = stress_case["stress_category"]

        results.append(
            summarize_stress_result(
                name=stress_case["name"],
                result=signal_result,
            )
        )

    return results


def asset_specific_stress_cases(asset):
    asset_type = str(get_asset_value(asset, "asset_type") or "")

    if "solar" in asset_type:
        return [
            {
                "name": "Solar curtailment/export-limit stress",
                "investor_case": "Solar curtailment/export-limit stress",
                "stress_category": "asset_specific_downside",
                "mode": "cap",
                "value": 90,
                "battery_multiplier": 0.85,
            }
        ]

    if "industrial" in asset_type or "behind" in asset_type:
        return [
            {
                "name": "Industrial site-load stress",
                "investor_case": "Industrial site-load stress",
                "stress_category": "asset_specific_downside",
                "mode": "add",
                "value": 0,
                "battery_multiplier": 0.8,
            }
        ]

    return [
        {
            "name": "Merchant spread compression",
            "investor_case": "Merchant spread compression",
            "stress_category": "asset_specific_downside",
            "mode": "cap",
            "value": 75,
            "battery_multiplier": 0.9,
        }
    ]


def asset_with_battery_config(asset, battery_config):
    if is_dataclass(asset):
        return replace(asset, battery_config=battery_config)
    if hasattr(asset, "to_dict"):
        payload = asset.to_dict()
    else:
        payload = dict(asset or {})
    payload["battery_config"] = battery_config
    return SimpleNamespace(**payload)


def get_asset_value(asset, key):
    if hasattr(asset, key):
        return getattr(asset, key)
    if isinstance(asset, dict):
        return asset.get(key)
    if hasattr(asset, "to_dict"):
        return asset.to_dict().get(key)
    return None
