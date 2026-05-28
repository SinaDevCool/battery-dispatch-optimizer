def build_risk_flags(signal_result):
    summary = signal_result.get("summary", {})
    dispatch = signal_result.get("dispatch", [])

    flags = []

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

    if len(dispatch) < 24:
        flags.append(
            {
                "level": "medium",
                "type": "short_forecast",
                "message": f"Forecast has only {len(dispatch)} rows. A full next-day forecast usually has 24 hourly rows.",
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

    if not flags:
        flags.append(
            {
                "level": "info",
                "type": "normal",
                "message": "No major risk flags detected.",
            }
        )

    return flags