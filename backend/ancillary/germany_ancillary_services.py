GERMANY_ANCILLARY_PRODUCTS = [
    {
        "product_id": "fcr",
        "name": "Frequency Containment Reserve",
        "symmetric": True,
        "minimum_duration_minutes": 60,
        "response_time_seconds": 30,
        "bsp_required": True,
    },
    {
        "product_id": "afrr_positive",
        "name": "Automatic Frequency Restoration Reserve positive",
        "symmetric": False,
        "minimum_duration_minutes": 60,
        "response_time_seconds": 300,
        "bsp_required": True,
    },
    {
        "product_id": "afrr_negative",
        "name": "Automatic Frequency Restoration Reserve negative",
        "symmetric": False,
        "minimum_duration_minutes": 60,
        "response_time_seconds": 300,
        "bsp_required": True,
    },
    {
        "product_id": "mfrr_positive",
        "name": "Manual Frequency Restoration Reserve positive",
        "symmetric": False,
        "minimum_duration_minutes": 240,
        "response_time_seconds": 750,
        "bsp_required": True,
    },
    {
        "product_id": "mfrr_negative",
        "name": "Manual Frequency Restoration Reserve negative",
        "symmetric": False,
        "minimum_duration_minutes": 240,
        "response_time_seconds": 750,
        "bsp_required": True,
    },
]


def assess_germany_ancillary_eligibility(asset):
    battery_config = asset.battery_config or {}
    regulatory = asset.regulatory or {}
    grid_connection = asset.grid_connection or {}

    capacity_mwh = float(
        battery_config.get("capacity_mwh")
        or battery_config.get("energy_mwh")
        or 0.0
    )
    discharge_power_mw = float(
        battery_config.get("max_discharge_power_mw")
        or battery_config.get("power_mw")
        or 0.0
    )
    charge_power_mw = float(
        battery_config.get("max_charge_power_mw")
        or battery_config.get("power_mw")
        or 0.0
    )

    duration_hours = capacity_mwh / discharge_power_mw if discharge_power_mw > 0 else 0.0
    prequalification_status = regulatory.get("ancillary_prequalification_status", "not_started")
    bsp_name = regulatory.get("balancing_service_provider")
    remote_control_ready = bool(regulatory.get("remote_control_ready", False))
    telemetry_ready = bool(regulatory.get("telemetry_ready", False))

    results = []

    for product in GERMANY_ANCILLARY_PRODUCTS:
        results.append(
            assess_product(
                product=product,
                capacity_mwh=capacity_mwh,
                charge_power_mw=charge_power_mw,
                discharge_power_mw=discharge_power_mw,
                duration_hours=duration_hours,
                prequalification_status=prequalification_status,
                bsp_name=bsp_name,
                remote_control_ready=remote_control_ready,
                telemetry_ready=telemetry_ready,
                grid_connection=grid_connection,
            )
        )

    eligible_count = len([result for result in results if result["eligible"]])

    return {
        "status": "ok",
        "asset_id": asset.asset_id,
        "duration_hours": round(duration_hours, 4),
        "prequalification_status": prequalification_status,
        "balancing_service_provider": bsp_name,
        "eligible_product_count": eligible_count,
        "products": results,
    }


def assess_product(
    product,
    capacity_mwh,
    charge_power_mw,
    discharge_power_mw,
    duration_hours,
    prequalification_status,
    bsp_name,
    remote_control_ready,
    telemetry_ready,
    grid_connection,
):
    blocking_reasons = []
    warnings = []

    minimum_duration_hours = product["minimum_duration_minutes"] / 60.0

    if discharge_power_mw <= 0 or charge_power_mw <= 0:
        blocking_reasons.append("Battery charge/discharge power must be configured.")

    if capacity_mwh <= 0:
        blocking_reasons.append("Battery capacity must be configured.")

    if duration_hours < minimum_duration_hours:
        blocking_reasons.append(
            f"Battery duration is below {minimum_duration_hours:.1f} h for {product['product_id']}."
        )

    if not bsp_name and product.get("bsp_required"):
        warnings.append("Balancing Service Provider is not configured.")

    if prequalification_status != "approved":
        warnings.append("Ancillary service prequalification is not approved.")

    if not remote_control_ready:
        warnings.append("Remote control readiness is not confirmed.")

    if not telemetry_ready:
        warnings.append("Telemetry readiness is not confirmed.")

    if not grid_connection:
        warnings.append("Grid connection limits are missing.")

    return {
        "product_id": product["product_id"],
        "name": product["name"],
        "symmetric": product["symmetric"],
        "minimum_duration_minutes": product["minimum_duration_minutes"],
        "response_time_seconds": product["response_time_seconds"],
        "bsp_required": product["bsp_required"],
        "eligible": len(blocking_reasons) == 0,
        "eligibility_status": "eligible" if len(blocking_reasons) == 0 else "blocked",
        "blocking_reasons": blocking_reasons,
        "review_warnings": warnings,
    }



