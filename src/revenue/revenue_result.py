from dataclasses import dataclass, field


@dataclass
class RevenueResult:
    product_id: str
    status: str
    estimated_revenue_eur: float | None
    source: str
    missing_inputs: list[str] = field(default_factory=list)
    assumptions: dict = field(default_factory=dict)
    details: dict = field(default_factory=dict)

    def to_dict(self):
        return {
            "product_id": self.product_id,
            "status": self.status,
            "estimated_revenue_eur": self.estimated_revenue_eur,
            "source": self.source,
            "missing_inputs": self.missing_inputs,
            "assumptions": self.assumptions,
            "details": self.details,
        }
