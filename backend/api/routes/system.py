import json
import os
from pathlib import Path

from fastapi import APIRouter

from backend.api.common import file_status
from backend.api.schemas import DataStatusResponse, HealthResponse
from backend.config.app_settings import get_app_settings
from backend.config.paths import (
    ACTUAL_PRICE_FILE,
    CLIENT_CONFIG_FILE,
    FORECAST_FILE,
    LATEST_SIGNAL_FILE,
    OUTPUT_DATA_DIR,
    SCENARIO_RESULTS_FILE,
)
from backend.db.readiness import build_database_namespace_readiness
from backend.execution.credential_readiness import build_credential_readiness
from backend.execution.live_adapter_handshake import (
    build_live_adapter_handshake_readiness,
    list_live_adapter_handshake_drills,
    run_live_adapter_handshake_drill,
)
from backend.services.data_sources import build_data_readiness, list_data_source_registry
from backend.services.persistence_readiness import build_persistence_readiness


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


@router.get("/system/persistence-readiness")
def persistence_readiness():
    try:
        return build_persistence_readiness()
    except Exception as error:
        return {
            "status": "error",
            "persistence_status": "blocked",
            "message": f"Could not evaluate persistence readiness: {error}",
            "checks": [],
            "summary": {
                "blocked": 1,
                "passed": 0,
                "review": 0,
                "total": 1,
            },
            "recommended_actions": [
                "Resolve backend persistence readiness evaluation before automated trading.",
            ],
        }


@router.get("/system/credential-readiness")
def credential_readiness():
    try:
        return build_credential_readiness()
    except Exception as error:
        return {
            "status": "error",
            "credential_readiness_status": "blocked",
            "message": f"Could not evaluate credential readiness: {error}",
            "credentials": [],
            "route_requirements": [],
            "summary": {
                "credential_count": 0,
                "configured_credential_count": 0,
                "missing_credential_count": 1,
                "route_count": 0,
                "credential_ready_route_count": 0,
                "credential_blocked_route_count": 0,
            },
            "recommended_actions": [
                "Resolve credential readiness evaluation before supervised live trading.",
            ],
        }


@router.get("/system/data-sources")
def data_source_registry():
    return {
        "status": "ok",
        "registry": list_data_source_registry(),
    }


@router.get("/system/data-readiness")
def data_readiness(asset_id: str = "default_site"):
    try:
        return build_data_readiness(asset_id=asset_id)
    except Exception as error:
        return {
            "status": "error",
            "asset_id": asset_id,
            "message": f"Could not evaluate data readiness: {error}",
            "domains": [],
            "summary": {
                "domain_count": 0,
                "current_ready_count": 0,
                "live_ready_count": 0,
                "live_missing_count": 1,
                "production_claim_allowed": False,
            },
        }


@router.get("/system/database-readiness")
def database_readiness():
    try:
        return build_database_namespace_readiness()
    except Exception as error:
        return {
            "status": "error",
            "message": f"Could not evaluate database namespace readiness: {error}",
        }


@router.get("/system/live-adapter-handshake")
def live_adapter_handshake_readiness(country: str = "Germany", asset_id: str = "default_site"):
    try:
        return build_live_adapter_handshake_readiness(country=country, asset_id=asset_id)
    except Exception as error:
        return {
            "status": "error",
            "handshake_readiness_status": "blocked",
            "message": f"Could not evaluate live adapter handshake readiness: {error}",
            "targets": [],
            "routes": [],
            "summary": {
                "handshake_target_count": 0,
                "handshake_ready_count": 0,
                "handshake_blocked_count": 1,
                "handshake_disabled_count": 0,
                "route_handshake_count": 0,
                "route_handshake_ready_count": 0,
                "route_handshake_blocked_count": 0,
                "route_handshake_disabled_count": 0,
            },
            "recommended_actions": [
                "Resolve live adapter handshake readiness before supervised live trading.",
            ],
        }


@router.post("/system/live-adapter-handshake/run")
def run_live_adapter_handshake(
    country: str = "Germany",
    asset_id: str = "default_site",
    target_id: str | None = None,
    route_id: str | None = None,
):
    try:
        return run_live_adapter_handshake_drill(
            asset_id=asset_id,
            target_id=target_id,
            route_id=route_id,
            country=country,
        )
    except ValueError as error:
        return {
            "status": "invalid",
            "message": str(error),
        }
    except Exception as error:
        return {
            "status": "error",
            "message": f"Could not run live adapter handshake drill: {error}",
        }


@router.get("/system/live-adapter-handshake/history")
def live_adapter_handshake_history(asset_id: str = "default_site", limit: int = 10):
    try:
        return list_live_adapter_handshake_drills(asset_id=asset_id, limit=limit)
    except Exception as error:
        return {
            "status": "error",
            "asset_id": asset_id,
            "message": f"Could not load live adapter handshake drill history: {error}",
            "drills": [],
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
            "/system/data-sources",
            "/system/data-readiness",
            "/system/database-readiness",
            "/data/status",
            "/data/update-entsoe",
            "/data/update-actual-prices",
            "/data/actual-prices/status",
            "/dashboard/summary",
            "/assets",
            "/demo/investor-seed",
            "/assets/{asset_id}/signal/run-latest",
            "/assets/{asset_id}/signal/latest",
            "/assets/{asset_id}/signal/history",
            "/assets/{asset_id}/signal/history/{file_name}",
            "/portfolio/run-daily",
            "/portfolio/latest",
            "/assets/{asset_id}/revenue-summary",
            "/assets/{asset_id}/regulatory-summary",
            "/assets/{asset_id}/execution-summary",
            "/assets/{asset_id}/client-evidence-summary",
            "/assets/{asset_id}/investor-readiness",
            "/assets/{asset_id}/intelligence/priority-gaps",
            "/agents",
            "/agents/personas",
            "/assets/{asset_id}/agents/persona/{persona_id}/status",
            "/assets/{asset_id}/agents/persona/{persona_id}/run",
            "/assets/{asset_id}/agents/trading-supervisor/status",
            "/assets/{asset_id}/agents/trading-supervisor/run",
            "/assets/{asset_id}/agents/trading-supervisor/history",
            "/assets/{asset_id}/agents/trading-supervisor/actions",
            "/assets/{asset_id}/agents/trading-supervisor/actions/{action_id}",
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
            "/assets/{asset_id}/forecast/status",
            "/forecast/preview",
            "/assets/{asset_id}/forecast/preview",
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
            "/assets/{asset_id}/scenarios/run-latest",
            "/assets/{asset_id}/scenarios/latest",
            "/stress/run-latest",
            "/stress/latest",
            "/assets/{asset_id}/stress/run-latest",
            "/assets/{asset_id}/stress/latest",
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
            "message": "No latest battery signal found. Run /workflow/run-daily or archive/manual_scripts/run_daily_signal.py first.",
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








