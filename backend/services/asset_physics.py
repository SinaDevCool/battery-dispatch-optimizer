import csv
from pathlib import Path


def apply_asset_physics(asset, signal_result, forecast_file):
    if asset.asset_type == "solar_colocated_battery":
        return apply_solar_colocated_physics(asset, signal_result, forecast_file)

    if asset.asset_type == "industrial_behind_the_meter_battery":
        return apply_industrial_btm_physics(asset, signal_result, forecast_file)

    signal_result["asset_physics"] = {
        "physics_model": "merchant_grid_battery_v1",
        "constraints_applied": [
            "battery_capacity",
            "minimum_soc",
            "charge_power",
            "discharge_power",
            "grid_import_limit",
            "grid_export_limit",
        ],
        "message": "Grid-scale battery dispatch uses asset-specific SOC, power, efficiency, and grid connection limits.",
    }
    return signal_result


def apply_solar_colocated_physics(asset, signal_result, forecast_file):
    forecast_rows = forecast_rows_by_timestamp(forecast_file)
    dispatch = recompute_dispatch_rows(
        asset=asset,
        dispatch_rows=signal_result.get("dispatch", []),
        forecast_rows=forecast_rows,
        action_resolver=lambda row, forecast: row.get("action", "idle"),
        charge_limit_resolver=lambda row, forecast, timestep: max(
            numeric(forecast.get("forecast_solar_mw")) * timestep,
            0.0,
        ),
        discharge_limit_resolver=lambda row, forecast, timestep: max(
            numeric(forecast.get("site_export_limit_mw"))
            or numeric(asset.grid_connection.get("max_export_mw"))
            or numeric(asset.battery_config.get("max_discharge_power_mw")),
            0.0,
        )
        * timestep,
        row_enricher=build_solar_row_context,
    )
    signal_result["dispatch"] = dispatch
    signal_result["summary"] = build_dispatch_summary(dispatch, asset)
    signal_result["asset_physics"] = {
        "physics_model": "solar_colocated_battery_v1",
        "constraints_applied": [
            "battery_capacity",
            "minimum_soc",
            "charge_power",
            "discharge_power",
            "solar_generation_charge_limit",
            "renewable_origin_tracking",
            "site_export_limit",
        ],
        "message": "Solar co-located dispatch caps charge energy by the solar forecast and tags charged energy as renewable-origin mock data.",
    }
    return signal_result


def apply_industrial_btm_physics(asset, signal_result, forecast_file):
    forecast_rows = forecast_rows_by_timestamp(forecast_file)

    def action_resolver(row, forecast):
        site_load_mw = numeric(forecast.get("site_load_mw"))
        peak_limit_mw = numeric(forecast.get("site_peak_limit_mw"))
        if peak_limit_mw and site_load_mw > peak_limit_mw:
            return "discharge"
        return row.get("action", "idle")

    def charge_limit_resolver(row, forecast, timestep):
        site_load_mw = numeric(forecast.get("site_load_mw"))
        peak_limit_mw = numeric(forecast.get("site_peak_limit_mw"))
        grid_import_limit_mw = numeric(asset.grid_connection.get("max_import_mw"))
        import_cap_mw = min_nonzero(peak_limit_mw, grid_import_limit_mw)
        if not import_cap_mw:
            return numeric(asset.battery_config.get("max_charge_power_mw")) * timestep
        return max(import_cap_mw - site_load_mw, 0.0) * timestep

    def discharge_limit_resolver(row, forecast, timestep):
        site_load_mw = numeric(forecast.get("site_load_mw"))
        peak_limit_mw = numeric(forecast.get("site_peak_limit_mw"))
        peak_excess_mwh = max(site_load_mw - peak_limit_mw, 0.0) * timestep
        if peak_excess_mwh > 0:
            return peak_excess_mwh
        return max(site_load_mw, 0.0) * timestep

    dispatch = recompute_dispatch_rows(
        asset=asset,
        dispatch_rows=signal_result.get("dispatch", []),
        forecast_rows=forecast_rows,
        action_resolver=action_resolver,
        charge_limit_resolver=charge_limit_resolver,
        discharge_limit_resolver=discharge_limit_resolver,
        row_enricher=build_industrial_btm_row_context,
    )
    signal_result["dispatch"] = dispatch
    signal_result["summary"] = build_dispatch_summary(dispatch, asset)
    signal_result["asset_physics"] = {
        "physics_model": "industrial_btm_battery_v1",
        "constraints_applied": [
            "battery_capacity",
            "minimum_soc",
            "charge_power",
            "discharge_power",
            "site_import_headroom",
            "peak_shaving_discharge",
            "behind_the_meter_load_offset",
        ],
        "message": "Industrial BTM dispatch uses site load and peak-limit mock forecasts to charge within import headroom and discharge into site-load reduction.",
    }
    return signal_result


def recompute_dispatch_rows(
    asset,
    dispatch_rows,
    forecast_rows,
    action_resolver,
    charge_limit_resolver,
    discharge_limit_resolver,
    row_enricher,
):
    battery_config = asset.battery_config or {}
    commercial_config = asset.commercial_config or {}
    timestep = numeric(asset.strategy_config.get("timestep_hours")) or 1.0
    capacity_mwh = numeric(battery_config.get("capacity_mwh"))
    min_soc_mwh = numeric(battery_config.get("min_soc_mwh"))
    charge_power_mw = numeric(battery_config.get("max_charge_power_mw"))
    discharge_power_mw = numeric(battery_config.get("max_discharge_power_mw"))
    charge_efficiency = numeric(battery_config.get("charge_efficiency")) or 1.0
    discharge_efficiency = numeric(battery_config.get("discharge_efficiency")) or 1.0
    soc_mwh = numeric(battery_config.get("initial_soc_mwh"))
    total_pnl_eur = 0.0
    enriched_rows = []

    for row in dispatch_rows:
        forecast = forecast_rows.get(str(row.get("timestamp")), {})
        price = numeric(row.get("price"))
        action = action_resolver(row, forecast)
        grid_energy_mwh = 0.0
        battery_energy_mwh = 0.0
        market_value_eur = 0.0
        cost_eur = 0.0
        pnl_eur = 0.0

        if action == "charge":
            available_storage_mwh = max(capacity_mwh - soc_mwh, 0.0)
            max_grid_energy_mwh = min(
                charge_power_mw * timestep,
                max(charge_limit_resolver(row, forecast, timestep), 0.0),
            )
            max_battery_energy_mwh = max_grid_energy_mwh * charge_efficiency
            battery_energy_mwh = min(available_storage_mwh, max_battery_energy_mwh)
            if battery_energy_mwh > 0:
                grid_energy_mwh = battery_energy_mwh / charge_efficiency
                soc_mwh = min(soc_mwh + battery_energy_mwh, capacity_mwh)
                market_value_eur = -price * grid_energy_mwh
                cost_eur = charge_cost(commercial_config, grid_energy_mwh, battery_energy_mwh)
                pnl_eur = market_value_eur - cost_eur
            else:
                action = "idle"

        elif action == "discharge":
            available_battery_energy_mwh = max(soc_mwh - min_soc_mwh, 0.0)
            max_battery_energy_mwh = min(
                discharge_power_mw * timestep,
                max(discharge_limit_resolver(row, forecast, timestep) / discharge_efficiency, 0.0),
            )
            battery_energy_mwh = min(available_battery_energy_mwh, max_battery_energy_mwh)
            if battery_energy_mwh > 0:
                grid_energy_mwh = battery_energy_mwh * discharge_efficiency
                soc_mwh = max(soc_mwh - battery_energy_mwh, min_soc_mwh)
                market_value_eur = price * grid_energy_mwh
                cost_eur = discharge_cost(commercial_config, grid_energy_mwh, battery_energy_mwh)
                pnl_eur = market_value_eur - cost_eur
            else:
                action = "idle"

        total_pnl_eur += pnl_eur
        enriched = {
            **row,
            "action": action,
            "soc_mwh": round(soc_mwh, 4),
            "grid_energy_mwh": round(grid_energy_mwh, 4),
            "battery_energy_mwh": round(battery_energy_mwh, 4),
            "market_value_eur": round(market_value_eur, 2),
            "cost_eur": round(cost_eur, 2),
            "pnl_eur": round(pnl_eur, 2),
            "total_pnl_eur": round(total_pnl_eur, 2),
        }
        enriched.update(row_enricher(enriched, forecast, asset, timestep))
        enriched_rows.append(enriched)

    return enriched_rows


def build_solar_row_context(row, forecast, asset, timestep):
    solar_mw = numeric(forecast.get("forecast_solar_mw"))
    solar_available_mwh = solar_mw * timestep
    charge_input_mwh = row["grid_energy_mwh"] if row["action"] == "charge" else 0.0
    stored_charge_mwh = row["battery_energy_mwh"] if row["action"] == "charge" else 0.0
    renewable_charge_mwh = stored_charge_mwh if charge_input_mwh <= solar_available_mwh else 0.0
    grid_charge_mwh = max(charge_input_mwh - solar_available_mwh, 0.0)
    site_export_limit_mw = numeric(forecast.get("site_export_limit_mw"))

    return {
        "forecast_solar_mw": round(solar_mw, 4),
        "solar_available_mwh": round(solar_available_mwh, 4),
        "renewable_charge_mwh": round(renewable_charge_mwh, 4),
        "grid_charge_mwh": round(grid_charge_mwh, 4),
        "stored_energy_origin": "renewable" if renewable_charge_mwh else "none",
        "site_export_limit_mw": round(site_export_limit_mw, 4),
        "site_export_headroom_mwh": round(max(site_export_limit_mw * timestep - row["grid_energy_mwh"], 0.0), 4),
    }


def build_industrial_btm_row_context(row, forecast, asset, timestep):
    site_load_mw = numeric(forecast.get("site_load_mw"))
    peak_limit_mw = numeric(forecast.get("site_peak_limit_mw"))
    load_before_mwh = site_load_mw * timestep
    load_offset_mwh = row["grid_energy_mwh"] if row["action"] == "discharge" else 0.0
    battery_import_mwh = row["grid_energy_mwh"] if row["action"] == "charge" else 0.0
    net_site_import_mwh = max(load_before_mwh + battery_import_mwh - load_offset_mwh, 0.0)
    peak_excess_before_mwh = max(site_load_mw - peak_limit_mw, 0.0) * timestep
    peak_excess_after_mwh = max((net_site_import_mwh / timestep) - peak_limit_mw, 0.0) * timestep

    return {
        "site_load_mw": round(site_load_mw, 4),
        "site_peak_limit_mw": round(peak_limit_mw, 4),
        "load_before_battery_mwh": round(load_before_mwh, 4),
        "battery_site_load_offset_mwh": round(load_offset_mwh, 4),
        "battery_site_import_mwh": round(battery_import_mwh, 4),
        "net_site_import_mwh": round(net_site_import_mwh, 4),
        "peak_excess_before_mwh": round(peak_excess_before_mwh, 4),
        "peak_excess_after_mwh": round(peak_excess_after_mwh, 4),
        "peak_shaved_mwh": round(max(peak_excess_before_mwh - peak_excess_after_mwh, 0.0), 4),
    }


def build_dispatch_summary(dispatch, asset):
    active = [row for row in dispatch if row["action"] != "idle"]
    charge_rows = [row for row in dispatch if row["action"] == "charge"]
    discharge_rows = [row for row in dispatch if row["action"] == "discharge"]
    total_pnl_eur = sum(row["pnl_eur"] for row in dispatch)
    charged_mwh = sum(row["battery_energy_mwh"] for row in charge_rows)
    discharged_mwh = sum(row["battery_energy_mwh"] for row in discharge_rows)
    capacity_mwh = numeric(asset.battery_config.get("capacity_mwh"))
    renewable_charge_mwh = sum(row.get("renewable_charge_mwh", 0.0) for row in dispatch)
    peak_shaved_mwh = sum(row.get("peak_shaved_mwh", 0.0) for row in dispatch)

    summary = {
        "signal": "ACTION" if active else "NO_ACTION",
        "total_pnl_eur": round(total_pnl_eur, 2),
        "profit_per_mw_day": round(
            total_pnl_eur / max(numeric(asset.battery_config.get("max_discharge_power_mw")), 1.0),
            2,
        ),
        "opportunity_level": classify_opportunity(total_pnl_eur),
        "charge_hours": len(charge_rows),
        "discharge_hours": len(discharge_rows),
        "first_charge_timestamp": charge_rows[0]["timestamp"] if charge_rows else None,
        "first_discharge_timestamp": discharge_rows[0]["timestamp"] if discharge_rows else None,
        "charged_mwh": round(charged_mwh, 4),
        "discharged_mwh": round(discharged_mwh, 4),
        "throughput_mwh": round(charged_mwh + discharged_mwh, 4),
        "equivalent_full_cycles": round((charged_mwh + discharged_mwh) / max(capacity_mwh * 2, 1.0), 4),
    }

    if asset.asset_type == "solar_colocated_battery":
        summary["renewable_charge_mwh"] = round(renewable_charge_mwh, 4)
        summary["renewable_charge_share"] = round(
            renewable_charge_mwh / charged_mwh,
            4,
        ) if charged_mwh else 0.0
    if asset.asset_type == "industrial_behind_the_meter_battery":
        summary["peak_shaved_mwh"] = round(peak_shaved_mwh, 4)

    return summary


def forecast_rows_by_timestamp(forecast_file):
    with Path(forecast_file).open(newline="", encoding="utf-8-sig") as file:
        rows = list(csv.DictReader(file))

    return {str(row["timestamp"]): row for row in rows}


def charge_cost(commercial_config, grid_energy_mwh, battery_energy_mwh):
    variable_cost = (
        numeric(commercial_config.get("trading_fee_eur_per_mwh"))
        + numeric(commercial_config.get("market_access_fee_eur_per_mwh"))
        + numeric(commercial_config.get("grid_fee_import_eur_per_mwh"))
        + numeric(commercial_config.get("tax_or_levy_eur_per_mwh"))
    )
    degradation_cost = numeric(commercial_config.get("degradation_cost_eur_per_mwh_throughput"))
    return variable_cost * grid_energy_mwh + degradation_cost * battery_energy_mwh


def discharge_cost(commercial_config, grid_energy_mwh, battery_energy_mwh):
    variable_cost = (
        numeric(commercial_config.get("trading_fee_eur_per_mwh"))
        + numeric(commercial_config.get("market_access_fee_eur_per_mwh"))
        + numeric(commercial_config.get("grid_fee_export_eur_per_mwh"))
    )
    degradation_cost = numeric(commercial_config.get("degradation_cost_eur_per_mwh_throughput"))
    return variable_cost * grid_energy_mwh + degradation_cost * battery_energy_mwh


def classify_opportunity(total_pnl_eur):
    if total_pnl_eur >= 1000:
        return "high"
    if total_pnl_eur > 0:
        return "low"
    return "none"


def min_nonzero(*values):
    numeric_values = [numeric(value) for value in values if numeric(value) > 0]
    return min(numeric_values) if numeric_values else 0.0


def numeric(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0
