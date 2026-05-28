import pandas as pd
import streamlit as st

from dashboard.api_client import get_json, post_json


def render_forecast_tab():
    st.header("Forecast Quality")

    forecast_quality = get_json("/forecast/status")

    if forecast_quality is None:
        st.warning("Could not load forecast quality status.")

    elif forecast_quality.get("status") != "ok":
        st.warning(
            forecast_quality.get(
                "message",
                "Forecast quality check failed.",
            )
        )

    else:
        col1, col2, col3, col4 = st.columns(4)

        col1.metric("Rows", forecast_quality["row_count"])
        col2.metric("Valid Rows", forecast_quality["valid_row_count"])
        col3.metric("Negative Prices", forecast_quality["negative_price_hours"])
        col4.metric(
            "Duplicate Timestamps",
            forecast_quality["duplicate_timestamps"],
        )

        col5, col6, col7 = st.columns(3)

        col5.metric("Min Price", f"{forecast_quality['min_price']} EUR/MWh")
        col6.metric("Max Price", f"{forecast_quality['max_price']} EUR/MWh")
        col7.metric(
            "Average Price",
            f"{forecast_quality['average_price']} EUR/MWh",
        )

        with st.expander("Forecast time range"):
            st.write("First timestamp:", forecast_quality["first_timestamp"])
            st.write("Last timestamp:", forecast_quality["last_timestamp"])
            st.write("Invalid timestamps:", forecast_quality["invalid_timestamps"])
            st.write("Missing prices:", forecast_quality["missing_prices"])

    
    st.header("Forecast Feature Preview")

    forecast_preview = get_json("/forecast/preview")

    if forecast_preview is None:
        st.warning("Could not load forecast preview.")

    elif forecast_preview.get("status") != "ok":
        st.info(forecast_preview.get("message", "No forecast preview available."))

    else:
        preview_df = pd.DataFrame(forecast_preview.get("preview", []))

        st.write(
            f"Rows: {forecast_preview.get('rows')} | "
            f"Columns: {', '.join(forecast_preview.get('columns', []))}"
        )

        if not preview_df.empty:
            preview_df["timestamp"] = pd.to_datetime(
                preview_df["timestamp"],
                errors="coerce",
            )

            st.dataframe(preview_df, use_container_width=True)

            chart_columns = [
                column for column in [
                    "forecast_price",
                    "load_forecast",
                    "generation_forecast",
                    "forecast_solar",
                    "forecast_wind",
                    "forecast_renewables_total",
                ]
                if column in preview_df.columns
            ]

            if chart_columns:
                selected_chart_column = st.selectbox(
                    "Forecast feature chart",
                    options=chart_columns,
                )

                st.line_chart(
                    preview_df,
                    x="timestamp",
                    y=selected_chart_column,
                    use_container_width=True,
             )
    
    
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

    if st.button("Create High-Spread Demo Forecast"):
        response = post_json("/forecast/demo-high-spread")

        if response and response.get("status") == "ok":
            st.success(
                f"High-spread demo forecast created with {response.get('rows')} rows."
            )
            st.info("Run Forecast Profitability Comparison to compare it.")
            st.rerun()
        else:
            st.warning("Could not create high-spread demo forecast.")

    if st.button("Create In-House Placeholder Forecast"):
        response = post_json("/forecast/inhouse-placeholder")

        if response and response.get("status") == "ok":
            st.success(
                f"In-house placeholder forecast created with {response.get('rows')} rows."
            )
            st.info("Run Forecast Profitability Comparison to include it.")
            st.rerun()
        else:
            st.warning("Could not create in-house placeholder forecast.")
    st.header("Forecast Upload")

    uploaded_file = st.file_uploader(
        "Upload next-day price forecast CSV",
        type=["csv"],
    )

    if uploaded_file is not None:
        try:
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
                st.error(
                    f"Forecast has {missing_prices} missing or invalid prices."
                )

            elif duplicate_timestamps > 0:
                st.error(
                    f"Forecast has {duplicate_timestamps} duplicate timestamps."
                )

            elif row_count < 2:
                st.error("Forecast must contain at least 2 rows.")

            else:
                if row_count != 24:
                    st.warning(
                        f"Forecast has {row_count} rows. "
                        "Expected 24 hourly rows for a full next-day signal."
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
                        st.info(
                            "Battery signal was generated automatically. "
                            "The dashboard will refresh."
                        )
                        st.rerun()
                    else:
                        st.warning("Forecast upload failed.")

        except Exception as error:
            st.error(f"Could not read forecast CSV: {error}")

    
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

    elif comparison_response.get("status") != "ok":
        st.info(
            comparison_response.get(
                "message",
                "No forecast profitability comparison found.",
            )
        )

    else:
        comparison_results = comparison_response.get("results", [])

        if not comparison_results:
            st.info("Forecast profitability comparison is empty.")

        else:
            comparison_df = pd.DataFrame(comparison_results)

            st.dataframe(comparison_df, use_container_width=True)

            ok_df = comparison_df[comparison_df["status"] == "ok"]

            if not ok_df.empty and "total_pnl_eur" in ok_df.columns:
                ok_df = ok_df.copy()

                base_rows = ok_df[
                ok_df["forecast_provider"] == "local_saved_forecast"
                ]

                if not base_rows.empty:
                    base_pnl = float(base_rows.iloc[0]["total_pnl_eur"])
                    ok_df["pnl_delta_vs_local"] = ok_df["total_pnl_eur"] - base_pnl
                else:
                    ok_df["pnl_delta_vs_local"] = 0.0

            if not ok_df.empty and "total_pnl_eur" in ok_df.columns:
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
    
    
    
    st.header("Data Update")

    st.caption(
        "Live ENTSO-E data is optional. If it is unavailable, the app keeps using the saved local forecast."
        )

    if st.button("Try Live ENTSO-E Update"):
        response = post_json("/data/update-entsoe")

        if response is None:
            st.error("Could not update ENTSO-E forecast.")

        elif response.get("status") == "ok":
            st.success(
                f"ENTSO-E forecast updated for {response.get('target_date')} "
                f"with {response.get('rows')} rows."
            )
            st.info("Now click Generate Daily Battery Signal.")

        elif response.get("status") == "fallback":
            st.warning(response.get("message", "Live ENTSO-E update failed."))
            st.info("The existing saved forecast is still available for local CSV mode.")

        else:
            st.warning(response.get("message", "ENTSO-E update failed."))
