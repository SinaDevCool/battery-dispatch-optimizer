from datetime import datetime

from src.assets.asset_loader import get_asset
from src.db.repositories.telemetry_repository import (
    get_latest_telemetry_snapshot,
    list_telemetry_snapshots,
    save_telemetry_snapshot,
)


def save_demo_asset_telemetry(asset_id):
    asset = get_asset(asset_id)
    battery_config = asset.battery_config or {}
    grid_connection = asset.grid_connection or {}

    capacity_mwh = numeric(battery_config.get("capacity_mwh"))
    max_charge_power_mw = numeric(
        battery_config.get("max_charge_power_mw")
        or battery_config.get("power_mw")
    )
    max_discharge_power_mw = numeric(
        battery_config.get("max_discharge_power_mw")
        or battery_config.get("power_mw")
    )
    min_soc_mwh = numeric(battery_config.get("min_soc_mwh"))
    soc_mwh = round(max(capacity_mwh * 0.55, min_soc_mwh), 4)
    soc_percent = round((soc_mwh / capacity_mwh) * 100, 2) if capacity_mwh else 0.0

    snapshot = {
        "status": "ok",
        "asset_id": asset_id,
        "captured_at": datetime.now().isoformat(timespec="seconds"),
        "provider": "demo_local_telemetry",
        "availability_status": "available",
        "soc_mwh": soc_mwh,
        "soc_percent": soc_percent,
        "available_charge_power_mw": max_charge_power_mw,
        "available_discharge_power_mw": max_discharge_power_mw,
        "grid_import_limit_mw": numeric(
            grid_connection.get("max_import_mw")
            or grid_connection.get("connection_capacity_mw")
            or max_charge_power_mw
        ),
        "grid_export_limit_mw": numeric(
            grid_connection.get("max_export_mw")
            or grid_connection.get("connection_capacity_mw")
            or max_discharge_power_mw
        ),
        "schedule_deviation_mwh": 0.0,
        "ems_status": "demo_connected",
        "inverter_status": "available",
        "curtailment_active": False,
        "maintenance_active": False,
        "warnings": [
            "Demo telemetry is synthetic and must be replaced by EMS/SCADA data before live trading.",
        ],
    }
    telemetry_id = save_telemetry_snapshot(snapshot)
    snapshot["telemetry_id"] = telemetry_id

    return snapshot


def latest_asset_telemetry(asset_id):
    latest = get_latest_telemetry_snapshot(asset_id)

    if latest is None:
        return {
            "status": "not_found",
            "asset_id": asset_id,
            "message": "No telemetry snapshot found. Connect telemetry or seed demo telemetry.",
            "telemetry": None,
        }

    return {
        "status": "ok",
        "asset_id": asset_id,
        "telemetry": latest["payload"],
    }


def telemetry_history(asset_id, limit=25):
    return {
        "status": "ok",
        "asset_id": asset_id,
        "telemetry": list_telemetry_snapshots(asset_id=asset_id, limit=limit),
    }


def numeric(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0
