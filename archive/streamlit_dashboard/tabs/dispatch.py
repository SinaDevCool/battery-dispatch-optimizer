import pandas as pd
import streamlit as st

from archive.streamlit_dashboard.api_client import get_json


def render_dispatch_tab():
    st.header("Dispatch Schedule")

    latest_signal = get_json("/battery/signal/latest")

    if latest_signal is None:
        st.warning("Could not load latest battery signal.")
        return

    if latest_signal.get("status") != "ok":
        st.warning(latest_signal.get("message", "No latest signal available."))
        st.info("Generate a daily battery signal first.")
        return

    signal_data = latest_signal["data"]
    dispatch = signal_data.get("dispatch", [])

    if not dispatch:
        st.info("No dispatch rows available.")
        return

    dispatch_df = pd.DataFrame(dispatch)
    dispatch_df["timestamp"] = pd.to_datetime(
        dispatch_df["timestamp"],
        errors="coerce",
    )

    selected_actions = st.multiselect(
        "Filter dispatch actions",
        options=["charge", "discharge", "idle"],
        default=["charge", "discharge", "idle"],
    )

    st.subheader("Forecast + Dispatch View")

    display_columns = [
        "timestamp",
        "price",
        "action",
        "soc_mwh",
        "grid_energy_mwh",
        "battery_energy_mwh",
        "market_value_eur",
        "cost_eur",
        "pnl_eur",
        "total_pnl_eur",
    ]

    available_columns = [
        column for column in display_columns
        if column in dispatch_df.columns
    ]

    dispatch_view_df = dispatch_df[available_columns].copy()

    if "action" in dispatch_view_df.columns:
        filtered_dispatch_view_df = dispatch_view_df[
            dispatch_view_df["action"].isin(selected_actions)
        ]
    else:
        filtered_dispatch_view_df = dispatch_view_df

    st.dataframe(
        filtered_dispatch_view_df,
        use_container_width=True,
    )

    st.subheader("Forecast Price")

    if "price" in dispatch_df.columns:
        st.line_chart(
            dispatch_df,
            x="timestamp",
            y="price",
            use_container_width=True,
        )
    else:
        st.info("No price column found in dispatch data.")

    st.subheader("Battery SOC")

    if "soc_mwh" in dispatch_df.columns:
        st.line_chart(
            dispatch_df,
            x="timestamp",
            y="soc_mwh",
            use_container_width=True,
        )
    else:
        st.info("No SOC column found in dispatch data.")

    st.subheader("Cumulative PnL")

    if "total_pnl_eur" in dispatch_df.columns:
        st.line_chart(
            dispatch_df,
            x="timestamp",
            y="total_pnl_eur",
            use_container_width=True,
        )
    else:
        st.info("No cumulative PnL column found in dispatch data.")

    dispatch_csv = filtered_dispatch_view_df.to_csv(index=False).encode("utf-8")

    st.download_button(
        label="Download Dispatch CSV",
        data=dispatch_csv,
        file_name="battery_dispatch_schedule.csv",
        mime="text/csv",
    )



