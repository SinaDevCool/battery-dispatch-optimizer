from dataclasses import dataclass, field


@dataclass
class RegulatoryResult:
    status: str
    warnings: list[dict] = field(default_factory=list)
    requirements: list[dict] = field(default_factory=list)
    assumptions: dict = field(default_factory=dict)

    def to_dict(self):
        return {
            "status": self.status,
            "warnings": self.warnings,
            "requirements": self.requirements,
            "assumptions": self.assumptions,
            "warning_count": len(self.warnings),
            "requirement_count": len(self.requirements),
        }
