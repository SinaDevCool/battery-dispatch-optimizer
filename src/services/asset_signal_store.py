import json
from datetime import datetime

from src.config.paths import ASSET_OUTPUTS_DIR


def get_asset_signal_dir(asset_id, base_dir=ASSET_OUTPUTS_DIR):
    return base_dir / asset_id


def get_asset_signal_runs_dir(asset_id, base_dir=ASSET_OUTPUTS_DIR):
    return get_asset_signal_dir(asset_id, base_dir=base_dir) / "runs"


def get_asset_latest_signal_file(asset_id, base_dir=ASSET_OUTPUTS_DIR):
    return get_asset_signal_dir(asset_id, base_dir=base_dir) / "latest_signal.json"


def save_asset_signal(signal_result, asset_id, target_date=None, base_dir=ASSET_OUTPUTS_DIR):
    asset_dir = get_asset_signal_dir(asset_id, base_dir=base_dir)
    runs_dir = get_asset_signal_runs_dir(asset_id, base_dir=base_dir)
    latest_signal_file = get_asset_latest_signal_file(asset_id, base_dir=base_dir)

    asset_dir.mkdir(parents=True, exist_ok=True)
    runs_dir.mkdir(parents=True, exist_ok=True)

    if target_date:
        safe_target_date = str(target_date).replace("-", "")
        run_file = runs_dir / f"{safe_target_date}_signal.json"
    else:
        generated_at = datetime.now()
        run_file = runs_dir / f"{generated_at.strftime('%Y%m%d_%H%M%S')}_signal.json"

    with open(latest_signal_file, "w", encoding="utf-8") as file:
        json.dump(signal_result, file, indent=2)

    with open(run_file, "w", encoding="utf-8") as file:
        json.dump(signal_result, file, indent=2)

    return {
        "asset_latest_signal_file": latest_signal_file,
        "asset_run_file": run_file,
    }


def load_asset_latest_signal(asset_id, base_dir=ASSET_OUTPUTS_DIR):
    latest_signal_file = get_asset_latest_signal_file(asset_id, base_dir=base_dir)

    if not latest_signal_file.exists():
        return {
            "status": "not_found",
            "message": f"No latest signal found for asset: {asset_id}",
            "asset_id": asset_id,
            "data": None,
        }

    with open(latest_signal_file, "r", encoding="utf-8") as file:
        signal = json.load(file)

    return {
        "status": "ok",
        "asset_id": asset_id,
        "signal_file": str(latest_signal_file),
        "data": signal,
    }


def list_asset_signal_history(asset_id, base_dir=ASSET_OUTPUTS_DIR):
    runs_dir = get_asset_signal_runs_dir(asset_id, base_dir=base_dir)

    if not runs_dir.exists():
        return {
            "status": "not_found",
            "message": f"No signal history found for asset: {asset_id}",
            "asset_id": asset_id,
            "runs": [],
        }

    run_files = sorted(runs_dir.glob("*_signal.json"))
    runs = []

    for run_file in run_files:
        runs.append(
            {
                "file_name": run_file.name,
                "file_path": str(run_file),
                "size_bytes": run_file.stat().st_size,
                "last_modified": datetime.fromtimestamp(
                    run_file.stat().st_mtime
                ).isoformat(timespec="seconds"),
            }
        )

    return {
        "status": "ok",
        "asset_id": asset_id,
        "runs": runs,
    }


def load_asset_signal_run(asset_id, file_name, base_dir=ASSET_OUTPUTS_DIR):
    runs_dir = get_asset_signal_runs_dir(asset_id, base_dir=base_dir)
    run_file = runs_dir / file_name

    if not run_file.exists():
        return {
            "status": "not_found",
            "message": f"Signal run not found for asset {asset_id}: {file_name}",
            "asset_id": asset_id,
            "data": None,
        }

    with open(run_file, "r", encoding="utf-8") as file:
        signal = json.load(file)

    return {
        "status": "ok",
        "asset_id": asset_id,
        "signal_file": str(run_file),
        "data": signal,
    }
