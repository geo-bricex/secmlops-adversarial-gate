from __future__ import annotations

import argparse
import json
from pathlib import Path

from src.security_gate.gate import evaluate_gate
from src.utils.config import load_yaml


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", required=True)
    parser.add_argument("--model-id", required=True)
    parser.add_argument("--clean-metrics", required=True, type=Path)
    parser.add_argument("--adversarial-metrics", required=True, type=Path)
    args = parser.parse_args()
    policy = load_yaml("configs/security_gate.yaml")
    result = evaluate_gate(args.model_id, args.dataset, json.loads(args.clean_metrics.read_text()), json.loads(args.adversarial_metrics.read_text()), policy["thresholds"], {})
    output = Path("results/security_gate") / args.dataset / args.model_id / "decision.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(output)


if __name__ == "__main__":
    main()

