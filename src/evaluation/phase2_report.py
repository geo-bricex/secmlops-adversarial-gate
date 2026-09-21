"""Build the reproducible clean-baseline Phase-2 consolidation from run artifacts."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
DATASETS = ("cic_iot_2023", "edge_iiotset", "ton_iot")
SEEDS = (42, 123, 2026)
METRICS = ("accuracy", "precision", "attack_recall", "specificity", "f1", "roc_auc", "pr_auc", "mcc")


def main() -> None:
    rows = []
    convergence = []
    for dataset in DATASETS:
        output = ROOT / "results" / "baseline" / dataset
        for seed in SEEDS:
            metrics_path = output / f"metrics_seed_{seed}.json"
            if not metrics_path.exists():
                raise FileNotFoundError(metrics_path)
            record = json.loads(metrics_path.read_text(encoding="utf-8"))
            rows.append(record)
            history = pd.read_csv(output / f"training_history_seed_{seed}.csv")
            best_epoch = int(record["best_epoch"])
            convergence.append({
                "dataset": dataset,
                "seed": seed,
                "best_epoch": best_epoch,
                "epochs_executed": int(record["epochs"]),
                "final_train_loss": float(history.iloc[-1]["train_loss"]),
                "final_validation_loss": float(history.iloc[-1]["validation_loss"]),
                "best_validation_loss": float(history["validation_loss"].min()),
                "possible_epoch_cap_truncation": best_epoch == int(record["epochs"]),
            })
    runs = pd.DataFrame(rows).sort_values(["dataset", "seed"])
    runs.to_csv(ROOT / "results" / "baseline" / "phase2_runs.csv", index=False)
    aggregates = []
    for dataset, group in runs.groupby("dataset", sort=True):
        for metric in METRICS:
            aggregates.append({"dataset": dataset, "metric": metric, "mean": group[metric].mean(), "std": group[metric].std(ddof=1), "n": len(group)})
    pd.DataFrame(aggregates).to_csv(ROOT / "results" / "baseline" / "phase2_summary.csv", index=False)
    pd.DataFrame(convergence).sort_values(["dataset", "seed"]).to_csv(ROOT / "results" / "baseline" / "phase2_convergence.csv", index=False)
    try:
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots(figsize=(8, 4.5))
        pivot = runs.pivot(index="dataset", columns="seed", values="f1").reindex(DATASETS)
        pivot.plot(kind="bar", ax=ax, ylim=(max(0, float(pivot.min().min()) - .03), 1.005), rot=0)
        ax.set_ylabel("Test F1")
        ax.set_title("Phase 2 clean-baseline F1 by dataset and seed")
        ax.grid(axis="y", alpha=.25)
        fig.tight_layout()
        figures = ROOT / "results" / "figures" / "baseline"; figures.mkdir(parents=True, exist_ok=True)
        fig.savefig(figures / "phase2_f1_by_seed.png", dpi=160)
        plt.close(fig)
    except ImportError:
        figures = ROOT / "results" / "figures" / "baseline"; figures.mkdir(parents=True, exist_ok=True)
        labels = {"cic_iot_2023": "CIC", "edge_iiotset": "Edge", "ton_iot": "ToN"}
        f1 = {dataset: float(runs.loc[runs.dataset == dataset, "f1"].mean()) for dataset in DATASETS}
        bars = "".join(f'<rect x="{70+i*150}" y="{260-f1[d]*220:.1f}" width="80" height="{f1[d]*220:.1f}" fill="#2878b5"/><text x="{80+i*150}" y="285">{labels[d]}</text><text x="{78+i*150}" y="{250-f1[d]*220:.1f}">{f1[d]:.3f}</text>' for i, d in enumerate(DATASETS))
        (figures / "phase2_f1_by_seed.svg").write_text(f'<svg xmlns="http://www.w3.org/2000/svg" width="560" height="320"><text x="120" y="28" font-size="18">Phase 2 clean-baseline mean test F1</text><line x1="50" y1="260" x2="530" y2="260" stroke="black"/>{bars}</svg>', encoding="utf-8")


if __name__ == "__main__":
    main()
