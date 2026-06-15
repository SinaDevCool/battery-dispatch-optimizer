from datetime import datetime

from backend.execution.market_adapters.base import MarketAdapter
from backend.execution.pretrade_proposal import numeric


MINIMUM_FCR_POWER_MW = 1.0
MINIMUM_FCR_DURATION_HOURS = 1.0


class RegelleistungFcrAdapter(MarketAdapter):
    adapter_id = "regelleistung_fcr"
    live_submission = False

    def submit_bids(self, bids, submitted_at):
        return {
            "adapter_id": self.adapter_id,
            "status": "preview_only",
            "submitted_at": submitted_at,
            "live_submission": self.live_submission,
            "summary": {
                "bid_count": len(bids or []),
            },
            "bids": bids or [],
        }


def build_regelleistung_fcr_preview(asset, telemetry=None, generated_at=None):
    generated_at = generated_at or datetime.now().isoformat(timespec="seconds")
    battery_config = asset.battery_config or {}
    grid_connection = asset.grid_connection or {}
    regulatory = asset.regulatory or {}
    telemetry = telemetry or {}
    capability = build_fcr_capability(
        battery_config=battery_config,
        grid_connection=grid_connection,
        telemetry=telemetry,
    )
    bid = build_fcr_capacity_bid(
        asset_id=asset.asset_id,
        capability=capability,
        telemetry=telemetry,
    )
    validation = validate_fcr_preview(
        capability=capability,
        regulatory=regulatory,
        telemetry=telemetry,
    )
    status = "ready_for_prequalification_review" if validation["status"] == "passed" else "not_ready"

    return {
        "status": status,
        "adapter_id": RegelleistungFcrAdapter.adapter_id,
        "adapter_name": "Regelleistung FCR",
        "venue": "regelleistung.net",
        "market_segment": "balancing_capacity",
        "product": "FCR_CAPACITY",
        "bidding_zone": "DE_LU",
        "environment": "preview",
        "live_submission": False,
        "generated_at": generated_at,
        "summary": {
            "available_symmetric_power_mw": capability["available_symmetric_power_mw"],
            "capacity_bid_mw": bid["capacity_mw"],
            "minimum_power_mw": MINIMUM_FCR_POWER_MW,
            "minimum_duration_hours": MINIMUM_FCR_DURATION_HOURS,
            "validation_status": validation["status"],
            "live_submission": False,
        },
        "capability": capability,
        "validation": validation,
        "bids": [bid] if bid["capacity_mw"] > 0 else [],
        "audit": [
            {
                "event": "regelleistung_fcr_mapping",
                "actor": "regelleistung_fcr_adapter",
                "status": validation["status"],
                "note": "Mapped asset capability into an FCR capacity preview. Live submission is disabled.",
            }
        ],
    }


def build_fcr_capability(battery_config, grid_connection, telemetry):
    max_charge_power_mw = numeric(
        battery_config.get("max_charge_power_mw")
        or battery_config.get("power_mw")
    )
    max_discharge_power_mw = numeric(
        battery_config.get("max_discharge_power_mw")
        or battery_config.get("power_mw")
    )
    capacity_mwh = numeric(battery_config.get("capacity_mwh"))
    min_soc_mwh = numeric(battery_config.get("min_soc_mwh"))
    available_charge_power_mw = numeric(
        telemetry.get("available_charge_power_mw")
        or max_charge_power_mw
    )
    available_discharge_power_mw = numeric(
        telemetry.get("available_discharge_power_mw")
        or max_discharge_power_mw
    )
    grid_import_limit_mw = numeric(
        telemetry.get("grid_import_limit_mw")
        or grid_connection.get("max_import_mw")
        or grid_connection.get("connection_capacity_mw")
        or available_charge_power_mw
    )
    grid_export_limit_mw = numeric(
        telemetry.get("grid_export_limit_mw")
        or grid_connection.get("max_export_mw")
        or grid_connection.get("connection_capacity_mw")
        or available_discharge_power_mw
    )
    soc_mwh = numeric(telemetry.get("soc_mwh"))

    if soc_mwh <= 0 and capacity_mwh:
        soc_mwh = capacity_mwh * 0.5

    upward_energy_mwh = max(soc_mwh - min_soc_mwh, 0.0)
    downward_energy_mwh = max(capacity_mwh - soc_mwh, 0.0)
    available_symmetric_power_mw = min(
        available_charge_power_mw,
        available_discharge_power_mw,
        grid_import_limit_mw,
        grid_export_limit_mw,
        upward_energy_mwh / MINIMUM_FCR_DURATION_HOURS if upward_energy_mwh else 0.0,
        downward_energy_mwh / MINIMUM_FCR_DURATION_HOURS if downward_energy_mwh else 0.0,
    )

    return {
        "max_charge_power_mw": round(max_charge_power_mw, 4),
        "max_discharge_power_mw": round(max_discharge_power_mw, 4),
        "capacity_mwh": round(capacity_mwh, 4),
        "min_soc_mwh": round(min_soc_mwh, 4),
        "soc_mwh": round(soc_mwh, 4),
        "upward_energy_mwh": round(upward_energy_mwh, 4),
        "downward_energy_mwh": round(downward_energy_mwh, 4),
        "grid_import_limit_mw": round(grid_import_limit_mw, 4),
        "grid_export_limit_mw": round(grid_export_limit_mw, 4),
        "available_symmetric_power_mw": round(max(available_symmetric_power_mw, 0.0), 4),
    }


def build_fcr_capacity_bid(asset_id, capability, telemetry):
    capacity_mw = round_down_to_tenth(capability["available_symmetric_power_mw"])

    return {
        "reserve_bid_id": "fcr-preview-001",
        "asset_id": asset_id,
        "venue": "regelleistung.net",
        "product": "FCR_CAPACITY",
        "direction": "symmetric",
        "capacity_mw": capacity_mw,
        "minimum_duration_hours": MINIMUM_FCR_DURATION_HOURS,
        "availability_status": telemetry.get("availability_status", "not_connected"),
        "telemetry_provider": telemetry.get("provider"),
        "live_submission": False,
        "status": "preview",
    }


def validate_fcr_preview(capability, regulatory, telemetry):
    checks = [
        validate_minimum_power(capability),
        validate_symmetric_capability(capability),
        validate_duration(capability),
        validate_soc_reserve(capability),
        validate_prequalification(regulatory),
        validate_telemetry(telemetry),
        {
            "check": "live_submission",
            "status": "passed",
            "message": "Live FCR submission is disabled for preview mode.",
        },
    ]
    status = "blocked" if any(check["status"] == "blocked" for check in checks) else "passed"

    return {
        "status": status,
        "checks": checks,
    }


def validate_minimum_power(capability):
    power = capability["available_symmetric_power_mw"]

    return {
        "check": "minimum_power",
        "status": "passed" if power >= MINIMUM_FCR_POWER_MW else "blocked",
        "message": "Available symmetric power meets the FCR minimum."
        if power >= MINIMUM_FCR_POWER_MW
        else "Available symmetric power is below the FCR minimum.",
        "context": {
            "available_symmetric_power_mw": power,
            "minimum_power_mw": MINIMUM_FCR_POWER_MW,
        },
    }


def validate_symmetric_capability(capability):
    charge = capability["max_charge_power_mw"]
    discharge = capability["max_discharge_power_mw"]

    return {
        "check": "symmetric_capability",
        "status": "passed" if charge > 0 and discharge > 0 else "blocked",
        "message": "Asset has both charge and discharge capability."
        if charge > 0 and discharge > 0
        else "Asset lacks symmetric charge/discharge capability.",
        "context": {
            "max_charge_power_mw": charge,
            "max_discharge_power_mw": discharge,
        },
    }


def validate_duration(capability):
    power = capability["available_symmetric_power_mw"]
    upward_duration = capability["upward_energy_mwh"] / power if power else 0
    downward_duration = capability["downward_energy_mwh"] / power if power else 0
    duration_ok = (
        upward_duration >= MINIMUM_FCR_DURATION_HOURS
        and downward_duration >= MINIMUM_FCR_DURATION_HOURS
    )

    return {
        "check": "energy_duration",
        "status": "passed" if duration_ok else "blocked",
        "message": "SOC and energy capacity support the minimum FCR duration."
        if duration_ok
        else "SOC or energy capacity does not support the minimum FCR duration.",
        "context": {
            "upward_duration_hours": round(upward_duration, 4),
            "downward_duration_hours": round(downward_duration, 4),
            "minimum_duration_hours": MINIMUM_FCR_DURATION_HOURS,
        },
    }


def validate_soc_reserve(capability):
    soc = capability["soc_mwh"]
    min_soc = capability["min_soc_mwh"]
    capacity = capability["capacity_mwh"]
    soc_ok = min_soc < soc < capacity if capacity else False

    return {
        "check": "soc_reserve",
        "status": "passed" if soc_ok else "blocked",
        "message": "SOC leaves both upward and downward FCR reserve headroom."
        if soc_ok
        else "SOC does not leave enough reserve headroom.",
        "context": {
            "soc_mwh": soc,
            "min_soc_mwh": min_soc,
            "capacity_mwh": capacity,
        },
    }


def validate_prequalification(regulatory):
    prequalified = bool(regulatory.get("prequalified_fcr"))

    return {
        "check": "fcr_prequalification",
        "status": "passed" if prequalified else "blocked",
        "message": "Asset is marked as FCR prequalified."
        if prequalified
        else "FCR prequalification is missing.",
        "context": {
            "prequalified_fcr": prequalified,
        },
    }


def validate_telemetry(telemetry):
    available = telemetry.get("availability_status") == "available"

    return {
        "check": "telemetry",
        "status": "passed" if available else "blocked",
        "message": "Telemetry shows the asset is available for reserve delivery."
        if available
        else "Telemetry is missing or does not show the asset as available.",
        "context": {
            "availability_status": telemetry.get("availability_status"),
            "provider": telemetry.get("provider"),
        },
    }


def round_down_to_tenth(value):
    return int(max(value, 0.0) * 10) / 10



