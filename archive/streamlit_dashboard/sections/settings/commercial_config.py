import streamlit as st


def render_commercial_config_section(commercial_cfg):
    st.subheader("Commercial Costs")

    col1, col2, col3 = st.columns(3)

    with col1:
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

    with col2:
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

    with col3:
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

    return {
        "trading_fee_eur_per_mwh": trading_fee_eur_per_mwh,
        "market_access_fee_eur_per_mwh": market_access_fee_eur_per_mwh,
        "grid_fee_import_eur_per_mwh": grid_fee_import_eur_per_mwh,
        "grid_fee_export_eur_per_mwh": grid_fee_export_eur_per_mwh,
        "tax_or_levy_eur_per_mwh": tax_or_levy_eur_per_mwh,
        "degradation_cost_eur_per_mwh_throughput": degradation_cost_eur_per_mwh_throughput,
    }




