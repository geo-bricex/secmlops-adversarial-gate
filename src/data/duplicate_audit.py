"""Duplicate-label audit using materialized Phase 1.5 DuckDB tables only.

It deliberately excludes target, attack-type and provenance fields from the
predictive fingerprint, so it identifies the same predictor vector carrying
conflicting labels without rereading raw CSV files.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import duckdb

from src.data.audit import OUTPUT, ROOT, SPECS, quote


EXCLUDED = {
    "cic_iot_2023": {"source_file", "original_label"},
    "edge_iiotset": {"source_file", "Attack_label", "Attack_type"},
    "ton_iot": {"source_file", "label", "type"},
}


def binary_expression(dataset: str) -> str:
    if dataset == "cic_iot_2023":
        return "CASE WHEN original_label = 'Benign_Final' THEN 0 ELSE 1 END"
    return quote(SPECS[dataset]["binary"])


def audit(dataset: str) -> dict:
    database = ROOT / "data" / dataset / "interim" / "audit.duckdb"
    connection = duckdb.connect(str(database), read_only=True, config={"memory_limit": "6GB", "threads": "6"})
    schema = connection.execute("DESCRIBE audit_source").fetchdf()
    all_columns = schema.column_name.tolist()
    predictor_columns = [column for column in all_columns if column not in EXCLUDED[dataset]]
    if not predictor_columns:
        raise ValueError("No predictor columns remain")
    fingerprint = "hash(" + ",".join(quote(column) for column in predictor_columns) + ")"
    label = binary_expression(dataset)
    # A 64-bit deterministic fingerprint is used only as an efficient group key.
    # The materialized source table remains available for collision confirmation if ever required.
    groups = f"""
        WITH grouped AS (
          SELECT {fingerprint} AS fingerprint, {label} AS binary_label, count(*)::BIGINT AS n
          FROM audit_source
          GROUP BY 1, 2
        ), merged AS (
          SELECT fingerprint, sum(n)::BIGINT AS group_size,
                 count(*)::BIGINT AS label_count, list(binary_label ORDER BY binary_label) AS labels
          FROM grouped GROUP BY 1
        )
        SELECT count(*)::BIGINT AS unique_feature_vectors,
               count(*) FILTER (WHERE group_size > 1)::BIGINT AS duplicate_groups,
               coalesce(sum(group_size) FILTER (WHERE group_size > 1), 0)::BIGINT AS rows_in_duplicate_groups,
               coalesce(avg(group_size) FILTER (WHERE group_size > 1), 0) AS mean_duplicate_group_size,
               coalesce(max(group_size) FILTER (WHERE group_size > 1), 0)::BIGINT AS max_duplicate_group_size,
               count(*) FILTER (WHERE label_count > 1)::BIGINT AS cross_label_duplicate_groups,
               coalesce(sum(group_size) FILTER (WHERE label_count > 1), 0)::BIGINT AS cross_label_duplicate_rows
        FROM merged
    """
    cursor = connection.execute(groups)
    result = dict(zip([description[0] for description in cursor.description], cursor.fetchone()))
    total = connection.execute("SELECT count(*) FROM audit_source").fetchone()[0]
    # Counts each duplicate row only when the duplicate group is label-consistent.
    within = f"""
        WITH grouped AS (
          SELECT {fingerprint} AS fingerprint, {label} AS binary_label, count(*)::BIGINT AS n
          FROM audit_source GROUP BY 1,2
        ), merged AS (
          SELECT fingerprint, sum(n)::BIGINT AS group_size, count(*) AS label_count
          FROM grouped GROUP BY 1
        )
        SELECT coalesce(sum(group_size - 1) FILTER (WHERE group_size > 1 AND label_count = 1), 0)::BIGINT FROM merged
    """
    result.update({
        "dataset": dataset,
        "rows_total": int(total),
        "predictor_columns": predictor_columns,
        "predictor_column_count": len(predictor_columns),
        "fingerprint_method": "DuckDB 64-bit hash over all predictive columns, excluding target/type/provenance metadata",
        "within_label_duplicate_rows": int(connection.execute(within).fetchone()[0]),
        "duplicate_rows": int(total - result["unique_feature_vectors"]),
    })
    label_summary = f"""
        WITH grouped AS (
          SELECT {fingerprint} AS fingerprint, {label} AS binary_label, count(*)::BIGINT AS n
          FROM audit_source GROUP BY 1, 2
        ), merged AS (
          SELECT fingerprint, count(*)::BIGINT AS label_count FROM grouped GROUP BY 1
        )
        SELECT binary_label, sum(n)::BIGINT AS original_rows,
               count(*) FILTER (WHERE label_count = 1)::BIGINT AS deduplicated_rows,
               coalesce(sum(n) FILTER (WHERE label_count > 1), 0)::BIGINT AS conflicting_rows
        FROM grouped JOIN merged USING (fingerprint)
        GROUP BY binary_label ORDER BY binary_label
    """
    result["label_summary"] = [
        {"binary_label": int(row[0]), "original_rows": int(row[1]),
         "deduplicated_rows": int(row[2]), "conflicting_rows": int(row[3])}
        for row in connection.execute(label_summary).fetchall()
    ]
    result["duplicate_rows_pct"] = 100 * result["duplicate_rows"] / total
    result["cross_label_duplicate_pct"] = 100 * result["cross_label_duplicate_rows"] / total
    output = OUTPUT / f"{dataset}_duplicate_audit.json"
    output.write_text(json.dumps(result, indent=2, default=str), encoding="utf-8")
    connection.close()
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", required=True, choices=tuple(SPECS))
    print(json.dumps(audit(parser.parse_args().dataset), indent=2, default=str))
