from backend.validation.dispatch_validator import validate_dispatch_signal


def build_test_battery_config():
    return {
        "capacity_mwh": 20.0,
        "initial_soc_mwh": 10.0,
        "min_soc_mwh": 2.0,
        "max_charge_power_mw": 10.0,
        "max_discharge_power_mw": 10.0,
        "charge_efficiency": 0.95,
        "discharge_efficiency": 0.95,
    }


def build_test_strategy_config():
    return {
        "timestep_hours": 0.25,
    }


def test_validate_dispatch_signal_returns_warning_for_short_valid_dispatch():
    signal_result = {
        "summary": {
            "total_pnl_eur": 10.0,
        },
        "metadata": {
            "asset_id": "asset_1",
            "market_profile_id": "de_lu_day_ahead",
            "forecast_provider": "local_saved_forecast",
            "forecast_model": "local_saved_forecast",
        },
        "dispatch": [
            {
                "timestamp": "2026-01-01 00:00:00",
                "action": "idle",
                "soc_mwh": 10.0,
                "grid_energy_mwh": 0.0,
                "battery_energy_mwh": 0.0,
                "pnl_eur": 0.0,
                "total_pnl_eur": 0.0,
            },
            {
                "timestamp": "2026-01-01 00:15:00",
                "action": "discharge",
                "soc_mwh": 7.5,
                "grid_energy_mwh": 2.5,
                "battery_energy_mwh": 2.5,
                "pnl_eur": 10.0,
                "total_pnl_eur": 10.0,
            },
        ],
    }

    validation = validate_dispatch_signal(
        signal_result=signal_result,
        battery_config=build_test_battery_config(),
        strategy_config=build_test_strategy_config(),
        market_profile_id="de_lu_day_ahead",
    ).to_dict()

    assert validation["status"] == "warning"
    assert validation["error_count"] == 0
    assert validation["warning_count"] >= 1


def test_validate_dispatch_signal_fails_when_soc_is_below_minimum():
    signal_result = {
        "summary": {
            "total_pnl_eur": 0.0,
        },
        "metadata": {
            "asset_id": "asset_1",
            "market_profile_id": "de_lu_day_ahead",
            "forecast_provider": "local_saved_forecast",
            "forecast_model": "local_saved_forecast",
        },
        "dispatch": [
            {
                "timestamp": "2026-01-01 00:00:00",
                "action": "discharge",
                "soc_mwh": 1.0,
                "grid_energy_mwh": 1.0,
                "battery_energy_mwh": 1.0,
                "pnl_eur": 0.0,
                "total_pnl_eur": 0.0,
            },
        ],
    }

    validation = validate_dispatch_signal(
        signal_result=signal_result,
        battery_config=build_test_battery_config(),
        strategy_config=build_test_strategy_config(),
        market_profile_id="de_lu_day_ahead",
    ).to_dict()

    assert validation["status"] == "fail"
    assert validation["error_count"] == 1
    assert validation["errors"][0]["code"] == "soc_below_minimum"



