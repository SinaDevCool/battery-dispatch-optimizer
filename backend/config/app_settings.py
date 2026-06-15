import os
from functools import lru_cache
from typing import Literal

from pydantic import BaseModel


EnvironmentName = Literal["local", "development", "staging", "production"]
StorageBackend = Literal["local", "azure_blob"]
AuthMode = Literal["dev", "entra"]


class AppSettings(BaseModel):
    environment: EnvironmentName = "local"
    service_name: str = "battery-dispatch-optimizer"

    frontend_origin: str = "http://127.0.0.1:3000"
    api_public_base_url: str = "http://127.0.0.1:8000"

    auth_mode: AuthMode = "dev"
    entra_tenant_id: str | None = None
    entra_audience: str | None = None

    storage_backend: StorageBackend = "local"
    azure_storage_account_url: str | None = None
    azure_blob_container_name: str = "battery-dispatch-data"

    database_url: str | None = None
    key_vault_url: str | None = None
    applicationinsights_connection_string: str | None = None

    entsoe_api_key: str | None = None
    entsoe_verify_ssl: bool = True

    @property
    def is_azure(self):
        return self.environment in {"staging", "production"}


def _get_bool_env(name, default):
    value = os.environ.get(name)

    if value is None:
        return default

    return value.strip().lower() in {"1", "true", "yes", "on"}


@lru_cache
def get_app_settings():
    return AppSettings(
        environment=os.environ.get("APP_ENV", "local"),
        service_name=os.environ.get(
            "SERVICE_NAME",
            "battery-dispatch-optimizer",
        ),
        frontend_origin=os.environ.get(
            "FRONTEND_ORIGIN",
            "http://127.0.0.1:3000",
        ),
        api_public_base_url=os.environ.get(
            "API_PUBLIC_BASE_URL",
            "http://127.0.0.1:8000",
        ),
        auth_mode=os.environ.get("AUTH_MODE", "dev"),
        entra_tenant_id=os.environ.get("ENTRA_TENANT_ID"),
        entra_audience=os.environ.get("ENTRA_AUDIENCE"),
        storage_backend=os.environ.get("STORAGE_BACKEND", "local"),
        azure_storage_account_url=os.environ.get("AZURE_STORAGE_ACCOUNT_URL"),
        azure_blob_container_name=os.environ.get(
            "AZURE_BLOB_CONTAINER_NAME",
            "battery-dispatch-data",
        ),
        database_url=os.environ.get("DATABASE_URL"),
        key_vault_url=os.environ.get("KEY_VAULT_URL"),
        applicationinsights_connection_string=os.environ.get(
            "APPLICATIONINSIGHTS_CONNECTION_STRING"
        ),
        entsoe_api_key=(
            os.environ.get("ENTSOE_API_KEY")
            or os.environ.get("ENTSOE_TOKEN")
        ),
        entsoe_verify_ssl=_get_bool_env("ENTSOE_VERIFY_SSL", True),
    )



