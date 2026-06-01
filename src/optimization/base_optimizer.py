from abc import ABC, abstractmethod

from src.optimization.optimization_result import OptimizationResult


class BaseDispatchOptimizer(ABC):
    optimizer_engine = "base"

    @abstractmethod
    def optimize(
        self,
        price_data,
        battery_config,
        strategy_config,
        commercial_config=None,
    ) -> OptimizationResult:
        raise NotImplementedError
