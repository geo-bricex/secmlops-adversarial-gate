from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[2]


def load_yaml(path: str | Path) -> dict[str, Any]:
    candidate = Path(path)
    if not candidate.is_absolute():
        candidate = ROOT / candidate
    with candidate.open(encoding="utf-8") as stream:
        value = yaml.safe_load(stream)
    if not isinstance(value, dict):
        raise ValueError(f"Configuration must be a mapping: {candidate}")
    return value


def load_dataset_config(dataset: str) -> dict[str, Any]:
    return load_yaml(Path("configs/datasets") / f"{dataset}.yaml")


def configuration_id(*configs: dict[str, Any]) -> str:
    payload = json.dumps(configs, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(payload.encode()).hexdigest()[:16]

