"""Generate leakage and adversarial-semantics decisions from audited real schemas."""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "results/data_profile"

TARGETS = {
    "cic_iot_2023": {"original_label", "source_file"},
    "edge_iiotset": {"Attack_label", "Attack_type", "source_file"},
    "ton_iot": {"label", "type", "source_file"},
}
IDENTIFIERS = {
    "edge_iiotset": {"frame.time", "ip.src_host", "ip.dst_host", "arp.dst.proto_ipv4", "arp.src.proto_ipv4",
                     "tcp.checksum", "tcp.options", "tcp.payload", "http.file_data", "http.request.uri.query",
                     "http.referer", "http.request.full_uri", "mqtt.msg", "tcp.ack", "tcp.ack_raw", "tcp.seq", "udp.stream"},
    "ton_iot": {"src_ip", "dst_ip", "dns_query", "http_uri", "http_user_agent", "ssl_subject", "ssl_issuer"},
    "cic_iot_2023": set(),
}
TEMPORAL = {"frame.time", "duration", "IAT", "udp.time_delta"}
BINARY_HINTS = {"label", "Attack_label", "fin_flag_number", "syn_flag_number", "rst_flag_number", "psh_flag_number",
                "ack_flag_number", "ece_flag_number", "cwr_flag_number", "HTTP", "HTTPS", "DNS", "Telnet", "SMTP",
                "SSH", "IRC", "TCP", "UDP", "DHCP", "ARP", "ICMP", "IGMP", "IPv", "LLC"}
DERIVED_HINTS = {"Rate", "Tot sum", "Min", "Max", "AVG", "Std", "Tot size", "Variance", "src_ip_bytes", "dst_ip_bytes",
                 "icmp.checksum", "tcp.flags.ack"}
CATEGORICAL_HINTS = {"Protocol Type", "proto", "service", "conn_state", "type", "Attack_type"}


def classify(dataset: str, row: pd.Series) -> tuple[str, str, str, str]:
    feature, dtype = row.feature, row.dtype
    low = feature.lower()
    if feature in TARGETS[dataset]:
        return "IDENTIFIER" if feature == "source_file" else "CATEGORICAL", "REMOVE", "none", "target/label metadata or provenance; direct leakage"
    if feature in IDENTIFIERS[dataset]:
        semantic = "TEMPORAL" if feature == "frame.time" else "IDENTIFIER"
        return semantic, "REMOVE", "none", "high-cardinality identity/content field; memorization and privacy risk"
    if feature in DERIVED_HINTS or any(token in low for token in ("mean", "std", "rate", "variance", "bytes")):
        return "CONTINUOUS_DERIVED", "CONDITIONALLY_MUTABLE", "nonnegative; preserve algebraic dependencies", "aggregate derived from packet/flow primitives"
    if feature in BINARY_HINTS or (row.cardinality_approx == 2 and feature not in CATEGORICAL_HINTS):
        return "BINARY", "IMMUTABLE", "values from observed binary domain", "continuous perturbation would create invalid flag values"
    if feature in CATEGORICAL_HINTS or dtype == "VARCHAR" or dataset == "edge_iiotset" and not pd.notna(row.get("analysis_dtype")):
        return "CATEGORICAL", "IMMUTABLE", "values from training vocabulary", "category cannot receive arbitrary continuous perturbations"
    if feature in TEMPORAL:
        return "TEMPORAL", "CONDITIONALLY_MUTABLE", "nonnegative; jointly consistent with rates/counters", "timing can change but only under traffic constraints"
    cardinality = int(row.cardinality_approx)
    if cardinality <= 256 or any(token in low for token in ("port", "count", "pkts", "len", "ttl", "number", "seq", "trans_id")):
        return "DISCRETE", "CONDITIONALLY_MUTABLE", "integer; observed range; nonnegative", "protocol/count field with bounded feasible values"
    return "CONTINUOUS_PRIMITIVE", "MUTABLE", "observed train range; nonnegative where applicable", "continuous traffic measurement, subject to feasibility projection"


def generate(dataset: str) -> None:
    stats = pd.read_csv(OUT / f"{dataset}_feature_stats.csv")
    config = yaml.safe_load((ROOT / "configs" / "datasets" / f"{dataset}.yaml").read_text(encoding="utf-8"))
    policy = config["feature_policy"]
    remove = set(policy.get("remove", []))
    numeric = set(policy.get("model_numeric", []))
    binary = set(policy.get("model_binary", []))
    categorical = set(policy.get("model_categorical", []))
    mutable = set(policy.get("mutable", []))
    conditional = set(policy.get("conditionally_mutable", [])) | set(policy.get("attack_conditionally_mutable", []))
    semantic_rows, leakage_rows = [], []
    for _, row in stats.iterrows():
        feature = row.feature
        if feature in remove:
            semantic, status, constraints, reason = "REMOVED", "REMOVE", "none", "frozen exclusion from model X"
        elif feature in binary:
            semantic, status, constraints, reason = "BINARY", "IMMUTABLE", "observed binary domain", "frozen binary model feature"
        elif feature in categorical:
            semantic, status, constraints, reason = "CATEGORICAL", "IMMUTABLE", "train vocabulary only", "frozen categorical model feature"
        elif feature in mutable:
            semantic, status, constraints, reason = "CONTINUOUS_PRIMITIVE", "MUTABLE", "projection, observed train range and integer rule where applicable", "frozen independently mutable model feature"
        elif feature in conditional:
            semantic, status, constraints, reason = "CONDITIONALLY_MUTABLE", "CONDITIONALLY_MUTABLE", "joint feasibility projection required", "frozen conditional attack candidate"
        elif feature in numeric:
            semantic, status, constraints, reason = "NUMERIC", "IMMUTABLE", "not in independent attack mask", "frozen numeric model feature"
        else:
            semantic, status, constraints, reason = "REMOVED", "REMOVE", "none", "not selected in the frozen model feature set"
        semantic_rows.append({"feature": row.feature, "dtype": row.dtype, "semantic_type": semantic,
                              "adversarial_status": status, "min": row.get("min"), "max": row.get("max"),
                              "unique_values": row.cardinality_approx, "constraints": constraints, "reason": reason})
        if status == "REMOVE":
            decision, risk = "REMOVE", "HIGH"
        elif status == "CONDITIONALLY_MUTABLE":
            decision, risk = "REVIEW", "MEDIUM"
        else:
            decision, risk = "KEEP", "LOW"
        leakage_rows.append({"feature": row.feature, "dtype": row.dtype, "cardinality": row.cardinality_approx,
                             "decision": decision, "risk": risk, "reason": reason})
    pd.DataFrame(semantic_rows).to_csv(OUT / f"{dataset}_feature_semantics.csv", index=False)
    pd.DataFrame(leakage_rows).to_csv(OUT / f"{dataset}_leakage_audit.csv", index=False)


if __name__ == "__main__":
    for name in TARGETS:
        generate(name)
