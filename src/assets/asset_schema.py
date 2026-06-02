from dataclasses import dataclass, field


@dataclass
class BatteryAsset:
    asset_id: str
    client_name: str
    site_name: str
    country: str
    market: str
    battery_config: dict
    strategy_config: dict
    commercial_config: dict = field(default_factory=dict)
    forecast_file: str | None = None
    market_profile_id: str = "de_lu_day_ahead"
    grid_connection: dict = field(default_factory=dict)
    regulatory: dict = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data):
        return cls(
            asset_id=data["asset_id"],
            client_name=data.get("client_name", ""),
            site_name=data.get("site_name", ""),
            country=data.get("country", ""),
            market=data.get("market", ""),
            battery_config=data["battery_config"],
            strategy_config=data["strategy_config"],
            commercial_config=data.get("commercial_config", {}),
            forecast_file=data.get("forecast_file"),
            market_profile_id=data.get("market_profile_id", "de_lu_day_ahead"),
            grid_connection=data.get("grid_connection", {}),
            regulatory=data.get("regulatory", {}),
        )

    def to_dict(self):
        return {
            "asset_id": self.asset_id,
            "client_name": self.client_name,
            "site_name": self.site_name,
            "country": self.country,
            "market": self.market,
            "battery_config": self.battery_config,
            "strategy_config": self.strategy_config,
            "commercial_config": self.commercial_config,
            "forecast_file": self.forecast_file,
            "market_profile_id": self.market_profile_id,
            "grid_connection": self.grid_connection,
            "regulatory": self.regulatory,
        }
