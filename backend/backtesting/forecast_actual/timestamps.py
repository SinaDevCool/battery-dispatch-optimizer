import pandas as pd


def normalize_market_timestamps(values):
    parsed = pd.to_datetime(values, errors="coerce")

    def normalize_value(value):
        if pd.isna(value):
            return pd.NaT

        timestamp = pd.Timestamp(value)

        if timestamp.tzinfo is not None:
            return timestamp.tz_localize(None)

        return timestamp

    return parsed.map(normalize_value)



