from src.assets.asset_loader import get_asset, load_assets


def list_asset_records():
    return [
        asset.to_dict()
        for asset in load_assets()
    ]


def get_asset_record(asset_id):
    return get_asset(asset_id).to_dict()
