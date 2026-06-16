import pytest

from backend.scenarios.stress_runner import apply_price_stress, run_price_stress_tests


def test_apply_price_stress_add():
    price_data = [
        {"timestamp": "2026-01-01 00:00:00", "price": 10},
        {"timestamp": "2026-01-01 01:00:00", "price": 20},
    ]

    result = apply_price_stress(price_data, mode="add", value=5)

    assert result[0]["price"] == 15
    assert result[1]["price"] == 25


def test_apply_price_stress_multiply():
    price_data = [
        {"timestamp": "2026-01-01 00:00:00", "price": 10},
        {"timestamp": "2026-01-01 01:00:00", "price": 20},
    ]

    result = apply_price_stress(price_data, mode="multiply", value=2)

    assert result[0]["price"] == 20
    assert result[1]["price"] == 40


def test_apply_price_stress_floor():
    price_data = [
        {"timestamp": "2026-01-01 00:00:00", "price": -10},
        {"timestamp": "2026-01-01 01:00:00", "price": 20},
    ]

    result = apply_price_stress(price_data, mode="floor", value=0)

    assert result[0]["price"] == 0
    assert result[1]["price"] == 20


def test_apply_price_stress_cap():
    price_data = [
        {"timestamp": "2026-01-01 00:00:00", "price": 50},
        {"timestamp": "2026-01-01 01:00:00", "price": 120},
    ]

    result = apply_price_stress(price_data, mode="cap", value=80)

    assert result[0]["price"] == 50
    assert result[1]["price"] == 80


def test_apply_price_stress_unsupported_mode():
    price_data = [
        {"timestamp": "2026-01-01 00:00:00", "price": 10},
    ]

    with pytest.raises(ValueError):
        apply_price_stress(price_data, mode="bad_mode", value=1)


def test_run_price_stress_tests_returns_results():
    price_data = [
        {"timestamp": "2026-01-01 00:00:00", "price": 35},
        {"timestamp": "2026-01-01 01:00:00", "price": 10},
        {"timestamp": "2026-01-01 02:00:00", "price": -8},
        {"timestamp": "2026-01-01 03:00:00", "price": 95},
        {"timestamp": "2026-01-01 04:00:00", "price": 130},
    ]

    results = run_price_stress_tests(price_data)

    assert len(results) > 0
    assert "scenario_name" in results[0]
    assert "investor_case" in results[0]
    assert "stress_category" in results[0]
    assert "total_pnl_eur" in results[0]

    scenario_names = {row["scenario_name"] for row in results}

    assert "Base case" in scenario_names
    assert "Low-price downside" in scenario_names
    assert "High-volatility upside" in scenario_names
    assert "Dispatch underperformance" in scenario_names
    assert "Battery degradation / availability reduction" in scenario_names


def test_run_price_stress_tests_adds_solar_asset_downside_case():
    price_data = [
        {"timestamp": "2026-01-01 00:00:00", "price": 35},
        {"timestamp": "2026-01-01 01:00:00", "price": 10},
        {"timestamp": "2026-01-01 02:00:00", "price": 95},
    ]

    results = run_price_stress_tests(
        price_data,
        asset={"asset_type": "solar_colocated_battery"},
    )
    scenario_names = {row["scenario_name"] for row in results}

    assert "Solar curtailment/export-limit stress" in scenario_names


def test_run_price_stress_tests_adds_industrial_asset_downside_case():
    price_data = [
        {"timestamp": "2026-01-01 00:00:00", "price": 35},
        {"timestamp": "2026-01-01 01:00:00", "price": 10},
        {"timestamp": "2026-01-01 02:00:00", "price": 95},
    ]

    results = run_price_stress_tests(
        price_data,
        asset={"asset_type": "industrial_behind_the_meter_battery"},
    )
    scenario_names = {row["scenario_name"] for row in results}

    assert "Industrial site-load stress" in scenario_names


