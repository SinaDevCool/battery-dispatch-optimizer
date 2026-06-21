from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.routes import API_ROUTERS
from backend.config.app_settings import get_app_settings
from backend.data_environment import reset_current_data_mode, set_current_data_mode


load_dotenv()
settings = get_app_settings()


app = FastAPI(
    title="Battery Dispatch Optimizer API",
    description=(
        "Simple API for battery dispatch signals, backtesting, scenarios, "
        "client config, forecasts, workflows, and reports."
    ),
    version="0.1.0",
)


app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_headers=["*"],
    allow_methods=["*"],
    allow_origins=[
        settings.frontend_origin,
        "http://localhost:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
    ],
    allow_origin_regex=(
        r"http://("
        r"localhost|127\.0\.0\.1|"
        r"10\.\d+\.\d+\.\d+|"
        r"172\.(1[6-9]|2\d|3[01])\.\d+\.\d+|"
        r"192\.168\.\d+\.\d+"
        r"):30\d+"
    ),
)


@app.middleware("http")
async def data_environment_middleware(request, call_next):
    data_mode = (
        request.headers.get("X-Data-Mode")
        or request.query_params.get("data_mode")
        or request.query_params.get("evidence_mode")
    )
    token = set_current_data_mode(data_mode)
    try:
        response = await call_next(request)
        response.headers["X-Data-Mode"] = request.headers.get("X-Data-Mode") or data_mode or "mock"
        return response
    finally:
        reset_current_data_mode(token)


for router in API_ROUTERS:
    app.include_router(router)



