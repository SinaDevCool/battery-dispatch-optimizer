from datetime import datetime

from backend.execution.automation_control import automation_control_status
from backend.execution.market_submission_lifecycle import latest_market_submission_lifecycle


RECOVERY_ACTIONS = {
    "drafted": {
        "action": "build_proposal",
        "category": "proposal",
        "endpoint": "/assets/{asset_id}/execution/proposal/build",
        "label": "Build proposal",
        "safe_to_auto_run": True,
    },
    "validated": {
        "action": "clear_validation_blocker",
        "category": "route_gate",
        "endpoint": None,
        "label": "Clear route or risk gate",
        "safe_to_auto_run": False,
    },
    "paper_traded": {
        "action": "run_paper_trade",
        "category": "paper_execution",
        "endpoint": "/assets/{asset_id}/execution/paper-trade/run",
        "label": "Run paper trade",
        "safe_to_auto_run": True,
    },
    "approved": {
        "action": "request_approval",
        "category": "human_gate",
        "endpoint": "/assets/{asset_id}/execution/approval/request",
        "label": "Request approval",
        "safe_to_auto_run": True,
    },
    "submitted": {
        "action": "submit_demo_or_poll_adapter",
        "category": "submission",
        "endpoint": "/assets/{asset_id}/execution/demo-submit",
        "label": "Submit or poll adapter",
        "safe_to_auto_run": True,
    },
    "acknowledged": {
        "action": "poll_market_acknowledgement",
        "category": "market_adapter",
        "endpoint": None,
        "label": "Poll acknowledgement",
        "safe_to_auto_run": False,
    },
    "accepted": {
        "action": "ingest_market_results",
        "category": "market_results",
        "endpoint": None,
        "label": "Ingest results",
        "safe_to_auto_run": False,
    },
    "awarded": {
        "action": "ingest_awards",
        "category": "market_results",
        "endpoint": None,
        "label": "Ingest awards",
        "safe_to_auto_run": False,
    },
    "settled": {
        "action": "run_settlement_reconciliation",
        "category": "settlement",
        "endpoint": "/assets/{asset_id}/settlement/reconcile",
        "label": "Reconcile settlement",
        "safe_to_auto_run": True,
    },
    "reconciled": {
        "action": "review_variance_feedback",
        "category": "learning_loop",
        "endpoint": None,
        "label": "Review feedback",
        "safe_to_auto_run": False,
    },
}


def build_execution_recovery_plan(asset_id):
    lifecycle = latest_market_submission_lifecycle(asset_id)
    control = automation_control_status(asset_id)
    current_step = lifecycle.get("current_step") or {}
    root_cause = classify_root_cause(current_step=current_step, lifecycle=lifecycle)
    primary_action = build_primary_action(
        asset_id=asset_id,
        current_step=current_step,
        lifecycle=lifecycle,
        control=control,
    )
    queue = build_recovery_queue(
        asset_id=asset_id,
        lifecycle=lifecycle,
        control=control,
        primary_action=primary_action,
    )

    return {
        "status": "ok",
        "asset_id": asset_id,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "recovery_status": classify_recovery_status(primary_action, lifecycle),
        "stuck_step": current_step,
        "root_cause": root_cause,
        "primary_action": primary_action,
        "recovery_queue": queue,
        "summary": {
            "auto_resolvable_count": len(
                [item for item in queue if item.get("auto_resolvable")]
            ),
            "manual_review_count": len(
                [item for item in queue if not item.get("auto_resolvable")]
            ),
            "lifecycle_status": lifecycle.get("lifecycle_status"),
            "market_route_status": lifecycle.get("market_route_status"),
        },
        "evidence": {
            "lifecycle_status": lifecycle.get("lifecycle_status"),
            "current_step": current_step.get("step"),
            "adapter_id": lifecycle.get("adapter_id"),
            "market_route_status": lifecycle.get("market_route_status"),
            "next_lifecycle_action": lifecycle.get("next_action"),
            "automation_mode": control.get("automation_mode"),
            "human_gate_status": (control.get("human_gate") or {}).get("status"),
        },
    }


def build_primary_action(asset_id, current_step, lifecycle, control):
    step = current_step.get("step") or "drafted"
    template = RECOVERY_ACTIONS.get(step, RECOVERY_ACTIONS["drafted"])
    endpoint = format_endpoint(template.get("endpoint"), asset_id)
    requires_human = requires_human_gate(
        current_step=current_step,
        lifecycle=lifecycle,
        control=control,
        template=template,
    )
    safe_to_auto_run = bool(template["safe_to_auto_run"] and not requires_human)

    if step == "validated" and current_step.get("status") == "review":
        template = RECOVERY_ACTIONS["paper_traded"]
        endpoint = format_endpoint(template.get("endpoint"), asset_id)
        safe_to_auto_run = True
        requires_human = False

    if step == "submitted" and lifecycle.get("market_route_status") in ["blocked", "paper_only"]:
        safe_to_auto_run = False
        requires_human = True

    return {
        "action": template["action"],
        "auto_resolvable": safe_to_auto_run and bool(endpoint),
        "category": template["category"],
        "label": template["label"],
        "requires_human_approval": requires_human,
        "resolution_endpoint": endpoint,
        "safe_to_auto_run": safe_to_auto_run,
        "severity": severity_for_step(current_step),
        "source": "submission_lifecycle",
        "message": recovery_message(
            current_step=current_step,
            template=template,
            lifecycle=lifecycle,
        ),
    }


def build_recovery_queue(asset_id, lifecycle, control, primary_action):
    queue = [primary_action]
    current_step_name = (lifecycle.get("current_step") or {}).get("step")

    for blocker in lifecycle.get("blockers", []):
        if blocker.get("step") == current_step_name:
            continue

        action = build_primary_action(
            asset_id=asset_id,
            current_step=blocker,
            lifecycle=lifecycle,
            control=control,
        )
        queue.append(action)

    for item in control.get("remediation_queue", []):
        queue.append(
            {
                "action": item.get("blocker_id") or item.get("category"),
                "auto_resolvable": bool(
                    item.get("auto_resolvable") and item.get("resolution_endpoint")
                ),
                "category": item.get("category"),
                "label": item.get("required_action") or item.get("message"),
                "message": item.get("required_action") or item.get("message"),
                "requires_human_approval": item.get("category") == "human_gate",
                "resolution_endpoint": item.get("resolution_endpoint"),
                "safe_to_auto_run": bool(item.get("auto_resolvable")),
                "severity": item.get("severity", "medium"),
                "source": item.get("source") or "automation_control",
            }
        )

    return dedupe_queue(queue)[:8]


def classify_root_cause(current_step, lifecycle):
    step = current_step.get("step")
    status = current_step.get("status")

    if lifecycle.get("market_route_status") in ["blocked", "paper_only"] and step in [
        "validated",
        "submitted",
    ]:
        return {
            "category": "market_route_gate",
            "message": lifecycle.get("next_action")
            or "The selected market route is not ready for automated submission.",
        }

    if status == "review":
        return {
            "category": "human_or_policy_review",
            "message": current_step.get("message"),
        }

    if status == "waiting":
        return {
            "category": "missing_evidence",
            "message": current_step.get("message"),
        }

    if status == "blocked_by_prior_step":
        return {
            "category": "upstream_blocker",
            "message": current_step.get("message"),
        }

    return {
        "category": "blocked_step",
        "message": current_step.get("message") or lifecycle.get("next_action"),
    }


def classify_recovery_status(primary_action, lifecycle):
    if lifecycle.get("lifecycle_status") == "complete":
        return "no_recovery_needed"

    if primary_action.get("auto_resolvable"):
        return "auto_recovery_available"

    if primary_action.get("requires_human_approval"):
        return "human_gate_required"

    return "manual_recovery_required"


def requires_human_gate(current_step, lifecycle, control, template):
    human_gate_status = (control.get("human_gate") or {}).get("status")

    if template["action"] == "request_approval":
        return False

    if current_step.get("step") == "submitted" and human_gate_status not in [
        "passed",
        "not_required",
    ]:
        return True

    return lifecycle.get("market_route_status") in ["blocked", "paper_only"] and current_step.get(
        "step"
    ) in ["submitted", "acknowledged", "accepted", "awarded"]


def recovery_message(current_step, template, lifecycle):
    if template["endpoint"]:
        return f"{template['label']} to recover lifecycle step {current_step.get('label') or current_step.get('step')}."

    return (
        current_step.get("message")
        or lifecycle.get("next_action")
        or f"{template['label']} requires manual connector work."
    )


def severity_for_step(current_step):
    if current_step.get("status") == "blocked":
        return "high"

    if current_step.get("status") == "review":
        return "medium"

    return "low"


def format_endpoint(template, asset_id):
    if not template:
        return None

    return template.format(asset_id=asset_id)


def dedupe_queue(queue):
    seen = set()
    result = []

    for item in queue:
        key = (
            item.get("action"),
            item.get("resolution_endpoint"),
            item.get("source"),
        )
        if key in seen:
            continue

        seen.add(key)
        result.append(item)

    return result



