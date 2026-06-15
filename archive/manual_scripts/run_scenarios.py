import json
from pathlib import Path

import pandas as pd

from backend.markets.data_loader import load_price_data_for_optimizer
from backend.scenarios.scenario_runner import run_scenarios


def main():
    forecast_file = Path("data/processed/next_day_price_forecast.csv")
    output_json = Path("data/outputs/scenario_results.json")
    output_csv = Path("data/outputs/scenario_results.csv")

    if not forecast_file.exists():
        print("No next-day forecast file found.")
        print(f"Expected file: {forecast_file}")
        return

    price_data = load_price_data_for_optimizer(
        forecast_file,
        price_column="forecast_price",
    )

    scenario_results = run_scenarios(price_data)

    output_json.parent.mkdir(parents=True, exist_ok=True)

    with open(output_json, "w", encoding="utf-8") as file:
        json.dump(scenario_results, file, indent=2)

    scenario_df = pd.DataFrame(scenario_results)
    scenario_df.to_csv(output_csv, index=False)

    print("Scenario Results")
    print("=" * 60)
    print(scenario_df)

    print("\nSaved:")
    print(output_json)
    print(output_csv)


if __name__ == "__main__":
    main()


