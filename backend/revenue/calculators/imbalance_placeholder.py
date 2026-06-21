from backend.revenue.revenue_result import RevenueResult
from backend.services.demo_evidence import get_demo_revenue_assumption


def calculate_imbalance_revenue(asset):
    demo = get_demo_revenue_assumption(asset, "imbalance_avoidance")
    if demo:
        return RevenueResult(
            product_id="imbalance_avoidance",
            status="ok",
            estimated_revenue_eur=demo["estimated_revenue_eur"],
            source=demo["source"],
            missing_inputs=[],
            assumptions={
                **demo["assumptions"],
                "evidence_mode": "mock_demo",
                "market_profile_id": asset.market_profile_id,
                "production_upgrade": "Replace mock imbalance evidence with imbalance price feeds, schedule deviation data, and BRP settlement evidence.",
            },
            details={
                "message": demo["message"],
            },
        )

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
