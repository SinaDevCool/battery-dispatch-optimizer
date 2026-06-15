from backend.ancillary.germany_ancillary_services import assess_germany_ancillary_eligibility
from backend.assets.asset_schema import BatteryAsset
from backend.energy_accounting.energy_origin_ledger import build_energy_origin_ledger
from backend.grid_fees.germany_grid_fee_model import build_germany_grid_fee_sensitivity
from backend.hedging.revenue_contracts import build_hedged_revenue_view
from backend.regulatory.eeg_compliance_checker import check_eeg_compliance
from backend.regulatory.storage_classification import classify_storage_asset


def build_test_asset(regulatory=None):
    return BatteryAsset(
        asset_id="test_asset",
        client_name="Test Client",
        site_name="Test Battery",
        country="Germany",
        market="Day-ahead spot",
        battery_config={
            "capacity_mwh": 20.0,
            "max_charge_power_mw": 10.0,
            "max_discharge_power_mw": 10.0,
        },
        strategy_config={},
        commercial_config={
            "grid_fee_import_eur_per_mwh": 0.0,
            "grid_fee_export_eur_per_mwh": 0.0,
        },
        market_profile_id="de_lu_day_ahead",
        grid_connection={
            "connection_capacity_mw": 10.0,
            "max_import_mw": 10.0,
            "max_export_mw": 10.0,
        },
        regulatory=regulatory or {},
    )


def test_storage_classification_flags_mixed_eeg_risk():
    asset = build_test_asset(
        {
            "is_colocated": True,
            "charges_from_grid": True,
            "charges_from_renewables": True,
            "uses_eeg_support": True,
            "exports_stored_renewable_power": True,
        }
    )

    result = classify_storage_asset(asset)

    assert result["storage_mode"] == "mixed_colocated"
    assert result["eeg_support_risk"] == "high"
    assert result["status"] == "high_risk"


def test_eeg_compliance_returns_actions():
    asset = build_test_asset(
        {
            "is_colocated": True,
            "charges_from_grid": True,
            "charges_from_renewables": True,
            "uses_eeg_support": True,
        }
    )

    result = check_eeg_compliance(asset)

    assert result["asset_id"] == "test_asset"
    assert result["recommended_actions"]


def test_grid_fee_sensitivity_uses_dispatch_import_export():
    asset = build_test_asset()
    dispatch_rows = [
        {"action": "charge", "grid_energy_mwh": 10.0},
        {"action": "discharge", "grid_energy_mwh": 9.0},
    ]

    result = build_germany_grid_fee_sensitivity(asset, dispatch_rows)

    assert result["status"] == "ok"
    assert result["import_mwh"] == 10.0
    assert result["export_mwh"] == 9.0
    assert len(result["scenarios"]) >= 4


def test_energy_origin_ledger_for_pure_green_storage():
    asset = build_test_asset(
        {
            "is_colocated": True,
            "charges_from_grid": False,
            "charges_from_renewables": True,
            "storage_mode": "pure_green_colocated",
            "metering_concept": "separate_metering",
        }
    )
    dispatch_rows = [
        {"timestamp": "2026-01-01 00:00:00", "action": "charge", "battery_energy_mwh": 5.0},
        {"timestamp": "2026-01-01 01:00:00", "action": "discharge", "battery_energy_mwh": 5.0},
    ]

    result = build_energy_origin_ledger(asset, dispatch_rows)

    assert result["summary"]["charged_from_renewables_mwh"] == 5.0
    assert result["summary"]["discharged_green_mwh"] == 5.0


def test_ancillary_eligibility_returns_products():
    asset = build_test_asset(
        {
            "balancing_service_provider": "Demo BSP",
            "ancillary_prequalification_status": "approved",
            "remote_control_ready": True,
            "telemetry_ready": True,
        }
    )

    result = assess_germany_ancillary_eligibility(asset)

    assert result["status"] == "ok"
    assert result["eligible_product_count"] >= 1
    assert "products" in result


def test_hedged_revenue_view_returns_best_contract():
    asset = build_test_asset()

    result = build_hedged_revenue_view(asset, merchant_revenue_eur=100000.0)

    assert result["status"] == "ok"
    assert result["best_contract"] is not None
    assert len(result["contracts"]) >= 1



