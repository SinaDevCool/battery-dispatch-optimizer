from backend.revenue.revenue_result import RevenueResult
from backend.services.demo_evidence import get_demo_revenue_assumption


def calculate_intraday_revenue(asset):
    demo = get_demo_revenue_assumption(asset, "intraday_arbitrage")
    if demo:
        return RevenueResult(
            product_id="intraday_arbitrage",
            status="ok",
            estimated_revenue_eur=demo["estimated_revenue_eur"],
            source=demo["source"],
            missing_inputs=[],
            assumptions={
                **demo["assumptions"],
                "evidence_mode": "mock_demo",
                "production_upgrade": "Replace mock intraday shape with exchange intraday prices, liquidity, and execution cost evidence.",
            },
            details={
                "message": demo["message"],
            },
        )

    return RevenueResult(
        product_id="intraday_arbitrage",
        status="assumption_required",
        estimated_revenue_eur=None,
        source="placeholder",
        missing_inputs=[
            "intraday_price_series",
            "intraday_liquidity_assumption",
            "execution_cost_assumption",
        ],
        assumptions={
            "market_profile_id": asset.market_profile_id,
        },
        details={
            "message": "Intraday revenue requires intraday prices, liquidity, and execution assumptions.",
        },
    )
