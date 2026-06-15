from datetime import datetime

from backend.db.repositories.execution_repository import (
    get_latest_execution_approval,
    get_latest_execution_paper_trade,
    get_latest_execution_proposal,
)
from backend.backtesting.forecast_actual.forecast_confidence import (
    build_forecast_confidence,
)
from backend.execution.approval_workflow import request_execution_approval
from backend.execution.automation_control import automation_control_status
from backend.execution.automation_guardrails import latest_automation_guardrails
from backend.execution.automation_policy import evaluate_automation_policy
from backend.execution.execution_readiness import build_execution_readiness
from backend.execution.market_submission import run_demo_market_submission
from backend.execution.multi_market_allocator import build_multi_market_allocation
from backend.execution.paper_trading import run_execution_paper_trade
from backend.execution.pretrade_proposal import build_execution_proposal
from backend.services.asset_signal_store import load_asset_latest_signal


def trading_orchestrator_status(asset_id):
    context = build_orchestration_context(asset_id)
    automation_control = automation_control_status(asset_id)
    stage = classify_stage(context)
    next_action = build_control_next_action(
        automation_control=automation_control,
        context=context,
        fallback_stage=stage,
    )

    return {
        "status": "ok",
        "asset_id": asset_id,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "orchestrator_status": stage["status"],
        "automation_mode": automation_control.get("automation_mode"),
        "automation_control": automation_control,
        "stage": stage,
        "next_action": next_action,
        "workflow": build_workflow_steps(context=context, stage=stage),
        "blockers": build_blockers(context=context),
        "evidence": build_evidence(context=context),
        "audit": build_audit(context=context, stage=stage, next_action=next_action),
    }


def run_trading_orchestrator(asset_id):
    before = automation_control_status(asset_id)
    next_action = before.get("next_automation_action", {})
    executed_actions = [
        execute_automation_action(
            action=next_action.get("action"),
            asset_id=asset_id,
            automation_control=before,
        )
    ]

    after = trading_orchestrator_status(asset_id)
    after["executed_actions"] = executed_actions
    after["automation_control_before"] = before
    after["message"] = executed_actions[0]["message"] if executed_actions else None

    return after


def execute_automation_action(action, asset_id, automation_control):
    if action == "build_proposal":
        proposal = build_execution_proposal(asset_id)
        return executed_action(
            action=action,
            status="complete",
            message="Automated bid proposal built from the latest ACTION signal.",
            record_id=proposal.get("execution_proposal_id"),
        )

    if action == "run_paper_trade":
        paper_trade = run_execution_paper_trade(asset_id)
        return executed_action(
            action=action,
            status="complete",
            message="Automatic paper trading validation completed.",
            record_id=paper_trade.get("paper_trade_id"),
        )

    if action == "wait_for_supervised_gate":
        human_gate = automation_control.get("human_gate", {})
        if human_gate.get("status") == "required":
            approval = request_execution_approval(
                asset_id=asset_id,
                requested_by="automation_orchestrator",
                reason="Automation control requires the human gate before supervised or live automated trading.",
            )
            return executed_action(
                action="request_human_gate",
                status="complete",
                message="Human gate request created for the latest automated trading proposal.",
                record_id=approval.get("approval_id"),
            )

        return executed_action(
            action=action,
            status="waiting",
            message="Human gate is already pending or not cleared; no automated market action was taken.",
            record_id=human_gate.get("approval_id"),
        )

    if action == "submit_with_limits":
        submission = run_demo_market_submission(asset_id)
        return executed_action(
            action=action,
            status="complete",
            message="Bids submitted through the configured limited automation submission path.",
            record_id=submission.get("market_submission_id"),
        )

    if action in ["clear_blockers", "clear_review_items"]:
        return executed_action(
            action=action,
            status="blocked",
            message=automation_control_blocker_message(automation_control),
        )

    return executed_action(
        action=action or "monitor_and_reoptimize",
        status="no_op",
        message=(
            (automation_control.get("next_automation_action") or {}).get("message")
            or "Automation control did not require a state-changing action."
        ),
    )


def executed_action(action, status, message, record_id=None):
    return {
        "action": action,
        "status": status,
        "message": message,
        "record_id": record_id,
    }


def automation_control_blocker_message(automation_control):
    blockers = automation_control.get("blockers", [])
    if not blockers:
        return "Automation control reported a blocker state without a detailed blocker row."

    first = blockers[0]
    return (
        f"Automation remains blocked by {first.get('source')}: "
        f"{first.get('message')}"
    )


def build_orchestration_context(asset_id):
    signal = load_asset_latest_signal(asset_id)
    proposal_record = get_latest_execution_proposal(asset_id)
    paper_trade_record = get_latest_execution_paper_trade(asset_id)
    approval_record = get_latest_execution_approval(asset_id)
    proposal = payload_with_id(proposal_record, "execution_proposal_id")
    paper_trade = payload_with_id(paper_trade_record, "paper_trade_id")
    approval = payload_with_id(approval_record, "approval_id")
    forecast_confidence = build_forecast_confidence(asset_id)
    policy = evaluate_automation_policy(
        asset_id=asset_id,
        forecast_confidence=forecast_confidence,
        proposal=proposal,
        paper_trade=paper_trade,
        approval=approval,
    )
    allocation = build_multi_market_allocation(asset_id)
    guardrails = latest_automation_guardrails(asset_id)
    readiness = build_execution_readiness(asset_id)

    return {
        "signal": signal,
        "proposal": proposal,
        "paper_trade": paper_trade,
        "approval": approval,
        "policy": policy,
        "allocation": allocation,
        "guardrails": guardrails,
        "readiness": readiness,
    }


def classify_stage(context):
    signal = context["signal"]
    proposal = context["proposal"]
    paper_trade = context["paper_trade"]
    approval = context["approval"]
    policy_decision = context["policy"].get("policy_decision")
    readiness_status = context["readiness"].get("readiness_status")
    allocation_status = context["allocation"].get("allocation_status")
    automation_status = context["guardrails"].get("automation_status")
    signal_value = (
        signal.get("data", {})
        .get("summary", {})
        .get("signal")
    )

    if signal.get("status") != "ok" or signal_value != "ACTION":
        return stage(
            status="waiting_for_signal",
            action="wait_for_signal",
            message="No tradable ACTION signal is available.",
            owner="market_intelligence",
        )

    if not proposal:
        return stage(
            status="proposal_required",
            action="build_proposal",
            message="Build a pre-trade proposal from the latest signal.",
            owner="execution_engine",
        )

    if allocation_status == "blocked":
        return stage(
            status="market_route_blocked",
            action="pause",
            message="Market allocation is blocked by route, readiness, or policy constraints.",
            owner="market_allocator",
        )

    if not paper_trade:
        return stage(
            status="paper_validation_required",
            action="run_paper_trade",
            message="Run paper market validation before approval or supervised execution.",
            owner="paper_adapter",
        )

    if policy_decision == "blocked" or automation_status == "blocked":
        return stage(
            status="policy_blocked",
            action="pause",
            message="Automation policy or guardrails block the workflow.",
            owner="risk_engine",
        )

    if policy_decision in ["paper_only", "paper_ready"]:
        return stage(
            status="paper_mode_ready",
            action="hold_for_review",
            message="Paper validation is ready; policy keeps execution out of live mode.",
            owner="operator",
        )

    if not approval or approval.get("status") != "approved":
        return stage(
            status="approval_required",
            action="request_approval",
            message="Request operator approval for supervised execution.",
            owner="operator",
        )

    if readiness_status == "supervised_ready" and policy_decision == "supervised_live_candidate":
        return stage(
            status="supervised_submission_ready",
            action="prepare_supervised_submission",
            message="All core checks passed; supervised submission can be prepared.",
            owner="trading_operator",
        )

    return stage(
        status="operator_review_required",
        action="hold_for_review",
        message="Workflow needs operator review before the next automated step.",
        owner="operator",
    )


def build_next_action(stage, context):
    primary_market = context["allocation"].get("primary_market") or {}

    return {
        "action": stage["action"],
        "label": humanize_action(stage["action"]),
        "message": stage["message"],
        "owner": stage["owner"],
        "target_market": primary_market.get("market_name"),
        "target_adapter_id": primary_market.get("adapter_id"),
    }


def build_control_next_action(automation_control, context, fallback_stage):
    control_action = automation_control.get("next_automation_action") or {}
    primary_market = automation_control.get("primary_market") or {}

    if not control_action:
        return build_next_action(stage=fallback_stage, context=context)

    return {
        "action": control_action.get("action"),
        "label": control_action.get("label") or humanize_action(
            control_action.get("action")
        ),
        "message": control_action.get("message"),
        "owner": control_action.get("owner"),
        "target_market": primary_market.get("market_name"),
        "target_adapter_id": primary_market.get("adapter_id"),
    }


def build_workflow_steps(context, stage):
    signal_value = (
        context["signal"].get("data", {})
        .get("summary", {})
        .get("signal")
    )
    proposal = context["proposal"]
    paper_trade = context["paper_trade"]
    approval = context["approval"]

    return [
        workflow_step(
            "signal",
            "Market signal",
            "passed" if signal_value == "ACTION" else "waiting",
            signal_value or "No action signal",
        ),
        workflow_step(
            "proposal",
            "Bid proposal",
            "passed" if proposal else "next" if stage["action"] == "build_proposal" else "waiting",
            proposal.get("status") if proposal else "No proposal",
        ),
        workflow_step(
            "policy",
            "Automation policy",
            status_from_decision(context["policy"].get("policy_decision")),
            context["policy"].get("policy_decision"),
        ),
        workflow_step(
            "market_allocation",
            "Market allocation",
            status_from_decision(context["allocation"].get("allocation_status")),
            context["allocation"].get("allocation_status"),
        ),
        workflow_step(
            "paper_trade",
            "Paper market",
            "passed" if paper_trade else "next" if stage["action"] == "run_paper_trade" else "waiting",
            (paper_trade or {}).get("status") or "No paper trade",
        ),
        workflow_step(
            "approval",
            "Operator approval",
            "passed" if (approval or {}).get("status") == "approved" else "next" if stage["action"] == "request_approval" else "review",
            (approval or {}).get("status") or "No approval",
        ),
        workflow_step(
            "supervised_submission",
            "Supervised submission",
            "next" if stage["action"] == "prepare_supervised_submission" else "waiting",
            stage["message"],
        ),
    ]


def build_blockers(context):
    blockers = []

    for source_key, row_key in [
        ("policy", "checks"),
        ("readiness", "checks"),
        ("guardrails", "guardrails"),
    ]:
        for item in context[source_key].get(row_key, []):
            if item.get("status") in ["blocked", "review"]:
                blockers.append(
                    {
                        "source": source_key,
                        "status": item.get("status"),
                        "blocker": item.get("message"),
                    }
                )

    for market in context["allocation"].get("excluded_markets", []):
        blockers.append(
            {
                "source": f"market:{market.get('adapter_id')}",
                "status": "blocked",
                "blocker": "; ".join(market.get("blocking_reasons", []))
                or market.get("operator_next_action"),
            }
        )

    return dedupe_blockers(blockers)


def build_evidence(context):
    proposal = context["proposal"] or {}
    paper_trade = context["paper_trade"] or {}
    approval = context["approval"] or {}
    primary_market = context["allocation"].get("primary_market") or {}

    return {
        "signal_status": context["signal"].get("status"),
        "signal": (
            context["signal"].get("data", {})
            .get("summary", {})
            .get("signal")
        ),
        "execution_proposal_id": proposal.get("execution_proposal_id"),
        "paper_trade_id": paper_trade.get("paper_trade_id"),
        "approval_id": approval.get("approval_id"),
        "approval_status": approval.get("status"),
        "policy_decision": context["policy"].get("policy_decision"),
        "readiness_status": context["readiness"].get("readiness_status"),
        "automation_status": context["guardrails"].get("automation_status"),
        "allocation_status": context["allocation"].get("allocation_status"),
        "primary_market": primary_market.get("market_name"),
        "primary_adapter_id": primary_market.get("adapter_id"),
    }


def build_audit(context, stage, next_action):
    evidence = build_evidence(context)

    return [
        {
            "event": "context_loaded",
            "actor": "trading_orchestrator",
            "status": "complete",
            "note": "Loaded signal, proposal, policy, market allocation, guardrails, readiness, paper trade, and approval state.",
        },
        {
            "event": "stage_classified",
            "actor": "trading_orchestrator",
            "status": stage["status"],
            "note": stage["message"],
        },
        {
            "event": "next_action_selected",
            "actor": next_action.get("owner"),
            "status": next_action.get("action"),
            "note": f"{next_action.get('label')} for {evidence.get('primary_market') or 'selected route'}.",
        },
    ]


def payload_with_id(record, id_key):
    if not record:
        return None

    payload = record.get("payload") or {}
    payload[id_key] = record.get(id_key)

    return payload


def stage(status, action, message, owner):
    return {
        "status": status,
        "action": action,
        "message": message,
        "owner": owner,
    }


def workflow_step(step_id, label, status, message):
    return {
        "step": step_id,
        "label": label,
        "status": status,
        "message": message,
    }


def humanize_action(action):
    return str(action or "").replace("_", " ").title()


def status_from_decision(value):
    if value in ["recommended", "supervised_live_candidate", "paper_ready"]:
        return "passed"

    if value in ["human_approval_required", "operator_review_required", "watchlist", "paper_only"]:
        return "review"

    if value == "blocked":
        return "blocked"

    return "waiting"


def dedupe_blockers(rows):
    seen = set()
    result = []

    for row in rows:
        key = (row.get("source"), row.get("status"), row.get("blocker"))
        if not row.get("blocker") or key in seen:
            continue

        seen.add(key)
        result.append(row)

    return result



