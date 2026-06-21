from backend.revenue.revenue_result import RevenueResult
from backend.services.demo_evidence import get_demo_revenue_assumption


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
    demo = get_demo_revenue_assumption(asset, product_id)
    if demo:
        return RevenueResult(
            product_id=product_id,
            status="ok",
            estimated_revenue_eur=demo["estimated_revenue_eur"],
            source=demo["source"],
            missing_inputs=[],
            assumptions={
                **demo["assumptions"],
                "evidence_mode": "mock_demo",
                "market_profile_id": asset.market_profile_id,
                "production_upgrade": "Replace mock reserve capacity evidence with TSO product prices, prequalification records, availability telemetry, and settlement records.",
            },
            details={
                "message": demo["message"],
            },
        )

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
