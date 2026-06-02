import json
from datetime import datetime

from src.config.paths import LATEST_SIGNAL_FILE, SIGNAL_RUNS_DIR


def add_signal_metadata(
    signal_result,
    source,
    forecast_model,
    target_date,
    forecast_file,
    generated_at=None,
    extra_metadata=None,
):
    if generated_at is None:
        generated_at = datetime.now()

    metadata = {
        "source": source,
        "forecast_provider": source,
        "forecast_model": forecast_model,
        "target_date": target_date,
        "generated_at": generated_at.isoformat(timespec="seconds"),
        "forecast_file": str(forecast_file),
    }

    if extra_metadata:
        metadata.update(extra_metadata)

    signal_result["metadata"] = metadata

    return signal_result


def save_signal_outputs(
    signal_result,
    target_date=None,
    signal_file=LATEST_SIGNAL_FILE,
    run_history_dir=SIGNAL_RUNS_DIR,
):
    signal_file.parent.mkdir(parents=True, exist_ok=True)
    run_history_dir.mkdir(parents=True, exist_ok=True)

    if target_date:
        safe_target_date = str(target_date).replace("-", "")
        run_history_file = run_history_dir / f"{safe_target_date}_battery_signal.json"
    else:
        generated_at = datetime.now()
        run_history_file = (
            run_history_dir
            / f"{generated_at.strftime('%Y%m%d_%H%M%S')}_battery_signal.json"
        )

    with open(signal_file, "w", encoding="utf-8") as file:
        json.dump(signal_result, file, indent=2)

    with open(run_history_file, "w", encoding="utf-8") as file:
        json.dump(signal_result, file, indent=2)

    return {
        "signal_file": signal_file,
        "run_history_file": run_history_file,
    }
