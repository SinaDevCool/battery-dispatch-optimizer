import streamlit as st


def render_strategy_config_section(strategy_cfg):
    st.subheader("Strategy")

    col1, col2, col3 = st.columns(3)

    with col1:
        low_price_threshold = st.number_input(
            "Low price threshold EUR/MWh",
            value=float(strategy_cfg["low_price_threshold"]),
        )

    with col2:
        high_price_threshold = st.number_input(
            "High price threshold EUR/MWh",
            value=float(strategy_cfg["high_price_threshold"]),
        )

    with col3:
        timestep_hours = st.number_input(
            "Timestep hours",
            min_value=0.25,
            value=float(strategy_cfg["timestep_hours"]),
        )

    return {
        "low_price_threshold": low_price_threshold,
        "high_price_threshold": high_price_threshold,
        "timestep_hours": timestep_hours,
    }
