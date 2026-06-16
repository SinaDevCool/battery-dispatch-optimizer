from backend.config.battery_config import DEFAULT_BATTERY_CONFIG, DEFAULT_STRATEGY_CONFIG
from backend.config.commercial_config import DEFAULT_COMMERCIAL_CONFIG
from backend.optimization.optimizer_registry import (
    get_dispatch_optimizer,
    list_optimizer_engines,
)
from backend.services.dispatch_service import optimize_dispatch_from_price_data


def test_optimizer_registry_lists_available_engines():
    engines = list_optimizer_engines()

    assert "rule_based_v1" in engines
    assert "linear_v1" in engines
    assert "linear_program_v1" in engines


def test_linear_optimizer_finds_profitable_dispatch():
    price_data = [
        {"timestamp": "2026-01-01 00:00:00", "price": 40.0},
        {"timestamp": "2026-01-01 01:00:00", "price": 5.0},
        {"timestamp": "2026-01-01 02:00:00", "price": 15.0},
        {"timestamp": "2026-01-01 03:00:00", "price": 120.0},
        {"timestamp": "2026-01-01 04:00:00", "price": 95.0},
    ]

    optimizer = get_dispatch_optimizer("linear_v1")

    result = optimizer.optimize(
        price_data=price_data,
        battery_config=DEFAULT_BATTERY_CONFIG,
        strategy_config=DEFAULT_STRATEGY_CONFIG,
        commercial_config=DEFAULT_COMMERCIAL_CONFIG,
    )

    actions = [row["action"] for row in result.dispatch]

    assert result.status == "ok"
    assert result.summary["signal"] == "ACTION"
    assert result.summary["total_pnl_eur"] > 0
    assert "charge" in actions
    assert "discharge" in actions
    assert result.metadata["constraint_status"] == "feasible"
    assert result.metadata["method"] == "linear_dispatch_program"
    assert result.metadata["objective_function"]["sense"] == "maximize"
    assert result.metadata["constraints"]["no_simultaneous_charge_discharge"]


def test_linear_optimizer_stays_idle_when_prices_are_flat():
    price_data = [
        {"timestamp": "2026-01-01 00:00:00", "price": 50.0},
        {"timestamp": "2026-01-01 01:00:00", "price": 50.0},
        {"timestamp": "2026-01-01 02:00:00", "price": 50.0},
        {"timestamp": "2026-01-01 03:00:00", "price": 50.0},
    ]

    optimizer = get_dispatch_optimizer("linear_v1")

    result = optimizer.optimize(
        price_data=price_data,
        battery_config=DEFAULT_BATTERY_CONFIG,
        strategy_config=DEFAULT_STRATEGY_CONFIG,
        commercial_config=DEFAULT_COMMERCIAL_CONFIG,
    )

    assert result.status == "ok"
    assert result.summary["signal"] == "NO_ACTION"
    assert result.summary["total_pnl_eur"] == 0.0
    assert all(row["action"] == "idle" for row in result.dispatch)


def test_linear_program_optimizer_alias_uses_investor_facing_engine_name():
    price_data = [
        {"timestamp": "2026-01-01 00:00:00", "price": 5.0},
        {"timestamp": "2026-01-01 01:00:00", "price": 120.0},
    ]

    optimizer = get_dispatch_optimizer("linear_program_v1")

    result = optimizer.optimize(
        price_data=price_data,
        battery_config={
            **DEFAULT_BATTERY_CONFIG,
            "capacity_mwh": 2.0,
            "initial_soc_mwh": 1.0,
            "min_soc_mwh": 0.0,
            "max_charge_power_mw": 1.0,
            "max_discharge_power_mw": 1.0,
        },
        strategy_config={**DEFAULT_STRATEGY_CONFIG, "timestep_hours": 1.0},
        commercial_config=DEFAULT_COMMERCIAL_CONFIG,
    )

    assert result.optimizer_engine == "linear_program_v1"
    assert result.status == "ok"
    assert result.metadata["formulation"] == "linear_objective_with_linear_soc_power_energy_constraints"


def test_dispatch_service_runs_linear_program_optimizer():
    price_data = [
        {"timestamp": "2026-01-01 00:00:00", "price": 5.0},
        {"timestamp": "2026-01-01 01:00:00", "price": 120.0},
    ]

    result = optimize_dispatch_from_price_data(
        price_data=price_data,
        battery_config={
            **DEFAULT_BATTERY_CONFIG,
            "capacity_mwh": 2.0,
            "initial_soc_mwh": 1.0,
            "min_soc_mwh": 0.0,
            "max_charge_power_mw": 1.0,
            "max_discharge_power_mw": 1.0,
        },
        strategy_config={**DEFAULT_STRATEGY_CONFIG, "timestep_hours": 1.0},
        commercial_config=DEFAULT_COMMERCIAL_CONFIG,
        optimizer_engine="linear_program_v1",
    )

    assert result.optimizer_engine == "linear_program_v1"
    assert result.signal_result["optimization"]["optimizer_engine"] == "linear_program_v1"
    assert result.signal_result["optimization"]["constraint_status"] == "feasible"



