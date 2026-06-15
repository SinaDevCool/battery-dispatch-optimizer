import json

from backend.config.paths import DATABASE_FILE
from backend.db.database import get_connection, initialize_database
from backend.db.models import row_to_dict


def save_forecast_actual_run(result, db_file=DATABASE_FILE):
    initialize_database(db_file=db_file)

    metrics = result.get("forecast_error_metrics", {})
    realized = result.get("realized_dispatch", {})
    metadata = result.get("metadata", {})

    with get_connection(db_file=db_file) as connection:
        cursor = connection.execute(
            """
            INSERT INTO forecast_actual_runs (
                asset_id,
                generated_at,
                target_date,
                forecast_provider,
                forecast_model,
                row_count,
                mae_eur_per_mwh,
                rmse_eur_per_mwh,
                bias_eur_per_mwh,
                predicted_pnl_eur,
                realized_pnl_eur,
                revenue_delta_eur,
                payload_json
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                result.get("asset_id"),
                result.get("generated_at"),
                metadata.get("target_date"),
                metadata.get("forecast_provider"),
                metadata.get("forecast_model"),
                metrics.get("row_count"),
                metrics.get("mae_eur_per_mwh"),
                metrics.get("rmse_eur_per_mwh"),
                metrics.get("bias_eur_per_mwh"),
                realized.get("predicted_pnl_eur"),
                realized.get("realized_pnl_eur"),
                realized.get("revenue_delta_eur"),
                json.dumps(result),
            ),
        )

        forecast_actual_id = cursor.lastrowid

    return forecast_actual_id


def list_forecast_performance_runs(asset_id, limit=50, db_file=DATABASE_FILE):
    initialize_database(db_file=db_file)

    with get_connection(db_file=db_file) as connection:
        rows = connection.execute(
            """
            SELECT
                forecast_actual_id,
                asset_id,
                generated_at,
                target_date,
                forecast_provider,
                forecast_model,
                row_count,
                mae_eur_per_mwh,
                rmse_eur_per_mwh,
                bias_eur_per_mwh,
                predicted_pnl_eur,
                realized_pnl_eur,
                revenue_delta_eur
            FROM forecast_actual_runs
            WHERE asset_id = ?
            ORDER BY forecast_actual_id DESC
            LIMIT ?
            """,
            (asset_id, limit),
        ).fetchall()

    return [row_to_dict(row) for row in rows]


def get_forecast_performance_run(forecast_actual_id, db_file=DATABASE_FILE):
    initialize_database(db_file=db_file)

    with get_connection(db_file=db_file) as connection:
        row = connection.execute(
            """
            SELECT *
            FROM forecast_actual_runs
            WHERE forecast_actual_id = ?
            """,
            (forecast_actual_id,),
        ).fetchone()

    if row is None:
        return None

    result = row_to_dict(row)
    result["payload"] = json.loads(result.pop("payload_json"))

    return result



