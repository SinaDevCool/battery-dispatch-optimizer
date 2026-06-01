def build_base_css(colors):
    return f"""
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

        @media (max-width: 900px) {{
            .block-container {{
                width: calc(100vw - 32px) !important;
            }}
        }}
    """
