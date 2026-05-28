import streamlit as st


def apply_dashboard_styles(theme="dark"):
    if theme == "light":
        colors = {
            "bg": "#f6f8fb",
            "panel": "#ffffff",
            "panel_soft": "#f1f5f9",
            "border": "#d6dde8",
            "border_strong": "#b8c4d4",
            "text": "#111827",
            "muted": "#64748b",
            "blue": "#2563eb",
        }
    else:
        colors = {
            "bg": "#0b0f16",
            "panel": "#111827",
            "panel_soft": "#151d2a",
            "border": "#2b3748",
            "border_strong": "#3f5066",
            "text": "#f8fafc",
            "muted": "#a8b3c2",
            "blue": "#60a5fa",
        }

    st.markdown(
        f"""
        <style>
            .stApp {{
                background: {colors["bg"]};
                color: {colors["text"]};
            }}

            html, body, [class*="css"] {{
                font-family: "Segoe UI", Inter, Arial, sans-serif;
                letter-spacing: 0 !important;
            }}

            .block-container {{
                width: min(1760px, calc(100vw - 96px)) !important;
                max-width: none !important;
                padding-top: 2rem !important;
                padding-left: 0 !important;
                padding-right: 0 !important;
                padding-bottom: 4rem !important;
            }}

            h1, h2, h3, p, label, span, div {{
                color: {colors["text"]};
            }}

            h1 {{
                font-size: 2.25rem !important;
                font-weight: 750 !important;
            }}

            h2 {{
                font-size: 1.55rem !important;
                font-weight: 720 !important;
                margin-top: 1.8rem !important;
            }}

            div[data-testid="stMetric"] {{
                background: {colors["panel"]};
                border: 1px solid {colors["border"]};
                border-radius: 8px;
                padding: 1rem 1.1rem;
                min-height: 92px;
            }}

            div[data-testid="stMetricLabel"] {{
                color: {colors["muted"]} !important;
                font-size: 0.78rem !important;
                font-weight: 700 !important;
            }}

            div[data-testid="stMetricValue"] {{
                color: {colors["text"]} !important;
                font-size: 1.45rem !important;
                font-weight: 720 !important;
            }}

            .stButton > button,
            .stDownloadButton > button,
            div[data-testid="stLinkButton"] a {{
                min-height: 42px;
                padding: 0.55rem 0.95rem;
                border-radius: 7px;
                border: 1px solid {colors["border_strong"]};
                background: {colors["panel_soft"]};
                color: {colors["text"]};
                font-size: 0.88rem;
                font-weight: 680;
            }}

            .stButton > button:hover,
            .stDownloadButton > button:hover,
            div[data-testid="stLinkButton"] a:hover {{
                border-color: {colors["blue"]};
            }}

            div[data-testid="stTabs"] button {{
                font-size: 0.88rem !important;
                font-weight: 650 !important;
                padding: 0.65rem 0.85rem !important;
            }}

            div[data-testid="stDataFrame"],
            div[data-testid="stExpander"] {{
                border: 1px solid {colors["border"]};
                border-radius: 8px;
                overflow: hidden;
                background: {colors["panel"]};
            }}

            div[data-testid="stVegaLiteChart"],
            div[data-testid="stPlotlyChart"] {{
                border: 1px solid {colors["border"]};
                border-radius: 8px;
                padding: 0.5rem;
                background: {colors["panel"]};
            }}

            div[data-baseweb="input"],
            div[data-baseweb="select"] > div,
            textarea {{
                border-radius: 7px !important;
                background: {colors["panel_soft"]} !important;
            }}

            .report-frame {{
                background: #ffffff;
                color: #111827;
                border: 1px solid #d1d5db;
                border-radius: 8px;
                overflow: hidden;
            }}

            @media (max-width: 900px) {{
                .block-container {{
                    width: calc(100vw - 32px) !important;
                }}
            }}
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