import pandas as pd

from src.storage.local import LocalStorageClient


def test_local_storage_json_roundtrip(tmp_path):
    storage = LocalStorageClient()
    path = tmp_path / "outputs" / "signal.json"
    payload = {"status": "ok", "value": 42}

    storage.write_json(path, payload)

    assert storage.exists(path)
    assert storage.read_json(path) == payload


def test_local_storage_dataframe_roundtrip(tmp_path):
    storage = LocalStorageClient()
    path = tmp_path / "processed" / "forecast.csv"
    dataframe = pd.DataFrame(
        [
            {"timestamp": "2026-01-01 00:00:00", "forecast_price": 10.5},
            {"timestamp": "2026-01-01 00:15:00", "forecast_price": 12.0},
        ]
    )

    storage.write_dataframe(path, dataframe)
    loaded = storage.read_dataframe(path)

    assert loaded.to_dict(orient="records") == dataframe.to_dict(orient="records")


def test_local_storage_lists_matching_files(tmp_path):
    storage = LocalStorageClient()
    run_dir = tmp_path / "runs"

    storage.write_json(run_dir / "20260101_battery_signal.json", {"status": "ok"})
    storage.write_json(run_dir / "ignore.json", {"status": "ok"})

    files = storage.list_files(run_dir, "*_battery_signal.json")

    assert [file.name for file in files] == ["20260101_battery_signal.json"]
