import json
import os
from pathlib import Path

from fastapi import APIRouter

from src.api.common import file_status
from src.config.paths import (
    CLIENT_CONFIG_FILE,
    FORECAST_FILE,
    LATEST_SIGNAL_FILE,
    OUTPUT_DATA_DIR,
    SCENARIO_RESULTS_FILE,
)


router = APIRouter()


@router.get("/health")
def health_check():
    return {
        "status": "ok",
        "service": "battery-dispatch-optimizer",
    }


@router.get("/system/health")
def system_health():
    client_config_file = CLIENT_CONFIG_FILE
    forecast_file = FORECAST_FILE
    signal_file = LATEST_SIGNAL_FILE
    scenario_file = SCENARIO_RESULTS_FILE
    report_dir = OUTPUT_DATA_DIR

    report_files = []
    if report_dir.exists():
        report_files = sorted(report_dir.glob("monthly_report_*.html"))

    checks = {
        "api": True,
        "client_config": client_config_file.exists(),
        "forecast_file": forecast_file.exists(),
        "latest_signal": signal_file.exists(),
        "scenario_results": scenario_file.exists(),
        "monthly_report": len(report_files) > 0,
        "entsoe_token": bool(os.environ.get("ENTSOE_API_KEY")),
    }

    required_checks = [
        "api",
        "client_config",
        "forecast_file",
        "latest_signal",
    ]

    missing_required = [
        check_name
        for check_name in required_checks
        if not checks[check_name]
    ]

    status = "not_ready" if missing_required else "ready"

    return {
        "status": status,
        "checks": checks,
        "missing_required": missing_required,
    }


@router.get("/status")
def project_status():
    return {
        "status": "ok",
        "project": "battery-dispatch-optimizer",
        "version": "0.1.0",
        "available_endpoints": [
            "/health",
            "/system/health",
            "/status",
            "/data/status",
            "/data/update-entsoe",
            "/dashboard/summary",
            "/client/config",
            "/forecast/upload",
            "/forecast/status",
            "/forecast/preview",
            "/forecasts/compare-profitability",
            "/forecasts/compare-profitability/latest",
            "/features/forecast",
            "/forecast/demo",
            "/forecast/demo-high-spread",
            "/forecast/inhouse-placeholder",
            "/battery/optimizers",
            "/battery/config",
            "/battery/constraints",
            "/battery/signal",
            "/battery/signal/latest",
            "/battery/signal/latest/explanation",
            "/battery/signal/latest/risks",
            "/battery/signal/run-latest",
            "/battery/signal/history",
            "/battery/backtest",
            "/scenarios/run",
            "/scenarios/run-latest",
            "/scenarios/latest",
            "/stress/run-latest",
            "/stress/latest",
            "/reports/monthly/latest",
            "/reports/monthly/latest/view",
            "/workflow/run-daily",
        ],
    }


@router.get("/data/status")
def data_status():
    forecast_file = FORECAST_FILE
    signal_file = LATEST_SIGNAL_FILE
    scenario_file = SCENARIO_RESULTS_FILE
    report_dir = OUTPUT_DATA_DIR

    report_files = []
    if report_dir.exists():
        report_files = sorted(report_dir.glob("monthly_report_*.html"))

    latest_report = (
        report_files[-1]
        if report_files
        else Path("data/outputs/monthly_report_missing.html")
    )

    return {
        "status": "ok",
        "forecast_file": file_status(forecast_file),
        "latest_signal_file": file_status(signal_file),
        "scenario_file": file_status(scenario_file),
        "latest_monthly_report": file_status(latest_report),
    }


@router.get("/dashboard/summary")
def dashboard_summary():
    signal_file = LATEST_SIGNAL_FILE
    report_dir = OUTPUT_DATA_DIR

    latest_signal = None

    if signal_file.exists():
        with open(signal_file, "r", encoding="utf-8") as file:
            latest_signal = json.load(file)

    latest_report = None

    if report_dir.exists():
        report_files = sorted(report_dir.glob("monthly_report_*.html"))

        if report_files:
            latest_report = report_files[-1]

    if latest_signal is None:
        return {
            "status": "not_found",
            "message": "No latest battery signal found. Run scripts/run_daily_signal.py first.",
            "battery_signal": None,
            "latest_report_available": latest_report is not None,
            "latest_report_url": "/reports/monthly/latest/view" if latest_report else None,
        }

    summary = latest_signal["summary"]

    return {
        "status": "ok",
        "battery_signal": summary["signal"],
        "opportunity_level": summary["opportunity_level"],
        "total_pnl_eur": summary["total_pnl_eur"],
        "profit_per_mw_day": summary["profit_per_mw_day"],
        "charge_hours": summary["charge_hours"],
        "discharge_hours": summary["discharge_hours"],
        "first_charge_timestamp": summary["first_charge_timestamp"],
        "first_discharge_timestamp": summary["first_discharge_timestamp"],
        "latest_report_available": latest_report is not None,
        "latest_report_url": "/reports/monthly/latest/view" if latest_report else None,
    }
