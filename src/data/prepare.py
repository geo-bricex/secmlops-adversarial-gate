from __future__ import annotations

import argparse
import json
from pathlib import Path

from src.data.io import discover_csvs, read_csvs
from src.data.sampling import stratified_sample, stratified_split
from src.preprocessing.labels import map_binary_labels
from src.utils.config import load_dataset_config, load_yaml


def prepare(dataset: str) -> dict:
    base, cfg = load_yaml("configs/base.yaml"), load_dataset_config(dataset)
    paths = discover_csvs(Path("data") / dataset / "raw", cfg.get("glob", "*.csv"))
    frame = read_csvs(paths)
    frame["binary_target"] = map_binary_labels(frame[cfg["target"]], cfg["benign_labels"])
    sample = stratified_sample(frame, "binary_target", cfg.get("sample_max_rows"), base["seed"])
    ratios = base["splits"]
    splits = stratified_split(sample, "binary_target", base["seed"], ratios["train"], ratios["validation"], ratios["test"])
    out = Path("data") / dataset / "processed"
    metadata = {"dataset": dataset, "population_rows": len(frame), "sample_rows": len(sample), "seed": base["seed"], "strategy": "stratified_random", "splits": {}}
    for name, part in zip(("train", "validation", "test"), splits):
        part.to_parquet(out / f"{name}.parquet", index=False)
        metadata["splits"][name] = {"rows": len(part), "class_counts": part["binary_target"].value_counts().to_dict()}
    (out / "metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    return metadata


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", required=True)
    args = parser.parse_args()
    print(json.dumps(prepare(args.dataset), indent=2))

