import json

from backend.config.paths import DATABASE_FILE
from backend.db.database import get_connection, initialize_database
from backend.db.mode_namespace import mode_value, payload_data_mode
from backend.db.models import row_to_dict


def save_telemetry_snapshot(snapshot, db_file=DATABASE_FILE):
    initialize_database(db_file=db_file)
    data_mode = payload_data_mode(snapshot)
    snapshot["data_mode"] = data_mode

    with get_connection(db_file=db_file) as connection:
        cursor = connection.execute(
            """
            INSERT INTO asset_telemetry_snapshots (
                asset_id,
                captured_at,
                provider,
                status,
                availability_status,
                soc_mwh,
                soc_percent,
                available_charge_power_mw,
                available_discharge_power_mw,
                grid_import_limit_mw,
                grid_export_limit_mw,
                schedule_deviation_mwh,
                data_mode,
                payload_json
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                snapshot["asset_id"],
                snapshot["captured_at"],
                snapshot["provider"],
                snapshot["status"],
                snapshot.get("availability_status"),
                snapshot.get("soc_mwh"),
                snapshot.get("soc_percent"),
                snapshot.get("available_charge_power_mw"),
                snapshot.get("available_discharge_power_mw"),
                snapshot.get("grid_import_limit_mw"),
                snapshot.get("grid_export_limit_mw"),
                snapshot.get("schedule_deviation_mwh"),
                data_mode,
                json.dumps(snapshot, default=str),
            ),
        )

    return cursor.lastrowid


def get_latest_telemetry_snapshot(asset_id, db_file=DATABASE_FILE, data_mode=None):
    initialize_database(db_file=db_file)
    resolved_data_mode = mode_value(data_mode)

    with get_connection(db_file=db_file) as connection:
        row = connection.execute(
            """
            SELECT *
            FROM asset_telemetry_snapshots
            WHERE asset_id = ?
              AND data_mode = ?
            ORDER BY telemetry_id DESC
            LIMIT 1
            """,
            (asset_id, resolved_data_mode),
        ).fetchone()

    if row is None:
        return None

    result = row_to_dict(row)
    result["payload"] = json.loads(result.pop("payload_json"))

    return result


def list_telemetry_snapshots(asset_id, limit=25, db_file=DATABASE_FILE, data_mode=None):
    initialize_database(db_file=db_file)
    resolved_data_mode = mode_value(data_mode)

    with get_connection(db_file=db_file) as connection:
        rows = connection.execute(
            """
            SELECT
                telemetry_id,
                asset_id,
                captured_at,
                provider,
                status,
                availability_status,
                soc_mwh,
                soc_percent,
                available_charge_power_mw,
                available_discharge_power_mw,
                grid_import_limit_mw,
                grid_export_limit_mw,
                schedule_deviation_mwh,
                data_mode
            FROM asset_telemetry_snapshots
            WHERE asset_id = ?
              AND data_mode = ?
            ORDER BY telemetry_id DESC
            LIMIT ?
            """,
            (asset_id, resolved_data_mode, limit),
        ).fetchall()

    return [row_to_dict(row) for row in rows]



