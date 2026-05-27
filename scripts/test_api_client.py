import requests


API_BASE_URL = "http://127.0.0.1:8000"


def test_health():
    response = requests.get(f"{API_BASE_URL}/health")
    print("Health:")
    print(response.json())


def test_battery_config():
    response = requests.get(f"{API_BASE_URL}/battery/config")
    print("\nBattery config:")
    print(response.json())


def test_battery_signal():
    payload = {
        "price_data": [
            {"timestamp": "2026-01-01 00:00:00", "price": 45},
            {"timestamp": "2026-01-01 01:00:00", "price": 15},
            {"timestamp": "2026-01-01 02:00:00", "price": -5},
            {"timestamp": "2026-01-01 03:00:00", "price": 90},
            {"timestamp": "2026-01-01 04:00:00", "price": 120},
        ]
    }

    response = requests.post(f"{API_BASE_URL}/battery/signal", json=payload)

    print("\nBattery signal:")
    print(response.json())


def test_battery_backtest():
    payload = {
        "price_data": [
            {"timestamp": "2026-01-01 00:00:00", "price": 45},
            {"timestamp": "2026-01-01 01:00:00", "price": 15},
            {"timestamp": "2026-01-01 02:00:00", "price": -5},
            {"timestamp": "2026-01-01 03:00:00", "price": 90},
            {"timestamp": "2026-01-01 04:00:00", "price": 120},
        ]
    }

    response = requests.post(f"{API_BASE_URL}/battery/backtest", json=payload)

    print("\nBattery backtest:")
    print(response.json())


def main():
    test_health()
    test_battery_config()
    test_battery_signal()
    test_battery_backtest()


if __name__ == "__main__":
    main()