from backend.api.routes.asset_signals import run_asset_latest_signal
from backend.execution.paper_trading import run_execution_paper_trade
from backend.execution.trading_orchestrator import run_trading_orchestrator
from backend.telemetry.asset_telemetry import save_demo_asset_telemetry
from backend.workflows.daily_workflow import run_daily_battery_workflow


SAFE_ACTIONS = {
    "refresh_forecast_demo": {
        "label": "Refresh Forecast Demo",
        "description": "Regenerate demo forecast data and daily workflow evidence.",
    },
    "run_signal": {
        "label": "Run Latest Signal",
        "description": "Load the latest asset signal evidence for supervisor context.",
    },
    "run_orchestrator": {
        "label": "Run Orchestrator",
        "description": "Run the next gated automation orchestrator action.",
    },
    "run_paper_trade": {
        "label": "Run Paper Trade",
        "description": "Run simulated paper-trading validation only.",
    },
    "refresh_telemetry_demo": {
        "label": "Refresh Telemetry Demo",
        "description": "Seed demo telemetry evidence for the selected asset.",
    },
}


def list_safe_actions():
    return [
        {
            "action_id": action_id,
            **metadata,
        }
        for action_id, metadata in SAFE_ACTIONS.items()
    ]


def run_safe_action(asset_id, action_id):
    if action_id not in SAFE_ACTIONS:
        return {
            "status": "invalid",
            "asset_id": asset_id,
            "action_id": action_id,
            "message": f"Unsupported AI supervisor action: {action_id}",
        }

    if action_id == "refresh_forecast_demo":
        result = run_daily_battery_workflow(optimizer_engine="linear_program_v1")
    elif action_id == "run_signal":
        result = run_asset_latest_signal(
            asset_id=asset_id,
            optimizer_engine="linear_program_v1",
        )
    elif action_id == "run_orchestrator":
        result = run_trading_orchestrator(asset_id)
    elif action_id == "run_paper_trade":
        result = run_execution_paper_trade(asset_id)
    elif action_id == "refresh_telemetry_demo":
        result = save_demo_asset_telemetry(asset_id)
    else:
        result = {}

    return {
        "status": "ok",
        "asset_id": asset_id,
        "action_id": action_id,
        "action": SAFE_ACTIONS[action_id],
        "message": f"AI supervisor safe action completed: {SAFE_ACTIONS[action_id]['label']}",
        "result": result,
    }
