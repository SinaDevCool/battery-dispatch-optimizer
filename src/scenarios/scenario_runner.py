from src.signals.signal_engine import generate_battery_signal


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


def run_scenarios(price_data, scenarios=None, strategy_config=None):
    if scenarios is None:
        scenarios = DEFAULT_SCENARIOS

    results = []

    for scenario in scenarios:
        signal_result = generate_battery_signal(
            price_data=price_data,
            battery_config=scenario["battery_config"],
            strategy_config=strategy_config,
        )

        summary = signal_result["summary"]

        results.append(
            {
                "scenario_name": scenario["name"],
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
            }
        )

    return results