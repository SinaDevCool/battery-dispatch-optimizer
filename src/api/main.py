from dotenv import load_dotenv
from fastapi import FastAPI

from src.api.routes import API_ROUTERS


load_dotenv()


app = FastAPI(
    title="Battery Dispatch Optimizer API",
    description=(
        "Simple API for battery dispatch signals, backtesting, scenarios, "
        "client config, forecasts, workflows, and reports."
    ),
    version="0.1.0",
)


for router in API_ROUTERS:
    app.include_router(router)
