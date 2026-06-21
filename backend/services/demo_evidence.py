from __future__ import annotations

from pathlib import Path

import pandas as pd

from backend.config.paths import ACTUAL_PRICE_FILE, FORECAST_FILE


DEMO_ASSET_IDS = {
    "default_site",
    "demo_solar_battery",
    "demo_industrial_btm",
}


DEMO_REVENUE_ASSUMPTIONS = {
    "intraday_arbitrage": {
        "estimated_revenue_eur": 185.4,
        "source": "mock_intraday_curve",
        "assumptions": {
            "intraday_liquidity_assumption": "moderate",
            "execution_cost_assumption_eur_per_mwh": 1.8,
            "price_source": "mock_demo_intraday_shape",
        },
        "message": "Demo intraday revenue uses a synthetic intraday price shape and conservative execution cost.",
    },
    "fcr_capacity": {
        "estimated_revenue_eur": 620.0,
        "source": "mock_fcr_capacity_curve",
        "assumptions": {
            "fcr_capacity_price_eur_per_mw_h": 31.0,
            "prequalified_fcr": True,
            "reserve_availability_hours": 20,
            "activation_energy_assumption": "symmetric_capacity_only_demo",
        },
        "message": "Demo FCR revenue assumes mock prequalification and capacity availability evidence.",
    },
    "afrr_capacity": {
        "estimated_revenue_eur": 410.0,
        "source": "mock_afrr_capacity_curve",
        "assumptions": {
            "afrr_capacity_price_eur_per_mw_h": 20.5,
            "prequalified_afrr": True,
            "reserve_availability_hours": 20,
            "activation_energy_assumption": "activation_energy_not_settled_in_demo",
        },
        "message": "Demo aFRR revenue uses mock capacity price and prequalification evidence.",
    },
    "mfrr_capacity": {
        "estimated_revenue_eur": 285.0,
        "source": "mock_mfrr_capacity_curve",
        "assumptions": {
            "mfrr_capacity_price_eur_per_mw_h": 14.25,
            "prequalified_mfrr": True,
            "reserve_availability_hours": 20,
            "activation_energy_assumption": "manual_activation_demo_placeholder",
        },
        "message": "Demo mFRR revenue uses mock capacity price and manual activation assumptions.",
    },
    "imbalance_avoidance": {
        "estimated_revenue_eur": 96.25,
        "source": "mock_imbalance_exposure",
        "assumptions": {
            "imbalance_price_series": "mock_demo_imbalance_prices",
            "schedule_deviation_series": "mock_demo_schedule_deviation",
            "balancing_responsible_party": "Demo BRP",
        },
        "message": "Demo imbalance value uses synthetic imbalance price and schedule-deviation evidence.",
    },
}


def is_demo_asset(asset) -> bool:
    return (
        getattr(asset, "asset_id", None) in DEMO_ASSET_IDS
        and getattr(asset, "data_mode", "mock") == "mock"
    )


def get_demo_revenue_assumption(asset, product_id: str) -> dict | None:
    if not is_demo_asset(asset):
        return None

    return DEMO_REVENUE_ASSUMPTIONS.get(product_id)


def get_demo_regulatory_value(asset, field_name: str):
    if not is_demo_asset(asset):
        return None

    for evidence in DEMO_REVENUE_ASSUMPTIONS.values():
        assumptions = evidence.get("assumptions", {})
        if field_name in assumptions:
            return assumptions[field_name]

    return None


def seed_demo_actual_prices(
    forecast_file: Path = FORECAST_FILE,
    actual_file: Path = ACTUAL_PRICE_FILE,
):
    forecast_file = Path(forecast_file)
    actual_file = Path(actual_file)

    if not forecast_file.exists():
        return {
            "status": "not_found",
            "message": f"Forecast file not found, cannot seed demo actual prices: {forecast_file}",
        }

    forecast = pd.read_csv(forecast_file)
    if "timestamp" not in forecast.columns or "forecast_price" not in forecast.columns:
        return {
            "status": "invalid",
            "message": "Forecast file must contain timestamp and forecast_price columns.",
        }

    actual = forecast[["timestamp", "forecast_price"]].copy()
    pattern = [-1.5, -0.8, 0.4, 1.1, 0.6, -0.5, 0.9, -1.0]
    actual["actual_price"] = [
        round(float(price) + pattern[index % len(pattern)], 2)
        for index, price in enumerate(actual["forecast_price"])
    ]
    actual["price"] = actual["actual_price"]
    actual["actual_price_eur_per_mwh"] = actual["actual_price"]
    actual["source"] = "mock_demo_actual_prices"

    actual_file.parent.mkdir(parents=True, exist_ok=True)
    actual[[
        "timestamp",
        "actual_price",
        "actual_price_eur_per_mwh",
        "price",
        "source",
    ]].to_csv(actual_file, index=False)

    return {
        "status": "ok",
        "actual_price_file": str(actual_file),
        "row_count": len(actual),
        "source": "mock_demo_actual_prices",
        "production_upgrade": "Replace this mock file with official actual-price ingestion before production use.",
    }
