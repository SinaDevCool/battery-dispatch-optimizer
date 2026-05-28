def format_price(price):
    return f"{price:.2f} EUR/MWh"


def format_money(value):
    return f"{value:.2f} EUR"


def explain_battery_signal(signal_result):
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

    total_pnl = summary.get("total_pnl_eur", 0.0)
    profit_per_mw_day = summary.get("profit_per_mw_day", 0.0)
    opportunity_level = summary.get("opportunity_level", "none")

    explanation_parts.append(
        f"The expected total PnL is {format_money(total_pnl)}, "
        f"equal to {profit_per_mw_day:.2f} EUR/MW-day. "
        f"This is classified as a {opportunity_level} opportunity."
    )

    return {
        "status": "ok",
        "explanation": " ".join(explanation_parts),
    }