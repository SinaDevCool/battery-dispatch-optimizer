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


status = get_json("/health")

if status is None:
    st.stop()

st.success("API is running")


client_config_response = get_json("/client/config")

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
    st.info("Run this first: python -m scripts.run_daily_signal")
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
    st.dataframe(dispatch, use_container_width=True)
else:
    st.info("No dispatch rows available.")


st.header("Scenario Analysis")

scenario_data = get_json("/scenarios/latest")

if scenario_data is None:
    st.stop()

if scenario_data.get("status") != "ok":
    st.warning(scenario_data.get("message", "No scenario results available."))
    st.info("Run scenarios first using POST /scenarios/run or python -m scripts.run_scenarios.")
else:
    scenarios = scenario_data["results"]

    if scenarios:
        st.dataframe(scenarios, use_container_width=True)

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