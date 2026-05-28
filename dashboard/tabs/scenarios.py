import pandas as pd
import streamlit as st

from dashboard.api_client import get_json, post_json


def render_scenarios_tab():
    st.header("Scenario Analysis")

    if st.button("Run Scenario Analysis"):
        response = post_json("/scenarios/run-latest")

        if response is None:
            st.error("Could not run scenario analysis.")

        elif response.get("status") == "ok":
            st.success("Scenario analysis completed successfully.")
            st.rerun()

        else:
            st.warning(
                response.get(
                    "message",
                    "Scenario analysis could not be generated.",
                )
            )

    scenario_data = get_json("/scenarios/latest")

    if scenario_data is None:
        st.warning("Could not load scenario results.")

    elif scenario_data.get("status") != "ok":
        st.info(scenario_data.get("message", "No scenario results available."))
        st.info("Click Run Scenario Analysis first.")

    else:
        scenarios = scenario_data.get("results", [])

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

            if "total_pnl_eur" in scenario_df.columns:
                best_scenario = max(
                    scenarios,
                    key=lambda row: row.get("total_pnl_eur", 0),
                )

                st.subheader("Best Scenario")

                col1, col2, col3, col4 = st.columns(4)

                col1.metric(
                    "Scenario",
                    best_scenario.get("scenario_name", "-"),
                )
                col2.metric(
                    "Total PnL",
                    f"{best_scenario.get('total_pnl_eur', 0)} EUR",
                )
                col3.metric(
                    "Profit per MW-day",
                    f"{best_scenario.get('profit_per_mw_day', 0)} EUR/MW-day",
                )
                col4.metric(
                    "Opportunity",
                    best_scenario.get("opportunity_level", "-"),
                )

                st.subheader("Scenario PnL Comparison")

                st.bar_chart(
                    scenario_df,
                    x="scenario_name",
                    y="total_pnl_eur",
                    use_container_width=True,
                )
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
            st.warning(
                response.get(
                    "message",
                    "Price stress tests could not be generated.",
                )
            )

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

            if (
                "scenario_name" in stress_df.columns
                and "total_pnl_eur" in stress_df.columns
            ):
                base_case = stress_df[stress_df["scenario_name"] == "Base case"]

                if not base_case.empty:
                    base_pnl = float(base_case.iloc[0]["total_pnl_eur"])
                    stress_df = stress_df.copy()
                    stress_df["pnl_delta_vs_base"] = (
                        stress_df["total_pnl_eur"] - base_pnl
                    )

                    st.subheader("PnL Sensitivity vs Base Case")

                    st.bar_chart(
                        stress_df,
                        x="scenario_name",
                        y="pnl_delta_vs_base",
                        use_container_width=True,
                    )
        else:
            st.info("Price stress result list is empty.")