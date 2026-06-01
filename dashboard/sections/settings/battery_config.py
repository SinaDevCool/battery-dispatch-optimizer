import streamlit as st


def render_battery_config_section(battery_cfg):
    st.subheader("Battery")

    col1, col2, col3 = st.columns(3)

    with col1:
        capacity_mwh = st.number_input(
            "Capacity MWh",
            min_value=0.1,
            value=float(battery_cfg["capacity_mwh"]),
        )

        initial_soc_mwh = st.number_input(
            "Initial SOC MWh",
            min_value=0.0,
            value=float(battery_cfg["initial_soc_mwh"]),
        )

        min_soc_mwh = st.number_input(
            "Minimum SOC MWh",
            min_value=0.0,
            value=float(battery_cfg["min_soc_mwh"]),
        )

    with col2:
        max_charge_power_mw = st.number_input(
            "Max charge power MW",
            min_value=0.1,
            value=float(battery_cfg["max_charge_power_mw"]),
        )

        max_discharge_power_mw = st.number_input(
            "Max discharge power MW",
            min_value=0.1,
            value=float(battery_cfg["max_discharge_power_mw"]),
        )

    with col3:
        charge_efficiency = st.number_input(
            "Charge efficiency",
            min_value=0.01,
            max_value=1.0,
            value=float(battery_cfg["charge_efficiency"]),
        )

        discharge_efficiency = st.number_input(
            "Discharge efficiency",
            min_value=0.01,
            max_value=1.0,
            value=float(battery_cfg["discharge_efficiency"]),
        )

    return {
        "capacity_mwh": capacity_mwh,
        "initial_soc_mwh": initial_soc_mwh,
        "min_soc_mwh": min_soc_mwh,
        "max_charge_power_mw": max_charge_power_mw,
        "max_discharge_power_mw": max_discharge_power_mw,
        "charge_efficiency": charge_efficiency,
        "discharge_efficiency": discharge_efficiency,
    }
