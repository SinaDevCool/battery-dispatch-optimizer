from datetime import datetime

from backend.assets.asset_loader import get_asset
from backend.db.repositories.execution_repository import (
    get_latest_automation_policy,
    list_automation_policies,
    save_automation_policy,
)
from backend.execution.market_adapters.registry import get_asset_market_adapter_status
from backend.execution.pretrade_proposal import numeric


DEFAULT_ALLOWED_MARKETS = [
    "epex_day_ahead",
    "epex_intraday_auction",
    "epex_intraday_continuous",
    "regelleistung_fcr",
    "regelleistung_afrr",
    "regelleistung_mfrr",
]


MARKET_CRITICALITY = {
    "epex_day_ahead": "base_schedule",
    "epex_intraday_auction": "schedule_refinement",
    "epex_intraday_continuous": "rebalancing",
    "regelleistung_fcr": "reserve_capacity",
    "regelleistung_afrr": "reserve_capacity_energy",
    "regelleistung_mfrr": "manual_reserve_capacity_energy",
}


def latest_automation_policy(asset_id):
    record = get_latest_automation_policy(asset_id)

    if record is not None:
        policy = record["payload"]
        policy["automation_policy_id"] = record["automation_policy_id"]
        return {
            "status": "ok",
            "asset_id": asset_id,
            "policy": policy,
            "source": "database",
        }

    policy = build_default_automation_policy(asset_id)

    return {
        "status": "ok",
        "asset_id": asset_id,
        "policy": policy,
        "source": "default",
    }


def automation_policy_history(asset_id, limit=25):
    return {
        "status": "ok",
        "asset_id": asset_id,
        "policies": list_automation_policies(asset_id=asset_id, limit=limit),
    }


def create_default_automation_policy(asset_id):
    policy = build_default_automation_policy(asset_id)
    policy_id = save_automation_policy(policy)
    policy["automation_policy_id"] = policy_id

    return {
        "status": "ok",
        "asset_id": asset_id,
        "policy": policy,
        "message": "Default supervised automation policy saved.",
    }


def upsert_automation_policy(asset_id, payload=None):
    policy = merge_policy(
        base=build_default_automation_policy(asset_id),
        updates=payload or {},
    )
    policy["asset_id"] = asset_id
    policy["updated_at"] = datetime.now().isoformat(timespec="seconds")
    policy_id = save_automation_policy(policy)
    policy["automation_policy_id"] = policy_id

    return {
        "status": "ok",
        "asset_id": asset_id,
        "policy": policy,
        "message": "Automation policy saved.",
    }


def evaluate_automation_policy(
    asset_id,
    forecast_confidence=None,
    proposal=None,
    paper_trade=None,
    approval=None,
):
    policy_response = latest_automation_policy(asset_id)
    policy = policy_response["policy"]
    checks = build_policy_checks(
        policy=policy,
        forecast_confidence=forecast_confidence or {},
        proposal=proposal or {},
        paper_trade=paper_trade,
        approval=approval,
    )
    decision = classify_policy_decision(policy=policy, checks=checks)

    return {
        "status": "ok",
        "asset_id": asset_id,
        "policy": policy,
        "policy_source": policy_response.get("source"),
        "policy_decision": decision,
        "checks": checks,
        "summary": summarize_checks(checks),
        "recommended_actions": build_policy_actions(
            policy=policy,
            decision=decision,
            checks=checks,
        ),
    }


def build_default_automation_policy(asset_id):
    asset = get_asset(asset_id)
    commercial_config = asset.commercial_config or {}
    battery_config = asset.battery_config or {}
    grid_connection = asset.grid_connection or {}
    adapter_status = get_asset_market_adapter_status(asset_id)
    live_submission = bool(adapter_status.get("live_submission_enabled"))
    max_order_power = (
        numeric(commercial_config.get("max_order_power_mw"))
        or numeric(commercial_config.get("max_bid_volume_mw"))
        or numeric(grid_connection.get("max_export_mw"))
        or numeric(battery_config.get("max_discharge_power_mw"))
        or 1.0
    )

    return {
        "asset_id": asset_id,
        "policy_version": "2026-06-supervised-v1",
        "updated_at": datetime.now().isoformat(timespec="seconds"),
        "automation_mode": (
            "supervised_live" if live_submission else "paper_first"
        ),
        "allowed_markets": DEFAULT_ALLOWED_MARKETS,
        "risk_limits": {
            "max_daily_loss_eur": (
                numeric(commercial_config.get("max_daily_loss_eur")) or 2500.0
            ),
            "max_order_power_mw": round(max_order_power, 4),
            "max_cycles_per_day": (
                numeric(commercial_config.get("max_cycles_per_day")) or 1.5
            ),
            "max_open_notional_eur": (
                numeric(commercial_config.get("max_open_notional_eur")) or 10000.0
            ),
        },
        "confidence_policy": {
            "min_confidence_score": 70.0,
            "min_confidence_band": "high",
            "medium_confidence_action": "human_approval",
            "low_confidence_action": "paper_only",
        },
        "approval_policy": {
            "require_human_approval": True,
            "auto_approve_below_power_mw": 0.0,
            "four_eyes_required_above_power_mw": max(1.0, round(max_order_power, 4)),
        },
        "simulation_policy": {
            "require_paper_trade": True,
            "max_paper_vs_expected_delta_eur": 250.0,
        },
        "fallback_policy": {
            "mode": "pause_to_advisory",
            "on_missing_forecast": "paper_only",
            "on_missing_telemetry": "pause",
            "on_adapter_unavailable": "paper_only",
        },
        "market_roles": [
            {
                "adapter_id": adapter_id,
                "role": MARKET_CRITICALITY[adapter_id],
                "automation_scope": (
                    "paper_and_supervised_live"
                    if adapter_id in ["epex_day_ahead", "epex_intraday_auction"]
                    else "paper_until_credentials_validated"
                ),
            }
            for adapter_id in DEFAULT_ALLOWED_MARKETS
        ],
    }


def build_policy_checks(policy, forecast_confidence, proposal, paper_trade, approval):
    checks = [
        automation_mode_check(policy),
        allowed_market_check(policy=policy, proposal=proposal),
        confidence_threshold_check(
            policy=policy,
            forecast_confidence=forecast_confidence,
        ),
        max_daily_loss_check(policy=policy, proposal=proposal),
        max_order_power_check(policy=policy, proposal=proposal),
        paper_trade_policy_check(policy=policy, paper_trade=paper_trade),
        approval_policy_check(policy=policy, proposal=proposal, approval=approval),
    ]

    return checks


def automation_mode_check(policy):
    mode = policy.get("automation_mode")
    if mode == "disabled":
        return policy_check(
            "automation_mode",
            "blocked",
            "Automation mode is disabled by policy.",
            {"automation_mode": mode},
        )

    if mode in ["paper_first", "supervised_live"]:
        return policy_check(
            "automation_mode",
            "passed",
            "Automation mode allows governed execution workflow.",
            {"automation_mode": mode},
        )

    return policy_check(
        "automation_mode",
        "review",
        "Automation mode requires operator interpretation.",
        {"automation_mode": mode},
    )


def allowed_market_check(policy, proposal):
    market_product_id = first_order_value(proposal, "market_product_id")
    inferred_adapter = infer_adapter_from_product(market_product_id)
    allowed_markets = policy.get("allowed_markets", [])

    if not inferred_adapter:
        return policy_check(
            "allowed_market",
            "review",
            "No market adapter could be inferred from the latest proposal.",
            {"market_product_id": market_product_id},
        )

    status = "passed" if inferred_adapter in allowed_markets else "blocked"

    return policy_check(
        "allowed_market",
        status,
        (
            "Proposal market is allowed by automation policy."
            if status == "passed"
            else "Proposal market is not allowed by automation policy."
        ),
        {
            "adapter_id": inferred_adapter,
            "allowed_markets": allowed_markets,
            "market_product_id": market_product_id,
        },
    )


def confidence_threshold_check(policy, forecast_confidence):
    confidence_policy = policy.get("confidence_policy", {})
    score = numeric(forecast_confidence.get("confidence_score"))
    min_score = numeric(confidence_policy.get("min_confidence_score")) or 70.0
    band = forecast_confidence.get("confidence_band")
    min_band = confidence_policy.get("min_confidence_band") or "high"

    if score >= min_score and band_rank(band) >= band_rank(min_band):
        status = "passed"
    elif band == "medium":
        status = "review"
    else:
        status = "blocked"

    return policy_check(
        "confidence_threshold",
        status,
        (
            "Forecast confidence clears automation policy."
            if status == "passed"
            else "Forecast confidence does not clear automatic submission policy."
        ),
        {
            "confidence_score": score,
            "min_confidence_score": min_score,
            "confidence_band": band,
            "min_confidence_band": min_band,
        },
    )


def max_daily_loss_check(policy, proposal):
    expected_pnl = numeric((proposal.get("summary") or {}).get("expected_pnl_eur"))
    max_daily_loss = numeric(
        (policy.get("risk_limits") or {}).get("max_daily_loss_eur")
    )
    status = "passed" if expected_pnl >= -max_daily_loss else "blocked"

    return policy_check(
        "max_daily_loss",
        status,
        (
            "Expected PnL is inside policy loss limits."
            if status == "passed"
            else "Expected PnL breaches policy loss limits."
        ),
        {
            "expected_pnl_eur": expected_pnl,
            "max_daily_loss_eur": max_daily_loss,
        },
    )


def max_order_power_check(policy, proposal):
    max_policy_power = numeric(
        (policy.get("risk_limits") or {}).get("max_order_power_mw")
    )
    max_order_power = max(
        [
            numeric(order.get("risk_adjusted_volume_mw") or order.get("volume_mw"))
            for order in proposal_orders(proposal)
        ]
        or [0.0]
    )

    if max_order_power <= 0:
        status = "review"
    else:
        status = "passed" if max_order_power <= max_policy_power else "blocked"

    return policy_check(
        "max_order_power",
        status,
        (
            "Order sizing is inside policy power limits."
            if status == "passed"
            else "Order sizing requires review against policy power limits."
            if status == "review"
            else "Order sizing breaches policy power limits."
        ),
        {
            "max_order_power_mw": round(max_order_power, 4),
            "policy_max_order_power_mw": max_policy_power,
        },
    )


def paper_trade_policy_check(policy, paper_trade):
    requires_paper = bool(
        (policy.get("simulation_policy") or {}).get("require_paper_trade")
    )
    if not requires_paper:
        return policy_check(
            "paper_trade_required",
            "passed",
            "Policy does not require paper trade evidence.",
            {"require_paper_trade": False},
        )

    if not paper_trade:
        return policy_check(
            "paper_trade_required",
            "blocked",
            "Policy requires a paper trade before live or supervised execution.",
            {"require_paper_trade": True},
        )

    return policy_check(
        "paper_trade_required",
        "passed",
        "Paper trade evidence exists for this asset.",
        {
            "paper_trade_id": paper_trade.get("paper_trade_id"),
            "paper_pnl_eur": (paper_trade.get("summary") or {}).get("paper_pnl_eur"),
        },
    )


def approval_policy_check(policy, proposal, approval):
    requires_approval = bool(
        (policy.get("approval_policy") or {}).get("require_human_approval")
    )

    if not requires_approval:
        return policy_check(
            "human_approval_required",
            "passed",
            "Policy allows auto approval for this route.",
            {"require_human_approval": False},
        )

    if not approval:
        return policy_check(
            "human_approval_required",
            "review",
            "Policy requires human approval before submission.",
            {"require_human_approval": True},
        )

    if approval.get("execution_proposal_id") != proposal.get("execution_proposal_id"):
        return policy_check(
            "human_approval_required",
            "blocked",
            "Latest approval does not match the latest proposal.",
            {
                "approval_id": approval.get("approval_id"),
                "approval_status": approval.get("status"),
            },
        )

    status = "passed" if approval.get("status") == "approved" else "review"

    return policy_check(
        "human_approval_required",
        status,
        (
            "Latest proposal has human approval."
            if status == "passed"
            else "Human approval is not complete."
        ),
        {
            "approval_id": approval.get("approval_id"),
            "approval_status": approval.get("status"),
        },
    )


def classify_policy_decision(policy, checks):
    statuses = {check["status"] for check in checks}
    mode = policy.get("automation_mode")

    if mode == "disabled" or "blocked" in statuses:
        return "blocked"

    if mode == "paper_first":
        return "paper_only" if "review" in statuses else "paper_ready"

    if mode == "supervised_live":
        return "human_approval_required" if "review" in statuses else "supervised_live_candidate"

    return "human_approval_required"


def build_policy_actions(policy, decision, checks):
    actions = []

    for check in checks:
        if check["status"] == "blocked":
            actions.append(f"Clear policy blocker: {check['message']}")
        elif check["status"] == "review":
            actions.append(f"Review policy item: {check['message']}")

    if decision == "paper_ready":
        actions.append("Run paper market validation before supervised execution.")
    elif decision == "supervised_live_candidate":
        actions.append("Prepare supervised live submission with audit capture.")
    elif decision == "blocked":
        actions.append(
            f"Apply fallback mode: {(policy.get('fallback_policy') or {}).get('mode')}"
        )

    return dedupe(actions)


def summarize_checks(checks):
    return {
        "passed": len([check for check in checks if check["status"] == "passed"]),
        "review": len([check for check in checks if check["status"] == "review"]),
        "blocked": len([check for check in checks if check["status"] == "blocked"]),
        "total": len(checks),
    }


def merge_policy(base, updates):
    merged = dict(base)

    for key, value in updates.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = {
                **merged[key],
                **value,
            }
        else:
            merged[key] = value

    return merged


def market_allowed_by_policy(asset_id, adapter_id):
    policy = latest_automation_policy(asset_id)["policy"]
    allowed_markets = policy.get("allowed_markets", [])

    return adapter_id in allowed_markets


def policy_check(check, status, message, context):
    return {
        "check": check,
        "status": status,
        "message": message,
        "context": context,
    }


def first_order_value(proposal, key):
    for order in proposal_orders(proposal):
        value = order.get(key)
        if value:
            return value

    return None


def proposal_orders(proposal):
    return proposal.get("bids") or proposal.get("orders") or []


def infer_adapter_from_product(product_id):
    if product_id == "day_ahead_arbitrage":
        return "epex_day_ahead"

    if product_id == "intraday_arbitrage":
        return "epex_intraday_continuous"

    if product_id == "fcr_capacity":
        return "regelleistung_fcr"

    if product_id == "afrr_capacity":
        return "regelleistung_afrr"

    if product_id == "mfrr_capacity":
        return "regelleistung_mfrr"

    return None


def band_rank(band):
    return {
        "low": 1,
        "medium": 2,
        "high": 3,
    }.get(band, 0)


def dedupe(items):
    seen = set()
    result = []

    for item in items:
        if not item or item in seen:
            continue

        seen.add(item)
        result.append(item)

    return result



