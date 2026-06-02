import pandas as pd

from src.storage import get_storage_client


def file_status(path):
    return get_storage_client().file_status(path)


def validate_forecast_dataframe(df):
    required_columns = ["timestamp", "forecast_price"]

    missing_columns = [
        column for column in required_columns
        if column not in df.columns
    ]

    if missing_columns:
        return False, f"Missing required columns: {', '.join(missing_columns)}"

    df = df.copy()

    df["timestamp"] = pd.to_datetime(
        df["timestamp"],
        errors="coerce",
    )

    df["forecast_price"] = pd.to_numeric(
        df["forecast_price"],
        errors="coerce",
    )

    invalid_timestamps = df["timestamp"].isna().sum()
    missing_prices = df["forecast_price"].isna().sum()
    duplicate_timestamps = df["timestamp"].duplicated().sum()

    if invalid_timestamps > 0:
        return False, f"Forecast has {invalid_timestamps} invalid timestamps."

    if missing_prices > 0:
        return False, f"Forecast has {missing_prices} missing or invalid prices."

    if duplicate_timestamps > 0:
        return False, f"Forecast has {duplicate_timestamps} duplicate timestamps."

    if len(df) < 2:
        return False, "Forecast must contain at least 2 rows."

    return True, "Forecast is valid."


def validate_client_config(config):
    errors = []

    battery_config = config.get("battery_config", {})
    strategy_config = config.get("strategy_config", {})

    capacity_mwh = battery_config.get("capacity_mwh")
    initial_soc_mwh = battery_config.get("initial_soc_mwh")
    min_soc_mwh = battery_config.get("min_soc_mwh")
    max_charge_power_mw = battery_config.get("max_charge_power_mw")
    max_discharge_power_mw = battery_config.get("max_discharge_power_mw")
    charge_efficiency = battery_config.get("charge_efficiency")
    discharge_efficiency = battery_config.get("discharge_efficiency")

    low_price_threshold = strategy_config.get("low_price_threshold")
    high_price_threshold = strategy_config.get("high_price_threshold")
    timestep_hours = strategy_config.get("timestep_hours")

    required_fields = {
        "battery_config.capacity_mwh": capacity_mwh,
        "battery_config.initial_soc_mwh": initial_soc_mwh,
        "battery_config.min_soc_mwh": min_soc_mwh,
        "battery_config.max_charge_power_mw": max_charge_power_mw,
        "battery_config.max_discharge_power_mw": max_discharge_power_mw,
        "battery_config.charge_efficiency": charge_efficiency,
        "battery_config.discharge_efficiency": discharge_efficiency,
        "strategy_config.low_price_threshold": low_price_threshold,
        "strategy_config.high_price_threshold": high_price_threshold,
        "strategy_config.timestep_hours": timestep_hours,
    }

    for field_name, value in required_fields.items():
        if value is None:
            errors.append(f"Missing required field: {field_name}")

    if errors:
        return errors

    if capacity_mwh <= 0:
        errors.append("Battery capacity must be greater than 0.")

    if min_soc_mwh < 0:
        errors.append("Minimum SOC cannot be negative.")

    if min_soc_mwh >= capacity_mwh:
        errors.append("Minimum SOC must be lower than capacity.")

    if initial_soc_mwh < min_soc_mwh:
        errors.append("Initial SOC cannot be lower than minimum SOC.")

    if initial_soc_mwh > capacity_mwh:
        errors.append("Initial SOC cannot be greater than capacity.")

    if max_charge_power_mw <= 0:
        errors.append("Max charge power must be greater than 0.")

    if max_discharge_power_mw <= 0:
        errors.append("Max discharge power must be greater than 0.")

    if not 0 < charge_efficiency <= 1:
        errors.append("Charge efficiency must be between 0 and 1.")

    if not 0 < discharge_efficiency <= 1:
        errors.append("Discharge efficiency must be between 0 and 1.")

    if high_price_threshold <= low_price_threshold:
        errors.append("High price threshold must be greater than low price threshold.")

    if timestep_hours <= 0:
        errors.append("Timestep hours must be greater than 0.")

    return errors
