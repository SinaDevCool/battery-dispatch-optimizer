def calculate_backtest_metrics(results):
    if not results:
        return {
            "total_pnl_eur": 0.0,
            "hours": 0,
            "charge_hours": 0,
            "discharge_hours": 0,
            "idle_hours": 0,
            "min_soc_mwh": None,
            "max_soc_mwh": None,
            "average_pnl_per_hour_eur": 0.0,
        }

    total_pnl_eur = results[-1]["total_pnl_eur"]
    hours = len(results)

    charge_hours = 0
    discharge_hours = 0
    idle_hours = 0

    soc_values = []
    pnl_values = []

    for row in results:
        action = row["action"]

        if action == "charge":
            charge_hours += 1
        elif action == "discharge":
            discharge_hours += 1
        else:
            idle_hours += 1

        soc_values.append(row["soc_mwh"])
        pnl_values.append(row["pnl_eur"])

    average_pnl_per_hour_eur = sum(pnl_values) / hours

    return {
        "total_pnl_eur": round(total_pnl_eur, 2),
        "hours": hours,
        "charge_hours": charge_hours,
        "discharge_hours": discharge_hours,
        "idle_hours": idle_hours,
        "min_soc_mwh": round(min(soc_values), 4),
        "max_soc_mwh": round(max(soc_values), 4),
        "average_pnl_per_hour_eur": round(average_pnl_per_hour_eur, 2),
    }


def print_backtest_metrics(metrics):
    print("\nBacktest Summary")
    print("=" * 40)
    print(f"Total PnL: {metrics['total_pnl_eur']:.2f} EUR")
    print(f"Hours: {metrics['hours']}")
    print(f"Charge hours: {metrics['charge_hours']}")
    print(f"Discharge hours: {metrics['discharge_hours']}")
    print(f"Idle hours: {metrics['idle_hours']}")
    print(f"Min SOC: {metrics['min_soc_mwh']} MWh")
    print(f"Max SOC: {metrics['max_soc_mwh']} MWh")
    print(f"Average PnL/hour: {metrics['average_pnl_per_hour_eur']:.2f} EUR")