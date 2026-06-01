import streamlit as st

from dashboard.style_parts.base import build_base_css
from dashboard.style_parts.controls import build_controls_css
from dashboard.style_parts.data_display import build_data_display_css
from dashboard.style_parts.metrics import build_metrics_css
from dashboard.style_parts.reports import build_report_css
from dashboard.style_parts.theme import get_theme_colors
from dashboard.style_parts.typography import build_typography_css


def build_dashboard_css(theme="dark"):
    colors = get_theme_colors(theme)

    return "\n".join(
        [
            build_base_css(colors),
            build_typography_css(colors),
            build_metrics_css(colors),
            build_controls_css(colors),
            build_data_display_css(colors),
            build_report_css(),
        ]
    )


def apply_dashboard_styles(theme="dark"):
    st.markdown(
        f"""
        <style>
            {build_dashboard_css(theme)}
        </style>
        """,
        unsafe_allow_html=True,
    )


def wrap_report_html(report_html):
    return f"""
    <div class="report-frame">
        {report_html}
    </div>
    """
