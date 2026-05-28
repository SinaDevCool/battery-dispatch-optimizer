import json
from pathlib import Path


DEFAULT_CLIENT_CONFIG_FILE = Path("data/config/client_config.json")


def load_client_config(config_file=DEFAULT_CLIENT_CONFIG_FILE):
    if not config_file.exists():
        raise FileNotFoundError(
            f"Client config file not found: {config_file}"
        )

    with open(config_file, "r", encoding="utf-8") as file:
        return json.load(file)


def save_client_config(config, config_file=DEFAULT_CLIENT_CONFIG_FILE):
    config_file.parent.mkdir(parents=True, exist_ok=True)

    with open(config_file, "w", encoding="utf-8") as file:
        json.dump(config, file, indent=2)

    return config_file


def get_client_battery_config(config_file=DEFAULT_CLIENT_CONFIG_FILE):
    config = load_client_config(config_file)
    return config["battery_config"]


def get_client_strategy_config(config_file=DEFAULT_CLIENT_CONFIG_FILE):
    config = load_client_config(config_file)
    return config["strategy_config"]


def get_client_commercial_config(config_file=DEFAULT_CLIENT_CONFIG_FILE):
    config = load_client_config(config_file)
    return config["commercial_config"]