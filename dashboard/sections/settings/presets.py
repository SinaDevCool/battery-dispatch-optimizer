import streamlit as st

from dashboard.api_client import get_json, post_json


def render_client_presets_section():
    st.subheader("Client Presets")

    preset_response = get_json("/client/presets")

    if not preset_response or preset_response.get("status") != "ok":
        st.info("No client presets available.")
        return

    preset_names = preset_response.get("presets", [])

    selected_preset = st.selectbox(
        "Client preset",
        options=[""] + preset_names,
        format_func=lambda value: "Select preset" if value == "" else value,
    )

    if st.button("Apply Preset"):
        if selected_preset:
            response = post_json(f"/client/presets/{selected_preset}/apply")

            if response and response.get("status") == "ok":
                st.success(f"Applied preset: {selected_preset}")
                st.rerun()
            else:
                st.warning(
                    response.get("message", "Could not apply preset.")
                    if response
                    else "Could not apply preset."
                )
        else:
            st.warning("Select a preset first.")
