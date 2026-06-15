from backend.assets.asset_schema import BatteryAsset
from backend.regulatory.germany_assumption_engine import (
    build_germany_regulatory_assumptions,
)


def build_asset(regulatory=None, commercial_config=None, grid_connection=None):
    return BatteryAsset(
        asset_id="test_asset",
        client_name="Test Client",
        site_name="Test Site",
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
        commercial_config=commercial_config or {},
        grid_connection=grid_connection or {},
        regulatory=regulatory or {},
    )


def test_germany_regulatory_assumptions_mark_incomplete_asset_high_risk():
    result = build_germany_regulatory_assumptions(build_asset()).to_dict()

    assert result["status"] == "high_risk"
    assert result["warning_count"] > 0
    assert any(
        warning["code"] == "mastr_registration_missing"
        for warning in result["warnings"]
    )


def test_germany_regulatory_assumptions_mark_complete_asset_ready():
    asset = build_asset(
        regulatory={
            "mastr_unit_id": "SEE123456789",
            "mastr_registered": True,
            "grid_operator": "Example Netz GmbH",
            "balancing_responsible_party": "Example BRP",
            "metering_concept": "separate_storage_metering",
            "technical_connection_rule": "VDE-AR-N 4110",
        },
        commercial_config={
            "grid_fee_import_eur_per_mwh": 1.0,
            "grid_fee_export_eur_per_mwh": 0.5,
            "network_tariff_model": "asset_specific_grid_operator_tariff",
            "construction_cost_contribution_eur_per_mw": 10000.0,
            "netting_storage_losses_only": True,
        },
        grid_connection={
            "connection_capacity_mw": 10.0,
            "max_import_mw": 10.0,
            "max_export_mw": 10.0,
        },
    )

    result = build_germany_regulatory_assumptions(asset).to_dict()

    assert result["status"] == "ready"
    assert result["warning_count"] == 0
    assert result["assumptions"]["technical_connection_rule"] == "VDE-AR-N 4110"



