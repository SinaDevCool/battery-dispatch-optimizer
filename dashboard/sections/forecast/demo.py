import streamlit as st

from dashboard.api_client import post_json


def render_forecast_demo_section():
    st.header("Demo Forecast")

    if st.button("Create 24-Hour Demo Forecast"):
        response = post_json("/forecast/demo")

        if response and response.get("status") == "ok":
            st.success(f"Demo forecast created with {response.get('rows')} rows.")
            st.info("Click Generate Daily Battery Signal to use it.")
            st.rerun()
        else:
            st.warning("Could not create demo forecast.")

    if st.button("Create High-Spread Demo Forecast"):
        response = post_json("/forecast/demo-high-spread")

        if response and response.get("status") == "ok":
            st.success(
                f"High-spread demo forecast created with {response.get('rows')} rows."
            )
            st.info("Run Forecast Profitability Comparison to compare it.")
            st.rerun()
        else:
            st.warning("Could not create high-spread demo forecast.")

    if st.button("Create In-House Placeholder Forecast"):
        response = post_json("/forecast/inhouse-placeholder")

        if response and response.get("status") == "ok":
            st.success(
                f"In-house placeholder forecast created with {response.get('rows')} rows."
            )
            st.info("Run Forecast Profitability Comparison to include it.")
            st.rerun()
        else:
            st.warning("Could not create in-house placeholder forecast.")
