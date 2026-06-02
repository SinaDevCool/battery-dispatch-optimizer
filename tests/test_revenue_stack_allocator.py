from src.assets.asset_schema import BatteryAsset
from src.revenue.revenue_stack_allocator import allocate_revenue_stack


def build_test_asset():
    return BatteryAsset(
        asset_id="test_asset",
        client_name="Test Client",
        site_name="Test Site",
        country="Germany",
        market="Day-ahead spot",
        battery_config={
            "capacity_mwh": 20.0,
            "max_charge_power_mw": 10.0,
            "max_discharge_power_mw": 10.0,
        },
        strategy_config={},
        commercial_config={},
        grid_connection={
            "connection_capacity_mw": 10.0,
            "max_import_mw": 10.0,
            "max_export_mw": 10.0,
        },
    )


def test_allocate_revenue_stack_respects_power_and_energy_constraints():
    asset = build_test_asset()
    revenue_stack = {
        "status": "ok",
        "products": [
            {
                "product_id": "day_ahead_arbitrage",
                "status": "ok",
                "eligible": True,
                "estimated_revenue_eur": 1000.0,
            },
            {
                "product_id": "fcr_capacity",
                "status": "ok",
                "eligible": True,
                "estimated_revenue_eur": 800.0,
            },
            {
                "product_id": "afrr_capacity",
                "status": "assumption_required",
                "eligible": True,
                "estimated_revenue_eur": None,
                "missing_inputs": ["afrr_capacity_price_eur_per_mw_h"],
            },
        ],
    }

    result = allocate_revenue_stack(asset, revenue_stack)

    assert result["status"] == "ok"
    assert result["allocation_count"] >= 1
    assert result["constraints"]["max_power_mw"] == 10.0
    assert result["constraints"]["remaining_power_mw"] >= 0.0
    assert result["constraints"]["remaining_energy_mwh"] >= 0.0
    assert result["total_expected_revenue_eur"] > 0.0
    assert any(
        product["product_id"] == "afrr_capacity"
        and product["exclusion_reason"] == "Product has no numeric revenue estimate."
        for product in result["excluded_products"]
    )
