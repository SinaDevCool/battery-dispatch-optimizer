import streamlit as st

from dashboard.api_client import get_json


def render_signal_explanation_section():
    st.header("Signal Explanation")

    explanation_response = get_json("/battery/signal/latest/explanation")

    if explanation_response is None:
        st.warning("Could not load signal explanation.")

    elif explanation_response.get("status") != "ok":
        st.warning(explanation_response.get("message", "No explanation available."))

    else:
        st.info(explanation_response["explanation"])
