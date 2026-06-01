from dataclasses import dataclass

from src.forecasts.forecast_loader import load_forecast_price_data
from src.optimization.optimizer_registry import get_dispatch_optimizer


@dataclass
class DispatchOptimizationResult:
    signal_result: dict
    price_data: list[dict]
    optimizer_engine: str


def optimize_dispatch_from_price_data(
    price_data,
    battery_config,
    strategy_config,
    commercial_config=None,
    optimizer_engine="rule_based_v1",
):
    optimizer = get_dispatch_optimizer(optimizer_engine)

    optimization_result = optimizer.optimize(
        price_data=price_data,
        battery_config=battery_config,
        strategy_config=strategy_config,
        commercial_config=commercial_config,
    )

    return DispatchOptimizationResult(
        signal_result=optimization_result.to_signal_result(),
        price_data=price_data,
        optimizer_engine=optimization_result.optimizer_engine,
    )


def optimize_dispatch_from_forecast_file(
    forecast_file,
    battery_config,
    strategy_config,
    commercial_config=None,
    optimizer_engine="rule_based_v1",
):
    price_data = load_forecast_price_data(forecast_file)

    return optimize_dispatch_from_price_data(
        price_data=price_data,
        battery_config=battery_config,
        strategy_config=strategy_config,
        commercial_config=commercial_config,
        optimizer_engine=optimizer_engine,
    )
