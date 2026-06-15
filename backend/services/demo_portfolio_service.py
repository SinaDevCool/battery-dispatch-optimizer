import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from backend.config.paths import FORECAST_FILE, OUTPUT_DATA_DIR
from backend.execution.pretrade_proposal import build_execution_proposal
from backend.forecasts.forecast_comparison import compare_forecast_profitability
from backend.forecasts.inhouse_forecast_provider import build_next_day_inhouse_forecast
from backend.revenue.revenue_stack_allocator import run_revenue_stack_allocation
from backend.services.asset_cockpit_service import build_asset_cockpit
from backend.services.asset_workflow_service import run_asset_audited_workflow
from backend.services.forecast_service import save_forecast_dataframe


def run_complete_demo_portfolio(
    asset_id="default_site",
    optimizer_engine="rule_based_v1",
):
    forecast_outputs = seed_demo_forecasts()
    comparison_forecast_files = {
        "local_saved_forecast": Path("data/processed/local_saved_forecast.csv"),
        "demo_high_spread": Path("data/processed/demo_high_spread_forecast.csv"),
        "inhouse_placeholder": Path("data/processed/inhouse_placeholder_forecast.csv"),
    }
    comparison_results = compare_forecast_profitability(comparison_forecast_files)
    comparison_file = OUTPUT_DATA_DIR / "forecast_profitability_comparison.json"
    comparison_file.parent.mkdir(parents=True, exist_ok=True)

    with open(comparison_file, "w", encoding="utf-8") as file:
        json.dump(comparison_results, file, indent=2, default=str)

    workflow = run_asset_audited_workflow(
        asset_id=asset_id,
        optimizer_engine=optimizer_engine,
    )
    allocation = run_revenue_stack_allocation(
        asset_id=asset_id,
        optimizer_engine=optimizer_engine,
        refresh_revenue_stack=False,
    )
    execution_proposal = build_execution_proposal(asset_id)
    cockpit = build_asset_cockpit(asset_id)

    return {
        "status": "ok",
        "message": "Complete demo portfolio workflow completed successfully.",
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "asset_id": asset_id,
        "optimizer_engine": optimizer_engine,
        "forecast_outputs": forecast_outputs,
        "forecast_comparison": {
            "comparison_file": str(comparison_file),
            "results": comparison_results,
        },
        "workflow_run": workflow.get("workflow_run"),
        "revenue_allocation": allocation,
        "execution_proposal": execution_proposal,
        "cockpit": cockpit.get("cockpit"),
    }


def seed_demo_forecasts():
    base_df = build_demo_forecast_dataframe(
        provider="demo",
        model="demo_base_15min",
        prices=[
            42, 38, 30, 22, 15, 8,
            12, 28, 55, 72, 85, 92,
            88, 75, 60, 48, 52, 70,
            96, 120, 110, 82, 58, 45,
        ],
    )
    high_spread_df = build_demo_forecast_dataframe(
        provider="demo_high_spread",
        model="demo_high_spread_15min",
        prices=[
            55, 48, 40, 28, 12, -5,
            -8, 20, 58, 85, 110, 125,
            118, 95, 72, 55, 62, 88,
            130, 155, 145, 100, 75, 60,
        ],
    )
    inhouse_df = build_next_day_inhouse_forecast()

    save_forecast_dataframe(base_df, Path("data/processed/local_saved_forecast.csv"))
    active_forecast = save_forecast_dataframe(high_spread_df, FORECAST_FILE)
    save_forecast_dataframe(
        high_spread_df,
        Path("data/processed/demo_high_spread_forecast.csv"),
    )
    save_forecast_dataframe(
        inhouse_df,
        Path("data/processed/inhouse_placeholder_forecast.csv"),
    )

    return {
        "active_forecast_file": str(FORECAST_FILE),
        "active_forecast_provider": "demo_high_spread",
        "active_forecast_model": "demo_high_spread_15min",
        "active_forecast_rows": len(active_forecast),
        "comparison_forecast_files": [
            "data/processed/local_saved_forecast.csv",
            "data/processed/demo_high_spread_forecast.csv",
            "data/processed/inhouse_placeholder_forecast.csv",
        ],
    }


def build_demo_forecast_dataframe(provider, model, prices):
    start_time = pd.Timestamp.now().normalize() + pd.Timedelta(days=1)
    created_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    rows = []

    for hour, price in enumerate(prices):
        for quarter in range(4):
            timestamp = (
                start_time
                + pd.Timedelta(hours=hour)
                + pd.Timedelta(minutes=15 * quarter)
            )
            rows.append(
                {
                    "timestamp": timestamp,
                    "forecast_price": price,
                    "forecast_provider": provider,
                    "forecast_model": model,
                    "market_profile_id": "de_lu_day_ahead",
                    "market_time_unit_minutes": 15,
                    "hour": timestamp.hour,
                    "date": str(timestamp.date()),
                    "created_at": created_at,
                }
            )

    return pd.DataFrame(rows)



