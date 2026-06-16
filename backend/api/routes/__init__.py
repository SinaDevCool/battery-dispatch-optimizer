from backend.api.routes.assets import router as assets_router
from backend.api.routes.asset_signals import router as asset_signals_router
from backend.api.routes.battery import router as battery_router
from backend.api.routes.business_decisions import router as business_decisions_router
from backend.api.routes.client import router as client_router
from backend.api.routes.execution import router as execution_router
from backend.api.routes.forecast_actual import router as forecast_actual_router
from backend.api.routes.forecasts import router as forecasts_router
from backend.api.routes.history import router as history_router
from backend.api.routes.markets import router as markets_router
from backend.api.routes.market_products import router as market_products_router
from backend.api.routes.reports import router as reports_router
from backend.api.routes.regulatory import router as regulatory_router
from backend.api.routes.revenue import router as revenue_router
from backend.api.routes.scenarios import router as scenarios_router
from backend.api.routes.settlement import router as settlement_router
from backend.api.routes.summaries import router as summaries_router
from backend.api.routes.system import router as system_router
from backend.api.routes.telemetry import router as telemetry_router
from backend.api.routes.workflow import router as workflow_router
from backend.api.routes.workflow_runs import router as workflow_runs_router


API_ROUTERS = [
    system_router,
    assets_router,
    asset_signals_router,
    market_products_router,
    markets_router,
    regulatory_router,
    revenue_router,
    settlement_router,
    summaries_router,
    telemetry_router,
    business_decisions_router,
    execution_router,
    history_router,
    forecast_actual_router,
    client_router,
    forecasts_router,
    battery_router,
    scenarios_router,
    reports_router,
    workflow_router,
    workflow_runs_router,
]



