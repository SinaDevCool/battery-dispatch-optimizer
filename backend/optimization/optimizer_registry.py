from backend.optimization.linear_optimizer import (
    LinearDispatchOptimizer,
    LinearProgramDispatchOptimizer,
)
from backend.optimization.rule_based_optimizer import RuleBasedDispatchOptimizer


OPTIMIZER_REGISTRY = {
    "rule_based_v1": RuleBasedDispatchOptimizer,
    "linear_v1": LinearDispatchOptimizer,
    "linear_program_v1": LinearProgramDispatchOptimizer,
}


def get_dispatch_optimizer(optimizer_engine="rule_based_v1"):
    if optimizer_engine not in OPTIMIZER_REGISTRY:
        available_engines = ", ".join(sorted(OPTIMIZER_REGISTRY))
        raise ValueError(
            f"Unknown optimizer engine: {optimizer_engine}. "
            f"Available engines: {available_engines}"
        )

    optimizer_class = OPTIMIZER_REGISTRY[optimizer_engine]

    return optimizer_class()


def list_optimizer_engines():
    return sorted(OPTIMIZER_REGISTRY)
