from src.config.paths import (
    CLIENT_CONFIG_FILE,
    FORECAST_FILE,
    LATEST_SIGNAL_FILE,
    OUTPUT_DATA_DIR,
    PROCESSED_DATA_DIR,
    SCENARIO_RESULTS_FILE,
    SIGNAL_RUNS_DIR,
)


def test_path_constants_are_under_data_folder():
    paths = [
        CLIENT_CONFIG_FILE,
        FORECAST_FILE,
        LATEST_SIGNAL_FILE,
        OUTPUT_DATA_DIR,
        PROCESSED_DATA_DIR,
        SCENARIO_RESULTS_FILE,
        SIGNAL_RUNS_DIR,
    ]

    for path in paths:
        assert str(path).startswith("data")


def test_forecast_file_name():
    assert FORECAST_FILE.name == "next_day_price_forecast.csv"


def test_latest_signal_file_name():
    assert LATEST_SIGNAL_FILE.name == "latest_battery_signal.json"