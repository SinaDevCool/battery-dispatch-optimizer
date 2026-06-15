from backend.execution.market_adapters.epex_intraday_continuous import (
    build_epex_intraday_continuous_preview,
)
from backend.execution.latest_preview import build_latest_bid_preview, preview_response


def build_latest_epex_intraday_continuous_preview(asset_id):
    return build_latest_bid_preview(asset_id, build_epex_intraday_continuous_preview)


def latest_epex_intraday_continuous_preview(asset_id):
    return preview_response(asset_id, build_latest_epex_intraday_continuous_preview(asset_id))



