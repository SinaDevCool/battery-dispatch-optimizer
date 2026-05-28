import pandas as pd

from src.config.battery_config import DEFAULT_BATTERY_CONFIG, DEFAULT_STRATEGY_CONFIG
from src.config.commercial_config import DEFAULT_COMMERCIAL_CONFIG
from src.forecasts.forecast_loader import load_forecast_price_data
from src.signals.signal_engine import generate_battery_signal


def summarize_forecast_signal(provider_name, forecast_file):
    price_data = load_forecast_price_data(forecast_file)

    signal_result = generate_battery_signal(
        price_data=price_data,
        battery_config=DEFAULT_BATTERY_CONFIG,
        strategy_config=DEFAULT_STRATEGY_CONFIG,
        commercial_config=DEFAULT_COMMERCIAL_CONFIG,
    )

    summary = signal_result.get("summary", {})

    return {
        "forecast_provider": provider_name,
        "forecast_file": str(forecast_file),
        "signal": summary.get("signal"),
        "opportunity_level": summary.get("opportunity_level"),
        "total_pnl_eur": summary.get("total_pnl_eur", 0),
        "profit_per_mw_day": summary.get("profit_per_mw_day", 0),
        "charge_hours": summary.get("charge_hours", 0),
        "discharge_hours": summary.get("discharge_hours", 0),
        "first_charge_timestamp": summary.get("first_charge_timestamp"),
        "first_discharge_timestamp": summary.get("first_discharge_timestamp"),
    }


def compare_forecast_profitability(forecast_files):
    results = []

    for provider_name, forecast_file in forecast_files.items():
        if not forecast_file.exists():
            results.append(
                {
                    "forecast_provider": provider_name,
                    "forecast_file": str(forecast_file),
                    "status": "missing",
                    "message": "Forecast file not found.",
                }
            )
            continue

        try:
            result = summarize_forecast_signal(
                provider_name=provider_name,
                forecast_file=forecast_file,
            )
            result["status"] = "ok"
            results.append(result)

        except Exception as error:
            results.append(
                {
                    "forecast_provider": provider_name,
                    "forecast_file": str(forecast_file),
                    "status": "error",
                    "message": str(error),
                }
            )

    return results