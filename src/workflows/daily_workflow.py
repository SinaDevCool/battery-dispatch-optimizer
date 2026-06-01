import json

from src.config.client_config import load_client_config
from src.config.paths import (
    FORECAST_FILE,
    SCENARIO_RESULTS_FILE,
)
from src.forecasts.entsoe_forecast_provider import EntsoeForecastError
from src.scenarios.scenario_runner import run_scenarios
from src.services.dispatch_service import optimize_dispatch_from_forecast_file
from src.services.forecast_service import load_next_day_forecast_with_fallback
from src.services.signal_service import add_signal_metadata, save_signal_outputs


def run_daily_battery_workflow():
    try:
        forecast_result = load_next_day_forecast_with_fallback(FORECAST_FILE)

    except ValueError as error:
        error_message = str(error)

        if "token" not in error_message.lower():
            return {
                "status": "invalid",
                "message": error_message,
            }

        return {
            "status": "missing_token",
            "message": error_message,
        }

    except EntsoeForecastError as error:
        return {
            "status": "not_found",
            "message": str(error),
        }

    except Exception as error:
        return {
            "status": "error",
            "message": f"Could not update ENTSO-E forecast: {error}",
        }

    try:
        client_config = load_client_config()
    except FileNotFoundError as error:
        return {
            "status": "not_found",
            "message": str(error),
        }

    dispatch_result = optimize_dispatch_from_forecast_file(
        forecast_file=FORECAST_FILE,
        battery_config=client_config["battery_config"],
        strategy_config=client_config["strategy_config"],
        commercial_config=client_config.get("commercial_config"),
    )

    signal_result = add_signal_metadata(
        signal_result=dispatch_result.signal_result,
        source=forecast_result.source,
        forecast_model=forecast_result.model,
        target_date=forecast_result.target_date,
        forecast_file=FORECAST_FILE,
    )

    saved_signal_files = save_signal_outputs(
        signal_result=signal_result,
        target_date=forecast_result.target_date,
    )

    scenario_results = run_scenarios(dispatch_result.price_data)

    SCENARIO_RESULTS_FILE.parent.mkdir(parents=True, exist_ok=True)

    with open(SCENARIO_RESULTS_FILE, "w", encoding="utf-8") as file:
        json.dump(scenario_results, file, indent=2)

    return {
        "status": "ok",
        "message": "Daily workflow completed successfully.",
        "target_date": forecast_result.target_date,
        "forecast_file": str(FORECAST_FILE),
        "signal_file": str(saved_signal_files["signal_file"]),
        "run_history_file": str(saved_signal_files["run_history_file"]),
        "scenario_file": str(SCENARIO_RESULTS_FILE),
        "forecast_rows": len(forecast_result.dataframe),
        "forecast_columns": forecast_result.dataframe.columns.tolist(),
        "workflow_source": forecast_result.source,
        "warning": forecast_result.warning,
        "forecast_provider": forecast_result.source,
        "forecast_model": forecast_result.model,
        "optimizer_engine": dispatch_result.optimizer_engine,
        "signal": signal_result["summary"],
        "scenarios": scenario_results,
    }
