from pathlib import Path

from src.config.paths import FORECAST_FILE


FORECAST_FILES = {
    "local_saved_forecast": FORECAST_FILE,
    "demo_high_spread": Path("data/processed/demo_high_spread_forecast.csv"),
    "inhouse_placeholder": Path("data/processed/inhouse_placeholder_forecast.csv"),
}


def get_forecast_files():
    return FORECAST_FILES.copy()
