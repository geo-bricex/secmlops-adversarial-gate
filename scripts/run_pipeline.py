from __future__ import annotations

import argparse
import subprocess
import sys

DATASETS = ("cic_iot_2023", "edge_iiotset", "ton_iot")


def run(dataset: str) -> None:
    for module in ("src.data.profile", "src.data.prepare"):
        subprocess.run([sys.executable, "-m", module, "--dataset", dataset], check=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Phase 1 data profiling and preparation")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--dataset", choices=DATASETS)
    group.add_argument("--all", action="store_true")
    args = parser.parse_args()
    for selected in DATASETS if args.all else (args.dataset,):
        run(selected)

