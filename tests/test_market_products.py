from src.assets.asset_schema import BatteryAsset
from src.markets.products.product_registry import (
    build_asset_product_eligibility_list,
    get_market_product,
    list_market_products,
)


def build_test_asset(regulatory=None):
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
        commercial_config={
            "grid_fee_import_eur_per_mwh": 0.0,
            "grid_fee_export_eur_per_mwh": 0.0,
        },
        grid_connection={
            "connection_capacity_mw": 10.0,
            "max_import_mw": 10.0,
            "max_export_mw": 10.0,
        },
        regulatory=regulatory or {},
    )


def test_list_market_products_contains_germany_products():
    products = list_market_products(country="Germany")
    product_ids = [product.product_id for product in products]

    assert "day_ahead_arbitrage" in product_ids
    assert "intraday_arbitrage" in product_ids
    assert "fcr_capacity" in product_ids


def test_get_market_product_returns_day_ahead_product():
    product = get_market_product("day_ahead_arbitrage")

    assert product.product_id == "day_ahead_arbitrage"
    assert product.bidding_zone == "DE_LU"
    assert product.settlement_interval_minutes == 15


def test_asset_product_eligibility_blocks_fcr_without_prequalification():
    asset = build_test_asset()
    results = build_asset_product_eligibility_list(asset)

    fcr_result = next(
        result for result in results
        if result["product"]["product_id"] == "fcr_capacity"
    )

    assert fcr_result["eligibility_status"] == "not_eligible"
    assert any(
        reason["code"] == "prequalification_missing"
        for reason in fcr_result["blocking_reasons"]
    )


def test_asset_product_eligibility_allows_fcr_with_prequalification():
    asset = build_test_asset(
        regulatory={
            "prequalified_fcr": True,
            "balancing_responsible_party": "Example BRP",
        }
    )
    results = build_asset_product_eligibility_list(asset)

    fcr_result = next(
        result for result in results
        if result["product"]["product_id"] == "fcr_capacity"
    )

    assert fcr_result["eligibility_status"] == "eligible"
