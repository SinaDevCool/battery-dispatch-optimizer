import streamlit as st

from archive.streamlit_dashboard.api_client import post_json


def _build_validation_errors(battery_config, strategy_config):
    validation_errors = []

    if battery_config["initial_soc_mwh"] > battery_config["capacity_mwh"]:
        validation_errors.append("Initial SOC cannot be greater than capacity.")

    if battery_config["min_soc_mwh"] >= battery_config["capacity_mwh"]:
        validation_errors.append("Minimum SOC must be lower than capacity.")

    if battery_config["initial_soc_mwh"] < battery_config["min_soc_mwh"]:
        validation_errors.append("Initial SOC cannot be lower than minimum SOC.")

    if strategy_config["high_price_threshold"] <= strategy_config["low_price_threshold"]:
        validation_errors.append(
            "High price threshold must be greater than low price threshold."
        )

    return validation_errors


def render_save_client_config_section(
    client_identity,
    battery_config,
    strategy_config,
    commercial_config,
):
    if not st.button("Save Client Config"):
        return

    validation_errors = _build_validation_errors(
        battery_config=battery_config,
        strategy_config=strategy_config,
    )

    if validation_errors:
        for error in validation_errors:
            st.error(error)

        return

    updated_config = {
        **client_identity,
        "battery_config": battery_config,
        "strategy_config": strategy_config,
        "commercial_config": commercial_config,
    }

    response = post_json("/client/config", updated_config)

    if response and response.get("status") == "ok":
        st.success("Client config saved.")
        st.info("Generate a new daily battery signal to use the updated config.")
        st.rerun()

    elif response and response.get("status") == "invalid":
        for error in response.get("errors", []):
            st.error(error)

    else:
        st.error("Could not save client config.")




