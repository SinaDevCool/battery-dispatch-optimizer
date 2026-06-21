import asyncio
import json
import os
from datetime import datetime

from backend.backtesting.forecast_actual.forecast_confidence import (
    build_forecast_confidence,
)
from backend.execution.automation_control import automation_control_status
from backend.execution.trading_orchestrator import trading_orchestrator_status
from backend.ai_intelligence.history import append_trading_supervisor_history
from backend.ai_intelligence.safe_actions import list_safe_actions
from backend.services.asset_signal_store import load_asset_latest_signal


DEFAULT_MODEL = os.environ.get("TRADING_SUPERVISOR_MODEL", "gpt-5.5")


TRADING_SUPERVISOR_INSTRUCTIONS = """
You are the AI Trading Supervisor for Battery Trader AI.
Your job is not to narrate every 15-minute trade. Your job is to supervise
continuous automated trading and explain only material exceptions, pauses,
escalations, and evidence gaps.

Use the provided machine context as source of truth. Do not invent market data,
revenues, approvals, connector status, or settlement facts. Produce concise
operator language with:
1. current supervisory decision,
2. why automation should continue, pause, or escalate,
3. highest-priority exception,
4. next human or system action,
5. audit evidence references available in the context.
"""


def build_trading_supervisor_status(
    asset_id,
    include_ai_brief=False,
    evidence_mode="live",
    record_history=False,
    operator_question=None,
):
    evidence_mode = normalize_evidence_mode(evidence_mode)
    context = build_supervisor_context(asset_id)
    if evidence_mode == "mock":
        context = apply_mock_supervisor_mode(context)
    exceptions = detect_supervisor_exceptions(context)
    recommendation = build_supervisor_recommendation(context, exceptions)
    ai_brief = build_ai_brief_if_requested(
        context=context,
        exceptions=exceptions,
        include_ai_brief=include_ai_brief,
        operator_question=operator_question,
        recommendation=recommendation,
    )

    response = {
        "status": "ok",
        "asset_id": asset_id,
        "evidence_mode": evidence_mode,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "agent": {
            "agent_id": "ai_trading_supervisor",
            "name": "AI Trading Supervisor Agent",
            "mode": "exception_supervision",
            "scope": [
                "day_ahead",
                "intraday",
                "ancillary_services",
                "automation_gates",
                "execution_evidence",
            ],
            "llm_model": DEFAULT_MODEL,
        },
        "supervisor_status": recommendation["supervisor_status"],
        "decision": recommendation["decision"],
        "automation_action": recommendation["automation_action"],
        "exception_count": len(exceptions),
        "highest_severity": highest_severity(exceptions),
        "exceptions": exceptions,
        "recommendation": recommendation,
        "daily_brief": build_daily_supervisor_brief(
            context=context,
            exceptions=exceptions,
            recommendation=recommendation,
        ),
        "suggested_questions": suggested_supervisor_questions(context, exceptions),
        "safe_actions": list_safe_actions(),
        "ai_brief": ai_brief,
        "operator_question": operator_question,
        "context": context,
    }
    if record_history:
        response["history_record"] = append_trading_supervisor_history(response)

    return response


def build_supervisor_context(asset_id):
    signal = load_asset_latest_signal(asset_id)
    automation = automation_control_status(asset_id)
    orchestrator = trading_orchestrator_status(asset_id)
    forecast_confidence = build_forecast_confidence(asset_id)

    return {
        "asset_id": asset_id,
        "latest_signal": compact_signal(signal),
        "forecast_confidence": compact_forecast_confidence(forecast_confidence),
        "automation_control": compact_automation_control(automation),
        "orchestrator": compact_orchestrator(orchestrator),
        "evidence": build_context_evidence(
            automation=automation,
            orchestrator=orchestrator,
            signal=signal,
        ),
    }


def normalize_evidence_mode(evidence_mode):
    mode = str(evidence_mode or "live").strip().lower()
    if mode in ["mock", "demo", "simulated", "simulation"]:
        return "mock"
    return "live"


def apply_mock_supervisor_mode(context):
    automation = {
        **(context.get("automation_control") or {}),
        "automation_mode": "live_auto_limited",
        "live_trading_allowed": True,
        "paper_trading_allowed": True,
        "supervised_trading_allowed": True,
        "policy_decision": "approved",
        "automation_status": "allowed",
        "readiness_status": "ready",
        "readiness_score": 100,
        "connector_status": "ready",
        "human_gate": {
            "status": "cleared",
            "message": "Mock Data mode uses simulated approval evidence.",
        },
        "mode_escalation": {
            "current_mode": "live_auto_limited",
            "next_eligible_mode": "live_auto_limited",
            "can_escalate": False,
            "escalation_blockers": [],
        },
        "blockers": [],
        "remediation_queue": [],
        "next_automation_action": {
            "action": "continue_live_automation",
            "message": "Mock Data mode has no unresolved blockers; continue simulated live supervision.",
            "owner": "ai_trading_supervisor",
        },
    }
    orchestrator = {
        **(context.get("orchestrator") or {}),
        "status": "ok",
        "orchestrator_status": "running",
        "automation_mode": "live_auto_limited",
        "stage": {
            "stage_id": "simulated_live_supervision",
            "status": "ready",
            "message": "Mock Data mode has a complete simulated execution chain.",
        },
        "next_action": {
            "action": "continue_live_automation",
            "message": "Continue simulated live monitoring.",
        },
        "blockers": [],
    }
    signal = {
        **(context.get("latest_signal") or {}),
        "status": "ok",
        "signal": (context.get("latest_signal") or {}).get("signal") or "ACTION",
        "opportunity_level": (context.get("latest_signal") or {}).get("opportunity_level") or "medium",
    }
    forecast = {
        **(context.get("forecast_confidence") or {}),
        "status": "ok",
        "confidence_score": (context.get("forecast_confidence") or {}).get("confidence_score") or 100,
        "confidence_band": (context.get("forecast_confidence") or {}).get("confidence_band") or "high",
        "automation_eligibility": "eligible",
        "reason": "Mock Data mode uses simulated forecast confidence evidence.",
    }
    evidence = {
        **(context.get("evidence") or {}),
        "mock_supervisor_mode": True,
        "execution_proposal_id": (context.get("evidence") or {}).get("execution_proposal_id") or "mock_proposal_ready",
        "paper_trade_id": (context.get("evidence") or {}).get("paper_trade_id") or "mock_paper_trade_ready",
        "approval_id": (context.get("evidence") or {}).get("approval_id") or "mock_approval_ready",
        "market_submission_id": (context.get("evidence") or {}).get("market_submission_id") or "mock_live_submission_ready",
    }

    return {
        **context,
        "latest_signal": signal,
        "forecast_confidence": forecast,
        "automation_control": automation,
        "orchestrator": orchestrator,
        "evidence": evidence,
    }


def compact_signal(signal):
    summary = (signal.get("data") or {}).get("summary") or {}
    metadata = (signal.get("data") or {}).get("metadata") or {}

    return {
        "status": signal.get("status"),
        "signal": summary.get("signal"),
        "opportunity_level": summary.get("opportunity_level"),
        "total_pnl_eur": summary.get("total_pnl_eur"),
        "profit_per_mw_day": summary.get("profit_per_mw_day"),
        "charge_hours": summary.get("charge_hours"),
        "discharge_hours": summary.get("discharge_hours"),
        "first_charge_timestamp": summary.get("first_charge_timestamp"),
        "first_discharge_timestamp": summary.get("first_discharge_timestamp"),
        "optimizer_engine": metadata.get("optimizer_engine"),
        "generated_at": metadata.get("generated_at"),
    }


def compact_forecast_confidence(forecast_confidence):
    return {
        "status": forecast_confidence.get("status"),
        "confidence_score": forecast_confidence.get("confidence_score"),
        "confidence_band": forecast_confidence.get("confidence_band"),
        "automation_eligibility": forecast_confidence.get("automation_eligibility"),
        "reason": forecast_confidence.get("reason"),
        "run_count": forecast_confidence.get("run_count"),
    }


def compact_automation_control(automation):
    return {
        "status": automation.get("status"),
        "automation_mode": automation.get("automation_mode"),
        "live_trading_allowed": automation.get("live_trading_allowed"),
        "paper_trading_allowed": automation.get("paper_trading_allowed"),
        "supervised_trading_allowed": automation.get("supervised_trading_allowed"),
        "policy_decision": automation.get("policy_decision"),
        "automation_status": automation.get("automation_status"),
        "readiness_status": automation.get("readiness_status"),
        "readiness_score": automation.get("readiness_score"),
        "connector_status": automation.get("connector_status"),
        "primary_market": automation.get("primary_market"),
        "secondary_market": automation.get("secondary_market"),
        "human_gate": automation.get("human_gate"),
        "mode_escalation": compact_mode_escalation(
            automation.get("mode_escalation") or {}
        ),
        "blockers": automation.get("blockers") or [],
        "remediation_queue": automation.get("remediation_queue") or [],
        "next_automation_action": automation.get("next_automation_action") or {},
    }


def compact_mode_escalation(escalation):
    return {
        "current_mode": escalation.get("current_mode"),
        "next_eligible_mode": escalation.get("next_eligible_mode"),
        "can_escalate": escalation.get("can_escalate"),
        "escalation_blockers": escalation.get("escalation_blockers") or [],
    }


def compact_orchestrator(orchestrator):
    return {
        "status": orchestrator.get("status"),
        "orchestrator_status": orchestrator.get("orchestrator_status"),
        "automation_mode": orchestrator.get("automation_mode"),
        "stage": orchestrator.get("stage") or {},
        "next_action": orchestrator.get("next_action") or {},
        "blockers": orchestrator.get("blockers") or [],
    }


def build_context_evidence(automation, orchestrator, signal):
    automation_evidence = automation.get("evidence") or {}
    orchestrator_evidence = orchestrator.get("evidence") or {}
    signal_data = signal.get("data") or {}
    signal_metadata = signal_data.get("metadata") or {}

    return {
        "signal_generated_at": signal_metadata.get("generated_at"),
        "execution_proposal_id": automation_evidence.get("execution_proposal_id"),
        "paper_trade_id": automation_evidence.get("paper_trade_id"),
        "approval_id": automation_evidence.get("approval_id"),
        "market_submission_id": automation_evidence.get("market_submission_id"),
        "automation_policy_id": automation_evidence.get("automation_policy_id"),
        "orchestrator_evidence": orchestrator_evidence,
    }


def detect_supervisor_exceptions(context):
    exceptions = []
    signal = context["latest_signal"]
    forecast = context["forecast_confidence"]
    automation = context["automation_control"]
    orchestrator = context["orchestrator"]

    add_if(
        exceptions,
        condition=signal.get("status") != "ok" or signal.get("signal") != "ACTION",
        severity="warning",
        source="market_intelligence",
        code="NO_ACTION_SIGNAL",
        message="No current ACTION signal is available for automated trade escalation.",
        next_action="Keep automation in monitoring mode until a tradable signal exists.",
    )
    add_if(
        exceptions,
        condition=forecast.get("confidence_band") == "low",
        severity="critical",
        source="forecast_trust",
        code="LOW_FORECAST_CONFIDENCE",
        message=forecast.get("reason")
        or "Forecast confidence is low for automated trading decisions.",
        next_action="Keep live execution blocked and use paper-only validation.",
    )
    add_if(
        exceptions,
        condition=automation.get("automation_status") == "blocked",
        severity="critical",
        source="automation_guardrails",
        code="AUTOMATION_BLOCKED",
        message="Automation guardrails are blocking the trading workflow.",
        next_action="Clear guardrail blockers before escalating beyond advisory or paper mode.",
    )
    add_if(
        exceptions,
        condition=bool(automation.get("blockers")),
        severity="critical",
        source="automation_control",
        code="CONTROL_BLOCKERS_PRESENT",
        message="Automation control has unresolved blockers.",
        next_action="Work through the remediation queue before supervised or live execution.",
        evidence=automation.get("blockers"),
    )
    add_if(
        exceptions,
        condition=automation.get("connector_status") in ["blocked", "not_ready"],
        severity="critical",
        source="market_connector",
        code="CONNECTOR_NOT_READY",
        message="The selected market connector is not ready for production routing.",
        next_action="Keep trading in paper or advisory mode until connector readiness is restored.",
    )
    add_if(
        exceptions,
        condition=(automation.get("human_gate") or {}).get("status") == "required",
        severity="warning",
        source="human_gate",
        code="HUMAN_APPROVAL_REQUIRED",
        message="A human approval gate is required before supervised execution.",
        next_action="Request or complete operator approval for the latest proposal.",
    )
    add_if(
        exceptions,
        condition=not automation.get("live_trading_allowed"),
        severity="info",
        source="automation_mode",
        code="LIVE_EXECUTION_NOT_ALLOWED",
        message="Current automation mode does not permit live market submission.",
        next_action="Continue monitoring or paper trading until escalation evidence is complete.",
    )
    add_if(
        exceptions,
        condition=orchestrator.get("orchestrator_status")
        in ["market_route_blocked", "policy_blocked"],
        severity="critical",
        source="trading_orchestrator",
        code="ORCHESTRATOR_BLOCKED",
        message=(orchestrator.get("stage") or {}).get("message")
        or "The trading orchestrator is blocked.",
        next_action=(orchestrator.get("next_action") or {}).get("message")
        or "Resolve the orchestrator blocker before continuing automation.",
    )

    return exceptions


def add_if(
    exceptions,
    condition,
    severity,
    source,
    code,
    message,
    next_action,
    evidence=None,
):
    if not condition:
        return

    exceptions.append(
        {
            "severity": severity,
            "source": source,
            "code": code,
            "message": message,
            "next_action": next_action,
            "evidence": evidence or [],
        }
    )


def build_supervisor_recommendation(context, exceptions):
    automation = context["automation_control"]
    severity = highest_severity(exceptions)
    action = automation.get("next_automation_action") or {}

    if context.get("evidence", {}).get("mock_supervisor_mode"):
        return recommendation(
            supervisor_status="normal",
            decision="continue_live_automation",
            automation_action=action.get("action") or "continue_live_automation",
            summary="Mock Data mode has a complete simulated execution chain and no material blocker.",
            next_action=action.get("message")
            or "Continue simulated live supervision.",
        )

    if severity == "critical":
        return recommendation(
            supervisor_status="exception",
            decision="hold_live_execution",
            automation_action="pause_or_paper_only",
            summary="Material exceptions require automation to stay out of live execution.",
            next_action=first_next_action(exceptions) or action.get("message"),
        )

    if severity == "warning":
        return recommendation(
            supervisor_status="review",
            decision="continue_with_human_review",
            automation_action=action.get("action") or "monitor_and_reoptimize",
            summary="Automation can continue only with the flagged review item visible.",
            next_action=first_next_action(exceptions) or action.get("message"),
        )

    if automation.get("live_trading_allowed"):
        return recommendation(
            supervisor_status="normal",
            decision="continue_live_automation",
            automation_action=action.get("action") or "monitor_and_reoptimize",
            summary="No material exception blocks the current live automation mode.",
            next_action=action.get("message")
            or "Continue automated monitoring and market event supervision.",
        )

    return recommendation(
        supervisor_status="normal",
        decision="continue_non_live_automation",
        automation_action=action.get("action") or "monitor_and_reoptimize",
        summary="No material exception requires escalation, but live execution is not enabled.",
        next_action=action.get("message")
        or "Continue monitoring, proposal generation, or paper validation.",
    )


def build_daily_supervisor_brief(context, exceptions, recommendation):
    automation = context["automation_control"]
    forecast = context["forecast_confidence"]
    signal = context["latest_signal"]
    evidence = context["evidence"]
    top_exception = exceptions[0] if exceptions else {}

    return {
        "decision": recommendation["decision"],
        "supervisor_status": recommendation["supervisor_status"],
        "top_blocker": top_exception.get("message") or "No material blocker detected.",
        "forecast_confidence": forecast.get("confidence_band"),
        "forecast_score": forecast.get("confidence_score"),
        "market_signal": signal.get("signal"),
        "opportunity_level": signal.get("opportunity_level"),
        "automation_mode": automation.get("automation_mode"),
        "live_trading_allowed": automation.get("live_trading_allowed"),
        "recommended_next_action": recommendation.get("next_action"),
        "evidence_references": {
            "signal_generated_at": evidence.get("signal_generated_at"),
            "execution_proposal_id": evidence.get("execution_proposal_id"),
            "paper_trade_id": evidence.get("paper_trade_id"),
            "approval_id": evidence.get("approval_id"),
            "market_submission_id": evidence.get("market_submission_id"),
        },
    }


def suggested_supervisor_questions(context, exceptions):
    questions = [
        "Why is live execution blocked or allowed right now?",
        "What should I fix first before supervised automation?",
        "Can this asset safely paper trade today?",
        "Which market route is blocking execution?",
        "What evidence is missing for live automation?",
    ]
    if exceptions:
        questions.insert(1, f"Explain the {exceptions[0].get('source')} exception.")

    return questions


def recommendation(
    supervisor_status,
    decision,
    automation_action,
    summary,
    next_action,
):
    return {
        "supervisor_status": supervisor_status,
        "decision": decision,
        "automation_action": automation_action,
        "summary": summary,
        "next_action": next_action,
    }


def highest_severity(exceptions):
    order = {"critical": 3, "warning": 2, "info": 1}
    if not exceptions:
        return "none"

    return max(exceptions, key=lambda item: order.get(item["severity"], 0))["severity"]


def first_next_action(exceptions):
    if not exceptions:
        return None

    return exceptions[0].get("next_action")


def build_ai_brief_if_requested(
    context,
    exceptions,
    include_ai_brief,
    operator_question,
    recommendation,
):
    if not include_ai_brief:
        return {
            "status": "not_requested",
            "brief": None,
            "model": DEFAULT_MODEL,
        }

    if not os.environ.get("OPENAI_API_KEY"):
        return {
            "status": "fallback",
            "brief": build_deterministic_supervisor_brief(
                context=context,
                exceptions=exceptions,
                operator_question=operator_question,
                recommendation=recommendation,
            ),
            "model": DEFAULT_MODEL,
            "message": "OPENAI_API_KEY is not configured; returned deterministic supervisor brief.",
        }

    try:
        brief = asyncio.run(
            generate_trading_supervisor_brief(
                context=context,
                exceptions=exceptions,
                operator_question=operator_question,
                recommendation=recommendation,
            )
        )
        return {
            "status": "generated",
            "brief": brief,
            "model": DEFAULT_MODEL,
        }
    except ImportError:
        return {
            "status": "fallback",
            "brief": build_deterministic_supervisor_brief(
                context=context,
                exceptions=exceptions,
                operator_question=operator_question,
                recommendation=recommendation,
            ),
            "model": DEFAULT_MODEL,
            "message": "openai-agents is not installed; returned deterministic supervisor brief.",
        }
    except Exception as error:
        return {
            "status": "fallback",
            "brief": build_deterministic_supervisor_brief(
                context=context,
                exceptions=exceptions,
                operator_question=operator_question,
                recommendation=recommendation,
            ),
            "model": DEFAULT_MODEL,
            "message": f"AI supervisor brief generation failed; returned deterministic supervisor brief. {error}",
        }


def build_deterministic_supervisor_brief(
    context,
    exceptions,
    operator_question,
    recommendation,
):
    automation = context.get("automation_control") or {}
    forecast = context.get("forecast_confidence") or {}
    signal = context.get("latest_signal") or {}
    top_exception = exceptions[0] if exceptions else {}

    lines = [
        f"Supervisor decision: {recommendation.get('decision')}.",
        recommendation.get("summary") or "No supervisor summary is available.",
        f"Next action: {recommendation.get('next_action') or 'Continue monitoring.'}",
        (
            "Main exception: "
            f"{top_exception.get('message')} "
            f"Action: {top_exception.get('next_action')}"
            if top_exception
            else "Main exception: none currently detected."
        ),
        (
            "Current evidence: "
            f"automation mode {automation.get('automation_mode') or '-'}, "
            f"live allowed {automation.get('live_trading_allowed')}, "
            f"forecast confidence {forecast.get('confidence_band') or '-'} "
            f"({forecast.get('confidence_score') or '-'}), "
            f"latest signal {signal.get('signal') or '-'}."
        ),
    ]

    if operator_question:
        lines.insert(0, f"Question: {operator_question}")

    return "\n\n".join(lines)


async def generate_trading_supervisor_brief(
    context,
    exceptions,
    operator_question,
    recommendation,
):
    from agents import Agent, Runner

    agent = Agent(
        name="AI Trading Supervisor",
        instructions=TRADING_SUPERVISOR_INSTRUCTIONS,
        model=DEFAULT_MODEL,
    )
    payload = {
        "recommendation": recommendation,
        "exceptions": exceptions,
        "operator_question": operator_question,
        "context": context,
    }
    question_instruction = (
        f"\nOperator question: {operator_question}\nAnswer it directly after the supervisor decision."
        if operator_question
        else ""
    )
    result = await Runner.run(
        agent,
        "Create an exception-based trading supervisor brief from this JSON:\n"
        + json.dumps(payload, indent=2, default=str)
        + question_instruction,
    )

    return result.final_output
