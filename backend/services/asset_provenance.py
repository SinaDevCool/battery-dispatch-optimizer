from datetime import datetime
from pathlib import Path
from typing import Any


DEFAULT_PRODUCTION_UPGRADE_PATH = (
    "Connect production forecast provider, exchange/market adapter, live telemetry, "
    "settlement evidence, and signed run provenance."
)


def build_asset_provenance(
    asset: Any,
    *,
    artifact: str | None = None,
    generated_at: str | None = None,
    kind: str | None = None,
    source_file: str | Path | None = None,
    production_upgrade_path: str | None = None,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    asset_dict = asset.to_dict() if hasattr(asset, "to_dict") else dict(asset or {})
    data_mode = asset_dict.get("data_mode") or "mock"
    data_profile = asset_dict.get("data_profile") or {}
    resolved_source_file = (
        str(source_file)
        if source_file
        else data_profile.get("forecast_source") or asset_dict.get("forecast_file")
    )

    metadata = {
        "asset_id": asset_dict.get("asset_id"),
        "asset_type": asset_dict.get("asset_type"),
        "asset_subtype": asset_dict.get("asset_subtype"),
        "data_mode": data_mode,
        "mock_or_production": "production" if data_mode == "production" else "mock",
        "source_file": resolved_source_file,
        "forecast_file": resolved_source_file,
        "artifact": artifact,
        "kind": kind,
        "generated_at": generated_at or utc_now(),
        "production_upgrade_path": (
            production_upgrade_path
            or data_profile.get("production_upgrade_path")
            or DEFAULT_PRODUCTION_UPGRADE_PATH
        ),
    }

    if extra:
        metadata.update({key: value for key, value in extra.items() if value is not None})

    return metadata


def attach_asset_provenance(
    payload: dict[str, Any],
    asset: Any,
    *,
    artifact: str | None = None,
    generated_at: str | None = None,
    kind: str | None = None,
    source_file: str | Path | None = None,
    production_upgrade_path: str | None = None,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    payload["metadata"] = build_asset_provenance(
        asset,
        artifact=artifact,
        generated_at=generated_at or payload.get("generated_at"),
        kind=kind,
        source_file=source_file or payload.get("source_file") or payload.get("forecast_file"),
        production_upgrade_path=production_upgrade_path,
        extra=extra,
    )
    return payload


def utc_now() -> str:
    return datetime.utcnow().isoformat(timespec="seconds") + "Z"
