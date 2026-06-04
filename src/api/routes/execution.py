from fastapi import APIRouter

from src.api.schemas import ApiResponse
from src.execution.approval_workflow import (
    approve_execution_proposal,
    execution_approval_history,
    latest_execution_approval,
    reject_execution_proposal,
    request_execution_approval,
)
from src.execution.automation_guardrails import latest_automation_guardrails
from src.execution.automation_policy import (
    automation_policy_history,
    create_default_automation_policy,
    evaluate_automation_policy,
    latest_automation_policy,
    upsert_automation_policy,
)
from src.execution.execution_readiness import build_execution_readiness
from src.execution.epex_day_ahead_preview import latest_epex_day_ahead_preview
from src.execution.epex_intraday_auction_preview import (
    latest_epex_intraday_auction_preview,
)
from src.execution.epex_intraday_continuous_preview import (
    latest_epex_intraday_continuous_preview,
)
from src.execution.regelleistung_fcr_preview import latest_regelleistung_fcr_preview
from src.execution.regelleistung_afrr_preview import latest_regelleistung_afrr_preview
from src.execution.regelleistung_mfrr_preview import latest_regelleistung_mfrr_preview
from src.execution.market_submission import (
    latest_market_submission,
    market_submission_history,
    run_demo_market_submission,
)
from src.execution.market_connector_readiness import market_connector_readiness
from src.execution.multi_market_allocator import build_multi_market_allocation
from src.execution.market_adapters.registry import (
    get_asset_market_adapter_status,
    list_market_adapters,
)
from src.execution.pretrade_proposal import (
    build_execution_proposal,
    execution_proposal_history,
    latest_execution_proposal,
)
from src.execution.paper_trading import (
    execution_paper_trade_history,
    latest_execution_paper_trade,
    run_execution_paper_trade,
)
from src.execution.trading_orchestrator import (
    run_trading_orchestrator,
    trading_orchestrator_status,
)


router = APIRouter()


@router.get(
    "/execution/market-adapters",
    response_model=ApiResponse,
)
def execution_market_adapters(country: str | None = None):
    return {
        "status": "ok",
        "country": country or "all",
        "adapters": list_market_adapters(country=country),
    }


@router.get(
    "/execution/market-connectors/readiness",
    response_model=ApiResponse,
)
def execution_market_connectors_readiness(country: str = "Germany"):
    try:
        return market_connector_readiness(country=country)
    except Exception as error:
        return {
            "status": "error",
            "country": country,
            "message": f"Could not evaluate market connector readiness: {error}",
        }


@router.get(
    "/assets/{asset_id}/execution/market-adapter/status",
    response_model=ApiResponse,
)
def asset_execution_market_adapter_status(asset_id: str):
    return get_asset_market_adapter_status(asset_id)


@router.get(
    "/assets/{asset_id}/execution/multi-market/allocation",
    response_model=ApiResponse,
)
def asset_execution_multi_market_allocation(
    asset_id: str,
    refresh_revenue_stack: bool = False,
):
    try:
        return build_multi_market_allocation(
            asset_id=asset_id,
            refresh_revenue_stack=refresh_revenue_stack,
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
            "message": f"Could not build multi-market allocation: {error}",
        }


@router.get(
    "/assets/{asset_id}/execution/orchestrator/status",
    response_model=ApiResponse,
)
def asset_execution_orchestrator_status(asset_id: str):
    try:
        return trading_orchestrator_status(asset_id)
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
            "message": f"Could not evaluate trading orchestrator: {error}",
        }


@router.post(
    "/assets/{asset_id}/execution/orchestrator/run",
    response_model=ApiResponse,
)
def run_asset_execution_orchestrator(asset_id: str):
    try:
        return run_trading_orchestrator(asset_id)
    except ValueError as error:
        return {
            "status": "invalid",
            "asset_id": asset_id,
            "message": str(error),
        }
    except FileNotFoundError as error:
        return {
            "status": "not_found",
            "asset_id": asset_id,
            "message": str(error),
        }
    except PermissionError as error:
        return {
            "status": "blocked",
            "asset_id": asset_id,
            "message": str(error),
        }
    except Exception as error:
        return {
            "status": "error",
            "asset_id": asset_id,
            "message": f"Could not run trading orchestrator: {error}",
        }


@router.get(
    "/assets/{asset_id}/execution/epex/day-ahead/preview",
    response_model=ApiResponse,
)
def asset_epex_day_ahead_preview(asset_id: str):
    try:
        return latest_epex_day_ahead_preview(asset_id)
    except FileNotFoundError as error:
        return {
            "status": "not_found",
            "asset_id": asset_id,
            "message": str(error),
            "preview": None,
        }


@router.get(
    "/assets/{asset_id}/execution/epex/intraday-auction/preview",
    response_model=ApiResponse,
)
def asset_epex_intraday_auction_preview(asset_id: str):
    try:
        return latest_epex_intraday_auction_preview(asset_id)
    except FileNotFoundError as error:
        return {
            "status": "not_found",
            "asset_id": asset_id,
            "message": str(error),
            "preview": None,
        }


@router.get(
    "/assets/{asset_id}/execution/epex/intraday-continuous/preview",
    response_model=ApiResponse,
)
def asset_epex_intraday_continuous_preview(asset_id: str):
    try:
        return latest_epex_intraday_continuous_preview(asset_id)
    except FileNotFoundError as error:
        return {
            "status": "not_found",
            "asset_id": asset_id,
            "message": str(error),
            "preview": None,
        }


@router.get(
    "/assets/{asset_id}/execution/regelleistung/fcr/preview",
    response_model=ApiResponse,
)
def asset_regelleistung_fcr_preview(asset_id: str):
    try:
        return latest_regelleistung_fcr_preview(asset_id)
    except ValueError as error:
        return {
            "status": "not_found",
            "asset_id": asset_id,
            "message": str(error),
            "preview": None,
        }


@router.get(
    "/assets/{asset_id}/execution/regelleistung/afrr/preview",
    response_model=ApiResponse,
)
def asset_regelleistung_afrr_preview(asset_id: str):
    try:
        return latest_regelleistung_afrr_preview(asset_id)
    except ValueError as error:
        return {
            "status": "not_found",
            "asset_id": asset_id,
            "message": str(error),
            "preview": None,
        }


@router.get(
    "/assets/{asset_id}/execution/regelleistung/mfrr/preview",
    response_model=ApiResponse,
)
def asset_regelleistung_mfrr_preview(asset_id: str):
    try:
        return latest_regelleistung_mfrr_preview(asset_id)
    except ValueError as error:
        return {
            "status": "not_found",
            "asset_id": asset_id,
            "message": str(error),
            "preview": None,
        }


@router.post(
    "/assets/{asset_id}/execution/proposal/build",
    response_model=ApiResponse,
)
def build_asset_execution_proposal(asset_id: str):
    try:
        proposal = build_execution_proposal(asset_id)
    except ValueError as error:
        return {
            "status": "not_found",
            "message": str(error),
        }
    except FileNotFoundError as error:
        return {
            "status": "not_found",
            "message": str(error),
        }
    except Exception as error:
        return {
            "status": "error",
            "message": f"Could not build execution proposal: {error}",
        }

    return {
        "status": "ok",
        "asset_id": asset_id,
        "proposal": proposal,
    }


@router.get(
    "/assets/{asset_id}/execution/proposal/latest",
    response_model=ApiResponse,
)
def latest_asset_execution_proposal(asset_id: str):
    return latest_execution_proposal(asset_id)


@router.get(
    "/assets/{asset_id}/execution/proposals",
    response_model=ApiResponse,
)
def asset_execution_proposals(asset_id: str, limit: int = 25):
    return execution_proposal_history(asset_id=asset_id, limit=limit)


@router.post(
    "/assets/{asset_id}/execution/paper-trade/run",
    response_model=ApiResponse,
)
def run_asset_execution_paper_trade(asset_id: str):
    try:
        paper_trade = run_execution_paper_trade(asset_id)
    except ValueError as error:
        return {
            "status": "invalid",
            "asset_id": asset_id,
            "message": str(error),
        }
    except FileNotFoundError as error:
        return {
            "status": "not_found",
            "asset_id": asset_id,
            "message": str(error),
        }
    except PermissionError as error:
        return {
            "status": "blocked",
            "asset_id": asset_id,
            "message": str(error),
        }
    except Exception as error:
        return {
            "status": "error",
            "asset_id": asset_id,
            "message": f"Could not run execution paper trade: {error}",
        }

    return {
        "status": "ok",
        "asset_id": asset_id,
        "paper_trade": paper_trade,
    }


@router.get(
    "/assets/{asset_id}/execution/paper-trade/latest",
    response_model=ApiResponse,
)
def latest_asset_execution_paper_trade(asset_id: str):
    return latest_execution_paper_trade(asset_id)


@router.get(
    "/assets/{asset_id}/execution/paper-trades",
    response_model=ApiResponse,
)
def asset_execution_paper_trades(asset_id: str, limit: int = 25):
    return execution_paper_trade_history(asset_id=asset_id, limit=limit)


@router.get(
    "/assets/{asset_id}/execution/automation-guardrails",
    response_model=ApiResponse,
)
def asset_execution_automation_guardrails(asset_id: str):
    try:
        return latest_automation_guardrails(asset_id)
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
            "message": f"Could not evaluate automation guardrails: {error}",
        }


@router.get(
    "/assets/{asset_id}/execution/automation-policy",
    response_model=ApiResponse,
)
def asset_execution_automation_policy(asset_id: str):
    try:
        return latest_automation_policy(asset_id)
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
            "message": f"Could not load automation policy: {error}",
        }


@router.get(
    "/assets/{asset_id}/execution/automation-policy/evaluation",
    response_model=ApiResponse,
)
def asset_execution_automation_policy_evaluation(asset_id: str):
    try:
        return evaluate_automation_policy(asset_id)
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
            "message": f"Could not evaluate automation policy: {error}",
        }


@router.post(
    "/assets/{asset_id}/execution/automation-policy/default",
    response_model=ApiResponse,
)
def save_default_asset_execution_automation_policy(asset_id: str):
    try:
        return create_default_automation_policy(asset_id)
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
            "message": f"Could not save automation policy: {error}",
        }


@router.post(
    "/assets/{asset_id}/execution/automation-policy",
    response_model=ApiResponse,
)
def save_asset_execution_automation_policy(asset_id: str, policy: dict | None = None):
    try:
        return upsert_automation_policy(asset_id=asset_id, payload=policy)
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
            "message": f"Could not save automation policy: {error}",
        }


@router.get(
    "/assets/{asset_id}/execution/automation-policies",
    response_model=ApiResponse,
)
def asset_execution_automation_policy_history(asset_id: str, limit: int = 25):
    return automation_policy_history(asset_id=asset_id, limit=limit)


@router.get(
    "/assets/{asset_id}/execution/readiness",
    response_model=ApiResponse,
)
def asset_execution_readiness(asset_id: str):
    try:
        return build_execution_readiness(asset_id)
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
            "message": f"Could not evaluate execution readiness: {error}",
        }


@router.post(
    "/assets/{asset_id}/execution/demo-submit",
    response_model=ApiResponse,
)
def demo_submit_asset_bids(asset_id: str):
    try:
        submission = run_demo_market_submission(asset_id)
    except ValueError as error:
        return {
            "status": "invalid",
            "asset_id": asset_id,
            "message": str(error),
        }
    except FileNotFoundError as error:
        return {
            "status": "not_found",
            "asset_id": asset_id,
            "message": str(error),
        }
    except PermissionError as error:
        return {
            "status": "blocked",
            "asset_id": asset_id,
            "message": str(error),
        }
    except Exception as error:
        return {
            "status": "error",
            "asset_id": asset_id,
            "message": f"Could not run demo market submission: {error}",
        }

    return {
        "status": "ok",
        "asset_id": asset_id,
        "submission": submission,
    }


@router.get(
    "/assets/{asset_id}/execution/submissions/latest",
    response_model=ApiResponse,
)
def latest_asset_market_submission(asset_id: str):
    return latest_market_submission(asset_id)


@router.get(
    "/assets/{asset_id}/execution/submissions",
    response_model=ApiResponse,
)
def asset_market_submission_history(asset_id: str, limit: int = 25):
    return market_submission_history(asset_id=asset_id, limit=limit)


@router.post(
    "/assets/{asset_id}/execution/approval/request",
    response_model=ApiResponse,
)
def request_asset_execution_approval(asset_id: str):
    try:
        approval = request_execution_approval(asset_id)
    except FileNotFoundError as error:
        return {
            "status": "not_found",
            "asset_id": asset_id,
            "message": str(error),
        }

    return {
        "status": "ok",
        "asset_id": asset_id,
        "approval": approval,
    }


@router.post(
    "/assets/{asset_id}/execution/approval/approve",
    response_model=ApiResponse,
)
def approve_asset_execution(asset_id: str):
    try:
        approval = approve_execution_proposal(asset_id)
    except FileNotFoundError as error:
        return {
            "status": "not_found",
            "asset_id": asset_id,
            "message": str(error),
        }

    return {
        "status": "ok",
        "asset_id": asset_id,
        "approval": approval,
    }


@router.post(
    "/assets/{asset_id}/execution/approval/reject",
    response_model=ApiResponse,
)
def reject_asset_execution(asset_id: str):
    try:
        approval = reject_execution_proposal(asset_id)
    except FileNotFoundError as error:
        return {
            "status": "not_found",
            "asset_id": asset_id,
            "message": str(error),
        }

    return {
        "status": "ok",
        "asset_id": asset_id,
        "approval": approval,
    }


@router.get(
    "/assets/{asset_id}/execution/approval/latest",
    response_model=ApiResponse,
)
def latest_asset_execution_approval(asset_id: str):
    return latest_execution_approval(asset_id)


@router.get(
    "/assets/{asset_id}/execution/approvals",
    response_model=ApiResponse,
)
def asset_execution_approval_history(asset_id: str, limit: int = 25):
    return execution_approval_history(asset_id=asset_id, limit=limit)

