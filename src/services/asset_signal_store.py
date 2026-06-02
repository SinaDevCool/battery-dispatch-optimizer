from datetime import datetime

from src.config.paths import ASSET_OUTPUTS_DIR, DATABASE_FILE
from src.db.repositories.signal_repository import save_signal_run
from src.storage import get_storage_client


def get_asset_signal_dir(asset_id, base_dir=ASSET_OUTPUTS_DIR):
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
    storage = get_storage_client()
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
    storage = get_storage_client()
    latest_signal_file = get_asset_latest_signal_file(asset_id, base_dir=base_dir)

    if not storage.exists(latest_signal_file):
        return {
            "status": "not_found",
            "message": f"No latest signal found for asset: {asset_id}",
            "asset_id": asset_id,
            "data": None,
        }

    signal = storage.read_json(latest_signal_file)

    return {
        "status": "ok",
        "asset_id": asset_id,
        "signal_file": str(latest_signal_file),
        "data": signal,
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
