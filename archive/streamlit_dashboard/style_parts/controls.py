def build_controls_css(colors):
    return f"""
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

        div[data-baseweb="input"],
        div[data-baseweb="select"] > div,
        textarea {{
            border-radius: 7px !important;
            background: {colors["panel_soft"]} !important;
        }}
    """




