from src.db.repositories.asset_repository import get_asset_record
from src.db.repositories.business_decision_repository import get_latest_business_decision
from src.db.repositories.execution_repository import get_latest_execution_proposal
from src.db.repositories.forecast_repository import get_latest_forecast_snapshot
from src.db.repositories.revenue_repository import list_revenue_stack_runs
from src.db.repositories.signal_repository import list_signal_runs
from src.db.repositories.workflow_repository import list_workflow_runs


def build_asset_data_completeness(asset_id):
    asset = get_asset_record(asset_id)
    forecast_snapshot = get_latest_forecast_snapshot(
        forecast_file=asset.get("forecast_file"),
    )
    signal_runs = list_signal_runs(asset_id=asset_id, limit=1)
    revenue_runs = list_revenue_stack_runs(asset_id=asset_id, limit=1)
    workflow_runs = list_workflow_runs(asset_id=asset_id, limit=1)
    decision = get_latest_business_decision(asset_id)
    execution_proposal = get_latest_execution_proposal(asset_id)

    signal = signal_runs[0] if signal_runs else None
    revenue = revenue_runs[0] if revenue_runs else None
    workflow = workflow_runs[0] if workflow_runs else None

    checks = [
        build_check(
            "asset_registered",
            "Asset registered",
            asset is not None,
            "Asset exists in the backend registry.",
            "Create or sync an asset record before running optimization.",
            record_id=asset.get("asset_id") if asset else None,
        ),
        build_check(
            "forecast_snapshot",
            "Forecast snapshot",
            forecast_snapshot is not None,
            "A forecast snapshot is available for the selected asset forecast file.",
            "Run or upload a forecast and store it as a snapshot.",
            record_id=forecast_snapshot.get("forecast_snapshot_id")
            if forecast_snapshot
            else None,
            evidence=forecast_snapshot,
        ),
        build_check(
            "latest_signal",
            "Latest dispatch signal",
            signal is not None,
            "A persisted signal run exists for this asset.",
            "Run optimization to create a signal run.",
            record_id=signal.get("signal_id") if signal else None,
            evidence=signal,
        ),
        build_check(
            "revenue_stack",
            "Revenue stack",
            revenue is not None,
            "A persisted revenue stack run exists for this asset.",
            "Run revenue stack modelling to value available market products.",
            record_id=revenue.get("revenue_stack_id") if revenue else None,
            evidence=revenue,
        ),
        build_check(
            "business_decision",
            "Business decision",
            decision is not None,
            "A commercial recommendation has been generated.",
            "Build a business decision after signal and revenue evidence exists.",
            record_id=decision.get("decision_id") if decision else None,
            evidence=strip_payload(decision),
        ),
        build_check(
            "workflow_audit",
            "Workflow audit",
            workflow is not None,
            "A linked workflow run connects forecast, signal, revenue, and decision evidence.",
            "Run audited workflow to create a traceable decision record.",
            record_id=workflow.get("workflow_run_id") if workflow else None,
            evidence=strip_payload(workflow),
        ),
        build_check(
            "execution_proposal",
            "Execution proposal",
            execution_proposal is not None,
            "A pre-trade proposal exists for review.",
            "Build a pre-trade proposal after a valid signal exists.",
            record_id=execution_proposal.get("execution_proposal_id")
            if execution_proposal
            else None,
            evidence=strip_payload(execution_proposal),
        ),
    ]

    complete_count = sum(1 for check in checks if check["status"] == "complete")
    warning_count = sum(1 for check in checks if check["status"] == "missing")
    score = round((complete_count / len(checks)) * 100, 1) if checks else 0

    return {
        "status": "ok",
        "asset_id": asset_id,
        "score": score,
        "complete_count": complete_count,
        "missing_count": warning_count,
        "check_count": len(checks),
        "readiness": classify_readiness(score),
        "checks": checks,
        "next_actions": [
            check["recommended_action"]
            for check in checks
            if check["status"] != "complete"
        ],
    }


def build_check(
    check_id,
    label,
    is_complete,
    complete_message,
    missing_message,
    record_id=None,
    evidence=None,
):
    return {
        "check_id": check_id,
        "label": label,
        "status": "complete" if is_complete else "missing",
        "record_id": record_id,
        "message": complete_message if is_complete else missing_message,
        "recommended_action": "-" if is_complete else missing_message,
        "evidence": evidence or {},
    }


def classify_readiness(score):
    if score >= 85:
        return "decision_ready"
    if score >= 55:
        return "usable_with_gaps"
    return "setup_required"


def strip_payload(record):
    if not record:
        return {}

    return {
        key: value
        for key, value in record.items()
        if key not in ["payload", "payload_json"]
    }
