from dataclasses import dataclass
from pathlib import Path

from backend.assets.asset_loader import build_default_asset_from_client_config
from backend.config.paths import FORECAST_FILE
from backend.regulatory.germany_assumption_engine import build_germany_regulatory_assumptions
from backend.services.dispatch_service import optimize_dispatch_from_forecast_file
from backend.validation.dispatch_validator import validate_dispatch_signal


@dataclass
class AssetDispatchResult:
    asset: object
    forecast_file: Path
    dispatch_result: object
    constrained_battery_config: dict
    assumption_risk_flags: list[dict]


def dispatch_default_asset(
    forecast_file=FORECAST_FILE,
    optimizer_engine="rule_based_v1",
):
    asset = build_default_asset_from_client_config()

    return dispatch_asset(
        asset=asset,
        forecast_file=forecast_file,
        optimizer_engine=optimizer_engine,
    )


def dispatch_asset(
    asset,
    forecast_file=None,
    optimizer_engine="rule_based_v1",
):
    resolved_forecast_file = (
        Path(forecast_file)
        if forecast_file is not None
        else Path(asset.forecast_file) if asset.forecast_file else FORECAST_FILE
    )

    if not resolved_forecast_file.exists():
        raise FileNotFoundError(f"Forecast file not found: {resolved_forecast_file}")

    constrained_battery_config = apply_grid_connection_limits(
        asset.battery_config,
        asset.grid_connection,
    )

    dispatch_result = optimize_dispatch_from_forecast_file(
        forecast_file=resolved_forecast_file,
        battery_config=constrained_battery_config,
        strategy_config=asset.strategy_config,
        commercial_config=asset.commercial_config,
        optimizer_engine=optimizer_engine,
    )

    return AssetDispatchResult(
        asset=asset,
        forecast_file=resolved_forecast_file,
        dispatch_result=dispatch_result,
        constrained_battery_config=constrained_battery_config,
        assumption_risk_flags=build_asset_assumption_flags(asset),
    )


def build_asset_signal_metadata(asset_dispatch_result):
    asset = asset_dispatch_result.asset
    regulatory_assumptions = build_germany_regulatory_assumptions(asset).to_dict()

    return {
        "asset_id": asset.asset_id,
        "client_name": asset.client_name,
        "site_name": asset.site_name,
        "country": asset.country,
        "market": asset.market,
        "market_profile_id": asset.market_profile_id,
        "grid_connection": asset.grid_connection,
        "regulatory": asset.regulatory,
        "regulatory_assumptions": regulatory_assumptions,
        "constrained_battery_config": asset_dispatch_result.constrained_battery_config,
        "assumption_risk_flags": asset_dispatch_result.assumption_risk_flags,
    }


def add_asset_dispatch_validation(signal_result, asset_dispatch_result):
    validation_result = validate_dispatch_signal(
        signal_result=signal_result,
        battery_config=asset_dispatch_result.constrained_battery_config,
        strategy_config=asset_dispatch_result.asset.strategy_config,
        market_profile_id=asset_dispatch_result.asset.market_profile_id,
    )

    signal_result["validation"] = validation_result.to_dict()

    return signal_result


def apply_grid_connection_limits(battery_config, grid_connection):
    if not grid_connection:
        return battery_config

    constrained_config = battery_config.copy()

    max_import_mw = grid_connection.get("max_import_mw")
    max_export_mw = grid_connection.get("max_export_mw")
    connection_capacity_mw = grid_connection.get("connection_capacity_mw")

    if max_import_mw is not None:
        constrained_config["max_charge_power_mw"] = min(
            float(constrained_config["max_charge_power_mw"]),
            float(max_import_mw),
        )

    if max_export_mw is not None:
        constrained_config["max_discharge_power_mw"] = min(
            float(constrained_config["max_discharge_power_mw"]),
            float(max_export_mw),
        )

    if connection_capacity_mw is not None:
        constrained_config["max_charge_power_mw"] = min(
            float(constrained_config["max_charge_power_mw"]),
            float(connection_capacity_mw),
        )
        constrained_config["max_discharge_power_mw"] = min(
            float(constrained_config["max_discharge_power_mw"]),
            float(connection_capacity_mw),
        )

    return constrained_config


def build_asset_assumption_flags(asset):
    flags = []
    commercial_config = asset.commercial_config or {}
    grid_connection = asset.grid_connection or {}
    regulatory = asset.regulatory or {}

    if asset.market_profile_id != "de_lu_day_ahead":
        flags.append(
            {
                "level": "medium",
                "type": "missing_germany_market_profile",
                "message": "Asset is not explicitly assigned to the German DE-LU day-ahead market profile.",
            }
        )

    if not grid_connection:
        flags.append(
            {
                "level": "high",
                "type": "missing_grid_connection_limits",
                "message": "Grid import/export limits are missing for this asset.",
            }
        )

    if (
        commercial_config.get("grid_fee_import_eur_per_mwh", 0.0) == 0.0
        and commercial_config.get("grid_fee_export_eur_per_mwh", 0.0) == 0.0
    ):
        flags.append(
            {
                "level": "medium",
                "type": "grid_fee_assumption_zero",
                "message": "Grid import/export fees are set to zero; this should be reviewed for German commercial use.",
            }
        )

    if commercial_config.get("construction_cost_contribution_eur_per_mw", 0.0) == 0.0:
        flags.append(
            {
                "level": "medium",
                "type": "missing_bkz_assumption",
                "message": "Construction cost contribution/BKZ assumption is zero or missing.",
            }
        )

    if not regulatory.get("mastr_registered"):
        flags.append(
            {
                "level": "medium",
                "type": "missing_mastr_registration_status",
                "message": "MaStR registration is missing or marked false for this German storage asset.",
            }
        )

    if not regulatory.get("metering_concept"):
        flags.append(
            {
                "level": "medium",
                "type": "missing_metering_concept",
                "message": "Metering concept is missing; this matters for German storage settlement and mixed-use cases.",
            }
        )

    if not flags:
        flags.append(
            {
                "level": "info",
                "type": "asset_assumptions_complete",
                "message": "No major asset assumption gaps detected.",
            }
        )

    return flags



