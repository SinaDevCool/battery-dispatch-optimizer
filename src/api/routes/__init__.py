from src.api.routes.battery import router as battery_router
from src.api.routes.client import router as client_router
from src.api.routes.forecasts import router as forecasts_router
from src.api.routes.reports import router as reports_router
from src.api.routes.scenarios import router as scenarios_router
from src.api.routes.system import router as system_router
from src.api.routes.workflow import router as workflow_router


API_ROUTERS = [
    system_router,
    client_router,
    forecasts_router,
    battery_router,
    scenarios_router,
    reports_router,
    workflow_router,
]
