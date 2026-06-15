from backend.execution.latest_preview import (
    build_latest_asset_telemetry_preview,
    preview_response,
)
from backend.execution.market_adapters.regelleistung_mfrr import (
    build_regelleistung_mfrr_preview,
)


def build_latest_regelleistung_mfrr_preview(asset_id):
    return build_latest_asset_telemetry_preview(
        asset_id,
        build_regelleistung_mfrr_preview,
    )


def latest_regelleistung_mfrr_preview(asset_id):
    return preview_response(asset_id, build_latest_regelleistung_mfrr_preview(asset_id))



