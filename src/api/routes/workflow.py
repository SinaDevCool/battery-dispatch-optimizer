from fastapi import APIRouter

from src.workflows.daily_workflow import run_daily_battery_workflow


router = APIRouter()


@router.post("/workflow/run-daily")
def run_daily_workflow():
    return run_daily_battery_workflow()
