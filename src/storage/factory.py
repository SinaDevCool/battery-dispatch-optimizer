from functools import lru_cache

from src.config.app_settings import get_app_settings
from src.storage.azure_blob import AzureBlobStorageClient
from src.storage.local import LocalStorageClient


@lru_cache
def get_storage_client():
    settings = get_app_settings()

    if settings.storage_backend == "azure_blob":
        if not settings.azure_storage_account_url:
            raise ValueError(
                "AZURE_STORAGE_ACCOUNT_URL is required when STORAGE_BACKEND=azure_blob."
            )

        return AzureBlobStorageClient(
            account_url=settings.azure_storage_account_url,
            container_name=settings.azure_blob_container_name,
        )

    return LocalStorageClient()
