from backend.assets.asset_loader import get_asset
from backend.execution.pretrade_proposal import build_asset_execution_context
from backend.revenue.revenue_stack_runner import build_asset_value_context


def test_solar_revenue_context_explains_renewable_origin_value():
    asset = get_asset("demo_solar_battery")

    context = build_asset_value_context(
        asset=asset,
        product_id="day_ahead_arbitrage",
        revenue_result={
            "details": {
                "summary": {
                    "renewable_charge_mwh": 2.82,
                    "renewable_charge_share": 1.0,
                }
            }
        },
    )

    assert context["asset_story"] == "solar_colocated_revenue"
    assert context["mock_metric"]["label"] == "Renewable-origin charge"
    assert context["mock_metric"]["value"] == 2.82
    assert "renewable-origin" in context["value_driver"]


def test_industrial_revenue_context_explains_peak_shaving_value():
    asset = get_asset("demo_industrial_btm")

    context = build_asset_value_context(
        asset=asset,
        product_id="day_ahead_arbitrage",
        revenue_result={
            "details": {
                "summary": {
                    "peak_shaved_mwh": 2.3,
                }
            }
        },
    )

    assert context["asset_story"] == "industrial_btm_revenue"
    assert context["mock_metric"]["label"] == "Peak shaved"
    assert context["mock_metric"]["value"] == 2.3
    assert "site load" in context["value_driver"]


def test_grid_execution_context_explains_merchant_dispatch_orders():
    asset = get_asset("default_site")

    context = build_asset_execution_context(
        asset=asset,
        summary={"throughput_mwh": 9.75},
        dispatch_rows=[],
    )

    assert context["execution_story"] == "grid_scale_merchant_execution"
    assert context["mock_metric"]["label"] == "Battery throughput"
    assert context["mock_metric"]["value"] == 9.75
    assert "draft market orders" in context["order_intent"]


def test_solar_execution_context_uses_renewable_charge_metric():
    asset = get_asset("demo_solar_battery")

    context = build_asset_execution_context(
        asset=asset,
        summary={
            "renewable_charge_mwh": 2.82,
            "renewable_charge_share": 1.0,
        },
        dispatch_rows=[],
    )

    assert context["execution_story"] == "solar_colocated_execution"
    assert context["mock_metric"]["label"] == "Renewable-origin charge"
    assert context["mock_metric"]["value"] == 2.82
    assert "renewable-origin" in context["investor_meaning"]


def test_industrial_execution_context_uses_peak_shaving_metric():
    asset = get_asset("demo_industrial_btm")

    context = build_asset_execution_context(
        asset=asset,
        summary={"peak_shaved_mwh": 2.3},
        dispatch_rows=[],
    )

    assert context["execution_story"] == "industrial_btm_execution"
    assert context["mock_metric"]["label"] == "Peak shaved"
    assert context["mock_metric"]["value"] == 2.3
    assert "industrial site" in context["investor_meaning"]
