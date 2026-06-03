import json
from datetime import datetime

from src.config.paths import DATABASE_FILE
from src.db.database import get_connection, initialize_database
from src.db.models import row_to_dict


def save_business_decision(asset_id, decision, db_file=DATABASE_FILE):
    initialize_database(db_file=db_file)

    with get_connection(db_file=db_file) as connection:
        cursor = connection.execute(
            """
            INSERT INTO business_decisions (
                asset_id,
                generated_at,
                recommendation_title,
                recommendation_status,
                readiness,
                expected_pnl_eur,
                hedged_revenue_eur,
                residual_exposure_eur,
                forecast_provider,
                forecast_model,
                payload_json
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                asset_id,
                decision.get("generated_at")
                or datetime.now().isoformat(timespec="seconds"),
                decision.get("recommendation_title"),
                decision.get("recommendation_status"),
                decision.get("readiness"),
                decision.get("expected_pnl_eur"),
                decision.get("hedged_revenue_eur"),
                decision.get("residual_exposure_eur"),
                decision.get("forecast_provider"),
                decision.get("forecast_model"),
                json.dumps(decision, default=str),
            ),
        )

    return cursor.lastrowid


def get_latest_business_decision(asset_id, db_file=DATABASE_FILE):
    initialize_database(db_file=db_file)

    with get_connection(db_file=db_file) as connection:
        row = connection.execute(
            """
            SELECT *
            FROM business_decisions
            WHERE asset_id = ?
            ORDER BY decision_id DESC
            LIMIT 1
            """,
            (asset_id,),
        ).fetchone()

    if row is None:
        return None

    result = row_to_dict(row)
    result["payload"] = json.loads(result.pop("payload_json"))

    return result


def list_business_decisions(asset_id, limit=25, db_file=DATABASE_FILE):
    initialize_database(db_file=db_file)

    with get_connection(db_file=db_file) as connection:
        rows = connection.execute(
            """
            SELECT
                decision_id,
                asset_id,
                generated_at,
                recommendation_title,
                recommendation_status,
                readiness,
                expected_pnl_eur,
                hedged_revenue_eur,
                residual_exposure_eur,
                forecast_provider,
                forecast_model
            FROM business_decisions
            WHERE asset_id = ?
            ORDER BY decision_id DESC
            LIMIT ?
            """,
            (asset_id, limit),
        ).fetchall()

    return [row_to_dict(row) for row in rows]
