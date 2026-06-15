import pandas as pd


def build_daily_market_features(market_df):
    required_cols = ["date", "price"]

    for col in required_cols:
        if col not in market_df.columns:
            raise ValueError(f"market_df is missing required column: {col}")

    market_df = market_df.copy()

    market_df["date"] = pd.to_datetime(
        market_df["date"],
        errors="coerce",
    )

    market_df["price"] = pd.to_numeric(
        market_df["price"],
        errors="coerce",
    )

    market_df = market_df.dropna(subset=["date", "price"])

    if "timestamp" in market_df.columns:
        market_df["timestamp"] = pd.to_datetime(
            market_df["timestamp"],
            errors="coerce",
        )
        market_df["hour"] = market_df["timestamp"].dt.hour
    else:
        market_df["hour"] = None

    daily_rows = []

    for date, day_df in market_df.groupby("date"):
        price_series = day_df["price"]

        cheapest_hour = None
        most_expensive_hour = None

        if "timestamp" in day_df.columns and day_df["timestamp"].notna().any():
            cheapest_idx = price_series.idxmin()
            expensive_idx = price_series.idxmax()

            cheapest_hour = int(day_df.loc[cheapest_idx, "timestamp"].hour)
            most_expensive_hour = int(day_df.loc[expensive_idx, "timestamp"].hour)

        daily_rows.append(
            {
                "date": date,
                "avg_price": round(float(price_series.mean()), 2),
                "min_price": round(float(price_series.min()), 2),
                "max_price": round(float(price_series.max()), 2),
                "price_spread_market": round(
                    float(price_series.max() - price_series.min()),
                    2,
                ),
                "price_volatility": round(float(price_series.std()), 2),
                "negative_price_hours": int((price_series < 0).sum()),
                "low_price_hours": int((price_series <= 20).sum()),
                "high_price_hours": int((price_series >= 80).sum()),
                "cheapest_hour": cheapest_hour,
                "most_expensive_hour": most_expensive_hour,
                "best_daily_spread": round(
                    float(price_series.max() - price_series.min()),
                    2,
                ),
            }
        )

    daily_market = pd.DataFrame(daily_rows)

    optional_columns = {
        "renewables_forecast_total": [
            ("avg_renewables_forecast", "mean"),
            ("max_renewables_forecast", "max"),
        ],
        "solar_forecast": [
            ("avg_solar_forecast", "mean"),
        ],
        "wind_forecast": [
            ("avg_wind_forecast", "mean"),
        ],
    }

    for source_column, features in optional_columns.items():
        if source_column in market_df.columns:
            optional_features = (
                market_df
                .groupby("date")[source_column]
                .agg([aggregation for _, aggregation in features])
                .reset_index()
            )

            rename_map = {
                aggregation: feature_name
                for feature_name, aggregation in features
            }

            optional_features = optional_features.rename(columns=rename_map)

            daily_market = daily_market.merge(
                optional_features,
                on="date",
                how="left",
            )

    return daily_market.round(2)


