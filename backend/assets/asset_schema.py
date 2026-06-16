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
    asset_name: str | None = None
    asset_type: str = "grid_scale_battery"
    asset_subtype: str = "standalone_grid_connected"
    data_mode: str = "mock"
    data_source: str = "local_seed"
    data_profile: dict = field(default_factory=dict)
    commercial_config: dict = field(default_factory=dict)
    forecast_file: str | None = None
    market_profile_id: str = "de_lu_day_ahead"
    grid_connection: dict = field(default_factory=dict)
    investment_assumptions: dict = field(default_factory=dict)
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
            asset_name=data.get("asset_name"),
            asset_type=data.get("asset_type", "grid_scale_battery"),
            asset_subtype=data.get("asset_subtype", "standalone_grid_connected"),
            data_mode=data.get("data_mode", "mock"),
            data_source=data.get("data_source", "local_seed"),
            data_profile=data.get("data_profile", {}),
            commercial_config=data.get("commercial_config", {}),
            forecast_file=data.get("forecast_file"),
            market_profile_id=data.get("market_profile_id", "de_lu_day_ahead"),
            grid_connection=data.get("grid_connection", {}),
            investment_assumptions=data.get("investment_assumptions", {}),
            regulatory=data.get("regulatory", {}),
        )

    def to_dict(self):
        return {
            "asset_id": self.asset_id,
            "client_name": self.client_name,
            "site_name": self.site_name,
            "asset_name": self.asset_name,
            "asset_type": self.asset_type,
            "asset_subtype": self.asset_subtype,
            "data_mode": self.data_mode,
            "data_source": self.data_source,
            "data_profile": self.data_profile,
            "country": self.country,
            "market": self.market,
            "battery_config": self.battery_config,
            "strategy_config": self.strategy_config,
            "commercial_config": self.commercial_config,
            "forecast_file": self.forecast_file,
            "market_profile_id": self.market_profile_id,
            "grid_connection": self.grid_connection,
            "investment_assumptions": self.investment_assumptions,
            "regulatory": self.regulatory,
        }



