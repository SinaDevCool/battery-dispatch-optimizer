from backend.assets.asset_loader import get_asset
from backend.db.repositories.execution_repository import get_latest_execution_proposal
from backend.db.repositories.telemetry_repository import get_latest_telemetry_snapshot


def build_latest_bid_preview(asset_id, preview_builder):
    proposal_record = get_latest_execution_proposal(asset_id)

    if proposal_record is None:
        raise FileNotFoundError(
            f"No execution proposal found for asset_id={asset_id}."
        )

    proposal = proposal_record["payload"]
    bids = proposal.get("bids") or proposal.get("orders") or []
    preview = preview_builder(bids=bids)
    preview["asset_id"] = asset_id
    preview["execution_proposal_id"] = proposal_record["execution_proposal_id"]
    preview["proposal_status"] = proposal.get("status")
    preview["approval_status"] = proposal.get("approval_status")
    return preview


def build_latest_asset_telemetry_preview(asset_id, preview_builder):
    asset = get_asset(asset_id)
    telemetry_record = get_latest_telemetry_snapshot(asset_id)
    telemetry = (telemetry_record or {}).get("payload") or {}

    preview = preview_builder(asset=asset, telemetry=telemetry)
    preview["asset_id"] = asset_id
    preview["telemetry_id"] = (telemetry_record or {}).get("telemetry_id")
    return preview


def preview_response(asset_id, preview):
    return {
        "status": "ok",
        "asset_id": asset_id,
        "preview": preview,
    }



