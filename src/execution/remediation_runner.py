from datetime import datetime

from src.db.repositories.execution_repository import save_automation_event
from src.execution.approval_workflow import request_execution_approval
from src.execution.automation_control import automation_control_status
from src.execution.execution_recovery_engine import build_execution_recovery_plan
from src.execution.market_submission import run_demo_market_submission
from src.execution.paper_trading import run_execution_paper_trade
from src.execution.pretrade_proposal import build_execution_proposal
from src.execution.strategy_intent import build_strategy_intent
from src.settlement.settlement_reconciliation import run_settlement_reconciliation
from src.telemetry.asset_telemetry import save_demo_asset_telemetry


def run_next_remediation(asset_id):
    before_control = automation_control_status(asset_id)
    before_strategy = build_strategy_intent(asset_id)
    recovery_plan = build_execution_recovery_plan(asset_id)
    remediation_item = next_auto_remediation(
        before_control,
        recovery_plan=recovery_plan,
    )

    if remediation_item is None:
        after_control = automation_control_status(asset_id)
        after_strategy = build_strategy_intent(asset_id)
        result = remediation_result(
            action_result={
                "status": "noop",
                "action": "noop",
                "message": "No auto-resolvable remediation item is available.",
            },
            after_control=after_control,
            after_strategy=after_strategy,
            asset_id=asset_id,
            before_control=before_control,
            before_strategy=before_strategy,
            remediation_item=None,
            recovery_plan=recovery_plan,
            status="blocked" if after_control.get("blockers") else "ok",
        )
        persist_automation_event(result)
        return result

    try:
        action_result = execute_remediation_item(
            asset_id=asset_id,
            before_control=before_control,
            remediation_item=remediation_item,
        )
    except Exception as error:
        action_result = action_result_from_error(
            remediation_item=remediation_item,
            error=error,
        )
    after_control = automation_control_status(asset_id)
    after_strategy = build_strategy_intent(asset_id)

    result = remediation_result(
        action_result=action_result,
        after_control=after_control,
        after_strategy=after_strategy,
        asset_id=asset_id,
        before_control=before_control,
        before_strategy=before_strategy,
        remediation_item=remediation_item,
        recovery_plan=recovery_plan,
        status=classify_runner_status(action_result, after_control),
    )
    persist_automation_event(result)
    return result


def next_auto_remediation(control, recovery_plan=None):
    recovery_action = (recovery_plan or {}).get("primary_action") or {}
    if recovery_action.get("auto_resolvable") and recovery_action.get(
        "resolution_endpoint"
    ):
        return {
            "auto_resolvable": True,
            "blocker_id": recovery_action.get("action"),
            "category": recovery_action.get("category"),
            "evidence_link": "/execution/audit",
            "message": recovery_action.get("message"),
            "required_action": recovery_action.get("label"),
            "resolution_endpoint": recovery_action.get("resolution_endpoint"),
            "severity": recovery_action.get("severity", "medium"),
            "source": "execution_recovery_engine",
        }

    for item in control.get("remediation_queue", []):
        if item.get("auto_resolvable") and item.get("resolution_endpoint"):
            return item

    return None


def execute_remediation_item(asset_id, before_control, remediation_item):
    endpoint = remediation_item.get("resolution_endpoint")

    if endpoint == f"/assets/{asset_id}/execution/proposal/build":
        proposal = build_execution_proposal(asset_id)
        return action_result(
            status="ok",
            action="build_proposal",
            message="Built the next automated execution proposal.",
            payload_key="proposal",
            payload=proposal,
        )

    if endpoint == f"/assets/{asset_id}/execution/paper-trade/run":
        paper_trade = run_execution_paper_trade(asset_id)
        return action_result(
            status="ok",
            action="run_paper_trade",
            message="Ran paper trading validation for the latest proposal.",
            payload_key="paper_trade",
            payload=paper_trade,
        )

    if endpoint == f"/assets/{asset_id}/execution/approval/request":
        approval = request_execution_approval(asset_id)
        return action_result(
            status="ok",
            action="request_human_gate",
            message="Requested the supervised automation human gate.",
            payload_key="approval",
            payload=approval,
        )

    if endpoint == f"/assets/{asset_id}/telemetry/demo":
        telemetry = save_demo_asset_telemetry(asset_id)
        return action_result(
            status="ok",
            action="refresh_demo_telemetry",
            message="Seeded fresh demo telemetry for automation validation.",
            payload_key="telemetry",
            payload=telemetry,
        )

    if endpoint == f"/assets/{asset_id}/settlement/reconcile":
        settlement = run_settlement_reconciliation(asset_id)
        return action_result(
            status="ok",
            action="run_settlement_reconciliation",
            message="Ran settlement reconciliation for automation feedback.",
            payload_key="settlement",
            payload=settlement,
        )

    if endpoint == f"/assets/{asset_id}/execution/demo-submit":
        human_gate = before_control.get("human_gate", {})
        if human_gate.get("status") not in ["passed", "not_required"]:
            return action_result(
                status="blocked",
                action="demo_submit",
                message="Submission remediation is blocked until the human gate clears.",
            )

        submission = run_demo_market_submission(asset_id)
        return action_result(
            status="ok",
            action="demo_submit",
            message="Ran configured demo market submission path.",
            payload_key="submission",
            payload=submission,
        )

    return action_result(
        status="unsupported",
        action="unsupported_remediation",
        message=f"No backend runner is registered for {endpoint}.",
    )


def remediation_result(
    action_result,
    after_control,
    after_strategy,
    asset_id,
    before_control,
    before_strategy,
    remediation_item,
    recovery_plan,
    status,
):
    return {
        "status": status,
        "asset_id": asset_id,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "event_type": "remediation_run_next",
        "message": action_result.get("message"),
        "remediation_item": remediation_item,
        "recovery_plan": recovery_plan,
        "action_result": action_result,
        "before": state_snapshot(
            control=before_control,
            strategy=before_strategy,
        ),
        "after": state_snapshot(
            control=after_control,
            strategy=after_strategy,
        ),
        "remaining_blockers": after_control.get("blockers", []),
        "remaining_remediation_queue": after_control.get("remediation_queue", []),
        "can_continue_automation": bool(
            after_control.get("next_automation_action", {}).get("action")
            not in ["clear_blockers", "clear_review_items"]
            and after_control.get("automation_mode") != "live_auto_blocked"
        ),
    }


def persist_automation_event(result):
    event = {
        "asset_id": result["asset_id"],
        "created_at": result["generated_at"],
        "event_type": result["event_type"],
        "action": result.get("action_result", {}).get("action"),
        "status": result["status"],
        "before": result["before"],
        "after": result["after"],
        "action_result": result["action_result"],
        "remediation_item": result.get("remediation_item"),
        "recovery_plan": result.get("recovery_plan"),
        "remaining_blocker_count": len(result.get("remaining_blockers", [])),
        "remaining_remediation_count": len(
            result.get("remaining_remediation_queue", [])
        ),
    }

    try:
        event_id = save_automation_event(event)
    except Exception as error:
        result["audit_event"] = {
            "persisted": False,
            "error_type": type(error).__name__,
            "message": str(error),
        }
        return

    result["audit_event"] = {
        "automation_event_id": event_id,
        "persisted": True,
    }


def state_snapshot(control, strategy):
    return {
        "automation_mode": control.get("automation_mode"),
        "automation_mode_rank": control.get("automation_mode_rank"),
        "blocker_count": len(control.get("blockers", [])),
        "next_automation_action": control.get("next_automation_action"),
        "strategy_mode": strategy.get("strategy_mode"),
        "dispatch_bias": strategy.get("dispatch_bias"),
        "strategy_confidence": strategy.get("confidence"),
        "recommended_strategy_action": strategy.get("recommended_next_action"),
    }


def action_result(status, action, message, payload_key=None, payload=None):
    result = {
        "status": status,
        "action": action,
        "message": message,
    }

    if payload_key:
        result[payload_key] = payload

    return result


def action_result_from_error(remediation_item, error):
    endpoint = remediation_item.get("resolution_endpoint")
    return {
        "status": "error",
        "action": remediation_item.get("blocker_id") or "remediation_error",
        "message": f"Remediation action failed for {endpoint}: {error}",
        "error_type": type(error).__name__,
    }


def classify_runner_status(action_result, after_control):
    if action_result.get("status") not in ["ok", "noop"]:
        return action_result.get("status")

    if after_control.get("blockers"):
        return "partial"

    return "ok"
