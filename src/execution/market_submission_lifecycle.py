from datetime import datetime

from src.db.repositories.execution_repository import (
    get_latest_execution_approval,
    get_latest_execution_market_submission,
    get_latest_execution_paper_trade,
    get_latest_execution_proposal,
)
from src.db.repositories.settlement_repository import (
    get_latest_settlement_reconciliation,
)
from src.execution.market_adapter_readiness_gate import (
    build_market_adapter_readiness_gate,
)


LIFECYCLE_STEPS = [
    {
        "step": "drafted",
        "label": "Order package drafted",
        "owner": "optimizer",
    },
    {
        "step": "validated",
        "label": "Market and risk validated",
        "owner": "risk_engine",
    },
    {
        "step": "paper_traded",
        "label": "Paper execution validated",
        "owner": "paper_adapter",
    },
    {
        "step": "approved",
        "label": "Human or policy gate passed",
        "owner": "approval_policy",
    },
    {
        "step": "submitted",
        "label": "Submitted to market adapter",
        "owner": "market_adapter",
    },
    {
        "step": "acknowledged",
        "label": "Market acknowledgement received",
        "owner": "market_adapter",
    },
    {
        "step": "accepted",
        "label": "Orders accepted or filled",
        "owner": "market_adapter",
    },
    {
        "step": "awarded",
        "label": "Award or fill result captured",
        "owner": "market_adapter",
    },
    {
        "step": "settled",
        "label": "Settlement evidence linked",
        "owner": "settlement",
    },
    {
        "step": "reconciled",
        "label": "Variance reconciled into feedback",
        "owner": "settlement",
    },
]


def latest_market_submission_lifecycle(asset_id):
    proposal_record = get_latest_execution_proposal(asset_id)
    approval_record = get_latest_execution_approval(asset_id)
    paper_record = get_latest_execution_paper_trade(asset_id)
    submission_record = get_latest_execution_market_submission(asset_id)
    settlement_record = get_latest_settlement_reconciliation(asset_id)

    proposal = payload_with_id(proposal_record, "execution_proposal_id")
    approval = payload_with_id(approval_record, "approval_id")
    paper_trade = payload_with_id(paper_record, "paper_trade_id")
    submission = payload_with_id(submission_record, "market_submission_id")
    settlement = payload_with_id(
        settlement_record,
        "settlement_reconciliation_id",
    )
    adapter_id = resolve_adapter_id(proposal, paper_trade, submission)
    route_gate = resolve_route_gate(asset_id, adapter_id)
    steps = build_lifecycle_steps(
        proposal=proposal,
        approval=approval,
        paper_trade=paper_trade,
        submission=submission,
        settlement=settlement,
        route_gate=route_gate,
    )
    current_step = resolve_current_step(steps)

    return {
        "status": "ok",
        "asset_id": asset_id,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "adapter_id": adapter_id,
        "market_route_status": route_gate.get("gate_status"),
        "settlement_basis": route_gate.get("settlement_basis")
        or (paper_trade or {}).get("settlement_basis"),
        "lifecycle_status": classify_lifecycle_status(steps),
        "current_step": current_step,
        "next_action": next_lifecycle_action(steps, route_gate),
        "summary": summarize_steps(steps),
        "steps": steps,
        "blockers": lifecycle_blockers(steps),
        "evidence": {
            "execution_proposal_id": (proposal or {}).get("execution_proposal_id"),
            "approval_id": (approval or {}).get("approval_id"),
            "paper_trade_id": (paper_trade or {}).get("paper_trade_id"),
            "market_submission_id": (submission or {}).get("market_submission_id"),
            "settlement_reconciliation_id": (settlement or {}).get(
                "settlement_reconciliation_id"
            ),
            "paper_status": (paper_trade or {}).get("status"),
            "submission_status": (submission or {}).get("status"),
            "settlement_status": (settlement or {}).get("status"),
        },
    }


def build_lifecycle_steps(
    proposal,
    approval,
    paper_trade,
    submission,
    settlement,
    route_gate,
):
    context = {
        "proposal": proposal,
        "approval": approval,
        "paper_trade": paper_trade,
        "submission": submission,
        "settlement": settlement,
        "route_gate": route_gate,
    }

    steps = []
    previous_blocked = False
    for spec in LIFECYCLE_STEPS:
        step = build_step(spec, context)
        if previous_blocked and step["status"] == "waiting":
            step["status"] = "blocked_by_prior_step"
        previous_blocked = previous_blocked or step["status"] in [
            "blocked",
            "review",
            "blocked_by_prior_step",
        ]
        steps.append(step)

    return steps


def build_step(spec, context):
    step = spec["step"]

    if step == "drafted":
        return with_status(
            spec,
            passed=bool(context["proposal"]),
            blocked_message="No order package has been drafted yet.",
            complete_message="Latest order package is available.",
            evidence_id=(context["proposal"] or {}).get("execution_proposal_id"),
        )

    if step == "validated":
        proposal = context["proposal"] or {}
        blockers = proposal.get("blockers") or []
        automation_blockers = proposal.get("automation_blockers") or []
        route_gate = context["route_gate"] or {}
        blocked = bool(blockers) or route_gate.get("gate_status") == "blocked"
        review = bool(automation_blockers)
        return {
            **spec,
            "status": "blocked" if blocked else "review" if review else "complete" if proposal else "waiting",
            "message": (
                "Market route or risk validation is blocked."
                if blocked
                else "Automation blockers require review."
                if review
                else "Risk checks and route gate are usable."
                if proposal
                else "Draft an order package first."
            ),
            "evidence": {
                "blocker_count": len(blockers),
                "automation_blocker_count": len(automation_blockers),
                "market_gate_status": route_gate.get("gate_status"),
                "market_gate_score": route_gate.get("readiness_score"),
            },
        }

    if step == "paper_traded":
        paper = context["paper_trade"] or {}
        validation = paper.get("validation") or {}
        blocked = validation.get("status") == "blocked"
        return {
            **spec,
            "status": "blocked" if blocked else "complete" if paper else "waiting",
            "message": (
                "Paper validation is blocked."
                if blocked
                else "Paper execution evidence is available."
                if paper
                else "Run market-specific paper execution."
            ),
            "evidence": {
                "paper_trade_id": paper.get("paper_trade_id"),
                "paper_status": paper.get("status"),
                "paper_pnl_eur": (paper.get("summary") or {}).get("paper_pnl_eur"),
                "validation_status": validation.get("status"),
                "settlement_basis": paper.get("settlement_basis"),
            },
        }

    if step == "approved":
        approval = context["approval"] or {}
        status = approval.get("status")
        return {
            **spec,
            "status": "complete" if status == "approved" else "review" if status == "requested" else "waiting",
            "message": (
                "Latest proposal is approved."
                if status == "approved"
                else "Approval has been requested."
                if status == "requested"
                else "Request approval or satisfy policy gate."
            ),
            "evidence": {
                "approval_id": approval.get("approval_id"),
                "approval_status": status,
            },
        }

    if step == "submitted":
        submission = context["submission"] or {}
        route_gate = context["route_gate"] or {}
        route_status = route_gate.get("gate_status")
        return {
            **spec,
            "status": "complete" if submission else "blocked" if route_status in ["blocked", "paper_only"] else "waiting",
            "message": (
                "Market submission evidence is available."
                if submission
                else "Route is not ready for supervised/live submission."
                if route_status in ["blocked", "paper_only"]
                else "Submit through the selected market adapter."
            ),
            "evidence": {
                "market_submission_id": submission.get("market_submission_id"),
                "submission_status": submission.get("status"),
                "route_gate_status": route_status,
                "adapter_id": submission.get("adapter_id") or route_gate.get("adapter_id"),
            },
        }

    if step == "acknowledged":
        submission = context["submission"] or {}
        return submission_step(
            spec,
            submission,
            complete_when=submission.get("status") in ["submitted", "accepted", "awarded", "settled"],
            waiting_message="Wait for market adapter acknowledgement.",
            complete_message="Market adapter acknowledged the package.",
        )

    if step == "accepted":
        submission = context["submission"] or {}
        summary = submission.get("summary") or {}
        return submission_step(
            spec,
            submission,
            complete_when=bool(summary.get("accepted_bid_count") or summary.get("filled_order_count")),
            waiting_message="No accepted order evidence yet.",
            complete_message="Accepted or filled order evidence is available.",
            extra_evidence={
                "accepted_bid_count": summary.get("accepted_bid_count"),
                "filled_order_count": summary.get("filled_order_count"),
            },
        )

    if step == "awarded":
        submission = context["submission"] or {}
        paper = context["paper_trade"] or {}
        summary = submission.get("summary") or {}
        paper_summary = paper.get("summary") or {}
        awarded = bool(
            summary.get("awarded_bid_count")
            or paper_summary.get("awarded_capacity_mw")
            or paper_summary.get("filled_order_count")
        )
        return {
            **spec,
            "status": "complete" if awarded else "waiting" if submission or paper else "blocked_by_prior_step",
            "message": (
                "Award or fill result is available."
                if awarded
                else "Await award, fill, or paper result evidence."
            ),
            "evidence": {
                "awarded_bid_count": summary.get("awarded_bid_count"),
                "awarded_capacity_mw": paper_summary.get("awarded_capacity_mw"),
                "filled_order_count": paper_summary.get("filled_order_count"),
            },
        }

    if step == "settled":
        settlement = context["settlement"] or {}
        return {
            **spec,
            "status": "complete" if settlement else "waiting",
            "message": (
                "Settlement reconciliation exists."
                if settlement
                else "Run settlement reconciliation after execution evidence."
            ),
            "evidence": {
                "settlement_reconciliation_id": settlement.get(
                    "settlement_reconciliation_id"
                ),
                "settlement_status": settlement.get("status"),
            },
        }

    settlement = context["settlement"] or {}
    variance_drivers = settlement.get("variance_drivers") or []
    high_severity = [
        row for row in variance_drivers if row.get("severity") in ["high", "critical"]
    ]
    return {
        **spec,
        "status": "blocked" if high_severity else "complete" if settlement else "waiting",
        "message": (
            "High-severity variance must be reviewed before learning loop closure."
            if high_severity
            else "Variance feedback is ready for automation learning."
            if settlement
            else "Reconcile settlement first."
        ),
        "evidence": {
            "variance_driver_count": len(variance_drivers),
            "high_severity_count": len(high_severity),
        },
    }


def with_status(spec, passed, blocked_message, complete_message, evidence_id=None):
    return {
        **spec,
        "status": "complete" if passed else "waiting",
        "message": complete_message if passed else blocked_message,
        "evidence": {"record_id": evidence_id},
    }


def submission_step(
    spec,
    submission,
    complete_when,
    waiting_message,
    complete_message,
    extra_evidence=None,
):
    evidence = {
        "market_submission_id": submission.get("market_submission_id"),
        "submission_status": submission.get("status"),
    }
    evidence.update(extra_evidence or {})

    return {
        **spec,
        "status": "complete" if complete_when else "waiting" if submission else "blocked_by_prior_step",
        "message": complete_message if complete_when else waiting_message,
        "evidence": evidence,
    }


def resolve_adapter_id(proposal, paper_trade, submission):
    proposal_adapter = (((proposal or {}).get("bid_package") or {}).get("adapter_id"))
    paper_adapter = (paper_trade or {}).get("adapter_id")
    submission_adapter = (submission or {}).get("adapter_id")

    for adapter_id in [proposal_adapter, paper_adapter, submission_adapter]:
        if adapter_id and adapter_id not in ["paper", "demo_market"]:
            return adapter_id

    return submission_adapter or paper_adapter or proposal_adapter or "epex_day_ahead"


def resolve_route_gate(asset_id, adapter_id):
    gate = build_market_adapter_readiness_gate(asset_id)
    for route in gate.get("route_gates", []):
        if route.get("adapter_id") == adapter_id:
            return route

    return {
        "adapter_id": adapter_id,
        "gate_status": "blocked",
        "next_action": "No route gate evidence exists for this adapter.",
        "readiness_score": 0,
    }


def resolve_current_step(steps):
    for step in steps:
        if step.get("status") in ["blocked", "review", "waiting", "blocked_by_prior_step"]:
            return step

    return steps[-1] if steps else None


def classify_lifecycle_status(steps):
    statuses = [step.get("status") for step in steps]

    if "blocked" in statuses:
        return "blocked"

    if "review" in statuses:
        return "review"

    if "waiting" in statuses or "blocked_by_prior_step" in statuses:
        return "in_progress"

    return "complete"


def summarize_steps(steps):
    return {
        "total": len(steps),
        "complete": count(steps, "complete"),
        "review": count(steps, "review"),
        "waiting": count(steps, "waiting") + count(steps, "blocked_by_prior_step"),
        "blocked": count(steps, "blocked"),
    }


def next_lifecycle_action(steps, route_gate):
    current = resolve_current_step(steps) or {}

    if current.get("status") == "blocked" and route_gate.get("next_action"):
        return route_gate.get("next_action")

    return current.get("message") or "Monitor lifecycle evidence."


def lifecycle_blockers(steps):
    return [
        {
            "step": step.get("step"),
            "label": step.get("label"),
            "status": step.get("status"),
            "message": step.get("message"),
            "owner": step.get("owner"),
        }
        for step in steps
        if step.get("status") in ["blocked", "review", "blocked_by_prior_step"]
    ]


def payload_with_id(record, id_key):
    if not record:
        return None

    payload = record.get("payload") or {}
    payload[id_key] = record.get(id_key)

    return payload


def count(steps, status):
    return len([step for step in steps if step.get("status") == status])
