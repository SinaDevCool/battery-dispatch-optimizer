import json
from datetime import datetime
from pathlib import Path

from backend.assets.asset_loader import load_assets
from backend.config.paths import FORECAST_FILE, PORTFOLIO_RESULTS_FILE
from backend.services.asset_dispatch_service import (
    add_asset_dispatch_validation,
    build_asset_signal_metadata,
    dispatch_asset,
)
from backend.services.asset_signal_store import save_asset_signal
from backend.services.signal_service import add_signal_metadata


def run_portfolio_dispatch(
    assets=None,
    optimizer_engine="rule_based_v1",
    output_file=PORTFOLIO_RESULTS_FILE,
):
    if assets is None:
        assets = load_assets()

    asset_results = []

    for asset in assets:
        forecast_file = Path(asset.forecast_file) if asset.forecast_file else FORECAST_FILE

        if not forecast_file.exists():
            asset_results.append(
                {
                    "asset_id": asset.asset_id,
                    "client_name": asset.client_name,
                    "site_name": asset.site_name,
                    "country": asset.country,
                    "market": asset.market,
                    "status": "not_found",
                    "message": f"Forecast file not found: {forecast_file}",
                }
            )
            continue

        try:
            asset_dispatch_result = dispatch_asset(
                asset=asset,
                forecast_file=forecast_file,
                optimizer_engine=optimizer_engine,
            )
            dispatch_result = asset_dispatch_result.dispatch_result

            asset_metadata = build_asset_signal_metadata(asset_dispatch_result)
            signal_result = add_signal_metadata(
                signal_result=dispatch_result.signal_result,
                source="asset_forecast_file",
                forecast_model="asset_forecast_file",
                target_date=None,
                forecast_file=forecast_file,
                extra_metadata=asset_metadata,
            )
            signal_result = add_asset_dispatch_validation(
                signal_result=signal_result,
                asset_dispatch_result=asset_dispatch_result,
            )
            saved_asset_signal_files = save_asset_signal(
                signal_result=signal_result,
                asset_id=asset.asset_id,
            )

            summary = signal_result["summary"]

            asset_results.append(
                {
                    "asset_id": asset.asset_id,
                    "client_name": asset.client_name,
                    "site_name": asset.site_name,
                    "country": asset.country,
                    "market": asset.market,
                    "market_profile_id": asset.market_profile_id,
                    "grid_connection": asset.grid_connection,
                    "regulatory": asset.regulatory,
                    "constrained_battery_config": asset_dispatch_result.constrained_battery_config,
                    "forecast_file": str(forecast_file),
                    "optimizer_engine": dispatch_result.optimizer_engine,
                    "status": "ok",
                    "asset_latest_signal_file": str(
                        saved_asset_signal_files["asset_latest_signal_file"]
                    ),
                    "asset_run_file": str(saved_asset_signal_files["asset_run_file"]),
                    "signal_id": saved_asset_signal_files["signal_id"],
                    "summary": summary,
                    "dispatch": signal_result["dispatch"],
                    "optimization": signal_result.get("optimization", {}),
                    "validation": signal_result["validation"],
                    "asset_metadata": asset_metadata,
                    "assumption_risk_flags": asset_dispatch_result.assumption_risk_flags,
                }
            )

        except Exception as error:
            asset_results.append(
                {
                    "asset_id": asset.asset_id,
                    "client_name": asset.client_name,
                    "site_name": asset.site_name,
                    "country": asset.country,
                    "market": asset.market,
                    "forecast_file": str(forecast_file),
                    "optimizer_engine": optimizer_engine,
                    "status": "error",
                    "message": str(error),
                }
            )

    portfolio_summary = build_portfolio_summary(asset_results)

    result = {
        "status": "ok",
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "optimizer_engine": optimizer_engine,
        "portfolio_summary": portfolio_summary,
        "assets": asset_results,
    }

    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, "w", encoding="utf-8") as file:
        json.dump(result, file, indent=2)

    return result


def build_portfolio_summary(asset_results):
    ok_results = [
        result for result in asset_results
        if result.get("status") == "ok"
    ]

    total_pnl_eur = sum(
        result["summary"].get("total_pnl_eur", 0.0)
        for result in ok_results
    )
    total_charge_hours = sum(
        result["summary"].get("charge_hours", 0)
        for result in ok_results
    )
    total_discharge_hours = sum(
        result["summary"].get("discharge_hours", 0)
        for result in ok_results
    )

    action_assets = [
        result for result in ok_results
        if result["summary"].get("signal") == "ACTION"
    ]

    return {
        "asset_count": len(asset_results),
        "successful_asset_count": len(ok_results),
        "failed_asset_count": len(asset_results) - len(ok_results),
        "action_asset_count": len(action_assets),
        "total_pnl_eur": round(total_pnl_eur, 2),
        "total_charge_hours": total_charge_hours,
        "total_discharge_hours": total_discharge_hours,
    }


def load_latest_portfolio_results(output_file=PORTFOLIO_RESULTS_FILE):
    if not output_file.exists():
        return {
            "status": "not_found",
            "message": "No portfolio results found. Run /portfolio/run-daily first.",
            "portfolio_summary": None,
            "assets": [],
        }

    with open(output_file, "r", encoding="utf-8") as file:
        return json.load(file)



