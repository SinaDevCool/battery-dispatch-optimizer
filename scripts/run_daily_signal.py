from pathlib import Path

from src.markets.data_loader import load_price_data_for_optimizer
from src.signals.signal_engine import generate_battery_signal


def main():
    forecast_file = Path("data/processed/next_day_price_forecast.csv")

    if not forecast_file.exists():
        print("No next-day forecast file found.")
        print(f"Expected file: {forecast_file}")
        print("Create a CSV with columns: timestamp, forecast_price")
        return

    price_data = load_price_data_for_optimizer(
        forecast_file,
        price_column="forecast_price",
    )

    result = generate_battery_signal(price_data)

    print("Battery Signal Summary")
    print("=" * 60)

    summary = result["summary"]

    print(f"Signal: {summary['signal']}")
    print(f"Opportunity level: {summary['opportunity_level']}")
    print(f"Total PnL: {summary['total_pnl_eur']} EUR")
    print(f"Profit per MW-day: {summary['profit_per_mw_day']} EUR/MW-day")
    print(f"Charge hours: {summary['charge_hours']}")
    print(f"Discharge hours: {summary['discharge_hours']}")
    print(f"First charge: {summary['first_charge_timestamp']}")
    print(f"First discharge: {summary['first_discharge_timestamp']}")

    print("\nDispatch")
    print("=" * 60)

    for row in result["dispatch"]:
        print(
            f"{row['timestamp']} | "
            f"price={row['price']:>7.2f} | "
            f"action={row['action']:<9} | "
            f"SOC={row['soc_mwh']:>6.2f} | "
            f"PnL={row['pnl_eur']:>8.2f}"
        )


if __name__ == "__main__":
    main()