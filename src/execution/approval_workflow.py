from datetime import datetime

from src.db.repositories.execution_repository import (
    get_latest_execution_approval,
    get_latest_execution_proposal,
    list_execution_approvals,
    save_execution_approval,
    update_execution_approval,
)


def request_execution_approval(
    asset_id,
    requested_by="operator",
    reason="Approval requested for latest execution proposal.",
):
    proposal_record = get_latest_execution_proposal(asset_id)

    if proposal_record is None:
        raise FileNotFoundError(
            f"No execution proposal found for asset_id={asset_id}."
        )

    approval = {
        "asset_id": asset_id,
        "execution_proposal_id": proposal_record["execution_proposal_id"],
        "requested_at": datetime.now().isoformat(timespec="seconds"),
        "decided_at": None,
        "status": "requested",
        "requested_by": requested_by,
        "decided_by": None,
        "reason": reason,
        "audit": [
            {
                "event": "approval_requested",
                "actor": requested_by,
                "status": "complete",
                "note": reason,
            }
        ],
    }
    approval_id = save_execution_approval(approval)
    approval["approval_id"] = approval_id

    return approval


def approve_execution_proposal(
    asset_id,
    decided_by="operator",
    reason="Approved for supervised demo submission.",
):
    return decide_latest_approval(
        asset_id=asset_id,
        decided_by=decided_by,
        reason=reason,
        status="approved",
    )


def reject_execution_proposal(
    asset_id,
    decided_by="operator",
    reason="Rejected by operator.",
):
    return decide_latest_approval(
        asset_id=asset_id,
        decided_by=decided_by,
        reason=reason,
        status="rejected",
    )


def latest_execution_approval(asset_id):
    latest = get_latest_execution_approval(asset_id)

    if latest is None:
        return {
            "status": "not_found",
            "asset_id": asset_id,
            "message": "No execution approval found. Request approval first.",
            "approval": None,
        }

    approval = latest["payload"]
    approval["approval_id"] = latest["approval_id"]

    return {
        "status": "ok",
        "asset_id": asset_id,
        "approval": approval,
    }


def execution_approval_history(asset_id, limit=25):
    return {
        "status": "ok",
        "asset_id": asset_id,
        "approvals": list_execution_approvals(asset_id=asset_id, limit=limit),
    }


def require_latest_approval(asset_id, execution_proposal_id=None):
    latest = get_latest_execution_approval(asset_id)

    if latest is None:
        raise PermissionError("No execution approval exists for this asset.")

    approval = latest["payload"]
    approval["approval_id"] = latest["approval_id"]

    if execution_proposal_id is not None and approval.get("execution_proposal_id") != execution_proposal_id:
        raise PermissionError("Latest approval does not match the latest execution proposal.")

    if approval.get("status") != "approved":
        raise PermissionError(
            f"Execution proposal is not approved. Current approval status: {approval.get('status')}."
        )

    return approval


def decide_latest_approval(asset_id, decided_by, reason, status):
    proposal_record = get_latest_execution_proposal(asset_id)
    if proposal_record is None:
        raise FileNotFoundError(
            f"No execution proposal found for asset_id={asset_id}."
        )

    latest = get_latest_execution_approval(asset_id)
    latest_payload = (latest or {}).get("payload") or {}
    proposal_id = proposal_record["execution_proposal_id"]

    if latest is None or latest_payload.get("execution_proposal_id") != proposal_id:
        approval = request_execution_approval(
            asset_id=asset_id,
            requested_by=decided_by,
            reason="Approval request created automatically before decision.",
        )
        latest = {
            "approval_id": approval["approval_id"],
            "payload": approval,
        }

    approval = latest["payload"]
    approval["approval_id"] = latest["approval_id"]
    approval["status"] = status
    approval["decided_at"] = datetime.now().isoformat(timespec="seconds")
    approval["decided_by"] = decided_by
    approval["reason"] = reason
    approval.setdefault("audit", []).append(
        {
            "event": f"approval_{status}",
            "actor": decided_by,
            "status": "complete",
            "note": reason,
        }
    )
    update_execution_approval(latest["approval_id"], approval)

    return approval
