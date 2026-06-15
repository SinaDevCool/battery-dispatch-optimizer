import streamlit as st

from archive.streamlit_dashboard.api_client import get_json


def render_forecast_quality_section():
    st.header("Forecast Quality")

    forecast_quality = get_json("/forecast/status")

    if forecast_quality is None:
        st.warning("Could not load forecast quality status.")
        return

    if forecast_quality.get("status") != "ok":
        st.warning(
            forecast_quality.get(
                "message",
                "Forecast quality check failed.",
            )
        )
        return

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Rows", forecast_quality["row_count"])
    col2.metric("Valid Rows", forecast_quality["valid_row_count"])
    col3.metric("Negative Prices", forecast_quality["negative_price_hours"])
    col4.metric(
        "Duplicate Timestamps",
        forecast_quality["duplicate_timestamps"],
    )

    col5, col6, col7 = st.columns(3)

    col5.metric("Min Price", f"{forecast_quality['min_price']} EUR/MWh")
    col6.metric("Max Price", f"{forecast_quality['max_price']} EUR/MWh")
    col7.metric(
        "Average Price",
        f"{forecast_quality['average_price']} EUR/MWh",
    )

    with st.expander("Forecast time range"):
        st.write("First timestamp:", forecast_quality["first_timestamp"])
        st.write("Last timestamp:", forecast_quality["last_timestamp"])
        st.write("Invalid timestamps:", forecast_quality["invalid_timestamps"])
        st.write("Missing prices:", forecast_quality["missing_prices"])




