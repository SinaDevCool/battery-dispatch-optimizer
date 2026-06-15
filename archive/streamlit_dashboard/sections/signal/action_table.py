import pandas as pd
import streamlit as st


def render_signal_action_table_section(dispatch):
    action_rows = [
        row for row in dispatch
        if row["action"] in ["charge", "discharge"]
    ]

    st.subheader("Why This Action?")

    if not action_rows:
        st.info("No charge or discharge actions selected.")
        return

    action_df = pd.DataFrame(action_rows)

    display_columns = [
        "timestamp",
        "price",
        "action",
        "grid_energy_mwh",
        "battery_energy_mwh",
        "market_value_eur",
        "cost_eur",
        "pnl_eur",
    ]

    available_columns = [
        column for column in display_columns
        if column in action_df.columns
    ]

    st.dataframe(
        action_df[available_columns],
        use_container_width=True,
    )




