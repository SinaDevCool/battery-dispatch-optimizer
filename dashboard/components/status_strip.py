import streamlit as st

from dashboard.api_client import get_json


def render_status_strip():
    latest_signal = get_json("/battery/signal/latest")

    if latest_signal is None or latest_signal.get("status") != "ok":
        st.info("No latest battery signal available yet.")
        return

    signal_data = latest_signal.get("data", {})
    summary = signal_data.get("summary", {})
    metadata = signal_data.get("metadata", {})

    forecast_source = metadata.get("source", "-")
    target_date = metadata.get("target_date", "-")
    latest_signal_value = summary.get("signal", "-")
    expected_pnl = summary.get("total_pnl_eur", 0)

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Forecast Source", forecast_source)
    col2.metric("Target Date", target_date)
    col3.metric("Latest Signal", latest_signal_value)
    col4.metric("Expected PnL", f"{expected_pnl} EUR")