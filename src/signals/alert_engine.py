import pandas as pd


def build_daily_market_features(market_df):
    required_cols = ["date", "price"]

    for col in required_cols:
        if col not in market_df.columns:
            raise ValueError(f"market_df is missing required column: {col}")

    market_df = market_df.copy()
    market_df["price"] = pd.to_numeric(market_df["price"], errors="coerce")
    market_df = market_df.dropna(subset=["date", "price"])

    agg_map = {
        "avg_price": ("price", "mean"),
        "min_price": ("price", "min"),
        "max_price": ("price", "max"),
        "price_spread_market": ("price", lambda x: x.max() - x.min()),
    }

    if "renewables_forecast_total" in market_df.columns:
        agg_map["avg_renewables_forecast"] = ("renewables_forecast_total", "mean")
        agg_map["max_renewables_forecast"] = ("renewables_forecast_total", "max")

    if "solar_forecast" in market_df.columns:
        agg_map["avg_solar_forecast"] = ("solar_forecast", "mean")

    if "wind_forecast" in market_df.columns:
        agg_map["avg_wind_forecast"] = ("wind_forecast", "mean")

    daily_market = (
        market_df
        .groupby("date")
        .agg(**agg_map)
        .reset_index()
    )

    return daily_market.round(2)


def build_market_summary(market_df):
    required_cols = ["price"]

    for col in required_cols:
        if col not in market_df.columns:
            raise ValueError(f"market_df is missing required column: {col}")

    summary = {
        "rows": len(market_df),
        "avg_price": round(market_df["price"].mean(), 2),
        "min_price": round(market_df["price"].min(), 2),
        "max_price": round(market_df["price"].max(), 2),
        "price_spread": round(market_df["price"].max() - market_df["price"].min(), 2),
    }

    if "is_negative_price" in market_df.columns:
        summary["negative_price_hours"] = int(market_df["is_negative_price"].sum())
        summary["negative_price_share_percent"] = round(
            market_df["is_negative_price"].mean() * 100,
            2,
        )

    if "timestamp" in market_df.columns:
        summary["start_timestamp"] = market_df["timestamp"].min()
        summary["end_timestamp"] = market_df["timestamp"].max()

    return summary


def add_forecast_price_column(market_df):
    market_df = market_df.copy()

    if "price" not in market_df.columns:
        raise ValueError("market_df must contain price column")

    # Historical backtest only:
    # We use actual historical price as perfect-foresight forecast.
    # Later replace this with real price forecasts from ENTSO-E, PRIO/Prior model, etc.
    market_df["forecast_price"] = market_df["price"]

    return market_df