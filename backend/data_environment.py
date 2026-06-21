from __future__ import annotations

from contextvars import ContextVar
from pathlib import Path

from backend.config.paths import OUTPUT_DATA_DIR


DataMode = str
DEFAULT_DATA_MODE = "mock"
LIVE_DATA_MODE = "live"
MOCK_DATA_MODE = "mock"

_current_data_mode: ContextVar[str] = ContextVar(
    "battery_optimizer_data_mode",
    default=DEFAULT_DATA_MODE,
)


def normalize_data_mode(value: str | None) -> str:
    mode = str(value or DEFAULT_DATA_MODE).strip().lower()
    if mode in {"live", "production", "real", "prod"}:
        return LIVE_DATA_MODE
    return MOCK_DATA_MODE


def set_current_data_mode(value: str | None):
    return _current_data_mode.set(normalize_data_mode(value))


def reset_current_data_mode(token) -> None:
    _current_data_mode.reset(token)


def current_data_mode() -> str:
    return normalize_data_mode(_current_data_mode.get())


def is_mock_mode(value: str | None = None) -> bool:
    return normalize_data_mode(value or current_data_mode()) == MOCK_DATA_MODE


def is_live_mode(value: str | None = None) -> bool:
    return normalize_data_mode(value or current_data_mode()) == LIVE_DATA_MODE


def mode_output_root(data_mode: str | None = None) -> Path:
    return OUTPUT_DATA_DIR / normalize_data_mode(data_mode or current_data_mode())


def mode_asset_outputs_dir(data_mode: str | None = None) -> Path:
    return mode_output_root(data_mode=data_mode) / "assets"


def mode_global_output_file(file_name: str, data_mode: str | None = None) -> Path:
    return mode_output_root(data_mode=data_mode) / file_name


def live_not_configured_response(asset_id: str, artifact: str, message: str | None = None) -> dict:
    return {
        "status": "live_not_configured",
        "asset_id": asset_id,
        "data_mode": LIVE_DATA_MODE,
        "artifact": artifact,
        "message": message
        or f"Live data is not configured for {artifact}. Connect the production source or switch to Mock Data mode.",
    }
