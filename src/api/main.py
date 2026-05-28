import json
import os
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

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
from src.config.client_presets import CLIENT_PRESETS
from src.scenarios.scenario_runner import run_scenarios
from src.scenarios.stress_runner import run_price_stress_tests
from src.signals.signal_engine import generate_battery_signal
from src.signals.explanation_engine import explain_battery_signal
from src.signals.risk_engine import build_risk_flags
from src.markets.data_loader import load_price_data_for_optimizer
from src.features.forecast_quality_features import build_forecast_quality_features
from src.features.negative_price_features import build_negative_price_features
from src.forecasts.forecast_loader import load_forecast_price_data
from src.config.paths import (
    CLIENT_CONFIG_FILE,
    FORECAST_FILE,
    LATEST_SIGNAL_FILE,
    MONTHLY_REPORT_PATTERN,
    OUTPUT_DATA_DIR,
    PRICE_STRESS_RESULTS_FILE,
    SCENARIO_RESULTS_FILE,
    SIGNAL_RUNS_DIR,
)
from src.forecasts.entsoe_forecast_provider import (
    EntsoeForecastError,
    build_next_day_entsoe_forecast,
)
from src.forecasts.forecast_comparison import compare_forecast_profitability


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

def validate_client_config(config):
    errors = []

    battery_config = config.get("battery_config", {})
    strategy_config = config.get("strategy_config", {})

    capacity_mwh = battery_config.get("capacity_mwh")
    initial_soc_mwh = battery_config.get("initial_soc_mwh")
    min_soc_mwh = battery_config.get("min_soc_mwh")
    max_charge_power_mw = battery_config.get("max_charge_power_mw")
    max_discharge_power_mw = battery_config.get("max_discharge_power_mw")
    charge_efficiency = battery_config.get("charge_efficiency")
    discharge_efficiency = battery_config.get("discharge_efficiency")

    low_price_threshold = strategy_config.get("low_price_threshold")
    high_price_threshold = strategy_config.get("high_price_threshold")
    timestep_hours = strategy_config.get("timestep_hours")

    required_fields = {
        "battery_config.capacity_mwh": capacity_mwh,
        "battery_config.initial_soc_mwh": initial_soc_mwh,
        "battery_config.min_soc_mwh": min_soc_mwh,
        "battery_config.max_charge_power_mw": max_charge_power_mw,
        "battery_config.max_discharge_power_mw": max_discharge_power_mw,
        "battery_config.charge_efficiency": charge_efficiency,
        "battery_config.discharge_efficiency": discharge_efficiency,
        "strategy_config.low_price_threshold": low_price_threshold,
        "strategy_config.high_price_threshold": high_price_threshold,
        "strategy_config.timestep_hours": timestep_hours,
    }

    for field_name, value in required_fields.items():
        if value is None:
            errors.append(f"Missing required field: {field_name}")

    if errors:
        return errors

    if capacity_mwh <= 0:
        errors.append("Battery capacity must be greater than 0.")

    if min_soc_mwh < 0:
        errors.append("Minimum SOC cannot be negative.")

    if min_soc_mwh >= capacity_mwh:
        errors.append("Minimum SOC must be lower than capacity.")

    if initial_soc_mwh < min_soc_mwh:
        errors.append("Initial SOC cannot be lower than minimum SOC.")

    if initial_soc_mwh > capacity_mwh:
        errors.append("Initial SOC cannot be greater than capacity.")

    if max_charge_power_mw <= 0:
        errors.append("Max charge power must be greater than 0.")

    if max_discharge_power_mw <= 0:
        errors.append("Max discharge power must be greater than 0.")

    if not 0 < charge_efficiency <= 1:
        errors.append("Charge efficiency must be between 0 and 1.")

    if not 0 < discharge_efficiency <= 1:
        errors.append("Discharge efficiency must be between 0 and 1.")

    if high_price_threshold <= low_price_threshold:
        errors.append("High price threshold must be greater than low price threshold.")

    if timestep_hours <= 0:
        errors.append("Timestep hours must be greater than 0.")

    return errors

@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "service": "battery-dispatch-optimizer",
    }

@app.get("/system/health")
def system_health():
    client_config_file = CLIENT_CONFIG_FILE
    forecast_file = FORECAST_FILE
    signal_file = LATEST_SIGNAL_FILE
    scenario_file = SCENARIO_RESULTS_FILE
    report_dir = SIGNAL_RUNS_DIR

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

    if missing_required:
        status = "not_ready"
    else:
        status = "ready"

    return {
        "status": status,
        "checks": checks,
        "missing_required": missing_required,
    }

@app.get("/status")
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
    validation_errors = validate_client_config(config)

    if validation_errors:
        return {
            "status": "invalid",
            "message": "Client config validation failed.",
            "errors": validation_errors,
        }

    config_file = save_client_config(config)

    return {
        "status": "ok",
        "message": "Client config saved successfully.",
        "config_file": str(config_file),
        "config": config,
    }

@app.get("/client/presets")
def list_client_presets():
    return {
        "status": "ok",
        "presets": list(CLIENT_PRESETS.keys()),
    }


@app.post("/client/presets/{preset_name}/apply")
def apply_client_preset(preset_name: str):
    if preset_name not in CLIENT_PRESETS:
        return {
            "status": "not_found",
            "message": f"Unknown preset: {preset_name}",
        }

    config = CLIENT_PRESETS[preset_name]
    validation_errors = validate_client_config(config)

    if validation_errors:
        return {
            "status": "invalid",
            "message": "Preset config validation failed.",
            "errors": validation_errors,
        }

    config_file = save_client_config(config)

    return {
        "status": "ok",
        "message": f"Applied client preset: {preset_name}",
        "config_file": str(config_file),
        "config": config,
    }

@app.get("/data/status")
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


@app.post("/data/update-entsoe")
def update_entsoe_data():
    forecast_file = FORECAST_FILE
    forecast_file.parent.mkdir(parents=True, exist_ok=True)

    try:
        df = build_next_day_entsoe_forecast()

    except ValueError as error:
        return {
            "status": "missing_token",
            "message": str(error),
        }

    except EntsoeForecastError as error:
        if forecast_file.exists():
            return {
                "status": "fallback",
                "message": (
                    f"{error} Existing local forecast file was kept, "
                    "so the dashboard can continue in local CSV mode."
                ),
                "forecast_file": str(forecast_file),
            }

        return {
            "status": "not_found",
            "message": str(error),
        }

    except Exception as error:
        return {
            "status": "error",
            "message": f"Could not update ENTSO-E forecast: {error}",
        }

    if df is None or df.empty:
        return {
            "status": "not_found",
            "message": "No ENTSO-E forecast data returned.",
        }

    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    df["forecast_price"] = pd.to_numeric(
        df["forecast_price"],
        errors="coerce",
    )

    df = df.dropna(subset=["timestamp", "forecast_price"])
    df = df.drop_duplicates(subset=["timestamp"])
    df = df.sort_values("timestamp")

    if df.empty:
        return {
            "status": "invalid",
            "message": "ENTSO-E forecast was returned, but no valid timestamp and price rows were available.",
        }

    df.to_csv(forecast_file, index=False)

    target_date = str(df["timestamp"].dt.date.iloc[0])

    return {
        "status": "ok",
        "message": "ENTSO-E forecast data updated successfully.",
        "target_date": target_date,
        "forecast_file": str(forecast_file),
        "rows": len(df),
        "columns": df.columns.tolist(),
        "forecast_provider": "entsoe",
        "forecast_model": "entsoe_day_ahead",
    }

@app.post("/forecast/upload")
def upload_forecast(request: BatterySignalRequest):
    forecast_file = FORECAST_FILE
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

    try:
        client_config = load_client_config()
    except FileNotFoundError as error:
        return {
            "status": "ok",
            "message": "Forecast uploaded successfully, but signal was not generated because client config is missing.",
            "forecast_file": str(forecast_file),
            "rows": len(df),
            "signal": None,
            "error": str(error),
        }

    price_data = load_forecast_price_data(forecast_file)

    signal_result = generate_battery_signal(
        price_data=price_data,
        battery_config=client_config["battery_config"],
        strategy_config=client_config["strategy_config"],
    )

    signal_file = LATEST_SIGNAL_FILE
    signal_file.parent.mkdir(parents=True, exist_ok=True)

    with open(signal_file, "w", encoding="utf-8") as file:
        json.dump(signal_result, file, indent=2)

    scenario_results = run_scenarios(price_data)

    scenario_file = SCENARIO_RESULTS_FILE
    scenario_file.parent.mkdir(parents=True, exist_ok=True)

    with open(scenario_file, "w", encoding="utf-8") as file:
        json.dump(scenario_results, file, indent=2)

    return {
        "status": "ok",
        "message": "Forecast uploaded, battery signal generated, and scenarios completed successfully.",
        "forecast_file": str(forecast_file),
        "signal_file": str(signal_file),
        "scenario_file": str(scenario_file),
        "rows": len(df),
        "signal": signal_result,
        "scenarios": scenario_results,
    }

@app.get("/forecast/status")
def forecast_status():
    forecast_file = FORECAST_FILE

    if not forecast_file.exists():
        return {
            "status": "not_found",
            "message": f"Forecast file not found: {forecast_file}",
        }

    df = pd.read_csv(forecast_file)
    features = build_forecast_quality_features(df)

    if features["status"] != "ok":
        return {
            "status": features["status"],
            "message": "Forecast quality check failed.",
            "forecast_file": str(forecast_file),
            **features,
        }

    return {
        "status": "ok",
        "forecast_file": str(forecast_file),
        **features,
    }

@app.get("/forecast/preview")
def forecast_preview():
    forecast_file = FORECAST_FILE

    if not forecast_file.exists():
        return {
            "status": "not_found",
            "message": f"Forecast file not found: {forecast_file}",
        }

    df = pd.read_csv(forecast_file)

    if df.empty:
        return {
            "status": "empty",
            "message": "Forecast file exists but is empty.",
            "forecast_file": str(forecast_file),
        }

    preview_rows = df.head(24).copy()

    return {
        "status": "ok",
        "forecast_file": str(forecast_file),
        "rows": len(df),
        "columns": df.columns.tolist(),
        "preview": preview_rows.to_dict(orient="records"),
    }

@app.post("/forecasts/compare-profitability")
def run_forecast_profitability_comparison():
    output_file = Path("data/outputs/forecast_profitability_comparison.json")
    output_file.parent.mkdir(parents=True, exist_ok=True)

    forecast_files = {
        "local_saved_forecast": FORECAST_FILE,
        
    }

    results = compare_forecast_profitability(forecast_files)

    with open(output_file, "w", encoding="utf-8") as file:
        json.dump(results, file, indent=2)

    return {
        "status": "ok",
        "message": "Forecast profitability comparison completed successfully.",
        "comparison_file": str(output_file),
        "results": results,
    }


@app.get("/forecasts/compare-profitability/latest")
def latest_forecast_profitability_comparison():
    comparison_file = Path("data/outputs/forecast_profitability_comparison.json")

    if not comparison_file.exists():
        return {
            "status": "not_found",
            "message": "No forecast profitability comparison found. Run /forecasts/compare-profitability first.",
            "results": [],
        }

    with open(comparison_file, "r", encoding="utf-8") as file:
        results = json.load(file)

    return {
        "status": "ok",
        "comparison_file": str(comparison_file),
        "results": results,
    }


@app.get("/features/forecast")
def forecast_features():
    forecast_file = FORECAST_FILE

    if not forecast_file.exists():
        return {
            "status": "not_found",
            "message": f"Forecast file not found: {forecast_file}",
        }

    df = pd.read_csv(forecast_file)

    quality_features = build_forecast_quality_features(
        df,
        price_column="forecast_price",
    )

    negative_features = build_negative_price_features(
        df,
        price_column="forecast_price",
    )

    return {
        "status": "ok",
        "forecast_file": str(forecast_file),
        "quality_features": quality_features,
        "negative_price_features": negative_features,
    }

@app.post("/forecast/demo")
def create_demo_forecast():
    forecast_file = FORECAST_FILE
    forecast_file.parent.mkdir(parents=True, exist_ok=True)

    start_time = pd.Timestamp.now().normalize() + pd.Timedelta(days=1)

    prices = [
        42, 38, 30, 22, 15, 8,
        12, 28, 55, 72, 85, 92,
        88, 75, 60, 48, 52, 70,
        96, 120, 110, 82, 58, 45,
    ]

    rows = []

    for hour, price in enumerate(prices):
        rows.append(
            {
                "timestamp": start_time + pd.Timedelta(hours=hour),
                "forecast_price": price,
                "forecast_provider": "demo",
                "forecast_model": "demo_base",
            }
        )

    df = pd.DataFrame(rows)
    df.to_csv(forecast_file, index=False)

    return {
        "status": "ok",
        "message": "Demo forecast created successfully.",
        "forecast_file": str(forecast_file),
        "rows": len(df),
        "forecast_provider": "demo",
        "forecast_model": "demo_base",
    }

@app.post("/forecast/demo-high-spread")
def create_demo_high_spread_forecast():
    forecast_file = Path("data/processed/demo_high_spread_forecast.csv")
    forecast_file.parent.mkdir(parents=True, exist_ok=True)

    start_time = pd.Timestamp.now().normalize() + pd.Timedelta(days=1)

    prices = [
        55, 48, 40, 28, 12, -5,
        -8, 20, 58, 85, 110, 125,
        118, 95, 72, 55, 62, 88,
        130, 155, 145, 100, 75, 60,
    ]

    rows = []

    for hour, price in enumerate(prices):
        rows.append(
            {
                "timestamp": start_time + pd.Timedelta(hours=hour),
                "forecast_price": price,
                "forecast_provider": "demo_high_spread",
                "forecast_model": "demo_high_spread",
            }
        )

    df = pd.DataFrame(rows)
    df.to_csv(forecast_file, index=False)

    return {
        "status": "ok",
        "message": "Demo high-spread forecast created successfully.",
        "forecast_file": str(forecast_file),
        "rows": len(df),
        "forecast_provider": "demo_high_spread",
        "forecast_model": "demo_high_spread",
    }

@app.get("/battery/config", response_model=BatteryConfigResponse)
def battery_config():
    return {
        "battery_config": DEFAULT_BATTERY_CONFIG,
        "strategy_config": DEFAULT_STRATEGY_CONFIG,
    }

@app.get("/battery/constraints")
def battery_constraints():
    try:
        client_config = load_client_config()
    except FileNotFoundError as error:
        return {
            "status": "not_found",
            "message": str(error),
        }

    battery_config = client_config["battery_config"]

    capacity_mwh = battery_config["capacity_mwh"]
    initial_soc_mwh = battery_config["initial_soc_mwh"]
    min_soc_mwh = battery_config["min_soc_mwh"]
    max_charge_power_mw = battery_config["max_charge_power_mw"]
    max_discharge_power_mw = battery_config["max_discharge_power_mw"]

    usable_capacity_mwh = capacity_mwh - min_soc_mwh
    initial_usable_soc_mwh = initial_soc_mwh - min_soc_mwh

    charge_duration_hours = capacity_mwh / max_charge_power_mw
    discharge_duration_hours = usable_capacity_mwh / max_discharge_power_mw

    return {
        "status": "ok",
        "capacity_mwh": capacity_mwh,
        "usable_capacity_mwh": round(usable_capacity_mwh, 4),
        "initial_usable_soc_mwh": round(initial_usable_soc_mwh, 4),
        "min_soc_mwh": min_soc_mwh,
        "initial_soc_mwh": initial_soc_mwh,
        "max_charge_power_mw": max_charge_power_mw,
        "max_discharge_power_mw": max_discharge_power_mw,
        "charge_duration_hours": round(charge_duration_hours, 4),
        "discharge_duration_hours": round(discharge_duration_hours, 4),
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
    signal_file = LATEST_SIGNAL_FILE

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

@app.get("/battery/signal/latest/explanation")
def latest_battery_signal_explanation():
    signal_file = LATEST_SIGNAL_FILE

    if not signal_file.exists():
        return {
            "status": "not_found",
            "message": "No latest battery signal found. Run the daily workflow first.",
        }

    with open(signal_file, "r", encoding="utf-8") as file:
        signal = json.load(file)

    forecast_file = FORECAST_FILE
    forecast_df = None

    if forecast_file.exists():
        forecast_df = pd.read_csv(forecast_file)

    return explain_battery_signal(signal, forecast_df=forecast_df)

@app.get("/battery/signal/latest/risks")
def latest_battery_signal_risks():
    signal_file = LATEST_SIGNAL_FILE

    if not signal_file.exists():
        return {
            "status": "not_found",
            "message": "No latest battery signal found. Run the daily workflow first.",
            "risks": [],
        }

    with open(signal_file, "r", encoding="utf-8") as file:
        signal = json.load(file)

    forecast_file = FORECAST_FILE
    forecast_df = None

    if forecast_file.exists():
        forecast_df = pd.read_csv(forecast_file)

    risks = build_risk_flags(signal, forecast_df=forecast_df)

    return {
        "status": "ok",
        "risks": risks,
    }

@app.post("/battery/signal/run-latest")
def run_latest_battery_signal():
    try:
        forecast_file = FORECAST_FILE
        output_file = LATEST_SIGNAL_FILE
        run_history_dir = SIGNAL_RUNS_DIR

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

        price_data = load_forecast_price_data(forecast_file)

        result = generate_battery_signal(
            price_data=price_data,
            battery_config=client_config["battery_config"],
            strategy_config=client_config["strategy_config"],
            commercial_config=client_config.get("commercial_config"),
        )

        generated_at = datetime.now()

        result["metadata"] = {
            "source": "processed_forecast_csv",
            "target_date": None,
            "generated_at": generated_at.isoformat(timespec="seconds"),
            "forecast_file": str(forecast_file),
        }

        output_file.parent.mkdir(parents=True, exist_ok=True)
        run_history_dir.mkdir(parents=True, exist_ok=True)

        run_history_file = (
            run_history_dir
            / f"{generated_at.strftime('%Y%m%d_%H%M%S')}_battery_signal.json"
        )

        with open(output_file, "w", encoding="utf-8") as file:
            json.dump(result, file, indent=2)

        with open(run_history_file, "w", encoding="utf-8") as file:
            json.dump(result, file, indent=2)

        return {
            "status": "ok",
            "message": "Latest battery signal generated successfully.",
            "signal_file": str(output_file),
            "run_history_file": str(run_history_file),
            "data": result,
        }

    except Exception as error:
        return {
            "status": "error",
            "message": f"Could not generate latest battery signal: {error}",
        }

@app.get("/battery/signal/history")
def battery_signal_history():
    run_history_dir = SIGNAL_RUNS_DIR

    if not run_history_dir.exists():
        return {
            "status": "not_found",
            "message": "No run history folder found.",
            "runs": [],
        }

    run_files = sorted(run_history_dir.glob("*_battery_signal.json"))

    runs = []

    for file_path in run_files:
        runs.append(
            {
                "file_name": file_path.name,
                "file_path": str(file_path),
                "last_modified": datetime.fromtimestamp(
                    file_path.stat().st_mtime
                ).isoformat(timespec="seconds"),
                "size_bytes": file_path.stat().st_size,
            }
        )

    return {
        "status": "ok",
        "runs": runs,
    }

@app.get("/battery/signal/history/{file_name}")
def get_battery_signal_history_file(file_name: str):
    run_history_dir = SIGNAL_RUNS_DIR
    run_file = run_history_dir / file_name

    if not run_file.exists():
        return {
            "status": "not_found",
            "message": f"Run history file not found: {file_name}",
        }

    if run_file.suffix != ".json":
        return {
            "status": "invalid_file",
            "message": "Only JSON run history files can be loaded.",
        }

    with open(run_file, "r", encoding="utf-8") as file:
        data = json.load(file)

    return {
        "status": "ok",
        "file_name": file_name,
        "data": data,
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

    output_file = SCENARIO_RESULTS_FILE
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
    forecast_file = FORECAST_FILE
    output_file = SCENARIO_RESULTS_FILE

    if not forecast_file.exists():
        return {
            "status": "not_found",
            "message": f"Forecast file not found: {forecast_file}",
        }

    price_data = load_forecast_price_data(forecast_file)

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
    scenario_file = SCENARIO_RESULTS_FILE

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


@app.post("/stress/run-latest")
def run_latest_price_stress_tests():
    forecast_file = FORECAST_FILE
    output_file = PRICE_STRESS_RESULTS_FILE

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

    stress_results = run_price_stress_tests(
        price_data=price_data,
        battery_config=client_config["battery_config"],
        strategy_config=client_config["strategy_config"],
        commercial_config=client_config.get("commercial_config"),
    )

    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, "w", encoding="utf-8") as file:
        json.dump(stress_results, file, indent=2)

    return {
        "status": "ok",
        "message": "Price stress tests completed successfully.",
        "stress_file": str(output_file),
        "results": stress_results,
    }


@app.get("/stress/latest")
def latest_price_stress_tests():
    stress_file = PRICE_STRESS_RESULTS_FILE

    if not stress_file.exists():
        return {
            "status": "not_found",
            "message": "No price stress results found. Run /stress/run-latest first.",
        }

    with open(stress_file, "r", encoding="utf-8") as file:
        results = json.load(file)

    return {
        "status": "ok",
        "stress_file": str(stress_file),
        "results": results,
    }

@app.get("/dashboard/summary")
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


@app.get("/reports/monthly/latest")
def latest_monthly_report():
    report_dir = OUTPUT_DATA_DIR

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
    report_dir = OUTPUT_DATA_DIR

    if not report_dir.exists():
        return "<h1>No report folder found</h1>"

    report_files = sorted(report_dir.glob("monthly_report_*.html"))

    if not report_files:
        return "<h1>No monthly reports found</h1>"

    latest_report = report_files[-1]

    with open(latest_report, "r", encoding="utf-8") as file:
        return file.read()
    

@app.post("/workflow/run-daily")
def run_daily_workflow():
    forecast_file = FORECAST_FILE
    signal_file = LATEST_SIGNAL_FILE
    scenario_file = SCENARIO_RESULTS_FILE
    run_history_dir = SIGNAL_RUNS_DIR

    forecast_file.parent.mkdir(parents=True, exist_ok=True)
    signal_file.parent.mkdir(parents=True, exist_ok=True)
    scenario_file.parent.mkdir(parents=True, exist_ok=True)
    run_history_dir.mkdir(parents=True, exist_ok=True)

    try:
        df = build_next_day_entsoe_forecast()

    except ValueError as error:
        return {
            "status": "missing_token",
            "message": str(error),
        }

    except EntsoeForecastError as error:
        if forecast_file.exists():
            df = pd.read_csv(forecast_file)
            workflow_source = "local_saved_forecast"
            workflow_warning = (
                f"{error} Existing local forecast file was used instead."
            )
        else:
            return {
                "status": "not_found",
                "message": str(error),
            }

    except Exception as error:
        return {
            "status": "error",
            "message": f"Could not update ENTSO-E forecast: {error}",
        }
    
    if "workflow_source" not in locals():
        workflow_source = "entsoe"
        workflow_warning = None

    if df is None or df.empty:
        return {
            "status": "not_found",
            "message": "No ENTSO-E forecast data returned.",
        }

    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    df["forecast_price"] = pd.to_numeric(
        df["forecast_price"],
        errors="coerce",
    )

    df = df.dropna(subset=["timestamp", "forecast_price"])
    df = df.drop_duplicates(subset=["timestamp"])
    df = df.sort_values("timestamp")

    if df.empty:
        return {
            "status": "invalid",
            "message": "ENTSO-E forecast was returned, but no valid timestamp and price rows were available.",
        }

    df.to_csv(forecast_file, index=False)

    target_date = str(df["timestamp"].dt.date.iloc[0])

    try:
        client_config = load_client_config()
    except FileNotFoundError as error:
        return {
            "status": "not_found",
            "message": str(error),
        }

    price_data = load_forecast_price_data(forecast_file)

    signal_result = generate_battery_signal(
        price_data=price_data,
        battery_config=client_config["battery_config"],
        strategy_config=client_config["strategy_config"],
        commercial_config=client_config.get("commercial_config"),
    )

    generated_at = datetime.now()

    signal_result["metadata"] = {
        "source": workflow_source,
        "forecast_provider": workflow_source,
        "forecast_model": (
        "entsoe_day_ahead"
            if workflow_source == "entsoe"
            else "local_saved_forecast"
        ),
        "target_date": target_date,
        "generated_at": generated_at.isoformat(timespec="seconds"),
        "forecast_file": str(forecast_file),
    }

    safe_target_date = target_date.replace("-", "")
    run_history_file = run_history_dir / f"{safe_target_date}_battery_signal.json"

    with open(signal_file, "w", encoding="utf-8") as file:
        json.dump(signal_result, file, indent=2)

    with open(run_history_file, "w", encoding="utf-8") as file:
        json.dump(signal_result, file, indent=2)

    scenario_results = run_scenarios(price_data)

    with open(scenario_file, "w", encoding="utf-8") as file:
        json.dump(scenario_results, file, indent=2)

    return {
        "status": "ok",
        "message": "Daily workflow completed successfully.",
        "target_date": target_date,
        "forecast_file": str(forecast_file),
        "signal_file": str(signal_file),
        "run_history_file": str(run_history_file),
        "scenario_file": str(scenario_file),
        "forecast_rows": len(df),
        "forecast_columns": df.columns.tolist(),
        "workflow_source": workflow_source,
        "warning": workflow_warning,
        "forecast_provider": workflow_source,
        "forecast_model": (
        "entsoe_day_ahead"
            if workflow_source == "entsoe"
            else "local_saved_forecast"
        ),
        "signal": signal_result["summary"],
        "scenarios": scenario_results,
    }