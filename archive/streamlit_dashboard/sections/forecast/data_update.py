import streamlit as st

from archive.streamlit_dashboard.api_client import post_json


def render_forecast_data_update_section():
    st.header("Data Update")

    st.caption(
        "Live ENTSO-E data is optional. If it is unavailable, the app keeps using the saved local forecast."
    )

    if st.button("Try Live ENTSO-E Update"):
        response = post_json("/data/update-entsoe")

        if response is None:
            st.error("Could not update ENTSO-E forecast.")

        elif response.get("status") == "ok":
            st.success(
                f"ENTSO-E forecast updated for {response.get('target_date')} "
                f"with {response.get('rows')} rows."
            )
            st.info("Now click Generate Daily Battery Signal.")

        elif response.get("status") == "fallback":
            st.warning(response.get("message", "Live ENTSO-E update failed."))
            st.info("The existing saved forecast is still available for local CSV mode.")

        else:
            st.warning(response.get("message", "ENTSO-E update failed."))




