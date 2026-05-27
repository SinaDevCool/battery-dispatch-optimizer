import pandas as pd


def build_negative_price_events(spot_df):
    if "is_negative_price" not in spot_df.columns:
        raise ValueError("spot_df must contain is_negative_price column")

    negative_events = spot_df[spot_df["is_negative_price"]].copy()
    negative_events = negative_events.sort_values("timestamp").reset_index(drop=True)

    return negative_events


def build_negative_price_daily_summary(spot_df):
    required_cols = ["date", "price", "is_negative_price"]

    for col in required_cols:
        if col not in spot_df.columns:
            raise ValueError(f"spot_df is missing required column: {col}")

    daily_summary = (
        spot_df
        .groupby("date")
        .agg(
            total_hours=("price", "count"),
            negative_price_hours=("is_negative_price", "sum"),
            avg_price=("price", "mean"),
            min_price=("price", "min"),
            max_price=("price", "max"),
        )
        .reset_index()
    )

    daily_summary["negative_price_share_percent"] = (
        daily_summary["negative_price_hours"] / daily_summary["total_hours"] * 100
    )

    daily_summary["price_spread"] = (
        daily_summary["max_price"] - daily_summary["min_price"]
    )

    return daily_summary.round(2)


def build_negative_price_monthly_summary(spot_df):
    required_cols = ["month", "price", "is_negative_price"]

    for col in required_cols:
        if col not in spot_df.columns:
            raise ValueError(f"spot_df is missing required column: {col}")

    monthly_summary = (
        spot_df
        .groupby("month")
        .agg(
            total_hours=("price", "count"),
            negative_price_hours=("is_negative_price", "sum"),
            avg_price=("price", "mean"),
            min_price=("price", "min"),
            max_price=("price", "max"),
        )
        .reset_index()
    )

    monthly_summary["negative_price_share_percent"] = (
        monthly_summary["negative_price_hours"] / monthly_summary["total_hours"] * 100
    )

    return monthly_summary.round(2)


def get_worst_price_hours(spot_df, limit=20):
    if "price" not in spot_df.columns:
        raise ValueError("spot_df must contain price column")

    return (
        spot_df
        .sort_values("price")
        .head(limit)
        .reset_index(drop=True)
    )


def build_negative_price_heatmap_data(spot_df):
    required_cols = ["month", "hour", "is_negative_price"]

    for col in required_cols:
        if col not in spot_df.columns:
            raise ValueError(f"spot_df is missing required column: {col}")

    heatmap_data = (
        spot_df
        .groupby(["month", "hour"])
        .agg(
            negative_price_hours=("is_negative_price", "sum")
        )
        .reset_index()
    )

    return heatmap_data