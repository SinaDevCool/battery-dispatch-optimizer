from datetime import datetime

from src.db.repositories.execution_repository import (
    get_latest_execution_market_submission,
    get_latest_execution_proposal,
    list_execution_market_submissions,
    save_execution_market_submission,
)
from src.execution.approval_workflow import require_latest_approval
from src.execution.market_adapters.demo_market import DemoMarketAdapter


def run_demo_market_submission(asset_id):
    proposal_record = get_latest_execution_proposal(asset_id)

    if proposal_record is None:
        raise FileNotFoundError(
            f"No execution proposal found for asset_id={asset_id}."
        )

    proposal = proposal_record["payload"]
    bids = proposal.get("bids") or proposal.get("orders", [])

    if not bids:
        raise ValueError("Latest execution proposal has no bids to submit.")

    approval = require_latest_approval(
        asset_id=asset_id,
        execution_proposal_id=proposal_record["execution_proposal_id"],
    )
    submitted_at = datetime.now().isoformat(timespec="seconds")
    adapter = DemoMarketAdapter()
    adapter_result = adapter.submit_bids(
        bids=bids,
        submitted_at=submitted_at,
    )
    submission = {
        "status": adapter_result["status"],
        "asset_id": asset_id,
        "execution_proposal_id": proposal_record["execution_proposal_id"],
        "approval_id": approval.get("approval_id"),
        "submitted_at": submitted_at,
        "adapter_id": adapter.adapter_id,
        "live_submission": adapter.live_submission,
        "summary": adapter_result["summary"],
        "bids": adapter_result["bids"],
        "lifecycle": build_submission_lifecycle(adapter_result),
        "audit": [
            {
                "event": "demo_submission_started",
                "actor": "execution_service",
                "status": "complete",
                "note": "Loaded latest approved execution proposal and submitted bids to demo adapter.",
            },
            {
                "event": "demo_market_result_received",
                "actor": "demo_market_adapter",
                "status": adapter_result["status"],
                "note": "Demo adapter simulated accepted, rejected, and awarded bid states.",
            },
        ],
    }
    market_submission_id = save_execution_market_submission(submission)
    submission["market_submission_id"] = market_submission_id

    return submission


def latest_market_submission(asset_id):
    latest = get_latest_execution_market_submission(asset_id)

    if latest is None:
        return {
            "status": "not_found",
            "asset_id": asset_id,
            "message": "No market submission found. Run demo submission first.",
            "submission": None,
        }

    submission = latest["payload"]
    submission["market_submission_id"] = latest["market_submission_id"]

    return {
        "status": "ok",
        "asset_id": asset_id,
        "submission": submission,
    }


def market_submission_history(asset_id, limit=25):
    return {
        "status": "ok",
        "asset_id": asset_id,
        "submissions": list_execution_market_submissions(
            asset_id=asset_id,
            limit=limit,
        ),
    }


def build_submission_lifecycle(adapter_result):
    summary = adapter_result.get("summary", {})

    return [
        {
            "step": "approved_for_demo",
            "label": "Approved for demo",
            "status": "complete",
            "owner": "operator",
        },
        {
            "step": "submitted",
            "label": "Submitted",
            "status": "complete",
            "owner": adapter_result.get("adapter_id"),
        },
        {
            "step": "accepted",
            "label": "Accepted",
            "status": "complete" if summary.get("accepted_bid_count") else "none",
            "owner": adapter_result.get("adapter_id"),
        },
        {
            "step": "awarded",
            "label": "Awarded",
            "status": "complete" if summary.get("awarded_bid_count") else "none",
            "owner": adapter_result.get("adapter_id"),
        },
        {
            "step": "settled",
            "label": "Settled",
            "status": "demo_settled",
            "owner": adapter_result.get("adapter_id"),
        },
    ]
