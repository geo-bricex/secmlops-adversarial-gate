from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from src.data.io import discover_csvs, read_csvs, sha256_file
from src.utils.config import load_dataset_config


def profile_frame(frame: pd.DataFrame, target: str) -> dict:
    numeric = frame.select_dtypes(include="number")
    unique = frame.nunique(dropna=False)
    finite_numeric = numeric.replace([np.inf, -np.inf], np.nan)
    quantiles = finite_numeric.quantile([0, .01, .25, .5, .75, .99, 1]).to_dict() if not numeric.empty else {}
    return {
        "rows": int(len(frame)), "columns": int(frame.shape[1]),
        "feature_names": list(map(str, frame.columns)),
        "dtypes": {str(k): str(v) for k, v in frame.dtypes.items()},
        "target": target,
        "labels": frame[target].value_counts(dropna=False).rename_axis("label").reset_index(name="count").astype({"label": str}).to_dict("records") if target in frame else [],
        "missing_values": {str(k): int(v) for k, v in frame.isna().sum().items() if v},
        "infinite_values": {str(k): int(v) for k, v in np.isinf(numeric).sum().items() if v},
        "duplicate_rows": int(frame.duplicated().sum()),
        "constant_features": [str(k) for k, v in unique.items() if v <= 1 and k != target],
        "binary_features": [str(k) for k, v in unique.items() if v == 2 and k != target],
        "discrete_features": [str(k) for k in numeric.columns if 2 < unique[k] <= 20 and k != target],
        "continuous_features": [str(k) for k in numeric.columns if unique[k] > 20 and k != target],
        "cardinality": {str(k): int(v) for k, v in unique.items()},
        "numeric_percentiles": quantiles,
    }


def profile_dataset(dataset: str) -> Path:
    cfg = load_dataset_config(dataset)
    raw = Path("data") / dataset / "raw"
    paths = discover_csvs(raw, cfg.get("glob", "*.csv"))
    frame = read_csvs(paths)
    result = profile_frame(frame, cfg["target"])
    result["files"] = [{"path": str(p), "bytes": p.stat().st_size, "sha256": sha256_file(p)} for p in paths]
    output = Path("results/data_profile") / f"{dataset}_profile.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, default=str), encoding="utf-8")
    return output


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", required=True)
    args = parser.parse_args()
    print(profile_dataset(args.dataset))
