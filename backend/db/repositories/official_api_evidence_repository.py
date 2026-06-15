import json
import sqlite3
from datetime import datetime

from backend.config.paths import DATABASE_FILE
from backend.db.database import get_connection, initialize_database
from backend.db.models import row_to_dict


def upsert_official_api_evidence(evidence, db_file=DATABASE_FILE):
    initialize_database(db_file=db_file)
    payload = {
        **evidence,
        "recorded_at": evidence.get("recorded_at")
        or datetime.now().isoformat(timespec="seconds"),
    }

    with get_connection(db_file=db_file) as connection:
        cursor = connection.execute(
            """
            INSERT INTO official_api_evidence (
                adapter_id,
                requirement_id,
                evidence_type,
                evidence_status,
                evidence_owner,
                evidence_reference,
                recorded_at,
                expires_at,
                review_at,
                unlocks_mode,
                payload_json
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(adapter_id, requirement_id)
            DO UPDATE SET
                evidence_type = excluded.evidence_type,
                evidence_status = excluded.evidence_status,
                evidence_owner = excluded.evidence_owner,
                evidence_reference = excluded.evidence_reference,
                recorded_at = excluded.recorded_at,
                expires_at = excluded.expires_at,
                review_at = excluded.review_at,
                unlocks_mode = excluded.unlocks_mode,
                payload_json = excluded.payload_json
            """,
            (
                payload["adapter_id"],
                payload["requirement_id"],
                payload.get("evidence_type"),
                payload.get("evidence_status", "pending"),
                payload.get("evidence_owner"),
                payload.get("evidence_reference"),
                payload["recorded_at"],
                payload.get("expires_at"),
                payload.get("review_at"),
                payload.get("unlocks_mode"),
                json.dumps(payload, default=str),
            ),
        )

    return cursor.lastrowid


def list_official_api_evidence(adapter_id=None, db_file=DATABASE_FILE):
    initialize_database(db_file=db_file)

    try:
        with get_connection(db_file=db_file) as connection:
            if adapter_id:
                rows = connection.execute(
                    """
                    SELECT *
                    FROM official_api_evidence
                    WHERE adapter_id = ?
                    ORDER BY recorded_at DESC
                    """,
                    (adapter_id,),
                ).fetchall()
            else:
                rows = connection.execute(
                    """
                    SELECT *
                    FROM official_api_evidence
                    ORDER BY adapter_id ASC, requirement_id ASC
                    """
                ).fetchall()
    except sqlite3.OperationalError as error:
        if "readonly" in str(error).lower() or "no such table" in str(error).lower():
            return []
        raise

    return [format_evidence_row(row) for row in rows]


def get_official_api_evidence(adapter_id, requirement_id, db_file=DATABASE_FILE):
    initialize_database(db_file=db_file)

    try:
        with get_connection(db_file=db_file) as connection:
            row = connection.execute(
                """
                SELECT *
                FROM official_api_evidence
                WHERE adapter_id = ? AND requirement_id = ?
                LIMIT 1
                """,
                (adapter_id, requirement_id),
            ).fetchone()
    except sqlite3.OperationalError as error:
        if "readonly" in str(error).lower() or "no such table" in str(error).lower():
            return None
        raise

    if row is None:
        return None

    return format_evidence_row(row)


def evidence_by_requirement(adapter_id, db_file=DATABASE_FILE):
    return {
        evidence["requirement_id"]: evidence
        for evidence in list_official_api_evidence(
            adapter_id=adapter_id,
            db_file=db_file,
        )
    }


def format_evidence_row(row):
    result = row_to_dict(row)
    payload = json.loads(result.pop("payload_json"))
    result.update(payload)
    result["secret_values_exposed"] = False
    return result



