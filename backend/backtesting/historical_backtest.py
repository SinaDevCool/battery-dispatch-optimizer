from pathlib import Path

import pandas as pd

from backend.backtesting.backtester import run_backtest
from backend.markets.data_loader import load_price_data_for_optimizer


def run_historical_backtest(
    market_file="data/processed/market_price_renewables_merged.csv",
    output_file="data/outputs/historical_battery_backtest_results.csv",
):
    market_file = Path(market_file)
    output_file = Path(output_file)

    if not market_file.exists():
        raise FileNotFoundError(f"Historical market file not found: {market_file}")

    price_data = load_price_data_for_optimizer(
        market_file,
        price_column="price",
    )

    results = run_backtest(price_data=price_data)

    results_df = pd.DataFrame(results)

    output_file.parent.mkdir(parents=True, exist_ok=True)
    results_df.to_csv(output_file, index=False)

    return results_df


def build_monthly_backtest_summary(results_df):
    if results_df.empty:
        return pd.DataFrame()

    df = results_df.copy()

    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    df["month"] = df["timestamp"].dt.to_period("M").astype(str)

    monthly_summary = (
        df
        .groupby("month")
        .agg(
            hours=("price", "count"),
            charge_hours=("action", lambda x: (x == "charge").sum()),
            discharge_hours=("action", lambda x: (x == "discharge").sum()),
            idle_hours=("action", lambda x: (x == "idle").sum()),
            total_pnl_eur=("pnl_eur", "sum"),
            avg_price=("price", "mean"),
            min_price=("price", "min"),
            max_price=("price", "max"),
            min_soc_mwh=("soc_mwh", "min"),
            max_soc_mwh=("soc_mwh", "max"),
        )
        .reset_index()
    )

    return monthly_summary.round(2)


def save_monthly_backtest_summary(
    monthly_summary,
    output_file="data/outputs/historical_battery_monthly_summary.csv",
):
    output_file = Path(output_file)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    monthly_summary.to_csv(output_file, index=False)

    return output_file


