from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.routes import API_ROUTERS
from src.config.app_settings import get_app_settings


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
        "http://127.0.0.1:3000",
    ],
    allow_origin_regex=r"http://(localhost|127\.0\.0\.1|192\.168\.\d+\.\d+):3000",
)


for router in API_ROUTERS:
    app.include_router(router)
