from dataclasses import dataclass, field


@dataclass
class ValidationResult:
    status: str
    errors: list[dict] = field(default_factory=list)
    warnings: list[dict] = field(default_factory=list)

    def to_dict(self):
        return {
            "status": self.status,
            "errors": self.errors,
            "warnings": self.warnings,
            "error_count": len(self.errors),
            "warning_count": len(self.warnings),
        }
