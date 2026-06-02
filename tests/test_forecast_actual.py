import pandas as pd

from src.backtesting.forecast_actual.forecast_actual_comparison import (
    compare_forecast_to_actual,
)
from src.backtesting.forecast_actual.forecast_performance_repository import (
    get_forecast_performance_run,
    list_forecast_performance_runs,
    save_forecast_actual_run,
)
from src.backtesting.forecast_actual.realized_dispatch_replay import (
    replay_dispatch_against_actual_prices,
)


def test_compare_forecast_to_actual_metrics():
    forecast_df = pd.DataFrame(
        [
            {
                "timestamp": "2026-01-01 00:00:00",
                "forecast_price": 10.0,
            },
            {
                "timestamp": "2026-01-01 01:00:00",
                "forecast_price": 20.0,
            },
        ]
    )
    actual_df = pd.DataFrame(
        [
            {
                "timestamp": "2026-01-01 00:00:00",
                "actual_price": 12.0,
            },
            {
                "timestamp": "2026-01-01 01:00:00",
                "actual_price": 18.0,
            },
        ]
    )

    result = compare_forecast_to_actual(forecast_df, actual_df)

    assert result["status"] == "ok"
    assert result["metrics"]["row_count"] == 2
    assert result["metrics"]["mae_eur_per_mwh"] == 2.0
    assert result["metrics"]["rmse_eur_per_mwh"] == 2.0
    assert result["metrics"]["bias_eur_per_mwh"] == 0.0
    assert len(result["rows"]) == 2


def test_replay_dispatch_against_actual_prices():
    signal_result = {
        "summary": {
            "total_pnl_eur": 50.0,
        },
        "dispatch": [
            {
                "timestamp": "2026-01-01 00:00:00",
                "price": 10.0,
                "action": "charge",
                "grid_energy_mwh": 1.0,
                "cost_eur": 1.0,
                "pnl_eur": -11.0,
            },
            {
                "timestamp": "2026-01-01 01:00:00",
                "price": 80.0,
                "action": "discharge",
                "grid_energy_mwh": 1.0,
                "cost_eur": 2.0,
                "pnl_eur": 78.0,
            },
        ],
    }
    actual_df = pd.DataFrame(
        [
            {
                "timestamp": "2026-01-01 00:00:00",
                "actual_price": 20.0,
            },
            {
                "timestamp": "2026-01-01 01:00:00",
                "actual_price": 90.0,
            },
        ]
    )

    result = replay_dispatch_against_actual_prices(signal_result, actual_df)

    assert result["status"] == "ok"
    assert result["predicted_pnl_eur"] == 50.0
    assert result["realized_pnl_eur"] == 67.0
    assert result["revenue_delta_eur"] == 17.0
    assert result["row_count"] == 2


def test_forecast_performance_repository(tmp_path):
    db_file = tmp_path / "forecast_performance.sqlite"
    result = {
        "asset_id": "asset_1",
        "generated_at": "2026-01-02T00:00:00",
        "metadata": {
            "target_date": "2026-01-01",
            "forecast_provider": "local_saved_forecast",
            "forecast_model": "local_saved_forecast",
        },
        "forecast_error_metrics": {
            "row_count": 2,
            "mae_eur_per_mwh": 2.0,
            "rmse_eur_per_mwh": 2.0,
            "bias_eur_per_mwh": 0.0,
        },
        "realized_dispatch": {
            "predicted_pnl_eur": 50.0,
            "realized_pnl_eur": 67.0,
            "revenue_delta_eur": 17.0,
        },
    }

    run_id = save_forecast_actual_run(result, db_file=db_file)
    runs = list_forecast_performance_runs("asset_1", db_file=db_file)
    loaded = get_forecast_performance_run(run_id, db_file=db_file)

    assert run_id == 1
    assert len(runs) == 1
    assert runs[0]["asset_id"] == "asset_1"
    assert loaded["payload"]["asset_id"] == "asset_1"
