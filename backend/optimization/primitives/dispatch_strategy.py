def get_simple_threshold_strategy(
    low_price_threshold=20.0,
    high_price_threshold=80.0,
    timestep_hours=1.0,
):
    return {
        "low_price_threshold": low_price_threshold,
        "high_price_threshold": high_price_threshold,
        "timestep_hours": timestep_hours,
    }


def get_conservative_strategy():
    return get_simple_threshold_strategy(
        low_price_threshold=10.0,
        high_price_threshold=100.0,
        timestep_hours=1.0,
    )


def get_aggressive_strategy():
    return get_simple_threshold_strategy(
        low_price_threshold=40.0,
        high_price_threshold=70.0,
        timestep_hours=1.0,
    )


def find_daily_arbitrage_hours(
    price_data,
    charge_hours=2,
    discharge_hours=2,
):
    if not price_data:
        return {
            "charge_timestamps": [],
            "discharge_timestamps": [],
        }

    sorted_by_price = sorted(price_data, key=lambda row: row["price"])

    cheap_rows = sorted_by_price[:charge_hours]
    expensive_rows = sorted_by_price[-discharge_hours:]

    charge_timestamps = [row["timestamp"] for row in cheap_rows]
    discharge_timestamps = [row["timestamp"] for row in expensive_rows]

    return {
        "charge_timestamps": charge_timestamps,
        "discharge_timestamps": discharge_timestamps,
    }


def get_action_for_timestamp(timestamp, strategy_hours):
    if timestamp in strategy_hours["charge_timestamps"]:
        return "charge"

    if timestamp in strategy_hours["discharge_timestamps"]:
        return "discharge"

    return "idle"


