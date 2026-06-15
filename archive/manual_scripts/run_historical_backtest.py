from backend.backtesting.historical_backtest import (
    build_monthly_backtest_summary,
    run_historical_backtest,
    save_monthly_backtest_summary,
)


def main():
    results_df = run_historical_backtest()

    monthly_summary = build_monthly_backtest_summary(results_df)

    output_file = save_monthly_backtest_summary(monthly_summary)

    print(f"Saved monthly summary to: {output_file}")


if __name__ == "__main__":
    main()


