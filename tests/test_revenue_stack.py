from src.assets.asset_schema import BatteryAsset
from src.revenue.calculators.imbalance_placeholder import (
    calculate_imbalance_revenue,
)
from src.revenue.calculators.intraday_placeholder import (
    calculate_intraday_revenue,
)
from src.revenue.calculators.reserve_capacity_placeholder import (
    calculate_reserve_capacity_revenue,
)
from src.revenue.revenue_stack_runner import calculate_product_revenue


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
        commercial_config={},
        grid_connection={
            "connection_capacity_mw": 10.0,
            "max_import_mw": 10.0,
            "max_export_mw": 10.0,
        },
        regulatory=regulatory or {},
    )


def test_intraday_placeholder_requires_market_inputs():
    result = calculate_intraday_revenue(build_test_asset()).to_dict()

    assert result["product_id"] == "intraday_arbitrage"
    assert result["status"] == "assumption_required"
    assert "intraday_price_series" in result["missing_inputs"]


def test_reserve_placeholder_requires_prequalification():
    result = calculate_reserve_capacity_revenue(
        asset=build_test_asset(),
        product_id="fcr_capacity",
    ).to_dict()

    assert result["product_id"] == "fcr_capacity"
    assert result["status"] == "assumption_required"
    assert "prequalified_fcr" in result["missing_inputs"]


def test_imbalance_placeholder_uses_brp_if_available():
    result = calculate_imbalance_revenue(
        build_test_asset(
            regulatory={
                "balancing_responsible_party": "Example BRP",
            }
        )
    ).to_dict()

    assert result["product_id"] == "imbalance_avoidance"
    assert "balancing_responsible_party" not in result["missing_inputs"]


def test_unsupported_revenue_product_raises_error():
    try:
        calculate_product_revenue(
            asset=build_test_asset(),
            product_id="not_real",
        )
    except ValueError as error:
        assert "Unsupported revenue product" in str(error)
    else:
        raise AssertionError("Expected unsupported revenue product to raise ValueError")
