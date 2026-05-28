import streamlit as st

from dashboard.api_client import get_json, post_json


def render_settings_tab():
    st.header("Client Settings")

    client_config_response = get_json("/client/config")

    if not client_config_response or client_config_response.get("status") != "ok":
        st.warning("No client configuration found.")
        return

    editable_client_config = client_config_response["config"]

    st.subheader("Client Presets")

    preset_response = get_json("/client/presets")

    if preset_response and preset_response.get("status") == "ok":
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
    else:
        st.info("No client presets available.")

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

    battery_cfg = editable_client_config["battery_config"]
    strategy_cfg = editable_client_config["strategy_config"]
    commercial_cfg = editable_client_config.get("commercial_config", {})

    st.subheader("Battery")

    col1, col2, col3 = st.columns(3)

    with col1:
        capacity_mwh = st.number_input(
            "Capacity MWh",
            min_value=0.1,
            value=float(battery_cfg["capacity_mwh"]),
        )

        initial_soc_mwh = st.number_input(
            "Initial SOC MWh",
            min_value=0.0,
            value=float(battery_cfg["initial_soc_mwh"]),
        )

        min_soc_mwh = st.number_input(
            "Minimum SOC MWh",
            min_value=0.0,
            value=float(battery_cfg["min_soc_mwh"]),
        )

    with col2:
        max_charge_power_mw = st.number_input(
            "Max charge power MW",
            min_value=0.1,
            value=float(battery_cfg["max_charge_power_mw"]),
        )

        max_discharge_power_mw = st.number_input(
            "Max discharge power MW",
            min_value=0.1,
            value=float(battery_cfg["max_discharge_power_mw"]),
        )

    with col3:
        charge_efficiency = st.number_input(
            "Charge efficiency",
            min_value=0.01,
            max_value=1.0,
            value=float(battery_cfg["charge_efficiency"]),
        )

        discharge_efficiency = st.number_input(
            "Discharge efficiency",
            min_value=0.01,
            max_value=1.0,
            value=float(battery_cfg["discharge_efficiency"]),
        )

    st.subheader("Strategy")

    col1, col2, col3 = st.columns(3)

    with col1:
        low_price_threshold = st.number_input(
            "Low price threshold EUR/MWh",
            value=float(strategy_cfg["low_price_threshold"]),
        )

    with col2:
        high_price_threshold = st.number_input(
            "High price threshold EUR/MWh",
            value=float(strategy_cfg["high_price_threshold"]),
        )

    with col3:
        timestep_hours = st.number_input(
            "Timestep hours",
            min_value=0.25,
            value=float(strategy_cfg["timestep_hours"]),
        )

    st.subheader("Commercial Costs")

    col1, col2, col3 = st.columns(3)

    with col1:
        trading_fee_eur_per_mwh = st.number_input(
            "Trading fee EUR/MWh",
            min_value=0.0,
            value=float(commercial_cfg.get("trading_fee_eur_per_mwh", 0.20)),
        )

        market_access_fee_eur_per_mwh = st.number_input(
            "Market access fee EUR/MWh",
            min_value=0.0,
            value=float(commercial_cfg.get("market_access_fee_eur_per_mwh", 0.30)),
        )

    with col2:
        grid_fee_import_eur_per_mwh = st.number_input(
            "Grid import fee EUR/MWh",
            min_value=0.0,
            value=float(commercial_cfg.get("grid_fee_import_eur_per_mwh", 0.0)),
        )

        grid_fee_export_eur_per_mwh = st.number_input(
            "Grid export fee EUR/MWh",
            min_value=0.0,
            value=float(commercial_cfg.get("grid_fee_export_eur_per_mwh", 0.0)),
        )

    with col3:
        tax_or_levy_eur_per_mwh = st.number_input(
            "Tax or levy EUR/MWh",
            min_value=0.0,
            value=float(commercial_cfg.get("tax_or_levy_eur_per_mwh", 0.0)),
        )

        degradation_cost_eur_per_mwh_throughput = st.number_input(
            "Degradation cost EUR/MWh throughput",
            min_value=0.0,
            value=float(
                commercial_cfg.get(
                    "degradation_cost_eur_per_mwh_throughput",
                    3.0,
                )
            ),
        )

    if st.button("Save Client Config"):
        validation_errors = []

        if initial_soc_mwh > capacity_mwh:
            validation_errors.append("Initial SOC cannot be greater than capacity.")

        if min_soc_mwh >= capacity_mwh:
            validation_errors.append("Minimum SOC must be lower than capacity.")

        if initial_soc_mwh < min_soc_mwh:
            validation_errors.append("Initial SOC cannot be lower than minimum SOC.")

        if high_price_threshold <= low_price_threshold:
            validation_errors.append(
                "High price threshold must be greater than low price threshold."
            )

        if validation_errors:
            for error in validation_errors:
                st.error(error)

            return

        updated_config = {
            "client_name": client_name,
            "site_name": site_name,
            "country": country,
            "market": market,
            "battery_config": {
                "capacity_mwh": capacity_mwh,
                "initial_soc_mwh": initial_soc_mwh,
                "min_soc_mwh": min_soc_mwh,
                "max_charge_power_mw": max_charge_power_mw,
                "max_discharge_power_mw": max_discharge_power_mw,
                "charge_efficiency": charge_efficiency,
                "discharge_efficiency": discharge_efficiency,
            },
            "strategy_config": {
                "low_price_threshold": low_price_threshold,
                "high_price_threshold": high_price_threshold,
                "timestep_hours": timestep_hours,
            },
            "commercial_config": {
                "trading_fee_eur_per_mwh": trading_fee_eur_per_mwh,
                "market_access_fee_eur_per_mwh": market_access_fee_eur_per_mwh,
                "grid_fee_import_eur_per_mwh": grid_fee_import_eur_per_mwh,
                "grid_fee_export_eur_per_mwh": grid_fee_export_eur_per_mwh,
                "tax_or_levy_eur_per_mwh": tax_or_levy_eur_per_mwh,
                "degradation_cost_eur_per_mwh_throughput": degradation_cost_eur_per_mwh_throughput,
            },
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