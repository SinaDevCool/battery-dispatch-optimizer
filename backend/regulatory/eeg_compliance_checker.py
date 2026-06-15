from backend.regulatory.storage_classification import classify_storage_asset


def check_eeg_compliance(asset):
    classification = classify_storage_asset(asset)
    regulatory = asset.regulatory or {}

    findings = []
    actions = []

    if classification["uses_eeg_support"]:
        findings.append(
            "Asset is marked as using EEG support, so stored-energy origin and export treatment matter."
        )

    if classification["storage_mode"] == "pure_green_colocated":
        findings.append(
            "Pure green co-located storage is lower EEG risk if it does not charge from the grid."
        )

    if classification["storage_mode"] == "mixed_colocated":
        findings.append(
            "Mixed co-located storage can create EEG allocation risk when grid and renewable energy are both stored."
        )
        actions.append(
            "Implement metered or auditable energy-origin allocation before treating EEG-supported exports as eligible."
        )

    if classification["charges_from_grid"] and classification["exports_stored_renewable_power"]:
        actions.append(
            "Separate grid-charged and renewable-charged MWh in dispatch settlement and reporting."
        )

    if not regulatory.get("metering_concept"):
        actions.append(
            "Add metering_concept to asset regulatory config."
        )

    if not actions:
        actions.append("No immediate EEG compliance action flagged by the current assumptions.")

    return {
        "status": classification["status"],
        "asset_id": asset.asset_id,
        "eeg_support_risk": classification["eeg_support_risk"],
        "storage_classification": classification,
        "findings": findings,
        "recommended_actions": actions,
    }



