from pathlib import Path

import pandas as pd

from src.backtesting.backtester import run_backtest
from src.markets.data_loader import load_price_data_for_optimizer


def main():
    market_file = Path("data/processed/market_price_renewables_merged.csv")

    if not market_file.exists():
        print("Historical market file not found.")
        print(f"Expected file: {market_file}")
        print("Copy your Colab output CSV into data/processed first.")
        return

    print(f"Loading historical market data from: {market_file}")

    price_data = load_price_data_for_optimizer(
        market_file,
        price_column="price",
    )

    print(f"Loaded price rows: {len(price_data)}")

    results = run_backtest(price_data=price_data)

    results_df = pd.DataFrame(results)

    output_file = Path("data/outputs/historical_battery_backtest_results.csv")
    output_file.parent.mkdir(parents=True, exist_ok=True)

    results_df.to_csv(output_file, index=False)

    print(f"Saved historical backtest results to: {output_file}")


if __name__ == "__main__":
    main()