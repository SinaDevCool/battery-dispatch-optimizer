import json

from src.config.paths import (
    FORECAST_FILE,
    SCENARIO_RESULTS_FILE,
)
from src.forecasts.entsoe_forecast_provider import EntsoeForecastError
from src.scenarios.scenario_runner import run_scenarios
from src.services.asset_dispatch_service import (
    add_asset_dispatch_validation,
    build_asset_signal_metadata,
    dispatch_default_asset,
)
from src.services.asset_signal_store import save_asset_signal
from src.services.forecast_service import load_next_day_forecast_with_fallback
from src.services.signal_service import add_signal_metadata, save_signal_outputs


def run_daily_battery_workflow(optimizer_engine="rule_based_v1"):
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
        asset_dispatch_result = dispatch_default_asset(
            forecast_file=FORECAST_FILE,
            optimizer_engine=optimizer_engine,
        )
    except FileNotFoundError as error:
        return {
            "status": "not_found",
            "message": str(error),
        }

    dispatch_result = asset_dispatch_result.dispatch_result

    signal_result = add_signal_metadata(
        signal_result=dispatch_result.signal_result,
        source=forecast_result.source,
        forecast_model=forecast_result.model,
        target_date=forecast_result.target_date,
        forecast_file=FORECAST_FILE,
        extra_metadata=build_asset_signal_metadata(asset_dispatch_result),
    )
    signal_result = add_asset_dispatch_validation(
        signal_result=signal_result,
        asset_dispatch_result=asset_dispatch_result,
    )

    saved_signal_files = save_signal_outputs(
        signal_result=signal_result,
        target_date=forecast_result.target_date,
    )
    saved_asset_signal_files = save_asset_signal(
        signal_result=signal_result,
        asset_id=asset_dispatch_result.asset.asset_id,
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
        "asset_latest_signal_file": str(
            saved_asset_signal_files["asset_latest_signal_file"]
        ),
        "asset_run_file": str(saved_asset_signal_files["asset_run_file"]),
        "scenario_file": str(SCENARIO_RESULTS_FILE),
        "forecast_rows": len(forecast_result.dataframe),
        "forecast_columns": forecast_result.dataframe.columns.tolist(),
        "workflow_source": forecast_result.source,
        "warning": forecast_result.warning,
        "forecast_provider": forecast_result.source,
        "forecast_model": forecast_result.model,
        "optimizer_engine": dispatch_result.optimizer_engine,
        "asset_id": asset_dispatch_result.asset.asset_id,
        "market_profile_id": asset_dispatch_result.asset.market_profile_id,
        "assumption_risk_flags": asset_dispatch_result.assumption_risk_flags,
        "validation": signal_result["validation"],
        "signal": signal_result["summary"],
        "scenarios": scenario_results,
    }
