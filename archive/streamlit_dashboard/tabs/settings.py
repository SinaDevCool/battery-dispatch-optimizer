import streamlit as st

from archive.streamlit_dashboard.api_client import get_json
from archive.streamlit_dashboard.sections.settings.battery_config import render_battery_config_section
from archive.streamlit_dashboard.sections.settings.client_identity import (
    render_client_identity_section,
)
from archive.streamlit_dashboard.sections.settings.commercial_config import (
    render_commercial_config_section,
)
from archive.streamlit_dashboard.sections.settings.presets import render_client_presets_section
from archive.streamlit_dashboard.sections.settings.save_config import render_save_client_config_section
from archive.streamlit_dashboard.sections.settings.strategy_config import render_strategy_config_section


def render_settings_tab():
    st.header("Client Settings")

    client_config_response = get_json("/client/config")

    if not client_config_response or client_config_response.get("status") != "ok":
        st.warning("No client configuration found.")
        return

    editable_client_config = client_config_response["config"]

    render_client_presets_section()

    client_identity = render_client_identity_section(editable_client_config)

    battery_config = render_battery_config_section(
        editable_client_config["battery_config"]
    )

    strategy_config = render_strategy_config_section(
        editable_client_config["strategy_config"]
    )

    commercial_config = render_commercial_config_section(
        editable_client_config.get("commercial_config", {})
    )

    render_save_client_config_section(
        client_identity=client_identity,
        battery_config=battery_config,
        strategy_config=strategy_config,
        commercial_config=commercial_config,
    )




