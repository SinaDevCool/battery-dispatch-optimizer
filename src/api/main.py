from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import HTMLResponse

from src.api.schemas import (
    BacktestRequest,
    BacktestResponse,
    BatterySignalRequest,
    BatterySignalResponse,
)
from src.backtesting.metrics import calculate_backtest_metrics
from src.config.battery_config import DEFAULT_BATTERY_CONFIG, DEFAULT_STRATEGY_CONFIG
from src.signals.signal_engine import generate_battery_signal


app = FastAPI(
    title="Battery Dispatch Optimizer API",
    description="Simple API for battery dispatch signals and backtesting.",
    version="0.1.0",
)


@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "service": "battery-dispatch-optimizer",
    }


@app.get("/status")
def project_status():
    return {
        "status": "ok",
        "project": "battery-dispatch-optimizer",
        "version": "0.1.0",
        "available_endpoints": [
            "/health",
            "/status",
            "/battery/config",
            "/battery/signal",
            "/battery/backtest",
            "/reports/monthly/latest",
            "/reports/monthly/latest/view",
        ],
    }


@app.get("/battery/config")
def battery_config():
    return {
        "battery_config": DEFAULT_BATTERY_CONFIG,
        "strategy_config": DEFAULT_STRATEGY_CONFIG,
    }


@app.post("/battery/signal", response_model=BatterySignalResponse)
def battery_signal(request: BatterySignalRequest):
    price_data = [
        {
            "timestamp": item.timestamp,
            "price": item.price,
        }
        for item in request.price_data
    ]

    battery_config = None
    strategy_config = None

    if request.battery_config is not None:
        battery_config = request.battery_config.model_dump()

    if request.strategy_config is not None:
        strategy_config = request.strategy_config.model_dump()

    result = generate_battery_signal(
        price_data=price_data,
        battery_config=battery_config,
        strategy_config=strategy_config,
    )

    return result


@app.post("/battery/backtest", response_model=BacktestResponse)
def battery_backtest(request: BacktestRequest):
    price_data = [
        {
            "timestamp": item.timestamp,
            "price": item.price,
        }
        for item in request.price_data
    ]

    battery_config = None
    strategy_config = None

    if request.battery_config is not None:
        battery_config = request.battery_config.model_dump()

    if request.strategy_config is not None:
        strategy_config = request.strategy_config.model_dump()

    result = generate_battery_signal(
        price_data=price_data,
        battery_config=battery_config,
        strategy_config=strategy_config,
    )

    metrics = calculate_backtest_metrics(result["dispatch"])

    return {
        "summary": metrics,
        "dispatch": result["dispatch"],
    }


@app.get("/reports/monthly/latest")
def latest_monthly_report():
    report_dir = Path("data/outputs")

    if not report_dir.exists():
        return {
            "status": "not_found",
            "message": "Report output folder does not exist yet.",
        }

    report_files = sorted(report_dir.glob("monthly_report_*.html"))

    if not report_files:
        return {
            "status": "not_found",
            "message": "No monthly reports found.",
        }

    latest_report = report_files[-1]

    return {
        "status": "ok",
        "report_file": str(latest_report),
        "report_name": latest_report.name,
    }


@app.get("/reports/monthly/latest/view", response_class=HTMLResponse)
def view_latest_monthly_report():
    report_dir = Path("data/outputs")

    if not report_dir.exists():
        return "<h1>No report folder found</h1>"

    report_files = sorted(report_dir.glob("monthly_report_*.html"))

    if not report_files:
        return "<h1>No monthly reports found</h1>"

    latest_report = report_files[-1]

    with open(latest_report, "r", encoding="utf-8") as file:
        html = file.read()

    return html