def build_data_display_css(colors):
    return f"""
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
    """




