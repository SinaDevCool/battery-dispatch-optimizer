from pathlib import Path

import pandas as pd

from backend.markets.entsoe_client import get_latest_available_price_forecast


def main():
    raw_data_dir = Path("data/raw")
    processed_data_dir = Path("data/processed")
    output_data_dir = Path("data/outputs")

    raw_data_dir.mkdir(parents=True, exist_ok=True)
    processed_data_dir.mkdir(parents=True, exist_ok=True)
    output_data_dir.mkdir(parents=True, exist_ok=True)

    output_file = processed_data_dir / "next_day_price_forecast.csv"

    print("Data folders are ready:")
    print(f"Raw data: {raw_data_dir}")
    print(f"Processed data: {processed_data_dir}")
    print(f"Outputs: {output_data_dir}")

    print("\nDownloading ENTSO-E next-day day-ahead prices...")

    result = get_latest_available_price_forecast()
    rows = result["rows"]
    target_date = result["target_date"]

    if not rows:
        print("No ENTSO-E data returned for tomorrow, today, or yesterday.")
        return

    print(f"Using ENTSO-E prices for: {target_date}")

    df = pd.DataFrame(rows)
    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    df["forecast_price"] = pd.to_numeric(df["forecast_price"], errors="coerce")

    df = df.dropna(subset=["timestamp", "forecast_price"])
    df = df.drop_duplicates(subset=["timestamp"])
    df = df.sort_values("timestamp")

    df.to_csv(output_file, index=False)

    print("\nSaved next-day forecast:")
    print(output_file)

    print("\nRows:", len(df))
    print("From:", df["timestamp"].min())
    print("To:", df["timestamp"].max())

    print("\nPreview:")
    print(df.head())
    print(df.tail())
    

if __name__ == "__main__":
    main()


