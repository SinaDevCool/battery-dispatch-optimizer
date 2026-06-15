from backend.revenue.revenue_result import RevenueResult
from backend.services.asset_dispatch_service import dispatch_asset


def calculate_day_ahead_revenue(asset, optimizer_engine="rule_based_v1"):
    try:
        asset_dispatch_result = dispatch_asset(
            asset=asset,
            optimizer_engine=optimizer_engine,
        )
    except FileNotFoundError as error:
        return RevenueResult(
            product_id="day_ahead_arbitrage",
            status="missing_forecast",
            estimated_revenue_eur=None,
            source="dispatch_optimizer",
            missing_inputs=["forecast_file"],
            details={"message": str(error)},
        )
    except Exception as error:
        return RevenueResult(
            product_id="day_ahead_arbitrage",
            status="error",
            estimated_revenue_eur=None,
            source="dispatch_optimizer",
            details={"message": str(error)},
        )

    dispatch_result = asset_dispatch_result.dispatch_result
    summary = dispatch_result.signal_result.get("summary", {})

    return RevenueResult(
        product_id="day_ahead_arbitrage",
        status="ok",
        estimated_revenue_eur=float(summary.get("total_pnl_eur", 0.0)),
        source="dispatch_optimizer",
        assumptions={
            "optimizer_engine": dispatch_result.optimizer_engine,
            "forecast_file": str(asset_dispatch_result.forecast_file),
            "market_profile_id": asset.market_profile_id,
        },
        details={
            "summary": summary,
            "optimization": dispatch_result.signal_result.get("optimization", {}),
            "assumption_risk_flags": asset_dispatch_result.assumption_risk_flags,
        },
    )



