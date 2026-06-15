import streamlit as st


def render_client_identity_section(editable_client_config):
    st.subheader("Client Details")

    client_name = st.text_input(
        "Client name",
        value=editable_client_config.get("client_name", ""),
    )

    site_name = st.text_input(
        "Site name",
        value=editable_client_config.get("site_name", ""),
    )

    country = st.text_input(
        "Country",
        value=editable_client_config.get("country", ""),
    )

    market = st.text_input(
        "Market",
        value=editable_client_config.get("market", ""),
    )

    return {
        "client_name": client_name,
        "site_name": site_name,
        "country": country,
        "market": market,
    }




