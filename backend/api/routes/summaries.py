from collections.abc import Callable
from typing import Any

from fastapi import APIRouter

from backend.api.schemas import ApiResponse
from backend.api.routes.assets import asset_data_completeness
from backend.api.routes.business_decisions import latest_asset_business_decision
from backend.api.routes.execution import (
    asset_execution_automation_control_status,
    asset_execution_automation_guardrails,
    asset_execution_multi_market_allocation,
    asset_execution_readiness,
    latest_asset_execution_approval,
    latest_asset_execution_paper_trade,
    latest_asset_execution_proposal,
    latest_asset_market_submission,
)
from backend.api.routes.forecasts import asset_forecast_status
from backend.api.routes.regulatory import (
    asset_eeg_compliance,
    asset_germany_ancillary_eligibility,
    asset_storage_classification,
)
from backend.api.routes.reports import latest_monthly_report
from backend.api.routes.revenue import (
    asset_hedged_revenue_view,
    latest_asset_revenue_stack,
    latest_asset_revenue_stack_allocation,
)
from backend.api.routes.settlement import latest_asset_settlement
from backend.api.routes.telemetry import latest_telemetry
from backend.assets.asset_loader import get_asset
from backend.services.asset_signal_store import load_asset_latest_signal
from backend.services.asset_provenance import build_asset_provenance
from backend.services.investor_evidence import (
    build_client_report_proof,
    build_execution_proof,
    build_regulatory_proof,
    build_revenue_proof,
)
from backend.services.investor_readiness import build_investor_readiness


router = APIRouter()


@router.get("/assets/{asset_id}/revenue-summary", response_model=ApiResponse)
def asset_revenue_summary(asset_id: str):
    asset = safe_section("asset", lambda selected_asset_id: get_asset(selected_asset_id).to_dict(), asset_id)
    revenue_stack = safe_section("revenue_stack", latest_asset_revenue_stack, asset_id)
    allocation = safe_section(
        "revenue_allocation",
        latest_asset_revenue_stack_allocation,
        asset_id,
    )
    signal = safe_section("latest_signal", load_asset_latest_signal, asset_id)
    eeg = safe_section("eeg_compliance", asset_eeg_compliance, asset_id)
    ancillary = safe_section(
        "ancillary_eligibility",
        asset_germany_ancillary_eligibility,
        asset_id,
    )
    hedging = safe_section("hedging", asset_hedged_revenue_view, asset_id)
    business_decision = safe_section(
        "business_decision",
        latest_asset_business_decision,
        asset_id,
    )
    revenue_rows = normalize_revenue_rows(revenue_stack)
    eligible_rows = [
        row for row in revenue_rows if row.get("eligibility_status") == "eligible"
    ]
    blocked_rows = [
        row
        for row in revenue_rows
        if row.get("eligibility_status") == "not_eligible"
        or row.get("status") == "blocked"
        or has_issue_list(row.get("blocking_reasons"))
    ]
    warning_rows = [
        row for row in revenue_rows if has_issue_list(row.get("review_warnings"))
    ]
    total_revenue = revenue_stack.get("total_estimated_revenue_eur")
    if total_revenue is None:
        total_revenue = sum(
            float(row.get("estimated_revenue_eur") or 0) for row in revenue_rows
        )

    summary = {
        "total_estimated_revenue_eur": total_revenue,
        "product_count": revenue_stack.get("product_count")
        or revenue_stack.get("estimated_product_count")
        or len(revenue_rows),
        "eligible_product_count": len(eligible_rows),
        "blocked_product_count": len(blocked_rows),
        "review_product_count": len(warning_rows),
        "allocation_available": allocation.get("status") == "ok"
        and bool(allocation.get("results") or allocation.get("allocation")),
        "eeg_eligible": eeg.get("eeg_eligible"),
        "ancillary_eligible_count": ancillary.get("eligible_product_count")
        or len(ancillary.get("eligible_products") or []),
        "business_decision_status": (business_decision.get("decision") or {}).get(
            "recommendation_status"
        ),
    }

    return {
        "status": combined_status(
            [
                asset,
                revenue_stack,
                allocation,
                signal,
                eeg,
                ancillary,
                hedging,
                business_decision,
            ]
        ),
        "asset_id": asset_id,
        "metadata": build_asset_provenance(
            asset,
            artifact="revenue_summary",
            kind="revenue_summary",
            generated_at=latest_generated_at(
                revenue_stack,
                allocation,
                signal.get("metadata") or (signal.get("data") or {}).get("metadata") or {},
            ),
            source_file=latest_source_file(revenue_stack, signal),
            production_upgrade_path=(
                "Connect exchange price feeds, official product eligibility, live telemetry, "
                "hedge contracts, and settlement evidence for production revenue decisions."
            ),
        ),
        "summary": summary,
        "revenue_proof": build_revenue_proof(
            allocation=allocation,
            asset=asset,
            revenue_rows=revenue_rows,
            signal=signal,
            hedging=hedging,
            total_revenue=total_revenue,
        ),
        "revenue_stack": revenue_stack,
        "revenue_allocation": allocation,
        "latest_signal": signal,
        "eeg_compliance": eeg,
        "ancillary_eligibility": ancillary,
        "hedging": hedging,
        "business_decision": business_decision,
    }


@router.get("/assets/{asset_id}/regulatory-summary", response_model=ApiResponse)
def asset_regulatory_summary(asset_id: str):
    asset = safe_section("asset", lambda selected_asset_id: get_asset(selected_asset_id).to_dict(), asset_id)
    classification = safe_section(
        "storage_classification",
        asset_storage_classification,
        asset_id,
    )
    eeg = safe_section("eeg_compliance", asset_eeg_compliance, asset_id)
    ancillary = safe_section(
        "ancillary_eligibility",
        asset_germany_ancillary_eligibility,
        asset_id,
    )
    blockers = build_regulatory_blockers(eeg=eeg, ancillary=ancillary)

    return {
        "status": combined_status([asset, classification, eeg, ancillary]),
        "asset_id": asset_id,
        "metadata": build_asset_provenance(
            asset,
            artifact="regulatory_summary",
            kind="regulatory_summary",
            production_upgrade_path=(
                "Connect official market rule sources, signed legal review, "
                "prequalification evidence, and meter/certificate records."
            ),
        ),
        "summary": {
            "approval_status": "needs_review" if blockers else "approval_ready",
            "blocker_count": len(blockers),
            "storage_classification": classification.get("storage_classification")
            or classification.get("storage_mode"),
            "eeg_eligible": eeg.get("eeg_eligible"),
            "ancillary_eligible_count": ancillary.get("eligible_product_count")
            or len(ancillary.get("eligible_products") or []),
        },
        "blockers": blockers,
        "regulatory_proof": build_regulatory_proof(
            ancillary=ancillary,
            asset=asset,
            blockers=blockers,
            classification=classification,
            eeg=eeg,
        ),
        "storage_classification": classification,
        "eeg_compliance": eeg,
        "ancillary_eligibility": ancillary,
    }


@router.get("/assets/{asset_id}/execution-summary", response_model=ApiResponse)
def asset_execution_summary(asset_id: str):
    return build_asset_execution_summary(asset_id)


def build_asset_execution_summary(asset_id: str, *, include_details: bool = True):
    asset = safe_section("asset", lambda selected_asset_id: get_asset(selected_asset_id).to_dict(), asset_id)
    proposal = safe_section(
        "execution_proposal",
        latest_asset_execution_proposal,
        asset_id,
    )
    readiness = safe_section(
        "execution_readiness",
        asset_execution_readiness,
        asset_id,
    )
    guardrails = safe_section(
        "automation_guardrails",
        asset_execution_automation_guardrails,
        asset_id,
    )
    automation_control = (
        safe_section("automation_control", asset_execution_automation_control_status, asset_id)
        if include_details
        else build_lightweight_automation_control(
            asset_id=asset_id,
            guardrails=guardrails,
            proposal=proposal,
            readiness=readiness,
        )
    )
    signal = safe_section("latest_signal", load_asset_latest_signal, asset_id)
    paper_trade = (
        safe_section("paper_trade", latest_asset_execution_paper_trade, asset_id)
        if include_details
        else lightweight_section("paper_trade")
    )
    market_submission = (
        safe_section("market_submission", latest_asset_market_submission, asset_id)
        if include_details
        else lightweight_section("market_submission")
    )
    approval = (
        safe_section("approval", latest_asset_execution_approval, asset_id)
        if include_details
        else lightweight_section("approval")
    )
    allocation = (
        safe_section("multi_market_allocation", asset_execution_multi_market_allocation, asset_id)
        if include_details
        else lightweight_section("multi_market_allocation")
    )
    telemetry = (
        safe_section("telemetry", latest_telemetry, asset_id)
        if include_details
        else lightweight_section("telemetry")
    )

    proposal_payload = proposal.get("proposal") or {}
    signal_summary = (signal.get("data") or {}).get("summary") or {}
    control_blockers = automation_control.get("blockers") or []
    proposal_blockers = proposal_payload.get("automation_blockers") or []
    hard_blockers = proposal_payload.get("blockers") or []

    summary = {
        "proposal_available": proposal.get("status") == "ok"
        and bool(proposal_payload),
        "signal": signal_summary.get("signal"),
        "expected_pnl_eur": (proposal_payload.get("summary") or {}).get(
            "expected_pnl_eur"
        )
        or signal_summary.get("total_pnl_eur"),
        "readiness_status": readiness.get("readiness_status"),
        "readiness_score": readiness.get("readiness_score"),
        "automation_status": guardrails.get("automation_status")
        or automation_control.get("automation_mode"),
        "blocker_count": len(control_blockers)
        + len(proposal_blockers)
        + len(hard_blockers),
        "paper_trade_available": paper_trade.get("status") == "ok"
        and bool(paper_trade.get("paper_trade")),
        "submission_available": market_submission.get("status") == "ok"
        and bool(market_submission.get("submission")),
        "approval_status": (approval.get("approval") or {}).get("status"),
        "primary_market": allocation.get("primary_market"),
        "telemetry_status": (telemetry.get("telemetry") or {}).get("status"),
    }

    return {
        "status": combined_status(
            [
                asset,
                proposal,
                readiness,
                automation_control,
                guardrails,
                signal,
                paper_trade,
                market_submission,
                approval,
                allocation,
                telemetry,
            ]
        ),
        "asset_id": asset_id,
        "metadata": build_asset_provenance(
            asset,
            artifact="execution_summary",
            kind="execution_summary",
            generated_at=latest_generated_at(
                proposal_payload,
                paper_trade.get("paper_trade") or {},
                market_submission.get("submission") or {},
                telemetry.get("telemetry") or {},
            ),
            source_file=latest_source_file(proposal, signal),
            production_upgrade_path=(
                "Connect live market adapters, exchange credentials, EMS telemetry, "
                "approval workflow, and settlement reconciliation before production execution."
            ),
        ),
        "summary": summary,
        "execution_proof": build_execution_proof(
            asset=asset,
            allocation=allocation,
            automation_control=automation_control,
            proposal=proposal,
            readiness=readiness,
            signal=signal,
            telemetry=telemetry,
        ),
        "execution_proposal": proposal,
        "execution_readiness": readiness,
        "automation_control": automation_control,
        "automation_guardrails": guardrails,
        "latest_signal": signal,
        "paper_trade": paper_trade,
        "market_submission": market_submission,
        "approval": approval,
        "multi_market_allocation": allocation,
        "telemetry": telemetry,
    }


@router.get("/assets/{asset_id}/client-evidence-summary", response_model=ApiResponse)
def asset_client_evidence_summary(asset_id: str):
    return build_asset_client_evidence_summary(asset_id)


def build_asset_client_evidence_summary(
    asset_id: str,
    *,
    execution: dict[str, Any] | None = None,
):
    asset = safe_section("asset", lambda selected_asset_id: get_asset(selected_asset_id).to_dict(), asset_id)
    completeness = safe_section(
        "data_completeness",
        asset_data_completeness,
        asset_id,
    )
    report = safe_section(
        "latest_report",
        lambda selected_asset_id: latest_monthly_report(asset_id=selected_asset_id),
        asset_id,
    )
    revenue = asset_revenue_summary(asset_id)
    regulatory = asset_regulatory_summary(asset_id)
    execution = execution or asset_execution_summary(asset_id)
    settlement = safe_section("settlement", latest_asset_settlement, asset_id)
    report_proof = build_client_report_proof(
        asset=asset,
        completeness=completeness,
        report=report,
        revenue=revenue,
        regulatory=regulatory,
        execution=execution,
    )

    open_gaps = []
    if report.get("status") != "ok":
        open_gaps.append("No current monthly report is available.")
    if int(completeness.get("missing_count") or 0) > 0:
        open_gaps.append(
            f"{completeness.get('missing_count')} evidence gap(s) remain."
        )
    open_gaps.extend(regulatory.get("blockers") or [])
    if (execution.get("summary") or {}).get("blocker_count"):
        open_gaps.append("Execution still has open automation blockers.")

    return {
        "status": combined_status(
            [completeness, report, revenue, regulatory, execution, settlement]
        ),
        "asset_id": asset_id,
        "metadata": build_asset_provenance(
            asset,
            artifact="client_evidence_summary",
            kind="client_evidence_summary",
            generated_at=latest_generated_at(
                report.get("metadata") or {},
                revenue.get("metadata") or {},
                regulatory.get("metadata") or {},
                execution.get("metadata") or {},
                settlement,
            ),
            source_file=latest_source_file(report, revenue, execution),
            production_upgrade_path=(
                "Replace local mock evidence with production connectors, signed archive, "
                "metered settlement, and investor-approved audit trail."
            ),
        ),
        "summary": {
            "delivery_status": "draft" if open_gaps else "client_ready",
            "open_gap_count": len(open_gaps),
            "evidence_score": completeness.get("score"),
            "report_available": report.get("status") == "ok",
            "modelled_revenue_eur": (revenue.get("summary") or {}).get(
                "total_estimated_revenue_eur"
            ),
            "regulatory_approval_status": (regulatory.get("summary") or {}).get(
                "approval_status"
            ),
            "execution_readiness_status": (execution.get("summary") or {}).get(
                "readiness_status"
            ),
            "settlement_available": settlement.get("status") == "ok",
        },
        "open_gaps": open_gaps,
        "report_proof": report_proof,
        "data_completeness": completeness,
        "latest_report": report,
        "revenue_summary": revenue,
        "regulatory_summary": regulatory,
        "execution_summary": execution,
        "settlement": settlement,
    }


@router.get("/assets/{asset_id}/investor-readiness", response_model=ApiResponse)
def asset_investor_readiness(asset_id: str):
    asset = safe_section(
        "asset",
        lambda selected_asset_id: get_asset(selected_asset_id).to_dict(),
        asset_id,
    )
    signal = safe_section("latest_signal", load_asset_latest_signal, asset_id)
    revenue = asset_revenue_summary(asset_id)
    execution = build_asset_execution_summary(asset_id, include_details=False)
    evidence = build_asset_client_evidence_summary(asset_id, execution=execution)
    forecast = safe_section("forecast_status", asset_forecast_status, asset_id)
    readiness = build_investor_readiness(
        asset=asset,
        evidence=evidence,
        execution=execution,
        forecast=forecast,
        revenue=revenue,
        signal=signal,
    )

    return {
        **readiness,
        "status": combined_status([asset, signal, revenue, execution, evidence, forecast]),
        "metadata": build_asset_provenance(
            asset,
            artifact="investor_readiness",
            kind="investor_readiness",
            generated_at=latest_generated_at(
                signal.get("metadata") or (signal.get("data") or {}).get("metadata") or {},
                revenue.get("metadata") or {},
                execution.get("metadata") or {},
                evidence.get("metadata") or {},
                forecast.get("metadata") or {},
            ),
            source_file=latest_source_file(signal, revenue, execution, evidence, forecast),
            production_upgrade_path=(
                "Replace mock forecast, dispatch, revenue, execution, settlement, and report evidence "
                "with production connectors while preserving this readiness evidence contract."
            ),
        ),
    }


def safe_section(label: str, builder: Callable[..., dict[str, Any]], *args):
    try:
        value = builder(*args)
    except Exception as error:
        return {
            "status": "error",
            "message": f"Could not build {label}: {error}",
        }
    if isinstance(value, dict):
        return value
    return {
        "status": "ok",
        label: value,
    }


def lightweight_section(label: str):
    return {
        "status": "skipped",
        "message": f"{label} is omitted from the lightweight investor readiness summary.",
    }


def build_lightweight_automation_control(
    *,
    asset_id: str,
    guardrails: dict[str, Any],
    proposal: dict[str, Any],
    readiness: dict[str, Any],
):
    proposal_payload = proposal.get("proposal") or {}
    guardrail_blockers = [
        {
            "source": "guardrail",
            "key": row.get("guardrail"),
            "status": row.get("status"),
            "message": row.get("message"),
        }
        for row in guardrails.get("guardrails", [])
        if row.get("status") in {"blocked", "review"}
    ]
    readiness_blockers = [
        {
            "source": "readiness",
            "key": row.get("check"),
            "status": row.get("status"),
            "message": row.get("message"),
        }
        for row in readiness.get("checks", [])
        if row.get("status") in {"blocked", "review"}
    ]
    proposal_blockers = proposal_payload.get("automation_blockers") or []
    hard_blockers = proposal_payload.get("blockers") or []
    all_blockers = [
        *guardrail_blockers,
        *readiness_blockers,
        *[
            {"source": "proposal", "status": "review", "message": message}
            for message in proposal_blockers
        ],
        *[
            {"source": "proposal", "status": "blocked", "message": message}
            for message in hard_blockers
        ],
    ]
    automation_status = guardrails.get("automation_status")
    readiness_status = readiness.get("readiness_status")
    blocked = automation_status == "blocked" or readiness_status == "blocked"

    return {
        "status": combined_status([guardrails, proposal, readiness]),
        "asset_id": asset_id,
        "automation_mode": "live_auto_blocked" if blocked else "advisory_only",
        "automation_status": automation_status,
        "readiness_status": readiness_status,
        "readiness_score": readiness.get("readiness_score"),
        "blockers": dedupe_summary_blockers(all_blockers),
        "message": "Lightweight investor summary derived from proposal, guardrails, and readiness evidence.",
    }


def dedupe_summary_blockers(rows: list[dict[str, Any]]):
    seen = set()
    result = []
    for row in rows:
        key = (row.get("source"), row.get("key"), row.get("status"), row.get("message"))
        if not row.get("message") or key in seen:
            continue
        seen.add(key)
        result.append(row)
    return result


def combined_status(sections: list[dict[str, Any]]):
    statuses = [section.get("status") for section in sections]
    if any(status == "ok" for status in statuses):
        if any(status not in {"ok", None} for status in statuses):
            return "partial"
        return "ok"
    if any(status == "not_found" for status in statuses):
        return "not_found"
    return "error"


def normalize_revenue_rows(revenue_stack: dict[str, Any]):
    rows = revenue_stack.get("results") or revenue_stack.get("products") or []
    return rows if isinstance(rows, list) else []


def has_issue_list(value: Any):
    if not value:
        return False
    if isinstance(value, str):
        return value not in {"-", "none", "None"}
    if isinstance(value, list):
        return len(value) > 0
    return True


def build_regulatory_blockers(eeg: dict[str, Any], ancillary: dict[str, Any]):
    blockers = []
    if eeg.get("eeg_eligible") is False:
        blockers.append("EEG compliance is not eligible for automatic trading.")
    if eeg.get("mixed_origin_risk"):
        blockers.append("Mixed-origin or renewable-support risk needs review.")
    products = ancillary.get("products") or []
    blocked_products = [
        product
        for product in products
        if product.get("eligibility_status") == "not_eligible"
        or has_issue_list(product.get("blocking_reasons"))
    ]
    if blocked_products:
        blockers.append(f"{len(blocked_products)} ancillary product(s) are blocked.")
    return blockers


def latest_generated_at(*sections: dict[str, Any]):
    for section in sections:
        value = (
            section.get("generated_at")
            or section.get("captured_at")
            or section.get("submitted_at")
            or section.get("requested_at")
            or (section.get("metadata") or {}).get("generated_at")
        )
        if value:
            return value
    return None


def latest_source_file(*sections: dict[str, Any]):
    for section in sections:
        metadata = section.get("metadata") or {}
        data_metadata = ((section.get("data") or {}).get("metadata") or {})
        value = (
            section.get("source_file")
            or section.get("forecast_file")
            or section.get("report_file")
            or section.get("signal_file")
            or metadata.get("source_file")
            or metadata.get("forecast_file")
            or data_metadata.get("source_file")
            or data_metadata.get("forecast_file")
        )
        if value:
            return value
    return None

