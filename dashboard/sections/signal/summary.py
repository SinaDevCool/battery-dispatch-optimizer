import pandas as pd
import streamlit as st


def render_signal_summary_section(signal_data, summary, dispatch):
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

    if not dispatch:
        return

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
