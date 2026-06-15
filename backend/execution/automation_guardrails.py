from backend.assets.asset_loader import get_asset
from backend.backtesting.forecast_actual.forecast_confidence import (
    build_forecast_confidence,
)
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
from backend.execution.automation_policy import evaluate_automation_policy
from backend.execution.pretrade_proposal import numeric


def evaluate_automation_guardrails(asset_id):
    asset = get_asset(asset_id)
    proposal_record = get_latest_execution_proposal(asset_id)
    approval_record = get_latest_execution_approval(asset_id)
    market_submission_record = get_latest_execution_market_submission(asset_id)
    paper_trade_record = get_latest_execution_paper_trade(asset_id)
    settlement_record = get_latest_settlement_reconciliation(asset_id)
    telemetry_record = get_latest_telemetry_snapshot(asset_id)
    forecast_confidence = build_forecast_confidence(asset_id)

    if proposal_record is None:
        return {
            "status": "proposal_missing",
            "asset_id": asset_id,
            "automation_status": "blocked",
            "message": "Build an execution proposal before evaluating automation.",
            "guardrails": [],
            "summary": {
                "passed": 0,
                "review": 0,
                "blocked": 1,
            },
            "recommended_actions": [
                "Build a pre-trade proposal from the latest dispatch signal.",
            ],
        }

    proposal = proposal_record["payload"]
    proposal["execution_proposal_id"] = proposal_record["execution_proposal_id"]
    approval = (approval_record or {}).get("payload")
    if approval:
        approval["approval_id"] = approval_record["approval_id"]
    paper_trade = (paper_trade_record or {}).get("payload")
    settlement = (settlement_record or {}).get("payload")
    telemetry = (telemetry_record or {}).get("payload")
    market_submission = (market_submission_record or {}).get("payload")
    guardrails = build_guardrails(
        asset=asset,
        forecast_confidence=forecast_confidence,
        paper_trade=paper_trade,
        proposal=proposal,
        settlement=settlement,
        telemetry=telemetry,
        market_submission=market_submission,
        approval=approval,
    )
    policy_evaluation = evaluate_automation_policy(
        asset_id=asset_id,
        forecast_confidence=forecast_confidence,
        paper_trade=paper_trade,
        proposal=proposal,
        approval=approval,
    )
    guardrails.append(automation_policy_guardrail(policy_evaluation))
    automation_status = classify_automation_status(
        asset=asset,
        forecast_confidence=forecast_confidence,
        guardrails=guardrails,
        policy_evaluation=policy_evaluation,
    )

    return {
        "status": "ok",
        "asset_id": asset_id,
        "automation_status": automation_status,
        "guardrails": guardrails,
        "summary": summarize_guardrails(guardrails),
        "recommended_actions": build_recommended_actions(
            automation_status=automation_status,
            guardrails=guardrails,
        ),
        "evidence": {
            "execution_proposal_id": proposal_record["execution_proposal_id"],
            "paper_trade_id": (paper_trade_record or {}).get("paper_trade_id"),
            "settlement_reconciliation_id": (
                settlement_record or {}
            ).get("settlement_reconciliation_id"),
            "telemetry_id": (telemetry_record or {}).get("telemetry_id"),
            "market_submission_id": (
                market_submission_record or {}
            ).get("market_submission_id"),
            "approval_id": (approval_record or {}).get("approval_id"),
            "forecast_confidence_score": forecast_confidence.get(
                "confidence_score"
            ),
            "forecast_confidence_band": forecast_confidence.get(
                "confidence_band"
            ),
            "automation_policy_id": policy_evaluation.get("policy", {}).get(
                "automation_policy_id"
            ),
            "automation_policy_source": policy_evaluation.get("policy_source"),
            "automation_policy_decision": policy_evaluation.get(
                "policy_decision"
            ),
        },
        "policy_evaluation": policy_evaluation,
    }


def latest_automation_guardrails(asset_id):
    return evaluate_automation_guardrails(asset_id)


def build_guardrails(
    asset,
    forecast_confidence,
    paper_trade,
    proposal,
    settlement,
    telemetry,
    market_submission,
    approval,
):
    commercial_config = asset.commercial_config or {}
    bids = proposal.get("bids") or proposal.get("orders", [])
    max_daily_loss = numeric(
        commercial_config.get("max_daily_loss_eur")
        or proposal.get("summary", {}).get("max_daily_loss_eur")
    )
    expected_pnl = numeric(proposal.get("summary", {}).get("expected_pnl_eur"))
    max_bid_volume_mw = max(
        [numeric(bid.get("risk_adjusted_volume_mw") or bid.get("volume_mw")) for bid in bids]
        or [0.0]
    )
    configured_max_bid_volume_mw = numeric(
        commercial_config.get("max_bid_volume_mw")
        or commercial_config.get("max_order_power_mw")
        or asset.grid_connection.get("max_export_mw")
        or asset.battery_config.get("max_discharge_power_mw")
    )

    return [
        forecast_confidence_guardrail(forecast_confidence),
        max_daily_loss_guardrail(expected_pnl, max_daily_loss),
        max_bid_size_guardrail(max_bid_volume_mw, configured_max_bid_volume_mw),
        paper_trade_guardrail(paper_trade),
        settlement_guardrail(settlement),
        market_adapter_guardrail(proposal, market_submission),
        telemetry_guardrail(asset, telemetry),
        approval_policy_guardrail(asset, proposal, approval),
    ]


def forecast_confidence_guardrail(forecast_confidence):
    score = numeric(forecast_confidence.get("confidence_score"))
    band = forecast_confidence.get("confidence_band")

    if band == "high":
        status = "passed"
    elif band == "medium":
        status = "review"
    else:
        status = "blocked"

    return {
        "guardrail": "forecast_confidence",
        "status": status,
        "message": forecast_confidence.get("reason"),
        "context": {
            "confidence_score": score,
            "confidence_band": band,
            "automation_eligibility": forecast_confidence.get(
                "automation_eligibility"
            ),
        },
    }


def max_daily_loss_guardrail(expected_pnl, max_daily_loss):
    if max_daily_loss <= 0:
        return {
            "guardrail": "max_daily_loss",
            "status": "review",
            "message": "No maximum daily loss limit is configured.",
            "context": {
                "expected_pnl_eur": expected_pnl,
                "max_daily_loss_eur": max_daily_loss,
            },
        }

    status = "passed" if expected_pnl >= -max_daily_loss else "blocked"

    return {
        "guardrail": "max_daily_loss",
        "status": status,
        "message": (
            "Expected PnL is within the daily loss limit."
            if status == "passed"
            else "Expected PnL breaches the configured daily loss limit."
        ),
        "context": {
            "expected_pnl_eur": expected_pnl,
            "max_daily_loss_eur": max_daily_loss,
        },
    }


def max_bid_size_guardrail(max_bid_volume_mw, configured_max_bid_volume_mw):
    if configured_max_bid_volume_mw <= 0:
        return {
            "guardrail": "max_bid_size",
            "status": "review",
            "message": "No max bid size limit is configured.",
            "context": {
                "max_bid_volume_mw": max_bid_volume_mw,
                "configured_max_bid_volume_mw": configured_max_bid_volume_mw,
            },
        }

    status = (
        "passed"
        if max_bid_volume_mw <= configured_max_bid_volume_mw
        else "blocked"
    )

    return {
        "guardrail": "max_bid_size",
        "status": status,
        "message": (
            "Risk-adjusted bid size is within configured limits."
            if status == "passed"
            else "Risk-adjusted bid size exceeds configured limits."
        ),
        "context": {
            "max_bid_volume_mw": max_bid_volume_mw,
            "configured_max_bid_volume_mw": configured_max_bid_volume_mw,
        },
    }


def paper_trade_guardrail(paper_trade):
    if not paper_trade:
        return {
            "guardrail": "paper_trade",
            "status": "blocked",
            "message": "No paper trade is available for the latest proposal.",
            "context": {},
        }

    return {
        "guardrail": "paper_trade",
        "status": "passed",
        "message": "A paper trade exists for execution-quality review.",
        "context": {
            "paper_pnl_eur": paper_trade.get("summary", {}).get("paper_pnl_eur"),
            "filled_order_count": paper_trade.get("summary", {}).get(
                "filled_order_count"
            ),
        },
    }


def settlement_guardrail(settlement):
    if not settlement:
        return {
            "guardrail": "settlement_reconciliation",
            "status": "review",
            "message": "No settlement reconciliation exists yet.",
            "context": {},
        }

    variance_drivers = settlement.get("variance_drivers", [])
    high_severity = any(
        driver.get("severity") == "high" for driver in variance_drivers
    )

    return {
        "guardrail": "settlement_reconciliation",
        "status": "blocked" if high_severity else "passed",
        "message": (
            "Settlement variance is within automation tolerance."
            if not high_severity
            else "Settlement variance has high-severity drivers."
        ),
        "context": {
            "settlement_status": settlement.get("status"),
            "primary_variance_driver": settlement.get("primary_variance_driver"),
        },
    }


def market_adapter_guardrail(proposal, market_submission):
    if proposal.get("market_submission_enabled"):
        return {
            "guardrail": "market_adapter",
            "status": "passed",
            "message": "Market submission is enabled for this proposal.",
            "context": {},
        }

    if market_submission:
        return {
            "guardrail": "market_adapter",
            "status": "review",
            "message": "Demo market adapter has simulated a submission lifecycle.",
            "context": {
                "adapter_id": market_submission.get("adapter_id"),
                "status": market_submission.get("status"),
                "live_submission": market_submission.get("live_submission"),
            },
        }

    return {
        "guardrail": "market_adapter",
        "status": "blocked",
        "message": "No live market adapter is enabled.",
        "context": {
            "market_submission_enabled": proposal.get("market_submission_enabled"),
        },
    }


def telemetry_guardrail(asset, telemetry):
    if not telemetry:
        return {
            "guardrail": "asset_telemetry",
            "status": "blocked",
            "message": "No telemetry snapshot is available.",
            "context": {
                "telemetry_available": False,
            },
        }

    availability_status = telemetry.get("availability_status")
    schedule_deviation_mwh = abs(numeric(telemetry.get("schedule_deviation_mwh")))
    maintenance_active = bool(telemetry.get("maintenance_active"))
    curtailment_active = bool(telemetry.get("curtailment_active"))

    if maintenance_active or curtailment_active:
        status = "blocked"
        message = "Asset telemetry shows maintenance or curtailment is active."
    elif availability_status != "available":
        status = "blocked"
        message = "Asset telemetry does not show the asset as available."
    elif schedule_deviation_mwh > 0.5:
        status = "review"
        message = "Schedule deviation requires operator review."
    else:
        status = "passed"
        message = "Latest telemetry supports execution readiness."

    return {
        "guardrail": "asset_telemetry",
        "status": status,
        "message": message,
        "context": {
            "telemetry_available": True,
            "provider": telemetry.get("provider"),
            "captured_at": telemetry.get("captured_at"),
            "availability_status": availability_status,
            "soc_percent": telemetry.get("soc_percent"),
            "schedule_deviation_mwh": telemetry.get("schedule_deviation_mwh"),
            "maintenance_active": maintenance_active,
            "curtailment_active": curtailment_active,
        },
    }


def approval_policy_guardrail(asset, proposal, approval):
    commercial_config = asset.commercial_config or {}
    approval_mode = commercial_config.get("approval_mode") or "human_required"

    if approval and approval.get("execution_proposal_id") != proposal.get("execution_proposal_id"):
        return {
            "guardrail": "approval_policy",
            "status": "blocked",
            "message": "Latest approval does not match the latest proposal.",
            "context": {
                "approval_status": approval.get("status"),
                "approval_id": approval.get("approval_id"),
                "approval_mode": approval_mode,
            },
        }

    if approval and approval.get("status") == "approved":
        status = "passed"
        message = "Latest execution proposal is approved."
    elif approval and approval.get("status") == "rejected":
        status = "blocked"
        message = "Latest execution proposal was rejected."
    elif approval and approval.get("status") == "requested":
        status = "review"
        message = "Execution approval is requested and awaiting decision."
    elif approval_mode == "auto":
        status = "passed"
        message = "Approval policy is auto."
    elif approval_mode in ["human_required", "supervised"]:
        status = "review"
        message = "Human approval is required before submission."
    else:
        status = "blocked"
        message = f"Approval policy is {approval_mode}."

    return {
        "guardrail": "approval_policy",
        "status": status,
        "message": message,
        "context": {
            "approval_mode": approval_mode,
            "approval_status": (approval or {}).get("status"),
            "approval_id": (approval or {}).get("approval_id"),
            "decided_by": (approval or {}).get("decided_by"),
            "decided_at": (approval or {}).get("decided_at"),
        },
    }


def automation_policy_guardrail(policy_evaluation):
    decision = policy_evaluation.get("policy_decision")
    summary = policy_evaluation.get("summary", {})

    if decision == "blocked":
        status = "blocked"
    elif summary.get("review", 0) > 0:
        status = "review"
    else:
        status = "passed"

    return {
        "guardrail": "automation_policy",
        "status": status,
        "message": f"Automation policy decision is {decision}.",
        "context": {
            "policy_decision": decision,
            "policy_source": policy_evaluation.get("policy_source"),
            "policy_summary": summary,
        },
    }


def classify_automation_status(
    asset,
    forecast_confidence,
    guardrails,
    policy_evaluation=None,
):
    statuses = {guardrail["status"] for guardrail in guardrails}
    commercial_config = asset.commercial_config or {}
    auto_trading_enabled = bool(commercial_config.get("auto_trading_enabled"))
    confidence_eligibility = forecast_confidence.get("automation_eligibility")
    policy_decision = (policy_evaluation or {}).get("policy_decision")

    if "blocked" in statuses:
        return "blocked"

    if policy_decision in ["paper_ready", "paper_only"]:
        return "paper_only"

    if policy_decision == "supervised_live_candidate":
        return "supervised_live_candidate"

    if policy_decision == "human_approval_required":
        return "human_approval_required"

    if confidence_eligibility == "paper_only":
        return "paper_only"

    if not auto_trading_enabled:
        return "human_approval_required"

    if "review" in statuses:
        return "human_approval_required"

    if confidence_eligibility == "supervised_live_candidate":
        return "supervised_live_candidate"

    return "human_approval_required"


def summarize_guardrails(guardrails):
    return {
        "passed": count_status(guardrails, "passed"),
        "review": count_status(guardrails, "review"),
        "blocked": count_status(guardrails, "blocked"),
        "total": len(guardrails),
    }


def build_recommended_actions(automation_status, guardrails):
    actions = []

    for guardrail in guardrails:
        if guardrail["status"] == "blocked":
            actions.append(f"Clear blocker: {guardrail['message']}")
        elif guardrail["status"] == "review":
            actions.append(f"Review: {guardrail['message']}")

    if not actions:
        actions.append(
            "Keep human-supervised mode until live adapter and telemetry controls are production validated."
        )

    if automation_status == "blocked":
        actions.append("Keep trading in advisory or paper mode.")
    elif automation_status == "human_approval_required":
        actions.append("Require operator approval before any live submission.")

    return dedupe(actions)


def count_status(guardrails, status):
    return len([guardrail for guardrail in guardrails if guardrail["status"] == status])


def dedupe(items):
    seen = set()
    result = []

    for item in items:
        if item in seen:
            continue

        seen.add(item)
        result.append(item)

    return result



