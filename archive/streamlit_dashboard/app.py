import streamlit as st

from archive.streamlit_dashboard.api_client import get_json
from archive.streamlit_dashboard.tabs.overview import render_overview_tab
from archive.streamlit_dashboard.tabs.forecast import render_forecast_tab
from archive.streamlit_dashboard.tabs.signal import render_signal_tab
from archive.streamlit_dashboard.tabs.dispatch import render_dispatch_tab
from archive.streamlit_dashboard.tabs.scenarios import render_scenarios_tab
from archive.streamlit_dashboard.tabs.reports import render_reports_tab
from archive.streamlit_dashboard.tabs.settings import render_settings_tab
from archive.streamlit_dashboard.styles import apply_dashboard_styles
from archive.streamlit_dashboard.components.status_strip import render_status_strip


st.set_page_config(
    page_title="Battery Dispatch Optimizer",
    layout="wide",
)

if "theme_mode" not in st.session_state:
    st.session_state["theme_mode"] = "dark"

with st.sidebar:
    theme_mode = st.radio(
        "Theme",
        options=["dark", "light"],
        index=0 if st.session_state["theme_mode"] == "dark" else 1,
        horizontal=True,
    )

st.session_state["theme_mode"] = theme_mode

apply_dashboard_styles(theme=theme_mode)

st.title("Battery Dispatch Optimizer")
st.caption("Daily battery dispatch signal dashboard")

status = get_json("/health")

if status is None:
    st.stop()

st.success("API is running")

render_status_strip()

tabs = st.tabs(
    [
        "Overview",
        "Forecast",
        "Signal",
        "Dispatch",
        "Scenarios & Stress",
        "Reports",
        "Settings",
    ]
)

with tabs[0]:
    render_overview_tab()

with tabs[1]:
    render_forecast_tab()

with tabs[2]:
    render_signal_tab()

with tabs[3]:
    render_dispatch_tab()

with tabs[4]:
    render_scenarios_tab()

with tabs[5]:
    render_reports_tab()

with tabs[6]:
    render_settings_tab()



