from datetime import datetime, timezone

import pandas as pd


def build_next_day_inhouse_forecast():
    start_time = pd.Timestamp.now().normalize() + pd.Timedelta(days=1)

    prices = [
        46, 42, 35, 24, 10, -2,
        4, 18, 50, 78, 98, 108,
        102, 86, 66, 54, 60, 82,
        112, 138, 128, 96, 70, 52,
    ]

    rows = []
    created_at = datetime.now(timezone.utc).isoformat(timespec="seconds")

    for hour, price in enumerate(prices):
        timestamp = start_time + pd.Timedelta(hours=hour)

        rows.append(
            {
                "timestamp": timestamp,
                "forecast_price": price,
                "load_forecast": None,
                "generation_forecast": None,
                "forecast_solar": None,
                "forecast_wind": None,
                "forecast_renewables_total": None,
                "hour": timestamp.hour,
                "date": str(timestamp.date()),
                "forecast_provider": "inhouse_placeholder",
                "forecast_model": "inhouse_placeholder_v0",
                "created_at": created_at,
            }
        )

    return pd.DataFrame(rows)
