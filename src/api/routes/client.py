from fastapi import APIRouter

from src.api.common import validate_client_config
from src.config.client_config import load_client_config, save_client_config
from src.config.client_presets import CLIENT_PRESETS


router = APIRouter()


@router.get("/client/config")
def get_client_config():
    try:
        config = load_client_config()

        return {
            "status": "ok",
            "config": config,
        }

    except FileNotFoundError as error:
        return {
            "status": "not_found",
            "message": str(error),
        }


@router.post("/client/config")
def update_client_config(config: dict):
    validation_errors = validate_client_config(config)

    if validation_errors:
        return {
            "status": "invalid",
            "message": "Client config validation failed.",
            "errors": validation_errors,
        }

    config_file = save_client_config(config)

    return {
        "status": "ok",
        "message": "Client config saved successfully.",
        "config_file": str(config_file),
        "config": config,
    }


@router.get("/client/presets")
def list_client_presets():
    return {
        "status": "ok",
        "presets": list(CLIENT_PRESETS.keys()),
    }


@router.post("/client/presets/{preset_name}/apply")
def apply_client_preset(preset_name: str):
    if preset_name not in CLIENT_PRESETS:
        return {
            "status": "not_found",
            "message": f"Unknown preset: {preset_name}",
        }

    config = CLIENT_PRESETS[preset_name]
    validation_errors = validate_client_config(config)

    if validation_errors:
        return {
            "status": "invalid",
            "message": "Preset config validation failed.",
            "errors": validation_errors,
        }

    config_file = save_client_config(config)

    return {
        "status": "ok",
        "message": f"Applied client preset: {preset_name}",
        "config_file": str(config_file),
        "config": config,
    }
