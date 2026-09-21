from __future__ import annotations

import hashlib
from pathlib import Path

import pandas as pd


def discover_csvs(directory: str | Path, pattern: str = "*.csv") -> list[Path]:
    return sorted(Path(directory).rglob(pattern))


def sha256_file(path: str | Path, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        while chunk := stream.read(chunk_size):
            digest.update(chunk)
    return digest.hexdigest()


def read_csvs(paths: list[Path]) -> pd.DataFrame:
    if not paths:
        raise FileNotFoundError("No CSV files were found")
    return pd.concat((pd.read_csv(path, low_memory=False) for path in paths), ignore_index=True)

