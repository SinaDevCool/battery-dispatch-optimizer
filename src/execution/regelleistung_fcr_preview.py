from src.assets.asset_loader import get_asset
from src.db.repositories.telemetry_repository import get_latest_telemetry_snapshot
from src.execution.market_adapters.regelleistung_fcr import (
    build_regelleistung_fcr_preview,
)


def build_latest_regelleistung_fcr_preview(asset_id):
    asset = get_asset(asset_id)
    telemetry_record = get_latest_telemetry_snapshot(asset_id)
    telemetry = (telemetry_record or {}).get("payload") or {}

    preview = build_regelleistung_fcr_preview(
        asset=asset,
        telemetry=telemetry,
    )
    preview["asset_id"] = asset_id
    preview["telemetry_id"] = (telemetry_record or {}).get("telemetry_id")

    return preview


def latest_regelleistung_fcr_preview(asset_id):
    return {
        "status": "ok",
        "asset_id": asset_id,
        "preview": build_latest_regelleistung_fcr_preview(asset_id),
    }
