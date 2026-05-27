from fastapi import FastAPI

from src.api.schemas import BatterySignalRequest, BatterySignalResponse
from src.signals.signal_engine import generate_battery_signal


app = FastAPI(
    title="Battery Dispatch Optimizer API",
    description="Simple API for battery dispatch signals and backtesting.",
    version="0.1.0",
)


@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "service": "battery-dispatch-optimizer",
    }


@app.post("/battery/signal", response_model=BatterySignalResponse)
def battery_signal(request: BatterySignalRequest):
    price_data = [
        {
            "timestamp": item.timestamp,
            "price": item.price,
        }
        for item in request.price_data
    ]

    battery_config = None
    strategy_config = None

    if request.battery_config is not None:
        battery_config = request.battery_config.model_dump()

    if request.strategy_config is not None:
        strategy_config = request.strategy_config.model_dump()

    result = generate_battery_signal(
        price_data=price_data,
        battery_config=battery_config,
        strategy_config=strategy_config,
    )

    return result