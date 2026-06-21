from __future__ import annotations

from datetime import datetime
from typing import Any, Callable

from backend.config.paths import ACTUAL_PRICE_FILE, FORECAST_FILE
from backend.backtesting.forecast_actual.forecast_actual_runner import (
    load_latest_forecast_actual_result,
    run_forecast_actual_backtest,
)
from backend.execution.paper_trading import run_execution_paper_trade
from backend.execution.pretrade_proposal import build_execution_proposal
from backend.revenue.revenue_stack_allocator import (
    load_latest_revenue_stack_allocation,
    run_revenue_stack_allocation,
)
from backend.revenue.revenue_stack_runner import (
    load_latest_asset_revenue_stack,
    run_asset_revenue_stack,
)
from backend.services.asset_signal_store import load_asset_latest_signal
from backend.services.demo_portfolio_service import seed_demo_forecasts
from backend.settlement.settlement_reconciliation import (
    latest_settlement_reconciliation,
    run_settlement_reconciliation,
)
from backend.telemetry.asset_telemetry import latest_asset_telemetry, save_demo_asset_telemetry


QUESTION_EVIDENCE_MAP = {
    "forecast_optimizer_trust": [
        "demo_forecasts",
        "signal",
        "forecast_actual",
    ],
    "revenue_opportunity": [
        "demo_forecasts",
        "signal",
        "revenue_stack",
        "revenue_allocation",
        "execution_proposal",
        "paper_trade",
        "forecast_actual",
        "settlement",
    ],
    "settlement_explanation": [
        "demo_forecasts",
        "signal",
        "execution_proposal",
        "paper_trade",
        "forecast_actual",
        "settlement",
    ],
    "stakeholder_update": [
        "demo_forecasts",
        "signal",
        "revenue_stack",
        "revenue_allocation",
        "execution_proposal",
        "paper_trade",
        "forecast_actual",
        "settlement",
        "telemetry",
    ],
    "production_gap_prioritization": [
        "demo_forecasts",
        "signal",
        "revenue_stack",
        "revenue_allocation",
        "execution_proposal",
        "paper_trade",
        "forecast_actual",
        "settlement",
        "telemetry",
    ],
    "evidence_gap": [
        "demo_forecasts",
        "signal",
        "revenue_stack",
        "revenue_allocation",
        "execution_proposal",
        "paper_trade",
        "forecast_actual",
        "settlement",
        "telemetry",
    ],
    "connector_onboarding": [
        "demo_forecasts",
        "signal",
        "execution_proposal",
        "telemetry",
    ],
    "trading_action": [
        "demo_forecasts",
        "signal",
        "execution_proposal",
        "paper_trade",
        "telemetry",
    ],
    "general_persona_answer": [
        "demo_forecasts",
        "signal",
        "revenue_stack",
        "forecast_actual",
    ],
}


def ensure_mock_evidence(asset_id: str, question_intent: str) -> dict[str, Any]:
    required = QUESTION_EVIDENCE_MAP.get(
        question_intent,
        QUESTION_EVIDENCE_MAP["general_persona_answer"],
    )
    step_results = []

    for step_id in required:
        step_results.append(ensure_step(asset_id=asset_id, step_id=step_id))

    available = [step for step in step_results if step["available"]]
    generated = [step["step_id"] for step in step_results if step["generated"]]
    missing = [step for step in step_results if not step["available"]]

    return {
        "status": "ready" if not missing else "partial",
        "asset_id": asset_id,
        "question_intent": question_intent,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "required_count": len(required),
        "available_count": len(available),
        "missing_count": len(missing),
        "generated_steps": generated,
        "missing_steps": [
            {
                "step_id": step["step_id"],
                "label": step["label"],
                "message": step.get("message"),
            }
            for step in missing
        ],
        "steps": step_results,
    }


def ensure_step(asset_id: str, step_id: str) -> dict[str, Any]:
    spec = STEP_SPECS[step_id]
    before = safe_check(spec["check"], asset_id)
    if before["available"]:
        return {
            **before,
            "step_id": step_id,
            "label": spec["label"],
            "generated": False,
        }

    generation = safe_generate(spec["generate"], asset_id)
    after = safe_check(spec["check"], asset_id)
    return {
        **after,
        "step_id": step_id,
        "label": spec["label"],
        "generated": generation["status"] == "ok" and after["available"],
        "generation_status": generation["status"],
        "generation_message": generation.get("message"),
    }


def safe_check(checker: Callable[[str], dict[str, Any]], asset_id: str) -> dict[str, Any]:
    try:
        return checker(asset_id)
    except Exception as error:
        return {
            "available": False,
            "status": "error",
            "message": str(error),
        }


def safe_generate(generator: Callable[[str], Any], asset_id: str) -> dict[str, Any]:
    try:
        result = generator(asset_id)
        status = result.get("status") if isinstance(result, dict) else "ok"
        if status in {"ok", "ready", "partial"}:
            return {"status": "ok", "result": result}
        return {
            "status": "error",
            "message": result.get("message") if isinstance(result, dict) else str(result),
            "result": result,
        }
    except Exception as error:
        return {
            "status": "error",
            "message": str(error),
        }


def check_ok(response: dict[str, Any], payload_key: str | None = None) -> dict[str, Any]:
    status = response.get("status")
    payload_available = True if payload_key is None else bool(response.get(payload_key))
    available = status in {"ok", "ready"} and payload_available
    return {
        "available": available,
        "status": status or "missing",
        "message": response.get("message"),
    }


def check_demo_forecasts(asset_id: str) -> dict[str, Any]:
    available = FORECAST_FILE.exists() and ACTUAL_PRICE_FILE.exists()
    return {
        "available": available,
        "status": "ok" if available else "missing",
        "message": (
            "Mock forecast and actual-price files are available."
            if available
            else "Mock forecast or actual-price file is missing."
        ),
    }


def generate_demo_forecasts(asset_id: str):
    return seed_demo_forecasts()


def check_signal(asset_id: str) -> dict[str, Any]:
    return check_ok(load_asset_latest_signal(asset_id), payload_key="data")


def generate_signal(asset_id: str):
    from backend.api.routes.asset_signals import run_asset_latest_signal

    return run_asset_latest_signal(asset_id=asset_id)


def check_revenue_stack(asset_id: str) -> dict[str, Any]:
    response = load_latest_asset_revenue_stack(asset_id)
    available = response.get("status") == "ok" and bool(response.get("products"))
    return {
        "available": available,
        "status": response.get("status", "missing"),
        "message": response.get("message"),
    }


def generate_revenue_stack(asset_id: str):
    return run_asset_revenue_stack(asset_id=asset_id)


def check_revenue_allocation(asset_id: str) -> dict[str, Any]:
    response = load_latest_revenue_stack_allocation(asset_id)
    available = response.get("status") == "ok" and bool(
        response.get("allocation") or response.get("results")
    )
    return {
        "available": available,
        "status": response.get("status", "missing"),
        "message": response.get("message"),
    }


def generate_revenue_allocation(asset_id: str):
    return run_revenue_stack_allocation(asset_id=asset_id)


def check_forecast_actual(asset_id: str) -> dict[str, Any]:
    response = load_latest_forecast_actual_result(asset_id)
    return check_ok(response)


def generate_forecast_actual(asset_id: str):
    return run_forecast_actual_backtest(asset_id=asset_id)


def check_settlement(asset_id: str) -> dict[str, Any]:
    return check_ok(latest_settlement_reconciliation(asset_id), payload_key="settlement")


def generate_settlement(asset_id: str):
    return run_settlement_reconciliation(asset_id)


def check_telemetry(asset_id: str) -> dict[str, Any]:
    return check_ok(latest_asset_telemetry(asset_id), payload_key="telemetry")


def generate_telemetry(asset_id: str):
    return save_demo_asset_telemetry(asset_id)


def check_execution_proposal(asset_id: str) -> dict[str, Any]:
    from backend.db.repositories.execution_repository import get_latest_execution_proposal

    record = get_latest_execution_proposal(asset_id)
    return {
        "available": bool(record),
        "status": "ok" if record else "missing",
        "message": None if record else "No mock execution proposal found.",
    }


def generate_execution_proposal(asset_id: str):
    return build_execution_proposal(asset_id)


def check_paper_trade(asset_id: str) -> dict[str, Any]:
    from backend.db.repositories.execution_repository import get_latest_execution_paper_trade

    record = get_latest_execution_paper_trade(asset_id)
    return {
        "available": bool(record),
        "status": "ok" if record else "missing",
        "message": None if record else "No mock paper trade found.",
    }


def generate_paper_trade(asset_id: str):
    return run_execution_paper_trade(asset_id)


STEP_SPECS = {
    "demo_forecasts": {
        "label": "Mock forecast and actual-price seed",
        "check": check_demo_forecasts,
        "generate": generate_demo_forecasts,
    },
    "signal": {
        "label": "Optimizer signal",
        "check": check_signal,
        "generate": generate_signal,
    },
    "revenue_stack": {
        "label": "Revenue stack",
        "check": check_revenue_stack,
        "generate": generate_revenue_stack,
    },
    "revenue_allocation": {
        "label": "Revenue allocation",
        "check": check_revenue_allocation,
        "generate": generate_revenue_allocation,
    },
    "execution_proposal": {
        "label": "Execution proposal",
        "check": check_execution_proposal,
        "generate": generate_execution_proposal,
    },
    "paper_trade": {
        "label": "Paper trade",
        "check": check_paper_trade,
        "generate": generate_paper_trade,
    },
    "forecast_actual": {
        "label": "Forecast-vs-actual backtest",
        "check": check_forecast_actual,
        "generate": generate_forecast_actual,
    },
    "settlement": {
        "label": "Settlement reconciliation",
        "check": check_settlement,
        "generate": generate_settlement,
    },
    "telemetry": {
        "label": "Telemetry snapshot",
        "check": check_telemetry,
        "generate": generate_telemetry,
    },
}
