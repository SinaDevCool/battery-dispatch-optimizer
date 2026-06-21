from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any

from backend.data_environment import (
    current_data_mode,
    is_live_mode,
    mode_asset_outputs_dir,
)


@dataclass(frozen=True)
class DataSourceDomain:
    domain: str
    label: str
    mock_source_type: str
    mock_source_name: str
    live_source_type: str
    live_source_name: str
    live_env_keys: tuple[str, ...]
    live_artifacts: tuple[str, ...]
    business_meaning: str
    production_upgrade: str


DATA_SOURCE_REGISTRY: tuple[DataSourceDomain, ...] = (
    DataSourceDomain(
        domain="forecasts",
        label="Forecasts",
        mock_source_type="simulated",
        mock_source_name="local forecast CSV / demo seed",
        live_source_type="connector",
        live_source_name="production forecast provider",
        live_env_keys=("FORECAST_PROVIDER_API_KEY", "ENTSOE_API_KEY"),
        live_artifacts=("latest_signal.json",),
        business_meaning="Price and dispatch decisions can be explained back to the forecast snapshot that created them.",
        production_upgrade="Connect the contracted forecast provider and persist forecast snapshot IDs.",
    ),
    DataSourceDomain(
        domain="market_prices",
        label="Market prices",
        mock_source_type="simulated",
        mock_source_name="demo market profile",
        live_source_type="connector",
        live_source_name="EPEX / ENTSO-E / TSO market data",
        live_env_keys=("ENTSOE_API_KEY", "EPEX_API_KEY", "REGELLEISTUNG_API_KEY"),
        live_artifacts=("latest_revenue_stack.json",),
        business_meaning="Revenue and route decisions are grounded in market data rather than static assumptions.",
        production_upgrade="Connect market-price feeds for day-ahead, intraday, and ancillary products.",
    ),
    DataSourceDomain(
        domain="optimizer_results",
        label="Optimizer results",
        mock_source_type="modelled",
        mock_source_name="local optimizer",
        live_source_type="runtime",
        live_source_name="production optimizer run",
        live_env_keys=(),
        live_artifacts=("latest_signal.json",),
        business_meaning="The schedule, PnL, SOC path, and decision trace are tied to the selected asset.",
        production_upgrade="Run the optimizer with live forecast, telemetry, and policy inputs.",
    ),
    DataSourceDomain(
        domain="execution",
        label="Execution",
        mock_source_type="paper",
        mock_source_name="paper trading / simulated market submission",
        live_source_type="connector",
        live_source_name="exchange or TSO order connector",
        live_env_keys=("EPEX_API_KEY", "REGELLEISTUNG_API_KEY"),
        live_artifacts=("latest_execution_proposal.json", "latest_market_submission.json"),
        business_meaning="Bid packages and market outcomes can be separated between paper evidence and actual submitted orders.",
        production_upgrade="Connect exchange credentials, order acknowledgements, award files, and cancellation records.",
    ),
    DataSourceDomain(
        domain="telemetry",
        label="Telemetry",
        mock_source_type="simulated",
        mock_source_name="demo local telemetry",
        live_source_type="connector",
        live_source_name="EMS / SCADA / meter telemetry",
        live_env_keys=("EMS_API_KEY", "SCADA_API_KEY", "METERING_API_KEY"),
        live_artifacts=("latest_telemetry.json",),
        business_meaning="Availability, SOC, metered delivery, and asset limits can be trusted for operational decisions.",
        production_upgrade="Connect EMS, SCADA, meter readings, outage status, and availability telemetry.",
    ),
    DataSourceDomain(
        domain="settlement",
        label="Settlement",
        mock_source_type="simulated",
        mock_source_name="paper settlement reconciliation",
        live_source_type="record",
        live_source_name="exchange / TSO / supplier settlement records",
        live_env_keys=("SETTLEMENT_SFTP_HOST", "SETTLEMENT_API_KEY"),
        live_artifacts=("latest_settlement_reconciliation.json",),
        business_meaning="Modelled revenue can be reconciled against awarded, delivered, and settled value.",
        production_upgrade="Attach award confirmations, metered delivery, invoice/settlement statements, and variance attribution.",
    ),
    DataSourceDomain(
        domain="revenue",
        label="Revenue stack",
        mock_source_type="modelled",
        mock_source_name="demo revenue assumptions",
        live_source_type="calculation",
        live_source_name="live market, execution, fee, and settlement evidence",
        live_env_keys=("ENTSOE_API_KEY", "EPEX_API_KEY", "SETTLEMENT_API_KEY"),
        live_artifacts=("latest_revenue_stack.json", "latest_revenue_stack_allocation.json"),
        business_meaning="Commercial value is traceable from product eligibility to allocation and settlement proof.",
        production_upgrade="Replace demo assumptions with live prices, executed trades, tariffs, fees, and settlement records.",
    ),
    DataSourceDomain(
        domain="ai_evidence",
        label="AI evidence",
        mock_source_type="curated_simulation",
        mock_source_name="complete simulated evidence pack",
        live_source_type="evidence_graph",
        live_source_name="production evidence graph",
        live_env_keys=("OPENAI_API_KEY",),
        live_artifacts=(),
        business_meaning="Persona agents can state whether their answer is based on simulated evidence or production proof.",
        production_upgrade="Feed the AI context from live connectors, signed records, and audit evidence instead of demo artifacts.",
    ),
)


def list_data_source_registry() -> list[dict[str, Any]]:
    return [domain_to_dict(domain) for domain in DATA_SOURCE_REGISTRY]


def build_data_readiness(asset_id: str = "default_site") -> dict[str, Any]:
    data_mode = current_data_mode()
    rows = [build_domain_readiness(domain, asset_id, data_mode) for domain in DATA_SOURCE_REGISTRY]
    live_ready_count = len([row for row in rows if row["live_status"] == "ready"])
    live_missing_count = len([row for row in rows if row["live_status"] == "missing"])
    current_ready_count = len([row for row in rows if row["current_status"] == "ready"])

    return {
        "status": "ok",
        "asset_id": asset_id,
        "data_mode": data_mode,
        "summary": {
            "domain_count": len(rows),
            "current_ready_count": current_ready_count,
            "live_ready_count": live_ready_count,
            "live_missing_count": live_missing_count,
            "production_claim_allowed": live_missing_count == 0,
        },
        "registry": list_data_source_registry(),
        "domains": rows,
    }


def build_domain_readiness(domain: DataSourceDomain, asset_id: str, data_mode: str) -> dict[str, Any]:
    live_configured = is_domain_live_configured(domain, asset_id)
    live_status = "ready" if live_configured else "missing"
    current_is_live = data_mode == "live"
    current_status = live_status if current_is_live else "ready"
    source_type = domain.live_source_type if current_is_live else domain.mock_source_type
    source_name = domain.live_source_name if current_is_live else domain.mock_source_name

    return {
        **domain_to_dict(domain),
        "asset_id": asset_id,
        "data_mode": data_mode,
        "current_status": current_status,
        "live_status": live_status,
        "mock_status": "ready",
        "source_type": source_type,
        "source_name": source_name,
        "production_claim_allowed": current_is_live and live_configured,
        "configured_live_inputs": configured_live_inputs(domain),
        "missing_live_inputs": missing_live_inputs(domain, asset_id),
    }


def build_source_provenance(
    *,
    domain: str | None,
    data_mode: str,
    asset_id: str | None = None,
    artifact: str | None = None,
) -> dict[str, Any]:
    registry_domain = get_domain(domain)
    if registry_domain is None:
        source_type = "connector" if data_mode == "live" else "simulated"
        source_name = "production source" if data_mode == "live" else "mock evidence"
        production_claim_allowed = data_mode == "live"
        business_meaning = "No domain-specific data source contract is registered yet."
        production_upgrade = "Register this domain in the data-source registry."
    else:
        readiness = build_domain_readiness(registry_domain, asset_id or "default_site", data_mode)
        source_type = readiness["source_type"]
        source_name = readiness["source_name"]
        production_claim_allowed = readiness["production_claim_allowed"]
        business_meaning = registry_domain.business_meaning
        production_upgrade = registry_domain.production_upgrade

    return {
        "data_mode": data_mode,
        "source_type": source_type,
        "source_name": source_name,
        "artifact": artifact,
        "production_claim_allowed": production_claim_allowed,
        "business_meaning": business_meaning,
        "production_upgrade": production_upgrade,
    }


def live_write_blocker(domain: str, asset_id: str = "default_site") -> dict[str, Any] | None:
    if not is_live_mode():
        return None

    registry_domain = get_domain(domain)
    if registry_domain and is_domain_live_configured(registry_domain, asset_id):
        return None

    return {
        "status": "live_not_configured",
        "asset_id": asset_id,
        "data_mode": "live",
        "domain": domain,
        "message": (
            f"Live {domain.replace('_', ' ')} cannot be generated from demo inputs. "
            "Connect the production source or switch to Mock Data mode."
        ),
        "source_contract": domain_to_dict(registry_domain) if registry_domain else None,
    }


def get_domain(domain: str | None) -> DataSourceDomain | None:
    if not domain:
        return None
    for item in DATA_SOURCE_REGISTRY:
        if item.domain == domain:
            return item
    return None


def is_domain_live_configured(domain: DataSourceDomain, asset_id: str) -> bool:
    return bool(configured_live_inputs(domain) or existing_live_artifacts(domain, asset_id))


def configured_live_inputs(domain: DataSourceDomain) -> list[str]:
    return [key for key in domain.live_env_keys if os.environ.get(key)]


def missing_live_inputs(domain: DataSourceDomain, asset_id: str) -> list[str]:
    missing_env = [key for key in domain.live_env_keys if not os.environ.get(key)]
    missing_artifacts = [
        artifact
        for artifact in domain.live_artifacts
        if not live_artifact_exists(asset_id, artifact)
    ]
    return [*missing_env, *missing_artifacts]


def existing_live_artifacts(domain: DataSourceDomain, asset_id: str) -> list[str]:
    return [
        artifact
        for artifact in domain.live_artifacts
        if live_artifact_exists(asset_id, artifact)
    ]


def live_artifact_exists(asset_id: str, artifact: str) -> bool:
    return (mode_asset_outputs_dir(data_mode="live") / asset_id / artifact).exists()


def domain_to_dict(domain: DataSourceDomain | None) -> dict[str, Any]:
    if domain is None:
        return {}
    return {
        "domain": domain.domain,
        "label": domain.label,
        "mock_source_type": domain.mock_source_type,
        "mock_source_name": domain.mock_source_name,
        "live_source_type": domain.live_source_type,
        "live_source_name": domain.live_source_name,
        "live_env_keys": list(domain.live_env_keys),
        "live_artifacts": list(domain.live_artifacts),
        "business_meaning": domain.business_meaning,
        "production_upgrade": domain.production_upgrade,
    }
