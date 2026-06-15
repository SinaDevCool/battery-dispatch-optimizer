from dataclasses import dataclass, field


@dataclass
class OptimizationResult:
    optimizer_engine: str
    status: str
    summary: dict
    dispatch: list[dict]
    metadata: dict = field(default_factory=dict)

    def to_signal_result(self):
        result = {
            "summary": self.summary,
            "dispatch": self.dispatch,
            "optimization": {
                "optimizer_engine": self.optimizer_engine,
                "status": self.status,
                **self.metadata,
            },
        }

        return result



