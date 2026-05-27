from pathlib import Path

import pandas as pd


def load_csv(file_path):
    file_path = Path(file_path)

    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    return pd.read_csv(file_path)


def load_market_data(file_path):
    df = load_csv(file_path)

    if "timestamp" in df.columns:
        df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")

    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"], errors="coerce").dt.date

    if "price" in df.columns:
        df["price"] = pd.to_numeric(df["price"], errors="coerce")

    return df


def load_price_data_for_optimizer(file_path, price_column="price"):
    df = load_market_data(file_path)

    required_cols = ["timestamp", price_column]

    for col in required_cols:
        if col not in df.columns:
            raise ValueError(f"Missing required column: {col}")

    df = df.dropna(subset=["timestamp", price_column])
    df = df.sort_values("timestamp")

    price_data = []

    for _, row in df.iterrows():
        price_data.append(
            {
                "timestamp": str(row["timestamp"]),
                "price": float(row[price_column]),
            }
        )

    return price_data


def save_dataframe(df, file_path):
    file_path = Path(file_path)
    file_path.parent.mkdir(parents=True, exist_ok=True)

    df.to_csv(file_path, index=False)

    return file_path