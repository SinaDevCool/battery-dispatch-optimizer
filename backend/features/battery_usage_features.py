import pandas as pd


def build_battery_usage_features(dispatch_rows, capacity_mwh):
    if not dispatch_rows:
        return {
            "charged_mwh": 0.0,
            "discharged_mwh": 0.0,
            "throughput_mwh": 0.0,
            "equivalent_full_cycles": 0.0,
        }

    dispatch_df = pd.DataFrame(dispatch_rows)

    if "action" not in dispatch_df.columns or "battery_energy_mwh" not in dispatch_df.columns:
        raise ValueError("Dispatch rows must contain action and battery_energy_mwh.")

    dispatch_df["battery_energy_mwh"] = pd.to_numeric(
        dispatch_df["battery_energy_mwh"],
        errors="coerce",
    ).fillna(0)

    charged_mwh = dispatch_df.loc[
        dispatch_df["action"] == "charge",
        "battery_energy_mwh",
    ].sum()

    discharged_mwh = dispatch_df.loc[
        dispatch_df["action"] == "discharge",
        "battery_energy_mwh",
    ].sum()

    throughput_mwh = charged_mwh + discharged_mwh

    equivalent_full_cycles = 0.0

    if capacity_mwh > 0:
        equivalent_full_cycles = throughput_mwh / (2 * capacity_mwh)

    return {
        "charged_mwh": round(float(charged_mwh), 4),
        "discharged_mwh": round(float(discharged_mwh), 4),
        "throughput_mwh": round(float(throughput_mwh), 4),
        "equivalent_full_cycles": round(float(equivalent_full_cycles), 4),
    }


