from datetime import datetime
from pathlib import Path

from backend.config.paths import ASSET_OUTPUTS_DIR
from backend.services.asset_provenance import build_asset_provenance


def asset_output_dir(asset_id: str) -> Path:
    return ASSET_OUTPUTS_DIR / asset_id


def asset_scenario_results_file(asset_id: str) -> Path:
    return asset_output_dir(asset_id) / "scenario_results.json"


def asset_price_stress_results_file(asset_id: str) -> Path:
    return asset_output_dir(asset_id) / "price_stress_results.json"


def build_asset_output_envelope(
    asset: dict,
    forecast_file: str,
    kind: str,
    results: list[dict],
):
    return {
        "metadata": build_asset_provenance(
            asset,
            kind=kind,
            source_file=forecast_file,
            generated_at=datetime.utcnow().isoformat(timespec="seconds") + "Z",
            production_upgrade_path=(
                "Persist production scenario runs with forecast snapshot IDs, optimizer run IDs, "
                "capex/degradation assumptions, and approval history."
            ),
        ),
        "results": results,
    }


def extract_results(payload):
    if isinstance(payload, dict) and isinstance(payload.get("results"), list):
        return payload["results"]
    return payload if isinstance(payload, list) else []


def extract_metadata(payload):
    if isinstance(payload, dict) and isinstance(payload.get("metadata"), dict):
        return payload["metadata"]
    return {}
