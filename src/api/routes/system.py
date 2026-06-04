import json
import os
from pathlib import Path

from fastapi import APIRouter

from src.api.common import file_status
from src.api.schemas import DataStatusResponse, HealthResponse
from src.config.app_settings import get_app_settings
from src.config.paths import (
    ACTUAL_PRICE_FILE,
    CLIENT_CONFIG_FILE,
    FORECAST_FILE,
    LATEST_SIGNAL_FILE,
    OUTPUT_DATA_DIR,
    SCENARIO_RESULTS_FILE,
)


router = APIRouter()


@router.get("/health", response_model=HealthResponse)
def health_check():
    settings = get_app_settings()

    return {
        "status": "ok",
        "service": settings.service_name,
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
    settings = get_app_settings()

    return {
        "status": "ok",
        "project": "battery-dispatch-optimizer",
        "version": "0.1.0",
        "environment": settings.environment,
        "storage_backend": settings.storage_backend,
        "auth_mode": settings.auth_mode,
        "available_endpoints": [
            "/health",
            "/system/health",
            "/status",
            "/data/status",
            "/data/update-entsoe",
            "/data/update-actual-prices",
            "/data/actual-prices/status",
            "/dashboard/summary",
            "/assets",
            "/assets/{asset_id}/signal/run-latest",
            "/assets/{asset_id}/signal/latest",
            "/assets/{asset_id}/signal/history",
            "/assets/{asset_id}/signal/history/{file_name}",
            "/portfolio/run-daily",
            "/portfolio/latest",
            "/markets",
            "/markets/{market_profile_id}",
            "/markets/products",
            "/markets/products/{product_id}",
            "/assets/{asset_id}/eligible-products",
            "/assets/{asset_id}/revenue-stack/run",
            "/assets/{asset_id}/revenue-stack/latest",
            "/assets/{asset_id}/revenue-stack/allocate",
            "/assets/{asset_id}/revenue-stack/allocation/latest",
            "/assets/{asset_id}/signals",
            "/assets/{asset_id}/signals/{signal_id}",
            "/assets/{asset_id}/revenue-stack/runs",
            "/assets/{asset_id}/revenue-stack/runs/{revenue_stack_id}",
            "/backtesting/forecast-actual/run",
            "/backtesting/forecast-actual/latest",
            "/assets/{asset_id}/forecast-performance",
            "/assets/{asset_id}/forecast-performance/{forecast_actual_id}",
            "/assets/{asset_id}/forecast-confidence",
            "/regulatory/germany/requirements",
            "/assets/{asset_id}/regulatory/germany",
            "/assets/{asset_id}/storage-classification",
            "/assets/{asset_id}/eeg-compliance/latest",
            "/assets/{asset_id}/ancillary/germany/eligibility",
            "/assets/{asset_id}/grid-fees/germany/sensitivity",
            "/assets/{asset_id}/energy-origin/latest",
            "/assets/{asset_id}/hedging/revenue",
            "/assets/{asset_id}/telemetry/demo",
            "/assets/{asset_id}/telemetry/latest",
            "/assets/{asset_id}/telemetry/history",
            "/execution/market-adapters",
            "/assets/{asset_id}/execution/market-adapter/status",
            "/assets/{asset_id}/execution/multi-market/allocation",
            "/assets/{asset_id}/execution/epex/day-ahead/preview",
            "/assets/{asset_id}/execution/epex/intraday-auction/preview",
            "/assets/{asset_id}/execution/epex/intraday-continuous/preview",
            "/assets/{asset_id}/execution/regelleistung/fcr/preview",
            "/assets/{asset_id}/execution/regelleistung/afrr/preview",
            "/assets/{asset_id}/execution/regelleistung/mfrr/preview",
            "/assets/{asset_id}/execution/automation-guardrails",
            "/assets/{asset_id}/execution/readiness",
            "/assets/{asset_id}/execution/demo-submit",
            "/assets/{asset_id}/execution/submissions/latest",
            "/assets/{asset_id}/execution/submissions",
            "/assets/{asset_id}/execution/approval/request",
            "/assets/{asset_id}/execution/approval/approve",
            "/assets/{asset_id}/execution/approval/reject",
            "/assets/{asset_id}/execution/approval/latest",
            "/assets/{asset_id}/execution/approvals",
            "/assets/{asset_id}/settlement/reconcile",
            "/assets/{asset_id}/settlement/latest",
            "/assets/{asset_id}/settlement/runs",
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


@router.get("/data/status", response_model=DataStatusResponse)
def data_status():
    forecast_file = FORECAST_FILE
    actual_file = ACTUAL_PRICE_FILE
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
        "actual_price_file": file_status(actual_file),
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





