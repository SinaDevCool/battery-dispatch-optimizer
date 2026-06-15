import json

from backend.config.paths import DATABASE_FILE
from backend.db.database import get_connection, initialize_database
from backend.db.models import row_to_dict


def save_settlement_reconciliation_run(result, db_file=DATABASE_FILE):
    initialize_database(db_file=db_file)

    summary = result.get("summary", {})
    links = result.get("links", {})

    with get_connection(db_file=db_file) as connection:
        cursor = connection.execute(
            """
            INSERT INTO settlement_reconciliation_runs (
                asset_id,
                generated_at,
                execution_proposal_id,
                paper_trade_id,
                forecast_actual_id,
                expected_pnl_eur,
                paper_pnl_eur,
                realized_pnl_eur,
                paper_delta_eur,
                realized_delta_eur,
                status,
                primary_variance_driver,
                payload_json
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                result["asset_id"],
                result["generated_at"],
                links.get("execution_proposal_id"),
                links.get("paper_trade_id"),
                links.get("forecast_actual_id"),
                summary.get("expected_pnl_eur"),
                summary.get("paper_pnl_eur"),
                summary.get("realized_pnl_eur"),
                summary.get("paper_delta_eur"),
                summary.get("realized_delta_eur"),
                result["status"],
                result.get("primary_variance_driver"),
                json.dumps(result, default=str),
            ),
        )

    return cursor.lastrowid


def get_latest_settlement_reconciliation(asset_id, db_file=DATABASE_FILE):
    initialize_database(db_file=db_file)

    with get_connection(db_file=db_file) as connection:
        row = connection.execute(
            """
            SELECT *
            FROM settlement_reconciliation_runs
            WHERE asset_id = ?
            ORDER BY settlement_reconciliation_id DESC
            LIMIT 1
            """,
            (asset_id,),
        ).fetchone()

    if row is None:
        return None

    result = row_to_dict(row)
    result["payload"] = json.loads(result.pop("payload_json"))

    return result


def list_settlement_reconciliations(asset_id, limit=25, db_file=DATABASE_FILE):
    initialize_database(db_file=db_file)

    with get_connection(db_file=db_file) as connection:
        rows = connection.execute(
            """
            SELECT
                settlement_reconciliation_id,
                asset_id,
                generated_at,
                execution_proposal_id,
                paper_trade_id,
                forecast_actual_id,
                expected_pnl_eur,
                paper_pnl_eur,
                realized_pnl_eur,
                paper_delta_eur,
                realized_delta_eur,
                status,
                primary_variance_driver
            FROM settlement_reconciliation_runs
            WHERE asset_id = ?
            ORDER BY settlement_reconciliation_id DESC
            LIMIT ?
            """,
            (asset_id, limit),
        ).fetchall()

    return [row_to_dict(row) for row in rows]



