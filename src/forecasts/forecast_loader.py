from pathlib import Path

import pandas as pd


DEFAULT_FORECAST_FILE = Path("data/processed/next_day_price_forecast.csv")


def normalize_forecast_dataframe(
    forecast_df,
    price_column="forecast_price",
):
    if "timestamp" not in forecast_df.columns:
        raise ValueError("Forecast file must contain a timestamp column.")

    if price_column not in forecast_df.columns:
        if "price" in forecast_df.columns:
            price_column = "price"
        else:
            raise ValueError(
                f"Forecast file must contain {price_column} or price column."
            )

    df = forecast_df.copy()

    df["timestamp"] = pd.to_datetime(
        df["timestamp"],
        errors="coerce",
    )

    df[price_column] = pd.to_numeric(
        df[price_column],
        errors="coerce",
    )

    df = df.dropna(subset=["timestamp", price_column])
    df = df.drop_duplicates(subset=["timestamp"])
    df = df.sort_values("timestamp")
    df = df.reset_index(drop=True)

    return df, price_column


def forecast_dataframe_to_price_data(
    forecast_df,
    price_column="forecast_price",
):
    normalized_df, resolved_price_column = normalize_forecast_dataframe(
        forecast_df=forecast_df,
        price_column=price_column,
    )

    price_data = []

    for _, row in normalized_df.iterrows():
        price_data.append(
            {
                "timestamp": str(row["timestamp"]),
                "price": float(row[resolved_price_column]),
            }
        )

    return price_data


def load_forecast_dataframe(
    forecast_file=DEFAULT_FORECAST_FILE,
    price_column="forecast_price",
):
    forecast_file = Path(forecast_file)

    if not forecast_file.exists():
        raise FileNotFoundError(
            f"Forecast file not found: {forecast_file}. "
            "Create this CSV first with timestamp and forecast_price columns."
        )

    forecast_df = pd.read_csv(forecast_file)

    normalized_df, _ = normalize_forecast_dataframe(
        forecast_df=forecast_df,
        price_column=price_column,
    )

    return normalized_df


def load_forecast_price_data(
    forecast_file=DEFAULT_FORECAST_FILE,
    price_column="forecast_price",
):
    forecast_file = Path(forecast_file)

    if not forecast_file.exists():
        raise FileNotFoundError(
            f"Forecast file not found: {forecast_file}. "
            "Create this CSV first with timestamp and forecast_price columns."
        )

    forecast_df = pd.read_csv(forecast_file)

    return forecast_dataframe_to_price_data(
        forecast_df=forecast_df,
        price_column=price_column,
    )


def load_next_day_forecast(
    forecast_file=DEFAULT_FORECAST_FILE,
    price_column="forecast_price",
):
    return load_forecast_price_data(
        forecast_file=forecast_file,
        price_column=price_column,
    )