import streamlit as st

from dashboard.api_client import get_json, post_json


def render_overview_tab():
    st.header("System Health")

    system_health = get_json("/system/health")

    if system_health is None:
        st.warning("Could not load system health.")
    else:
        checks = system_health.get("checks", {})
        missing_required = system_health.get("missing_required", [])

        col1, col2, col3, col4 = st.columns(4)

        col1.metric("System", system_health.get("status", "-"))
        col2.metric(
            "Client Config",
            "OK" if checks.get("client_config") else "Missing",
        )
        col3.metric(
            "Forecast",
            "OK" if checks.get("forecast_file") else "Missing",
        )
        col4.metric(
            "Latest Signal",
            "OK" if checks.get("latest_signal") else "Missing",
        )

        col5, col6, col7 = st.columns(3)

        col5.metric(
            "Scenarios",
            "OK" if checks.get("scenario_results") else "Missing",
        )
        col6.metric(
            "Monthly Report",
            "OK" if checks.get("monthly_report") else "Missing",
        )
        col7.metric(
            "ENTSO-E Token",
            "OK" if checks.get("entsoe_token") else "Missing",
        )

        if missing_required:
            st.warning("Missing required items: " + ", ".join(missing_required))
        elif not checks.get("entsoe_token"):
            st.info(
                "System is ready in local CSV mode. "
                "Add ENTSO-E token later for live market data."
            )
        else:
            st.success("System is fully ready.")

    st.header("Daily Workflow")

    if st.button("Run Full Daily Workflow"):
        response = post_json("/workflow/run-daily")

        if response is None:
            st.error("Could not run daily workflow.")

        elif response.get("status") == "ok":
            st.success("Daily workflow completed successfully.")

            if response.get("warning"):
                st.warning(response["warning"])
            else:
                st.info(f"Used ENTSO-E data for: {response.get('target_date')}")

            st.rerun()

        else:
            st.warning(response.get("message", "Daily workflow failed."))

    st.header("Forecast / Data Status")

    data_status = get_json("/data/status")

    if data_status and data_status.get("status") == "ok":
        forecast_status = data_status["forecast_file"]
        signal_status = data_status["latest_signal_file"]
        scenario_status = data_status["scenario_file"]

        col1, col2, col3 = st.columns(3)

        col1.metric(
            "Forecast File",
            "Available" if forecast_status["exists"] else "Missing",
        )

        col2.metric(
            "Latest Signal",
            "Available" if signal_status["exists"] else "Missing",
        )

        col3.metric(
            "Scenario Results",
            "Available" if scenario_status["exists"] else "Missing",
        )

        with st.expander("File details"):
            st.write("Forecast file:", forecast_status)
            st.write("Latest signal file:", signal_status)
            st.write("Scenario file:", scenario_status)

    else:
        st.warning("Could not load data status.")


    st.header("Client / Site")

    client_config_response = get_json("/client/config")

    if client_config_response and client_config_response.get("status") == "ok":
        client_config = client_config_response["config"]

        col1, col2, col3, col4 = st.columns(4)

        col1.metric("Client", client_config.get("client_name", "-"))
        col2.metric("Site", client_config.get("site_name", "-"))
        col3.metric("Country", client_config.get("country", "-"))
        col4.metric("Market", client_config.get("market", "-"))

        config = {
            "battery_config": client_config["battery_config"],
            "strategy_config": client_config["strategy_config"],
        }

    else:
        st.warning("No client configuration found. Using default battery configuration.")
        config = get_json("/battery/config")

    st.header("Battery Configuration")

    if config:
        battery_config = config["battery_config"]
        strategy_config = config["strategy_config"]

        col1, col2, col3, col4 = st.columns(4)

        col1.metric("Capacity", f"{battery_config['capacity_mwh']} MWh")
        col2.metric("Initial SOC", f"{battery_config['initial_soc_mwh']} MWh")
        col3.metric("Max Charge", f"{battery_config['max_charge_power_mw']} MW")
        col4.metric(
            "Max Discharge",
            f"{battery_config['max_discharge_power_mw']} MW",
        )

        col5, col6, col7, col8 = st.columns(4)

        col5.metric(
            "Charge Efficiency",
            f"{battery_config['charge_efficiency'] * 100:.1f}%",
        )
        col6.metric(
            "Discharge Efficiency",
            f"{battery_config['discharge_efficiency'] * 100:.1f}%",
        )
        col7.metric(
            "Low Price Threshold",
            f"{strategy_config['low_price_threshold']} EUR/MWh",
        )
        col8.metric(
            "High Price Threshold",
            f"{strategy_config['high_price_threshold']} EUR/MWh",
        )

    st.header("Battery Constraints")

    battery_constraints = get_json("/battery/constraints")

    if battery_constraints is None:
        st.warning("Could not load battery constraints.")

    elif battery_constraints.get("status") != "ok":
        st.warning(
            battery_constraints.get(
                "message",
                "Battery constraints unavailable.",
            )
        )

    else:
        col1, col2, col3, col4 = st.columns(4)

        col1.metric(
            "Usable Capacity",
            f"{battery_constraints['usable_capacity_mwh']} MWh",
        )

        col2.metric(
            "Initial Usable SOC",
            f"{battery_constraints['initial_usable_soc_mwh']} MWh",
        )

        col3.metric(
            "Charge Duration",
            f"{battery_constraints['charge_duration_hours']} h",
        )

        col4.metric(
            "Discharge Duration",
            f"{battery_constraints['discharge_duration_hours']} h",
        )