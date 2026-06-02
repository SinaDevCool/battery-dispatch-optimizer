from pathlib import Path


DATA_DIR = Path("data")
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
OUTPUT_DATA_DIR = DATA_DIR / "outputs"
ASSET_OUTPUTS_DIR = OUTPUT_DATA_DIR / "assets"
CONFIG_DATA_DIR = DATA_DIR / "config"

FORECAST_FILE = PROCESSED_DATA_DIR / "next_day_price_forecast.csv"

LATEST_SIGNAL_FILE = OUTPUT_DATA_DIR / "latest_battery_signal.json"
SCENARIO_RESULTS_FILE = OUTPUT_DATA_DIR / "scenario_results.json"
PRICE_STRESS_RESULTS_FILE = OUTPUT_DATA_DIR / "price_stress_results.json"

SIGNAL_RUNS_DIR = OUTPUT_DATA_DIR / "runs"
MONTHLY_REPORT_PATTERN = "monthly_report_*.html"
CLIENT_CONFIG_FILE = CONFIG_DATA_DIR / "client_config.json"
ASSETS_CONFIG_FILE = CONFIG_DATA_DIR / "assets.json"
MARKET_PROFILES_FILE = CONFIG_DATA_DIR / "market_profiles.json"
PORTFOLIO_RESULTS_FILE = OUTPUT_DATA_DIR / "portfolio_results.json"
REVENUE_STACK_RESULTS_FILE = OUTPUT_DATA_DIR / "revenue_stack_results.json"
