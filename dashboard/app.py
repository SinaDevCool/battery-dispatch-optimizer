import pandas as pd
import requests
import streamlit as st


API_BASE_URL = "http://127.0.0.1:8000"


st.set_page_config(
    page_title="Battery Dispatch Optimizer",
    layout="wide",
)


st.title("Battery Dispatch Optimizer")
st.caption("Daily battery dispatch signal dashboard")


def get_json(endpoint):
    url = f"{API_BASE_URL}{endpoint}"

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.json()

    except requests.RequestException as error:
        st.error(f"Could not connect to API: {error}")
        return None


def post_json(endpoint, payload=None):
    url = f"{API_BASE_URL}{endpoint}"

    if payload is None:
        payload = {}

    try:
        response = requests.post(url, json=payload, timeout=30)
        response.raise_for_status()
        return response.json()

    except requests.RequestException as error:
        st.error(f"Could not send data to API: {error}")
        return None


status = get_json("/health")

if status is None:
    st.stop()

st.success("API is running")

data_status = get_json("/data/status")

st.header("Data Status")

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

st.header("Forecast Upload")

uploaded_file = st.file_uploader(
    "Upload next-day price forecast CSV",
    type=["csv"],
)

if uploaded_file is not None:
    try:
        import pandas as pd

        forecast_df = pd.read_csv(uploaded_file)

        st.write("Preview")
        st.dataframe(forecast_df.head(), use_container_width=True)

        required_columns = ["timestamp", "forecast_price"]

        missing_columns = [
            col for col in required_columns
            if col not in forecast_df.columns
        ]

        forecast_df["timestamp"] = pd.to_datetime(
        forecast_df["timestamp"],
            errors="coerce",
        )

        forecast_df["forecast_price"] = pd.to_numeric(
        forecast_df["forecast_price"],
        errors="coerce",
        )

        invalid_timestamps = forecast_df["timestamp"].isna().sum()
        missing_prices = forecast_df["forecast_price"].isna().sum()
        duplicate_timestamps = forecast_df["timestamp"].duplicated().sum()
        row_count = len(forecast_df)

        if missing_columns:
            st.error(
                "Missing required columns: "
                + ", ".join(missing_columns)
            )

        elif invalid_timestamps > 0:
            st.error(f"Forecast has {invalid_timestamps} invalid timestamps.")

        elif missing_prices > 0:
            st.error(f"Forecast has {missing_prices} missing or invalid prices.")

        elif duplicate_timestamps > 0:
            st.error(f"Forecast has {duplicate_timestamps} duplicate timestamps.")

        elif row_count < 2:
            st.error("Forecast must contain at least 2 rows.")

        elif row_count != 24:
            st.warning(
                f"Forecast has {row_count} rows. Expected 24 hourly rows for a full next-day signal."
        )

        elif st.button("Save Forecast CSV"):
            price_data = []

            for _, row in forecast_df.iterrows():
                price_data.append(
                    {
                        "timestamp": str(row["timestamp"]),
                        "price": float(row["forecast_price"]),
                    }
                )

            response = post_json(
                "/forecast/upload",
                {
                    "price_data": price_data,
                },
            )

            if response and response.get("status") == "ok":
                st.info("Battery signal was generated automatically. The dashboard will refresh.")
                st.rerun()  
            else:
                st.warning("Forecast upload failed.")

    except Exception as error:
        st.error(f"Could not read forecast CSV: {error}")

st.header("Data Update")

if st.button("Update ENTSO-E Forecast"):
    response = post_json("/data/update-entsoe")

    if response is None:
        st.error("Could not update ENTSO-E forecast.")

    elif response.get("status") == "ok":
        st.success(
            f"ENTSO-E forecast updated for {response.get('target_date')} "
            f"with {response.get('rows')} rows."
        )
        st.info("Now click Generate Daily Battery Signal.")

    else:
        st.warning(response.get("message", "ENTSO-E update failed."))

st.header("Daily Signal Control")

if st.button("Generate Daily Battery Signal"):
    response = post_json("/battery/signal/run-latest")

    if response is None:
        st.error("Could not generate battery signal.")

    elif response.get("status") == "ok":
        st.success("Daily battery signal generated successfully.")
        st.rerun()

    else:
        st.warning(response.get("message", "Signal could not be generated."))


client_config_response = get_json("/client/config")


if client_config_response and client_config_response.get("status") == "ok":
    editable_client_config = client_config_response["config"]

    with st.sidebar:
        st.header("Edit Client Config")

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

        low_price_threshold = st.number_input(
            "Low price threshold EUR/MWh",
            value=float(strategy_cfg["low_price_threshold"]),
        )

        high_price_threshold = st.number_input(
            "High price threshold EUR/MWh",
            value=float(strategy_cfg["high_price_threshold"]),
        )

        timestep_hours = st.number_input(
            "Timestep hours",
            min_value=0.25,
            value=float(strategy_cfg["timestep_hours"]),
        )

        save_clicked = st.button("Save Client Config")

        if save_clicked:
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
                "commercial_config": commercial_cfg,
            }

            response = post_json("/client/config", updated_config)

            if response and response.get("status") == "ok":
                st.success("Client config saved.")
                st.info("Click Generate Daily Battery Signal to use the updated config.")


st.header("Client / Site")

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


latest_signal = get_json("/battery/signal/latest")


st.header("Battery Configuration")

if config:
    battery_config = config["battery_config"]
    strategy_config = config["strategy_config"]

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Capacity", f"{battery_config['capacity_mwh']} MWh")
    col2.metric("Initial SOC", f"{battery_config['initial_soc_mwh']} MWh")
    col3.metric("Max Charge", f"{battery_config['max_charge_power_mw']} MW")
    col4.metric("Max Discharge", f"{battery_config['max_discharge_power_mw']} MW")

    col5, col6, col7, col8 = st.columns(4)

    col5.metric("Charge Efficiency", f"{battery_config['charge_efficiency'] * 100:.1f}%")
    col6.metric("Discharge Efficiency", f"{battery_config['discharge_efficiency'] * 100:.1f}%")
    col7.metric("Low Price Threshold", f"{strategy_config['low_price_threshold']} EUR/MWh")
    col8.metric("High Price Threshold", f"{strategy_config['high_price_threshold']} EUR/MWh")


st.header("Latest Battery Signal")

if latest_signal is None:
    st.stop()

if latest_signal.get("status") != "ok":
    st.warning(latest_signal.get("message", "No latest signal available."))
    st.info("Click Generate Daily Battery Signal first.")
    st.stop()


signal_data = latest_signal["data"]
summary = signal_data["summary"]
dispatch = signal_data["dispatch"]


col1, col2, col3, col4 = st.columns(4)

col1.metric("Signal", summary["signal"])
col2.metric("Opportunity", summary["opportunity_level"])
col3.metric("Total PnL", f"{summary['total_pnl_eur']} EUR")
col4.metric("Profit per MW-day", f"{summary['profit_per_mw_day']} EUR/MW-day")


col5, col6, col7, col8 = st.columns(4)

col5.metric("Charge Hours", summary["charge_hours"])
col6.metric("Discharge Hours", summary["discharge_hours"])
col7.metric("First Charge", summary["first_charge_timestamp"] or "-")
col8.metric("First Discharge", summary["first_discharge_timestamp"] or "-")


st.header("Dispatch Schedule")

if dispatch:
    dispatch_df = pd.DataFrame(dispatch)
    dispatch_df["timestamp"] = pd.to_datetime(dispatch_df["timestamp"], errors="coerce")

    st.subheader("Forecast Price")
    st.line_chart(
        dispatch_df,
        x="timestamp",
        y="price",
        use_container_width=True,
    )

    st.subheader("Battery SOC")
    st.line_chart(
        dispatch_df,
        x="timestamp",
        y="soc_mwh",
        use_container_width=True,
    )

    st.subheader("Cumulative PnL")
    st.line_chart(
        dispatch_df,
        x="timestamp",
        y="total_pnl_eur",
        use_container_width=True,
    )

    dispatch_csv = dispatch_df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="Download Dispatch CSV",
        data=dispatch_csv,
        file_name="battery_dispatch_schedule.csv",
        mime="text/csv",
    )

    st.subheader("Dispatch Table")
    st.dataframe(dispatch_df, use_container_width=True)

else:
    st.info("No dispatch rows available.")


st.header("Scenario Analysis")

if st.button("Run Scenario Analysis"):
    response = post_json("/scenarios/run-latest")

    if response is None:
        st.error("Could not run scenario analysis.")

    elif response.get("status") == "ok":
        st.success("Scenario analysis completed successfully.")
        st.rerun()

    else:
        st.warning(response.get("message", "Scenario analysis could not be generated."))


scenario_data = get_json("/scenarios/latest")

if scenario_data is None:
    st.stop()

if scenario_data.get("status") != "ok":
    st.warning(scenario_data.get("message", "No scenario results available."))
    st.info("Click Run Scenario Analysis first.")
else:
    scenarios = scenario_data["results"]

    if scenarios:
        scenario_df = pd.DataFrame(scenarios)

        st.dataframe(scenario_df, use_container_width=True)

        scenario_csv = scenario_df.to_csv(index=False).encode("utf-8")

        st.download_button(
            label="Download Scenario CSV",
            data=scenario_csv,
            file_name="battery_scenario_results.csv",
            mime="text/csv",
        )

        best_scenario = max(
            scenarios,
            key=lambda row: row["total_pnl_eur"],
        )

        st.subheader("Best Scenario")

        col1, col2, col3, col4 = st.columns(4)

        col1.metric("Scenario", best_scenario["scenario_name"])
        col2.metric("Total PnL", f"{best_scenario['total_pnl_eur']} EUR")
        col3.metric("Profit per MW-day", f"{best_scenario['profit_per_mw_day']} EUR/MW-day")
        col4.metric("Opportunity", best_scenario["opportunity_level"])
    else:
        st.info("Scenario result list is empty.")