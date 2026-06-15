from backend.optimization.primitives.battery_optimizer import BatteryOptimizer


def test_battery_charges_when_price_is_low():
    battery = BatteryOptimizer(
        capacity_mwh=20.0,
        initial_soc_mwh=10.0,
        min_soc_mwh=2.0,
        max_charge_power_mw=10.0,
        max_discharge_power_mw=10.0,
        charge_efficiency=0.95,
        discharge_efficiency=0.95,
    )

    price_data = [
        {
            "timestamp": "2026-01-01 00:00:00",
            "price": 10.0,
        }
    ]

    results = battery.optimize(
        price_data=price_data,
        low_price_threshold=20.0,
        high_price_threshold=80.0,
        timestep_hours=1.0,
    )

    first_row = results[0]

    assert first_row["action"] == "charge"
    assert first_row["soc_mwh"] > 10.0
    assert first_row["soc_mwh"] <= 20.0
    assert first_row["pnl_eur"] < 0


def test_battery_discharges_when_price_is_high():
    battery = BatteryOptimizer(
        capacity_mwh=20.0,
        initial_soc_mwh=10.0,
        min_soc_mwh=2.0,
        max_charge_power_mw=10.0,
        max_discharge_power_mw=10.0,
        charge_efficiency=0.95,
        discharge_efficiency=0.95,
    )

    price_data = [
        {
            "timestamp": "2026-01-01 00:00:00",
            "price": 100.0,
        }
    ]

    results = battery.optimize(
        price_data=price_data,
        low_price_threshold=20.0,
        high_price_threshold=80.0,
        timestep_hours=1.0,
    )

    first_row = results[0]

    assert first_row["action"] == "discharge"
    assert first_row["soc_mwh"] < 10.0
    assert first_row["soc_mwh"] >= 2.0
    assert first_row["pnl_eur"] > 0


def test_battery_stays_idle_when_price_is_middle():
    battery = BatteryOptimizer(
        capacity_mwh=20.0,
        initial_soc_mwh=10.0,
        min_soc_mwh=2.0,
        max_charge_power_mw=10.0,
        max_discharge_power_mw=10.0,
        charge_efficiency=0.95,
        discharge_efficiency=0.95,
    )

    price_data = [
        {
            "timestamp": "2026-01-01 00:00:00",
            "price": 50.0,
        }
    ]

    results = battery.optimize(
        price_data=price_data,
        low_price_threshold=20.0,
        high_price_threshold=80.0,
        timestep_hours=1.0,
    )

    first_row = results[0]

    assert first_row["action"] == "idle"
    assert first_row["soc_mwh"] == 10.0
    assert first_row["pnl_eur"] == 0.0


def test_soc_never_goes_above_capacity():
    battery = BatteryOptimizer(
        capacity_mwh=20.0,
        initial_soc_mwh=19.5,
        min_soc_mwh=2.0,
        max_charge_power_mw=10.0,
        max_discharge_power_mw=10.0,
        charge_efficiency=0.95,
        discharge_efficiency=0.95,
    )

    price_data = [
        {
            "timestamp": "2026-01-01 00:00:00",
            "price": -10.0,
        }
    ]

    results = battery.optimize(
        price_data=price_data,
        low_price_threshold=20.0,
        high_price_threshold=80.0,
        timestep_hours=1.0,
    )

    first_row = results[0]

    assert first_row["action"] == "charge"
    assert first_row["soc_mwh"] <= 20.0


def test_soc_never_goes_below_minimum():
    battery = BatteryOptimizer(
        capacity_mwh=20.0,
        initial_soc_mwh=2.5,
        min_soc_mwh=2.0,
        max_charge_power_mw=10.0,
        max_discharge_power_mw=10.0,
        charge_efficiency=0.95,
        discharge_efficiency=0.95,
    )

    price_data = [
        {
            "timestamp": "2026-01-01 00:00:00",
            "price": 100.0,
        }
    ]

    results = battery.optimize(
        price_data=price_data,
        low_price_threshold=20.0,
        high_price_threshold=80.0,
        timestep_hours=1.0,
    )

    first_row = results[0]

    assert first_row["action"] == "discharge"
    assert first_row["soc_mwh"] >= 2.0



