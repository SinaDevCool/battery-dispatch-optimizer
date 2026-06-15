import pandas as pd

from backend.config.battery_config import DEFAULT_BATTERY_CONFIG, DEFAULT_STRATEGY_CONFIG
from backend.config.commercial_config import DEFAULT_COMMERCIAL_CONFIG
from backend.optimization.primitives.battery_optimizer import BatteryOptimizer
from backend.optimization.primitives.dispatch_strategy import find_daily_arbitrage_hours
from backend.features.battery_usage_features import build_battery_usage_features


OPTIMIZER_COMMERCIAL_KEYS = [
    "trading_fee_eur_per_mwh",
    "market_access_fee_eur_per_mwh",
    "grid_fee_import_eur_per_mwh",
    "grid_fee_export_eur_per_mwh",
    "tax_or_levy_eur_per_mwh",
    "degradation_cost_eur_per_mwh_throughput",
]


def classify_opportunity(profit_per_mw_day):
    if profit_per_mw_day >= 200:
        return "high"
    if profit_per_mw_day >= 100:
        return "medium"
    if profit_per_mw_day > 0:
        return "low"
    return "none"


def generate_battery_signal(
    price_data,
    battery_config=None,
    strategy_config=None,
    commercial_config=None,
):
    if battery_config is None:
        battery_config = DEFAULT_BATTERY_CONFIG

    if strategy_config is None:
        strategy_config = DEFAULT_STRATEGY_CONFIG

    if commercial_config is None:
        commercial_config = DEFAULT_COMMERCIAL_CONFIG

    optimizer_commercial_config = {
        key: value
        for key, value in commercial_config.items()
        if key in OPTIMIZER_COMMERCIAL_KEYS
    }

    optimizer_config = {
        **battery_config,
        **optimizer_commercial_config,
    }

    battery = BatteryOptimizer(**optimizer_config)

    strategy_hours = find_daily_arbitrage_hours(
        price_data=price_data,
        charge_hours=2,
        discharge_hours=2,
    )

    dispatch_rows = battery.optimize(
        price_data=price_data,
        strategy_hours=strategy_hours,
        **strategy_config,
    )

    if not dispatch_rows:
        return {
            "summary": {
                "signal": "NO_DATA",
                "total_pnl_eur": 0.0,
                "profit_per_mw_day": 0.0,
                "opportunity_level": "none",
                "charge_hours": 0,
                "discharge_hours": 0,
                "first_charge_timestamp": None,
                "first_discharge_timestamp": None,
            },
            "dispatch": [],
        }

    total_pnl_eur = dispatch_rows[-1]["total_pnl_eur"]
    battery_power_mw = battery_config["max_discharge_power_mw"]

    profit_per_mw_day = total_pnl_eur / battery_power_mw
    opportunity_level = classify_opportunity(profit_per_mw_day)

    charge_rows = [row for row in dispatch_rows if row["action"] == "charge"]
    discharge_rows = [row for row in dispatch_rows if row["action"] == "discharge"]

    usage_features = build_battery_usage_features(
    dispatch_rows=dispatch_rows,
    capacity_mwh=battery_config["capacity_mwh"],
    )

    signal = "ACTION" if total_pnl_eur > 0 else "NO_ACTION"

    summary = {
        "signal": signal,
        "total_pnl_eur": round(total_pnl_eur, 2),
        "profit_per_mw_day": round(profit_per_mw_day, 2),
        "opportunity_level": opportunity_level,
        "charge_hours": len(charge_rows),
        "discharge_hours": len(discharge_rows),
        "first_charge_timestamp": charge_rows[0]["timestamp"] if charge_rows else None,
        "first_discharge_timestamp": discharge_rows[0]["timestamp"] if discharge_rows else None,
        "charged_mwh": usage_features["charged_mwh"],
        "discharged_mwh": usage_features["discharged_mwh"],
        "throughput_mwh": usage_features["throughput_mwh"],
        "equivalent_full_cycles": usage_features["equivalent_full_cycles"],
    }

    return {
        "summary": summary,
        "dispatch": dispatch_rows,
    }


def dataframe_to_price_data(df, price_column="forecast_price"):
    required_cols = ["timestamp", price_column]

    for col in required_cols:
        if col not in df.columns:
            raise ValueError(f"Missing required column: {col}")

    price_data = []

    for _, row in df.iterrows():
        price_data.append(
            {
                "timestamp": str(row["timestamp"]),
                "price": float(row[price_column]),
            }
        )

    return price_data


def generate_signal_from_dataframe(
    forecast_df,
    price_column="forecast_price",
    battery_config=None,
    strategy_config=None,
    commercial_config=None,
):
    forecast_df = forecast_df.copy()

    forecast_df["timestamp"] = pd.to_datetime(
        forecast_df["timestamp"],
        errors="coerce",
    )

    forecast_df[price_column] = pd.to_numeric(
        forecast_df[price_column],
        errors="coerce",
    )

    forecast_df = forecast_df.dropna(subset=["timestamp", price_column])
    forecast_df = forecast_df.sort_values("timestamp")

    price_data = dataframe_to_price_data(
        forecast_df,
        price_column=price_column,
    )

    return generate_battery_signal(
        price_data=price_data,
        battery_config=battery_config,
        strategy_config=strategy_config,
        commercial_config=commercial_config,
    )



