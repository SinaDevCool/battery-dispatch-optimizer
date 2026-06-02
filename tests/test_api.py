from fastapi.testclient import TestClient

from src.api.main import app


client = TestClient(app)


def test_health_endpoint():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_status_endpoint():
    response = client.get("/status")

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "ok"
    assert "/battery/signal" in data["available_endpoints"]
    assert "/assets/{asset_id}/signal/latest" in data["available_endpoints"]
    assert "/assets/{asset_id}/regulatory/germany" in data["available_endpoints"]
    assert "/markets/products" in data["available_endpoints"]
    assert "/assets/{asset_id}/eligible-products" in data["available_endpoints"]
    assert "/assets/{asset_id}/revenue-stack/run" in data["available_endpoints"]


def test_battery_config_endpoint():
    response = client.get("/battery/config")

    assert response.status_code == 200

    data = response.json()

    assert "battery_config" in data
    assert "strategy_config" in data
    assert data["battery_config"]["capacity_mwh"] > 0


def test_battery_optimizers_endpoint():
    response = client.get("/battery/optimizers")

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "ok"
    assert data["default_optimizer"] == "rule_based_v1"
    assert "rule_based_v1" in data["available_optimizers"]
    assert "linear_v1" in data["available_optimizers"]


def test_battery_signal_endpoint():
    payload = {
        "price_data": [
            {
                "timestamp": "2026-01-01 00:00:00",
                "price": 40,
            },
            {
                "timestamp": "2026-01-01 01:00:00",
                "price": 10,
            },
            {
                "timestamp": "2026-01-01 02:00:00",
                "price": 100,
            },
        ]
    }

    response = client.post("/battery/signal", json=payload)

    assert response.status_code == 200

    data = response.json()

    assert "summary" in data
    assert "dispatch" in data
    assert len(data["dispatch"]) == 3
    assert data["summary"]["signal"] in ["ACTION", "NO_ACTION", "NO_DATA"]


def test_battery_backtest_endpoint():
    payload = {
        "price_data": [
            {
                "timestamp": "2026-01-01 00:00:00",
                "price": 40,
            },
            {
                "timestamp": "2026-01-01 01:00:00",
                "price": 10,
            },
            {
                "timestamp": "2026-01-01 02:00:00",
                "price": 100,
            },
        ]
    }

    response = client.post("/battery/backtest", json=payload)

    assert response.status_code == 200

    data = response.json()

    assert "summary" in data
    assert "dispatch" in data
    assert len(data["dispatch"]) == 3


def test_forecast_features_endpoint():
    response = client.get("/features/forecast")

    assert response.status_code == 200

    data = response.json()

    assert "status" in data


def test_battery_constraints_endpoint():
    response = client.get("/battery/constraints")

    assert response.status_code == 200

    data = response.json()

    assert "status" in data

    if data["status"] == "ok":
        assert "usable_capacity_mwh" in data
        assert "charge_duration_hours" in data
        assert "discharge_duration_hours" in data


def test_system_health_endpoint():
    response = client.get("/system/health")

    assert response.status_code == 200

    data = response.json()

    assert "status" in data
    assert "checks" in data


def test_assets_endpoint():
    response = client.get("/assets")

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "ok"
    assert data["asset_count"] >= 1
    assert "assets" in data
    assert "asset_id" in data["assets"][0]


def test_markets_endpoint():
    response = client.get("/markets")

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "ok"
    assert data["market_count"] >= 1
    assert data["markets"][0]["market_profile_id"] == "de_lu_day_ahead"


def test_germany_market_profile_endpoint():
    response = client.get("/markets/de_lu_day_ahead")

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "ok"
    assert data["market"]["bidding_zone"] == "DE_LU"
    assert data["market"]["market_time_unit_minutes"] == 15
    assert data["market"]["expected_intervals_per_day"] == 96


def test_market_products_endpoint():
    response = client.get("/markets/products")

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "ok"
    assert data["product_count"] >= 1
    assert "day_ahead_arbitrage" in [
        product["product_id"] for product in data["products"]
    ]


def test_market_product_detail_endpoint():
    response = client.get("/markets/products/day_ahead_arbitrage")

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "ok"
    assert data["product"]["product_id"] == "day_ahead_arbitrage"


def test_asset_eligible_products_endpoint():
    response = client.get("/assets/default_site/eligible-products")

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "ok"
    assert data["asset_id"] == "default_site"
    assert data["product_count"] >= 1
    assert "products" in data


def test_asset_revenue_stack_latest_endpoint():
    response = client.get("/assets/default_site/revenue-stack/latest")

    assert response.status_code == 200

    data = response.json()

    assert "status" in data
    assert data["asset_id"] == "default_site"


def test_run_asset_revenue_stack_endpoint():
    response = client.post("/assets/default_site/revenue-stack/run")

    assert response.status_code == 200

    data = response.json()

    assert "status" in data

    if data["status"] == "ok":
        assert data["asset_id"] == "default_site"
        assert "products" in data
        assert "total_estimated_revenue_eur" in data


def test_germany_regulatory_requirements_endpoint():
    response = client.get("/regulatory/germany/requirements")

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "ok"
    assert data["country"] == "Germany"
    assert len(data["requirements"]) >= 1


def test_asset_germany_regulatory_endpoint():
    response = client.get("/assets/default_site/regulatory/germany")

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "ok"
    assert data["asset_id"] == "default_site"
    assert "regulatory_assumptions" in data


def test_portfolio_latest_endpoint():
    response = client.get("/portfolio/latest")

    assert response.status_code == 200

    data = response.json()

    assert "status" in data
    assert "assets" in data


def test_asset_signal_latest_endpoint():
    response = client.get("/assets/default_site/signal/latest")

    assert response.status_code == 200

    data = response.json()

    assert "status" in data
    assert data["asset_id"] == "default_site"


def test_run_latest_battery_signal_endpoint():
    response = client.post("/battery/signal/run-latest")

    assert response.status_code == 200

    data = response.json()

    assert "status" in data

    if data["status"] == "ok":
        assert "data" in data
        assert "summary" in data["data"]
        assert "dispatch" in data["data"]
        assert "validation" in data
        assert data["validation"]["status"] in ["pass", "warning", "fail"]

def test_client_presets_endpoint():
    response = client.get("/client/presets")

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "ok"
    assert "presets" in data
    assert "grid_scale_battery" in data["presets"]


def test_apply_missing_client_preset():
    response = client.post("/client/presets/not_a_real_preset/apply")

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "not_found"
