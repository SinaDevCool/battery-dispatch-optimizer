import json
from datetime import datetime
from pathlib import Path

from backend.backtesting.forecast_actual.actual_price_loader import (
    load_actual_price_dataframe,
)
from backend.backtesting.forecast_actual.forecast_actual_comparison import (
    compare_forecast_to_actual,
)
from backend.backtesting.forecast_actual.forecast_performance_repository import (
    save_forecast_actual_run,
)
from backend.backtesting.forecast_actual.realized_dispatch_replay import (
    replay_dispatch_against_actual_prices,
)
from backend.assets.asset_loader import get_asset
from backend.config.paths import (
    ACTUAL_PRICE_FILE,
    FORECAST_FILE,
)
from backend.data_environment import (
    current_data_mode,
    is_live_mode,
    live_not_configured_response,
    mode_global_output_file,
)
from backend.forecasts.forecast_loader import load_forecast_dataframe
from backend.services.asset_output_paths import asset_output_dir, readable_asset_output_file
from backend.services.asset_signal_store import load_asset_latest_signal


def run_forecast_actual_backtest(
    asset_id="default_site",
    forecast_file=None,
    actual_file=ACTUAL_PRICE_FILE,
):
    data_mode = current_data_mode()
    asset = get_asset(asset_id)
    resolved_forecast_file = Path(
        forecast_file or asset.forecast_file or FORECAST_FILE
    )
    resolved_actual_file = Path(actual_file or ACTUAL_PRICE_FILE)

    forecast_df = load_forecast_dataframe(
        forecast_file=resolved_forecast_file,
        price_column="forecast_price",
    )
    actual_df = load_actual_price_dataframe(actual_file=resolved_actual_file)

    latest_signal_response = load_asset_latest_signal(asset_id)

    if latest_signal_response.get("status") != "ok":
        raise FileNotFoundError(
            f"No latest asset signal found for asset {asset_id}. "
            "Run the asset signal first."
        )

    signal_result = latest_signal_response["data"]
    metadata = signal_result.get("metadata", {})

    comparison = compare_forecast_to_actual(
        forecast_df=forecast_df,
        actual_df=actual_df,
    )
    realized_dispatch = replay_dispatch_against_actual_prices(
        signal_result=signal_result,
        actual_df=actual_df,
    )

    result = {
        "status": "ok",
        "asset_id": asset_id,
        "data_mode": data_mode,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "forecast_file": str(resolved_forecast_file),
        "actual_file": str(resolved_actual_file),
        "metadata": {
            "target_date": metadata.get("target_date"),
            "forecast_provider": metadata.get("forecast_provider"),
            "forecast_model": metadata.get("forecast_model"),
            "market_profile_id": metadata.get("market_profile_id"),
            "signal_file": latest_signal_response.get("signal_file"),
        },
        "forecast_error_status": comparison["status"],
        "forecast_error_metrics": comparison["metrics"],
        "forecast_error_rows": comparison["rows"],
        "realized_dispatch": realized_dispatch,
    }

    forecast_actual_id = save_forecast_actual_run(result)
    result["forecast_actual_id"] = forecast_actual_id

    save_forecast_actual_result(asset_id, result)

    return result


def save_forecast_actual_result(asset_id, result):
    result["data_mode"] = current_data_mode()
    global_file = mode_global_output_file("forecast_actual_results.json")
    global_file.parent.mkdir(parents=True, exist_ok=True)

    with open(global_file, "w", encoding="utf-8") as file:
        json.dump(result, file, indent=2)

    asset_dir = asset_output_dir(asset_id)
    asset_dir.mkdir(parents=True, exist_ok=True)
    asset_file = asset_dir / "latest_forecast_actual.json"

    with open(asset_file, "w", encoding="utf-8") as file:
        json.dump(result, file, indent=2)

    return {
        "forecast_actual_file": global_file,
        "asset_forecast_actual_file": asset_file,
    }


def load_latest_forecast_actual_result(asset_id):
    data_mode = current_data_mode()
    asset_file = readable_asset_output_file(
        asset_id,
        "latest_forecast_actual.json",
        data_mode=data_mode,
    )

    if not asset_file.exists():
        if is_live_mode(data_mode):
            return live_not_configured_response(asset_id, "forecast_actual")
        return {
            "status": "not_found",
            "data_mode": data_mode,
            "message": f"No latest forecast-vs-actual result found for asset: {asset_id}",
            "asset_id": asset_id,
        }

    with open(asset_file, "r", encoding="utf-8") as file:
        result = json.load(file)
        result.setdefault("data_mode", data_mode)
        if is_live_mode(data_mode) and result.get("data_mode") != "live":
            return live_not_configured_response(asset_id, "forecast_actual")
        return result



