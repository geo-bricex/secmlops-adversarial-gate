from __future__ import annotations

from datetime import datetime, timezone


def evaluate_gate(model_id: str, dataset: str, clean: dict, adversarial: dict, thresholds: dict, attack_configuration: dict, **metadata) -> dict:
    checks = {
        "clean_f1": clean["f1"] >= thresholds["min_clean_f1"],
        "clean_attack_recall": clean["attack_recall"] >= thresholds["min_clean_attack_recall"],
        "adversarial_attack_recall": adversarial["attack_recall"] >= thresholds["min_adversarial_attack_recall"],
        "relative_f1_drop": adversarial["relative_f1_drop"] <= thresholds["max_relative_f1_drop"],
    }
    return {
        "dataset": dataset, "model_id": model_id, "decision": "PASS" if all(checks.values()) else "BLOCK",
        "clean_metrics": clean, "adversarial_metrics": adversarial, "thresholds": thresholds,
        "conditions": checks, "failed_conditions": [name for name, passed in checks.items() if not passed],
        "attack_configuration": attack_configuration, "timestamp": datetime.now(timezone.utc).isoformat(), **metadata,
    }

