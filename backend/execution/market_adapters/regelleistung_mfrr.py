from datetime import datetime

from backend.execution.market_adapters.base import MarketAdapter
from backend.execution.pretrade_proposal import numeric


MINIMUM_MFRR_POWER_MW = 1.0
MINIMUM_MFRR_DURATION_HOURS = 1.0
DEFAULT_MFRR_ENERGY_RESERVATION_SHARE = 0.2


class RegelleistungMfrrAdapter(MarketAdapter):
    adapter_id = "regelleistung_mfrr"
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


def build_regelleistung_mfrr_preview(asset, telemetry=None, generated_at=None):
    generated_at = generated_at or datetime.now().isoformat(timespec="seconds")
    battery_config = asset.battery_config or {}
    grid_connection = asset.grid_connection or {}
    regulatory = asset.regulatory or {}
    commercial_config = asset.commercial_config or {}
    telemetry = telemetry or {}
    capability = build_mfrr_capability(
        battery_config=battery_config,
        grid_connection=grid_connection,
        telemetry=telemetry,
        commercial_config=commercial_config,
    )
    bids = build_mfrr_bid_set(asset_id=asset.asset_id, capability=capability, telemetry=telemetry)
    validation = validate_mfrr_preview(
        capability=capability,
        regulatory=regulatory,
        telemetry=telemetry,
    )
    status = "ready_for_prequalification_review" if validation["status"] == "passed" else "not_ready"

    return {
        "status": status,
        "adapter_id": RegelleistungMfrrAdapter.adapter_id,
        "adapter_name": "Regelleistung mFRR",
        "venue": "regelleistung.net",
        "market_segment": "balancing_capacity_energy",
        "product": "MFRR_CAPACITY_ENERGY",
        "bidding_zone": "DE_LU",
        "environment": "preview",
        "live_submission": False,
        "generated_at": generated_at,
        "summary": {
            "positive_capacity_mw": capability["positive_capacity_mw"],
            "negative_capacity_mw": capability["negative_capacity_mw"],
            "reserved_capacity_mw": capability["reserved_capacity_mw"],
            "energy_arbitrage_capacity_after_reserve_mw": capability[
                "energy_arbitrage_capacity_after_reserve_mw"
            ],
            "minimum_power_mw": MINIMUM_MFRR_POWER_MW,
            "minimum_duration_hours": MINIMUM_MFRR_DURATION_HOURS,
            "validation_status": validation["status"],
            "live_submission": False,
        },
        "capability": capability,
        "validation": validation,
        "bids": bids,
        "audit": [
            {
                "event": "regelleistung_mfrr_mapping",
                "actor": "regelleistung_mfrr_adapter",
                "status": validation["status"],
                "note": "Mapped asset capability into mFRR positive/negative capacity and activation-energy preview rows. Live submission is disabled.",
            }
        ],
    }


def build_mfrr_capability(
    battery_config,
    grid_connection,
    telemetry,
    commercial_config,
):
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
    soc_mwh = numeric(telemetry.get("soc_mwh"))

    if soc_mwh <= 0 and capacity_mwh:
        soc_mwh = capacity_mwh * 0.5

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
    upward_energy_mwh = max(soc_mwh - min_soc_mwh, 0.0)
    downward_energy_mwh = max(capacity_mwh - soc_mwh, 0.0)
    positive_capacity_mw = min(
        available_discharge_power_mw,
        grid_export_limit_mw,
        upward_energy_mwh / MINIMUM_MFRR_DURATION_HOURS if upward_energy_mwh else 0.0,
    )
    negative_capacity_mw = min(
        available_charge_power_mw,
        grid_import_limit_mw,
        downward_energy_mwh / MINIMUM_MFRR_DURATION_HOURS if downward_energy_mwh else 0.0,
    )
    reserve_share = numeric(
        commercial_config.get("mfrr_energy_reservation_share")
    ) or DEFAULT_MFRR_ENERGY_RESERVATION_SHARE
    reserved_capacity_mw = max(positive_capacity_mw, negative_capacity_mw) * reserve_share
    energy_arbitrage_capacity_after_reserve_mw = max(
        min(max_charge_power_mw, max_discharge_power_mw) - reserved_capacity_mw,
        0.0,
    )

    return {
        "max_charge_power_mw": round(max_charge_power_mw, 4),
        "max_discharge_power_mw": round(max_discharge_power_mw, 4),
        "capacity_mwh": round(capacity_mwh, 4),
        "min_soc_mwh": round(min_soc_mwh, 4),
        "soc_mwh": round(soc_mwh, 4),
        "upward_energy_mwh": round(upward_energy_mwh, 4),
        "downward_energy_mwh": round(downward_energy_mwh, 4),
        "positive_capacity_mw": round_down_to_tenth(positive_capacity_mw),
        "negative_capacity_mw": round_down_to_tenth(negative_capacity_mw),
        "reserved_capacity_mw": round(reserved_capacity_mw, 4),
        "energy_arbitrage_capacity_after_reserve_mw": round(
            energy_arbitrage_capacity_after_reserve_mw,
            4,
        ),
    }


def build_mfrr_bid_set(asset_id, capability, telemetry):
    positive_capacity = capability["positive_capacity_mw"]
    negative_capacity = capability["negative_capacity_mw"]

    return [
        build_mfrr_bid(
            asset_id=asset_id,
            bid_id="mfrr-pos-cap-preview-001",
            product="MFRR_CAPACITY_POSITIVE",
            direction="positive",
            capacity_mw=positive_capacity,
            telemetry=telemetry,
        ),
        build_mfrr_bid(
            asset_id=asset_id,
            bid_id="mfrr-neg-cap-preview-001",
            product="MFRR_CAPACITY_NEGATIVE",
            direction="negative",
            capacity_mw=negative_capacity,
            telemetry=telemetry,
        ),
        build_mfrr_activation_placeholder(
            asset_id=asset_id,
            bid_id="mfrr-pos-energy-placeholder-001",
            product="MFRR_ENERGY_POSITIVE",
            direction="positive",
            capacity_mw=positive_capacity,
            telemetry=telemetry,
        ),
        build_mfrr_activation_placeholder(
            asset_id=asset_id,
            bid_id="mfrr-neg-energy-placeholder-001",
            product="MFRR_ENERGY_NEGATIVE",
            direction="negative",
            capacity_mw=negative_capacity,
            telemetry=telemetry,
        ),
    ]


def build_mfrr_bid(asset_id, bid_id, product, direction, capacity_mw, telemetry):
    return {
        "reserve_bid_id": bid_id,
        "asset_id": asset_id,
        "venue": "regelleistung.net",
        "product": product,
        "direction": direction,
        "capacity_mw": capacity_mw,
        "minimum_duration_hours": MINIMUM_MFRR_DURATION_HOURS,
        "activation_mode": "manual",
        "availability_status": telemetry.get("availability_status", "not_connected"),
        "telemetry_provider": telemetry.get("provider"),
        "live_submission": False,
        "status": "preview" if capacity_mw > 0 else "not_available",
    }


def build_mfrr_activation_placeholder(asset_id, bid_id, product, direction, capacity_mw, telemetry):
    return {
        "reserve_bid_id": bid_id,
        "asset_id": asset_id,
        "venue": "regelleistung.net",
        "product": product,
        "direction": direction,
        "activation_energy_price_eur_mwh": None,
        "linked_capacity_mw": capacity_mw,
        "activation_mode": "manual",
        "activation_policy": "placeholder_requires_manual_activation_price_model",
        "availability_status": telemetry.get("availability_status", "not_connected"),
        "telemetry_provider": telemetry.get("provider"),
        "live_submission": False,
        "status": "placeholder",
    }


def validate_mfrr_preview(capability, regulatory, telemetry):
    checks = [
        validate_minimum_power(capability),
        validate_positive_capability(capability),
        validate_negative_capability(capability),
        validate_soc_headroom(capability),
        validate_prequalification(regulatory),
        validate_telemetry(telemetry),
        validate_activation_readiness(telemetry),
        validate_capacity_reservation(capability),
        {
            "check": "live_submission",
            "status": "passed",
            "message": "Live mFRR submission is disabled for preview mode.",
        },
    ]
    status = "blocked" if any(check["status"] == "blocked" for check in checks) else "passed"

    return {
        "status": status,
        "checks": checks,
    }


def validate_minimum_power(capability):
    positive = capability["positive_capacity_mw"]
    negative = capability["negative_capacity_mw"]
    ok = positive >= MINIMUM_MFRR_POWER_MW or negative >= MINIMUM_MFRR_POWER_MW

    return {
        "check": "minimum_power",
        "status": "passed" if ok else "blocked",
        "message": "At least one mFRR direction meets the minimum power requirement."
        if ok
        else "Neither mFRR direction meets the minimum power requirement.",
        "context": {
            "positive_capacity_mw": positive,
            "negative_capacity_mw": negative,
            "minimum_power_mw": MINIMUM_MFRR_POWER_MW,
        },
    }


def validate_positive_capability(capability):
    positive = capability["positive_capacity_mw"]

    return {
        "check": "positive_reserve_capability",
        "status": "passed" if positive >= MINIMUM_MFRR_POWER_MW else "review",
        "message": "Positive mFRR reserve capability is available."
        if positive >= MINIMUM_MFRR_POWER_MW
        else "Positive mFRR capability is below minimum and should be excluded or reviewed.",
        "context": {
            "positive_capacity_mw": positive,
        },
    }


def validate_negative_capability(capability):
    negative = capability["negative_capacity_mw"]

    return {
        "check": "negative_reserve_capability",
        "status": "passed" if negative >= MINIMUM_MFRR_POWER_MW else "review",
        "message": "Negative mFRR reserve capability is available."
        if negative >= MINIMUM_MFRR_POWER_MW
        else "Negative mFRR capability is below minimum and should be excluded or reviewed.",
        "context": {
            "negative_capacity_mw": negative,
        },
    }


def validate_soc_headroom(capability):
    has_upward = capability["upward_energy_mwh"] > 0
    has_downward = capability["downward_energy_mwh"] > 0

    return {
        "check": "soc_headroom",
        "status": "passed" if has_upward and has_downward else "blocked",
        "message": "SOC has headroom for positive and negative reserve activation."
        if has_upward and has_downward
        else "SOC headroom is insufficient for both mFRR directions.",
        "context": {
            "soc_mwh": capability["soc_mwh"],
            "upward_energy_mwh": capability["upward_energy_mwh"],
            "downward_energy_mwh": capability["downward_energy_mwh"],
        },
    }


def validate_prequalification(regulatory):
    prequalified = bool(regulatory.get("prequalified_mfrr"))

    return {
        "check": "mfrr_prequalification",
        "status": "passed" if prequalified else "blocked",
        "message": "Asset is marked as mFRR prequalified."
        if prequalified
        else "mFRR prequalification is missing.",
        "context": {
            "prequalified_mfrr": prequalified,
        },
    }


def validate_telemetry(telemetry):
    available = telemetry.get("availability_status") == "available"

    return {
        "check": "telemetry",
        "status": "passed" if available else "blocked",
        "message": "Telemetry shows the asset is available for mFRR delivery."
        if available
        else "Telemetry is missing or does not show the asset as available.",
        "context": {
            "availability_status": telemetry.get("availability_status"),
            "provider": telemetry.get("provider"),
        },
    }


def validate_activation_readiness(telemetry):
    ems_status = telemetry.get("ems_status")
    inverter_status = telemetry.get("inverter_status")
    ready = ems_status is not None and inverter_status == "available"

    return {
        "check": "manual_activation_readiness",
        "status": "passed" if ready else "review",
        "message": "Telemetry includes EMS/inverter evidence for manual activation readiness."
        if ready
        else "Manual activation readiness needs EMS and inverter evidence.",
        "context": {
            "ems_status": ems_status,
            "inverter_status": inverter_status,
        },
    }


def validate_capacity_reservation(capability):
    remaining = capability["energy_arbitrage_capacity_after_reserve_mw"]

    return {
        "check": "capacity_reservation",
        "status": "passed" if remaining > 0 else "review",
        "message": "Capacity reservation leaves residual power for energy-market participation."
        if remaining > 0
        else "mFRR reservation may consume all energy-market flexibility.",
        "context": {
            "reserved_capacity_mw": capability["reserved_capacity_mw"],
            "energy_arbitrage_capacity_after_reserve_mw": remaining,
        },
    }


def round_down_to_tenth(value):
    return int(max(value, 0.0) * 10) / 10



