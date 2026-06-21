from fastapi import APIRouter

from backend.api.schemas import ApiResponse
from backend.data_environment import current_data_mode
from backend.agents.trading_supervisor import build_trading_supervisor_status
from backend.ai_intelligence.history import list_trading_supervisor_history
from backend.ai_intelligence.persona_agents import (
    build_persona_agent_status,
    list_persona_agents,
)
from backend.ai_intelligence.registry import list_ai_agents
from backend.ai_intelligence.safe_actions import list_safe_actions, run_safe_action


router = APIRouter()


@router.get("/agents", response_model=ApiResponse)
def ai_agents():
    return list_ai_agents()


@router.get("/agents/personas", response_model=ApiResponse)
def persona_agents():
    return list_persona_agents()


@router.get(
    "/assets/{asset_id}/agents/persona/{persona_id}/status",
    response_model=ApiResponse,
)
def asset_persona_agent_status(
    asset_id: str,
    persona_id: str,
    include_ai_brief: bool = False,
    evidence_mode: str | None = None,
):
    try:
        return build_persona_agent_status(
            asset_id=asset_id,
            persona_id=persona_id,
            include_ai_brief=include_ai_brief,
            operator_question=None,
            evidence_mode=evidence_mode or current_data_mode(),
        )
    except ValueError as error:
        return {
            "status": "not_found",
            "asset_id": asset_id,
            "persona_id": persona_id,
            "message": str(error),
        }
    except Exception as error:
        return {
            "status": "error",
            "asset_id": asset_id,
            "persona_id": persona_id,
            "message": f"Could not build persona AI agent status: {error}",
        }


@router.post(
    "/assets/{asset_id}/agents/persona/{persona_id}/run",
    response_model=ApiResponse,
)
def run_asset_persona_agent(
    asset_id: str,
    persona_id: str,
    payload: dict | None = None,
):
    payload = payload or {}
    operator_question = payload.get("question")
    evidence_mode = payload.get("evidence_mode") or current_data_mode()

    try:
        return build_persona_agent_status(
            asset_id=asset_id,
            persona_id=persona_id,
            include_ai_brief=bool(payload.get("include_ai_brief", True)),
            operator_question=str(operator_question) if operator_question else None,
            evidence_mode=str(evidence_mode),
        )
    except ValueError as error:
        return {
            "status": "not_found",
            "asset_id": asset_id,
            "persona_id": persona_id,
            "message": str(error),
        }
    except Exception as error:
        return {
            "status": "error",
            "asset_id": asset_id,
            "persona_id": persona_id,
            "message": f"Could not run persona AI agent: {error}",
        }


@router.get(
    "/assets/{asset_id}/agents/trading-supervisor/status",
    response_model=ApiResponse,
)
def asset_trading_supervisor_status(
    asset_id: str,
    include_ai_brief: bool = False,
    evidence_mode: str | None = None,
):
    try:
        return build_trading_supervisor_status(
            asset_id=asset_id,
            include_ai_brief=include_ai_brief,
            evidence_mode=evidence_mode or current_data_mode(),
            record_history=False,
            operator_question=None,
        )
    except ValueError as error:
        return {
            "status": "not_found",
            "asset_id": asset_id,
            "message": str(error),
        }
    except Exception as error:
        return {
            "status": "error",
            "asset_id": asset_id,
            "message": f"Could not build AI trading supervisor status: {error}",
        }


@router.post(
    "/assets/{asset_id}/agents/trading-supervisor/run",
    response_model=ApiResponse,
)
def run_asset_trading_supervisor(asset_id: str, payload: dict | None = None):
    payload = payload or {}
    include_ai_brief = bool(payload.get("include_ai_brief", True))
    evidence_mode = payload.get("evidence_mode") or current_data_mode()
    operator_question = payload.get("question")
    record_history = bool(payload.get("record_history", True))

    try:
        return build_trading_supervisor_status(
            asset_id=asset_id,
            include_ai_brief=include_ai_brief,
            evidence_mode=str(evidence_mode),
            record_history=record_history,
            operator_question=str(operator_question) if operator_question else None,
        )
    except ValueError as error:
        return {
            "status": "not_found",
            "asset_id": asset_id,
            "message": str(error),
        }
    except Exception as error:
        return {
            "status": "error",
            "asset_id": asset_id,
            "message": f"Could not run AI trading supervisor agent: {error}",
        }


@router.get(
    "/assets/{asset_id}/agents/trading-supervisor/history",
    response_model=ApiResponse,
)
def asset_trading_supervisor_history(asset_id: str, limit: int = 20):
    return list_trading_supervisor_history(asset_id=asset_id, limit=limit)


@router.get(
    "/assets/{asset_id}/agents/trading-supervisor/actions",
    response_model=ApiResponse,
)
def asset_trading_supervisor_actions(asset_id: str):
    return {
        "status": "ok",
        "asset_id": asset_id,
        "actions": list_safe_actions(),
    }


@router.post(
    "/assets/{asset_id}/agents/trading-supervisor/actions/{action_id}",
    response_model=ApiResponse,
)
def run_asset_trading_supervisor_action(asset_id: str, action_id: str):
    try:
        return run_safe_action(asset_id=asset_id, action_id=action_id)
    except Exception as error:
        return {
            "status": "error",
            "asset_id": asset_id,
            "action_id": action_id,
            "message": f"Could not run AI supervisor safe action: {error}",
        }
