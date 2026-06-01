import pandas as pd
import streamlit as st

from dashboard.api_client import get_json, post_json


def render_forecast_comparison_section():
    st.header("Forecast Profitability Comparison")

    if st.button("Run Forecast Profitability Comparison"):
        response = post_json("/forecasts/compare-profitability")

        if response is None:
            st.error("Could not run forecast profitability comparison.")

        elif response.get("status") == "ok":
            st.success("Forecast profitability comparison completed successfully.")
            st.rerun()

        else:
            st.warning(
                response.get(
                    "message",
                    "Forecast profitability comparison failed.",
                )
            )

    comparison_response = get_json("/forecasts/compare-profitability/latest")

    if comparison_response is None:
        st.warning("Could not load forecast profitability comparison.")
        return

    if comparison_response.get("status") != "ok":
        st.info(
            comparison_response.get(
                "message",
                "No forecast profitability comparison found.",
            )
        )
        return

    comparison_results = comparison_response.get("results", [])

    if not comparison_results:
        st.info("Forecast profitability comparison is empty.")
        return

    comparison_df = pd.DataFrame(comparison_results)

    st.dataframe(comparison_df, use_container_width=True)

    ok_df = comparison_df[comparison_df["status"] == "ok"]

    if ok_df.empty or "total_pnl_eur" not in ok_df.columns:
        return

    ok_df = ok_df.copy()

    base_rows = ok_df[
        ok_df["forecast_provider"] == "local_saved_forecast"
    ]

    if not base_rows.empty:
        base_pnl = float(base_rows.iloc[0]["total_pnl_eur"])
        ok_df["pnl_delta_vs_local"] = ok_df["total_pnl_eur"] - base_pnl
    else:
        ok_df["pnl_delta_vs_local"] = 0.0

    best_row = ok_df.sort_values(
        "total_pnl_eur",
        ascending=False,
    ).iloc[0]

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Best Forecast", best_row["forecast_provider"])
    col2.metric("Signal", best_row["signal"])
    col3.metric("Total PnL", f"{best_row['total_pnl_eur']} EUR")
    col4.metric(
        "Profit per MW-day",
        f"{best_row['profit_per_mw_day']} EUR/MW-day",
    )

    st.subheader("Total PnL by Forecast Provider")

    st.bar_chart(
        ok_df,
        x="forecast_provider",
        y="total_pnl_eur",
        use_container_width=True,
    )

    st.subheader("PnL Delta vs Local Saved Forecast")

    st.bar_chart(
        ok_df,
        x="forecast_provider",
        y="pnl_delta_vs_local",
        use_container_width=True,
    )
