import pandas as pd


def build_negative_price_features(price_df, price_column="price"):
    required_cols = ["timestamp", price_column]

    for col in required_cols:
        if col not in price_df.columns:
            raise ValueError(f"price_df is missing required column: {col}")

    df = price_df.copy()

    df["timestamp"] = pd.to_datetime(
        df["timestamp"],
        errors="coerce",
    )

    df[price_column] = pd.to_numeric(
        df[price_column],
        errors="coerce",
    )

    df = df.dropna(subset=["timestamp", price_column])
    df = df.sort_values("timestamp")

    negative_df = df[df[price_column] < 0].copy()

    if negative_df.empty:
        return {
            "negative_price_hours": 0,
            "min_negative_price": None,
            "avg_negative_price": None,
            "first_negative_timestamp": None,
            "last_negative_timestamp": None,
            "longest_negative_event_hours": 0,
        }

    negative_df["time_gap_hours"] = (
        negative_df["timestamp"].diff().dt.total_seconds() / 3600
    )

    negative_df["event_id"] = (
        negative_df["time_gap_hours"].isna()
        | (negative_df["time_gap_hours"] > 1.5)
    ).cumsum()

    event_lengths = negative_df.groupby("event_id").size()

    return {
        "negative_price_hours": int(len(negative_df)),
        "min_negative_price": round(float(negative_df[price_column].min()), 2),
        "avg_negative_price": round(float(negative_df[price_column].mean()), 2),
        "first_negative_timestamp": str(negative_df["timestamp"].iloc[0]),
        "last_negative_timestamp": str(negative_df["timestamp"].iloc[-1]),
        "longest_negative_event_hours": int(event_lengths.max()),
    }


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

    monthly_summary["price_spread"] = (
        monthly_summary["max_price"] - monthly_summary["min_price"]
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


