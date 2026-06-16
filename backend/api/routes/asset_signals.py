from datetime import datetime

from fastapi import APIRouter

from backend.api.schemas import AssetSignalRunResponse, LatestSignalResponse
from backend.assets.asset_loader import get_asset
from backend.services.asset_dispatch_service import (
    add_asset_dispatch_validation,
    build_asset_signal_metadata,
    dispatch_asset,
)
from backend.services.asset_signal_store import (
    list_asset_signal_history,
    load_asset_latest_signal,
    load_asset_signal_run,
    save_asset_signal,
)
from backend.services.asset_provenance import attach_asset_provenance
from backend.services.signal_service import add_signal_metadata


router = APIRouter()


@router.post(
    "/assets/{asset_id}/signal/run-latest",
    response_model=AssetSignalRunResponse,
)
def run_asset_latest_signal(asset_id: str, optimizer_engine: str = "rule_based_v1"):
    try:
        asset = get_asset(asset_id)
        asset_dispatch_result = dispatch_asset(
            asset=asset,
            optimizer_engine=optimizer_engine,
        )
    except ValueError as error:
        return {
            "status": "not_found",
            "message": str(error),
        }
    except FileNotFoundError as error:
        return {
            "status": "not_found",
            "message": str(error),
        }
    except Exception as error:
        return {
            "status": "error",
            "message": f"Could not generate asset signal: {error}",
        }

    dispatch_result = asset_dispatch_result.dispatch_result
    generated_at = datetime.now()

    signal_result = add_signal_metadata(
        signal_result=dispatch_result.signal_result,
        source="asset_forecast_file",
        forecast_model="asset_forecast_file",
        target_date=None,
        forecast_file=asset_dispatch_result.forecast_file,
        generated_at=generated_at,
        extra_metadata=build_asset_signal_metadata(asset_dispatch_result),
    )
    signal_result = add_asset_dispatch_validation(
        signal_result=signal_result,
        asset_dispatch_result=asset_dispatch_result,
    )

    saved_files = save_asset_signal(
        signal_result=signal_result,
        asset_id=asset_id,
    )

    response = {
        "status": "ok",
        "message": "Asset battery signal generated successfully.",
        "asset_id": asset_id,
        "optimizer_engine": dispatch_result.optimizer_engine,
        "asset_latest_signal_file": str(saved_files["asset_latest_signal_file"]),
        "asset_run_file": str(saved_files["asset_run_file"]),
        "signal_id": saved_files["signal_id"],
        "assumption_risk_flags": asset_dispatch_result.assumption_risk_flags,
        "validation": signal_result["validation"],
        "data": signal_result,
    }
    return attach_asset_provenance(
        response,
        asset,
        artifact=str(saved_files["asset_latest_signal_file"]),
        kind="signal_run",
        source_file=asset_dispatch_result.forecast_file,
        extra={"optimizer_engine": dispatch_result.optimizer_engine},
    )


@router.get("/assets/{asset_id}/signal/latest", response_model=LatestSignalResponse)
def latest_asset_signal(asset_id: str):
    signal = load_asset_latest_signal(asset_id)
    return enrich_signal_with_proof(asset_id=asset_id, signal=signal)


@router.get("/assets/{asset_id}/signal/history")
def asset_signal_history(asset_id: str):
    return list_asset_signal_history(asset_id)


@router.get("/assets/{asset_id}/signal/history/{file_name}")
def asset_signal_history_run(asset_id: str, file_name: str):
    return load_asset_signal_run(asset_id, file_name)


def enrich_signal_with_proof(asset_id: str, signal: dict):
    if not isinstance(signal, dict):
        return signal
    try:
        asset = get_asset(asset_id)
    except Exception:
        asset = {}

    signal_data = signal.get("data") or {}
    asset_dict = asset.to_dict() if hasattr(asset, "to_dict") else asset
    signal["dispatch_proof"] = build_dispatch_proof(asset=asset_dict, signal_data=signal_data)
    signal["signal_proof"] = build_signal_proof(asset=asset_dict, signal=signal, signal_data=signal_data)
    return attach_asset_provenance(
        signal,
        asset,
        artifact=signal.get("signal_file"),
        generated_at=(signal_data.get("metadata") or {}).get("generated_at"),
        kind="latest_signal",
        source_file=(signal_data.get("metadata") or {}).get("forecast_file"),
    )


def build_dispatch_proof(asset: dict, signal_data: dict):
    summary = signal_data.get("summary") or {}
    asset_physics = signal_data.get("asset_physics") or {}
    validation = signal_data.get("validation") or {}
    asset_type = asset.get("asset_type")
    rows = [
        {
            "physical_feature": "Validation status",
            "value": validation.get("status") or "-",
            "investor_meaning": (
                "The mock dispatch passes SOC, power, PnL, and market-interval checks."
                if validation.get("status") == "pass"
                else "Run or refresh the dispatch signal before relying on the physical proof."
            ),
        },
        {
            "physical_feature": "Validation issues",
            "value": f"{validation.get('error_count', '-')} error(s) / {validation.get('warning_count', '-')} warning(s)",
            "investor_meaning": "Keeps mock evidence honest by showing whether physical constraints or data intervals failed validation.",
        },
        {
            "physical_feature": "Physics model",
            "value": format_label(asset_physics.get("physics_model")),
            "investor_meaning": asset_physics.get("message")
            or "Dispatch physical model will appear after the selected asset signal is generated.",
        },
        {
            "physical_feature": "Applied constraints",
            "value": ", ".join(
                format_label(value) for value in asset_physics.get("constraints_applied") or []
            )
            or "-",
            "investor_meaning": "Shows which physical limits shaped the mock dispatch, beyond UI labels.",
        },
    ]

    if asset_type == "solar_colocated_battery":
        rows.append(
            {
                "physical_feature": "Renewable-origin charge",
                "value": f"{format_number(summary.get('renewable_charge_mwh'), 2)} MWh / {format_number(numeric(summary.get('renewable_charge_share')) * 100, 1)}%",
                "investor_meaning": "Confirms the solar demo charges from forecast solar energy instead of generic grid arbitrage.",
            }
        )

    if asset_type == "industrial_behind_the_meter_battery":
        rows.append(
            {
                "physical_feature": "Peak shaved",
                "value": f"{format_number(summary.get('peak_shaved_mwh'), 2)} MWh",
                "investor_meaning": "Confirms the industrial demo uses site load and peak limits, not only merchant price spread.",
            }
        )

    return {"rows": rows}


def build_signal_proof(asset: dict, signal: dict, signal_data: dict):
    summary = signal_data.get("summary") or {}
    dispatch = signal_data.get("dispatch") or []
    metadata = signal_data.get("metadata") or {}
    asset_type = asset.get("asset_type")
    active_intervals = len([row for row in dispatch if row.get("action") != "idle"])
    physics_model = (signal_data.get("asset_physics") or {}).get("physics_model")
    signal_value = summary.get("signal") or "-"

    if asset_type == "solar_colocated_battery":
        kpis = [
            {
                "accent": "emerald",
                "helper": "Renewable-origin charge is carried into signal evidence.",
                "label": "Green charge",
                "value": f"{format_number(summary.get('renewable_charge_mwh'), 1)} MWh",
            },
            {
                "accent": "blue",
                "helper": "Signal uses the selected solar co-located mock profile.",
                "label": "Signal",
                "value": signal_value,
            },
            {
                "accent": "emerald" if active_intervals else "amber",
                "helper": "Intervals available for dispatch-to-order conversion.",
                "label": "Active intervals",
                "value": active_intervals,
            },
        ]
        rows = [
            {
                "signal_driver": "Renewable-origin signal",
                "mock_evidence": f"{format_number(summary.get('renewable_charge_mwh'), 1)} MWh renewable charge / {format_percent(summary.get('renewable_charge_share'))} green charge share",
                "investor_meaning": "The market signal is tied to solar-origin dispatch evidence.",
                "production_upgrade": "Connect generation meter, renewable-origin accounting, and production forecast data.",
            },
            {
                "signal_driver": "Solar export envelope",
                "mock_evidence": f"{format_energy(sum_rows(dispatch, 'site_export_headroom_mwh'))} export headroom / {format_energy(sum_rows(dispatch, 'solar_available_mwh'))} solar available",
                "investor_meaning": "Signal readiness respects site export constraints before order generation.",
                "production_upgrade": "Use live inverter limits, DSO export constraints, and metered solar generation.",
            },
            {
                "signal_driver": "Forecast-to-action trace",
                "mock_evidence": f"{metadata.get('forecast_file') or '-'} / {active_intervals} active interval(s)",
                "investor_meaning": "The investor can trace which forecast produced the trading signal.",
                "production_upgrade": "Persist forecast snapshot IDs, actuals comparison, and model confidence evidence.",
            },
        ]
    elif asset_type == "industrial_behind_the_meter_battery":
        kpis = [
            {
                "accent": "emerald",
                "helper": "Site-load reduction carried into signal evidence.",
                "label": "Peak shaved",
                "value": f"{format_number(summary.get('peak_shaved_mwh'), 1)} MWh",
            },
            {
                "accent": "blue",
                "helper": "Intervals available for dispatch-to-order conversion.",
                "label": "Active intervals",
                "value": active_intervals,
            },
            {
                "accent": "emerald" if signal_value == "ACTION" else "amber",
                "helper": "Latest optimizer recommendation.",
                "label": "Signal",
                "value": signal_value,
            },
        ]
        rows = [
            {
                "signal_driver": "Site-load signal",
                "mock_evidence": f"{format_energy(summary.get('peak_shaved_mwh') or sum_rows(dispatch, 'peak_shaved_mwh'))} peak shaved / {format_energy(sum_rows(dispatch, 'battery_site_load_offset_mwh'))} load offset",
                "investor_meaning": "The signal is grounded in industrial site value, not only external market spread.",
                "production_upgrade": "Connect site meter telemetry, tariff model, and load forecast evidence.",
            },
            {
                "signal_driver": "Connection-limit guard",
                "mock_evidence": f"{format_energy(sum_rows(dispatch, 'peak_excess_before_mwh'))} peak excess before / {format_energy(sum_rows(dispatch, 'peak_excess_after_mwh'))} after battery",
                "investor_meaning": "The signal demonstrates whether the battery reduces site import stress.",
                "production_upgrade": "Use live DSO capacity terms, site demand, and operational constraints.",
            },
            {
                "signal_driver": "Forecast-to-action trace",
                "mock_evidence": f"{metadata.get('forecast_file') or '-'} / {active_intervals} active interval(s) / {format_label(physics_model)}",
                "investor_meaning": "The investor can trace which forecast and physics model produced the signal.",
                "production_upgrade": "Persist forecast snapshot IDs, actuals comparison, and model confidence evidence.",
            },
        ]
    else:
        throughput = get_dispatch_throughput(summary, dispatch)
        kpis = [
            {
                "accent": "emerald" if signal_value == "ACTION" else "amber",
                "helper": "Latest optimizer recommendation.",
                "label": "Signal",
                "value": signal_value,
            },
            {
                "accent": "blue",
                "helper": "Physical movement behind the signal.",
                "label": "Throughput",
                "value": format_energy(throughput),
            },
            {
                "accent": "emerald" if active_intervals else "amber",
                "helper": "Intervals available for dispatch-to-order conversion.",
                "label": "Active intervals",
                "value": active_intervals,
            },
        ]
        rows = [
            {
                "signal_driver": "Physical dispatch movement",
                "mock_evidence": f"{format_energy(summary.get('charged_mwh'))} charged / {format_energy(summary.get('discharged_mwh'))} discharged / {format_energy(throughput)} throughput",
                "investor_meaning": "The signal is backed by physical battery movement, not static labels.",
                "production_upgrade": "Connect live EMS SOC, availability, and meter telemetry.",
            },
            {
                "signal_driver": "Forecast-to-action trace",
                "mock_evidence": f"{metadata.get('forecast_file') or '-'} / {active_intervals} active interval(s)",
                "investor_meaning": "The investor can trace which forecast produced the trading signal.",
                "production_upgrade": "Persist forecast snapshot IDs, actuals comparison, and model confidence evidence.",
            },
            {
                "signal_driver": "Physics model",
                "mock_evidence": format_label(physics_model),
                "investor_meaning": "The signal should reflect battery constraints before revenue or execution can trust it.",
                "production_upgrade": "Connect EMS telemetry, degradation model, and validated dispatch records.",
            },
        ]

    return {"kpis": kpis, "rows": rows}


def sum_rows(rows: list[dict], key: str):
    total = 0.0
    for row in rows:
        try:
            total += float(row.get(key) or 0)
        except (TypeError, ValueError):
            continue
    return total


def get_dispatch_throughput(summary: dict, rows: list[dict]):
    throughput = numeric(summary.get("throughput_mwh"))
    if throughput > 0:
        return throughput
    charged = numeric(summary.get("charged_mwh"))
    discharged = numeric(summary.get("discharged_mwh"))
    if charged > 0 or discharged > 0:
        return charged + discharged
    return sum(abs(numeric(row.get("grid_energy_mwh"))) for row in rows)


def numeric(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def format_number(value, digits=1):
    try:
        numeric_value = float(value)
    except (TypeError, ValueError):
        return "-"
    return f"{numeric_value:,.{digits}f}"


def format_energy(value):
    try:
        numeric_value = float(value)
    except (TypeError, ValueError):
        return "-"
    return f"{numeric_value:,.1f} MWh"


def format_percent(value):
    try:
        numeric_value = float(value)
    except (TypeError, ValueError):
        return "-"
    percent = numeric_value * 100 if numeric_value <= 1 else numeric_value
    return f"{percent:,.0f}%"


def format_label(value):
    if not value:
        return "-"
    return " ".join(part.capitalize() for part in str(value).split("_") if part)



