from datetime import datetime

from src.db.repositories.official_api_evidence_repository import (
    evidence_by_requirement,
    list_official_api_evidence,
    upsert_official_api_evidence,
)
from src.execution.market_adapters.registry import list_market_adapters


APPROVED_EVIDENCE_STATUSES = {"approved", "valid", "passed", "active"}


OFFICIAL_API_REQUIREMENTS = {
    "epex_day_ahead": {
        "official_system": "EPEX SPOT MATS",
        "access_model": "member_or_certified_isv",
        "required_access_modes": ["read", "write"],
        "public_reference": "https://www.epexspot.com/en/software-providers",
        "public_download_reference": "https://www.epexspot.com/en/downloads",
        "checks": [
            {
                "check": "official_api_documentation_loaded",
                "label": "Official MATS/API documentation",
                "env_keys": ["EPEX_MATS_API_SPEC_VERSION"],
                "message": "Load the member-area EPEX MATS/API specification version used for day-ahead auction submission.",
            },
            {
                "check": "member_or_broker_market_access",
                "label": "Member or broker market access",
                "env_keys": ["EPEX_MEMBER_ID", "EPEX_PORTFOLIO_ID"],
                "message": "Configure EPEX member or broker route and portfolio permissions for DE-LU day-ahead products.",
            },
            {
                "check": "read_write_access_approved",
                "label": "Read/write API approval",
                "env_keys": ["EPEX_API_ACCESS_MODE"],
                "required_value": "read_write",
                "message": "Confirm EPEX read/write API access; read-only access cannot submit automated orders.",
            },
            {
                "check": "conformance_test_passed",
                "label": "EPEX conformance test",
                "env_keys": ["EPEX_CONFORMANCE_STATUS"],
                "required_value": "passed",
                "message": "Pass EPEX conformance testing before production API access.",
            },
            {
                "check": "production_endpoint_locked",
                "label": "Production endpoint and certificates",
                "env_keys": ["EPEX_PROD_API_URL", "EPEX_CLIENT_CERT_PATH"],
                "message": "Configure official EPEX production endpoint and client certificate material without exposing secrets.",
            },
            {
                "check": "official_schema_mapping",
                "label": "Official order and result schema mapping",
                "env_keys": ["EPEX_ORDER_SCHEMA_VERSION", "EPEX_RESULT_SCHEMA_VERSION"],
                "message": "Map order submission, acknowledgement, award, and settlement references to the official EPEX schema.",
            },
        ],
    },
    "epex_intraday_auction": {
        "official_system": "EPEX SPOT MATS",
        "access_model": "member_or_certified_isv",
        "required_access_modes": ["read", "write"],
        "public_reference": "https://www.epexspot.com/en/software-providers",
        "public_download_reference": "https://www.epexspot.com/en/downloads",
        "checks": [
            {
                "check": "official_api_documentation_loaded",
                "label": "Official MATS/API documentation",
                "env_keys": ["EPEX_MATS_API_SPEC_VERSION"],
                "message": "Load the member-area EPEX MATS/API specification version used for intraday auctions.",
            },
            {
                "check": "member_or_broker_market_access",
                "label": "Member or broker market access",
                "env_keys": ["EPEX_MEMBER_ID", "EPEX_PORTFOLIO_ID"],
                "message": "Configure EPEX member or broker route and portfolio permissions for intraday auction products.",
            },
            {
                "check": "read_write_access_approved",
                "label": "Read/write API approval",
                "env_keys": ["EPEX_API_ACCESS_MODE"],
                "required_value": "read_write",
                "message": "Confirm EPEX read/write API access; read-only access cannot submit automated auction orders.",
            },
            {
                "check": "conformance_test_passed",
                "label": "EPEX conformance test",
                "env_keys": ["EPEX_CONFORMANCE_STATUS"],
                "required_value": "passed",
                "message": "Pass EPEX conformance testing before production API access.",
            },
            {
                "check": "auction_schema_mapping",
                "label": "Auction product and result schema",
                "env_keys": ["EPEX_INTRADAY_AUCTION_SCHEMA_VERSION"],
                "message": "Map intraday auction product, gate, acknowledgement, award, and settlement fields.",
            },
        ],
    },
    "epex_intraday_continuous": {
        "official_system": "EPEX SPOT M7",
        "access_model": "member_or_certified_isv",
        "required_access_modes": ["read", "write"],
        "public_reference": "https://www.epexspot.com/en/software-providers",
        "public_download_reference": "https://www.epexspot.com/en/downloads",
        "checks": [
            {
                "check": "official_api_documentation_loaded",
                "label": "Official M7 API documentation",
                "env_keys": ["EPEX_M7_API_SPEC_VERSION"],
                "message": "Load the official EPEX M7 API specification version for continuous intraday trading.",
            },
            {
                "check": "member_or_broker_market_access",
                "label": "Member or broker market access",
                "env_keys": ["EPEX_MEMBER_ID", "EPEX_PORTFOLIO_ID"],
                "message": "Configure EPEX member or broker route and portfolio permissions for continuous intraday products.",
            },
            {
                "check": "read_write_access_approved",
                "label": "Read/write API approval",
                "env_keys": ["EPEX_API_ACCESS_MODE"],
                "required_value": "read_write",
                "message": "Confirm EPEX M7 read/write access; read-only access cannot place or cancel orders.",
            },
            {
                "check": "conformance_test_passed",
                "label": "EPEX conformance test",
                "env_keys": ["EPEX_CONFORMANCE_STATUS"],
                "required_value": "passed",
                "message": "Pass EPEX conformance testing before production M7 access.",
            },
            {
                "check": "m7_order_book_and_trade_streams",
                "label": "M7 order book and trade streams",
                "env_keys": ["EPEX_M7_ORDER_BOOK_ENABLED", "EPEX_M7_TRADE_STREAM_ENABLED"],
                "required_value": "true",
                "message": "Enable official M7 order book and trade streams before continuous automation.",
            },
        ],
    },
    "regelleistung_fcr": {
        "official_system": "regelleistung.net BSP API",
        "access_model": "registered_bsp",
        "required_access_modes": ["read", "write"],
        "public_reference": "https://bspsupportregelleistung.atlassian.net/wiki/spaces/APIDOC",
        "public_download_reference": "https://www.regelleistung.net/de-de/Marktinformationen",
        "checks": [
            {
                "check": "official_bsp_api_version_loaded",
                "label": "Official BSP API version",
                "env_keys": ["REGELLEISTUNG_BSP_API_VERSION"],
                "message": "Load the official regelleistung.net BSP API version used for balancing reserve tendering.",
            },
            {
                "check": "bsp_access_approved",
                "label": "BSP platform access",
                "env_keys": ["TSO_PARTICIPANT_ID", "REGELLEISTUNG_API_KEY"],
                "message": "Configure approved BSP participant access for regelleistung.net.",
            },
            {
                "check": "prequalification_reference",
                "label": "Prequalification reference",
                "env_keys": ["REGELLEISTUNG_FCR_PREQUALIFICATION_ID"],
                "message": "Map the official FCR prequalification reference before capacity bidding.",
            },
            {
                "check": "bid_schema_mapping",
                "label": "FCR bid and result schema",
                "env_keys": ["REGELLEISTUNG_FCR_SCHEMA_VERSION"],
                "message": "Map FCR tender, bid, result, backup, and settlement fields to the BSP API schema.",
            },
        ],
    },
    "regelleistung_afrr": {
        "official_system": "regelleistung.net BSP API",
        "access_model": "registered_bsp",
        "required_access_modes": ["read", "write"],
        "public_reference": "https://bspsupportregelleistung.atlassian.net/wiki/spaces/APIDOC",
        "public_download_reference": "https://www.regelleistung.net/de-de/Marktinformationen",
        "checks": [
            {
                "check": "official_bsp_api_version_loaded",
                "label": "Official BSP API version",
                "env_keys": ["REGELLEISTUNG_BSP_API_VERSION"],
                "message": "Load the official regelleistung.net BSP API version used for aFRR tendering.",
            },
            {
                "check": "bsp_access_approved",
                "label": "BSP platform access",
                "env_keys": ["TSO_PARTICIPANT_ID", "REGELLEISTUNG_API_KEY"],
                "message": "Configure approved BSP participant access for regelleistung.net.",
            },
            {
                "check": "prequalification_reference",
                "label": "Prequalification reference",
                "env_keys": ["REGELLEISTUNG_AFRR_PREQUALIFICATION_ID"],
                "message": "Map official aFRR prequalification and product permissions before bidding.",
            },
            {
                "check": "capacity_energy_schema_mapping",
                "label": "aFRR capacity and energy schema",
                "env_keys": ["REGELLEISTUNG_AFRR_SCHEMA_VERSION"],
                "message": "Map aFRR capacity bids, energy activation, results, backups, and settlement fields.",
            },
        ],
    },
    "regelleistung_mfrr": {
        "official_system": "regelleistung.net BSP API",
        "access_model": "registered_bsp",
        "required_access_modes": ["read", "write"],
        "public_reference": "https://bspsupportregelleistung.atlassian.net/wiki/spaces/APIDOC",
        "public_download_reference": "https://www.regelleistung.net/de-de/Marktinformationen",
        "checks": [
            {
                "check": "official_bsp_api_version_loaded",
                "label": "Official BSP API version",
                "env_keys": ["REGELLEISTUNG_BSP_API_VERSION"],
                "message": "Load the official regelleistung.net BSP API version used for mFRR tendering.",
            },
            {
                "check": "bsp_access_approved",
                "label": "BSP platform access",
                "env_keys": ["TSO_PARTICIPANT_ID", "REGELLEISTUNG_API_KEY"],
                "message": "Configure approved BSP participant access for regelleistung.net.",
            },
            {
                "check": "prequalification_reference",
                "label": "Prequalification reference",
                "env_keys": ["REGELLEISTUNG_MFRR_PREQUALIFICATION_ID"],
                "message": "Map official mFRR prequalification and product permissions before bidding.",
            },
            {
                "check": "manual_activation_schema_mapping",
                "label": "mFRR tender and activation schema",
                "env_keys": ["REGELLEISTUNG_MFRR_SCHEMA_VERSION"],
                "message": "Map mFRR capacity bids, manual activation workflow, results, backups, and settlement fields.",
            },
        ],
    },
}


def build_official_api_compliance(country="Germany"):
    routes = [
        evaluate_official_api_compliance(adapter["adapter_id"])
        for adapter in list_market_adapters(country=country)
        if adapter["adapter_id"] in OFFICIAL_API_REQUIREMENTS
    ]
    summary = summarize_compliance(routes)
    evidence_vault = build_official_api_evidence_vault(country=country)
    return {
        "status": "ok",
        "country": country,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "official_api_compliance_status": classify_portfolio_compliance(summary),
        "summary": summary,
        "evidence_vault_status": evidence_vault["evidence_vault_status"],
        "evidence_summary": evidence_vault["summary"],
        "routes": routes,
        "evidence_records": evidence_vault["evidence_records"],
        "recommended_actions": [
            route["official_api_next_action"]
            for route in routes
            if route["official_api_compliance_status"] != "compliant"
        ][:8]
        + evidence_vault["recommended_actions"][:4],
    }


def get_route_official_api_compliance(adapter_id):
    if adapter_id not in OFFICIAL_API_REQUIREMENTS:
        return {}
    return evaluate_official_api_compliance(adapter_id)


def evaluate_official_api_compliance(adapter_id):
    spec = OFFICIAL_API_REQUIREMENTS[adapter_id]
    evidence_records = evidence_by_requirement(adapter_id)
    checks = [
        evaluate_check(
            adapter_id=adapter_id,
            check=check,
            evidence=evidence_records.get(check["check"]),
        )
        for check in spec["checks"]
    ]
    blockers = [
        check["message"]
        for check in checks
        if check["status"] == "blocked"
    ]
    passed_count = len([check for check in checks if check["status"] == "passed"])
    status = "compliant" if passed_count == len(checks) else "blocked"
    return {
        "adapter_id": adapter_id,
        "official_system": spec["official_system"],
        "access_model": spec["access_model"],
        "required_access_modes": spec["required_access_modes"],
        "public_reference": spec["public_reference"],
        "public_download_reference": spec["public_download_reference"],
        "official_api_compliance_status": status,
        "official_api_compliance_score": round(passed_count / max(len(checks), 1) * 100, 1),
        "official_api_check_count": len(checks),
        "official_api_passed_count": passed_count,
        "official_api_blockers": blockers,
        "official_api_checks": checks,
        "official_api_next_action": next_action(adapter_id, checks),
        "fail_closed": status != "compliant",
    }


def evaluate_check(adapter_id, check, evidence=None):
    import os

    env_keys = check.get("env_keys", [])
    required_value = check.get("required_value")
    configured_values = {
        key: sanitize_value(os.getenv(key))
        for key in env_keys
        if os.getenv(key)
    }

    if required_value is not None:
        machine_configured = all(
            str(os.getenv(key, "")).lower() == str(required_value).lower()
            for key in env_keys
        )
    else:
        machine_configured = all(os.getenv(key) for key in env_keys)

    evidence_valid = is_evidence_valid(evidence)
    evidence_expired = is_evidence_expired(evidence)
    status = "passed" if evidence_valid else "blocked"
    if evidence_valid:
        message = f"{check['label']} has approved official evidence."
    elif machine_configured:
        message = (
            f"Attach approved evidence for {check['label']}; machine configuration exists "
            "but has not been audited."
        )
    elif evidence_expired:
        message = f"Renew expired official evidence for {check['label']}."
    else:
        message = check["message"]

    return {
        "adapter_id": adapter_id,
        "check": check["check"],
        "label": check["label"],
        "status": status,
        "env_keys": env_keys,
        "configured_env_keys": list(configured_values.keys()),
        "machine_configured": machine_configured,
        "required_value": required_value,
        "message": message,
        "evidence_id": evidence.get("evidence_id") if evidence else None,
        "evidence_status": evidence.get("evidence_status") if evidence else "missing",
        "evidence_type": evidence.get("evidence_type") if evidence else None,
        "evidence_owner": evidence.get("evidence_owner") if evidence else None,
        "evidence_reference": evidence.get("evidence_reference") if evidence else None,
        "evidence_recorded_at": evidence.get("recorded_at") if evidence else None,
        "evidence_expires_at": evidence.get("expires_at") if evidence else None,
        "evidence_review_at": evidence.get("review_at") if evidence else None,
        "evidence_valid": evidence_valid,
        "evidence_expired": evidence_expired,
        "unlocks_mode": evidence.get("unlocks_mode") if evidence else None,
        "secret_values_exposed": False,
    }


def next_action(adapter_id, checks):
    first_blocked = next(
        (check for check in checks if check["status"] == "blocked"),
        None,
    )
    if first_blocked:
        return f"{adapter_id}: {first_blocked['message']}"
    return f"{adapter_id}: official API compliance passed; continue conformance evidence monitoring."


def summarize_compliance(routes):
    return {
        "official_api_route_count": len(routes),
        "official_api_compliant_route_count": len(
            [route for route in routes if route["official_api_compliance_status"] == "compliant"]
        ),
        "official_api_blocked_route_count": len(
            [route for route in routes if route["official_api_compliance_status"] != "compliant"]
        ),
        "official_api_check_count": sum(route["official_api_check_count"] for route in routes),
        "official_api_passed_check_count": sum(route["official_api_passed_count"] for route in routes),
        "average_official_api_compliance_score": round(
            sum(route["official_api_compliance_score"] for route in routes)
            / max(len(routes), 1),
            1,
        ),
    }


def build_official_api_evidence_vault(country="Germany"):
    evidence_records = list_official_api_evidence()
    evidence_by_key = {
        (record["adapter_id"], record["requirement_id"]): record
        for record in evidence_records
    }
    requirements = []

    for adapter in list_market_adapters(country=country):
        adapter_id = adapter["adapter_id"]
        spec = OFFICIAL_API_REQUIREMENTS.get(adapter_id)
        if not spec:
            continue
        for check in spec["checks"]:
            evidence = evidence_by_key.get((adapter_id, check["check"]))
            requirements.append(
                build_evidence_requirement_row(
                    adapter_id=adapter_id,
                    spec=spec,
                    check=check,
                    evidence=evidence,
                )
            )

    summary = summarize_evidence_vault(requirements)
    return {
        "status": "ok",
        "country": country,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "evidence_vault_status": classify_evidence_vault(summary),
        "summary": summary,
        "requirements": requirements,
        "evidence_records": evidence_records,
        "recommended_actions": [
            row["next_action"]
            for row in requirements
            if row["evidence_readiness"] != "approved"
        ][:10],
    }


def upsert_official_api_evidence_record(payload):
    adapter_id = payload.get("adapter_id")
    requirement_id = payload.get("requirement_id")
    requirement = find_requirement(adapter_id, requirement_id)
    if requirement is None:
        raise ValueError(
            f"Unknown official API requirement: {adapter_id}/{requirement_id}"
        )

    evidence = {
        **payload,
        "adapter_id": adapter_id,
        "requirement_id": requirement_id,
        "evidence_status": payload.get("evidence_status", "pending"),
        "official_system": requirement["spec"]["official_system"],
        "label": requirement["check"]["label"],
        "message": requirement["check"]["message"],
    }
    upsert_official_api_evidence(evidence)
    return {
        "status": "ok",
        "adapter_id": adapter_id,
        "requirement_id": requirement_id,
        "evidence": evidence,
        "message": "Official API evidence saved.",
    }


def build_evidence_requirement_row(adapter_id, spec, check, evidence):
    valid = is_evidence_valid(evidence)
    expired = is_evidence_expired(evidence)
    if valid:
        readiness = "approved"
        next_action_text = f"{adapter_id}: monitor {check['label']} evidence expiry and review dates."
    elif expired:
        readiness = "expired"
        next_action_text = f"{adapter_id}: renew expired {check['label']} evidence."
    elif evidence:
        readiness = "review"
        next_action_text = f"{adapter_id}: approve or remediate {check['label']} evidence."
    else:
        readiness = "missing"
        next_action_text = f"{adapter_id}: attach approved evidence for {check['label']}."

    return {
        "adapter_id": adapter_id,
        "requirement_id": check["check"],
        "label": check["label"],
        "official_system": spec["official_system"],
        "access_model": spec["access_model"],
        "public_reference": spec["public_reference"],
        "public_download_reference": spec["public_download_reference"],
        "required_env_keys": check.get("env_keys", []),
        "required_value": check.get("required_value"),
        "evidence_readiness": readiness,
        "evidence_valid": valid,
        "evidence_expired": expired,
        "evidence_status": evidence.get("evidence_status") if evidence else "missing",
        "evidence_type": evidence.get("evidence_type") if evidence else None,
        "evidence_owner": evidence.get("evidence_owner") if evidence else None,
        "evidence_reference": evidence.get("evidence_reference") if evidence else None,
        "recorded_at": evidence.get("recorded_at") if evidence else None,
        "expires_at": evidence.get("expires_at") if evidence else None,
        "review_at": evidence.get("review_at") if evidence else None,
        "unlocks_mode": evidence.get("unlocks_mode") if evidence else None,
        "next_action": next_action_text,
        "secret_values_exposed": False,
    }


def find_requirement(adapter_id, requirement_id):
    spec = OFFICIAL_API_REQUIREMENTS.get(adapter_id)
    if not spec:
        return None
    check = next(
        (item for item in spec["checks"] if item["check"] == requirement_id),
        None,
    )
    if check is None:
        return None
    return {"spec": spec, "check": check}


def is_evidence_valid(evidence):
    if not evidence:
        return False
    status = str(evidence.get("evidence_status", "")).lower()
    return status in APPROVED_EVIDENCE_STATUSES and not is_evidence_expired(evidence)


def is_evidence_expired(evidence):
    if not evidence or not evidence.get("expires_at"):
        return False
    try:
        expires_at = datetime.fromisoformat(str(evidence["expires_at"]))
    except ValueError:
        return True
    return expires_at < datetime.now()


def summarize_evidence_vault(requirements):
    return {
        "required_evidence_count": len(requirements),
        "approved_evidence_count": len(
            [row for row in requirements if row["evidence_readiness"] == "approved"]
        ),
        "missing_evidence_count": len(
            [row for row in requirements if row["evidence_readiness"] == "missing"]
        ),
        "review_evidence_count": len(
            [row for row in requirements if row["evidence_readiness"] == "review"]
        ),
        "expired_evidence_count": len(
            [row for row in requirements if row["evidence_readiness"] == "expired"]
        ),
    }


def classify_evidence_vault(summary):
    if summary["required_evidence_count"] == summary["approved_evidence_count"]:
        return "official_evidence_complete"
    if summary["approved_evidence_count"]:
        return "partial_official_evidence"
    return "official_evidence_missing"


def classify_portfolio_compliance(summary):
    if summary["official_api_compliant_route_count"] == summary["official_api_route_count"]:
        return "official_api_compliant"
    if summary["official_api_compliant_route_count"]:
        return "partial_official_api_compliance"
    return "official_api_blocked"


def sanitize_value(value):
    if value is None:
        return None
    if len(value) <= 4:
        return "***"
    return f"{value[:2]}***{value[-2:]}"
