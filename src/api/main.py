import json
from datetime import datetime
from pathlib import Path

import pandas as pd
from fastapi import FastAPI
from fastapi.responses import HTMLResponse

from src.api.schemas import (
    BacktestRequest,
    BacktestResponse,
    BatteryConfigResponse,
    BatterySignalRequest,
    BatterySignalResponse,
)
from src.backtesting.metrics import calculate_backtest_metrics
from src.config.battery_config import DEFAULT_BATTERY_CONFIG, DEFAULT_STRATEGY_CONFIG
from src.config.client_config import load_client_config, save_client_config
from src.scenarios.scenario_runner import run_scenarios
from src.signals.signal_engine import generate_battery_signal
from src.markets.data_loader import load_price_data_for_optimizer


app = FastAPI(
    title="Battery Dispatch Optimizer API",
    description="Simple API for battery dispatch signals, backtesting, scenarios, client config, and reports.",
    version="0.1.0",
)


def file_status(path):
    if not path.exists():
        return {
            "exists": False,
            "path": str(path),
            "last_modified": None,
            "size_bytes": 0,
        }

    modified_time = datetime.fromtimestamp(path.stat().st_mtime)

    return {
        "exists": True,
        "path": str(path),
        "last_modified": modified_time.isoformat(timespec="seconds"),
        "size_bytes": path.stat().st_size,
    }

def validate_forecast_dataframe(df):
    required_columns = ["timestamp", "forecast_price"]

    missing_columns = [
        column for column in required_columns
        if column not in df.columns
    ]

    if missing_columns:
        return False, f"Missing required columns: {', '.join(missing_columns)}"

    df = df.copy()

    df["timestamp"] = pd.to_datetime(
        df["timestamp"],
        errors="coerce",
    )

    df["forecast_price"] = pd.to_numeric(
        df["forecast_price"],
        errors="coerce",
    )

    invalid_timestamps = df["timestamp"].isna().sum()
    missing_prices = df["forecast_price"].isna().sum()
    duplicate_timestamps = df["timestamp"].duplicated().sum()

    if invalid_timestamps > 0:
        return False, f"Forecast has {invalid_timestamps} invalid timestamps."

    if missing_prices > 0:
        return False, f"Forecast has {missing_prices} missing or invalid prices."

    if duplicate_timestamps > 0:
        return False, f"Forecast has {duplicate_timestamps} duplicate timestamps."

    if len(df) < 2:
        return False, "Forecast must contain at least 2 rows."

    return True, "Forecast is valid."

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
            "/data/status",
            "/dashboard/summary",
            "/client/config",
            "/forecast/upload",
            "/battery/config",
            "/battery/signal",
            "/battery/signal/latest",
            "/battery/signal/run-latest",
            "/battery/backtest",
            "/scenarios/run",
            "/scenarios/run-latest",
            "/scenarios/latest",
            "/reports/monthly/latest",
            "/reports/monthly/latest/view",
        ],
    }


@app.get("/client/config")
def get_client_config():
    try:
        config = load_client_config()

        return {
            "status": "ok",
            "config": config,
        }

    except FileNotFoundError as error:
        return {
            "status": "not_found",
            "message": str(error),
        }


@app.post("/client/config")
def update_client_config(config: dict):
    config_file = save_client_config(config)

    return {
        "status": "ok",
        "message": "Client config saved successfully.",
        "config_file": str(config_file),
        "config": config,
    }


@app.get("/data/status")
def data_status():
    forecast_file = Path("data/processed/next_day_price_forecast.csv")
    signal_file = Path("data/outputs/latest_battery_signal.json")
    scenario_file = Path("data/outputs/scenario_results.json")
    report_dir = Path("data/outputs")

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


@app.post("/forecast/upload")
def upload_forecast(request: BatterySignalRequest):
    forecast_file = Path("data/processed/next_day_price_forecast.csv")
    forecast_file.parent.mkdir(parents=True, exist_ok=True)

    rows = []

    for item in request.price_data:
        rows.append(
            {
                "timestamp": item.timestamp,
                "forecast_price": item.price,
            }
        )

    df = pd.DataFrame(rows)
    is_valid, validation_message = validate_forecast_dataframe(df)

    if not is_valid:
        return {
            "status": "invalid",
            "message": validation_message,
            "forecast_file": str(forecast_file),
            "rows": len(df),
        }
    df.to_csv(forecast_file, index=False)

    return {
        "status": "ok",
        "message": "Forecast uploaded successfully.",
        "forecast_file": str(forecast_file),
        "rows": len(df),
    }


@app.get("/battery/config", response_model=BatteryConfigResponse)
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

    return generate_battery_signal(
        price_data=price_data,
        battery_config=battery_config,
        strategy_config=strategy_config,
    )


@app.get("/battery/signal/latest")
def latest_battery_signal():
    signal_file = Path("data/outputs/latest_battery_signal.json")

    if not signal_file.exists():
        return {
            "status": "not_found",
            "message": "No latest battery signal found. Run scripts/run_daily_signal.py first.",
        }

    with open(signal_file, "r", encoding="utf-8") as file:
        signal = json.load(file)

    return {
        "status": "ok",
        "signal_file": str(signal_file),
        "data": signal,
    }



@app.post("/battery/signal/run-latest")
def run_latest_battery_signal():
    forecast_file = Path("data/processed/next_day_price_forecast.csv")
    output_file = Path("data/outputs/latest_battery_signal.json")

    if not forecast_file.exists():
        return {
            "status": "not_found",
            "message": f"Forecast file not found: {forecast_file}",
        }

    try:
        client_config = load_client_config()
    except FileNotFoundError as error:
        return {
            "status": "not_found",
            "message": str(error),
        }

    price_data = load_price_data_for_optimizer(
        forecast_file,
        price_column="forecast_price",
    )

    result = generate_battery_signal(
        price_data=price_data,
        battery_config=client_config["battery_config"],
        strategy_config=client_config["strategy_config"],
    )

    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, "w", encoding="utf-8") as file:
        json.dump(result, file, indent=2)

    return {
        "status": "ok",
        "message": "Latest battery signal generated successfully.",
        "signal_file": str(output_file),
        "data": result,
    }

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


@app.post("/scenarios/run")
def run_battery_scenarios(request: BatterySignalRequest):
    price_data = [
        {
            "timestamp": item.timestamp,
            "price": item.price,
        }
        for item in request.price_data
    ]

    scenario_results = run_scenarios(price_data)

    output_file = Path("data/outputs/scenario_results.json")
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, "w", encoding="utf-8") as file:
        json.dump(scenario_results, file, indent=2)

    return {
        "status": "ok",
        "results": scenario_results,
        "output_file": str(output_file),
    }

@app.post("/scenarios/run-latest")
def run_latest_scenarios():
    forecast_file = Path("data/processed/next_day_price_forecast.csv")
    output_file = Path("data/outputs/scenario_results.json")

    if not forecast_file.exists():
        return {
            "status": "not_found",
            "message": f"Forecast file not found: {forecast_file}",
        }

    price_data = load_price_data_for_optimizer(
        forecast_file,
        price_column="forecast_price",
    )

    scenario_results = run_scenarios(price_data)

    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, "w", encoding="utf-8") as file:
        json.dump(scenario_results, file, indent=2)

    return {
        "status": "ok",
        "message": "Scenario analysis completed successfully.",
        "scenario_file": str(output_file),
        "results": scenario_results,
    }

@app.get("/scenarios/latest")
def latest_scenarios():
    scenario_file = Path("data/outputs/scenario_results.json")

    if not scenario_file.exists():
        return {
            "status": "not_found",
            "message": "No scenario results found. Run /scenarios/run first.",
        }

    with open(scenario_file, "r", encoding="utf-8") as file:
        results = json.load(file)

    return {
        "status": "ok",
        "scenario_file": str(scenario_file),
        "results": results,
    }


@app.get("/dashboard/summary")
def dashboard_summary():
    signal_file = Path("data/outputs/latest_battery_signal.json")
    report_dir = Path("data/outputs")

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
        return file.read()