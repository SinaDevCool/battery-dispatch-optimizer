import os
import sqlite3
from datetime import datetime

from src.config.paths import DATABASE_FILE


REQUIRED_TABLES = [
    "assets",
    "signal_runs",
    "revenue_stack_runs",
    "execution_proposals",
    "execution_paper_trades",
    "execution_market_submissions",
    "execution_approvals",
    "automation_policies",
    "automation_events",
    "asset_telemetry_snapshots",
    "settlement_reconciliation_runs",
]


def build_persistence_readiness(db_file=DATABASE_FILE):
    db_path = db_file
    parent_dir = db_path.parent
    checks = [
        database_exists_check(db_path),
        parent_writable_check(parent_dir),
        database_file_writable_check(db_path),
        migration_capability_check(db_path),
        required_tables_check(db_path),
        transactional_write_probe_check(db_path),
    ]
    status = classify_persistence_status(checks)

    return {
        "status": "ok",
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "database_file": str(db_path),
        "persistence_status": status,
        "automation_blocking_level": (
            "paper_trading" if status != "ready" else None
        ),
        "checks": checks,
        "summary": {
            "passed": count_status(checks, "passed"),
            "blocked": count_status(checks, "blocked"),
            "review": count_status(checks, "review"),
            "total": len(checks),
            "missing_tables": missing_required_tables(checks),
        },
        "recommended_actions": build_recommended_actions(checks, status),
    }


def database_exists_check(db_path):
    exists = db_path.exists()

    return readiness_check(
        check="database_file_exists",
        label="Database file",
        status="passed" if exists else "blocked",
        message=(
            "Database file exists."
            if exists
            else "Database file is missing; initialize persistence before automation."
        ),
        evidence={"path": str(db_path)},
    )


def parent_writable_check(parent_dir):
    writable = parent_dir.exists() and os.access(parent_dir, os.W_OK)

    if not writable:
        return readiness_check(
            check="database_parent_writable",
            label="Database directory",
            status="blocked",
            message="Database directory is not writable by the application process.",
            evidence={"path": str(parent_dir), "os_access_writable": writable},
        )

    return readiness_check(
        check="database_parent_writable",
        label="Database directory",
        status="passed",
        message="Database directory reports write access.",
        evidence={"path": str(parent_dir), "os_access_writable": writable},
    )


def database_file_writable_check(db_path):
    if not db_path.exists():
        return readiness_check(
            check="database_file_writable",
            label="Database file write access",
            status="blocked",
            message="Database file does not exist, so write access cannot be verified.",
            evidence={"path": str(db_path)},
        )

    try:
        with open(db_path, "r+b"):
            pass
    except OSError as error:
        return readiness_check(
            check="database_file_writable",
            label="Database file write access",
            status="blocked",
            message=f"Database file is not writable: {error}",
            evidence={
                "path": str(db_path),
                "error_type": type(error).__name__,
                "os_access_writable": os.access(db_path, os.W_OK),
            },
        )

    return readiness_check(
        check="database_file_writable",
        label="Database file write access",
        status="passed",
        message="Database file can be opened for write access.",
        evidence={
            "path": str(db_path),
            "os_access_writable": os.access(db_path, os.W_OK),
        },
    )


def migration_capability_check(db_path):
    try:
        with readiness_connection(db_path) as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS automation_events (
                    automation_event_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    asset_id TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    action TEXT,
                    status TEXT NOT NULL,
                    automation_mode_before TEXT,
                    automation_mode_after TEXT,
                    strategy_mode_before TEXT,
                    strategy_mode_after TEXT,
                    error_type TEXT,
                    payload_json TEXT NOT NULL
                )
                """
            )
    except sqlite3.Error as error:
        return readiness_check(
            check="migration_capability",
            label="Migration capability",
            status="blocked",
            message=f"Database migrations cannot be applied: {error}",
            evidence={"error_type": type(error).__name__},
        )

    return readiness_check(
        check="migration_capability",
        label="Migration capability",
        status="passed",
        message="Database migrations can be applied.",
        evidence={"required_migration": "automation_events"},
    )


def required_tables_check(db_path):
    try:
        with readiness_connection(db_path) as connection:
            rows = connection.execute(
                """
                SELECT name
                FROM sqlite_master
                WHERE type = 'table'
                """
            ).fetchall()
    except sqlite3.Error as error:
        return readiness_check(
            check="required_tables",
            label="Required tables",
            status="blocked",
            message=f"Required tables cannot be inspected: {error}",
            evidence={"error_type": type(error).__name__, "missing_tables": REQUIRED_TABLES},
        )

    existing_tables = {row["name"] for row in rows}
    missing = [
        table
        for table in REQUIRED_TABLES
        if table not in existing_tables
    ]

    return readiness_check(
        check="required_tables",
        label="Required tables",
        status="blocked" if missing else "passed",
        message=(
            "All required persistence tables exist."
            if not missing
            else "Required persistence tables are missing."
        ),
        evidence={
            "missing_tables": missing,
            "required_tables": REQUIRED_TABLES,
        },
    )


def transactional_write_probe_check(db_path):
    try:
        with readiness_connection(db_path) as connection:
            connection.execute("BEGIN")
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS __persistence_write_probe (
                    probe_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    created_at TEXT NOT NULL
                )
                """
            )
            connection.execute(
                """
                INSERT INTO __persistence_write_probe (created_at)
                VALUES (?)
                """,
                (datetime.now().isoformat(timespec="seconds"),),
            )
            connection.execute("DROP TABLE __persistence_write_probe")
            connection.rollback()
    except sqlite3.Error as error:
        return readiness_check(
            check="transactional_write_probe",
            label="Transactional write probe",
            status="blocked",
            message=f"Database write probe failed: {error}",
            evidence={"error_type": type(error).__name__},
        )

    return readiness_check(
        check="transactional_write_probe",
        label="Transactional write probe",
        status="passed",
        message="Database accepts transactional writes.",
        evidence={"probe": "create_insert_drop_rollback"},
    )


def readiness_connection(db_path):
    connection = sqlite3.connect(db_path, timeout=1)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA busy_timeout = 1000")
    return connection


def readiness_check(check, label, status, message, evidence):
    return {
        "check": check,
        "evidence": evidence,
        "label": label,
        "message": message,
        "status": status,
    }


def classify_persistence_status(checks):
    if any(check["status"] == "blocked" for check in checks):
        return "blocked"

    if any(check["status"] == "review" for check in checks):
        return "review"

    return "ready"


def count_status(checks, status):
    return len([check for check in checks if check["status"] == status])


def missing_required_tables(checks):
    for check in checks:
        if check["check"] == "required_tables":
            return check.get("evidence", {}).get("missing_tables", [])

    return []


def build_recommended_actions(checks, status):
    if status == "ready":
        return [
            "Persistence is ready for automated proposal, paper trade, telemetry, settlement, approval, submission, and audit writes.",
        ]

    actions = []
    for check in checks:
        if check["status"] != "blocked":
            continue

        if check["check"] == "database_file_writable":
            actions.append("Fix database file permissions or move SQLite storage to a writable service path.")
        elif check["check"] == "database_parent_writable":
            actions.append("Fix database directory permissions for the application runtime.")
        elif check["check"] == "migration_capability":
            actions.append("Allow schema migrations or run migrations in a writable maintenance context.")
        elif check["check"] == "required_tables":
            actions.append("Apply database migrations so automation_events and execution evidence tables exist.")
        elif check["check"] == "transactional_write_probe":
            actions.append("Resolve SQLite write lock or read-only mount before enabling automated trading.")
        else:
            actions.append(check["message"])

    return dedupe(actions)


def dedupe(items):
    seen = set()
    result = []

    for item in items:
        if item in seen:
            continue

        seen.add(item)
        result.append(item)

    return result
