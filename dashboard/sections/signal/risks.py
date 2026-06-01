import streamlit as st

from dashboard.api_client import get_json


def render_signal_risks_section():
    st.header("Risk Flags")

    risk_response = get_json("/battery/signal/latest/risks")

    if risk_response is None:
        st.warning("Could not load risk flags.")

    elif risk_response.get("status") != "ok":
        st.warning(risk_response.get("message", "No risk flags available."))

    else:
        risks = risk_response.get("risks", [])

        if not risks:
            st.info("No risk flags returned.")
        else:
            for risk in risks:
                level = risk.get("level", "info")
                message = risk.get("message", "")

                if level == "high":
                    st.error(message)
                elif level == "medium":
                    st.warning(message)
                else:
                    st.info(message)
