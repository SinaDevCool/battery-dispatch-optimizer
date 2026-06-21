import json

from backend.config.paths import DATABASE_FILE
from backend.db.database import get_connection, initialize_database
from backend.db.mode_namespace import mode_value, payload_data_mode
from backend.db.models import row_to_dict


def save_signal_run(signal_result, asset_id=None, db_file=DATABASE_FILE):
    initialize_database(db_file=db_file)

    metadata = signal_result.get("metadata", {})
    summary = signal_result.get("summary", {})
    validation = signal_result.get("validation", {})
    data_mode = payload_data_mode(signal_result)

    resolved_asset_id = asset_id or metadata.get("asset_id") or "default_site"
    signal_result.setdefault("metadata", {})
    signal_result["metadata"]["data_mode"] = data_mode

    with get_connection(db_file=db_file) as connection:
        cursor = connection.execute(
            """
            INSERT INTO signal_runs (
                asset_id,
                generated_at,
                target_date,
                optimizer_engine,
                forecast_provider,
                forecast_model,
                market_profile_id,
                signal,
                opportunity_level,
                total_pnl_eur,
                profit_per_mw_day,
                validation_status,
                data_mode,
                payload_json
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                resolved_asset_id,
                metadata.get("generated_at"),
                metadata.get("target_date"),
                signal_result.get("optimization", {}).get("optimizer_engine"),
                metadata.get("forecast_provider"),
                metadata.get("forecast_model"),
                metadata.get("market_profile_id"),
                summary.get("signal"),
                summary.get("opportunity_level"),
                summary.get("total_pnl_eur"),
                summary.get("profit_per_mw_day"),
                validation.get("status"),
                data_mode,
                json.dumps(signal_result),
            ),
        )

        signal_id = cursor.lastrowid

    return signal_id


def list_signal_runs(asset_id, limit=50, db_file=DATABASE_FILE, data_mode=None):
    initialize_database(db_file=db_file)
    resolved_data_mode = mode_value(data_mode)

    with get_connection(db_file=db_file) as connection:
        rows = connection.execute(
            """
            SELECT
                signal_id,
                asset_id,
                generated_at,
                target_date,
                optimizer_engine,
                forecast_provider,
                forecast_model,
                market_profile_id,
                signal,
                opportunity_level,
                total_pnl_eur,
                profit_per_mw_day,
                validation_status,
                data_mode
            FROM signal_runs
            WHERE asset_id = ?
              AND data_mode = ?
            ORDER BY signal_id DESC
            LIMIT ?
            """,
            (asset_id, resolved_data_mode, limit),
        ).fetchall()

    return [row_to_dict(row) for row in rows]


def get_signal_run(signal_id, db_file=DATABASE_FILE):
    initialize_database(db_file=db_file)

    with get_connection(db_file=db_file) as connection:
        row = connection.execute(
            """
            SELECT *
            FROM signal_runs
            WHERE signal_id = ?
            """,
            (signal_id,),
        ).fetchone()

    if row is None:
        return None

    result = row_to_dict(row)
    result["payload"] = json.loads(result.pop("payload_json"))

    return result



