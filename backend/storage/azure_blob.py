import json
from datetime import datetime, timezone
from io import StringIO
from pathlib import Path

import pandas as pd


def _blob_name(path):
    return Path(path).as_posix()


class AzureBlobStorageClient:
    def __init__(self, account_url, container_name):
        try:
            from azure.identity import DefaultAzureCredential
            from azure.storage.blob import BlobServiceClient
        except ImportError as error:
            raise RuntimeError(
                "Azure Blob storage requires azure-identity and azure-storage-blob."
            ) from error

        credential = DefaultAzureCredential()
        blob_service_client = BlobServiceClient(
            account_url=account_url,
            credential=credential,
        )
        self.container_client = blob_service_client.get_container_client(
            container_name,
        )

    def exists(self, path):
        return self.container_client.get_blob_client(_blob_name(path)).exists()

    def list_files(self, prefix, pattern="*"):
        if pattern != "*":
            suffix = pattern.removeprefix("*")
        else:
            suffix = ""

        names = []

        for blob in self.container_client.list_blobs(
            name_starts_with=_blob_name(prefix),
        ):
            if not suffix or blob.name.endswith(suffix):
                names.append(Path(blob.name))

        return sorted(names)

    def file_status(self, path):
        blob_name = _blob_name(path)
        blob_client = self.container_client.get_blob_client(blob_name)

        if not blob_client.exists():
            return {
                "exists": False,
                "path": blob_name,
                "last_modified": None,
                "size_bytes": 0,
            }

        properties = blob_client.get_blob_properties()
        last_modified = properties.last_modified

        if last_modified is None:
            last_modified = datetime.now(timezone.utc)

        return {
            "exists": True,
            "path": blob_name,
            "last_modified": last_modified.isoformat(timespec="seconds"),
            "size_bytes": properties.size,
        }

    def read_text(self, path):
        blob_client = self.container_client.get_blob_client(_blob_name(path))
        data = blob_client.download_blob().readall()
        return data.decode("utf-8")

    def write_text(self, path, value):
        blob_client = self.container_client.get_blob_client(_blob_name(path))
        blob_client.upload_blob(value.encode("utf-8"), overwrite=True)

    def read_json(self, path):
        return json.loads(self.read_text(path))

    def write_json(self, path, value):
        self.write_text(path, json.dumps(value, indent=2, default=str))

    def read_dataframe(self, path, **kwargs):
        return pd.read_csv(StringIO(self.read_text(path)), **kwargs)

    def write_dataframe(self, path, dataframe, **kwargs):
        buffer = StringIO()
        dataframe.to_csv(buffer, index=False, **kwargs)
        self.write_text(path, buffer.getvalue())



