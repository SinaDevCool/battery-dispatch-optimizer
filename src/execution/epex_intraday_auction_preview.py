from src.execution.market_adapters.epex_intraday_auction import (
    build_epex_intraday_auction_preview,
)
from src.execution.latest_preview import build_latest_bid_preview, preview_response


def build_latest_epex_intraday_auction_preview(asset_id):
    return build_latest_bid_preview(asset_id, build_epex_intraday_auction_preview)


def latest_epex_intraday_auction_preview(asset_id):
    return preview_response(asset_id, build_latest_epex_intraday_auction_preview(asset_id))
