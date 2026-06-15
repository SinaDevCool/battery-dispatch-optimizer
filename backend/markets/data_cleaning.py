import pandas as pd


def prepare_spot_prices(df):
    df = df.copy()

    date_col = None
    time_col = None
    price_col = None

    for col in df.columns:
        col_lower = col.lower().strip()

        if date_col is None and col_lower in ["datum", "date"]:
            date_col = col

        if time_col is None and col_lower in ["von", "from", "beginn", "start"]:
            time_col = col

        if price_col is None and (
            "spot" in col_lower
            or "preis" in col_lower
            or col_lower in ["price", "wert"]
        ):
            if "endpoint" not in col_lower and "request" not in col_lower:
                price_col = col

    if date_col is None:
        raise ValueError("Could not find spot price date column")

    if time_col is None:
        raise ValueError("Could not find spot price time column, e.g. 'von'")

    if price_col is None:
        numeric_cols = df.select_dtypes(include="number").columns.tolist()
        if numeric_cols:
            price_col = numeric_cols[0]
        else:
            raise ValueError("Could not find spot price column")

    date_str = df[date_col].astype(str).str.strip()
    time_str = df[time_col].astype(str).str.strip()

    time_str = (
        time_str
        .str.replace("UTC", "", regex=False)
        .str.strip()
    )

    time_str = time_str.str.replace(r"^(\d):", r"0\1:", regex=True)

    is_24 = time_str.str.startswith("24:")
    time_str_clean = time_str.mask(is_24, "00:00")

    timestamp = pd.to_datetime(
        date_str + " " + time_str_clean,
        errors="coerce",
        dayfirst=True,
    )

    timestamp = timestamp + pd.to_timedelta(is_24.astype(int), unit="D")

    df["timestamp"] = timestamp
    df["price"] = pd.to_numeric(df[price_col], errors="coerce")

    df = df.dropna(subset=["timestamp", "price"])

    df["timestamp"] = df["timestamp"].dt.floor("h")
    df["date"] = df["timestamp"].dt.date
    df["hour"] = df["timestamp"].dt.hour
    df["month"] = df["timestamp"].dt.to_period("M").astype(str)
    df["is_negative_price"] = df["price"] < 0

    return df[
        [
            "timestamp",
            "date",
            "hour",
            "month",
            "price",
            "is_negative_price",
        ]
    ]


def prepare_generation_forecast(df, label):
    df = df.copy()

    date_col = None
    time_col = None

    for col in df.columns:
        col_lower = col.lower().strip()

        if date_col is None and col_lower in ["datum", "date"]:
            date_col = col

        if time_col is None and col_lower in ["von", "from", "beginn", "start"]:
            time_col = col

    if date_col is None:
        raise ValueError(f"Could not find date column for {label}")

    if time_col is None:
        raise ValueError(f"Could not find time column for {label}")

    tso_cols = [
        col for col in df.columns
        if any(tso in col.lower() for tso in ["50hertz", "amprion", "tennet", "transnet"])
    ]

    if not tso_cols:
        raise ValueError(f"Could not find TSO MW columns for {label}")

    date_str = df[date_col].astype(str).str.strip()
    time_str = df[time_col].astype(str).str.strip()

    time_str = (
        time_str
        .str.replace("UTC", "", regex=False)
        .str.strip()
    )

    time_str = time_str.str.replace(r"^(\d):", r"0\1:", regex=True)

    is_24 = time_str.str.startswith("24:")
    time_str_clean = time_str.mask(is_24, "00:00")

    timestamp = pd.to_datetime(
        date_str + " " + time_str_clean,
        errors="coerce",
    )

    timestamp = timestamp + pd.to_timedelta(is_24.astype(int), unit="D")

    df["timestamp"] = timestamp

    for col in tso_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")
        df.loc[df[col] < 0, col] = pd.NA

    df[label] = df[tso_cols].sum(axis=1, min_count=1)

    df = df.dropna(subset=["timestamp", label])
    df["timestamp"] = df["timestamp"].dt.floor("h")

    hourly_df = (
        df
        .groupby("timestamp", as_index=False)[label]
        .mean()
    )

    return hourly_df[["timestamp", label]]


