from backend.assets.asset_loader import get_asset, load_assets
from backend.assets.asset_schema import BatteryAsset
from backend.services.asset_dispatch_service import (
    apply_grid_connection_limits,
    build_asset_assumption_flags,
    build_asset_signal_metadata,
    dispatch_asset,
)


def sample_asset():
    return BatteryAsset(
        asset_id="test_site",
        client_name="Test Client",
        site_name="Test Battery",
        country="Germany",
        market="Day-ahead spot",
        market_profile_id="de_lu_day_ahead",
        forecast_file="data/processed/next_day_price_forecast.csv",
        battery_config={
            "capacity_mwh": 20.0,
            "initial_soc_mwh": 10.0,
            "min_soc_mwh": 2.0,
            "max_charge_power_mw": 10.0,
            "max_discharge_power_mw": 10.0,
            "charge_efficiency": 0.95,
            "discharge_efficiency": 0.95,
        },
        strategy_config={
            "low_price_threshold": 20.0,
            "high_price_threshold": 80.0,
            "timestep_hours": 0.25,
        },
        commercial_config={
            "trading_fee_eur_per_mwh": 0.2,
            "market_access_fee_eur_per_mwh": 0.3,
            "grid_fee_import_eur_per_mwh": 0.0,
            "grid_fee_export_eur_per_mwh": 0.0,
            "tax_or_levy_eur_per_mwh": 0.0,
            "degradation_cost_eur_per_mwh_throughput": 3.0,
            "construction_cost_contribution_eur_per_mw": 0.0,
        },
        grid_connection={
            "connection_capacity_mw": 8.0,
            "max_import_mw": 7.0,
            "max_export_mw": 6.0,
        },
        regulatory={
            "mastr_registered": False,
            "metering_concept": None,
        },
    )


def test_apply_grid_connection_limits_reduces_charge_and_discharge_power():
    asset = sample_asset()

    constrained = apply_grid_connection_limits(
        asset.battery_config,
        asset.grid_connection,
    )

    assert constrained["max_charge_power_mw"] == 7.0
    assert constrained["max_discharge_power_mw"] == 6.0


def test_asset_assumption_flags_include_germany_review_items():
    flags = build_asset_assumption_flags(sample_asset())
    flag_types = [flag["type"] for flag in flags]

    assert "grid_fee_assumption_zero" in flag_types
    assert "missing_bkz_assumption" in flag_types
    assert "missing_mastr_registration_status" in flag_types
    assert "missing_metering_concept" in flag_types


def test_asset_signal_metadata_contains_grid_and_regulatory_context():
    class Result:
        asset = sample_asset()
        constrained_battery_config = {"max_charge_power_mw": 7.0}
        assumption_risk_flags = [{"type": "grid_fee_assumption_zero"}]

    metadata = build_asset_signal_metadata(Result())

    assert metadata["asset_id"] == "test_site"
    assert metadata["market_profile_id"] == "de_lu_day_ahead"
    assert metadata["grid_connection"]["max_import_mw"] == 7.0
    assert metadata["regulatory"]["mastr_registered"] is False
    assert metadata["constrained_battery_config"]["max_charge_power_mw"] == 7.0


def test_solar_colocated_asset_dispatch_tracks_renewable_charge_origin():
    asset = get_asset("demo_solar_battery")
    result = dispatch_asset(asset)
    signal_result = result.dispatch_result.signal_result
    renewable_charge_rows = [
        row
        for row in signal_result["dispatch"]
        if row.get("renewable_charge_mwh", 0) > 0
    ]

    assert signal_result["asset_physics"]["physics_model"] == "solar_colocated_battery_v1"
    assert renewable_charge_rows
    assert signal_result["summary"]["renewable_charge_mwh"] > 0
    assert 0 < signal_result["summary"]["renewable_charge_share"] <= 1
    assert all(row["grid_charge_mwh"] == 0 for row in renewable_charge_rows)


def test_industrial_btm_asset_dispatch_shaves_site_peak():
    asset = get_asset("demo_industrial_btm")
    result = dispatch_asset(asset)
    signal_result = result.dispatch_result.signal_result
    peak_shaving_rows = [
        row
        for row in signal_result["dispatch"]
        if row.get("peak_shaved_mwh", 0) > 0
    ]

    assert signal_result["asset_physics"]["physics_model"] == "industrial_btm_battery_v1"
    assert peak_shaving_rows
    assert signal_result["summary"]["peak_shaved_mwh"] > 0
    assert all(row["action"] == "discharge" for row in peak_shaving_rows)
    assert all(row["peak_excess_after_mwh"] == 0 for row in peak_shaving_rows)


def test_mock_asset_dispatch_respects_soc_envelopes():
    for asset in load_assets():
        result = dispatch_asset(asset)
        dispatch = result.dispatch_result.signal_result["dispatch"]
        min_soc_mwh = asset.battery_config["min_soc_mwh"]
        capacity_mwh = asset.battery_config["capacity_mwh"]

        assert dispatch
        for row in dispatch:
            assert min_soc_mwh <= row["soc_mwh"] <= capacity_mwh
