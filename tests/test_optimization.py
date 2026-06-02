from src.config.battery_config import DEFAULT_BATTERY_CONFIG, DEFAULT_STRATEGY_CONFIG
from src.config.commercial_config import DEFAULT_COMMERCIAL_CONFIG
from src.optimization.optimizer_registry import (
    get_dispatch_optimizer,
    list_optimizer_engines,
)


def test_optimizer_registry_lists_available_engines():
    engines = list_optimizer_engines()

    assert "rule_based_v1" in engines
    assert "linear_v1" in engines


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
