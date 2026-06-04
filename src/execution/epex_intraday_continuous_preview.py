from src.db.repositories.execution_repository import get_latest_execution_proposal
from src.execution.market_adapters.epex_intraday_continuous import (
    build_epex_intraday_continuous_preview,
)


def build_latest_epex_intraday_continuous_preview(asset_id):
    proposal_record = get_latest_execution_proposal(asset_id)

    if proposal_record is None:
        raise FileNotFoundError(
            f"No execution proposal found for asset_id={asset_id}."
        )

    proposal = proposal_record["payload"]
    bids = proposal.get("bids") or proposal.get("orders") or []

    preview = build_epex_intraday_continuous_preview(bids=bids)
    preview["asset_id"] = asset_id
    preview["execution_proposal_id"] = proposal_record["execution_proposal_id"]
    preview["proposal_status"] = proposal.get("status")
    preview["approval_status"] = proposal.get("approval_status")

    return preview


def latest_epex_intraday_continuous_preview(asset_id):
    return {
        "status": "ok",
        "asset_id": asset_id,
        "preview": build_latest_epex_intraday_continuous_preview(asset_id),
    }
