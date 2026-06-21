from __future__ import annotations

from urllib.parse import urlparse

from backend.config.app_settings import get_app_settings
from backend.config.paths import DATABASE_FILE
from backend.data_environment import current_data_mode
from backend.db.database import get_connection, initialize_database
from backend.db.mode_namespace import MODE_AWARE_TABLES


def build_database_namespace_readiness() -> dict:
    settings = get_app_settings()
    active_backend = classify_database_backend(settings.database_url)
    initialize_database()
    mode_columns = inspect_mode_columns()

    return {
        "status": "ok",
        "data_mode": current_data_mode(),
        "active_backend": active_backend,
        "database_url_configured": bool(settings.database_url),
        "local_sqlite_file": str(DATABASE_FILE),
        "cloud_target": {
            "recommended_engine": "azure_postgresql_flexible_server",
            "namespace_strategy": "schemas",
            "schemas": ["mock", "live", "audit", "config"],
            "blob_containers": ["mock-evidence", "live-evidence", "audit-archive"],
        },
        "local_namespace_strategy": {
            "engine": "sqlite",
            "separation": "data_mode columns plus repository-level filters",
            "tables": mode_columns,
        },
        "production_controls": [
            "Use a mock_app_user scoped to mock schema only.",
            "Use a live_app_user scoped to live schema only.",
            "Use a read_only_ai_user for AI evidence views.",
            "Store large evidence files in separate Azure Blob containers.",
        ],
    }


def classify_database_backend(database_url: str | None) -> str:
    if not database_url:
        return "local_sqlite"

    scheme = urlparse(database_url).scheme.lower()
    if scheme in {"postgres", "postgresql"}:
        return "postgresql"

    if scheme in {"sqlite", "sqlite3"}:
        return "sqlite"

    return scheme or "configured"


def inspect_mode_columns() -> list[dict]:
    rows = []
    with get_connection() as connection:
        for table_name in MODE_AWARE_TABLES:
            columns = connection.execute(f"PRAGMA table_info({table_name})").fetchall()
            has_data_mode = any(column["name"] == "data_mode" for column in columns)
            indexes = connection.execute(f"PRAGMA index_list({table_name})").fetchall()
            mode_indexes = [
                index["name"]
                for index in indexes
                if "data_mode" in str(index["name"])
            ]
            rows.append(
                {
                    "table": table_name,
                    "data_mode_column": has_data_mode,
                    "mode_index_count": len(mode_indexes),
                    "mode_indexes": mode_indexes,
                }
            )
    return rows
