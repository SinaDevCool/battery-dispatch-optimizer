import pandas as pd

from backend.backtesting.forecast_actual.timestamps import normalize_market_timestamps


def replay_dispatch_against_actual_prices(signal_result, actual_df):
    dispatch = signal_result.get("dispatch", [])
    summary = signal_result.get("summary", {})

    if not dispatch:
        return {
            "status": "no_dispatch",
            "message": "Signal contains no dispatch rows to replay.",
            "predicted_pnl_eur": summary.get("total_pnl_eur", 0.0),
            "realized_pnl_eur": 0.0,
            "revenue_delta_eur": 0.0,
            "rows": [],
        }

    dispatch_df = pd.DataFrame(dispatch)
    actual = actual_df.copy()

    dispatch_df["timestamp"] = normalize_market_timestamps(dispatch_df["timestamp"])
    actual["timestamp"] = normalize_market_timestamps(actual["timestamp"])

    merged = dispatch_df.merge(
        actual[["timestamp", "actual_price"]],
        on="timestamp",
        how="inner",
    )

    if merged.empty:
        return {
            "status": "no_overlap",
            "message": "Dispatch and actual price data have no overlapping timestamps.",
            "predicted_pnl_eur": summary.get("total_pnl_eur", 0.0),
            "realized_pnl_eur": 0.0,
            "revenue_delta_eur": 0.0,
            "rows": [],
        }

    realized_rows = []
    total_realized_pnl = 0.0

    for row in merged.to_dict("records"):
        action = row.get("action")
        actual_price = float(row.get("actual_price", 0.0))
        grid_energy_mwh = float(row.get("grid_energy_mwh", 0.0))
        cost_eur = float(row.get("cost_eur", 0.0))

        if action == "charge":
            realized_market_value_eur = -actual_price * grid_energy_mwh
        elif action == "discharge":
            realized_market_value_eur = actual_price * grid_energy_mwh
        else:
            realized_market_value_eur = 0.0

        realized_pnl_eur = realized_market_value_eur - cost_eur
        total_realized_pnl += realized_pnl_eur

        forecast_price = row.get("price")
        if forecast_price is not None:
            forecast_price = float(forecast_price)

        forecast_pnl_eur = row.get("pnl_eur", 0.0)
        if forecast_pnl_eur is not None:
            forecast_pnl_eur = float(forecast_pnl_eur)

        realized_rows.append(
            {
                "timestamp": str(row["timestamp"]),
                "forecast_price": forecast_price,
                "actual_price": actual_price,
                "action": action,
                "grid_energy_mwh": round(grid_energy_mwh, 4),
                "cost_eur": round(cost_eur, 2),
                "forecast_pnl_eur": forecast_pnl_eur,
                "realized_market_value_eur": round(realized_market_value_eur, 2),
                "realized_pnl_eur": round(realized_pnl_eur, 2),
                "realized_total_pnl_eur": round(total_realized_pnl, 2),
            }
        )

    predicted_pnl = float(summary.get("total_pnl_eur", 0.0))
    realized_pnl = round(total_realized_pnl, 2)

    return {
        "status": "ok",
        "predicted_pnl_eur": round(predicted_pnl, 2),
        "realized_pnl_eur": realized_pnl,
        "revenue_delta_eur": round(realized_pnl - predicted_pnl, 2),
        "row_count": len(realized_rows),
        "rows": realized_rows,
    }



