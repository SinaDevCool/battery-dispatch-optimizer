import json
from datetime import datetime
from pathlib import Path

import pandas as pd


class LocalStorageClient:
    def exists(self, path):
        return Path(path).exists()

    def list_files(self, prefix, pattern="*"):
        directory = Path(prefix)

        if not directory.exists():
            return []

        return sorted(directory.glob(pattern))

    def file_status(self, path):
        path = Path(path)

        if not path.exists():
            return {
                "exists": False,
                "path": str(path),
                "last_modified": None,
                "size_bytes": 0,
            }

        modified_time = datetime.fromtimestamp(path.stat().st_mtime)

        return {
            "exists": True,
            "path": str(path),
            "last_modified": modified_time.isoformat(timespec="seconds"),
            "size_bytes": path.stat().st_size,
        }

    def read_text(self, path):
        return Path(path).read_text(encoding="utf-8")

    def write_text(self, path, value):
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(value, encoding="utf-8")

    def read_json(self, path):
        return json.loads(self.read_text(path))

    def write_json(self, path, value):
        self.write_text(path, json.dumps(value, indent=2, default=str))

    def read_dataframe(self, path, **kwargs):
        return pd.read_csv(path, **kwargs)

    def write_dataframe(self, path, dataframe, **kwargs):
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        dataframe.to_csv(path, index=False, **kwargs)



