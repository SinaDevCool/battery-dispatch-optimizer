import pandas as pd
import streamlit as st

from dashboard.api_client import post_json


def _forecast_df_to_price_data(forecast_df):
    price_data = []

    for _, row in forecast_df.iterrows():
        price_data.append(
            {
                "timestamp": str(row["timestamp"]),
                "price": float(row["forecast_price"]),
            }
        )

    return price_data


def render_saved_forecast_section():
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

            response = post_json(
                "/forecast/upload",
                {
                    "price_data": _forecast_df_to_price_data(edited_df),
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
