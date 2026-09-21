"""Log completed Phase-2 run artifacts to MLflow without retraining."""
from __future__ import annotations

import json
from pathlib import Path

import mlflow

from src.tracking.mlflow import configure_tracking

ROOT = Path(__file__).resolve().parents[2]


def main() -> None:
    configure_tracking("secmlops-adversarial-gate-phase2")
    for dataset in ("cic_iot_2023", "edge_iiotset", "ton_iot"):
        for seed in (42, 123, 2026):
            path = ROOT / "results" / "baseline" / dataset / f"metrics_seed_{seed}.json"
            metrics = json.loads(path.read_text(encoding="utf-8"))
            with mlflow.start_run(run_name=f"{dataset}-seed-{seed}"):
                mlflow.set_tags({"dataset": dataset, "seed": str(seed), "phase": "2", "run_origin": "artifact_backfill"})
                mlflow.log_params({"seed": seed, "raw_feature_count": len(json.loads((ROOT / "results" / "baseline" / dataset / "feature_contract.json").read_text())["features"]), "batch_size": 4096, "max_epochs": 15, "patience": 3})
                mlflow.log_metrics({key: float(value) for key, value in metrics.items() if isinstance(value, (int, float))})
                mlflow.log_artifact(str(path), artifact_path="metrics")


if __name__ == "__main__":
    main()
