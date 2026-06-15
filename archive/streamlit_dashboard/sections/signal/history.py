import pandas as pd
import streamlit as st

from archive.streamlit_dashboard.api_client import get_json


def render_signal_history_section():
    st.header("Signal Run History")

    history_data = get_json("/battery/signal/history")

    if history_data is None:
        st.warning("Could not load signal run history.")
        return

    if history_data.get("status") != "ok":
        st.info(history_data.get("message", "No signal run history found yet."))
        return

    runs = history_data.get("runs", [])

    if not runs:
        st.info("No historical signal runs saved yet.")
        return

    history_df = pd.DataFrame(runs)

    st.dataframe(history_df, use_container_width=True)

    selected_run_file = st.selectbox(
        "Select historical run",
        history_df["file_name"].tolist(),
    )

    if selected_run_file:
        selected_run_response = get_json(
            f"/battery/signal/history/{selected_run_file}"
        )

        selected_dispatch = []

        if (
            selected_run_response
            and selected_run_response.get("status") == "ok"
        ):
            selected_run = selected_run_response["data"]

            st.subheader("Selected Historical Run")

            selected_summary = selected_run.get("summary", {})
            selected_dispatch = selected_run.get("dispatch", [])

            col1, col2, col3, col4 = st.columns(4)

            col1.metric("Signal", selected_summary.get("signal", "-"))
            col2.metric(
                "Opportunity",
                selected_summary.get("opportunity_level", "-"),
            )
            col3.metric(
                "Total PnL",
                f"{selected_summary.get('total_pnl_eur', 0)} EUR",
            )
            col4.metric(
                "Profit per MW-day",
                f"{selected_summary.get('profit_per_mw_day', 0)} EUR/MW-day",
            )

        if selected_dispatch:
            selected_dispatch_df = pd.DataFrame(selected_dispatch)
            selected_dispatch_df["timestamp"] = pd.to_datetime(
                selected_dispatch_df["timestamp"],
                errors="coerce",
            )

            st.line_chart(
                selected_dispatch_df,
                x="timestamp",
                y="total_pnl_eur",
                use_container_width=True,
            )

            st.dataframe(selected_dispatch_df, use_container_width=True)
        else:
            st.info("Selected run has no dispatch rows.")

    history_csv = history_df.to_csv(index=False).encode("utf-8")

    st.download_button(
        label="Download Run History CSV",
        data=history_csv,
        file_name="battery_signal_run_history.csv",
        mime="text/csv",
    )




