import json
from datetime import datetime

from src.config.paths import DATABASE_FILE
from src.db.database import get_connection, initialize_database
from src.db.models import row_to_dict


def save_workflow_run(workflow_run, db_file=DATABASE_FILE):
    initialize_database(db_file=db_file)

    with get_connection(db_file=db_file) as connection:
        cursor = connection.execute(
            """
            INSERT INTO workflow_runs (
                asset_id,
                status,
                started_at,
                completed_at,
                optimizer_engine,
                forecast_snapshot_id,
                signal_id,
                revenue_stack_id,
                decision_id,
                target_date,
                forecast_provider,
                forecast_model,
                recommendation_status,
                expected_pnl_eur,
                payload_json
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                workflow_run["asset_id"],
                workflow_run.get("status", "ok"),
                workflow_run.get("started_at")
                or datetime.now().isoformat(timespec="seconds"),
                workflow_run.get("completed_at"),
                workflow_run.get("optimizer_engine"),
                workflow_run.get("forecast_snapshot_id"),
                workflow_run.get("signal_id"),
                workflow_run.get("revenue_stack_id"),
                workflow_run.get("decision_id"),
                workflow_run.get("target_date"),
                workflow_run.get("forecast_provider"),
                workflow_run.get("forecast_model"),
                workflow_run.get("recommendation_status"),
                workflow_run.get("expected_pnl_eur"),
                json.dumps(workflow_run, default=str),
            ),
        )

    return cursor.lastrowid


def list_workflow_runs(asset_id, limit=25, db_file=DATABASE_FILE):
    initialize_database(db_file=db_file)

    with get_connection(db_file=db_file) as connection:
        rows = connection.execute(
            """
            SELECT
                workflow_run_id,
                asset_id,
                status,
                started_at,
                completed_at,
                optimizer_engine,
                forecast_snapshot_id,
                signal_id,
                revenue_stack_id,
                decision_id,
                target_date,
                forecast_provider,
                forecast_model,
                recommendation_status,
                expected_pnl_eur
            FROM workflow_runs
            WHERE asset_id = ?
            ORDER BY workflow_run_id DESC
            LIMIT ?
            """,
            (asset_id, limit),
        ).fetchall()

    return [row_to_dict(row) for row in rows]


def get_latest_workflow_run(asset_id, db_file=DATABASE_FILE):
    runs = list_workflow_runs(asset_id=asset_id, limit=1, db_file=db_file)

    if not runs:
        return None

    return get_workflow_run(runs[0]["workflow_run_id"], db_file=db_file)


def get_workflow_run(workflow_run_id, db_file=DATABASE_FILE):
    initialize_database(db_file=db_file)

    with get_connection(db_file=db_file) as connection:
        row = connection.execute(
            """
            SELECT *
            FROM workflow_runs
            WHERE workflow_run_id = ?
            """,
            (workflow_run_id,),
        ).fetchone()

    if row is None:
        return None

    result = row_to_dict(row)
    result["payload"] = json.loads(result.pop("payload_json"))

    return result
