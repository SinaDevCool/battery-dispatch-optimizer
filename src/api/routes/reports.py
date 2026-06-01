from fastapi import APIRouter
from fastapi.responses import HTMLResponse

from src.config.paths import OUTPUT_DATA_DIR


router = APIRouter()


@router.get("/reports/monthly/latest")
def latest_monthly_report():
    report_dir = OUTPUT_DATA_DIR

    if not report_dir.exists():
        return {
            "status": "not_found",
            "message": "Report output folder does not exist yet.",
        }

    report_files = sorted(report_dir.glob("monthly_report_*.html"))

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


@router.get("/reports/monthly/latest/view", response_class=HTMLResponse)
def view_latest_monthly_report():
    report_dir = OUTPUT_DATA_DIR

    if not report_dir.exists():
        return "<h1>No report folder found</h1>"

    report_files = sorted(report_dir.glob("monthly_report_*.html"))

    if not report_files:
        return "<h1>No monthly reports found</h1>"

    latest_report = report_files[-1]

    with open(latest_report, "r", encoding="utf-8") as file:
        return file.read()
