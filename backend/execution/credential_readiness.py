import os
from datetime import datetime


CREDENTIAL_REQUIREMENTS = [
    {
        "credential_id": "epex_api_key",
        "label": "EPEX API key",
        "group": "EPEX market access",
        "env_keys": ["EPEX_API_KEY"],
        "required_for": [
            "epex_day_ahead",
            "epex_intraday_auction",
            "epex_intraday_continuous",
        ],
        "blocks_mode": "supervised_live",
        "next_action": "Add the EPEX member or broker API key to the runtime secret store.",
    },
    {
        "credential_id": "epex_member_id",
        "label": "EPEX member ID",
        "group": "EPEX market access",
        "env_keys": ["EPEX_MEMBER_ID"],
        "required_for": [
            "epex_day_ahead",
            "epex_intraday_auction",
            "epex_intraday_continuous",
        ],
        "blocks_mode": "supervised_live",
        "next_action": "Add the EPEX member ID or broker-routed member reference.",
    },
    {
        "credential_id": "epex_portfolio_id",
        "label": "EPEX portfolio ID",
        "group": "EPEX market access",
        "env_keys": ["EPEX_PORTFOLIO_ID"],
        "required_for": [
            "epex_day_ahead",
            "epex_intraday_auction",
            "epex_intraday_continuous",
        ],
        "blocks_mode": "supervised_live",
        "next_action": "Map the EPEX portfolio ID used for bid submission and settlement.",
    },
    {
        "credential_id": "regelleistung_api_key",
        "label": "regelleistung API key",
        "group": "Ancillary services access",
        "env_keys": ["REGELLEISTUNG_API_KEY"],
        "required_for": [
            "regelleistung_fcr",
            "regelleistung_afrr",
            "regelleistung_mfrr",
        ],
        "blocks_mode": "supervised_live",
        "next_action": "Add the regelleistung or TSO platform API key.",
    },
    {
        "credential_id": "tso_participant_id",
        "label": "TSO participant ID",
        "group": "Ancillary services access",
        "env_keys": ["TSO_PARTICIPANT_ID"],
        "required_for": [
            "regelleistung_fcr",
            "regelleistung_afrr",
            "regelleistung_mfrr",
        ],
        "blocks_mode": "supervised_live",
        "next_action": "Add the TSO participant identifier for reserve-market submission.",
    },
    {
        "credential_id": "prequalification_id",
        "label": "Reserve prequalification ID",
        "group": "Ancillary services access",
        "env_keys": ["RESERVE_PREQUALIFICATION_ID", "TSO_PREQUALIFICATION_ID"],
        "required_for": [
            "regelleistung_fcr",
            "regelleistung_afrr",
            "regelleistung_mfrr",
        ],
        "blocks_mode": "supervised_live",
        "next_action": "Map the asset prequalification ID before reserve capacity can be automated.",
    },
    {
        "credential_id": "ems_api_url",
        "label": "EMS API URL",
        "group": "Asset telemetry",
        "env_keys": ["EMS_API_URL"],
        "required_for": ["asset_telemetry", "live_dispatch_feedback"],
        "blocks_mode": "live_auto_limited",
        "next_action": "Add the EMS or SCADA endpoint used for SOC, availability, and dispatch acknowledgements.",
    },
    {
        "credential_id": "ems_api_token",
        "label": "EMS API token",
        "group": "Asset telemetry",
        "env_keys": ["EMS_API_TOKEN"],
        "required_for": ["asset_telemetry", "live_dispatch_feedback"],
        "blocks_mode": "live_auto_limited",
        "next_action": "Add the EMS or SCADA API token to the runtime secret store.",
    },
    {
        "credential_id": "entsoe_api_token",
        "label": "ENTSO-E API token",
        "group": "Market data",
        "env_keys": ["ENTSOE_API_TOKEN", "ENTSOE_API_KEY", "ENTSOE_TOKEN"],
        "required_for": ["forecast_provider", "actual_price_feed"],
        "blocks_mode": "supervised_auto",
        "next_action": "Add the ENTSO-E token used for live forecast and actual-price evidence.",
    },
]


def build_credential_readiness():
    credentials = [build_credential_status(item) for item in CREDENTIAL_REQUIREMENTS]
    route_requirements = build_route_requirements(credentials)
    summary = summarize_credentials(credentials, route_requirements)
    return {
        "status": "ok",
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "credential_readiness_status": classify_credential_readiness(summary),
        "summary": summary,
        "credentials": credentials,
        "route_requirements": route_requirements,
        "recommended_actions": build_credential_actions(credentials),
    }


def get_route_credential_readiness(adapter_id):
    readiness = build_credential_readiness()
    return next(
        (
            route
            for route in readiness["route_requirements"]
            if route["adapter_id"] == adapter_id
        ),
        {},
    )


def get_missing_env_keys_for_route(adapter_id):
    route = get_route_credential_readiness(adapter_id)
    return route.get("missing_env_keys", [])


def build_credential_status(requirement):
    configured_env_key = next(
        (
            key
            for key in requirement["env_keys"]
            if bool(os.getenv(key))
        ),
        None,
    )
    configured = configured_env_key is not None
    return {
        "credential_id": requirement["credential_id"],
        "label": requirement["label"],
        "group": requirement["group"],
        "status": "configured" if configured else "missing",
        "configured": configured,
        "configured_env_key": configured_env_key or "-",
        "accepted_env_keys": requirement["env_keys"],
        "missing_env_keys": [] if configured else requirement["env_keys"],
        "required_for": requirement["required_for"],
        "blocks_mode": requirement["blocks_mode"],
        "secret_value_exposed": False,
        "next_action": (
            "Credential is present in runtime environment."
            if configured
            else requirement["next_action"]
        ),
    }


def build_route_requirements(credentials):
    route_ids = sorted(
        {
            route_id
            for credential in credentials
            for route_id in credential["required_for"]
        }
    )
    route_requirements = []

    for route_id in route_ids:
        route_credentials = [
            credential
            for credential in credentials
            if route_id in credential["required_for"]
        ]
        missing = [
            credential
            for credential in route_credentials
            if not credential["configured"]
        ]
        route_requirements.append({
            "adapter_id": route_id,
            "credential_status": "configured" if not missing else "missing",
            "required_credential_count": len(route_credentials),
            "configured_credential_count": len(route_credentials) - len(missing),
            "missing_credential_count": len(missing),
            "required_credentials": [
                credential["credential_id"] for credential in route_credentials
            ],
            "missing_credentials": [
                credential["credential_id"] for credential in missing
            ],
            "missing_env_keys": [
                key
                for credential in missing
                for key in credential["accepted_env_keys"]
            ],
            "onboarding_next_action": next_route_action(missing),
        })

    return route_requirements


def summarize_credentials(credentials, route_requirements):
    return {
        "credential_count": len(credentials),
        "configured_credential_count": len(
            [credential for credential in credentials if credential["configured"]]
        ),
        "missing_credential_count": len(
            [credential for credential in credentials if not credential["configured"]]
        ),
        "route_count": len(route_requirements),
        "credential_ready_route_count": len(
            [
                route
                for route in route_requirements
                if route["credential_status"] == "configured"
            ]
        ),
        "credential_blocked_route_count": len(
            [
                route
                for route in route_requirements
                if route["credential_status"] == "missing"
            ]
        ),
    }


def classify_credential_readiness(summary):
    if summary["missing_credential_count"] == 0:
        return "credentials_configured"

    if summary["configured_credential_count"] > 0:
        return "partial_credentials"

    return "credentials_missing"


def build_credential_actions(credentials):
    return [
        credential["next_action"]
        for credential in credentials
        if not credential["configured"]
    ][:8]


def next_route_action(missing):
    if not missing:
        return "Credentials are configured; validate live adapter handshake next."

    credential = missing[0]
    return credential["next_action"]



