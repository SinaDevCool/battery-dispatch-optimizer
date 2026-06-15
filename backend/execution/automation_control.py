from datetime import datetime, timezone

from backend.config.paths import ACTUAL_PRICE_FILE, FORECAST_FILE
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
from backend.execution.automation_policy import latest_automation_policy
from backend.execution.execution_readiness import build_execution_readiness
from backend.execution.market_adapters.registry import get_asset_market_adapter_status
from backend.execution.multi_market_allocator import build_multi_market_allocation
from backend.services.persistence_readiness import build_persistence_readiness
from backend.storage import get_storage_client


AUTOMATION_MODE_SEQUENCE = [
    "advisory_only",
    "paper_trading",
    "supervised_auto",
    "live_auto_limited",
    "live_auto_blocked",
]


def automation_control_status(asset_id, allocation=None, guardrails=None):
    policy_response = latest_automation_policy(asset_id)
    policy = policy_response["policy"]
    guardrails = guardrails or latest_automation_guardrails(asset_id)
    readiness = build_execution_readiness(asset_id)
    adapter_status = get_asset_market_adapter_status(asset_id)
    allocation = allocation or build_multi_market_allocation(asset_id)
    proposal_record = get_latest_execution_proposal(asset_id)
    paper_trade_record = get_latest_execution_paper_trade(asset_id)
    approval_record = get_latest_execution_approval(asset_id)
    submission_record = get_latest_execution_market_submission(asset_id)
    freshness_gates = build_freshness_gates(asset_id)
    persistence_readiness = build_persistence_readiness()

    policy_decision = (
        guardrails.get("policy_evaluation", {}).get("policy_decision")
        or guardrails.get("evidence", {}).get("automation_policy_decision")
    )
    mode = classify_automation_mode(
        adapter_status=adapter_status,
        guardrails=guardrails,
        policy=policy,
        policy_decision=policy_decision,
        persistence_readiness=persistence_readiness,
        readiness=readiness,
        paper_trade_record=paper_trade_record,
    )
    blockers = build_automation_blockers(
        allocation=allocation,
        freshness_gates=freshness_gates,
        guardrails=guardrails,
        persistence_readiness=persistence_readiness,
        readiness=readiness,
    )
    human_gate = build_human_gate(
        approval_record=approval_record,
        policy=policy,
        proposal_record=proposal_record,
    )
    escalation = evaluate_mode_escalation(
        approval_record=approval_record,
        freshness_gates=freshness_gates,
        guardrails=guardrails,
        human_gate=human_gate,
        mode=mode,
        paper_trade_record=paper_trade_record,
        policy=policy,
        proposal_record=proposal_record,
        settlement_record=get_latest_settlement_reconciliation(asset_id),
    )

    return {
        "status": "ok",
        "asset_id": asset_id,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "automation_mode": mode,
        "automation_mode_rank": AUTOMATION_MODE_SEQUENCE.index(mode),
        "live_trading_allowed": mode == "live_auto_limited",
        "paper_trading_allowed": mode in [
            "paper_trading",
            "supervised_auto",
            "live_auto_limited",
        ],
        "supervised_trading_allowed": mode in [
            "supervised_auto",
            "live_auto_limited",
        ],
        "policy_decision": policy_decision,
        "automation_status": guardrails.get("automation_status"),
        "readiness_status": readiness.get("readiness_status"),
        "readiness_score": readiness.get("readiness_score"),
        "connector_status": adapter_status.get("market_adapter_status"),
        "primary_market": allocation.get("primary_market"),
        "secondary_market": allocation.get("secondary_market"),
        "allowed_markets": policy.get("allowed_markets", []),
        "risk_limits": policy.get("risk_limits", {}),
        "confidence_policy": policy.get("confidence_policy", {}),
        "human_gate": human_gate,
        "mode_escalation": escalation,
        "persistence_readiness": persistence_readiness,
        "freshness_gates": freshness_gates,
        "blockers": blockers,
        "remediation_queue": build_remediation_queue(
            asset_id=asset_id,
            blockers=blockers,
            human_gate=human_gate,
            paper_trade_record=paper_trade_record,
            proposal_record=proposal_record,
            submission_record=submission_record,
        ),
        "next_automation_action": next_automation_action(
            blockers=blockers,
            human_gate=human_gate,
            mode=mode,
            paper_trade_record=paper_trade_record,
            proposal_record=proposal_record,
            submission_record=submission_record,
        ),
        "evidence": {
            "automation_policy_id": policy.get("automation_policy_id"),
            "automation_policy_source": policy_response.get("source"),
            "execution_proposal_id": (proposal_record or {}).get(
                "execution_proposal_id"
            ),
            "paper_trade_id": (paper_trade_record or {}).get("paper_trade_id"),
            "approval_id": (approval_record or {}).get("approval_id"),
            "market_submission_id": (submission_record or {}).get(
                "market_submission_id"
            ),
            "readiness_summary": readiness.get("summary", {}),
            "guardrail_summary": guardrails.get("summary", {}),
            "allocation_summary": allocation.get("summary", {}),
            "persistence_summary": persistence_readiness.get("summary", {}),
            "live_submission_enabled": adapter_status.get(
                "live_submission_enabled"
            ),
        },
    }


def evaluate_mode_escalation(
    approval_record,
    freshness_gates,
    guardrails,
    human_gate,
    mode,
    paper_trade_record,
    policy,
    proposal_record,
    settlement_record,
):
    ladder = build_mode_ladder()
    current_index = mode_rank(mode)
    next_mode = next_eligible_target_mode(mode)
    target_requirements = mode_requirements(
        approval_record=approval_record,
        freshness_gates=freshness_gates,
        guardrails=guardrails,
        human_gate=human_gate,
        paper_trade_record=paper_trade_record,
        policy=policy,
        proposal_record=proposal_record,
        settlement_record=settlement_record,
        target_mode=next_mode,
    )
    failed = [
        requirement
        for requirement in target_requirements
        if requirement["status"] != "passed"
    ]

    return {
        "current_mode": mode,
        "current_mode_rank": current_index,
        "next_eligible_mode": next_mode,
        "can_escalate": bool(next_mode and not failed),
        "escalation_blockers": failed,
        "ladder": [
            {
                **step,
                "status": ladder_step_status(
                    current_index=current_index,
                    step_mode=step["mode"],
                ),
            }
            for step in ladder
        ],
        "required_evidence": target_requirements,
        "target_mode": next_mode,
    }


def build_mode_ladder():
    return [
        {
            "mode": "advisory_only",
            "label": "Advisory",
            "description": "Recommendations only; no automated market action.",
        },
        {
            "mode": "paper_trading",
            "label": "Paper Trading",
            "description": "Automated proposals and simulated execution.",
        },
        {
            "mode": "supervised_auto",
            "label": "Supervised Auto",
            "description": "Automation runs with a human gate before submission.",
        },
        {
            "mode": "live_auto_limited",
            "label": "Limited Live Auto",
            "description": "Live submission inside hard limits and connector gates.",
        },
    ]


def mode_rank(mode):
    ranks = {
        "advisory_only": 0,
        "paper_trading": 1,
        "supervised_auto": 2,
        "live_auto_limited": 3,
        "live_auto_blocked": 0,
    }

    return ranks.get(mode, 0)


def next_eligible_target_mode(mode):
    if mode in ["live_auto_limited"]:
        return None

    if mode in ["supervised_auto"]:
        return "live_auto_limited"

    if mode in ["paper_trading"]:
        return "supervised_auto"

    return "paper_trading"


def ladder_step_status(current_index, step_mode):
    step_index = mode_rank(step_mode)

    if step_index < current_index:
        return "passed"

    if step_index == current_index:
        return "current"

    if step_index == current_index + 1:
        return "next"

    return "locked"


def mode_requirements(
    approval_record,
    freshness_gates,
    guardrails,
    human_gate,
    paper_trade_record,
    policy,
    proposal_record,
    settlement_record,
    target_mode,
):
    if target_mode is None:
        return []

    requirements = []

    requirements.append(
        evidence_requirement(
            check="proposal_available",
            label="Automated proposal",
            status="passed" if proposal_record else "blocked",
            message=(
                "Latest automated proposal exists."
                if proposal_record
                else "Build an automated proposal before mode escalation."
            ),
        )
    )

    if target_mode in ["paper_trading", "supervised_auto", "live_auto_limited"]:
        requirements.extend(freshness_requirements(freshness_gates, target_mode))

    if target_mode in ["supervised_auto", "live_auto_limited"]:
        requirements.append(
            evidence_requirement(
                check="paper_trade_available",
                label="Paper trading evidence",
                status="passed" if paper_trade_record else "blocked",
                message=(
                    "Paper trading evidence exists."
                    if paper_trade_record
                    else "Run paper trading before supervised automation."
                ),
            )
        )
        requirements.append(
            paper_delta_requirement(policy=policy, paper_trade_record=paper_trade_record)
        )

    if target_mode == "live_auto_limited":
        requirements.append(
            human_gate_requirement(human_gate=human_gate, approval_record=approval_record)
        )
        requirements.append(
            guardrail_requirement(guardrails=guardrails)
        )
        requirements.append(
            settlement_requirement(settlement_record=settlement_record)
        )

    return requirements


def freshness_requirements(freshness_gates, target_mode):
    target_rank = mode_rank(target_mode)
    requirements = []

    for gate in freshness_gates:
        if mode_rank(gate.get("blocks_mode")) > target_rank:
            continue

        status = "passed" if gate.get("freshness_status") == "fresh" else "blocked"
        requirements.append(
            evidence_requirement(
                check=gate.get("gate_id"),
                label=gate.get("label"),
                status=status,
                message=(
                    f"{gate.get('label')} freshness is valid."
                    if status == "passed"
                    else gate.get("required_action")
                ),
                context={
                    "age_minutes": gate.get("age_minutes"),
                    "blocks_mode": gate.get("blocks_mode"),
                    "freshness_status": gate.get("freshness_status"),
                    "max_age_minutes": gate.get("max_age_minutes"),
                },
            )
        )

    return requirements


def paper_delta_requirement(policy, paper_trade_record):
    if not paper_trade_record:
        return evidence_requirement(
            check="paper_delta",
            label="Paper delta tolerance",
            status="blocked",
            message="No paper trade is available for delta tolerance evaluation.",
        )

    paper_trade = paper_trade_record.get("payload", {})
    summary = paper_trade.get("summary", {})
    delta = abs(numeric(summary.get("paper_vs_expected_delta_eur")))
    max_delta = numeric(
        (policy.get("simulation_policy") or {}).get(
            "max_paper_vs_expected_delta_eur"
        )
    )
    status = "passed" if max_delta <= 0 or delta <= max_delta else "blocked"

    return evidence_requirement(
        check="paper_delta",
        label="Paper delta tolerance",
        status=status,
        message=(
            "Paper-vs-expected delta is inside automation tolerance."
            if status == "passed"
            else "Paper-vs-expected delta exceeds automation tolerance."
        ),
        context={
            "paper_vs_expected_delta_eur": delta,
            "max_paper_vs_expected_delta_eur": max_delta,
        },
    )


def human_gate_requirement(human_gate, approval_record):
    status = "passed" if human_gate.get("status") in ["passed", "not_required"] else "blocked"

    return evidence_requirement(
        check="human_gate",
        label="Human gate",
        status=status,
        message=(
            "Human gate is clear for escalation."
            if status == "passed"
            else "Clear the human gate before limited live automation."
        ),
        context={
            "approval_id": (approval_record or {}).get("approval_id"),
            "human_gate_status": human_gate.get("status"),
        },
    )


def guardrail_requirement(guardrails):
    summary = guardrails.get("summary", {})
    status = (
        "passed"
        if not summary.get("blocked", 0) and not summary.get("review", 0)
        else "blocked"
    )

    return evidence_requirement(
        check="guardrails_clear",
        label="Automation guardrails",
        status=status,
        message=(
            "Automation guardrails are clear."
            if status == "passed"
            else "Resolve blocked or review guardrails before limited live automation."
        ),
        context=summary,
    )


def settlement_requirement(settlement_record):
    if not settlement_record:
        return evidence_requirement(
            check="settlement_feedback",
            label="Settlement feedback",
            status="blocked",
            message="Settlement feedback is required before limited live automation.",
        )

    settlement = settlement_record.get("payload", {})
    high_variance = any(
        row.get("severity") == "high"
        for row in settlement.get("variance_drivers", [])
    )

    return evidence_requirement(
        check="settlement_feedback",
        label="Settlement feedback",
        status="blocked" if high_variance else "passed",
        message=(
            "Settlement feedback is inside escalation tolerance."
            if not high_variance
            else "High-severity settlement variance blocks limited live automation."
        ),
        context={
            "settlement_reconciliation_id": settlement_record.get(
                "settlement_reconciliation_id"
            ),
            "status": settlement.get("status"),
        },
    )


def evidence_requirement(check, label, status, message, context=None):
    return {
        "check": check,
        "context": context or {},
        "label": label,
        "message": message,
        "status": status,
    }


def classify_automation_mode(
    adapter_status,
    guardrails,
    policy,
    policy_decision,
    persistence_readiness,
    readiness,
    paper_trade_record,
):
    policy_mode = policy.get("automation_mode")

    if policy_mode == "disabled":
        return "live_auto_blocked"

    if persistence_readiness.get("persistence_status") != "ready":
        return "live_auto_blocked"

    if (
        guardrails.get("automation_status") == "blocked"
        or readiness.get("readiness_status") == "blocked"
        or policy_decision == "blocked"
    ):
        return "live_auto_blocked"

    if policy_decision in ["paper_only", "paper_ready"] or not paper_trade_record:
        return "paper_trading"

    if (
        policy_decision == "supervised_live_candidate"
        and readiness.get("readiness_status") == "supervised_ready"
    ):
        if adapter_status.get("live_submission_enabled"):
            approval_policy = policy.get("approval_policy", {})
            if not approval_policy.get("require_human_approval", True):
                return "live_auto_limited"
        return "supervised_auto"

    if policy_decision == "human_approval_required":
        return "supervised_auto"

    return "advisory_only"


def build_human_gate(policy, proposal_record, approval_record):
    approval_policy = policy.get("approval_policy", {})
    requires_human = bool(approval_policy.get("require_human_approval", True))
    proposal_id = (proposal_record or {}).get("execution_proposal_id")
    approval_payload = (approval_record or {}).get("payload") or {}
    approval_status = approval_payload.get("status")
    approval_matches = (
        bool(approval_record)
        and proposal_id is not None
        and approval_payload.get("execution_proposal_id") == proposal_id
    )

    if not requires_human:
        gate_status = "not_required"
    elif approval_matches and approval_status == "approved":
        gate_status = "passed"
    elif approval_matches and approval_status == "requested":
        gate_status = "pending"
    elif approval_matches and approval_status == "rejected":
        gate_status = "blocked"
    else:
        gate_status = "required"

    return {
        "required": requires_human,
        "status": gate_status,
        "approval_id": (approval_record or {}).get("approval_id"),
        "approval_status": approval_status,
        "execution_proposal_id": proposal_id,
        "auto_approve_below_power_mw": approval_policy.get(
            "auto_approve_below_power_mw"
        ),
        "four_eyes_required_above_power_mw": approval_policy.get(
            "four_eyes_required_above_power_mw"
        ),
    }


def build_freshness_gates(asset_id):
    telemetry_record = get_latest_telemetry_snapshot(asset_id)
    settlement_record = get_latest_settlement_reconciliation(asset_id)

    return [
        file_freshness_gate(
            gate_id="forecast_freshness",
            label="Forecast",
            path=FORECAST_FILE,
            max_age_minutes=180,
            blocks_mode="paper_trading",
            required_action="Refresh forecast data before automated proposal generation.",
        ),
        file_freshness_gate(
            gate_id="actual_price_freshness",
            label="Actual prices",
            path=ACTUAL_PRICE_FILE,
            max_age_minutes=1440,
            blocks_mode="supervised_auto",
            required_action="Refresh actual price data for forecast confidence and reconciliation.",
        ),
        record_freshness_gate(
            gate_id="telemetry_freshness",
            label="Telemetry / EMS",
            record=telemetry_record,
            timestamp_key="captured_at",
            max_age_minutes=15,
            blocks_mode="live_auto_limited",
            required_action="Refresh EMS telemetry before live automated trading.",
        ),
        record_freshness_gate(
            gate_id="settlement_freshness",
            label="Settlement evidence",
            record=settlement_record,
            timestamp_key="generated_at",
            max_age_minutes=10080,
            blocks_mode="live_auto_limited",
            required_action="Run settlement reconciliation to keep feedback evidence current.",
        ),
    ]


def file_freshness_gate(
    gate_id,
    label,
    path,
    max_age_minutes,
    blocks_mode,
    required_action,
):
    storage = get_storage_client()

    if not storage.exists(path):
        return freshness_gate(
            age_minutes=None,
            blocks_mode=blocks_mode,
            freshness_status="missing",
            gate_id=gate_id,
            label=label,
            last_seen_at=None,
            max_age_minutes=max_age_minutes,
            required_action=required_action,
        )

    try:
        modified_at = datetime.fromtimestamp(path.stat().st_mtime)
    except OSError:
        modified_at = None

    return timestamp_freshness_gate(
        blocks_mode=blocks_mode,
        gate_id=gate_id,
        label=label,
        max_age_minutes=max_age_minutes,
        required_action=required_action,
        timestamp=modified_at,
    )


def record_freshness_gate(
    gate_id,
    label,
    record,
    timestamp_key,
    max_age_minutes,
    blocks_mode,
    required_action,
):
    payload = (record or {}).get("payload") or {}
    timestamp = parse_datetime(payload.get(timestamp_key) or (record or {}).get(timestamp_key))

    return timestamp_freshness_gate(
        blocks_mode=blocks_mode,
        gate_id=gate_id,
        label=label,
        max_age_minutes=max_age_minutes,
        required_action=required_action,
        timestamp=timestamp,
    )


def timestamp_freshness_gate(
    blocks_mode,
    gate_id,
    label,
    max_age_minutes,
    required_action,
    timestamp,
):
    if timestamp is None:
        return freshness_gate(
            age_minutes=None,
            blocks_mode=blocks_mode,
            freshness_status="missing",
            gate_id=gate_id,
            label=label,
            last_seen_at=None,
            max_age_minutes=max_age_minutes,
            required_action=required_action,
        )

    age_minutes = round(
        max((datetime.now() - timestamp).total_seconds() / 60, 0),
        1,
    )

    return freshness_gate(
        age_minutes=age_minutes,
        blocks_mode=blocks_mode,
        freshness_status="fresh" if age_minutes <= max_age_minutes else "stale",
        gate_id=gate_id,
        label=label,
        last_seen_at=timestamp.isoformat(timespec="seconds"),
        max_age_minutes=max_age_minutes,
        required_action=required_action,
    )


def freshness_gate(
    age_minutes,
    blocks_mode,
    freshness_status,
    gate_id,
    label,
    last_seen_at,
    max_age_minutes,
    required_action,
):
    return {
        "age_minutes": age_minutes,
        "blocks_mode": blocks_mode,
        "freshness_status": freshness_status,
        "gate_id": gate_id,
        "label": label,
        "last_seen_at": last_seen_at,
        "max_age_minutes": max_age_minutes,
        "required_action": required_action,
    }


def parse_datetime(value):
    if not value:
        return None

    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None

    if parsed.tzinfo is not None:
        return parsed.astimezone(timezone.utc).replace(tzinfo=None)

    return parsed


def numeric(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def build_automation_blockers(
    guardrails,
    readiness,
    allocation,
    freshness_gates,
    persistence_readiness,
):
    blockers = []

    blockers.extend(
        blocker_rows(
            source="guardrail",
            rows=guardrails.get("guardrails", []),
            label_key="guardrail",
        )
    )
    blockers.extend(
        blocker_rows(
            source="readiness",
            rows=readiness.get("checks", []),
            label_key="check",
        )
    )

    for market in allocation.get("excluded_markets", []):
        blockers.append(
            {
                "source": "market_allocation",
                "key": market.get("adapter_id"),
                "status": "blocked",
                "message": "; ".join(market.get("blocking_reasons", []))
                or market.get("operator_next_action"),
            }
        )

    for gate in freshness_gates:
        if gate.get("freshness_status") in ["missing", "stale"]:
            blockers.append(
                {
                    "source": "freshness",
                    "key": gate.get("gate_id"),
                    "status": "blocked",
                    "message": (
                        f"{gate.get('label')} is {gate.get('freshness_status')} "
                        f"and blocks {gate.get('blocks_mode')}."
                    ),
                }
            )

    if persistence_readiness.get("persistence_status") != "ready":
        blockers.append(
            {
                "source": "persistence",
                "key": "persistence_readiness",
                "status": "blocked",
                "message": "Persistence is not ready and blocks automated trading evidence writes.",
            }
        )

        for check in persistence_readiness.get("checks", []):
            if check.get("status") == "blocked":
                blockers.append(
                    {
                        "source": "persistence",
                        "key": check.get("check"),
                        "status": "blocked",
                        "message": check.get("message"),
                    }
                )

    return dedupe_blockers(blockers)


def build_remediation_queue(
    asset_id,
    blockers,
    human_gate,
    paper_trade_record,
    proposal_record,
    submission_record,
):
    queue = []

    if not proposal_record:
        queue.append(
            remediation_item(
                blocker_id="missing_execution_proposal",
                category="automation_step",
                message="No automated bid proposal is available.",
                required_action="Build the next proposal from the latest actionable signal.",
                resolution_endpoint=f"/assets/{asset_id}/execution/proposal/build",
                severity="high",
                source="execution_proposal",
                auto_resolvable=True,
                evidence_link="/execution/proposals",
            )
        )

    if proposal_record and not paper_trade_record:
        queue.append(
            remediation_item(
                blocker_id="missing_paper_trade",
                category="automation_step",
                message="No paper trade exists for the latest proposal.",
                required_action="Run automatic paper trading validation.",
                resolution_endpoint=f"/assets/{asset_id}/execution/paper-trade/run",
                severity="high",
                source="paper_trade",
                auto_resolvable=True,
                evidence_link="/execution/simulation",
            )
        )

    if human_gate.get("status") == "required":
        queue.append(
            remediation_item(
                blocker_id="human_gate_required",
                category="human_gate",
                message="Automation policy requires a human gate before higher automation modes.",
                required_action="Request the human gate for the latest automated trading proposal.",
                resolution_endpoint=f"/assets/{asset_id}/execution/approval/request",
                severity="medium",
                source="approval_policy",
                auto_resolvable=True,
                evidence_link="/execution/risk-approval",
            )
        )
    elif human_gate.get("status") == "pending":
        queue.append(
            remediation_item(
                blocker_id="human_gate_pending",
                category="human_gate",
                message="Human gate has been requested and is awaiting decision.",
                required_action="Clear or block the human gate after review.",
                resolution_endpoint=None,
                severity="medium",
                source="approval_policy",
                auto_resolvable=False,
                evidence_link="/execution/risk-approval",
            )
        )
    elif human_gate.get("status") == "blocked":
        queue.append(
            remediation_item(
                blocker_id="human_gate_blocked",
                category="human_gate",
                message="Human gate blocks automated trading.",
                required_action="Resolve the rejected gate reason before continuing automation.",
                resolution_endpoint=None,
                severity="critical",
                source="approval_policy",
                auto_resolvable=False,
                evidence_link="/execution/risk-approval",
            )
        )

    if proposal_record and paper_trade_record and not submission_record:
        queue.append(
            remediation_item(
                blocker_id="missing_submission_evidence",
                category="automation_step",
                message="No simulated or live market submission evidence exists.",
                required_action="Run the configured submission path after the human gate clears.",
                resolution_endpoint=f"/assets/{asset_id}/execution/demo-submit",
                severity="medium",
                source="market_submission",
                auto_resolvable=human_gate.get("status") in ["passed", "not_required"],
                evidence_link="/execution/simulation",
            )
        )

    for blocker in blockers:
        mapped = remediation_from_blocker(asset_id=asset_id, blocker=blocker)
        if mapped:
            queue.append(mapped)

    return dedupe_remediation(queue)


def remediation_from_blocker(asset_id, blocker):
    source = blocker.get("source")
    key = blocker.get("key")
    message = blocker.get("message") or ""

    if source == "freshness":
        return freshness_remediation(asset_id=asset_id, key=key, message=message)

    if source == "persistence":
        return remediation_item(
            blocker_id=f"persistence_{key}",
            category="persistence",
            message=message,
            required_action="Fix database writability, migration capability, and required automation evidence tables.",
            resolution_endpoint=None,
            severity="critical",
            source=source,
            auto_resolvable=False,
            evidence_link="/execution/market-connectors",
        )

    if key in ["asset_telemetry", "asset_telemetry"]:
        return remediation_item(
            blocker_id="missing_or_blocked_telemetry",
            category="asset_evidence",
            message=message,
            required_action="Refresh asset telemetry or seed demo telemetry for validation.",
            resolution_endpoint=f"/assets/{asset_id}/telemetry/demo",
            severity="high",
            source=source,
            auto_resolvable=True,
            evidence_link="/execution/audit",
        )

    if key in ["settlement_reconciliation"]:
        return remediation_item(
            blocker_id="missing_settlement_reconciliation",
            category="settlement",
            message=message,
            required_action="Run settlement reconciliation after paper/submission evidence exists.",
            resolution_endpoint=f"/assets/{asset_id}/settlement/reconcile",
            severity="medium",
            source=source,
            auto_resolvable=True,
            evidence_link="/execution/settlement",
        )

    if key in ["paper_trade", "paper_trade_required"]:
        return remediation_item(
            blocker_id="paper_trade_required",
            category="automation_step",
            message=message,
            required_action="Run automatic paper trading validation.",
            resolution_endpoint=f"/assets/{asset_id}/execution/paper-trade/run",
            severity="high",
            source=source,
            auto_resolvable=True,
            evidence_link="/execution/simulation",
        )

    if key in ["execution_proposal", "allowed_market"]:
        return remediation_item(
            blocker_id=f"{key}_blocked",
            category="market_or_bid_evidence",
            message=message,
            required_action="Refresh proposal and market allocation evidence.",
            resolution_endpoint=f"/assets/{asset_id}/execution/proposal/build",
            severity="high",
            source=source,
            auto_resolvable=True,
            evidence_link="/execution/proposals",
        )

    if key in ["market_adapter"] or "adapter" in message.lower() or "credentials" in message.lower():
        return remediation_item(
            blocker_id="market_adapter_integration",
            category="integration",
            message=message,
            required_action="Connect market credentials and validate adapter readiness before live automation.",
            resolution_endpoint=None,
            severity="critical",
            source=source,
            auto_resolvable=False,
            evidence_link="/execution/market-connectors",
        )

    if key in ["forecast_confidence", "confidence_threshold"]:
        return remediation_item(
            blocker_id="forecast_confidence_gate",
            category="market_evidence",
            message=message,
            required_action="Improve or validate forecast performance before increasing automation mode.",
            resolution_endpoint=None,
            severity="high",
            source=source,
            auto_resolvable=False,
            evidence_link="/forecasts",
        )

    if key in ["human_approval_required", "approval_policy", "operator_approval"]:
        return remediation_item(
            blocker_id="human_gate_policy",
            category="human_gate",
            message=message,
            required_action="Request or clear the human automation gate.",
            resolution_endpoint=f"/assets/{asset_id}/execution/approval/request",
            severity="medium",
            source=source,
            auto_resolvable=True,
            evidence_link="/execution/risk-approval",
        )

    if blocker.get("status") == "review":
        return remediation_item(
            blocker_id=f"review_{source}_{key}",
            category="review",
            message=message,
            required_action="Review evidence before increasing automation level.",
            resolution_endpoint=None,
            severity="medium",
            source=source,
            auto_resolvable=False,
            evidence_link="/execution",
        )

    return remediation_item(
        blocker_id=f"blocked_{source}_{key}",
        category="unknown",
        message=message,
        required_action="Resolve this blocker before live automated trading.",
        resolution_endpoint=None,
        severity="high",
        source=source,
        auto_resolvable=False,
        evidence_link="/execution",
    )


def freshness_remediation(asset_id, key, message):
    if key == "telemetry_freshness":
        return remediation_item(
            blocker_id="stale_telemetry",
            category="freshness",
            message=message,
            required_action="Refresh EMS telemetry before live automated trading.",
            resolution_endpoint=f"/assets/{asset_id}/telemetry/demo",
            severity="high",
            source="freshness",
            auto_resolvable=True,
            evidence_link="/execution/audit",
        )

    if key == "settlement_freshness":
        return remediation_item(
            blocker_id="stale_settlement",
            category="freshness",
            message=message,
            required_action="Run settlement reconciliation to refresh feedback evidence.",
            resolution_endpoint=f"/assets/{asset_id}/settlement/reconcile",
            severity="medium",
            source="freshness",
            auto_resolvable=True,
            evidence_link="/execution/settlement",
        )

    return remediation_item(
        blocker_id=f"stale_{key}",
        category="freshness",
        message=message,
        required_action="Refresh source data before increasing automation level.",
        resolution_endpoint=None,
        severity="high",
        source="freshness",
        auto_resolvable=False,
        evidence_link="/forecasts",
    )


def remediation_item(
    blocker_id,
    category,
    message,
    required_action,
    resolution_endpoint,
    severity,
    source,
    auto_resolvable,
    evidence_link,
):
    return {
        "blocker_id": blocker_id,
        "category": category,
        "severity": severity,
        "source": source,
        "message": message,
        "required_action": required_action,
        "auto_resolvable": bool(auto_resolvable and resolution_endpoint),
        "resolution_endpoint": resolution_endpoint,
        "evidence_link": evidence_link,
    }


def dedupe_remediation(rows):
    seen = set()
    result = []

    severity_rank = {
        "critical": 0,
        "high": 1,
        "medium": 2,
        "low": 3,
    }

    for row in sorted(rows, key=lambda item: severity_rank.get(item["severity"], 4)):
        key = row.get("blocker_id")
        if not key or key in seen:
            continue

        seen.add(key)
        result.append(row)

    return result


def blocker_rows(source, rows, label_key):
    return [
        {
            "source": source,
            "key": row.get(label_key),
            "status": row.get("status"),
            "message": row.get("message"),
        }
        for row in rows
        if row.get("status") in ["blocked", "review"]
    ]


def next_automation_action(
    blockers,
    human_gate,
    mode,
    paper_trade_record,
    proposal_record,
    submission_record,
):
    if mode == "live_auto_blocked":
        return automation_action(
            "clear_blockers",
            "Clear automation blockers before any live trading.",
            "risk_engine",
        )

    if not proposal_record:
        return automation_action(
            "build_proposal",
            "Build the next bid proposal automatically from the latest ACTION signal.",
            "execution_engine",
        )

    if not paper_trade_record:
        return automation_action(
            "run_paper_trade",
            "Run paper trading automatically before supervised or live submission.",
            "paper_adapter",
        )

    if human_gate.get("status") in ["required", "pending"]:
        return automation_action(
            "wait_for_supervised_gate",
            "Keep automated trading in supervised mode until the human gate clears.",
            "approval_gate",
        )

    if blockers:
        return automation_action(
            "clear_review_items",
            "Resolve review items before increasing automation level.",
            "automation_control",
        )

    if mode == "live_auto_limited" and not submission_record:
        return automation_action(
            "submit_with_limits",
            "Submit automatically within configured risk and market limits.",
            "market_adapter",
        )

    return automation_action(
        "monitor_and_reoptimize",
        "Continue monitoring signals, telemetry, and market routes for automatic re-optimization.",
        "automation_control",
    )


def automation_action(action, message, owner):
    return {
        "action": action,
        "label": action.replace("_", " ").title(),
        "message": message,
        "owner": owner,
    }


def dedupe_blockers(rows):
    seen = set()
    result = []

    for row in rows:
        key = (row.get("source"), row.get("key"), row.get("status"), row.get("message"))
        if not row.get("message") or key in seen:
            continue

        seen.add(key)
        result.append(row)

    return result



