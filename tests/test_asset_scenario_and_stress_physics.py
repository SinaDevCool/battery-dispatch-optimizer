from backend.assets.asset_loader import get_asset
from backend.forecasts.forecast_loader import load_forecast_price_data
from backend.scenarios.scenario_runner import run_scenarios
from backend.scenarios.stress_runner import run_price_stress_tests


def test_asset_scenarios_use_selected_asset_physics():
    asset = get_asset("demo_solar_battery")
    price_data = load_forecast_price_data(asset.forecast_file)

    results = run_scenarios(
        price_data,
        strategy_config=asset.strategy_config,
        commercial_config=asset.commercial_config,
        asset=asset,
        forecast_file=asset.forecast_file,
    )

    assert len(results) == 4
    assert all("Investor Demo Solar + Battery" in row["scenario_name"] for row in results)
    assert all(row["scenario_basis"].startswith("selected_asset_") for row in results)
    assert all(row["physics_model"] == "solar_colocated_battery_v1" for row in results)
    assert any(row.get("renewable_charge_mwh", 0) > 0 for row in results)


def test_solar_stress_results_include_renewable_origin_physics():
    asset = get_asset("demo_solar_battery")
    price_data = load_forecast_price_data(asset.forecast_file)

    results = run_price_stress_tests(
        price_data=price_data,
        battery_config=asset.battery_config,
        strategy_config=asset.strategy_config,
        commercial_config=asset.commercial_config,
        asset=asset,
        forecast_file=asset.forecast_file,
    )

    assert any(row["scenario_name"] == "Solar curtailment/export-limit stress" for row in results)
    assert all(row["physics_model"] == "solar_colocated_battery_v1" for row in results)
    assert any(row.get("renewable_charge_mwh", 0) > 0 for row in results)


def test_industrial_stress_results_include_peak_shaving_physics():
    asset = get_asset("demo_industrial_btm")
    price_data = load_forecast_price_data(asset.forecast_file)

    results = run_price_stress_tests(
        price_data=price_data,
        battery_config=asset.battery_config,
        strategy_config=asset.strategy_config,
        commercial_config=asset.commercial_config,
        asset=asset,
        forecast_file=asset.forecast_file,
    )

    assert any(row["scenario_name"] == "Industrial site-load stress" for row in results)
    assert all(row["physics_model"] == "industrial_btm_battery_v1" for row in results)
    assert any(row.get("peak_shaved_mwh", 0) > 0 for row in results)
