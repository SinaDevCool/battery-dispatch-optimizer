import streamlit as st

from dashboard.api_client import get_json, post_json


def render_signal_control_section():
    st.header("Daily Signal Control")

    if st.button("Generate Daily Battery Signal"):
        response = post_json("/battery/signal/run-latest")

        if response is None:
            st.error("Could not generate battery signal.")

        elif response.get("status") == "ok":
            st.success("Daily battery signal generated successfully.")
            st.rerun()

        else:
            st.warning(response.get("message", "Signal could not be generated."))

    latest_signal = get_json("/battery/signal/latest")

    st.header("Latest Battery Signal")

    if latest_signal is None:
        st.warning("Could not load latest signal.")
        return None

    if latest_signal.get("status") != "ok":
        st.warning(latest_signal.get("message", "No latest signal available."))
        st.info("Click Generate Daily Battery Signal first.")
        return None

    return latest_signal
