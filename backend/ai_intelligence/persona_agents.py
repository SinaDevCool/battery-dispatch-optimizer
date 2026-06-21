import asyncio
import json
import os
from datetime import datetime

from backend.api.routes.forecast_actual import asset_forecast_confidence
from backend.api.routes.regulatory import (
    asset_germany_ancillary_eligibility,
    asset_storage_classification,
)
from backend.api.routes.revenue import (
    asset_hedged_revenue_view,
    latest_asset_revenue_stack,
)
from backend.api.routes.settlement import latest_asset_settlement
from backend.api.routes.summaries import (
    build_asset_execution_summary,
    asset_client_evidence_summary,
    asset_regulatory_summary,
    asset_revenue_summary,
)
from backend.ai_intelligence.mock_evidence_orchestrator import ensure_mock_evidence
from backend.ai_intelligence.priority_gaps import build_priority_gap_analysis
from backend.execution.market_connector_readiness import market_connector_readiness
from backend.services.asset_signal_store import load_asset_latest_signal


DEFAULT_MODEL = os.environ.get("PERSONA_AGENT_MODEL", "gpt-5.5")


PERSONA_AGENT_MAP = {
    "all": "executive_decision_agent",
    "asset_owner": "asset_owner_value_agent",
    "investor_lender": "investor_evidence_agent",
    "project_developer": "project_development_agent",
    "executive": "executive_decision_agent",
    "client_success": "client_success_agent",
    "trading_desk": "trading_supervisor_agent",
    "automation_operator": "automation_operator_agent",
    "risk_compliance": "compliance_audit_agent",
    "market_operations": "market_readiness_agent",
    "forecast_quant": "forecast_trust_agent",
    "revenue_analyst": "revenue_assurance_agent",
}


PERSONA_AGENT_PROFILES = {
    "trading_supervisor_agent": {
        "name": "Trading Desk Agent",
        "primary_question": "What should we do in the market now?",
        "audience": "trader deciding whether to trade, hold, paper trade, or escalate",
        "plain_language_goal": "Turn operational evidence into a short market action call.",
        "decision_type": "trade_hold_escalate",
        "summary_sections": ["execution", "forecast", "revenue"],
    },
    "automation_operator_agent": {
        "name": "Automation Operator Agent",
        "primary_question": "Can automation safely continue or escalate?",
        "audience": "operator responsible for keeping automation controlled and recoverable",
        "plain_language_goal": "Explain whether automation should continue, pause, or stay in paper mode.",
        "decision_type": "automation_escalation",
        "summary_sections": ["execution", "forecast", "market"],
    },
    "compliance_audit_agent": {
        "name": "Compliance & Audit Agent",
        "primary_question": "Can this automated trading decision be approved and defended?",
        "audience": "risk, compliance, or approval owner",
        "plain_language_goal": "Translate gates, approvals, settlement, and policy evidence into defensibility.",
        "decision_type": "approval_defensibility",
        "summary_sections": ["execution", "regulatory", "settlement"],
    },
    "market_readiness_agent": {
        "name": "Market Readiness Agent",
        "primary_question": "Which market routes and connectors are production-ready?",
        "audience": "market operations team preparing exchange and ancillary-service access",
        "plain_language_goal": "Rank go-live readiness and name the missing access evidence.",
        "decision_type": "market_route_readiness",
        "summary_sections": ["market", "regulatory", "execution"],
    },
    "forecast_trust_agent": {
        "name": "Forecast Trust Agent",
        "primary_question": "Can we trust the forecast and optimizer output?",
        "audience": "forecast or quant owner deciding how much model risk to allow",
        "plain_language_goal": "Explain forecast confidence in bid-sizing language.",
        "decision_type": "forecast_trust",
        "summary_sections": ["forecast", "execution", "revenue"],
    },
    "revenue_assurance_agent": {
        "name": "Revenue Assurance Agent",
        "primary_question": "Where is revenue created, blocked, or leaking?",
        "audience": "revenue analyst responsible for explaining value capture and leakage",
        "plain_language_goal": "Show the money story: created value, blocked value, leakage, and what to change.",
        "decision_type": "revenue_assurance",
        "summary_sections": ["revenue", "settlement", "forecast"],
    },
    "asset_owner_value_agent": {
        "name": "Asset Owner Value Agent",
        "primary_question": "Is this asset creating defensible owner value?",
        "audience": "asset owner judging commercial performance and operational trust",
        "plain_language_goal": "Explain whether the asset is creating value that can be defended to owners.",
        "decision_type": "asset_value",
        "summary_sections": ["revenue", "settlement", "client_evidence"],
    },
    "investor_evidence_agent": {
        "name": "Investor Evidence Agent",
        "primary_question": "Is this asset bankable and downside-protected?",
        "audience": "investor or lender evaluating bankability, downside, and evidence quality",
        "plain_language_goal": "Translate technical evidence into a diligence-ready bankability view.",
        "decision_type": "bankability",
        "summary_sections": ["client_evidence", "revenue", "regulatory"],
    },
    "project_development_agent": {
        "name": "Project Development Agent",
        "primary_question": "Is this project commercially ready to build or finance?",
        "audience": "developer deciding whether a project is ready for investment or COD planning",
        "plain_language_goal": "Explain readiness gaps before capital is committed.",
        "decision_type": "development_readiness",
        "summary_sections": ["regulatory", "market", "revenue"],
    },
    "executive_decision_agent": {
        "name": "Executive Decision Agent",
        "primary_question": "What is the portfolio-level decision and top blocker?",
        "audience": "executive who needs the top decision, value signal, and main blocker",
        "plain_language_goal": "Condense platform evidence into a board-level action call.",
        "decision_type": "executive_status",
        "summary_sections": ["execution", "revenue", "client_evidence"],
    },
    "client_success_agent": {
        "name": "Client Success Agent",
        "primary_question": "Is this battery bankable or profitable this month?",
        "audience": "client success owner preparing an explainable client update",
        "plain_language_goal": "Turn evidence into client-ready language and report gaps.",
        "decision_type": "client_report_readiness",
        "summary_sections": ["client_evidence", "settlement", "audit"],
    },
}


PERSONA_VOICE = {
    "asset_owner": {
        "role": "asset owner",
        "opening": "For my owner update",
        "stakeholder": "the owner",
    },
    "investor_lender": {
        "role": "investor or lender",
        "opening": "For my investment view",
        "stakeholder": "the investment committee",
    },
    "project_developer": {
        "role": "project developer",
        "opening": "For my development decision",
        "stakeholder": "the project team",
    },
    "executive": {
        "role": "executive",
        "opening": "For my executive readout",
        "stakeholder": "the leadership team",
    },
    "client_success": {
        "role": "client success lead",
        "opening": "For my client update",
        "stakeholder": "the client",
    },
    "trading_desk": {
        "role": "trader",
        "opening": "For my trading decision",
        "stakeholder": "the trading desk",
    },
    "automation_operator": {
        "role": "automation operator",
        "opening": "For my automation decision",
        "stakeholder": "the operations team",
    },
    "risk_compliance": {
        "role": "risk and compliance owner",
        "opening": "For my approval decision",
        "stakeholder": "risk and compliance",
    },
    "market_operations": {
        "role": "market operations lead",
        "opening": "For my connector plan",
        "stakeholder": "market operations",
    },
    "forecast_quant": {
        "role": "forecast and quant owner",
        "opening": "For my model-risk view",
        "stakeholder": "the quant team",
    },
    "revenue_analyst": {
        "role": "revenue analyst",
        "opening": "For my revenue analysis",
        "stakeholder": "commercial owners",
    },
    "all": {
        "role": "platform operator",
        "opening": "For my platform decision",
        "stakeholder": "the platform team",
    },
}


PERSONA_QUESTIONS = {
    "asset_owner": [
        "What value was created?",
        "What should I tell the owner this week?",
        "What revenue is modelled, demo-proven, or production-ready?",
        "Which production proof should I ask for next?",
    ],
    "investor_lender": [
        "Is this bankable or still mock-backed?",
        "What diligence risk remains?",
        "What proof would make this lender-ready?",
        "What downside evidence is missing?",
    ],
    "project_developer": [
        "Is this project ready for investment planning?",
        "Which assumption blocks development confidence?",
        "What should I validate before COD planning?",
        "What market evidence should I collect next?",
    ],
    "executive": [
        "What should I escalate first?",
        "What is ready for a board update?",
        "Where is the biggest production risk?",
        "What is the next commercial unlock?",
    ],
    "client_success": [
        "Is this battery bankable or profitable this month?",
        "What numbers should I show in the client update?",
        "Which revenue products created the value?",
        "What proof is missing before client reporting?",
    ],
    "trading_desk": [
        "Can I trade, paper trade, or wait?",
        "What market action should I take now?",
        "What blocks supervised live trading?",
        "Should bid sizing be reduced?",
    ],
    "automation_operator": [
        "Can automation continue safely?",
        "What should stay in paper mode?",
        "What control blocks live automation?",
        "What should I rerun after evidence changes?",
    ],
    "risk_compliance": [
        "Can I defend this decision?",
        "What approval evidence is incomplete?",
        "What is mock-ready versus production-ready?",
        "What should stay out of client claims?",
    ],
    "market_operations": [
        "Which connector should I configure first?",
        "What blocks production market access?",
        "What can run in paper mode today?",
        "Which credential unlocks the most evidence?",
    ],
    "forecast_quant": [
        "Can I trust the forecast for bidding?",
        "Should bid sizing be reduced?",
        "What forecast evidence is weak?",
        "What actual-price proof should I refresh?",
    ],
    "revenue_analyst": [
        "Which revenue product creates most value?",
        "Which products were excluded from allocation and why?",
        "What revenue is modelled versus proven?",
        "What is the next highest-value unlock?",
    ],
    "all": [
        "Which production gap should we solve first?",
        "What is mock-ready versus production-ready?",
        "What should we demo now?",
        "What should we build next?",
    ],
}


SECTION_GUIDANCE = {
    "audit": {
        "label": "audit trail",
        "page": "Audit Evidence",
        "route": "/execution/audit",
    },
    "client_evidence": {
        "label": "client evidence pack",
        "page": "Investor Demo or Reports",
        "route": "/investor-demo",
    },
    "execution": {
        "label": "execution readiness",
        "page": "Mission Control",
        "route": "/execution",
    },
    "forecast": {
        "label": "forecast trust",
        "page": "Forecast Trust",
        "route": "/forecasts",
    },
    "hedging": {
        "label": "hedging and downside protection",
        "page": "Hedging",
        "route": "/hedging",
    },
    "market": {
        "label": "market access",
        "page": "Market Access & Data",
        "route": "/execution/market-connectors",
    },
    "regulatory": {
        "label": "regulatory evidence",
        "page": "Regulatory Compliance",
        "route": "/regulation",
    },
    "revenue": {
        "label": "revenue proof",
        "page": "Revenue Assurance",
        "route": "/revenue",
    },
    "revenue_stack": {
        "label": "revenue stack",
        "page": "Revenue Assurance",
        "route": "/revenue",
    },
    "settlement": {
        "label": "settlement proof",
        "page": "Settlement Evidence",
        "route": "/execution/settlement",
    },
    "priority_gaps": {
        "label": "priority evidence gaps",
        "page": "Decision Evidence",
        "route": "/intelligence",
    },
    "storage_classification": {
        "label": "storage classification",
        "page": "Regulatory Compliance",
        "route": "/regulation",
    },
    "ancillary_eligibility": {
        "label": "ancillary-service eligibility",
        "page": "Regulatory Compliance",
        "route": "/regulation",
    },
}


METRIC_LABELS = {
    "approval_status": "approval status",
    "blocked_product_count": "blocked revenue products",
    "blocker_count": "open blockers",
    "credential_blocked_route_count": "market routes blocked by credentials",
    "credential_ready_route_count": "market routes with credentials ready",
    "eligible_product_count": "eligible products",
    "evidence_score": "evidence score",
    "modelled_revenue_eur": "modelled revenue",
    "open_gap_count": "open evidence gaps",
    "product_count": "total products checked",
    "readiness_score": "readiness score",
    "readiness_status": "readiness status",
    "review_product_count": "products needing review",
    "settlement_available": "settlement available",
    "total_estimated_revenue_eur": "estimated revenue",
}


def list_persona_agents():
    agents = []
    for agent_id, profile in PERSONA_AGENT_PROFILES.items():
        personas = [
            persona_id
            for persona_id, mapped_agent_id in PERSONA_AGENT_MAP.items()
            if mapped_agent_id == agent_id
        ]
        agents.append(
            {
                "agent_id": agent_id,
                **profile,
                "personas": personas,
            }
        )

    return {
        "status": "ok",
        "agent_count": len(agents),
        "agents": agents,
        "persona_agent_map": PERSONA_AGENT_MAP,
    }


def build_persona_agent_status(
    asset_id,
    persona_id,
    include_ai_brief=False,
    operator_question=None,
    evidence_mode="live",
):
    agent_id = PERSONA_AGENT_MAP.get(persona_id, PERSONA_AGENT_MAP["all"])
    profile = PERSONA_AGENT_PROFILES[agent_id]
    question_intent = classify_question_intent(operator_question or profile["primary_question"])
    mock_evidence = None
    if normalize_evidence_mode(evidence_mode) == "mock":
        mock_evidence = ensure_mock_evidence(
            asset_id=asset_id,
            question_intent=question_intent,
        )
    context = build_persona_context(
        asset_id=asset_id,
        evidence_mode=evidence_mode,
        profile=profile,
    )
    if mock_evidence:
        context["mock_evidence"] = mock_evidence
    decision = build_persona_decision(
        agent_id=agent_id,
        context=context,
        operator_question=operator_question,
        persona_id=persona_id,
        profile=profile,
    )
    ai_brief = build_persona_ai_brief_if_requested(
        context=context,
        decision=decision,
        include_ai_brief=include_ai_brief,
        operator_question=operator_question,
        persona_id=persona_id,
        profile=profile,
    )

    return {
        "status": "ok",
        "asset_id": asset_id,
        "evidence_mode": context.get("priority_gaps", {}).get("evidence_mode", evidence_mode),
        "persona_id": persona_id,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "agent": {
            "agent_id": agent_id,
            "name": profile["name"],
            "primary_question": profile["primary_question"],
            "decision_type": profile["decision_type"],
            "llm_model": DEFAULT_MODEL,
        },
        "decision": decision,
        "ai_brief": ai_brief,
        "suggested_questions": build_persona_questions(
            agent_id=agent_id,
            profile=profile,
            persona_id=persona_id,
        ),
        "context": context,
    }


def build_persona_context(asset_id, profile, evidence_mode="live"):
    sections = profile["summary_sections"]
    context = {}

    if "execution" in sections or "audit" in sections:
        context["execution"] = safe_section(
            "execution",
            lambda: build_asset_execution_summary(asset_id, include_details=False),
        )
    if "revenue" in sections:
        context["revenue"] = safe_section("revenue", lambda: asset_revenue_summary(asset_id))
        context["revenue_stack"] = safe_section(
            "revenue_stack",
            lambda: latest_asset_revenue_stack(asset_id),
        )
        context["hedging"] = safe_section(
            "hedging",
            lambda: asset_hedged_revenue_view(asset_id),
        )
    if "forecast" in sections:
        context["forecast"] = safe_section(
            "forecast",
            lambda: asset_forecast_confidence(asset_id),
        )
        context["signal"] = safe_section(
            "signal",
            lambda: load_asset_latest_signal(asset_id),
        )
    if "settlement" in sections:
        context["settlement"] = safe_section(
            "settlement",
            lambda: latest_asset_settlement(asset_id),
        )
    if "regulatory" in sections:
        context["regulatory"] = safe_section(
            "regulatory",
            lambda: asset_regulatory_summary(asset_id),
        )
        context["storage_classification"] = safe_section(
            "storage_classification",
            lambda: asset_storage_classification(asset_id),
        )
        context["ancillary_eligibility"] = safe_section(
            "ancillary_eligibility",
            lambda: asset_germany_ancillary_eligibility(asset_id),
        )
    if "market" in sections:
        context["market"] = safe_section(
            "market",
            lambda: market_connector_readiness(country="Germany", asset_id=asset_id),
        )
    if "client_evidence" in sections:
        context["client_evidence"] = safe_section(
            "client_evidence",
            lambda: asset_client_evidence_summary(asset_id),
        )
    context["priority_gaps"] = safe_section(
        "priority_gaps",
        lambda: build_priority_gap_analysis(asset_id, evidence_mode=evidence_mode),
    )

    return context


def normalize_evidence_mode(evidence_mode):
    mode = str(evidence_mode or "live").strip().lower()
    return "mock" if mode in {"mock", "demo", "simulated", "simulation"} else "live"


def safe_section(name, loader):
    try:
        return loader()
    except Exception as error:
        return {
            "status": "error",
            "section": name,
            "message": str(error),
        }


def build_persona_decision(agent_id, context, operator_question, persona_id, profile):
    intent = classify_question_intent(operator_question)
    voice = persona_voice(persona_id)
    blockers = collect_blockers(context)
    evidence = collect_evidence(context)
    missing_evidence = collect_missing_evidence(context, blockers)
    relevant_pages = collect_relevant_pages(context, blockers)
    if is_mock_evidence_context(context):
        blockers = []
        missing_evidence = []
        relevant_pages = []
    score = calculate_persona_score(agent_id=agent_id, blockers=blockers, context=context)
    severity = score_status(score)
    decision = persona_decision_label(agent_id=agent_id, blockers=blockers)
    narrative = build_persona_narrative(
        agent_id=agent_id,
        blockers=blockers,
        context=context,
        evidence=evidence,
        profile=profile,
        score=score,
    )

    decision_payload = {
        "decision": decision,
        "status": severity,
        "score": score,
        "score_label": score_label(score),
        "business_question": profile["primary_question"],
        "question_intent": intent,
        "persona_voice": voice,
        "audience": profile["audience"],
        "summary": build_persona_summary(
            agent_id=agent_id,
            blockers=blockers,
            context=context,
            profile=profile,
            score=score,
        ),
        "human_answer": narrative["human_answer"],
        "what_it_means": narrative["what_it_means"],
        "business_value": narrative["business_value"],
        "top_blocker": blockers[0] if blockers else "No material blocker detected in selected evidence.",
        "next_action": build_persona_next_action(agent_id=agent_id, blockers=blockers),
        "recommended_actions": narrative["recommended_actions"],
        "explainability": narrative["explainability"],
        "priority_intelligence": build_priority_intelligence_summary(context),
        "forecast_optimizer_evidence": build_forecast_optimizer_evidence(context),
        "mock_evidence_completeness": context.get("mock_evidence"),
        "missing_evidence": missing_evidence[:8],
        "relevant_pages": relevant_pages[:5],
        "answer_sections": build_answer_sections(
            blockers=blockers,
            evidence=evidence,
            missing_evidence=missing_evidence,
            relevant_pages=relevant_pages,
            score=score,
        ),
        "placeholder_calculations": build_placeholder_calculations(
            agent_id=agent_id,
            blockers=blockers,
            context=context,
            score=score,
        ),
        "blockers": blockers[:8],
        "evidence": evidence[:8],
        "operator_question": operator_question,
        "persona_id": persona_id,
    }
    decision_payload["structured_answer"] = build_structured_answer(decision_payload)
    return decision_payload


def is_mock_evidence_context(context):
    priority = context.get("priority_gaps") or {}
    return priority.get("evidence_mode") == "mock"


def build_forecast_optimizer_evidence(context):
    forecast = context.get("forecast") or {}
    signal_response = context.get("signal") or {}
    signal = signal_response.get("data") or {}
    signal_summary = signal.get("summary") or {}
    optimization = signal.get("optimization") or {}
    validation = signal.get("validation") or {}
    dispatch = signal.get("dispatch") or []
    forecast_evidence = forecast.get("evidence") or []
    latest_run = forecast_evidence[0] if forecast_evidence else {}
    risk_policy = forecast.get("risk_policy") or {}
    active_intervals = len([
        row for row in dispatch
        if str(row.get("action", "idle")).lower() != "idle"
    ])
    charge_intervals = len([
        row for row in dispatch
        if str(row.get("action", "")).lower() == "charge"
    ])
    discharge_intervals = len([
        row for row in dispatch
        if str(row.get("action", "")).lower() == "discharge"
    ])
    throughput = (
        numeric(signal_summary.get("throughput_mwh"))
        or numeric(signal_summary.get("charged_mwh"))
        + numeric(signal_summary.get("discharged_mwh"))
    )

    return {
        "forecast_status": forecast.get("status"),
        "confidence_score": forecast.get("confidence_score"),
        "confidence_band": forecast.get("confidence_band"),
        "automation_eligibility": forecast.get("automation_eligibility"),
        "run_count": forecast.get("run_count"),
        "volume_multiplier": risk_policy.get("volume_multiplier"),
        "price_buffer_eur_per_mwh": risk_policy.get("price_buffer_eur_per_mwh"),
        "latest_mae_eur_per_mwh": latest_run.get("mae_eur_per_mwh"),
        "latest_rmse_eur_per_mwh": latest_run.get("rmse_eur_per_mwh"),
        "latest_revenue_delta_eur": latest_run.get("revenue_delta_eur"),
        "optimizer_engine": optimization.get("optimizer_engine"),
        "signal": signal_summary.get("signal"),
        "opportunity_level": signal_summary.get("opportunity_level"),
        "expected_pnl_eur": signal_summary.get("total_pnl_eur"),
        "profit_per_mw_day": signal_summary.get("profit_per_mw_day"),
        "charged_mwh": signal_summary.get("charged_mwh"),
        "discharged_mwh": signal_summary.get("discharged_mwh"),
        "throughput_mwh": round(throughput, 3),
        "active_intervals": active_intervals,
        "charge_intervals": charge_intervals,
        "discharge_intervals": discharge_intervals,
        "validation_status": validation.get("status"),
        "validation_errors": validation.get("error_count"),
        "validation_warnings": validation.get("warning_count"),
    }


def build_structured_answer(decision):
    intent = decision.get("question_intent") or "general_persona_answer"
    builders = {
        "forecast_optimizer_trust": structured_forecast_optimizer_answer,
        "revenue_opportunity": structured_revenue_opportunity_answer,
        "settlement_explanation": structured_settlement_answer,
        "production_gap_prioritization": structured_production_gap_answer,
        "connector_onboarding": structured_connector_answer,
        "stakeholder_update": structured_stakeholder_update_answer,
    }
    builder = builders.get(intent, structured_general_answer)
    answer = builder(decision)
    answer["intent"] = intent
    answer["audience"] = decision.get("audience")
    answer["persona_id"] = decision.get("persona_id")
    answer["score"] = decision.get("score")
    answer["score_label"] = decision.get("score_label")
    answer["evidence_completeness"] = structured_evidence_completeness(decision)
    return answer


def structured_forecast_optimizer_answer(decision):
    evidence = decision.get("forecast_optimizer_evidence") or {}
    confidence_score = numeric(evidence.get("confidence_score"))
    validation_status = evidence.get("validation_status") or "-"
    trust_decision = (
        "trust_for_supervised_sizing"
        if confidence_score >= 80 and validation_status in ["pass", "passed", "-"]
        else "trust_with_reduced_sizing"
        if confidence_score >= 60
        else "paper_only"
    )
    return {
        "answer_type": "forecast_optimizer_trust",
        "short_answer": (
            "Forecast and optimizer output are strong enough for supervised sizing."
            if trust_decision == "trust_for_supervised_sizing"
            else "Forecast can be used, but bid sizing should be reduced."
            if trust_decision == "trust_with_reduced_sizing"
            else "Forecast is not strong enough for normal bid sizing."
        ),
        "trust_decision": trust_decision,
        "kpis": {
            "confidence_score": evidence.get("confidence_score"),
            "confidence_band": evidence.get("confidence_band"),
            "mae_eur_per_mwh": evidence.get("latest_mae_eur_per_mwh"),
            "rmse_eur_per_mwh": evidence.get("latest_rmse_eur_per_mwh"),
            "revenue_delta_eur": evidence.get("latest_revenue_delta_eur"),
            "expected_pnl_eur": evidence.get("expected_pnl_eur"),
            "active_intervals": evidence.get("active_intervals"),
            "throughput_mwh": evidence.get("throughput_mwh"),
        },
        "bid_sizing": {
            "volume_multiplier": evidence.get("volume_multiplier"),
            "price_buffer_eur_per_mwh": evidence.get("price_buffer_eur_per_mwh"),
            "recommendation": forecast_sizing_call(
                confidence_score=confidence_score,
                volume_multiplier=evidence.get("volume_multiplier"),
                validation_status=validation_status,
            ),
        },
        "optimizer_output": {
            "optimizer_engine": evidence.get("optimizer_engine"),
            "signal": evidence.get("signal"),
            "opportunity_level": evidence.get("opportunity_level"),
            "charge_intervals": evidence.get("charge_intervals"),
            "discharge_intervals": evidence.get("discharge_intervals"),
            "validation_status": validation_status,
            "validation_errors": evidence.get("validation_errors"),
            "validation_warnings": evidence.get("validation_warnings"),
        },
        "source_pages": [
            {"label": "Forecast Trust", "route": "/forecasts"},
            {"label": "Market Signals", "route": "/market-signals"},
        ],
    }


def structured_revenue_opportunity_answer(decision):
    priority = decision.get("priority_intelligence") or {}
    revenue = priority.get("revenue_opportunities") or {}
    settlement = priority.get("settlement_explainer") or {}
    rows = revenue.get("rows") or []
    total_visible = sum(numeric(row.get("estimated_revenue_eur")) for row in rows)
    total_allocated = sum(numeric(row.get("allocated_revenue_eur")) for row in rows)
    excluded = [row for row in rows if row.get("allocation_status") == "excluded"]
    excluded_value = sum(numeric(row.get("estimated_revenue_eur")) for row in excluded)
    top = revenue.get("highest_value_product") or (rows[0] if rows else {})
    return {
        "answer_type": "revenue_opportunity",
        "short_answer": (
            "The asset is profitable in the current evidence pack."
            if total_visible > 0 and (total_allocated > 0 or numeric(settlement.get("expected_pnl_eur")) > 0)
            else "The asset does not yet show enough positive value."
        ),
        "bankability_call": (
            "bankable_for_first_review"
            if total_visible > 0 and decision.get("score", 0) >= 75
            else "not_bankable_yet"
        ),
        "kpis": {
            "total_visible_revenue_eur": round(total_visible, 2),
            "allocated_revenue_eur": round(total_allocated, 2),
            "excluded_revenue_eur": round(excluded_value, 2),
            "expected_pnl_eur": settlement.get("expected_pnl_eur"),
            "paper_pnl_eur": settlement.get("paper_pnl_eur"),
        },
        "top_product": top,
        "product_rows": rows[:8],
        "source_pages": [
            {"label": "Revenue Assurance", "route": "/revenue"},
            {"label": "Settlement Evidence", "route": "/execution/settlement"},
        ],
    }


def structured_settlement_answer(decision):
    settlement = (decision.get("priority_intelligence") or {}).get("settlement_explainer") or {}
    return {
        "answer_type": "settlement_explanation",
        "short_answer": settlement.get("short_answer") or "Settlement evidence is not loaded yet.",
        "kpis": {
            "expected_pnl_eur": settlement.get("expected_pnl_eur"),
            "paper_pnl_eur": settlement.get("paper_pnl_eur"),
            "realized_pnl_eur": settlement.get("realized_pnl_eur"),
            "paper_delta_eur": settlement.get("paper_delta_eur"),
        },
        "variance_explanation": settlement.get("human_variance_explanation"),
        "production_record_needed": settlement.get("production_record_needed") or [],
        "next_action": settlement.get("next_action"),
        "source_pages": [{"label": "Settlement Evidence", "route": "/execution/settlement"}],
    }


def structured_production_gap_answer(decision):
    priority = decision.get("priority_intelligence") or {}
    gaps = priority.get("gaps") or []
    open_gaps = [gap for gap in gaps if gap.get("status") != "ready"]
    first_gap = choose_first_production_gap(open_gaps)
    return {
        "answer_type": "production_gap_prioritization",
        "short_answer": (
            "No mock evidence gap is open."
            if priority.get("evidence_mode") == "mock"
            else (first_gap or {}).get("title") or "No production gap detected."
        ),
        "top_gap": first_gap,
        "open_gap_count": len(open_gaps),
        "ready_domain_count": (priority.get("summary") or {}).get("ready_domain_count"),
        "domains": gaps,
        "source_pages": [{"label": "Decision Evidence", "route": "/intelligence"}],
    }


def structured_connector_answer(decision):
    onboarding = (decision.get("priority_intelligence") or {}).get("connector_onboarding") or {}
    rows = onboarding.get("rows") or []
    first = rows[0] if rows else {}
    return {
        "answer_type": "connector_onboarding",
        "short_answer": f"Configure {first.get('adapter_name', 'the first blocked connector')} first.",
        "first_connector": first,
        "connector_rows": rows,
        "source_pages": [{"label": "Market Access & Data", "route": "/execution/market-connectors"}],
    }


def structured_stakeholder_update_answer(decision):
    priority = decision.get("priority_intelligence") or {}
    summary = priority.get("summary") or {}
    return {
        "answer_type": "stakeholder_update",
        "short_answer": (
            "Mock evidence is ready for a client-style walkthrough."
            if priority.get("evidence_mode") == "mock"
            else summary.get("business_answer", "Current evidence is ready for review.")
        ),
        "safe_to_say": summary.get("business_answer"),
        "avoid_overclaiming": (
            "Do not claim production-live status from Mock Data mode."
            if priority.get("evidence_mode") == "mock"
            else "Do not overclaim missing production connectors or records."
        ),
        "proof_to_show": priority.get("evidence_modes") or [],
        "source_pages": [{"label": "Reports", "route": "/reports"}],
    }


def structured_general_answer(decision):
    return {
        "answer_type": "general_persona_answer",
        "short_answer": decision.get("human_answer"),
        "recommended_actions": decision.get("recommended_actions") or [],
        "source_pages": decision.get("relevant_pages") or [],
    }


def structured_evidence_completeness(decision):
    mock = decision.get("mock_evidence_completeness") or {}
    if not mock:
        return {
            "mode": "live_or_not_applicable",
            "available_count": None,
            "required_count": None,
            "missing": [],
            "generated_steps": [],
        }
    return {
        "mode": "mock",
        "status": mock.get("status"),
        "available_count": mock.get("available_count"),
        "required_count": mock.get("required_count"),
        "missing_count": mock.get("missing_count"),
        "missing": mock.get("missing_steps") or [],
        "generated_steps": mock.get("generated_steps") or [],
    }


def calculate_persona_score(agent_id, blockers, context):
    base = 88
    base -= min(len(blockers) * 8, 56)

    score_adjustments = {
        "investor_evidence_agent": evidence_score_adjustment(context),
        "revenue_assurance_agent": revenue_score_adjustment(context),
        "market_readiness_agent": market_score_adjustment(context),
        "compliance_audit_agent": compliance_score_adjustment(context),
        "forecast_trust_agent": forecast_score_adjustment(context),
        "automation_operator_agent": automation_score_adjustment(context),
        "trading_supervisor_agent": trading_score_adjustment(context),
    }

    return max(0, min(100, round(base + score_adjustments.get(agent_id, 0))))


def score_status(score):
    if score >= 75:
        return "ready"
    if score >= 50:
        return "review"
    return "blocked"


def score_label(score):
    if score >= 75:
        return "Strong"
    if score >= 50:
        return "Needs review"
    return "Blocked"


def nested_get(mapping, path, default=None):
    current = mapping
    for key in path:
        if not isinstance(current, dict):
            return default
        current = current.get(key)
    return current if current is not None else default


def evidence_score_adjustment(context):
    summary = nested_get(context, ["client_evidence", "summary"], {})
    if not isinstance(summary, dict):
        return -8
    blockers = numeric(summary.get("blocker_count") or summary.get("open_gap_count"))
    return -10 if blockers else 6


def revenue_score_adjustment(context):
    total = nested_get(context, ["revenue_stack", "total_estimated_revenue_eur"], 0)
    blocked = nested_get(context, ["revenue", "summary", "blocked_product_count"], 0)
    adjustment = 8 if numeric(total) > 0 else -8
    adjustment -= min(numeric(blocked) * 6, 18)
    return adjustment


def market_score_adjustment(context):
    summary = nested_get(context, ["market", "summary"], {})
    if not isinstance(summary, dict):
        return -8
    blocked = numeric(summary.get("credential_blocked_route_count") or summary.get("blocked_route_count"))
    ready = numeric(summary.get("credential_ready_route_count") or summary.get("ready_route_count"))
    return min(ready * 5, 10) - min(blocked * 7, 28)


def compliance_score_adjustment(context):
    summary = nested_get(context, ["execution", "summary"], {})
    settlement_status = nested_get(context, ["settlement", "status"], None)
    adjustment = 0
    if isinstance(summary, dict) and summary.get("approval_status") in ["approved", "passed"]:
        adjustment += 6
    if settlement_status in ["ok", "ready"]:
        adjustment += 4
    return adjustment


def forecast_score_adjustment(context):
    score = numeric(nested_get(context, ["forecast", "confidence_score"], 0))
    if score >= 80:
        return 10
    if score >= 60:
        return 2
    if score > 0:
        return -12
    return -8


def automation_score_adjustment(context):
    mode = nested_get(context, ["execution", "summary", "automation_mode"], "")
    if mode == "live_auto_limited":
        return 10
    if mode in ["supervised_auto", "paper_trading"]:
        return 2
    return -8


def trading_score_adjustment(context):
    revenue = numeric(nested_get(context, ["revenue_stack", "total_estimated_revenue_eur"], 0))
    forecast = forecast_score_adjustment(context)
    return (8 if revenue > 0 else -4) + forecast


def numeric(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def build_persona_narrative(agent_id, blockers, context, evidence, profile, score):
    builder = PERSONA_NARRATIVE_BUILDERS.get(agent_id, generic_narrative)
    return builder(
        blockers=blockers,
        context=context,
        evidence=evidence,
        profile=profile,
        score=score,
    )


def generic_narrative(blockers, context, evidence, profile, score):
    ready = score >= 75
    return {
        "human_answer": (
            "Yes, the selected evidence is strong enough for the next review step."
            if ready
            else "Not yet. The evidence points to a review step before this should be treated as ready."
        ),
        "what_it_means": profile["plain_language_goal"],
        "business_value": "This agent turns backend status into a decision a business owner can act on.",
        "recommended_actions": build_action_list(blockers, "Continue with the next evidence review."),
        "explainability": build_explainability(evidence, blockers),
    }


def investor_narrative(blockers, context, evidence, profile, score):
    return {
        "human_answer": (
            "The asset is not yet fully bankable. It has a revenue story, but the evidence still needs stronger proof before an investor or lender should rely on it."
            if score < 75
            else "The asset has a defendable bankability story for a first investor review."
        ),
        "what_it_means": (
            "For an investor, the key question is not whether the optimizer can produce a schedule. "
            "It is whether revenue, downside protection, regulation, settlement, and audit evidence are coherent enough to support financing."
        ),
        "business_value": "Helps turn technical dispatch outputs into a diligence-ready investment memo.",
        "recommended_actions": build_action_list(
            blockers,
            "Package the revenue, downside, and audit evidence into an investor memo.",
        ),
        "explainability": build_explainability(evidence, blockers),
    }


def revenue_narrative(blockers, context, evidence, profile, score):
    total = nested_get(context, ["revenue_stack", "total_estimated_revenue_eur"], None)
    return {
        "human_answer": (
            f"The platform shows estimated revenue of {total} EUR, but the agent still sees evidence gaps that can hide leakage."
            if blockers
            else f"The current revenue evidence is coherent, with estimated revenue of {total} EUR and no material blocker in the selected evidence."
        ),
        "what_it_means": (
            "This separates value creation from value capture: expected arbitrage revenue is useful only when forecast, execution, and settlement evidence agree."
        ),
        "business_value": "Helps asset owners understand whether money was made, missed, or merely modelled.",
        "recommended_actions": build_action_list(
            blockers,
            "Use the revenue stack and settlement evidence in the next owner value report.",
        ),
        "explainability": build_explainability(evidence, blockers),
    }


def market_narrative(blockers, context, evidence, profile, score):
    return {
        "human_answer": (
            "Market access is not production-ready yet. The likely blockers are credentials, route readiness, or prequalification evidence."
            if blockers
            else "The selected market evidence is ready for the next go-live review."
        ),
        "what_it_means": (
            "The asset may have a good trading signal, but it cannot be called production-ready until the exchange route, credentials, connector, and market rules are proven."
        ),
        "business_value": "Turns market integration work into a ranked go-live checklist.",
        "recommended_actions": build_action_list(
            blockers,
            "Prepare the route-readiness pack for EPEX and ancillary-service review.",
        ),
        "explainability": build_explainability(evidence, blockers),
    }


def compliance_narrative(blockers, context, evidence, profile, score):
    return {
        "human_answer": (
            "This decision should not be treated as approval-defensible yet. The evidence trail still has gaps."
            if blockers
            else "This decision is defensible enough for the next approval review."
        ),
        "what_it_means": (
            "Compliance cares less about the raw trading upside and more about whether the decision can be reconstructed: policy, human gate, audit, settlement, and rule assumptions."
        ),
        "business_value": "Reduces enterprise risk by making automated trading explainable before escalation.",
        "recommended_actions": build_action_list(
            blockers,
            "Prepare a compact approval packet with policy, human gate, settlement, and audit references.",
        ),
        "explainability": build_explainability(evidence, blockers),
    }


def forecast_narrative(blockers, context, evidence, profile, score):
    confidence = nested_get(context, ["forecast", "confidence_band"], "unknown")
    confidence_score = nested_get(context, ["forecast", "confidence_score"], "-")
    return {
        "human_answer": (
            f"Forecast confidence is {confidence} ({confidence_score}). Bid sizing should stay conservative until the evidence improves."
            if score < 75
            else f"Forecast confidence is {confidence} ({confidence_score}); it is strong enough for normal supervised sizing."
        ),
        "what_it_means": (
            "The forecast is being judged by whether it deserves trading risk, not by whether it merely exists as a file."
        ),
        "business_value": "Connects model quality directly to bid sizing and automation eligibility.",
        "recommended_actions": build_action_list(
            blockers,
            "Run forecast-vs-actual checks and adjust bid size based on confidence.",
        ),
        "explainability": build_explainability(evidence, blockers),
    }


def owner_narrative(blockers, context, evidence, profile, score):
    return {
        "human_answer": (
            "The asset has a value story, but it is not yet fully defensible for an owner update."
            if blockers
            else "The asset value story is defensible for an owner update."
        ),
        "what_it_means": (
            "An owner needs a clean explanation of revenue, operational maturity, settlement proof, and the next blocker, not raw backend statuses."
        ),
        "business_value": "Makes asset performance explainable to commercial owners.",
        "recommended_actions": build_action_list(
            blockers,
            "Prepare an owner-facing value summary with top blocker and next action.",
        ),
        "explainability": build_explainability(evidence, blockers),
    }


def client_success_narrative(blockers, context, evidence, profile, score):
    return {
        "human_answer": (
            "Do not send a polished client report yet; explain the open evidence gaps first."
            if blockers
            else "This is ready for a client-facing update."
        ),
        "what_it_means": (
            "Client success needs language that explains what happened, what is proven, what is still mock/paper, and what will be fixed next."
        ),
        "business_value": "Shortens reporting work and prevents overclaiming production readiness.",
        "recommended_actions": build_action_list(
            blockers,
            "Draft a client update that separates proven evidence from remaining gaps.",
        ),
        "explainability": build_explainability(evidence, blockers),
    }


PERSONA_NARRATIVE_BUILDERS = {
    "investor_evidence_agent": investor_narrative,
    "revenue_assurance_agent": revenue_narrative,
    "market_readiness_agent": market_narrative,
    "compliance_audit_agent": compliance_narrative,
    "forecast_trust_agent": forecast_narrative,
    "asset_owner_value_agent": owner_narrative,
    "client_success_agent": client_success_narrative,
}


def build_action_list(blockers, fallback):
    if blockers:
        return [
            f"Resolve first: {blockers[0]}",
            "Re-run the persona agent after the evidence changes.",
            "Keep the explanation in review language until the blocker is cleared.",
        ]

    return [fallback, "Keep the evidence trail current before the next decision."]


def build_explainability(evidence, blockers):
    return {
        "plain_language_basis": evidence[:5],
        "why_not_ready": blockers[:5],
        "note": (
            "Some scoring is intentionally heuristic until deeper backend calculation "
            "modules are added. The agent labels those values as placeholder calculations."
        ),
    }


def build_placeholder_calculations(agent_id, blockers, context, score):
    return {
        "score": score,
        "score_status": score_status(score),
        "blocker_penalty": min(len(blockers) * 8, 56),
        "method": (
            "Heuristic persona score using available backend evidence. This is a "
            "temporary explainability layer until dedicated financial/readiness models "
            "are added."
        ),
        "future_backend_needed": future_backend_calculation(agent_id),
    }


def future_backend_calculation(agent_id):
    mapping = {
        "investor_evidence_agent": "Dedicated bankability model with DSCR-style downside, contracted revenue, and lender diligence weights.",
        "revenue_assurance_agent": "Expected-vs-realized revenue attribution across price, dispatch deviation, fees, imbalance, and settlement.",
        "market_readiness_agent": "Formal market-route readiness scoring by product, credential, prequalification, connector, and telemetry evidence.",
        "compliance_audit_agent": "Approval defensibility score with policy controls, human gates, audit chain completeness, and regulatory assumptions.",
        "forecast_trust_agent": "Interval-level forecast confidence and bid-sizing adjustment model.",
    }

    return mapping.get(agent_id, "Persona-specific scoring model backed by domain data tables.")


def build_priority_intelligence_summary(context):
    priority = context.get("priority_gaps") or {}
    return {
        "evidence_mode": priority.get("evidence_mode", "live"),
        "summary": priority.get("summary") or {},
        "gaps": priority.get("gaps") or [],
        "evidence_modes": priority.get("evidence_modes") or [],
        "revenue_opportunities": priority.get("revenue_opportunities") or {},
        "settlement_explainer": priority.get("settlement_explainer") or {},
        "connector_onboarding": priority.get("connector_onboarding") or {},
        "persona_playbooks": priority.get("persona_playbooks") or [],
    }


def collect_missing_evidence(context, blockers):
    missing = []

    for section_name, section in context.items():
        if not isinstance(section, dict):
            continue

        guidance = section_guidance(section_name)
        status = section.get("status")
        if status in ["partial", "review", "missing", "not_found", "invalid", "error"]:
            missing.append(
                missing_evidence_item(
                    section_name=section_name,
                    message=section.get("message")
                    or f"{guidance['label']} is marked {status}, so it is not complete enough to rely on alone.",
                )
            )

        summary = section.get("summary") or {}
        if isinstance(summary, dict):
            for key, value in summary.items():
                count = numeric(value)
                if count <= 0:
                    continue
                if "blocked" in key:
                    missing.append(
                        missing_evidence_item(
                            section_name=section_name,
                            message=human_metric_sentence(section_name, key, value, "blocked"),
                        )
                    )
                elif "missing" in key or "open_gap" in key:
                    missing.append(
                        missing_evidence_item(
                            section_name=section_name,
                            message=human_metric_sentence(section_name, key, value, "missing"),
                        )
                    )
                elif "review" in key:
                    missing.append(
                        missing_evidence_item(
                            section_name=section_name,
                            message=human_metric_sentence(section_name, key, value, "review"),
                        )
                    )

        for key in ["blockers", "exceptions", "missing_required", "open_gaps", "gaps"]:
            rows = section.get(key)
            if isinstance(rows, list):
                for row in rows[:3]:
                    missing.append(
                        missing_evidence_item(
                            section_name=section_name,
                            message=human_row_message(row),
                        )
                    )

    if not missing and blockers:
        for blocker in blockers[:5]:
            section_name = str(blocker).split(":", 1)[0]
            missing.append(
                missing_evidence_item(section_name=section_name, message=str(blocker))
            )

    return dedupe_structured(missing, "message")


def missing_evidence_item(section_name, message):
    guidance = section_guidance(section_name)
    return {
        "section": section_name,
        "label": guidance["label"],
        "message": clean_sentence(message),
        "page": guidance["page"],
        "route": guidance["route"],
    }


def collect_relevant_pages(context, blockers):
    section_names = set()

    for item in blockers:
        possible_section = str(item).split(":", 1)[0]
        if possible_section in SECTION_GUIDANCE:
            section_names.add(possible_section)

    for section_name, section in context.items():
        if not isinstance(section, dict):
            continue
        if section.get("status") in ["partial", "review", "missing", "blocked", "error", "not_found", "invalid"]:
            section_names.add(section_name)
        summary = section.get("summary") or {}
        if isinstance(summary, dict):
            for key, value in summary.items():
                if numeric(value) > 0 and any(token in key for token in ["blocked", "missing", "open_gap", "review"]):
                    section_names.add(section_name)

    if not section_names:
        section_names = set(context.keys())

    pages = []
    for section_name in section_names:
        guidance = section_guidance(section_name)
        pages.append(
            {
                "section": section_name,
                "label": guidance["label"],
                "page": guidance["page"],
                "route": guidance["route"],
            }
        )

    return dedupe_structured(pages, "route")


def build_answer_sections(blockers, evidence, missing_evidence, relevant_pages, score):
    if missing_evidence:
        short_answer = (
            "Not all evidence is complete yet. The biggest gap is: "
            f"{missing_evidence[0]['message']}"
        )
    elif score >= 75:
        short_answer = "The selected evidence is strong enough for the next business review."
    else:
        short_answer = "The answer is not fully proven from the evidence currently available."

    if missing_evidence:
        page = missing_evidence[0]
        fallback = (
            f"For product-level detail, open {page['page']} ({page['route']}). "
            "That page is the best source if you need the underlying rows."
        )
    elif relevant_pages:
        page = relevant_pages[0]
        fallback = (
            f"For product-level detail, open {page['page']} ({page['route']}). "
            "That page is the best source if you need the underlying rows."
        )
    else:
        fallback = (
            "If you need more detail, check the page that owns the underlying evidence "
            "before treating this as final."
        )

    return {
        "short_answer": short_answer,
        "missing_evidence": [item["message"] for item in missing_evidence[:5]],
        "supporting_evidence": evidence[:5],
        "where_to_check": fallback,
        "confidence": score_label(score),
    }


def collect_blockers(context):
    blockers = []

    for section_name, section in context.items():
        if not isinstance(section, dict):
            continue

        if section.get("status") in ["blocked", "error", "not_found", "invalid", "partial", "review", "missing"]:
            guidance = section_guidance(section_name)
            status_message = (
                section.get("message")
                or f"{guidance['label']} is marked {section.get('status')}, so it is not complete enough to rely on alone."
            )
            blockers.append(clean_sentence(status_message))

        summary = section.get("summary") or {}
        if isinstance(summary, dict):
            for key, value in summary.items():
                if not numeric(value):
                    continue
                if "blocked" in key or "blocker" in key:
                    blockers.append(human_metric_sentence(section_name, key, value, "blocked"))
                if "missing" in key or "open_gap" in key:
                    blockers.append(human_metric_sentence(section_name, key, value, "missing"))
                if "review" in key:
                    blockers.append(human_metric_sentence(section_name, key, value, "review"))

        for key in ["blockers", "exceptions", "missing_required", "open_gaps", "gaps"]:
            rows = section.get(key)
            if isinstance(rows, list):
                for row in rows[:3]:
                    blockers.append(
                        clean_sentence(
                            f"{section_guidance(section_name)['label']}: {human_row_message(row)}"
                        )
                    )

    return dedupe(blockers)


def collect_evidence(context):
    evidence = []

    for section_name, section in context.items():
        if not isinstance(section, dict):
            continue

        guidance = section_guidance(section_name)
        status = section.get("status", "-")
        evidence.append(f"{guidance['label']} status is {status}")
        summary = section.get("summary")
        if isinstance(summary, dict):
            for key, value in list(summary.items())[:4]:
                label = METRIC_LABELS.get(key, key.replace("_", " "))
                evidence.append(f"{guidance['label']} - {label}: {value}")

    return dedupe(evidence)


def section_guidance(section_name):
    return SECTION_GUIDANCE.get(
        section_name,
        {
            "label": section_name.replace("_", " "),
            "page": "the relevant platform page",
            "route": "/",
        },
    )


def human_metric_sentence(section_name, key, value, issue_type):
    guidance = section_guidance(section_name)
    metric = METRIC_LABELS.get(key, key.replace("_", " "))

    if issue_type == "blocked":
        return f"{guidance['label']}: {value} {metric} still block the story."
    if issue_type == "missing":
        return f"{guidance['label']}: {value} {metric} are still missing."
    if issue_type == "review":
        return f"{guidance['label']}: {value} {metric} still need review."

    return f"{guidance['label']}: {metric} is {value}."


def human_row_message(row):
    if isinstance(row, dict):
        return (
            row.get("message")
            or row.get("blocker")
            or row.get("required_action")
            or row.get("recommended_action")
            or row.get("next_action")
            or row.get("title")
            or row.get("label")
            or str(row)
        )

    return str(row)


def clean_sentence(value):
    text = str(value).replace("_", " ").strip()
    if not text:
        return text
    return text[0].upper() + text[1:]


def dedupe_structured(values, key):
    seen = set()
    result = []
    for value in values:
        text = str(value.get(key))
        if text not in seen:
            seen.add(text)
            result.append(value)
    return result


def dedupe(values):
    seen = set()
    result = []
    for value in values:
        text = str(value)
        if text not in seen:
            seen.add(text)
            result.append(text)
    return result


def persona_decision_label(agent_id, blockers):
    if agent_id == "investor_evidence_agent":
        return "bankability_review_required" if blockers else "bankability_evidence_ready"
    if agent_id == "revenue_assurance_agent":
        return "revenue_leakage_review_required" if blockers else "revenue_assurance_ready"
    if agent_id == "market_readiness_agent":
        return "market_access_blocked" if blockers else "market_access_ready"
    if agent_id == "compliance_audit_agent":
        return "approval_not_defensible" if blockers else "approval_defensible"
    if agent_id == "forecast_trust_agent":
        return "forecast_trust_review_required" if blockers else "forecast_trust_ready"
    if agent_id == "client_success_agent":
        return "client_report_gaps_open" if blockers else "client_report_ready"
    if agent_id == "project_development_agent":
        return "development_readiness_review_required" if blockers else "development_ready"
    if agent_id == "asset_owner_value_agent":
        return "owner_value_review_required" if blockers else "owner_value_defensible"
    if agent_id == "executive_decision_agent":
        return "executive_attention_required" if blockers else "portfolio_on_track"
    return "trade_review_required" if blockers else "trade_ready"


def build_persona_summary(agent_id, blockers, context, profile, score):
    if blockers:
        return (
            f"{profile['name']} gives this a {score_label(score).lower()} score ({score}/100). "
            f"The main reason is: {blockers[0]}"
        )

    return (
        f"{profile['name']} gives this a {score_label(score).lower()} score ({score}/100). "
        f"The selected evidence is coherent enough for the next {profile['decision_type']} review."
    )


def build_persona_next_action(agent_id, blockers):
    if blockers:
        return blockers[0]

    actions = {
        "investor_evidence_agent": "Package bankability evidence for investor review.",
        "revenue_assurance_agent": "Use settlement and revenue evidence in the next owner update.",
        "market_readiness_agent": "Prepare the next market-route go-live checklist.",
        "compliance_audit_agent": "Prepare approval evidence for compliance review.",
        "forecast_trust_agent": "Keep monitoring forecast-vs-actual performance.",
        "client_success_agent": "Generate or update the client-facing performance note.",
        "project_development_agent": "Use scenario and market evidence for development planning.",
        "asset_owner_value_agent": "Summarize defensible owner value and next operational action.",
        "executive_decision_agent": "Escalate only if portfolio blockers reappear.",
    }
    return actions.get(agent_id, "Continue supervised monitoring.")


def build_persona_questions(agent_id, profile, persona_id=None):
    resolved_persona_id = persona_id or next(
        (
            mapped_persona_id
            for mapped_persona_id, mapped_agent_id in PERSONA_AGENT_MAP.items()
            if mapped_agent_id == agent_id and mapped_persona_id != "all"
        ),
        "all",
    )
    base = PERSONA_QUESTIONS.get(resolved_persona_id, PERSONA_QUESTIONS["all"])
    extras = {
        "investor_evidence_agent": [
            "Is this asset bankable?",
            "What diligence risk remains?",
        ],
        "revenue_assurance_agent": [
            "Where is revenue leaking?",
            "What changed between expected and settled revenue?",
        ],
        "market_readiness_agent": [
            "Which route is closest to production-ready?",
            "Which credentials or prequalification evidence are missing?",
        ],
        "compliance_audit_agent": [
            "Can this decision be approved?",
            "What audit evidence is incomplete?",
        ],
        "forecast_trust_agent": [
            "Should bid sizing be reduced?",
            "Which forecast evidence is weak?",
        ],
    }

    return base + extras.get(agent_id, [])


def classify_question_intent(question):
    text = (question or "").lower()
    if any(token in text for token in ["forecast", "optimizer", "optimiser", "model trust", "confidence", "bid sizing", "trust the model"]):
        return "forecast_optimizer_trust"
    if any(token in text for token in ["production gap", "solve first", "production-ready", "mock-ready", "mock ready", "mock-backed"]):
        return "production_gap_prioritization"
    if any(token in text for token in ["client", "tell", "update", "reporting", "stakeholder"]):
        return "stakeholder_update"
    if any(token in text for token in ["revenue", "value", "allocation", "excluded", "money", "bankable", "bankability", "profit", "profitable", "proftable", "pnl", "return"]):
        return "revenue_opportunity"
    if any(token in text for token in ["settlement", "realized", "paper pnl", "variance"]):
        return "settlement_explanation"
    if any(token in text for token in ["connector", "credential", "market access", "configure"]):
        return "connector_onboarding"
    if any(token in text for token in ["trade", "bid", "paper trade", "live"]):
        return "trading_action"
    if any(token in text for token in ["missing", "evidence", "gap", "proof"]):
        return "evidence_gap"
    return "general_persona_answer"


def persona_voice(persona_id):
    return PERSONA_VOICE.get(persona_id, PERSONA_VOICE["all"])


def build_persona_ai_brief_if_requested(
    context,
    decision,
    include_ai_brief,
    operator_question,
    persona_id,
    profile,
):
    if not include_ai_brief:
        return {
            "status": "not_requested",
            "brief": None,
            "model": DEFAULT_MODEL,
        }

    if is_mock_evidence_context(context):
        return {
            "status": "fallback",
            "brief": build_deterministic_persona_brief(
                decision=decision,
                operator_question=operator_question,
                persona_id=persona_id,
                profile=profile,
            ),
            "model": DEFAULT_MODEL,
            "message": "Mock Data mode uses deterministic persona intelligence for fast demo responses.",
        }

    if not os.environ.get("OPENAI_API_KEY"):
        return {
            "status": "fallback",
            "brief": build_deterministic_persona_brief(
                decision=decision,
                operator_question=operator_question,
                persona_id=persona_id,
                profile=profile,
            ),
            "model": DEFAULT_MODEL,
        }

    try:
        brief = asyncio.run(
            generate_persona_ai_brief(
                context=context,
                decision=decision,
                operator_question=operator_question,
                persona_id=persona_id,
                profile=profile,
            )
        )
        return {
            "status": "generated",
            "brief": brief,
            "model": DEFAULT_MODEL,
        }
    except Exception as error:
        return {
            "status": "fallback",
            "brief": build_deterministic_persona_brief(
                decision=decision,
                operator_question=operator_question,
                persona_id=persona_id,
                profile=profile,
            ),
            "message": f"Persona AI brief failed; returned deterministic brief. {error}",
            "model": DEFAULT_MODEL,
        }


def build_deterministic_persona_brief(decision, operator_question, persona_id, profile):
    answer_sections = decision.get("answer_sections") or {}
    question = operator_question or profile["primary_question"]
    intent = decision.get("question_intent") or classify_question_intent(question)
    voice = decision.get("persona_voice") or persona_voice(persona_id)
    lower_question = question.lower()
    missing_evidence = decision.get("missing_evidence") or []
    relevant_pages = decision.get("relevant_pages") or []
    intent_brief = build_intent_specific_brief(
        decision=decision,
        intent=intent,
        question=question,
        voice=voice,
    )
    if intent_brief:
        return intent_brief

    if any(token in lower_question for token in ["missing", "evidence", "gap", "proof"]):
        if missing_evidence:
            opener = (
                "The missing piece is not one single document. It is the proof that the "
                f"{missing_evidence[0]['label']} is complete enough to support the claim."
            )
        else:
            opener = (
                "I do not see a material evidence gap in the selected data. "
                "I would still confirm the source page before using this externally."
            )
    else:
        opener = decision["human_answer"]

    where_to_check = answer_sections.get("where_to_check")
    if not where_to_check and relevant_pages:
        page = relevant_pages[0]
        where_to_check = f"Check {page['page']} ({page['route']}) for the underlying rows."

    lines = [
        f"Question: {question}",
        f"Short answer: {opener}",
        (
            f"Confidence: {decision['score_label']} ({decision['score']}/100). "
            "This score is a practical review signal, not a final financial model."
        ),
        f"Why it matters: {decision['what_it_means']}",
    ]

    if missing_evidence:
        lines.extend(
            [
                "What is missing:",
                *[f"- {item['message']}" for item in missing_evidence[:4]],
            ]
        )
    elif decision.get("blockers"):
        lines.extend(
            [
                "What needs attention:",
                *[f"- {item}" for item in decision.get("blockers", [])[:4]],
            ]
        )
    else:
        lines.append("What looks solid: I do not see a material gap in the selected evidence.")

    if where_to_check:
        lines.append(f"Where to check next: {where_to_check}")

    lines.extend(
        [
            "Recommended next steps:",
            *[f"- {action}" for action in decision.get("recommended_actions", [])[:3]],
            "Evidence I used:",
            *[f"- {item}" for item in decision.get("evidence", [])[:4]],
        ]
    )

    return append_mock_evidence_completeness("\n\n".join(lines), decision)


def build_intent_specific_brief(decision, intent, question, voice):
    brief = None
    if intent == "forecast_optimizer_trust":
        brief = build_forecast_optimizer_trust_brief(decision=decision, question=question, voice=voice)
    elif intent == "production_gap_prioritization":
        brief = build_production_gap_brief(decision=decision, question=question, voice=voice)
    elif intent == "revenue_opportunity":
        brief = build_revenue_opportunity_brief(decision=decision, question=question, voice=voice)
    elif intent == "settlement_explanation":
        brief = build_settlement_brief(decision=decision, question=question, voice=voice)
    elif intent == "connector_onboarding":
        brief = build_connector_brief(decision=decision, question=question, voice=voice)
    elif intent == "stakeholder_update":
        brief = build_stakeholder_update_brief(decision=decision, question=question, voice=voice)

    if brief:
        return append_mock_evidence_completeness(brief, decision)
    return None


def append_mock_evidence_completeness(brief, decision):
    mock = decision.get("mock_evidence_completeness") or {}
    if not mock:
        return brief

    missing = mock.get("missing_steps") or []
    generated = mock.get("generated_steps") or []
    lines = [
        f"Evidence completeness: {mock.get('available_count', 0)}/{mock.get('required_count', 0)} mock evidence item(s) available.",
        f"Missing: {', '.join(item.get('label', item.get('step_id', '-')) for item in missing) if missing else 'none'}.",
        f"Generated for this answer: {', '.join(generated) if generated else 'none; existing mock evidence was reused'}.",
    ]
    return "\n\n".join([brief, *lines])


def build_forecast_optimizer_trust_brief(decision, question, voice):
    evidence = decision.get("forecast_optimizer_evidence") or {}
    priority = decision.get("priority_intelligence") or {}
    evidence_mode = priority.get("evidence_mode", "live")
    confidence_score = numeric(evidence.get("confidence_score"))
    confidence_band = evidence.get("confidence_band") or "-"
    run_count = int(numeric(evidence.get("run_count")))
    volume_multiplier = evidence.get("volume_multiplier")
    price_buffer = evidence.get("price_buffer_eur_per_mwh")
    expected_pnl = numeric(evidence.get("expected_pnl_eur"))
    active_intervals = int(numeric(evidence.get("active_intervals")))
    throughput = numeric(evidence.get("throughput_mwh"))
    validation_status = evidence.get("validation_status") or "-"
    mode_label = "Mock Data" if evidence_mode == "mock" else "Live Data"
    sizing_call = forecast_sizing_call(
        confidence_score=confidence_score,
        volume_multiplier=volume_multiplier,
        validation_status=validation_status,
    )
    trust_call = (
        "yes, for supervised sizing"
        if confidence_score >= 80 and validation_status in ["pass", "passed", "-"]
        else "yes, but only with reduced sizing"
        if confidence_score >= 60
        else "not yet for normal sizing"
    )

    return "\n\n".join([
        f"Question: {question}",
        f"Short answer: {voice['opening']}, {trust_call}. This is based on {mode_label} forecast and optimizer evidence, not just a file being present.",
        (
            f"Forecast evidence: confidence is {round(confidence_score, 1)}/100 ({confidence_band}); "
            f"{run_count} forecast-vs-actual run(s) are in the evidence set; "
            f"latest MAE is {format_metric(evidence.get('latest_mae_eur_per_mwh'), 'EUR/MWh')}, "
            f"latest RMSE is {format_metric(evidence.get('latest_rmse_eur_per_mwh'), 'EUR/MWh')}, "
            f"and latest revenue delta is {format_metric(evidence.get('latest_revenue_delta_eur'), 'EUR')}."
        ),
        (
            f"Optimizer evidence: engine {evidence.get('optimizer_engine') or '-'} produced signal "
            f"{evidence.get('signal') or '-'} / {evidence.get('opportunity_level') or '-'} with "
            f"{format_metric(expected_pnl, 'EUR')} expected PnL, {active_intervals} active interval(s), "
            f"{format_metric(throughput, 'MWh')} throughput, "
            f"{int(numeric(evidence.get('charge_intervals')))} charge interval(s), and "
            f"{int(numeric(evidence.get('discharge_intervals')))} discharge interval(s)."
        ),
        (
            f"Validation and sizing: validation status is {validation_status}; "
            f"errors {int(numeric(evidence.get('validation_errors')))}, warnings {int(numeric(evidence.get('validation_warnings')))}. "
            f"My sizing interpretation is: {sizing_call}"
        ),
        "What I would do with this:",
        f"- Use volume multiplier {format_metric(volume_multiplier, 'x')} and price buffer {format_metric(price_buffer, 'EUR/MWh')} for bid sizing.",
        "- Keep the forecast-vs-actual run current before changing the automation level.",
        "- In Mock Data mode, treat this as a complete simulated trust proof; switch to Live Data mode before claiming production forecast performance.",
        "Evidence I used:",
        f"- forecast confidence score: {round(confidence_score, 1)}",
        f"- forecast run count: {run_count}",
        f"- optimizer expected PnL EUR: {round(expected_pnl, 2)}",
        f"- active optimizer intervals: {active_intervals}",
        "Where I would check: Forecast Trust (/forecasts) and Market Signals (/market-signals).",
    ])


def forecast_sizing_call(confidence_score, volume_multiplier, validation_status):
    if confidence_score >= 80 and validation_status in ["pass", "passed", "-"]:
        return (
            f"normal supervised sizing is acceptable at {format_metric(volume_multiplier, 'x')} volume, "
            "assuming the operator keeps the normal approval gate."
        )
    if confidence_score >= 60:
        return (
            f"use reduced sizing at {format_metric(volume_multiplier, 'x')} volume and keep human approval active."
        )
    return "keep this paper-only or very small until forecast error improves."


def format_metric(value, suffix):
    if value is None:
        return "-"
    try:
        number = float(value)
    except (TypeError, ValueError):
        return str(value)
    if suffix == "x":
        return f"{number:.2f}x"
    if abs(number) >= 100:
        return f"{number:,.2f} {suffix}"
    return f"{number:.2f} {suffix}"


def build_production_gap_brief(decision, question, voice):
    priority = decision.get("priority_intelligence") or {}
    summary = priority.get("summary") or {}
    evidence_mode = priority.get("evidence_mode", "live")
    production_gaps = [
        gap for gap in priority.get("gaps", [])
        if gap.get("status") != "ready"
    ]
    first_gap = choose_first_production_gap(production_gaps)
    evidence_modes = priority.get("evidence_modes") or []

    if evidence_mode == "mock":
        return "\n\n".join([
            f"Question: {question}",
            f"Short answer: {voice['opening']}, I do not see a missing proof item in Mock Data mode.",
            (
                "What this means: the agent has a complete simulated evidence pack for revenue, "
                "settlement, market readiness, and forecast trust. I can use it to explain the workflow, "
                "the calculations, and the expected decision logic."
            ),
            f"Live-data boundary: {summary.get('business_answer', 'Switch to Live Data mode to check production proof.')}",
            "Proof I would show in the platform:",
            *[f"- {mode.get('domain')}: {mode.get('agent_language')}" for mode in evidence_modes[:4]],
            "My next action: use Mock Data mode for the walkthrough, then switch to Live Data mode before making production claims.",
        ])

    if not first_gap:
        short_answer = (
            f"{voice['opening']}, I do not see an open production gap in the current evidence."
        )
        why = "The four priority domains are ready for the current evidence mode."
        next_action = "Keep the evidence refreshed before using it externally."
        source = "Decision Evidence (/intelligence)"
        missing = ["No material production gap detected."]
    else:
        production_missing = production_missing_items_for_gap(
            gap=first_gap,
            priority=priority,
        )
        short_answer = (
            f"{voice['opening']}, I would solve {first_gap['domain'].lower()} first. "
            f"The demo story is usable, but this is still {first_gap.get('status', 'not production-ready').replace('_', '-')}."
        )
        why = first_gap.get("why_it_matters") or first_gap.get("business_impact")
        next_action = first_gap.get("next_action")
        source = f"{first_gap.get('source_page')} ({first_gap.get('source_route')})"
        missing = production_missing or first_gap.get("missing_evidence") or []

    mode_lines = [
        f"{mode.get('domain')}: {mode.get('agent_language')}"
        for mode in evidence_modes[:4]
    ]

    return "\n\n".join([
        f"Question: {question}",
        f"Short answer: {short_answer}",
        (
            f"Production view: {summary.get('business_answer', 'The current platform evidence chain is available, but production readiness still needs review.')}"
        ),
        f"Why I would prioritize it: {why}",
        "What is already usable:",
        *[f"- {line}" for line in mode_lines],
        "What production proof is still needed:",
        *[f"- {item}" for item in missing[:5]],
        f"Where I would check: {source}",
        f"My next action: {next_action}",
    ])


def build_revenue_opportunity_brief(decision, question, voice):
    revenue = (decision.get("priority_intelligence") or {}).get("revenue_opportunities") or {}
    settlement = (decision.get("priority_intelligence") or {}).get("settlement_explainer") or {}
    priority = decision.get("priority_intelligence") or {}
    evidence_mode = priority.get("evidence_mode", "live")
    rows = revenue.get("rows") or []
    top = revenue.get("highest_value_product") or (rows[0] if rows else {})
    total_visible = sum(numeric(row.get("estimated_revenue_eur")) for row in rows)
    total_allocated = sum(numeric(row.get("allocated_revenue_eur")) for row in rows)
    excluded = [row for row in rows if row.get("allocation_status") == "excluded"]
    excluded_value = sum(numeric(row.get("estimated_revenue_eur")) for row in excluded)
    allocated_rows = [row for row in rows if row.get("allocation_status") == "allocated"]
    allocation_ratio = (total_allocated / total_visible * 100) if total_visible else 0
    expected_pnl = numeric(settlement.get("expected_pnl_eur"))
    paper_pnl = numeric(settlement.get("paper_pnl_eur"))
    mode_label = "mock/simulated" if evidence_mode == "mock" else "live-data"
    profitability_call = (
        "profitable in the current model"
        if total_visible > 0 and (total_allocated > 0 or expected_pnl > 0)
        else "not yet showing enough positive value"
    )
    bankability_call = (
        "bankable for a first review"
        if total_visible > 0 and len(allocated_rows) >= 1 and decision.get("score", 0) >= 75
        else "not bankable yet without stronger evidence"
    )
    return "\n\n".join([
        f"Question: {question}",
        (
            f"Short answer: {voice['opening']}, the battery is {profitability_call} and "
            f"{bankability_call} in {mode_label} mode."
        ),
        (
            f"Revenue numbers: total visible monthly opportunity is {round(total_visible, 2)} EUR; "
            f"{round(total_allocated, 2)} EUR is allocated into the current value stack "
            f"({round(allocation_ratio, 1)}% of visible value)."
        ),
        (
            f"Top product: {top.get('product_id', 'n/a')} contributes "
            f"{top.get('estimated_revenue_eur', '-')} EUR estimated revenue and "
            f"{top.get('allocated_revenue_eur', '-')} EUR allocated revenue."
        ),
        (
            f"Upside not currently used: {len(excluded)} product(s) are excluded by allocation constraints, "
            f"representing {round(excluded_value, 2)} EUR of modelled optional upside."
        ),
        (
            f"Execution/PnL check: proposal expected PnL is {settlement.get('expected_pnl_eur', '-')}; "
            f"paper PnL is {settlement.get('paper_pnl_eur', '-')}; "
            f"paper delta is {settlement.get('paper_delta_eur', '-')}. "
            f"That means the commercial story is strongest as a {mode_label} revenue case until live settlement records are attached."
        ),
        "Products I used:",
        *[
            (
                f"- {row.get('product_id')}: {row.get('estimated_revenue_eur', '-')} EUR estimated, "
                f"{format_allocated_revenue(row.get('allocated_revenue_eur'))}, {row.get('allocation_status', '-')}"
            )
            for row in rows[:6]
        ],
        f"My next action: {top.get('next_action', 'Refresh revenue allocation and review product-level evidence.')}",
        "Where I would check: Revenue Assurance (/revenue)",
    ])


def format_allocated_revenue(value):
    if value is None:
        return "not allocated"
    return f"{value} EUR allocated"


def build_settlement_brief(decision, question, voice):
    settlement = (decision.get("priority_intelligence") or {}).get("settlement_explainer") or {}
    return "\n\n".join([
        f"Question: {question}",
        f"Short answer: {voice['opening']}, {settlement.get('short_answer', 'settlement proof is not loaded yet.')}",
        f"Why it matters: I cannot claim production-realized revenue until expected, paper, realized, and statement evidence line up.",
        f"Evidence I would cite: expected PnL {settlement.get('expected_pnl_eur', '-')}, paper PnL {settlement.get('paper_pnl_eur', '-')}, realized PnL {settlement.get('realized_pnl_eur', '-')}.",
        f"Variance explanation: {settlement.get('human_variance_explanation', '-')}",
        "Production proof still needed:",
        *[f"- {item}" for item in (settlement.get("production_record_needed") or [])[:5]],
        f"My next action: {settlement.get('next_action', 'Attach production settlement records.')}",
        "Where I would check: Settlement Evidence (/execution/settlement)",
    ])


def build_connector_brief(decision, question, voice):
    onboarding = (decision.get("priority_intelligence") or {}).get("connector_onboarding") or {}
    rows = onboarding.get("rows") or []
    first = rows[0] if rows else {}
    return "\n\n".join([
        f"Question: {question}",
        f"Short answer: {voice['opening']}, I would configure {first.get('adapter_name', 'the first blocked connector')} first.",
        onboarding.get("business_answer", "Connector onboarding evidence is not loaded yet."),
        f"Why this matters: {first.get('business_value', 'Production market access depends on credentials, handshakes, and connector controls.')}",
        f"First credential: {first.get('first_credential', '-')}",
        f"My next action: {first.get('next_action', 'Open the connector page and complete the first missing credential.')}",
        "Where I would check: Market Access & Data (/execution/market-connectors)",
    ])


def build_stakeholder_update_brief(decision, question, voice):
    priority = decision.get("priority_intelligence") or {}
    summary = priority.get("summary") or {}
    evidence_mode = priority.get("evidence_mode", "live")
    production_gaps = [
        gap for gap in priority.get("gaps", [])
        if gap.get("status") != "ready"
    ]
    first_gap = choose_first_production_gap(production_gaps)

    if evidence_mode == "mock":
        evidence_modes = priority.get("evidence_modes") or []
        return "\n\n".join([
            f"Question: {question}",
            f"Short answer: {voice['opening']}, the Mock Data evidence pack is ready for the client-style walkthrough.",
            (
                "What I can safely say: the platform has simulated proof for the value story, "
                "paper execution, settlement explanation, forecast confidence, and market-readiness workflow."
            ),
            (
                "What I would avoid overclaiming: I would not call the asset live-connected or production-settled "
                "until the same question is checked in Live Data mode."
            ),
            "Proof I would show:",
            *[f"- {mode.get('domain')}: {mode.get('source_page')} ({mode.get('source_route')})" for mode in evidence_modes[:4]],
            "My next action: run the client update in Mock Data mode, then use Live Data mode as the production-readiness checklist.",
        ])

    return "\n\n".join([
        f"Question: {question}",
        f"Short answer: {voice['opening']}, I would say the current platform evidence chain is ready, but I would not call it production-live yet.",
        f"What I can safely say: {summary.get('business_answer', 'The current evidence is usable for demo review.')}",
        f"What I would avoid overclaiming: {first_gap.get('title') if first_gap else 'No material production gap detected.'}",
        f"Proof I would show: {(first_gap or {}).get('source_page', 'Decision Evidence')} ({(first_gap or {}).get('source_route', '/intelligence')}).",
        f"My next action: {first_gap.get('next_action') if first_gap else 'Keep the evidence refreshed.'}",
    ])


def choose_first_production_gap(gaps):
    if not gaps:
        return None
    priority_order = {
        "settlement_proof": 1,
        "market_readiness": 2,
        "revenue_proof": 3,
        "forecast_trust": 4,
    }
    return sorted(
        gaps,
        key=lambda gap: (
            priority_order.get(gap.get("gap_id"), 99),
            -severity_sort(gap.get("severity")),
        ),
    )[0]


def severity_sort(severity):
    return {"high": 3, "medium": 2, "low": 1}.get(severity, 0)


def production_missing_items_for_gap(gap, priority):
    if not gap:
        return []
    if gap.get("gap_id") == "settlement_proof":
        settlement = priority.get("settlement_explainer") or {}
        return settlement.get("production_record_needed") or []
    if gap.get("gap_id") == "market_readiness":
        onboarding = priority.get("connector_onboarding") or {}
        rows = onboarding.get("rows") or []
        if rows:
            first = rows[0]
            return [
                item
                for item in [
                    first.get("first_credential"),
                    first.get("next_action"),
                ]
                if item and item != "-"
            ]
    return []


async def generate_persona_ai_brief(
    context,
    decision,
    operator_question,
    persona_id,
    profile,
):
    from agents import Agent, Runner

    agent = Agent(
        name=profile["name"],
        instructions=(
            f"You are {profile['name']} for Battery Trader AI. "
            f"Answer for persona {persona_id}. Focus on: {profile['primary_question']} "
            "Use only the supplied JSON evidence. Do not invent facts. "
            "Answer in first person from the persona's operating perspective. "
            "Do not say 'this persona needs'; say what I would do, say, approve, configure, or avoid claiming. "
            "Use the decision.question_intent and decision.priority_intelligence first when available. "
            "Avoid raw machine-status language unless it is translated into business meaning. "
            "Give a short answer, why it matters, evidence basis, risks/gaps, and next actions. "
            "If a calculation is heuristic or placeholder, say that clearly."
        ),
        model=DEFAULT_MODEL,
    )
    payload = {
        "persona_id": persona_id,
        "profile": profile,
        "decision": decision,
        "operator_question": operator_question,
        "context": context,
    }

    result = await Runner.run(
        agent,
        "Create a persona-specific decision brief from this JSON:\n"
        + json.dumps(payload, indent=2, default=str),
    )
    return result.final_output
