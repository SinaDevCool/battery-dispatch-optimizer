from pathlib import Path
from typing import Protocol

import pandas as pd


class StorageClient(Protocol):
    def exists(self, path: str | Path) -> bool:
        ...

    def list_files(self, prefix: str | Path, pattern: str = "*") -> list[Path]:
        ...

    def file_status(self, path: str | Path) -> dict:
        ...

    def read_text(self, path: str | Path) -> str:
        ...

    def write_text(self, path: str | Path, value: str) -> None:
        ...

    def read_json(self, path: str | Path):
        ...

    def write_json(self, path: str | Path, value) -> None:
        ...

    def read_dataframe(self, path: str | Path, **kwargs) -> pd.DataFrame:
        ...

    def write_dataframe(self, path: str | Path, dataframe: pd.DataFrame, **kwargs) -> None:
        ...
