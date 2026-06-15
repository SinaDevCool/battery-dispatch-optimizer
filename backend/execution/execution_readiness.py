from backend.db.repositories.execution_repository import (
    get_latest_execution_approval,
    get_latest_execution_market_submission,
    get_latest_execution_paper_trade,
    get_latest_execution_proposal,
)
from backend.db.repositories.settlement_repository import (
    get_latest_settlement_reconciliation,
)
from backend.db.repositories.telemetry_repository import get_latest_telemetry_snapshot
from backend.execution.automation_guardrails import latest_automation_guardrails
from backend.execution.market_adapters.registry import get_asset_market_adapter_status


def build_execution_readiness(asset_id):
    proposal_record = get_latest_execution_proposal(asset_id)
    approval_record = get_latest_execution_approval(asset_id)
    paper_trade_record = get_latest_execution_paper_trade(asset_id)
    submission_record = get_latest_execution_market_submission(asset_id)
    telemetry_record = get_latest_telemetry_snapshot(asset_id)
    settlement_record = get_latest_settlement_reconciliation(asset_id)
    guardrails = latest_automation_guardrails(asset_id)
    adapter_status = get_asset_market_adapter_status(asset_id)

    proposal = payload_with_id(
        proposal_record,
        id_key="execution_proposal_id",
    )
    approval = payload_with_id(approval_record, id_key="approval_id")
    paper_trade = payload_with_id(paper_trade_record, id_key="paper_trade_id")
    submission = payload_with_id(
        submission_record,
        id_key="market_submission_id",
    )
    telemetry = payload_with_id(telemetry_record, id_key="telemetry_id")
    settlement = payload_with_id(
        settlement_record,
        id_key="settlement_reconciliation_id",
    )

    checks = [
        proposal_check(proposal),
        approval_check(proposal, approval),
        guardrails_check(guardrails),
        telemetry_check(telemetry),
        paper_trade_check(proposal, paper_trade),
        market_adapter_check(proposal, submission, adapter_status),
        settlement_check(settlement),
    ]
    score = readiness_score(checks)
    readiness_status = classify_readiness(checks, score)

    return {
        "status": "ok",
        "asset_id": asset_id,
        "readiness_status": readiness_status,
        "readiness_score": score,
        "market_adapter_status": adapter_status.get("market_adapter_status"),
        "market_adapters": adapter_status.get("adapters", []),
        "automation_status": guardrails.get("automation_status"),
        "checks": checks,
        "summary": summarize_checks(checks),
        "evidence": {
            "execution_proposal_id": (proposal_record or {}).get(
                "execution_proposal_id"
            ),
            "approval_id": (approval_record or {}).get("approval_id"),
            "paper_trade_id": (paper_trade_record or {}).get("paper_trade_id"),
            "market_submission_id": (submission_record or {}).get(
                "market_submission_id"
            ),
            "telemetry_id": (telemetry_record or {}).get("telemetry_id"),
            "settlement_reconciliation_id": (settlement_record or {}).get(
                "settlement_reconciliation_id"
            ),
        },
        "recommended_actions": recommended_actions(checks, readiness_status),
    }


def payload_with_id(record, id_key):
    if not record:
        return None

    payload = record.get("payload") or {}
    payload[id_key] = record.get(id_key)

    return payload


def proposal_check(proposal):
    if not proposal:
        return readiness_check(
            check="execution_proposal",
            label="Execution proposal",
            status="blocked",
            message="No execution proposal exists.",
            evidence={},
        )

    bids = proposal.get("bids") or proposal.get("orders") or []

    return readiness_check(
        check="execution_proposal",
        label="Execution proposal",
        status="passed" if bids else "blocked",
        message=(
            "Latest execution proposal has tradable bid rows."
            if bids
            else "Latest execution proposal has no bid rows."
        ),
        evidence={
            "execution_proposal_id": proposal.get("execution_proposal_id"),
            "proposal_status": proposal.get("status"),
            "bid_count": len(bids),
        },
    )


def approval_check(proposal, approval):
    proposal_id = (proposal or {}).get("execution_proposal_id")

    if not approval:
        return readiness_check(
            check="operator_approval",
            label="Operator approval",
            status="review",
            message="No approval decision exists for the latest proposal.",
            evidence={"execution_proposal_id": proposal_id},
        )

    if proposal_id and approval.get("execution_proposal_id") != proposal_id:
        return readiness_check(
            check="operator_approval",
            label="Operator approval",
            status="blocked",
            message="Latest approval does not match the latest proposal.",
            evidence={
                "approval_id": approval.get("approval_id"),
                "approval_status": approval.get("status"),
                "approval_proposal_id": approval.get("execution_proposal_id"),
                "execution_proposal_id": proposal_id,
            },
        )

    status = approval.get("status")
    if status == "approved":
        readiness_status = "passed"
        message = "Latest proposal is approved for supervised submission."
    elif status == "requested":
        readiness_status = "review"
        message = "Approval has been requested and is awaiting decision."
    else:
        readiness_status = "blocked"
        message = f"Approval status is {status or 'missing'}."

    return readiness_check(
        check="operator_approval",
        label="Operator approval",
        status=readiness_status,
        message=message,
        evidence={
            "approval_id": approval.get("approval_id"),
            "approval_status": status,
            "decided_by": approval.get("decided_by"),
            "decided_at": approval.get("decided_at"),
        },
    )


def guardrails_check(guardrails):
    summary = guardrails.get("summary") or {}
    automation_status = guardrails.get("automation_status")

    if guardrails.get("status") == "proposal_missing":
        status = "blocked"
        message = guardrails.get("message")
    elif summary.get("blocked", 0):
        status = "blocked"
        message = "One or more automation guardrails are blocked."
    elif summary.get("review", 0):
        status = "review"
        message = "Automation guardrails require operator review."
    else:
        status = "passed"
        message = "Automation guardrails passed."

    return readiness_check(
        check="automation_guardrails",
        label="Automation guardrails",
        status=status,
        message=message,
        evidence={
            "automation_status": automation_status,
            "passed": summary.get("passed", 0),
            "review": summary.get("review", 0),
            "blocked": summary.get("blocked", 0),
        },
    )


def telemetry_check(telemetry):
    if not telemetry:
        return readiness_check(
            check="asset_telemetry",
            label="Asset telemetry",
            status="blocked",
            message="No telemetry snapshot is available.",
            evidence={},
        )

    availability = telemetry.get("availability_status")
    maintenance = bool(telemetry.get("maintenance_active"))
    curtailment = bool(telemetry.get("curtailment_active"))

    if availability == "available" and not maintenance and not curtailment:
        status = "passed"
        message = "Telemetry shows the asset is available."
    else:
        status = "blocked"
        message = "Telemetry does not show the asset as available."

    return readiness_check(
        check="asset_telemetry",
        label="Asset telemetry",
        status=status,
        message=message,
        evidence={
            "telemetry_id": telemetry.get("telemetry_id"),
            "provider": telemetry.get("provider"),
            "availability_status": availability,
            "soc_percent": telemetry.get("soc_percent"),
            "maintenance_active": maintenance,
            "curtailment_active": curtailment,
        },
    )


def paper_trade_check(proposal, paper_trade):
    proposal_id = (proposal or {}).get("execution_proposal_id")

    if not paper_trade:
        return readiness_check(
            check="paper_trade",
            label="Paper trade",
            status="blocked",
            message="No paper trade exists for the latest proposal.",
            evidence={"execution_proposal_id": proposal_id},
        )

    status = (
        "passed"
        if not proposal_id
        or paper_trade.get("execution_proposal_id") == proposal_id
        else "review"
    )

    return readiness_check(
        check="paper_trade",
        label="Paper trade",
        status=status,
        message=(
            "Paper trade evidence exists for the latest proposal."
            if status == "passed"
            else "Paper trade evidence does not match the latest proposal."
        ),
        evidence={
            "paper_trade_id": paper_trade.get("paper_trade_id"),
            "execution_proposal_id": paper_trade.get("execution_proposal_id"),
            "paper_pnl_eur": paper_trade.get("summary", {}).get(
                "paper_pnl_eur"
            ),
        },
    )


def market_adapter_check(proposal, submission, adapter_status):
    connected_count = adapter_status.get("connected_adapter_count", 0)

    if proposal and proposal.get("market_submission_enabled"):
        status = "passed"
        message = "Market submission is enabled for this proposal."
    elif submission:
        status = "review"
        message = "Demo market adapter has submission evidence."
    elif connected_count:
        status = "review"
        message = "Only paper/demo market adapters are currently connected."
    else:
        status = "blocked"
        message = "No live market adapter is connected."

    return readiness_check(
        check="market_adapter",
        label="Market adapter",
        status=status,
        message=message,
        evidence={
            "adapter_id": (submission or {}).get("adapter_id") or "demo_market",
            "live_submission": (submission or {}).get("live_submission", False),
            "market_submission_id": (submission or {}).get(
                "market_submission_id"
            ),
            "market_adapter_status": adapter_status.get("market_adapter_status"),
            "connected_adapter_count": connected_count,
            "planned_adapter_count": adapter_status.get("planned_adapter_count"),
            "next_connection_action": adapter_status.get(
                "next_connection_action"
            ),
        },
    )


def settlement_check(settlement):
    if not settlement:
        return readiness_check(
            check="settlement_reconciliation",
            label="Settlement reconciliation",
            status="review",
            message="No settlement reconciliation exists yet.",
            evidence={},
        )

    return readiness_check(
        check="settlement_reconciliation",
        label="Settlement reconciliation",
        status="passed",
        message="Settlement reconciliation evidence exists.",
        evidence={
            "settlement_reconciliation_id": settlement.get(
                "settlement_reconciliation_id"
            ),
            "settlement_status": settlement.get("status"),
            "primary_variance_driver": settlement.get(
                "primary_variance_driver"
            ),
        },
    )


def readiness_check(check, label, status, message, evidence):
    return {
        "check": check,
        "label": label,
        "status": status,
        "message": message,
        "evidence": evidence,
    }


def readiness_score(checks):
    points = {
        "passed": 100,
        "review": 55,
        "blocked": 0,
    }

    if not checks:
        return 0

    return round(
        sum(points.get(check["status"], 0) for check in checks) / len(checks),
        1,
    )


def classify_readiness(checks, score):
    statuses = {check["status"] for check in checks}

    if "blocked" in statuses:
        return "blocked"

    if "review" in statuses:
        return "operator_review_required"

    if score >= 95:
        return "supervised_ready"

    return "operator_review_required"


def summarize_checks(checks):
    return {
        "passed": count(checks, "passed"),
        "review": count(checks, "review"),
        "blocked": count(checks, "blocked"),
        "total": len(checks),
    }


def recommended_actions(checks, readiness_status):
    actions = []

    for check in checks:
        if check["status"] == "blocked":
            actions.append(f"Clear blocker: {check['message']}")
        elif check["status"] == "review":
            actions.append(f"Review: {check['message']}")

    if readiness_status == "supervised_ready":
        actions.append("Keep supervised execution mode until live adapter validation is complete.")
    elif readiness_status == "blocked":
        actions.append("Keep execution in advisory or paper mode.")

    return dedupe(actions)


def count(checks, status):
    return len([check for check in checks if check["status"] == status])


def dedupe(items):
    seen = set()
    result = []

    for item in items:
        if item in seen:
            continue

        seen.add(item)
        result.append(item)

    return result



