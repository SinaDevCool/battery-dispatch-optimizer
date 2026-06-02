from src.revenue.revenue_result import RevenueResult


def calculate_intraday_revenue(asset):
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
