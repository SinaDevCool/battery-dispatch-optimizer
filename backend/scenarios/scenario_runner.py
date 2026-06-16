from copy import deepcopy
from dataclasses import is_dataclass, replace
from types import SimpleNamespace

from backend.services.asset_physics import apply_asset_physics
from backend.signals.signal_engine import generate_battery_signal


DEFAULT_SCENARIOS = [
    {
        "name": "Small battery - 1 MW / 2 MWh",
        "battery_config": {
            "capacity_mwh": 2.0,
            "initial_soc_mwh": 1.0,
            "min_soc_mwh": 0.2,
            "max_charge_power_mw": 1.0,
            "max_discharge_power_mw": 1.0,
            "charge_efficiency": 0.95,
            "discharge_efficiency": 0.95,
        },
    },
    {
        "name": "Medium battery - 5 MW / 10 MWh",
        "battery_config": {
            "capacity_mwh": 10.0,
            "initial_soc_mwh": 5.0,
            "min_soc_mwh": 1.0,
            "max_charge_power_mw": 5.0,
            "max_discharge_power_mw": 5.0,
            "charge_efficiency": 0.95,
            "discharge_efficiency": 0.95,
        },
    },
    {
        "name": "Base battery - 10 MW / 20 MWh",
        "battery_config": {
            "capacity_mwh": 20.0,
            "initial_soc_mwh": 10.0,
            "min_soc_mwh": 2.0,
            "max_charge_power_mw": 10.0,
            "max_discharge_power_mw": 10.0,
            "charge_efficiency": 0.95,
            "discharge_efficiency": 0.95,
        },
    },
    {
        "name": "Large battery - 20 MW / 40 MWh",
        "battery_config": {
            "capacity_mwh": 40.0,
            "initial_soc_mwh": 20.0,
            "min_soc_mwh": 4.0,
            "max_charge_power_mw": 20.0,
            "max_discharge_power_mw": 20.0,
            "charge_efficiency": 0.95,
            "discharge_efficiency": 0.95,
        },
    },
]


def run_scenarios(
    price_data,
    scenarios=None,
    strategy_config=None,
    commercial_config=None,
    asset=None,
    forecast_file=None,
):
    if scenarios is None:
        scenarios = build_asset_scenarios(asset) if asset else DEFAULT_SCENARIOS

    results = []

    for scenario in scenarios:
        signal_result = generate_battery_signal(
            price_data=price_data,
            battery_config=scenario["battery_config"],
            strategy_config=strategy_config,
            commercial_config=commercial_config,
        )
        if asset is not None and forecast_file is not None:
            scenario_asset = asset_with_battery_config(asset, scenario["battery_config"])
            signal_result = apply_asset_physics(
                asset=scenario_asset,
                signal_result=signal_result,
                forecast_file=forecast_file,
            )

        summary = signal_result["summary"]
        row = {
            "scenario_name": scenario["name"],
            "scenario_basis": scenario.get("scenario_basis") or "generic_battery_size",
            "capacity_mwh": scenario["battery_config"]["capacity_mwh"],
            "max_charge_power_mw": scenario["battery_config"]["max_charge_power_mw"],
            "max_discharge_power_mw": scenario["battery_config"]["max_discharge_power_mw"],
            "signal": summary["signal"],
            "opportunity_level": summary["opportunity_level"],
            "total_pnl_eur": summary["total_pnl_eur"],
            "profit_per_mw_day": summary["profit_per_mw_day"],
            "charge_hours": summary["charge_hours"],
            "discharge_hours": summary["discharge_hours"],
            "first_charge_timestamp": summary["first_charge_timestamp"],
            "first_discharge_timestamp": summary["first_discharge_timestamp"],
            "charged_mwh": summary.get("charged_mwh"),
            "discharged_mwh": summary.get("discharged_mwh"),
            "throughput_mwh": summary.get("throughput_mwh"),
        }
        physics = signal_result.get("asset_physics") or {}
        if physics:
            row["asset_type"] = get_asset_value(asset, "asset_type")
            row["physics_model"] = physics.get("physics_model")
        if "renewable_charge_mwh" in summary:
            row["renewable_charge_mwh"] = summary["renewable_charge_mwh"]
            row["renewable_charge_share"] = summary.get("renewable_charge_share")
        if "peak_shaved_mwh" in summary:
            row["peak_shaved_mwh"] = summary["peak_shaved_mwh"]
        results.append(row)

    return results


def build_asset_scenarios(asset):
    asset_name = (
        get_asset_value(asset, "asset_name")
        or get_asset_value(asset, "site_name")
        or "Selected asset"
    )
    battery_config = deepcopy(get_asset_value(asset, "battery_config") or {})
    return [
        {
            "name": f"{asset_name} - current mock asset",
            "scenario_basis": "selected_asset_base_case",
            "battery_config": scale_battery_config(
                battery_config,
                capacity_multiplier=1.0,
                power_multiplier=1.0,
            ),
        },
        {
            "name": f"{asset_name} - conservative availability",
            "scenario_basis": "selected_asset_downside_availability",
            "battery_config": scale_battery_config(
                battery_config,
                capacity_multiplier=0.9,
                power_multiplier=0.85,
            ),
        },
        {
            "name": f"{asset_name} - higher energy duration",
            "scenario_basis": "selected_asset_energy_upside",
            "battery_config": scale_battery_config(
                battery_config,
                capacity_multiplier=1.25,
                power_multiplier=1.0,
            ),
        },
        {
            "name": f"{asset_name} - higher power access",
            "scenario_basis": "selected_asset_power_upside",
            "battery_config": scale_battery_config(
                battery_config,
                capacity_multiplier=1.0,
                power_multiplier=1.2,
            ),
        },
    ]


def scale_battery_config(config, *, capacity_multiplier, power_multiplier):
    scaled = deepcopy(config)
    for key in ["capacity_mwh", "initial_soc_mwh", "min_soc_mwh"]:
        if scaled.get(key) is not None:
            scaled[key] = round(float(scaled[key]) * capacity_multiplier, 4)
    for key in ["max_charge_power_mw", "max_discharge_power_mw"]:
        if scaled.get(key) is not None:
            scaled[key] = round(float(scaled[key]) * power_multiplier, 4)
    if scaled.get("min_soc_mwh") is not None and scaled.get("capacity_mwh") is not None:
        scaled["min_soc_mwh"] = min(
            float(scaled["min_soc_mwh"]),
            float(scaled["capacity_mwh"]),
        )
    if scaled.get("initial_soc_mwh") is not None and scaled.get("capacity_mwh") is not None:
        scaled["initial_soc_mwh"] = min(
            float(scaled["initial_soc_mwh"]),
            float(scaled["capacity_mwh"]),
        )
    return scaled


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
