import pandas as pd
import streamlit as st

from dashboard.api_client import post_json


def _build_price_data(forecast_df):
    price_data = []

    for _, row in forecast_df.iterrows():
        price_data.append(
            {
                "timestamp": str(row["timestamp"]),
                "price": float(row["forecast_price"]),
            }
        )

    return price_data


def render_forecast_upload_section():
    st.header("Forecast Upload")

    uploaded_file = st.file_uploader(
        "Upload next-day price forecast CSV",
        type=["csv"],
    )

    if uploaded_file is None:
        return

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
                response = post_json(
                    "/forecast/upload",
                    {
                        "price_data": _build_price_data(forecast_df),
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
