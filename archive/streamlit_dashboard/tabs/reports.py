import requests
import streamlit as st

from archive.streamlit_dashboard.api_client import API_BASE_URL, get_json


def render_reports_tab():
    st.header("Monthly Report")

    report_response = get_json("/reports/monthly/latest")

    if report_response is None:
        st.warning("Could not load monthly report status.")
        return

    if report_response.get("status") != "ok":
        st.info(report_response.get("message", "No monthly report available."))
        return

    report_name = report_response["report_name"]
    report_url = f"{API_BASE_URL}/reports/monthly/latest/view"

    st.success(f"Latest report available: {report_name}")

    col1, col2 = st.columns(2)

    with col1:
        st.link_button(
            "Open Latest Monthly Report",
            report_url,
            use_container_width=True,
        )

    try:
        report_html_response = requests.get(report_url, timeout=10)
        report_html_response.raise_for_status()
        report_html = report_html_response.text

    except requests.RequestException as error:
        st.warning(f"Could not download monthly report: {error}")
        return

    with col2:
        st.download_button(
            label="Download Monthly Report HTML",
            data=report_html,
            file_name=report_name,
            mime="text/html",
            use_container_width=True,
        )

    st.subheader("Report Preview")

    st.components.v1.html(
        report_html,
        height=850,
        scrolling=True,
    )



