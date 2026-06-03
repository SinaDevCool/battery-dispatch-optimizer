import json
from datetime import datetime

import pandas as pd

from src.config.paths import DATABASE_FILE
from src.db.database import get_connection, initialize_database
from src.db.models import row_to_dict


def save_forecast_snapshot(forecast_file, forecast_df, db_file=DATABASE_FILE):
    initialize_database(db_file=db_file)

    df = forecast_df.copy()
    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    df["forecast_price"] = pd.to_numeric(df["forecast_price"], errors="coerce")
    valid_df = df.dropna(subset=["timestamp", "forecast_price"])

    target_date = None

    if not valid_df.empty:
        target_date = str(valid_df["timestamp"].dt.date.iloc[0])

    with get_connection(db_file=db_file) as connection:
        cursor = connection.execute(
            """
            INSERT INTO forecast_snapshots (
                forecast_file,
                forecast_provider,
                forecast_model,
                target_date,
                row_count,
                min_price,
                max_price,
                average_price,
                payload_json,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                str(forecast_file),
                first_non_empty(df, "forecast_provider"),
                first_non_empty(df, "forecast_model"),
                target_date,
                len(df),
                safe_float(valid_df["forecast_price"].min()) if not valid_df.empty else None,
                safe_float(valid_df["forecast_price"].max()) if not valid_df.empty else None,
                safe_float(valid_df["forecast_price"].mean()) if not valid_df.empty else None,
                json.dumps(df.to_dict(orient="records"), default=str),
                datetime.now().isoformat(timespec="seconds"),
            ),
        )

    return cursor.lastrowid


def list_forecast_snapshots(limit=25, db_file=DATABASE_FILE):
    initialize_database(db_file=db_file)

    with get_connection(db_file=db_file) as connection:
        rows = connection.execute(
            """
            SELECT
                forecast_snapshot_id,
                forecast_file,
                forecast_provider,
                forecast_model,
                target_date,
                row_count,
                min_price,
                max_price,
                average_price,
                created_at
            FROM forecast_snapshots
            ORDER BY forecast_snapshot_id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()

    return [row_to_dict(row) for row in rows]


def get_latest_forecast_snapshot(
    forecast_file=None,
    target_date=None,
    db_file=DATABASE_FILE,
):
    initialize_database(db_file=db_file)

    where_clauses = []
    params = []

    if forecast_file is not None:
        where_clauses.append("forecast_file = ?")
        params.append(str(forecast_file))

    if target_date is not None:
        where_clauses.append("target_date = ?")
        params.append(str(target_date))

    where_sql = ""

    if where_clauses:
        where_sql = "WHERE " + " AND ".join(where_clauses)

    with get_connection(db_file=db_file) as connection:
        row = connection.execute(
            f"""
            SELECT
                forecast_snapshot_id,
                forecast_file,
                forecast_provider,
                forecast_model,
                target_date,
                row_count,
                min_price,
                max_price,
                average_price,
                created_at
            FROM forecast_snapshots
            {where_sql}
            ORDER BY forecast_snapshot_id DESC
            LIMIT 1
            """,
            params,
        ).fetchone()

    if row is None:
        return None

    return row_to_dict(row)


def first_non_empty(df, column):
    if column not in df.columns:
        return None

    values = df[column].dropna()

    if values.empty:
        return None

    return str(values.iloc[0])


def safe_float(value):
    if pd.isna(value):
        return None

    return float(value)
