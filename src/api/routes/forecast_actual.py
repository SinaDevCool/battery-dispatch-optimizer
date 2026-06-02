from fastapi import APIRouter

from src.api.schemas import ForecastActualBacktestResponse
from src.backtesting.forecast_actual.forecast_actual_runner import (
    load_latest_forecast_actual_result,
    run_forecast_actual_backtest,
)
from src.backtesting.forecast_actual.forecast_performance_repository import (
    get_forecast_performance_run,
    list_forecast_performance_runs,
)


router = APIRouter()


@router.post(
    "/backtesting/forecast-actual/run",
    response_model=ForecastActualBacktestResponse,
)
def run_forecast_actual_backtest_endpoint(
    asset_id: str = "default_site",
    actual_file: str | None = None,
    forecast_file: str | None = None,
):
    try:
        result = run_forecast_actual_backtest(
            asset_id=asset_id,
            forecast_file=forecast_file,
            actual_file=actual_file,
        )
        return result

    except FileNotFoundError as error:
        return {
            "status": "not_found",
            "message": str(error),
        }

    except ValueError as error:
        return {
            "status": "invalid",
            "message": str(error),
        }

    except Exception as error:
        return {
            "status": "error",
            "message": f"Could not run forecast-vs-actual backtest: {error}",
        }


@router.get(
    "/backtesting/forecast-actual/latest",
    response_model=ForecastActualBacktestResponse,
)
def latest_forecast_actual_result(asset_id: str = "default_site"):
    return load_latest_forecast_actual_result(asset_id)


@router.get("/assets/{asset_id}/forecast-performance")
def asset_forecast_performance(asset_id: str, limit: int = 50):
    runs = list_forecast_performance_runs(
        asset_id=asset_id,
        limit=limit,
    )

    return {
        "status": "ok",
        "asset_id": asset_id,
        "run_count": len(runs),
        "runs": runs,
    }


@router.get("/assets/{asset_id}/forecast-performance/{forecast_actual_id}")
def asset_forecast_performance_run(asset_id: str, forecast_actual_id: int):
    run = get_forecast_performance_run(forecast_actual_id)

    if run is None or run["asset_id"] != asset_id:
        return {
            "status": "not_found",
            "message": (
                "Forecast performance run not found for asset "
                f"{asset_id}: {forecast_actual_id}"
            ),
        }

    return {
        "status": "ok",
        "asset_id": asset_id,
        "forecast_performance": run,
    }
