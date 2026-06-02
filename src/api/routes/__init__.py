from src.api.routes.assets import router as assets_router
from src.api.routes.asset_signals import router as asset_signals_router
from src.api.routes.battery import router as battery_router
from src.api.routes.client import router as client_router
from src.api.routes.forecasts import router as forecasts_router
from src.api.routes.markets import router as markets_router
from src.api.routes.market_products import router as market_products_router
from src.api.routes.reports import router as reports_router
from src.api.routes.regulatory import router as regulatory_router
from src.api.routes.revenue import router as revenue_router
from src.api.routes.scenarios import router as scenarios_router
from src.api.routes.system import router as system_router
from src.api.routes.workflow import router as workflow_router


API_ROUTERS = [
    system_router,
    assets_router,
    asset_signals_router,
    market_products_router,
    markets_router,
    regulatory_router,
    revenue_router,
    client_router,
    forecasts_router,
    battery_router,
    scenarios_router,
    reports_router,
    workflow_router,
]
