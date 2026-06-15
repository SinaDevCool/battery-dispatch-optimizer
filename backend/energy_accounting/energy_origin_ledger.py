from backend.regulatory.storage_classification import classify_storage_asset


def build_energy_origin_ledger(asset, dispatch_rows):
    classification = classify_storage_asset(asset)
    storage_mode = classification["storage_mode"]

    ledger_rows = []
    total_grid_charge_mwh = 0.0
    total_renewable_charge_mwh = 0.0
    total_mixed_discharge_mwh = 0.0
    total_green_discharge_mwh = 0.0

    renewable_share = infer_renewable_charge_share(classification)

    for row in dispatch_rows or []:
        action = row.get("action")
        battery_energy_mwh = float(row.get("battery_energy_mwh", 0.0) or 0.0)
        grid_energy_mwh = float(row.get("grid_energy_mwh", 0.0) or 0.0)

        charged_from_grid_mwh = 0.0
        charged_from_renewables_mwh = 0.0
        discharged_green_mwh = 0.0
        discharged_mixed_mwh = 0.0

        if action == "charge":
            charged_from_renewables_mwh = battery_energy_mwh * renewable_share
            charged_from_grid_mwh = battery_energy_mwh - charged_from_renewables_mwh
            total_grid_charge_mwh += charged_from_grid_mwh
            total_renewable_charge_mwh += charged_from_renewables_mwh

        if action == "discharge":
            if storage_mode == "pure_green_colocated":
                discharged_green_mwh = battery_energy_mwh
            elif storage_mode in ["mixed_colocated", "brown_colocated"]:
                discharged_mixed_mwh = battery_energy_mwh
            else:
                discharged_mixed_mwh = battery_energy_mwh

            total_green_discharge_mwh += discharged_green_mwh
            total_mixed_discharge_mwh += discharged_mixed_mwh

        ledger_rows.append(
            {
                "timestamp": row.get("timestamp"),
                "action": action,
                "battery_energy_mwh": round(battery_energy_mwh, 4),
                "grid_energy_mwh": round(grid_energy_mwh, 4),
                "charged_from_grid_mwh": round(charged_from_grid_mwh, 4),
                "charged_from_renewables_mwh": round(charged_from_renewables_mwh, 4),
                "discharged_green_mwh": round(discharged_green_mwh, 4),
                "discharged_mixed_mwh": round(discharged_mixed_mwh, 4),
                "storage_mode": storage_mode,
            }
        )

    return {
        "status": "ok",
        "asset_id": asset.asset_id,
        "storage_classification": classification,
        "summary": {
            "charged_from_grid_mwh": round(total_grid_charge_mwh, 4),
            "charged_from_renewables_mwh": round(total_renewable_charge_mwh, 4),
            "discharged_green_mwh": round(total_green_discharge_mwh, 4),
            "discharged_mixed_mwh": round(total_mixed_discharge_mwh, 4),
        },
        "ledger": ledger_rows,
    }


def infer_renewable_charge_share(classification):
    if classification["storage_mode"] == "pure_green_colocated":
        return 1.0

    if classification["storage_mode"] == "mixed_colocated":
        return 0.5

    if classification["charges_from_renewables"] and not classification["charges_from_grid"]:
        return 1.0

    return 0.0



