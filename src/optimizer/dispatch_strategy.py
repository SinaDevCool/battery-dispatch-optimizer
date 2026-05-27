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