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

system_health = get_json("/system/health")

st.header("System Health")

if system_health is None:
    st.warning("Could not load system health.")

else:
    checks = system_health.get("checks", {})
    missing_required = system_health.get("missing_required", [])

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("System", system_health.get("status", "-"))
    col2.metric("Client Config", "OK" if checks.get("client_config") else "Missing")
    col3.metric("Forecast", "OK" if checks.get("forecast_file") else "Missing")
    col4.metric("Latest Signal", "OK" if checks.get("latest_signal") else "Missing")

    col5, col6, col7 = st.columns(3)

    col5.metric("Scenarios", "OK" if checks.get("scenario_results") else "Missing")
    col6.metric("Monthly Report", "OK" if checks.get("monthly_report") else "Missing")
    col7.metric("ENTSO-E Token", "OK" if checks.get("entsoe_token") else "Missing")

    if missing_required:
        st.warning("Missing required items: " + ", ".join(missing_required))
    elif not checks.get("entsoe_token"):
        st.info("System is ready in local CSV mode. Add ENTSO-E token later for live market data.")
    else:
        st.success("System is fully ready.")

st.header("Daily Workflow")

if st.button("Run Full Daily Workflow"):
    response = post_json("/workflow/run-daily")

    if response is None:
        st.error("Could not run daily workflow.")

    elif response.get("status") == "ok":
        st.success("Daily workflow completed successfully.")
        st.info(f"Used ENTSO-E data for: {response.get('target_date')}")
        st.rerun()

    else:
        st.warning(response.get("message", "Daily workflow failed."))

data_status = get_json("/data/status")

st.header("Forecast / Data Status")

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


forecast_quality = get_json("/forecast/status")

st.header("Forecast Quality")

if forecast_quality is None:
    st.warning("Could not load forecast quality status.")

elif forecast_quality.get("status") != "ok":
    st.warning(forecast_quality.get("message", "Forecast quality check failed."))

else:
    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Rows", forecast_quality["row_count"])
    col2.metric("Valid Rows", forecast_quality["valid_row_count"])
    col3.metric("Negative Prices", forecast_quality["negative_price_hours"])
    col4.metric("Duplicate Timestamps", forecast_quality["duplicate_timestamps"])

    col5, col6, col7 = st.columns(3)

    col5.metric("Min Price", f"{forecast_quality['min_price']} EUR/MWh")
    col6.metric("Max Price", f"{forecast_quality['max_price']} EUR/MWh")
    col7.metric("Average Price", f"{forecast_quality['average_price']} EUR/MWh")

    with st.expander("Forecast time range"):
        st.write("First timestamp:", forecast_quality["first_timestamp"])
        st.write("Last timestamp:", forecast_quality["last_timestamp"])
        st.write("Invalid timestamps:", forecast_quality["invalid_timestamps"])
        st.write("Missing prices:", forecast_quality["missing_prices"])


st.header("Saved Forecast Preview")

try:
    saved_forecast_df = pd.read_csv("data/processed/next_day_price_forecast.csv")
    saved_forecast_df["timestamp"] = pd.to_datetime(
        saved_forecast_df["timestamp"],
        errors="coerce",
    )

    st.dataframe(saved_forecast_df, use_container_width=True)

    st.line_chart(
        saved_forecast_df,
        x="timestamp",
        y="forecast_price",
        use_container_width=True,
    )

    forecast_csv = saved_forecast_df.to_csv(index=False).encode("utf-8")

    st.download_button(
        label="Download Saved Forecast CSV",
        data=forecast_csv,
        file_name="next_day_price_forecast.csv",
        mime="text/csv",
    )

    st.subheader("Edit Saved Forecast")

    editable_forecast_df = st.data_editor(
        saved_forecast_df,
        use_container_width=True,
        num_rows="dynamic",
    )

    if st.button("Save Edited Forecast"):
        edited_df = editable_forecast_df.copy()

        edited_df["timestamp"] = pd.to_datetime(
            edited_df["timestamp"],
            errors="coerce",
        )

        edited_df["forecast_price"] = pd.to_numeric(
            edited_df["forecast_price"],
            errors="coerce",
        )

        edited_df = edited_df.dropna(subset=["timestamp", "forecast_price"])
        edited_df = edited_df.drop_duplicates(subset=["timestamp"])
        edited_df = edited_df.sort_values("timestamp")

        price_data = []

        for _, row in edited_df.iterrows():
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
            st.success("Edited forecast saved and signal regenerated.")
            st.rerun()
        else:
            st.warning("Could not save edited forecast.")

except FileNotFoundError:
    st.info("No saved forecast file found yet.")

except Exception as error:
    st.warning(f"Could not preview saved forecast: {error}")

st.header("Demo Forecast")

if st.button("Create 24-Hour Demo Forecast"):
    response = post_json("/forecast/demo")

    if response and response.get("status") == "ok":
        st.success(f"Demo forecast created with {response.get('rows')} rows.")
        st.info("Click Generate Daily Battery Signal to use it.")
        st.rerun()
    else:
        st.warning("Could not create demo forecast.")

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

        else:
            if row_count != 24:
                st.warning(
                    f"Forecast has {row_count} rows. Expected 24 hourly rows for a full next-day signal."
                )

            if st.button("Save Forecast CSV"):
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

        st.subheader("Commercial Costs")

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

        save_clicked = st.button("Save Client Config")

        if save_clicked:
            validation_errors = []

            if initial_soc_mwh > capacity_mwh:
                validation_errors.append("Initial SOC cannot be greater than capacity.")

            if min_soc_mwh >= capacity_mwh:
                validation_errors.append("Minimum SOC must be lower than capacity.")

            if initial_soc_mwh < min_soc_mwh:
                validation_errors.append("Initial SOC cannot be lower than minimum SOC.")

            if high_price_threshold <= low_price_threshold:
                validation_errors.append("High price threshold must be greater than low price threshold.")

            if validation_errors:
                for error in validation_errors:
                    st.error(error)

                st.stop()

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
                st.info("Click Generate Daily Battery Signal to use the updated config.")
            elif response and response.get("status") == "invalid":
                for error in response.get("errors", []):
                    st.error(error)
            else:
                st.error("Could not save client config.")


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


battery_constraints = get_json("/battery/constraints")

st.header("Battery Constraints")

if battery_constraints is None:
    st.warning("Could not load battery constraints.")

elif battery_constraints.get("status") != "ok":
    st.warning(battery_constraints.get("message", "Battery constraints unavailable."))

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

recommendation = "No dispatch action recommended."

if summary["signal"] == "ACTION":
    recommendation = (
        f"Dispatch recommended. Charge for {summary['charge_hours']} hour(s), "
        f"discharge for {summary['discharge_hours']} hour(s), "
        f"expected PnL {summary['total_pnl_eur']} EUR."
    )

if summary["opportunity_level"] == "high":
    st.success(recommendation)
elif summary["opportunity_level"] == "medium":
    st.info(recommendation)
elif summary["opportunity_level"] == "low":
    st.warning(recommendation)
else:
    st.warning(recommendation)

action_rows = [
    row for row in dispatch
    if row["action"] in ["charge", "discharge"]
]

st.subheader("Why This Action?")

if action_rows:
    action_df = pd.DataFrame(action_rows)

    st.dataframe(
        action_df[
            [
                "timestamp",
                "price",
                "action",
                "grid_energy_mwh",
                "battery_energy_mwh",
                "market_value_eur",
                "cost_eur",
                "pnl_eur",
            ]
        ],
        use_container_width=True,
    )
else:
    st.info("No charge or discharge actions selected.")

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

col9, col10, col11, col12 = st.columns(4)

col9.metric("Charged Energy", f"{summary.get('charged_mwh', 0)} MWh")
col10.metric("Discharged Energy", f"{summary.get('discharged_mwh', 0)} MWh")
col11.metric("Throughput", f"{summary.get('throughput_mwh', 0)} MWh")
col12.metric("Equivalent Cycles", summary.get("equivalent_full_cycles", 0))

if dispatch:
    dispatch_cost_df = pd.DataFrame(dispatch)

    total_market_value = dispatch_cost_df["market_value_eur"].sum()
    total_cost = dispatch_cost_df["cost_eur"].sum()
    total_dispatch_pnl = dispatch_cost_df["pnl_eur"].sum()

    col1, col2, col3 = st.columns(3)

    col1.metric("Market Value", f"{total_market_value:.2f} EUR")
    col2.metric("Commercial Costs", f"{total_cost:.2f} EUR")
    col3.metric("Dispatch PnL", f"{total_dispatch_pnl:.2f} EUR")

st.header("Signal Explanation")

explanation_response = get_json("/battery/signal/latest/explanation")

if explanation_response is None:
    st.warning("Could not load signal explanation.")

elif explanation_response.get("status") != "ok":
    st.warning(explanation_response.get("message", "No explanation available."))

else:
    st.info(explanation_response["explanation"])

st.header("Risk Flags")

risk_response = get_json("/battery/signal/latest/risks")

if risk_response is None:
    st.warning("Could not load risk flags.")

elif risk_response.get("status") != "ok":
    st.warning(risk_response.get("message", "No risk flags available."))

else:
    risks = risk_response.get("risks", [])

    if not risks:
        st.info("No risk flags returned.")
    else:
        for risk in risks:
            level = risk.get("level", "info")
            message = risk.get("message", "")

            if level == "high":
                st.error(message)
            elif level == "medium":
                st.warning(message)
            else:
                st.info(message)

st.header("Dispatch Schedule")

if dispatch:
    dispatch_df = pd.DataFrame(dispatch)
    dispatch_df["timestamp"] = pd.to_datetime(dispatch_df["timestamp"], errors="coerce")

    selected_actions = st.multiselect(
        "Filter dispatch actions",
        options=["charge", "discharge", "idle"],
        default=["charge", "discharge", "idle"],
    )

    filtered_dispatch_df = dispatch_df[
        dispatch_df["action"].isin(selected_actions)
    ]

    st.subheader("Forecast + Dispatch View")

    dispatch_view_df = dispatch_df[
        [
            "timestamp",
            "price",
            "action",
            "soc_mwh",
            "grid_energy_mwh",
            "battery_energy_mwh",
            "market_value_eur",
            "cost_eur",
            "pnl_eur",
            "total_pnl_eur",
        ]
    ].copy()

    filtered_dispatch_view_df = dispatch_view_df[
        dispatch_view_df["action"].isin(selected_actions)
    ]

    st.dataframe(filtered_dispatch_view_df, use_container_width=True)

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

    dispatch_csv = filtered_dispatch_view_df.to_csv(index=False).encode("utf-8")

    st.download_button(
        label="Download Dispatch CSV",
        data=dispatch_csv,
        file_name="battery_dispatch_schedule.csv",
        mime="text/csv",
    )


else:
    st.info("No dispatch rows available.")

st.header("Signal Run History")

history_data = get_json("/battery/signal/history")

if history_data is None:
    st.warning("Could not load signal run history.")

elif history_data.get("status") != "ok":
    st.info(history_data.get("message", "No signal run history found yet."))

else:
    runs = history_data.get("runs", [])

    if not runs:
        st.info("No historical signal runs saved yet.")
    else:
        history_df = pd.DataFrame(runs)

        st.dataframe(history_df, use_container_width=True)

        selected_run_file = st.selectbox(
            "Select historical run",
            history_df["file_name"].tolist(),
        )

        if selected_run_file:
            selected_run_response = get_json(
            f"/battery/signal/history/{selected_run_file}"
            )

            selected_dispatch = []
            if selected_run_response and selected_run_response.get("status") == "ok":
                selected_run = selected_run_response["data"]

                st.subheader("Selected Historical Run")

                selected_summary = selected_run.get("summary", {})
                selected_dispatch = selected_run.get("dispatch", [])

                col1, col2, col3, col4 = st.columns(4)

                col1.metric("Signal", selected_summary.get("signal", "-"))
                col2.metric("Opportunity", selected_summary.get("opportunity_level", "-"))
                col3.metric("Total PnL", f"{selected_summary.get('total_pnl_eur', 0)} EUR")
                col4.metric(
                    "Profit per MW-day",
                    f"{selected_summary.get('profit_per_mw_day', 0)} EUR/MW-day",
                )

            if selected_dispatch:
                selected_dispatch_df = pd.DataFrame(selected_dispatch)
                selected_dispatch_df["timestamp"] = pd.to_datetime(
                    selected_dispatch_df["timestamp"],
                    errors="coerce",
                )

                st.line_chart(
                    selected_dispatch_df,
                    x="timestamp",
                    y="total_pnl_eur",
                    use_container_width=True,
                )

                st.dataframe(selected_dispatch_df, use_container_width=True)
            else:
                st.info("Selected run has no dispatch rows.")

        history_csv = history_df.to_csv(index=False).encode("utf-8")

        st.download_button(
            label="Download Run History CSV",
            data=history_csv,
            file_name="battery_signal_run_history.csv",
            mime="text/csv",
        )

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


st.header("Price Stress Tests")

if st.button("Run Price Stress Tests"):
    response = post_json("/stress/run-latest")

    if response is None:
        st.error("Could not run price stress tests.")

    elif response.get("status") == "ok":
        st.success("Price stress tests completed successfully.")
        st.rerun()

    else:
        st.warning(response.get("message", "Price stress tests could not be generated."))


stress_data = get_json("/stress/latest")

if stress_data is None:
    st.warning("Could not load price stress results.")

elif stress_data.get("status") != "ok":
    st.info(stress_data.get("message", "No price stress results available."))

else:
    stress_results = stress_data.get("results", [])

    if stress_results:
        stress_df = pd.DataFrame(stress_results)

        st.dataframe(stress_df, use_container_width=True)

        stress_csv = stress_df.to_csv(index=False).encode("utf-8")

        st.download_button(
            label="Download Price Stress CSV",
            data=stress_csv,
            file_name="price_stress_results.csv",
            mime="text/csv",
        )

        base_case = stress_df[stress_df["scenario_name"] == "Base case"]

        if not base_case.empty:
            base_pnl = float(base_case.iloc[0]["total_pnl_eur"])
            stress_df["pnl_delta_vs_base"] = stress_df["total_pnl_eur"] - base_pnl

            st.subheader("PnL Sensitivity vs Base Case")
            st.bar_chart(
                stress_df,
                x="scenario_name",
                y="pnl_delta_vs_base",
                use_container_width=True,
            )
    else:
        st.info("Price stress result list is empty.")

st.header("Monthly Report")

report_response = get_json("/reports/monthly/latest")

if report_response is None:
    st.warning("Could not load monthly report status.")

elif report_response.get("status") != "ok":
    st.info(report_response.get("message", "No monthly report available."))

else:
    st.success(f"Latest report available: {report_response['report_name']}")

    report_url = f"{API_BASE_URL}/reports/monthly/latest/view"

    st.link_button(
        "Open Latest Monthly Report",
        report_url,
    )

    try:
        report_html_response = requests.get(report_url, timeout=10)
        report_html_response.raise_for_status()

        st.download_button(
            label="Download Monthly Report HTML",
            data=report_html_response.text,
            file_name=report_response["report_name"],
            mime="text/html",
        )

    except requests.RequestException as error:
        st.warning(f"Could not download monthly report: {error}")