def build_typography_css(colors):
    return f"""
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
    """




