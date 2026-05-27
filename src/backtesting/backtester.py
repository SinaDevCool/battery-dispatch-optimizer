from src.config.battery_config import DEFAULT_BATTERY_CONFIG, DEFAULT_STRATEGY_CONFIG
from src.optimizer.battery_optimizer import BatteryOptimizer


def run_backtest(price_data=None):
    if price_data is None:
        price_data = [
            {"timestamp": "2026-01-01 00:00:00", "price": 45.0},
            {"timestamp": "2026-01-01 01:00:00", "price": 35.0},
            {"timestamp": "2026-01-01 02:00:00", "price": 15.0},
            {"timestamp": "2026-01-01 03:00:00", "price": -5.0},
            {"timestamp": "2026-01-01 04:00:00", "price": 20.0},
            {"timestamp": "2026-01-01 05:00:00", "price": 60.0},
            {"timestamp": "2026-01-01 06:00:00", "price": 95.0},
            {"timestamp": "2026-01-01 07:00:00", "price": 120.0},
            {"timestamp": "2026-01-01 08:00:00", "price": 80.0},
            {"timestamp": "2026-01-01 09:00:00", "price": 40.0},
        ]

    battery = BatteryOptimizer(**DEFAULT_BATTERY_CONFIG)

    results = battery.optimize(
        price_data=price_data,
        **DEFAULT_STRATEGY_CONFIG,
    )

    print("Battery Backtest Results")
    print("=" * 100)

    for row in results:
        print(
            f"{row['timestamp']} | "
            f"price={row['price']:>7.2f} | "
            f"action={row['action']:<9} | "
            f"SOC={row['soc_mwh']:>6.2f} MWh | "
            f"energy={row['grid_energy_mwh']:>6.2f} MWh | "
            f"PnL={row['pnl_eur']:>8.2f} EUR | "
            f"Total PnL={row['total_pnl_eur']:>8.2f} EUR"
        )

    total_pnl = results[-1]["total_pnl_eur"] if results else 0.0

    print("=" * 100)
    print(f"Total PnL: {total_pnl:.2f} EUR")

    return results


if __name__ == "__main__":
    run_backtest()