from src.revenue.revenue_result import RevenueResult


RESERVE_REQUIRED_INPUTS = {
    "fcr_capacity": [
        "fcr_capacity_price_eur_per_mw_h",
        "prequalified_fcr",
        "reserve_availability_hours",
        "activation_energy_assumption",
    ],
    "afrr_capacity": [
        "afrr_capacity_price_eur_per_mw_h",
        "prequalified_afrr",
        "reserve_availability_hours",
        "activation_energy_assumption",
    ],
    "mfrr_capacity": [
        "mfrr_capacity_price_eur_per_mw_h",
        "prequalified_mfrr",
        "reserve_availability_hours",
        "activation_energy_assumption",
    ],
}


def calculate_reserve_capacity_revenue(asset, product_id):
    regulatory = asset.regulatory or {}
    missing_inputs = []

    for input_name in RESERVE_REQUIRED_INPUTS.get(product_id, []):
        if input_name.startswith("prequalified_"):
            if not regulatory.get(input_name):
                missing_inputs.append(input_name)
        else:
            missing_inputs.append(input_name)

    return RevenueResult(
        product_id=product_id,
        status="assumption_required",
        estimated_revenue_eur=None,
        source="placeholder",
        missing_inputs=missing_inputs,
        assumptions={
            "requires_prequalification": True,
            "market_profile_id": asset.market_profile_id,
        },
        details={
            "message": "Reserve revenue requires product price, prequalification, availability, and activation assumptions.",
        },
    )
