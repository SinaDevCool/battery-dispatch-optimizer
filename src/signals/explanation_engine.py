import pandas as pd

from src.features.forecast_quality_features import build_forecast_quality_features
from src.features.negative_price_features import build_negative_price_features
from src.markets.market_profile_loader import get_default_market_profile


def format_price(price):
    return f"{price:.2f} EUR/MWh"


def format_money(value):
    return f"{value:.2f} EUR"


def explain_battery_signal(signal_result, forecast_df=None):
    summary = signal_result.get("summary", {})
    dispatch = signal_result.get("dispatch", [])
    metadata = signal_result.get("metadata", {})

    if not dispatch:
        return {
            "status": "no_data",
            "explanation": "No dispatch data is available, so no battery signal explanation can be generated.",
        }

    charge_rows = [
        row for row in dispatch
        if row.get("action") == "charge"
    ]

    discharge_rows = [
        row for row in dispatch
        if row.get("action") == "discharge"
    ]

    if not charge_rows and not discharge_rows:
        return {
            "status": "ok",
            "explanation": (
                "The model does not recommend battery action for this forecast. "
                "No charge or discharge hours were selected because the price opportunity was not strong enough."
            ),
        }

    lowest_charge_price = min(
        [row["price"] for row in charge_rows],
        default=None,
    )

    highest_discharge_price = max(
        [row["price"] for row in discharge_rows],
        default=None,
    )

    charge_times = [
        row["timestamp"]
        for row in charge_rows
    ]

    discharge_times = [
        row["timestamp"]
        for row in discharge_rows
    ]

    explanation_parts = []

    source = metadata.get("source")
    target_date = metadata.get("target_date")

    if source:
        if target_date:
            explanation_parts.append(
                f"The signal was generated from {source} forecast data for {target_date}."
            )
        else:
            explanation_parts.append(
                f"The signal was generated from {source} forecast data."
            )

    if charge_rows:
        explanation_parts.append(
            "The model recommends charging during the lowest-price forecast hours: "
            + ", ".join(charge_times)
            + "."
        )

        if lowest_charge_price is not None:
            if lowest_charge_price < 0:
                explanation_parts.append(
                    f"The lowest charge price is {format_price(lowest_charge_price)}, "
                    "so the battery is paid to consume energy during that hour."
                )
            else:
                explanation_parts.append(
                    f"The lowest selected charge price is {format_price(lowest_charge_price)}."
                )

    if discharge_rows:
        explanation_parts.append(
            "The model recommends discharging during the highest-price forecast hours: "
            + ", ".join(discharge_times)
            + "."
        )

        if highest_discharge_price is not None:
            explanation_parts.append(
                f"The highest selected discharge price is {format_price(highest_discharge_price)}."
            )

    if lowest_charge_price is not None and highest_discharge_price is not None:
        spread = highest_discharge_price - lowest_charge_price

        explanation_parts.append(
            f"The maximum observed spread between selected charge and discharge prices is {format_price(spread)}."
        )

    dispatch_df = pd.DataFrame(dispatch)

    if "market_value_eur" in dispatch_df.columns and "cost_eur" in dispatch_df.columns:
        market_value = dispatch_df["market_value_eur"].sum()
        commercial_costs = dispatch_df["cost_eur"].sum()

        if commercial_costs > 0:
            explanation_parts.append(
                f"Commercial costs reduce the dispatch value by {format_money(commercial_costs)}. "
                f"The gross market value is {format_money(market_value)}."
            )

    total_pnl = summary.get("total_pnl_eur", 0.0)
    profit_per_mw_day = summary.get("profit_per_mw_day", 0.0)
    opportunity_level = summary.get("opportunity_level", "none")
    equivalent_full_cycles = summary.get("equivalent_full_cycles")
    throughput_mwh = summary.get("throughput_mwh")

    explanation_parts.append(
        f"The expected total PnL is {format_money(total_pnl)}, "
        f"equal to {profit_per_mw_day:.2f} EUR/MW-day. "
        f"This is classified as a {opportunity_level} opportunity."
    )

    if equivalent_full_cycles is not None and throughput_mwh is not None:
        explanation_parts.append(
        f"The schedule uses {throughput_mwh:.2f} MWh of battery throughput, "
        f"equal to {equivalent_full_cycles:.2f} equivalent full cycle(s)."
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

        valid_rows = quality_features.get("valid_row_count")

        if valid_rows is not None:
            explanation_parts.append(
                f"The forecast quality check found {valid_rows} valid row(s)."
            )

        market_profile = get_default_market_profile()
        expected_intervals = market_profile.get("expected_intervals_per_day", 24)

        if valid_rows is not None and valid_rows < expected_intervals:
            explanation_parts.append(
                "Because the forecast has fewer than "
                f"{expected_intervals} valid rows for "
                f"{market_profile['market_profile_id']}, this should be treated "
                "as a partial-day or demo signal."
            )

        negative_hours = negative_features.get("negative_price_hours", 0)

        if negative_hours > 0:
            explanation_parts.append(
                f"The forecast includes {negative_hours} negative-price hour(s), which can improve charging economics."
            )

    return {
        "status": "ok",
        "explanation": " ".join(explanation_parts),
    }
