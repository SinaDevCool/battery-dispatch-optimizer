from src.optimization.base_optimizer import BaseDispatchOptimizer


class LinearDispatchOptimizer(BaseDispatchOptimizer):
    optimizer_engine = "linear_v1"

    def optimize(
        self,
        price_data,
        battery_config,
        strategy_config,
        commercial_config=None,
    ):
        raise NotImplementedError(
            "linear_v1 is reserved for the future linear programming dispatch engine."
        )
