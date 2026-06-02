PURE_GREEN_STORAGE = "pure_green_colocated"
MIXED_COLOCATED_STORAGE = "mixed_colocated"
STANDALONE_GRID_STORAGE = "standalone_grid_connected"
BROWN_COLOCATED_STORAGE = "brown_colocated"
UNKNOWN_STORAGE = "unknown"


def classify_storage_asset(asset):
    regulatory = asset.regulatory or {}
    grid_connection = asset.grid_connection or {}

    charges_from_grid = bool(regulatory.get("charges_from_grid", True))
    charges_from_renewables = bool(regulatory.get("charges_from_renewables", False))
    uses_eeg_support = bool(regulatory.get("uses_eeg_support", False))
    exports_stored_renewable_power = bool(
        regulatory.get("exports_stored_renewable_power", False)
    )
    colocated_generation_type = regulatory.get("colocated_generation_type")
    is_colocated = bool(
        regulatory.get("is_colocated", False)
        or colocated_generation_type
        or charges_from_renewables
    )

    storage_mode = regulatory.get("storage_mode")

    if not storage_mode:
        if not is_colocated:
            storage_mode = STANDALONE_GRID_STORAGE
        elif charges_from_renewables and not charges_from_grid:
            storage_mode = PURE_GREEN_STORAGE
        elif charges_from_renewables and charges_from_grid:
            storage_mode = MIXED_COLOCATED_STORAGE
        elif is_colocated and not charges_from_renewables:
            storage_mode = BROWN_COLOCATED_STORAGE
        else:
            storage_mode = UNKNOWN_STORAGE

    warnings = []

    if uses_eeg_support and charges_from_grid and exports_stored_renewable_power:
        warnings.append(
            build_warning(
                "eeg_support_mixing_risk",
                "high",
                "Storage exports may mix grid electricity with EEG-supported renewable electricity.",
            )
        )

    if uses_eeg_support and storage_mode == MIXED_COLOCATED_STORAGE:
        warnings.append(
            build_warning(
                "mixed_storage_eeg_review_required",
                "high",
                "Mixed co-located storage with EEG support requires explicit metering and allocation review.",
            )
        )

    if storage_mode == PURE_GREEN_STORAGE and charges_from_grid:
        warnings.append(
            build_warning(
                "pure_green_inconsistent_grid_charging",
                "high",
                "Storage is marked pure green but grid charging is enabled.",
            )
        )

    if is_colocated and not regulatory.get("metering_concept"):
        warnings.append(
            build_warning(
                "colocation_metering_missing",
                "high",
                "Co-located storage requires a clear metering concept for settlement and energy-origin separation.",
            )
        )

    if not grid_connection:
        warnings.append(
            build_warning(
                "grid_connection_missing",
                "medium",
                "Grid connection data is missing, so operating mode cannot be fully validated.",
            )
        )

    eeg_support_risk = classify_eeg_support_risk(
        storage_mode=storage_mode,
        uses_eeg_support=uses_eeg_support,
        charges_from_grid=charges_from_grid,
        exports_stored_renewable_power=exports_stored_renewable_power,
        warnings=warnings,
    )

    return {
        "status": classify_status(warnings),
        "asset_id": asset.asset_id,
        "storage_mode": storage_mode,
        "is_colocated": is_colocated,
        "colocated_generation_type": colocated_generation_type,
        "charges_from_grid": charges_from_grid,
        "charges_from_renewables": charges_from_renewables,
        "exports_stored_renewable_power": exports_stored_renewable_power,
        "uses_eeg_support": uses_eeg_support,
        "eeg_support_risk": eeg_support_risk,
        "metering_concept": regulatory.get("metering_concept"),
        "warnings": warnings,
    }


def classify_eeg_support_risk(
    storage_mode,
    uses_eeg_support,
    charges_from_grid,
    exports_stored_renewable_power,
    warnings,
):
    severities = [warning["severity"] for warning in warnings]

    if "high" in severities:
        return "high"

    if not uses_eeg_support:
        return "low"

    if storage_mode == PURE_GREEN_STORAGE and not charges_from_grid:
        return "low"

    if charges_from_grid or exports_stored_renewable_power:
        return "medium"

    return "medium"


def classify_status(warnings):
    severities = [warning["severity"] for warning in warnings]

    if "high" in severities:
        return "high_risk"

    if "medium" in severities:
        return "needs_review"

    return "ready"


def build_warning(code, severity, message):
    return {
        "code": code,
        "severity": severity,
        "message": message,
    }
