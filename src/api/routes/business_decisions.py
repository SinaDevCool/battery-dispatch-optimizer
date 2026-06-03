from fastapi import APIRouter

from src.api.schemas import ApiResponse
from src.config.paths import DATABASE_FILE
from src.db.database import get_connection, initialize_database
from src.services.business_decision_service import (
    build_business_decision,
    get_or_build_latest_business_decision,
    list_business_decision_history,
)


router = APIRouter()


@router.post("/assets/{asset_id}/business-decision/build", response_model=ApiResponse)
def build_asset_business_decision(asset_id: str):
    try:
        decision = build_business_decision(asset_id)
    except ValueError as error:
        return {
            "status": "not_found",
            "message": str(error),
        }

    return {
        "status": "ok",
        "asset_id": asset_id,
        "decision": decision,
    }


@router.get("/assets/{asset_id}/business-decision/latest", response_model=ApiResponse)
def latest_asset_business_decision(asset_id: str):
    try:
        decision = get_or_build_latest_business_decision(asset_id)
    except ValueError as error:
        return {
            "status": "not_found",
            "message": str(error),
        }

    return {
        "status": "ok",
        "asset_id": asset_id,
        "decision": decision,
    }


@router.get("/assets/{asset_id}/business-decision/history", response_model=ApiResponse)
def asset_business_decision_history(asset_id: str, limit: int = 25):
    decisions = list_business_decision_history(asset_id=asset_id, limit=limit)

    return {
        "status": "ok",
        "asset_id": asset_id,
        "decisions": decisions,
    }


@router.get("/database/status", response_model=ApiResponse)
def database_status():
    initialize_database()

    table_names = [
        "assets",
        "forecast_snapshots",
        "signal_runs",
        "revenue_stack_runs",
        "revenue_product_results",
        "forecast_actual_runs",
        "business_decisions",
        "workflow_runs",
        "execution_proposals",
    ]

    with get_connection() as connection:
        table_counts = {
            table_name: connection.execute(
                f"SELECT COUNT(*) AS count FROM {table_name}"
            ).fetchone()["count"]
            for table_name in table_names
        }

    return {
        "status": "ok",
        "database_file": str(DATABASE_FILE),
        "table_counts": table_counts,
    }
