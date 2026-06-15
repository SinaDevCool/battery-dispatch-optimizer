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
    ASSET_OUTPUTS_DIR,
    FORECAST_ACTUAL_RESULTS_FILE,
    FORECAST_FILE,
)
from backend.forecasts.forecast_loader import load_forecast_dataframe
from backend.services.asset_signal_store import load_asset_latest_signal


def run_forecast_actual_backtest(
    asset_id="default_site",
    forecast_file=None,
    actual_file=ACTUAL_PRICE_FILE,
):
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
    FORECAST_ACTUAL_RESULTS_FILE.parent.mkdir(parents=True, exist_ok=True)

    with open(FORECAST_ACTUAL_RESULTS_FILE, "w", encoding="utf-8") as file:
        json.dump(result, file, indent=2)

    asset_dir = ASSET_OUTPUTS_DIR / asset_id
    asset_dir.mkdir(parents=True, exist_ok=True)
    asset_file = asset_dir / "latest_forecast_actual.json"

    with open(asset_file, "w", encoding="utf-8") as file:
        json.dump(result, file, indent=2)

    return {
        "forecast_actual_file": FORECAST_ACTUAL_RESULTS_FILE,
        "asset_forecast_actual_file": asset_file,
    }


def load_latest_forecast_actual_result(asset_id):
    asset_file = ASSET_OUTPUTS_DIR / asset_id / "latest_forecast_actual.json"

    if not asset_file.exists():
        return {
            "status": "not_found",
            "message": f"No latest forecast-vs-actual result found for asset: {asset_id}",
            "asset_id": asset_id,
        }

    with open(asset_file, "r", encoding="utf-8") as file:
        return json.load(file)



