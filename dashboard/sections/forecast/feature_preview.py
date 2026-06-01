import pandas as pd
import streamlit as st

from dashboard.api_client import get_json


def render_forecast_feature_preview_section():
    st.header("Forecast Feature Preview")

    forecast_preview = get_json("/forecast/preview")

    if forecast_preview is None:
        st.warning("Could not load forecast preview.")
        return

    if forecast_preview.get("status") != "ok":
        st.info(forecast_preview.get("message", "No forecast preview available."))
        return

    preview_df = pd.DataFrame(forecast_preview.get("preview", []))

    st.write(
        f"Rows: {forecast_preview.get('rows')} | "
        f"Columns: {', '.join(forecast_preview.get('columns', []))}"
    )

    if preview_df.empty:
        st.info("Forecast preview is empty.")
        return

    preview_df["timestamp"] = pd.to_datetime(
        preview_df["timestamp"],
        errors="coerce",
    )

    st.dataframe(preview_df, use_container_width=True)

    chart_columns = [
        column for column in [
            "forecast_price",
            "load_forecast",
            "generation_forecast",
            "forecast_solar",
            "forecast_wind",
            "forecast_renewables_total",
        ]
        if column in preview_df.columns
    ]

    if not chart_columns:
        return

    selected_chart_column = st.selectbox(
        "Forecast feature chart",
        options=chart_columns,
    )

    st.line_chart(
        preview_df,
        x="timestamp",
        y=selected_chart_column,
        use_container_width=True,
    )
