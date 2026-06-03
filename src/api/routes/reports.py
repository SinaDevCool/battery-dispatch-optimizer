from fastapi import APIRouter
from fastapi.responses import HTMLResponse

from src.api.schemas import ApiResponse
from src.api.schemas import MonthlyReportResponse
from src.config.paths import OUTPUT_DATA_DIR
from src.storage import get_storage_client


router = APIRouter()


@router.get("/reports/monthly/latest", response_model=MonthlyReportResponse)
def latest_monthly_report():
    report_dir = OUTPUT_DATA_DIR
    storage = get_storage_client()
    report_files = storage.list_files(report_dir, "monthly_report_*.html")

    if not report_files:
        return {
            "status": "not_found",
            "message": "No monthly reports found.",
        }

    latest_report = report_files[-1]

    return {
        "status": "ok",
        "report_file": str(latest_report),
        "report_name": latest_report.name,
    }


@router.get("/reports/monthly/list", response_model=ApiResponse)
def list_monthly_reports():
    report_dir = OUTPUT_DATA_DIR
    storage = get_storage_client()
    report_files = storage.list_files(report_dir, "monthly_report_*.html")

    return {
        "status": "ok",
        "report_count": len(report_files),
        "reports": [
            {
                "report_name": report_file.name,
                "report_file": str(report_file),
            }
            for report_file in reversed(report_files)
        ],
    }


@router.get("/reports/monthly/latest/view", response_class=HTMLResponse)
def view_latest_monthly_report():
    report_dir = OUTPUT_DATA_DIR
    storage = get_storage_client()
    report_files = storage.list_files(report_dir, "monthly_report_*.html")

    if not report_files:
        return "<h1>No monthly reports found</h1>"

    latest_report = report_files[-1]

    return storage.read_text(latest_report)
