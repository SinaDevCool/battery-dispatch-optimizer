from dataclasses import dataclass, field


@dataclass
class MarketProduct:
    product_id: str
    name: str
    country: str
    market: str
    bidding_zone: str
    settlement_interval_minutes: int
    revenue_type: str
    requires_prequalification: bool
    stackable_with: list[str] = field(default_factory=list)
    minimum_power_mw: float | None = None
    minimum_duration_hours: float | None = None
    risk_notes: list[str] = field(default_factory=list)
    required_asset_fields: list[str] = field(default_factory=list)
    required_regulatory_fields: list[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data):
        return cls(
            product_id=data["product_id"],
            name=data["name"],
            country=data.get("country", "Germany"),
            market=data.get("market", "DE_LU"),
            bidding_zone=data.get("bidding_zone", "DE_LU"),
            settlement_interval_minutes=int(
                data.get("settlement_interval_minutes", 15)
            ),
            revenue_type=data["revenue_type"],
            requires_prequalification=bool(
                data.get("requires_prequalification", False)
            ),
            stackable_with=data.get("stackable_with", []),
            minimum_power_mw=data.get("minimum_power_mw"),
            minimum_duration_hours=data.get("minimum_duration_hours"),
            risk_notes=data.get("risk_notes", []),
            required_asset_fields=data.get("required_asset_fields", []),
            required_regulatory_fields=data.get("required_regulatory_fields", []),
        )

    def to_dict(self):
        return {
            "product_id": self.product_id,
            "name": self.name,
            "country": self.country,
            "market": self.market,
            "bidding_zone": self.bidding_zone,
            "settlement_interval_minutes": self.settlement_interval_minutes,
            "revenue_type": self.revenue_type,
            "requires_prequalification": self.requires_prequalification,
            "stackable_with": self.stackable_with,
            "minimum_power_mw": self.minimum_power_mw,
            "minimum_duration_hours": self.minimum_duration_hours,
            "risk_notes": self.risk_notes,
            "required_asset_fields": self.required_asset_fields,
            "required_regulatory_fields": self.required_regulatory_fields,
        }
