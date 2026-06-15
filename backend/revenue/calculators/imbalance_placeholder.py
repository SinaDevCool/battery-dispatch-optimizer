from backend.revenue.revenue_result import RevenueResult


def calculate_imbalance_revenue(asset):
    missing_inputs = [
        "imbalance_price_series",
        "schedule_deviation_series",
        "balancing_responsible_party",
    ]

    regulatory = asset.regulatory or {}

    if regulatory.get("balancing_responsible_party"):
        missing_inputs.remove("balancing_responsible_party")

    return RevenueResult(
        product_id="imbalance_avoidance",
        status="assumption_required",
        estimated_revenue_eur=None,
        source="placeholder",
        missing_inputs=missing_inputs,
        assumptions={
            "market_profile_id": asset.market_profile_id,
        },
        details={
            "message": "Imbalance value requires imbalance prices and schedule deviation exposure.",
        },
    )



