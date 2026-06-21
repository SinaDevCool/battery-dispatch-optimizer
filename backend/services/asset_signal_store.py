from datetime import datetime

from backend.config.paths import ASSET_OUTPUTS_DIR, DATABASE_FILE
from backend.data_environment import current_data_mode, is_live_mode, is_mock_mode, live_not_configured_response, mode_asset_outputs_dir
from backend.db.repositories.signal_repository import (
    get_signal_run,
    list_signal_runs,
    save_signal_run,
)
from backend.storage import get_storage_client


def get_asset_signal_dir(asset_id, base_dir=ASSET_OUTPUTS_DIR):
    if base_dir == ASSET_OUTPUTS_DIR:
        base_dir = mode_asset_outputs_dir()
    return base_dir / asset_id


def get_asset_signal_runs_dir(asset_id, base_dir=ASSET_OUTPUTS_DIR):
    return get_asset_signal_dir(asset_id, base_dir=base_dir) / "runs"


def get_asset_latest_signal_file(asset_id, base_dir=ASSET_OUTPUTS_DIR):
    return get_asset_signal_dir(asset_id, base_dir=base_dir) / "latest_signal.json"


def save_asset_signal(
    signal_result,
    asset_id,
    target_date=None,
    base_dir=ASSET_OUTPUTS_DIR,
    db_file=DATABASE_FILE,
):
    data_mode = current_data_mode()
    storage = get_storage_client()
    signal_result.setdefault("metadata", {})
    signal_result["metadata"]["data_mode"] = data_mode
    asset_dir = get_asset_signal_dir(asset_id, base_dir=base_dir)
    runs_dir = get_asset_signal_runs_dir(asset_id, base_dir=base_dir)
    latest_signal_file = get_asset_latest_signal_file(asset_id, base_dir=base_dir)

    if target_date:
        safe_target_date = str(target_date).replace("-", "")
        run_file = runs_dir / f"{safe_target_date}_signal.json"
    else:
        generated_at = datetime.now()
        run_file = runs_dir / f"{generated_at.strftime('%Y%m%d_%H%M%S')}_signal.json"

    storage.write_json(latest_signal_file, signal_result)
    storage.write_json(run_file, signal_result)

    signal_id = save_signal_run(
        signal_result=signal_result,
        asset_id=asset_id,
        db_file=db_file,
    )
    return {
        "asset_latest_signal_file": latest_signal_file,
        "asset_run_file": run_file,
        "signal_id": signal_id,
    }


def load_asset_latest_signal(asset_id, base_dir=ASSET_OUTPUTS_DIR):
    data_mode = current_data_mode()
    storage = get_storage_client()
    latest_signal_file = get_asset_latest_signal_file(asset_id, base_dir=base_dir)

    if not storage.exists(latest_signal_file):
        if is_mock_mode(data_mode) and base_dir == ASSET_OUTPUTS_DIR:
            legacy_latest_signal_file = ASSET_OUTPUTS_DIR / asset_id / "latest_signal.json"
            if storage.exists(legacy_latest_signal_file):
                signal = storage.read_json(legacy_latest_signal_file)
                return {
                    "status": "ok",
                    "asset_id": asset_id,
                    "data_mode": data_mode,
                    "signal_file": str(legacy_latest_signal_file),
                    "storage_source": "legacy_mock_file",
                    "data": signal,
                }

        database_signal = load_latest_signal_from_database(asset_id, data_mode=data_mode)

        if database_signal is not None:
            return database_signal

        if is_live_mode(data_mode):
            return live_not_configured_response(
                asset_id=asset_id,
                artifact="latest_signal",
                message="No live signal exists for this asset. Run a live forecast/signal pipeline or switch to Mock Data mode.",
            ) | {"data": None}

        return {
            "status": "not_found",
            "data_mode": data_mode,
            "message": f"No latest signal found for asset: {asset_id}",
            "asset_id": asset_id,
            "data": None,
        }

    signal = storage.read_json(latest_signal_file)

    return {
        "status": "ok",
        "asset_id": asset_id,
        "data_mode": data_mode,
        "signal_file": str(latest_signal_file),
        "data": signal,
    }


def load_latest_signal_from_database(asset_id, data_mode: str | None = None):
    signal_runs = list_signal_runs(asset_id=asset_id, limit=1)

    if not signal_runs:
        return None

    signal_id = signal_runs[0]["signal_id"]
    signal_run = get_signal_run(signal_id)

    if signal_run is None:
        return None

    payload = signal_run["payload"]
    payload_data_mode = (payload.get("metadata") or {}).get("data_mode")
    if payload_data_mode and payload_data_mode != (data_mode or current_data_mode()):
        return None
    if not payload_data_mode and is_live_mode(data_mode or current_data_mode()):
        return None
    payload.setdefault("metadata", {})
    payload["metadata"].setdefault("asset_id", asset_id)
    payload["metadata"].setdefault("data_mode", data_mode or current_data_mode())
    payload["metadata"]["signal_id"] = signal_id
    payload["metadata"]["storage_source"] = "database"

    return {
        "status": "ok",
        "asset_id": asset_id,
        "data_mode": data_mode or current_data_mode(),
        "signal_file": None,
        "signal_id": signal_id,
        "storage_source": "database",
        "data": payload,
    }


def list_asset_signal_history(asset_id, base_dir=ASSET_OUTPUTS_DIR):
    storage = get_storage_client()
    runs_dir = get_asset_signal_runs_dir(asset_id, base_dir=base_dir)

    if not storage.exists(runs_dir) and not storage.list_files(runs_dir, "*_signal.json"):
        return {
            "status": "not_found",
            "message": f"No signal history found for asset: {asset_id}",
            "asset_id": asset_id,
            "runs": [],
        }

    run_files = storage.list_files(runs_dir, "*_signal.json")
    runs = []

    for run_file in run_files:
        status = storage.file_status(run_file)
        runs.append(
            {
                "file_name": run_file.name,
                "file_path": str(run_file),
                "size_bytes": status["size_bytes"],
                "last_modified": status["last_modified"],
            }
        )

    return {
        "status": "ok",
        "asset_id": asset_id,
        "runs": runs,
    }


def load_asset_signal_run(asset_id, file_name, base_dir=ASSET_OUTPUTS_DIR):
    storage = get_storage_client()
    runs_dir = get_asset_signal_runs_dir(asset_id, base_dir=base_dir)
    run_file = runs_dir / file_name

    if not storage.exists(run_file):
        return {
            "status": "not_found",
            "message": f"Signal run not found for asset {asset_id}: {file_name}",
            "asset_id": asset_id,
            "data": None,
        }

    signal = storage.read_json(run_file)

    return {
        "status": "ok",
        "asset_id": asset_id,
        "signal_file": str(run_file),
        "data": signal,
    }



