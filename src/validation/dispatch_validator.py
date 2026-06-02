import math

import pandas as pd

from src.markets.market_profile_loader import get_market_profile
from src.validation.validation_result import ValidationResult


TOLERANCE = 1e-3


def validate_dispatch_signal(
    signal_result,
    battery_config,
    strategy_config=None,
    market_profile_id=None,
):
    errors = []
    warnings = []

    if strategy_config is None:
        strategy_config = {}

    dispatch_rows = signal_result.get("dispatch", [])
    summary = signal_result.get("summary", {})
    metadata = signal_result.get("metadata", {})

    if not dispatch_rows:
        warnings.append(
            build_issue(
                code="empty_dispatch",
                message="Dispatch contains no rows.",
            )
        )
        return build_validation_result(errors, warnings)

    validate_required_metadata(metadata, warnings)
    validate_required_dispatch_columns(dispatch_rows, errors)

    if errors:
        return build_validation_result(errors, warnings)

    validate_soc_limits(dispatch_rows, battery_config, errors)
    validate_power_limits(dispatch_rows, battery_config, strategy_config, errors)
    validate_actions(dispatch_rows, errors)
    validate_pnl_consistency(dispatch_rows, summary, errors, warnings)
    validate_market_interval(dispatch_rows, market_profile_id, warnings)

    return build_validation_result(errors, warnings)


def validate_required_metadata(metadata, warnings):
    required_keys = [
        "asset_id",
        "market_profile_id",
        "forecast_provider",
        "forecast_model",
    ]

    missing_keys = [
        key for key in required_keys
        if metadata.get(key) in [None, ""]
    ]

    if missing_keys:
        warnings.append(
            build_issue(
                code="missing_signal_metadata",
                message="Signal metadata is missing fields required for audit-grade traceability.",
                context={"missing_keys": missing_keys},
            )
        )


def validate_required_dispatch_columns(dispatch_rows, errors):
    required_columns = [
        "timestamp",
        "action",
        "soc_mwh",
        "grid_energy_mwh",
        "battery_energy_mwh",
        "pnl_eur",
        "total_pnl_eur",
    ]

    first_row = dispatch_rows[0]
    missing_columns = [
        column for column in required_columns
        if column not in first_row
    ]

    if missing_columns:
        errors.append(
            build_issue(
                code="missing_dispatch_columns",
                message="Dispatch rows are missing required validation columns.",
                context={"missing_columns": missing_columns},
            )
        )


def validate_soc_limits(dispatch_rows, battery_config, errors):
    min_soc_mwh = float(battery_config.get("min_soc_mwh", 0.0))
    capacity_mwh = float(battery_config.get("capacity_mwh", 0.0))

    for index, row in enumerate(dispatch_rows):
        soc_mwh = safe_float(row.get("soc_mwh"))

        if soc_mwh is None:
            errors.append(
                build_issue(
                    code="invalid_soc",
                    message="SOC value is missing or invalid.",
                    context={"row_index": index, "timestamp": row.get("timestamp")},
                )
            )
            continue

        if soc_mwh < min_soc_mwh - TOLERANCE:
            errors.append(
                build_issue(
                    code="soc_below_minimum",
                    message="Dispatch SOC is below the configured minimum SOC.",
                    context={
                        "row_index": index,
                        "timestamp": row.get("timestamp"),
                        "soc_mwh": soc_mwh,
                        "min_soc_mwh": min_soc_mwh,
                    },
                )
            )

        if soc_mwh > capacity_mwh + TOLERANCE:
            errors.append(
                build_issue(
                    code="soc_above_capacity",
                    message="Dispatch SOC is above configured battery capacity.",
                    context={
                        "row_index": index,
                        "timestamp": row.get("timestamp"),
                        "soc_mwh": soc_mwh,
                        "capacity_mwh": capacity_mwh,
                    },
                )
            )


def validate_power_limits(dispatch_rows, battery_config, strategy_config, errors):
    timestep_hours = float(strategy_config.get("timestep_hours", 1.0))
    max_charge_power_mw = float(battery_config.get("max_charge_power_mw", 0.0))
    max_discharge_power_mw = float(battery_config.get("max_discharge_power_mw", 0.0))

    max_charge_grid_energy_mwh = max_charge_power_mw * timestep_hours
    max_discharge_grid_energy_mwh = max_discharge_power_mw * timestep_hours

    for index, row in enumerate(dispatch_rows):
        action = row.get("action")
        grid_energy_mwh = safe_float(row.get("grid_energy_mwh"))

        if grid_energy_mwh is None:
            errors.append(
                build_issue(
                    code="invalid_grid_energy",
                    message="Grid energy value is missing or invalid.",
                    context={"row_index": index, "timestamp": row.get("timestamp")},
                )
            )
            continue

        if action == "charge" and grid_energy_mwh > max_charge_grid_energy_mwh + TOLERANCE:
            errors.append(
                build_issue(
                    code="charge_power_limit_exceeded",
                    message="Charge energy exceeds the configured charge power limit for one timestep.",
                    context={
                        "row_index": index,
                        "timestamp": row.get("timestamp"),
                        "grid_energy_mwh": grid_energy_mwh,
                        "limit_mwh": max_charge_grid_energy_mwh,
                    },
                )
            )

        if action == "discharge" and grid_energy_mwh > max_discharge_grid_energy_mwh + TOLERANCE:
            errors.append(
                build_issue(
                    code="discharge_power_limit_exceeded",
                    message="Discharge energy exceeds the configured discharge power limit for one timestep.",
                    context={
                        "row_index": index,
                        "timestamp": row.get("timestamp"),
                        "grid_energy_mwh": grid_energy_mwh,
                        "limit_mwh": max_discharge_grid_energy_mwh,
                    },
                )
            )


def validate_actions(dispatch_rows, errors):
    valid_actions = {"charge", "discharge", "idle"}

    for index, row in enumerate(dispatch_rows):
        action = row.get("action")

        if action not in valid_actions:
            errors.append(
                build_issue(
                    code="invalid_dispatch_action",
                    message="Dispatch action must be charge, discharge, or idle.",
                    context={
                        "row_index": index,
                        "timestamp": row.get("timestamp"),
                        "action": action,
                    },
                )
            )


def validate_pnl_consistency(dispatch_rows, summary, errors, warnings):
    pnl_sum = sum(
        safe_float(row.get("pnl_eur")) or 0.0
        for row in dispatch_rows
    )
    final_total_pnl = safe_float(dispatch_rows[-1].get("total_pnl_eur"))
    summary_total_pnl = safe_float(summary.get("total_pnl_eur"))

    if final_total_pnl is None:
        errors.append(
            build_issue(
                code="invalid_final_total_pnl",
                message="Final cumulative PnL is missing or invalid.",
            )
        )
        return

    if not math.isclose(pnl_sum, final_total_pnl, abs_tol=0.05):
        errors.append(
            build_issue(
                code="dispatch_pnl_sum_mismatch",
                message="Sum of dispatch row PnL does not match final cumulative PnL.",
                context={
                    "row_pnl_sum": round(pnl_sum, 4),
                    "final_total_pnl": final_total_pnl,
                },
            )
        )

    if summary_total_pnl is None:
        warnings.append(
            build_issue(
                code="missing_summary_total_pnl",
                message="Summary total PnL is missing or invalid.",
            )
        )
        return

    if not math.isclose(summary_total_pnl, final_total_pnl, abs_tol=0.05):
        errors.append(
            build_issue(
                code="summary_pnl_mismatch",
                message="Summary total PnL does not match dispatch final cumulative PnL.",
                context={
                    "summary_total_pnl": summary_total_pnl,
                    "final_total_pnl": final_total_pnl,
                },
            )
        )


def validate_market_interval(dispatch_rows, market_profile_id, warnings):
    if not market_profile_id:
        warnings.append(
            build_issue(
                code="missing_market_profile_id",
                message="Market profile id is missing; timestep consistency cannot be fully validated.",
            )
        )
        return

    try:
        market_profile = get_market_profile(market_profile_id)
    except ValueError:
        warnings.append(
            build_issue(
                code="unknown_market_profile",
                message="Market profile could not be loaded for timestep validation.",
                context={"market_profile_id": market_profile_id},
            )
        )
        return

    expected_minutes = int(market_profile.get("market_time_unit_minutes", 60))
    expected_intervals = int(market_profile.get("expected_intervals_per_day", 24))

    timestamps = pd.to_datetime(
        [row.get("timestamp") for row in dispatch_rows],
        errors="coerce",
    )

    invalid_timestamp_count = int(timestamps.isna().sum())

    if invalid_timestamp_count > 0:
        warnings.append(
            build_issue(
                code="invalid_dispatch_timestamps",
                message="Some dispatch timestamps could not be parsed.",
                context={"invalid_timestamp_count": invalid_timestamp_count},
            )
        )
        return

    if len(timestamps) >= 2:
        intervals = pd.Series(timestamps).diff().dropna()
        interval_minutes = intervals.dt.total_seconds() / 60
        unexpected_intervals = interval_minutes[
            abs(interval_minutes - expected_minutes) > TOLERANCE
        ]

        if not unexpected_intervals.empty:
            warnings.append(
                build_issue(
                    code="market_interval_mismatch",
                    message="Dispatch timestep does not consistently match the configured market interval.",
                    context={
                        "expected_minutes": expected_minutes,
                        "unexpected_interval_count": int(len(unexpected_intervals)),
                    },
                )
            )

    if len(dispatch_rows) != expected_intervals:
        warnings.append(
            build_issue(
                code="market_interval_count_mismatch",
                message="Dispatch row count does not match the expected full-day market interval count.",
                context={
                    "expected_intervals": expected_intervals,
                    "actual_intervals": len(dispatch_rows),
                },
            )
        )


def build_validation_result(errors, warnings):
    if errors:
        status = "fail"
    elif warnings:
        status = "warning"
    else:
        status = "pass"

    return ValidationResult(
        status=status,
        errors=errors,
        warnings=warnings,
    )


def build_issue(code, message, context=None):
    issue = {
        "code": code,
        "message": message,
    }

    if context:
        issue["context"] = context

    return issue


def safe_float(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
