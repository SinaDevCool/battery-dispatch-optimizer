import json

from src.config.paths import DATABASE_FILE
from src.db.database import get_connection, initialize_database
from src.db.models import row_to_dict


def save_execution_proposal(proposal, db_file=DATABASE_FILE):
    initialize_database(db_file=db_file)

    summary = proposal.get("summary", {})

    with get_connection(db_file=db_file) as connection:
        cursor = connection.execute(
            """
            INSERT INTO execution_proposals (
                asset_id,
                generated_at,
                status,
                approval_status,
                signal_id,
                workflow_run_id,
                target_date,
                market,
                order_count,
                total_buy_mwh,
                total_sell_mwh,
                expected_pnl_eur,
                max_daily_loss_eur,
                payload_json
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                proposal["asset_id"],
                proposal["generated_at"],
                proposal["status"],
                proposal.get("approval_status"),
                proposal.get("signal_id"),
                proposal.get("workflow_run_id"),
                proposal.get("target_date"),
                proposal.get("market"),
                summary.get("order_count"),
                summary.get("total_buy_mwh"),
                summary.get("total_sell_mwh"),
                summary.get("expected_pnl_eur"),
                summary.get("max_daily_loss_eur"),
                json.dumps(proposal, default=str),
            ),
        )

    return cursor.lastrowid


def get_latest_execution_proposal(asset_id, db_file=DATABASE_FILE):
    initialize_database(db_file=db_file)

    with get_connection(db_file=db_file) as connection:
        row = connection.execute(
            """
            SELECT *
            FROM execution_proposals
            WHERE asset_id = ?
            ORDER BY execution_proposal_id DESC
            LIMIT 1
            """,
            (asset_id,),
        ).fetchone()

    if row is None:
        return None

    result = row_to_dict(row)
    result["payload"] = json.loads(result.pop("payload_json"))

    return result


def list_execution_proposals(asset_id, limit=25, db_file=DATABASE_FILE):
    initialize_database(db_file=db_file)

    with get_connection(db_file=db_file) as connection:
        rows = connection.execute(
            """
            SELECT
                execution_proposal_id,
                asset_id,
                generated_at,
                status,
                approval_status,
                signal_id,
                workflow_run_id,
                target_date,
                market,
                order_count,
                total_buy_mwh,
                total_sell_mwh,
                expected_pnl_eur,
                max_daily_loss_eur
            FROM execution_proposals
            WHERE asset_id = ?
            ORDER BY execution_proposal_id DESC
            LIMIT ?
            """,
            (asset_id, limit),
        ).fetchall()

    return [row_to_dict(row) for row in rows]
