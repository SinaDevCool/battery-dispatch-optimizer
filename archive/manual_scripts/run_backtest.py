from pathlib import Path

from backend.backtesting.backtester import run_backtest
from backend.markets.data_loader import load_price_data_for_optimizer


def main():
    market_file = Path("data/processed/market_price_renewables_merged.csv")

    if market_file.exists():
        print(f"Loading market data from: {market_file}")
        price_data = load_price_data_for_optimizer(
            market_file,
            price_column="price",
        )
        run_backtest(price_data=price_data)
    else:
        print("No processed market file found.")
        print("Running demo backtest with sample prices.")
        run_backtest()


if __name__ == "__main__":
    main()


