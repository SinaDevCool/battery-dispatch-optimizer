import re
from datetime import datetime

from fastapi import APIRouter
from fastapi.responses import HTMLResponse

from backend.api.schemas import ApiResponse
from backend.api.schemas import MonthlyReportResponse
from backend.assets.asset_loader import get_asset
from backend.config.paths import OUTPUT_DATA_DIR
from backend.db.repositories.asset_repository import get_asset_record
from backend.db.repositories.execution_repository import (
    get_latest_execution_paper_trade,
    get_latest_execution_proposal,
    list_automation_events,
)
from backend.regulatory.germany_assumption_engine import (
    build_germany_regulatory_assumptions,
)
from backend.reports.monthly_report import build_asset_client_report_html
from backend.revenue.revenue_stack_runner import load_latest_asset_revenue_stack
from backend.services.asset_provenance import attach_asset_provenance
from backend.services.asset_signal_store import load_asset_latest_signal
from backend.services.data_completeness_service import build_asset_data_completeness
from backend.settlement.settlement_reconciliation import latest_settlement_reconciliation
from backend.storage import get_storage_client


router = APIRouter()


@router.get("/reports/monthly/latest", response_model=MonthlyReportResponse)
def latest_monthly_report(asset_id: str | None = None):
    report_dir = OUTPUT_DATA_DIR
    storage = get_storage_client()
    report_files = list_report_files(storage, report_dir, asset_id=asset_id)

    if not report_files:
        return {
            "status": "not_found",
            "message": "No monthly reports found.",
            "asset_id": asset_id,
        }

    latest_report = report_files[-1]

    response = {
        "status": "ok",
        "asset_id": asset_id,
        "report_file": str(latest_report),
        "report_name": latest_report.name,
        "report_title": build_report_title(latest_report.name),
        "report_period": report_period_from_name(latest_report.name),
        "viewer_route": build_viewer_route(asset_id),
    }
    if asset_id:
        try:
            return attach_asset_provenance(
                response,
                get_asset(asset_id),
                artifact=str(latest_report),
                kind="monthly_report",
                source_file=str(latest_report),
                production_upgrade_path=(
                    "Connect production data sources, signed report archive, PDF export, "
                    "and settlement-backed audit evidence."
                ),
            )
        except ValueError:
            return response
    return response


@router.get("/reports/monthly/list", response_model=ApiResponse)
def list_monthly_reports(asset_id: str | None = None):
    report_dir = OUTPUT_DATA_DIR
    storage = get_storage_client()
    report_files = list_report_files(storage, report_dir, asset_id=asset_id)

    response = {
        "status": "ok",
        "asset_id": asset_id,
        "report_count": len(report_files),
        "reports": [
            {
                "report_name": report_file.name,
                "report_title": build_report_title(report_file.name),
                "report_period": report_period_from_name(report_file.name),
                "report_file": str(report_file),
                "asset_id": asset_id_from_report_name(report_file.name),
            }
            for report_file in reversed(report_files)
        ],
    }
    if asset_id:
        try:
            return attach_asset_provenance(
                response,
                get_asset(asset_id),
                artifact="monthly_report_list",
                kind="monthly_report_list",
            )
        except ValueError:
            return response
    return response


@router.get("/reports/monthly/latest/view", response_class=HTMLResponse)
def view_latest_monthly_report(asset_id: str | None = None):
    report_dir = OUTPUT_DATA_DIR
    storage = get_storage_client()
    report_files = list_report_files(storage, report_dir, asset_id=asset_id)

    if not report_files:
        return "<h1>No monthly reports found</h1>"

    latest_report = report_files[-1]

    return storage.read_text(latest_report)


@router.post("/assets/{asset_id}/reports/monthly/generate", response_model=MonthlyReportResponse)
def generate_asset_monthly_report(asset_id: str):
    try:
        asset_record = get_asset_record(asset_id)
        asset = get_asset(asset_id)
        completeness = build_asset_data_completeness(asset_id)
        signal = load_asset_latest_signal(asset_id)
        revenue = load_latest_asset_revenue_stack(asset_id)
        regulatory = {
            "status": "ok",
            "asset_id": asset_id,
            "regulatory_assumptions": build_germany_regulatory_assumptions(asset).to_dict(),
        }
        execution_proposal = unwrap_payload(get_latest_execution_proposal(asset_id))
        paper_trade = unwrap_payload(get_latest_execution_paper_trade(asset_id))
        settlement = latest_settlement_reconciliation(asset_id)
        audit_events = list_automation_events(asset_id=asset_id, limit=20)

        html = build_asset_client_report_html(
            asset=asset_record,
            completeness=completeness,
            signal=signal,
            revenue=revenue,
            regulatory=regulatory,
            execution_proposal=execution_proposal,
            paper_trade=paper_trade,
            settlement=settlement,
            audit_events=audit_events,
        )
        report_file = build_asset_report_file(asset_id)
        storage = get_storage_client()
        storage.write_text(report_file, html)

        return attach_asset_provenance({
            "status": "ok",
            "asset_id": asset_id,
            "message": "Generated selected-asset client report.",
            "report_file": str(report_file),
            "report_name": report_file.name,
            "report_title": build_report_title(report_file.name),
            "report_period": report_period_from_name(report_file.name),
            "viewer_route": build_viewer_route(asset_id),
        }, get_asset(asset_id), artifact=str(report_file), kind="monthly_report", source_file=str(report_file))
    except Exception as error:
        return {
            "status": "error",
            "asset_id": asset_id,
            "message": f"Could not generate monthly report: {error}",
        }


def list_report_files(storage, report_dir, asset_id=None):
    pattern = (
        f"monthly_report_{safe_asset_id(asset_id)}_*.html"
        if asset_id
        else "monthly_report_*.html"
    )
    return storage.list_files(report_dir, pattern)


def build_asset_report_file(asset_id):
    report_month = datetime.now().strftime("%Y-%m")
    return OUTPUT_DATA_DIR / f"monthly_report_{safe_asset_id(asset_id)}_{report_month}.html"


def build_viewer_route(asset_id=None):
    route = "/reports/monthly/latest/view"
    if asset_id:
        return f"{route}?asset_id={asset_id}"
    return route


def unwrap_payload(record):
    if not record:
        return None
    return record.get("payload") or record


def safe_asset_id(asset_id):
    return re.sub(r"[^A-Za-z0-9_-]+", "_", str(asset_id or "portfolio"))


def asset_id_from_report_name(report_name):
    match = re.match(r"monthly_report_(.+)_\d{4}-\d{2}\.html$", report_name)
    return match.group(1) if match else None


def report_period_from_name(report_name):
    match = re.search(r"_(\d{4}-\d{2})\.html$", report_name)
    return match.group(1) if match else None


def build_report_title(report_name):
    period = report_period_from_name(report_name)
    asset_id = asset_id_from_report_name(report_name)
    asset_label = asset_id.replace("_", " ").title() if asset_id else "Portfolio"
    if period:
        return f"{asset_label} investor evidence report - {period}"
    return f"{asset_label} investor evidence report"



