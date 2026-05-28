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


def test_battery_config_endpoint():
    response = client.get("/battery/config")

    assert response.status_code == 200

    data = response.json()

    assert "battery_config" in data
    assert "strategy_config" in data
    assert data["battery_config"]["capacity_mwh"] > 0


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

def test_run_latest_battery_signal_endpoint():
    response = client.post("/battery/signal/run-latest")

    assert response.status_code == 200

    data = response.json()

    assert "status" in data

    if data["status"] == "ok":
        assert "data" in data
        assert "summary" in data["data"]
        assert "dispatch" in data["data"]

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