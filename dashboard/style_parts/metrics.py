def build_metrics_css(colors):
    return f"""
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
    """
