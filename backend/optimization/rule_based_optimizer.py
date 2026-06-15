from backend.optimization.base_optimizer import BaseDispatchOptimizer
from backend.optimization.optimization_result import OptimizationResult
from backend.signals.signal_engine import generate_battery_signal


class RuleBasedDispatchOptimizer(BaseDispatchOptimizer):
    optimizer_engine = "rule_based_v1"

    def optimize(
        self,
        price_data,
        battery_config,
        strategy_config,
        commercial_config=None,
    ):
        signal_result = generate_battery_signal(
            price_data=price_data,
            battery_config=battery_config,
            strategy_config=strategy_config,
            commercial_config=commercial_config,
        )

        return OptimizationResult(
            optimizer_engine=self.optimizer_engine,
            status="ok",
            summary=signal_result["summary"],
            dispatch=signal_result["dispatch"],
            metadata={
                "method": "price_spread_rule_based_dispatch",
                "description": "Uses the current rule-based arbitrage engine.",
            },
        )



