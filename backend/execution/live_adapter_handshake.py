import os
from datetime import datetime

from backend.db.repositories.execution_repository import (
    list_automation_event_payloads,
    save_automation_event,
)
from backend.execution.credential_readiness import build_credential_readiness


HANDSHAKE_DRILL_EVENT_TYPE = "live_adapter_handshake_drill"
DEFAULT_HANDSHAKE_ASSET_ID = "default_site"


EPEX_ROUTES = [
    "epex_day_ahead",
    "epex_intraday_auction",
    "epex_intraday_continuous",
]

REGELLEISTUNG_ROUTES = [
    "regelleistung_fcr",
    "regelleistung_afrr",
    "regelleistung_mfrr",
]


HANDSHAKE_TARGETS = [
    {
        "target_id": "epex_member_access",
        "label": "EPEX member or broker handshake",
        "group": "EPEX market access",
        "required_for": EPEX_ROUTES,
        "endpoint_env_keys": ["EPEX_API_URL", "EPEX_BROKER_API_URL"],
        "mode_env_key": "EPEX_HANDSHAKE_MODE",
        "expected_response_schema": [
            "member_id",
            "portfolio_id",
            "market_permissions",
            "clock",
        ],
        "next_action": "Configure EPEX endpoint and run a dry-run authentication handshake.",
    },
    {
        "target_id": "regelleistung_tso_access",
        "label": "regelleistung / TSO handshake",
        "group": "Ancillary services access",
        "required_for": REGELLEISTUNG_ROUTES,
        "endpoint_env_keys": ["REGELLEISTUNG_API_URL", "TSO_API_URL"],
        "mode_env_key": "REGELLEISTUNG_HANDSHAKE_MODE",
        "expected_response_schema": [
            "participant_id",
            "prequalification_id",
            "reserve_products",
            "submission_windows",
        ],
        "next_action": "Configure regelleistung or TSO endpoint and validate reserve-market dry-run access.",
    },
    {
        "target_id": "ems_scada_access",
        "label": "EMS / SCADA dispatch handshake",
        "group": "Asset telemetry",
        "required_for": ["asset_telemetry", "live_dispatch_feedback", *EPEX_ROUTES, *REGELLEISTUNG_ROUTES],
        "endpoint_env_keys": ["EMS_API_URL", "SCADA_API_URL"],
        "mode_env_key": "EMS_HANDSHAKE_MODE",
        "expected_response_schema": [
            "asset_id",
            "soc",
            "availability",
            "dispatch_acknowledgement",
        ],
        "next_action": "Configure EMS/SCADA endpoint and validate telemetry plus dispatch acknowledgement schema.",
    },
    {
        "target_id": "entsoe_market_data_access",
        "label": "ENTSO-E market data handshake",
        "group": "Market data",
        "required_for": ["forecast_provider", "actual_price_feed", *EPEX_ROUTES],
        "endpoint_env_keys": ["ENTSOE_API_URL"],
        "default_endpoint": "https://web-api.tp.entsoe.eu",
        "mode_env_key": "ENTSOE_HANDSHAKE_MODE",
        "expected_response_schema": [
            "bidding_zone",
            "period_start",
            "period_end",
            "price",
        ],
        "next_action": "Set ENTSO-E handshake mode to dry_run after the token is configured.",
    },
    {
        "target_id": "settlement_backoffice_access",
        "label": "Settlement / backoffice evidence handshake",
        "group": "Settlement evidence",
        "required_for": ["settlement_evidence", *EPEX_ROUTES, *REGELLEISTUNG_ROUTES],
        "endpoint_env_keys": ["SETTLEMENT_API_URL", "BACKOFFICE_API_URL"],
        "mode_env_key": "SETTLEMENT_HANDSHAKE_MODE",
        "expected_response_schema": [
            "award_id",
            "metered_delivery",
            "settlement_statement_id",
            "variance_reason",
        ],
        "next_action": "Configure settlement/backoffice endpoint and validate award, meter, and statement schema.",
    },
]


def build_live_adapter_handshake_readiness(country="Germany", asset_id=DEFAULT_HANDSHAKE_ASSET_ID):
    generated_at = datetime.now().isoformat(timespec="seconds")
    credential_readiness = build_credential_readiness()
    latest_evidence = load_latest_handshake_evidence(asset_id=asset_id)
    targets = [
        build_handshake_target_status(
            target,
            credential_readiness,
            generated_at,
            latest_evidence,
        )
        for target in HANDSHAKE_TARGETS
    ]
    env_checklist = build_handshake_env_checklist(
        targets=targets,
        credential_readiness=credential_readiness,
    )
    env_activation_guide = build_env_activation_guide(
        asset_id=asset_id,
        checklist=env_checklist,
        country=country,
    )
    routes = build_route_handshake_readiness(targets)
    summary = {
        **summarize_handshakes(targets, routes),
        **summarize_env_checklist(env_checklist),
        **summarize_env_activation_guide(env_activation_guide),
    }

    return {
        "status": "ok",
        "asset_id": asset_id,
        "country": country,
        "generated_at": generated_at,
        "handshake_readiness_status": classify_portfolio_handshake(summary),
        "summary": summary,
        "env_checklist": env_checklist,
        "env_activation_guide": env_activation_guide,
        "targets": targets,
        "routes": routes,
        "recommended_actions": build_handshake_actions(targets, routes),
    }


def get_route_handshake_readiness(adapter_id):
    readiness = build_live_adapter_handshake_readiness()
    return next(
        (
            route
            for route in readiness["routes"]
            if route["adapter_id"] == adapter_id
        ),
        {},
    )


def run_live_adapter_handshake_drill(
    asset_id=DEFAULT_HANDSHAKE_ASSET_ID,
    target_id=None,
    route_id=None,
    country="Germany",
):
    readiness = build_live_adapter_handshake_readiness(
        country=country,
        asset_id=asset_id,
    )
    if target_id and route_id:
        raise ValueError("Run a target drill or a route drill, not both.")

    route_target_ids = None
    if route_id:
        route = next(
            (
                route
                for route in readiness["routes"]
                if route.get("adapter_id") == route_id
            ),
            None,
        )
        if not route:
            raise ValueError(f"Unknown live adapter handshake route: {route_id}")
        route_target_ids = set(route.get("route_handshake_targets", []))

    selected_targets = [
        target
        for target in readiness["targets"]
        if (
            (target_id is None and route_target_ids is None)
            or target["target_id"] == target_id
            or (
                route_target_ids is not None
                and target["target_id"] in route_target_ids
            )
        )
    ]

    if target_id and not selected_targets:
        raise ValueError(f"Unknown live adapter handshake target: {target_id}")

    created_at = datetime.now().isoformat(timespec="seconds")
    results = [build_drill_result(target, created_at) for target in selected_targets]
    status = "passed" if results and all(result["status"] == "passed" for result in results) else "blocked"
    event = {
        "asset_id": asset_id,
        "created_at": created_at,
        "event_type": HANDSHAKE_DRILL_EVENT_TYPE,
        "action": drill_action(target_id=target_id, route_id=route_id),
        "status": status,
        "before": {
            "handshake_readiness_status": readiness.get(
                "handshake_readiness_status"
            ),
        },
        "after": {
            "drill_status": status,
            "passed_target_count": len(
                [result for result in results if result["status"] == "passed"]
            ),
            "target_count": len(results),
        },
        "action_result": {
            "action": drill_action(target_id=target_id, route_id=route_id),
            "status": status,
            "target_count": len(results),
        },
        "target_id": target_id,
        "route_id": route_id,
        "country": country,
        "order_submission_performed": False,
        "no_order_submission": True,
        "results": results,
    }
    event_id = save_automation_event(event)

    return {
        "status": status,
        "asset_id": asset_id,
        "country": country,
        "generated_at": created_at,
        "automation_event_id": event_id,
        "target_id": target_id,
        "route_id": route_id,
        "summary": {
            "target_count": len(results),
            "passed_count": len([result for result in results if result["status"] == "passed"]),
            "blocked_count": len([result for result in results if result["status"] == "blocked"]),
            "order_submission_performed": False,
        },
        "results": results,
        "recommended_actions": dedupe(
            result["next_handshake_action"]
            for result in results
            if result["status"] != "passed"
        ),
    }


def list_live_adapter_handshake_drills(
    asset_id=DEFAULT_HANDSHAKE_ASSET_ID,
    limit=10,
):
    events = list_automation_event_payloads(
        asset_id=asset_id,
        event_type=HANDSHAKE_DRILL_EVENT_TYPE,
        limit=limit,
    )
    return {
        "status": "ok",
        "asset_id": asset_id,
        "event_type": HANDSHAKE_DRILL_EVENT_TYPE,
        "drills": [format_drill_event(event) for event in events],
    }


def drill_action(target_id=None, route_id=None):
    if target_id:
        return target_id

    if route_id:
        return f"run_route_live_adapter_handshake:{route_id}"

    return "run_all_live_adapter_handshakes"


def build_handshake_target_status(
    target,
    credential_readiness,
    generated_at,
    latest_evidence=None,
):
    route_requirements = credential_readiness.get("route_requirements", [])
    relevant_routes = [
        route
        for route in route_requirements
        if route.get("adapter_id") in target["required_for"]
    ]
    missing_credentials = dedupe(
        credential
        for route in relevant_routes
        for credential in route.get("missing_credentials", [])
    )
    missing_env_keys = dedupe(
        key
        for route in relevant_routes
        for key in route.get("missing_env_keys", [])
    )
    configured_endpoint_key = configured_env_key(target["endpoint_env_keys"])
    endpoint_configured = bool(configured_endpoint_key or target.get("default_endpoint"))
    mode = normalize_mode(os.getenv(target["mode_env_key"], "disabled"))
    credentials_configured = not missing_credentials
    prerequisites_ready = credentials_configured and endpoint_configured
    response_schema_status = (
        "expected_schema_defined"
        if target.get("expected_response_schema")
        else "missing_schema"
    )
    handshake_status = classify_target_handshake_status(
        mode=mode,
        prerequisites_ready=prerequisites_ready,
        response_schema_status=response_schema_status,
    )
    blockers = target_blockers(
        mode=mode,
        credentials_configured=credentials_configured,
        endpoint_configured=endpoint_configured,
        response_schema_status=response_schema_status,
        missing_credentials=missing_credentials,
    )
    evidence = (latest_evidence or {}).get(target["target_id"], {})
    recent_successful_drill = evidence.get("status") == "passed"

    return {
        "target_id": target["target_id"],
        "label": target["label"],
        "group": target["group"],
        "required_for": target["required_for"],
        "endpoint_status": "configured" if endpoint_configured else "missing",
        "endpoint_env_keys": target["endpoint_env_keys"],
        "configured_endpoint_key": configured_endpoint_key
        or ("default_endpoint" if target.get("default_endpoint") else "-"),
        "default_endpoint_used": bool(target.get("default_endpoint") and not configured_endpoint_key),
        "credential_status": "configured" if credentials_configured else "missing",
        "missing_credentials": missing_credentials,
        "missing_env_keys": missing_env_keys,
        "handshake_mode": mode,
        "auth_attempt_mode": "none" if mode == "disabled" else mode,
        "handshake_status": handshake_status,
        "response_schema_status": response_schema_status,
        "expected_response_schema": target["expected_response_schema"],
        "no_order_submission": True,
        "order_submission_performed": False,
        "audit_event_captured": True,
        "latest_drill_status": evidence.get("status"),
        "latest_drill_event_id": evidence.get("automation_event_id"),
        "latest_drill_at": evidence.get("created_at"),
        "last_successful_handshake_at": evidence.get("created_at")
        if evidence.get("status") == "passed"
        else None,
        "recent_successful_drill": recent_successful_drill,
        "blockers": blockers,
        "next_handshake_action": next_target_action(
            target=target,
            handshake_status=handshake_status,
            mode=mode,
            blockers=blockers,
        ),
    }


def build_drill_result(target, created_at):
    passed = target.get("handshake_status") in ["dry_run_ready", "real_ready"]
    blockers = target.get("blockers", [])

    return {
        "target_id": target["target_id"],
        "label": target.get("label"),
        "group": target.get("group"),
        "status": "passed" if passed else "blocked",
        "created_at": created_at,
        "handshake_mode": target.get("handshake_mode"),
        "auth_attempt_mode": target.get("auth_attempt_mode"),
        "endpoint_status": target.get("endpoint_status"),
        "credential_status": target.get("credential_status"),
        "response_schema_status": target.get("response_schema_status"),
        "expected_response_schema": target.get("expected_response_schema", []),
        "schema_checked": target.get("response_schema_status") == "expected_schema_defined",
        "audit_event_captured": True,
        "no_order_submission": True,
        "order_submission_performed": False,
        "blockers": blockers,
        "next_handshake_action": (
            "Handshake drill passed; attach this evidence to the supervised-live gate."
            if passed
            else target.get("next_handshake_action")
        ),
    }


def load_latest_handshake_evidence(asset_id=DEFAULT_HANDSHAKE_ASSET_ID):
    events = list_automation_event_payloads(
        asset_id=asset_id,
        event_type=HANDSHAKE_DRILL_EVENT_TYPE,
        limit=50,
    )
    latest = {}

    for event in events:
        payload = event.get("payload") or {}
        for result in payload.get("results", []):
            target_id = result.get("target_id")
            if not target_id or target_id in latest:
                continue

            latest[target_id] = {
                "automation_event_id": event.get("automation_event_id"),
                "created_at": event.get("created_at"),
                "status": result.get("status"),
                "payload": result,
            }

    return latest


def format_drill_event(event):
    payload = event.get("payload") or {}
    return {
        "automation_event_id": event.get("automation_event_id"),
        "asset_id": event.get("asset_id"),
        "created_at": event.get("created_at"),
        "action": event.get("action"),
        "status": event.get("status"),
        "target_id": payload.get("target_id"),
        "route_id": payload.get("route_id"),
        "target_count": (payload.get("summary") or {}).get("target_count"),
        "passed_count": (payload.get("summary") or {}).get("passed_count"),
        "blocked_count": (payload.get("summary") or {}).get("blocked_count"),
        "order_submission_performed": payload.get("order_submission_performed", False),
        "results": payload.get("results", []),
    }


def build_route_handshake_readiness(targets):
    route_ids = sorted(
        {
            route_id
            for target in HANDSHAKE_TARGETS
            for route_id in target["required_for"]
        }
    )
    routes = []

    for route_id in route_ids:
        route_targets = [
            target
            for target in targets
            if route_id in target.get("required_for", [])
        ]
        blockers = dedupe(
            blocker
            for target in route_targets
            for blocker in target.get("blockers", [])
        )
        blockers.extend(
            f"{target['target_id']}: no successful handshake drill evidence has been captured."
            for target in route_targets
            if target.get("handshake_status") in ["dry_run_ready", "real_ready"]
            and not target.get("recent_successful_drill")
        )
        blockers = dedupe(blockers)
        ready_targets = [
            target
            for target in route_targets
            if target.get("handshake_status") in ["dry_run_ready", "real_ready"]
            and target.get("recent_successful_drill")
        ]
        status = classify_route_handshake_status(route_targets, ready_targets, blockers)

        routes.append({
            "adapter_id": route_id,
            "route_handshake_status": status,
            "route_handshake_ready": status == "ready",
            "route_handshake_target_count": len(route_targets),
            "route_handshake_ready_count": len(ready_targets),
            "route_handshake_targets": [
                target["target_id"] for target in route_targets
            ],
            "route_handshake_blockers": blockers,
            "route_handshake_next_action": next_route_handshake_action(
                route_targets,
                blockers,
            ),
        })

    return routes


def build_handshake_env_checklist(targets, credential_readiness):
    route_requirements = {
        route["adapter_id"]: route
        for route in credential_readiness.get("route_requirements", [])
    }
    checklist = []

    for target in targets:
        spec = target_spec(target["target_id"])
        checklist.append({
            "target_id": target["target_id"],
            "target": target.get("label"),
            "group": target.get("group"),
            "item_type": "mode",
            "env_keys": [spec["mode_env_key"]],
            "required_value": "dry_run",
            "status": "configured"
            if target.get("handshake_mode") in ["dry_run", "real"]
            else "missing",
            "configured_env_key": spec["mode_env_key"]
            if os.getenv(spec["mode_env_key"])
            else "-",
            "value_exposed": False,
            "secret": False,
            "blocks_routes": target.get("required_for", []),
            "next_action": f"Set {spec['mode_env_key']}=dry_run to enable safe handshake drills.",
        })
        checklist.append({
            "target_id": target["target_id"],
            "target": target.get("label"),
            "group": target.get("group"),
            "item_type": "endpoint",
            "env_keys": target.get("endpoint_env_keys", []),
            "required_value": "configured_url",
            "status": target.get("endpoint_status"),
            "configured_env_key": target.get("configured_endpoint_key"),
            "value_exposed": False,
            "secret": False,
            "blocks_routes": target.get("required_for", []),
            "next_action": (
                "Endpoint is configured."
                if target.get("endpoint_status") == "configured"
                else f"Configure one endpoint variable: {', '.join(target.get('endpoint_env_keys', []))}."
            ),
        })

        for credential in target_credentials(target, route_requirements):
            checklist.append({
                "target_id": target["target_id"],
                "target": target.get("label"),
                "group": target.get("group"),
                "item_type": "secret",
                "env_keys": credential.get("env_keys", []),
                "credential_id": credential.get("credential_id"),
                "required_value": "secret_present",
                "status": "missing"
                if credential.get("credential_id") in target.get("missing_credentials", [])
                else "configured",
                "configured_env_key": configured_env_key(credential.get("env_keys", []))
                or "-",
                "value_exposed": False,
                "secret": True,
                "blocks_routes": target.get("required_for", []),
                "next_action": (
                    "Secret is present in the runtime environment."
                    if credential.get("credential_id") not in target.get("missing_credentials", [])
                    else credential.get("next_action")
                    or f"Configure one accepted key: {', '.join(credential.get('env_keys', []))}."
                ),
            })

    return checklist


def build_env_activation_guide(asset_id, checklist, country):
    route_ids = sorted(
        {
            route_id
            for item in checklist
            for route_id in item.get("blocks_routes", [])
            if route_id.startswith("epex_") or route_id.startswith("regelleistung_")
        }
    )
    guide = []

    for route_id in route_ids:
        route_items = [
            item
            for item in checklist
            if route_id in item.get("blocks_routes", [])
        ]
        missing_items = [
            item for item in route_items if item.get("status") != "configured"
        ]
        secret_items = [
            item for item in route_items if item.get("secret")
        ]
        mode_item = next(
            (item for item in route_items if item.get("item_type") == "mode"),
            {},
        )
        endpoint_item = next(
            (item for item in route_items if item.get("item_type") == "endpoint"),
            {},
        )
        next_unlock = classify_route_env_next_unlock(missing_items)
        guide.append({
            "adapter_id": route_id,
            "route_label": route_label(route_id),
            "market_family": (
                "EPEX"
                if route_id.startswith("epex_")
                else "regelleistung"
            ),
            "activation_status": (
                "configured"
                if not missing_items
                else "secrets_missing"
                if any(item.get("secret") for item in missing_items)
                else "setup_required"
            ),
            "configured_count": len(route_items) - len(missing_items),
            "missing_count": len(missing_items),
            "required_count": len(route_items),
            "secret_count": len(secret_items),
            "mode_status": mode_item.get("status"),
            "endpoint_status": endpoint_item.get("status"),
            "required_mode": "dry_run",
            "required_env_keys": dedupe(
                key
                for item in route_items
                for key in item.get("env_keys", [])
            ),
            "missing_env_keys": dedupe(
                key
                for item in missing_items
                for key in item.get("env_keys", [])
            ),
            "secret_env_keys": dedupe(
                key
                for item in secret_items
                for key in item.get("env_keys", [])
            ),
            "configured_env_keys": dedupe(
                item.get("configured_env_key")
                for item in route_items
                if item.get("configured_env_key")
                and item.get("configured_env_key") not in ["-", "default_endpoint"]
            ),
            "next_unlock_category": next_unlock["category"],
            "next_unlock_label": next_unlock["label"],
            "next_action": next_unlock["message"],
            "handshake_drill_enabled_after_setup": not missing_items,
            "run_drill_endpoint": (
                "/execution/market-connectors/live-handshake/run"
                if not missing_items
                else None
            ),
            "route_drill_endpoint": (
                f"/execution/market-connectors/live-handshake/run?"
                f"asset_id={asset_id}&country={country}&route_id={route_id}"
                if not missing_items
                else None
            ),
            "system_route_drill_endpoint": (
                f"/system/live-adapter-handshake/run?"
                f"asset_id={asset_id}&country={country}&route_id={route_id}"
                if not missing_items
                else None
            ),
            "safe_deployment_steps": build_safe_deployment_steps(
                route_id=route_id,
                missing_items=missing_items,
                route_items=route_items,
            ),
            "secret_values_exposed": False,
        })

    return guide


def classify_route_env_next_unlock(missing_items):
    if not missing_items:
        return {
            "category": "run_handshake",
            "label": "Run handshake drill",
            "message": "Environment is configured; run a no-order handshake drill.",
        }

    first_missing = missing_items[0]
    if first_missing.get("item_type") == "mode":
        return {
            "category": "set_mode",
            "label": "Set dry-run mode",
            "message": first_missing.get("next_action"),
        }

    if first_missing.get("item_type") == "endpoint":
        return {
            "category": "set_endpoint",
            "label": "Configure endpoint URL",
            "message": first_missing.get("next_action"),
        }

    return {
        "category": "set_secret",
        "label": "Configure secret",
        "message": first_missing.get("next_action"),
    }


def build_safe_deployment_steps(route_id, missing_items, route_items):
    if not missing_items:
        return [
            "Recheck readiness after deployment.",
            f"Run a no-order handshake drill for {route_label(route_id)}.",
            "Attach the drill result to supervised-live evidence before enabling live submission.",
        ]

    steps = []
    for item in missing_items[:6]:
        keys = ", ".join(item.get("env_keys", []))
        if item.get("item_type") == "mode":
            steps.append(
                f"Set {keys}=dry_run in the deployment environment."
            )
        elif item.get("item_type") == "endpoint":
            steps.append(
                f"Configure one endpoint variable for {item.get('target')}: {keys}."
            )
        elif item.get("secret"):
            steps.append(
                f"Add one secret for {item.get('credential_id') or item.get('target')}: {keys}."
            )
        else:
            steps.append(item.get("next_action"))

    configured = [
        item.get("configured_env_key")
        for item in route_items
        if item.get("configured_env_key")
        and item.get("configured_env_key") not in ["-", "default_endpoint"]
    ]
    if configured:
        steps.append(
            "Already configured: " + ", ".join(dedupe(configured)[:4]) + "."
        )

    steps.append("Restart or redeploy the API process so new env values are loaded.")
    steps.append("Recheck readiness; secret values will remain hidden.")
    return dedupe(steps)


def summarize_env_activation_guide(guide):
    return {
        "env_activation_route_count": len(guide),
        "env_activation_configured_route_count": len(
            [route for route in guide if route.get("activation_status") == "configured"]
        ),
        "env_activation_setup_required_route_count": len(
            [route for route in guide if route.get("activation_status") != "configured"]
        ),
    }


def route_label(route_id):
    labels = {
        "epex_day_ahead": "EPEX day-ahead",
        "epex_intraday_auction": "EPEX intraday auction",
        "epex_intraday_continuous": "EPEX intraday continuous",
        "regelleistung_fcr": "Regelleistung FCR",
        "regelleistung_afrr": "Regelleistung aFRR",
        "regelleistung_mfrr": "Regelleistung mFRR",
    }
    return labels.get(route_id, route_id.replace("_", " "))


def target_credentials(target, route_requirements):
    credential_items = []
    seen = set()

    for route_id in target.get("required_for", []):
        route = route_requirements.get(route_id, {})
        for credential_id in route.get("required_credentials", []):
            if credential_id in seen:
                continue

            seen.add(credential_id)
            credential_items.append(resolve_credential_requirement(credential_id))

    return [item for item in credential_items if item]


def resolve_credential_requirement(credential_id):
    readiness = build_credential_readiness()
    return next(
        (
            {
                "credential_id": item.get("credential_id"),
                "env_keys": item.get("accepted_env_keys", []),
                "next_action": item.get("next_action"),
            }
            for item in readiness.get("credentials", [])
            if item.get("credential_id") == credential_id
        ),
        None,
    )


def target_spec(target_id):
    return next(
        (target for target in HANDSHAKE_TARGETS if target["target_id"] == target_id),
        {},
    )


def classify_target_handshake_status(mode, prerequisites_ready, response_schema_status):
    if mode == "disabled":
        return "disabled"

    if response_schema_status != "expected_schema_defined":
        return "blocked"

    if not prerequisites_ready:
        return "blocked"

    if mode == "dry_run":
        return "dry_run_ready"

    if mode == "real":
        return "real_ready"

    return "blocked"


def classify_route_handshake_status(route_targets, ready_targets, blockers):
    if route_targets and len(ready_targets) == len(route_targets):
        return "ready"

    if any(target.get("handshake_status") == "disabled" for target in route_targets):
        return "disabled"

    if blockers:
        return "blocked"

    return "not_required"


def summarize_handshakes(targets, routes):
    return {
        "handshake_target_count": len(targets),
        "handshake_ready_count": len(
            [
                target
                for target in targets
                if target.get("handshake_status") in ["dry_run_ready", "real_ready"]
            ]
        ),
        "handshake_blocked_count": len(
            [
                target
                for target in targets
                if target.get("handshake_status") == "blocked"
            ]
        ),
        "handshake_disabled_count": len(
            [
                target
                for target in targets
                if target.get("handshake_status") == "disabled"
            ]
        ),
        "route_handshake_count": len(routes),
        "route_handshake_ready_count": len(
            [route for route in routes if route.get("route_handshake_status") == "ready"]
        ),
        "route_handshake_blocked_count": len(
            [route for route in routes if route.get("route_handshake_status") == "blocked"]
        ),
        "route_handshake_disabled_count": len(
            [route for route in routes if route.get("route_handshake_status") == "disabled"]
        ),
    }


def summarize_env_checklist(checklist):
    return {
        "env_checklist_count": len(checklist),
        "env_configured_count": len(
            [item for item in checklist if item.get("status") == "configured"]
        ),
        "env_missing_count": len(
            [item for item in checklist if item.get("status") != "configured"]
        ),
        "env_secret_count": len(
            [item for item in checklist if item.get("item_type") == "secret"]
        ),
        "env_endpoint_count": len(
            [item for item in checklist if item.get("item_type") == "endpoint"]
        ),
        "env_mode_count": len(
            [item for item in checklist if item.get("item_type") == "mode"]
        ),
    }


def classify_portfolio_handshake(summary):
    if summary.get("route_handshake_count") and summary.get(
        "route_handshake_count"
    ) == summary.get("route_handshake_ready_count"):
        return "handshake_ready"

    if summary.get("handshake_ready_count"):
        return "partial_handshake_ready"

    if summary.get("handshake_blocked_count"):
        return "handshake_blocked"

    return "handshake_disabled"


def build_handshake_actions(targets, routes):
    actions = [
        target["next_handshake_action"]
        for target in targets
        if target.get("handshake_status") not in ["dry_run_ready", "real_ready"]
    ]
    actions.extend(
        route["route_handshake_next_action"]
        for route in routes
        if route.get("route_handshake_status") != "ready"
    )
    return dedupe(actions)[:8]


def target_blockers(
    mode,
    credentials_configured,
    endpoint_configured,
    response_schema_status,
    missing_credentials,
):
    blockers = []

    if mode == "disabled":
        blockers.append("Dry-run handshake mode is disabled.")

    if not credentials_configured:
        blockers.append(
            "Missing credentials: " + ", ".join(missing_credentials)
        )

    if not endpoint_configured:
        blockers.append("Endpoint URL is not configured.")

    if response_schema_status != "expected_schema_defined":
        blockers.append("Expected response schema is not defined.")

    return blockers


def next_target_action(target, handshake_status, mode, blockers):
    if handshake_status in ["dry_run_ready", "real_ready"]:
        return "Dry-run handshake is ready; use it as evidence before supervised live submission."

    if mode == "disabled":
        return f"Set {target['mode_env_key']}=dry_run after credentials and endpoint are configured."

    if blockers:
        return blockers[0]

    return target["next_action"]


def next_route_handshake_action(route_targets, blockers):
    if blockers:
        return blockers[0]

    first_incomplete = next(
        (
            target
            for target in route_targets
            if target.get("handshake_status") not in ["dry_run_ready", "real_ready"]
        ),
        None,
    )
    if first_incomplete:
        return first_incomplete.get("next_handshake_action")

    return "Route handshake is ready for supervised-live gate evidence."


def normalize_mode(value):
    normalized = str(value or "disabled").strip().lower()
    if normalized in ["dry_run", "dry-run", "dryrun"]:
        return "dry_run"
    if normalized in ["real", "live", "enabled"]:
        return "real"
    if normalized in ["disabled", "off", "false", "0"]:
        return "disabled"
    return "blocked"


def configured_env_key(keys):
    return next((key for key in keys if bool(os.getenv(key))), None)


def dedupe(items):
    seen = set()
    result = []

    for item in items:
        if not item or item in seen:
            continue

        seen.add(item)
        result.append(item)

    return result



