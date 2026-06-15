from backend.services.asset_signal_store import (
    list_asset_signal_history,
    load_asset_latest_signal,
    load_asset_signal_run,
    save_asset_signal,
)


def test_save_and_load_asset_signal(tmp_path):
    signal_result = {
        "summary": {
            "signal": "ACTION",
            "total_pnl_eur": 100.0,
        },
        "dispatch": [],
        "metadata": {
            "asset_id": "test_asset",
        },
    }

    saved_files = save_asset_signal(
        signal_result=signal_result,
        asset_id="test_asset",
        target_date="2026-01-02",
        base_dir=tmp_path,
        db_file=tmp_path / "test.sqlite",
    )

    assert saved_files["asset_latest_signal_file"].exists()
    assert saved_files["asset_run_file"].exists()

    latest = load_asset_latest_signal("test_asset", base_dir=tmp_path)

    assert latest["status"] == "ok"
    assert latest["asset_id"] == "test_asset"
    assert latest["data"]["summary"]["signal"] == "ACTION"

    history = list_asset_signal_history("test_asset", base_dir=tmp_path)

    assert history["status"] == "ok"
    assert len(history["runs"]) == 1
    assert history["runs"][0]["file_name"] == "20260102_signal.json"

    run = load_asset_signal_run(
        asset_id="test_asset",
        file_name="20260102_signal.json",
        base_dir=tmp_path,
    )

    assert run["status"] == "ok"
    assert run["data"]["summary"]["total_pnl_eur"] == 100.0


def test_missing_asset_signal_returns_not_found(tmp_path):
    latest = load_asset_latest_signal("missing_asset", base_dir=tmp_path)
    history = list_asset_signal_history("missing_asset", base_dir=tmp_path)

    assert latest["status"] == "not_found"
    assert history["status"] == "not_found"
    assert history["runs"] == []



