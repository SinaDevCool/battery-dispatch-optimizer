import json

from backend.assets.asset_schema import BatteryAsset
from backend.config.client_config import load_client_config
from backend.config.paths import ASSETS_CONFIG_FILE, FORECAST_FILE


def build_default_asset_from_client_config():
    client_config = load_client_config()

    return BatteryAsset(
        asset_id="default_site",
        client_name=client_config.get("client_name", "Default Client"),
        site_name=client_config.get("site_name", "Default Battery Site"),
        asset_name=client_config.get("asset_name"),
        asset_type=client_config.get("asset_type", "grid_scale_battery"),
        asset_subtype=client_config.get("asset_subtype", "standalone_grid_connected"),
        data_mode=client_config.get("data_mode", "mock"),
        data_source=client_config.get("data_source", "client_config_seed"),
        data_profile=client_config.get("data_profile", {}),
        country=client_config.get("country", ""),
        market=client_config.get("market", ""),
        battery_config=client_config["battery_config"],
        strategy_config=client_config["strategy_config"],
        commercial_config=client_config.get("commercial_config", {}),
        forecast_file=str(FORECAST_FILE),
        market_profile_id=client_config.get("market_profile_id", "de_lu_day_ahead"),
        grid_connection=client_config.get("grid_connection", {}),
        regulatory=client_config.get("regulatory", {}),
    )


def load_assets(config_file=ASSETS_CONFIG_FILE):
    if not config_file.exists():
        return [build_default_asset_from_client_config()]

    with open(config_file, "r", encoding="utf-8") as file:
        data = json.load(file)

    raw_assets = data.get("assets", [])

    if not raw_assets:
        return [build_default_asset_from_client_config()]

    return [BatteryAsset.from_dict(asset) for asset in raw_assets]


def get_asset(asset_id, config_file=ASSETS_CONFIG_FILE):
    assets = load_assets(config_file=config_file)

    for asset in assets:
        if asset.asset_id == asset_id:
            return asset

    raise ValueError(f"Asset not found: {asset_id}")


def save_assets(assets, config_file=ASSETS_CONFIG_FILE):
    config_file.parent.mkdir(parents=True, exist_ok=True)

    payload = {
        "assets": [
            asset.to_dict() if hasattr(asset, "to_dict") else asset
            for asset in assets
        ]
    }

    with open(config_file, "w", encoding="utf-8") as file:
        json.dump(payload, file, indent=2)

    return config_file



