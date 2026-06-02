DEFAULT_GRID_FEE_SCENARIOS = {
    "current_exempt": {
        "description": "Current local assumption with storage grid fees treated as exempt or zero.",
        "import_grid_fee_eur_per_mwh": 0.0,
        "export_grid_fee_eur_per_mwh": 0.0,
        "capacity_charge_eur_per_mw_year": 0.0,
        "construction_cost_contribution_eur_per_mw": 0.0,
        "dynamic_incentive_discount_percent": 0.0,
    },
    "post_2029_tariff": {
        "description": "Conservative future German storage tariff sensitivity after current exemption uncertainty.",
        "import_grid_fee_eur_per_mwh": 12.0,
        "export_grid_fee_eur_per_mwh": 0.0,
        "capacity_charge_eur_per_mw_year": 18000.0,
        "construction_cost_contribution_eur_per_mw": 0.0,
        "dynamic_incentive_discount_percent": 0.0,
    },
    "dynamic_grid_fee": {
        "description": "Network-beneficial operation with an incentive-style dynamic grid fee discount.",
        "import_grid_fee_eur_per_mwh": 12.0,
        "export_grid_fee_eur_per_mwh": 0.0,
        "capacity_charge_eur_per_mw_year": 18000.0,
        "construction_cost_contribution_eur_per_mw": 0.0,
        "dynamic_incentive_discount_percent": 35.0,
    },
    "full_grid_fee": {
        "description": "Downside case where storage pays a full import fee and annual capacity charge.",
        "import_grid_fee_eur_per_mwh": 35.0,
        "export_grid_fee_eur_per_mwh": 0.0,
        "capacity_charge_eur_per_mw_year": 30000.0,
        "construction_cost_contribution_eur_per_mw": 0.0,
        "dynamic_incentive_discount_percent": 0.0,
    },
}


def build_germany_grid_fee_sensitivity(asset, dispatch_rows=None):
    battery_config = asset.battery_config or {}
    commercial_config = asset.commercial_config or {}
    grid_connection = asset.grid_connection or {}

    import_mwh = calculate_import_mwh(dispatch_rows)
    export_mwh = calculate_export_mwh(dispatch_rows)
    power_mw = float(
        grid_connection.get("connection_capacity_mw")
        or battery_config.get("max_discharge_power_mw")
        or battery_config.get("power_mw")
        or 0.0
    )

    base_import_fee = float(commercial_config.get("grid_fee_import_eur_per_mwh", 0.0))
    base_export_fee = float(commercial_config.get("grid_fee_export_eur_per_mwh", 0.0))
    base_capacity_charge = float(
        commercial_config.get("capacity_charge_eur_per_mw_year", 0.0)
    )
    base_construction_cost = float(
        commercial_config.get("construction_cost_contribution_eur_per_mw", 0.0)
    )

    results = []

    for scenario_name, scenario in DEFAULT_GRID_FEE_SCENARIOS.items():
        merged = scenario.copy()

        if scenario_name == "current_exempt":
            merged["import_grid_fee_eur_per_mwh"] = base_import_fee
            merged["export_grid_fee_eur_per_mwh"] = base_export_fee
            merged["capacity_charge_eur_per_mw_year"] = base_capacity_charge
            merged["construction_cost_contribution_eur_per_mw"] = base_construction_cost

        results.append(
            calculate_grid_fee_scenario(
                scenario_name=scenario_name,
                scenario=merged,
                import_mwh=import_mwh,
                export_mwh=export_mwh,
                power_mw=power_mw,
            )
        )

    return {
        "status": "ok",
        "asset_id": asset.asset_id,
        "import_mwh": round(import_mwh, 4),
        "export_mwh": round(export_mwh, 4),
        "connection_power_mw": round(power_mw, 4),
        "scenarios": results,
    }


def calculate_grid_fee_scenario(scenario_name, scenario, import_mwh, export_mwh, power_mw):
    import_fee = float(scenario.get("import_grid_fee_eur_per_mwh", 0.0))
    export_fee = float(scenario.get("export_grid_fee_eur_per_mwh", 0.0))
    capacity_charge = float(scenario.get("capacity_charge_eur_per_mw_year", 0.0))
    construction_cost = float(
        scenario.get("construction_cost_contribution_eur_per_mw", 0.0)
    )
    discount_percent = float(scenario.get("dynamic_incentive_discount_percent", 0.0))

    energy_fee = import_mwh * import_fee + export_mwh * export_fee
    annual_capacity_cost = power_mw * capacity_charge
    construction_cost_total = power_mw * construction_cost
    discount = energy_fee * (discount_percent / 100.0)

    annualized_cost = energy_fee - discount + annual_capacity_cost

    return {
        "grid_fee_scenario": scenario_name,
        "description": scenario.get("description"),
        "import_grid_fee_eur_per_mwh": import_fee,
        "export_grid_fee_eur_per_mwh": export_fee,
        "capacity_charge_eur_per_mw_year": capacity_charge,
        "construction_cost_contribution_eur_per_mw": construction_cost,
        "dynamic_incentive_discount_percent": discount_percent,
        "energy_grid_fee_eur": round(energy_fee, 2),
        "dynamic_incentive_discount_eur": round(discount, 2),
        "annual_capacity_cost_eur": round(annual_capacity_cost, 2),
        "construction_cost_contribution_eur": round(construction_cost_total, 2),
        "annualized_grid_fee_cost_eur": round(annualized_cost, 2),
    }


def calculate_import_mwh(dispatch_rows):
    if not dispatch_rows:
        return 0.0

    total = 0.0

    for row in dispatch_rows:
        if row.get("action") == "charge":
            total += float(row.get("grid_energy_mwh", 0.0) or 0.0)

    return total


def calculate_export_mwh(dispatch_rows):
    if not dispatch_rows:
        return 0.0

    total = 0.0

    for row in dispatch_rows:
        if row.get("action") == "discharge":
            total += float(row.get("grid_energy_mwh", 0.0) or 0.0)

    return total
