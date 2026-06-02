from fastapi import APIRouter

from src.workflows.daily_workflow import run_daily_battery_workflow


router = APIRouter()


@router.post("/workflow/run-daily")
def run_daily_workflow(optimizer_engine: str = "rule_based_v1"):
    return run_daily_battery_workflow(optimizer_engine=optimizer_engine)
