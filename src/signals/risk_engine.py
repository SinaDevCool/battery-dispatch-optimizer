import pandas as pd

from src.features.forecast_quality_features import build_forecast_quality_features
from src.features.negative_price_features import build_negative_price_features
from src.markets.market_profile_loader import get_default_market_profile


def build_risk_flags(signal_result, forecast_df=None):
    summary = signal_result.get("summary", {})
    dispatch = signal_result.get("dispatch", [])

    flags = []
    market_profile = get_default_market_profile()
    expected_intervals = int(market_profile.get("expected_intervals_per_day", 24))
    market_time_unit_minutes = int(market_profile.get("market_time_unit_minutes", 60))

    if not dispatch:
        return [
            {
                "level": "high",
                "type": "no_dispatch_data",
                "message": "No dispatch data is available.",
            }
        ]

    charge_rows = [
        row for row in dispatch
        if row.get("action") == "charge"
    ]

    discharge_rows = [
        row for row in dispatch
        if row.get("action") == "discharge"
    ]

    prices = [
        row["price"]
        for row in dispatch
        if "price" in row
    ]

    soc_values = [
        row["soc_mwh"]
        for row in dispatch
        if "soc_mwh" in row
    ]

    if len(dispatch) < expected_intervals:
        flags.append(
            {
                "level": "medium",
                "type": "short_forecast",
                "message": (
                    f"Forecast has only {len(dispatch)} rows. "
                    f"The {market_profile['market_profile_id']} profile expects "
                    f"{expected_intervals} rows at {market_time_unit_minutes}-minute resolution."
                ),
            }
        )

    if market_time_unit_minutes == 15 and len(dispatch) == 24:
        flags.append(
            {
                "level": "high",
                "type": "hourly_forecast_used_for_15min_market",
                "message": (
                    "The German day-ahead market profile expects 15-minute prices, "
                    "but this signal appears to use 24 hourly rows."
                ),
            }
        )

    negative_charge_rows = [
        row for row in charge_rows
        if row.get("price", 0) < 0
    ]

    if negative_charge_rows:
        flags.append(
            {
                "level": "high",
                "type": "negative_price_charging",
                "message": f"Battery charges during {len(negative_charge_rows)} negative-price hour(s).",
            }
        )

    if prices:
        price_spread = max(prices) - min(prices)

        if price_spread >= 100:
            flags.append(
                {
                    "level": "high",
                    "type": "high_price_spread",
                    "message": f"Large price spread detected: {price_spread:.2f} EUR/MWh.",
                }
            )

        elif price_spread >= 50:
            flags.append(
                {
                    "level": "medium",
                    "type": "medium_price_spread",
                    "message": f"Medium price spread detected: {price_spread:.2f} EUR/MWh.",
                }
            )

    if not charge_rows and not discharge_rows:
        flags.append(
            {
                "level": "low",
                "type": "no_action",
                "message": "No battery action was selected for this forecast.",
            }
        )

    if summary.get("opportunity_level") == "none":
        flags.append(
            {
                "level": "low",
                "type": "no_profit_opportunity",
                "message": "The model does not identify a profitable opportunity.",
            }
        )

    if soc_values:
        max_soc = max(soc_values)
        min_soc = min(soc_values)

        flags.append(
            {
                "level": "info",
                "type": "soc_range",
                "message": f"SOC ranges from {min_soc:.2f} MWh to {max_soc:.2f} MWh during the dispatch.",
            }
        )

    equivalent_full_cycles = summary.get("equivalent_full_cycles")

    if equivalent_full_cycles is not None:
        if equivalent_full_cycles >= 1.0:
            flags.append(
                {
                    "level": "high",
                    "type": "high_cycle_usage",
                    "message": f"Equivalent full cycles are high for one day: {equivalent_full_cycles:.2f}.",
                }
            )

        elif equivalent_full_cycles >= 0.5:
            flags.append(
                {
                    "level": "medium",
                    "type": "medium_cycle_usage",
                    "message": f"Equivalent full cycles are moderate: {equivalent_full_cycles:.2f}.",
                }
            )

    if forecast_df is not None:
        quality_features = build_forecast_quality_features(
            forecast_df,
            price_column="forecast_price",
        )

        negative_features = build_negative_price_features(
            forecast_df,
            price_column="forecast_price",
        )

        if quality_features.get("valid_row_count", 0) < expected_intervals:
            flags.append(
                {
                    "level": "medium",
                    "type": "forecast_quality_short_forecast",
                    "message": (
                        "Forecast quality check confirms fewer than "
                        f"{expected_intervals} valid forecast rows for the market profile."
                    ),
                }
            )

        if quality_features.get("interval_gap_count", 0) > 0:
            flags.append(
                {
                    "level": "medium",
                    "type": "forecast_interval_gaps",
                    "message": "Forecast contains timestamp gaps for the expected market interval.",
                }
            )

        if quality_features.get("duplicate_timestamps", 0) > 0:
            flags.append(
                {
                    "level": "high",
                    "type": "forecast_duplicate_timestamps",
                    "message": "Forecast contains duplicate timestamps.",
                }
            )

        if quality_features.get("missing_prices", 0) > 0:
            flags.append(
                {
                    "level": "high",
                    "type": "forecast_missing_prices",
                    "message": "Forecast contains missing or invalid prices.",
                }
            )

        if negative_features.get("negative_price_hours", 0) > 0:
            flags.append(
                {
                    "level": "info",
                    "type": "forecast_negative_prices",
                    "message": f"Forecast contains {negative_features['negative_price_hours']} negative-price hour(s).",
                }
            )

    if not flags:
        flags.append(
            {
                "level": "info",
                "type": "normal",
                "message": "No major risk flags detected.",
            }
        )

    return flags
