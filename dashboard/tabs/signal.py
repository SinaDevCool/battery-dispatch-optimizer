import pandas as pd
import streamlit as st

from dashboard.api_client import get_json, post_json


def render_signal_tab():
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

    latest_signal = get_json("/battery/signal/latest")

    st.header("Latest Battery Signal")

    if latest_signal is None:
        st.warning("Could not load latest signal.")
        return

    if latest_signal.get("status") != "ok":
        st.warning(latest_signal.get("message", "No latest signal available."))
        st.info("Click Generate Daily Battery Signal first.")
        return

    signal_data = latest_signal["data"]
    summary = signal_data["summary"]
    dispatch = signal_data["dispatch"]

    metadata = signal_data.get("metadata", {})

    source = metadata.get("source", "-")
    forecast_model = metadata.get("forecast_model", "-")
    target_date = metadata.get("target_date", "-")
    generated_at = metadata.get("generated_at", "-")

    col_source1, col_source2, col_source3, col_source4 = st.columns(4)

    col_source1.metric("Forecast Source", source)
    col_source2.metric("Forecast Model", forecast_model)
    col_source3.metric("Target Date", target_date)
    col_source4.metric("Generated At", generated_at)

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

        display_columns = [
            "timestamp",
            "price",
            "action",
            "grid_energy_mwh",
            "battery_energy_mwh",
            "market_value_eur",
            "cost_eur",
            "pnl_eur",
        ]

        available_columns = [
            column for column in display_columns
            if column in action_df.columns
        ]

        st.dataframe(
            action_df[available_columns],
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

        if {
            "market_value_eur",
            "cost_eur",
            "pnl_eur",
        }.issubset(dispatch_cost_df.columns):
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

                if (
                    selected_run_response
                    and selected_run_response.get("status") == "ok"
                ):
                    selected_run = selected_run_response["data"]

                    st.subheader("Selected Historical Run")

                    selected_summary = selected_run.get("summary", {})
                    selected_dispatch = selected_run.get("dispatch", [])

                    col1, col2, col3, col4 = st.columns(4)

                    col1.metric("Signal", selected_summary.get("signal", "-"))
                    col2.metric(
                        "Opportunity",
                        selected_summary.get("opportunity_level", "-"),
                    )
                    col3.metric(
                        "Total PnL",
                        f"{selected_summary.get('total_pnl_eur', 0)} EUR",
                    )
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