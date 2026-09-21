"""Read-only, scalable audit of the downloaded datasets.

Raw files are opened only for reading. Reports are written below results/data_profile.
DuckDB performs out-of-core aggregation; exact counts are distinguished from approximate
cardinality and quantiles in the emitted metadata.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
import time
from pathlib import Path
from typing import Iterable

import duckdb
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT / "results" / "data_profile"
SPECS = {
    "cic_iot_2023": {
        "root": ROOT / "data/cic_iot_2023/raw/CIC_IOT_Dataset2023/CSV",
        "selected": "**/*.csv", "label": None, "binary": None,
    },
    "edge_iiotset": {
        "root": ROOT / "data/edge_iiotset/raw/Edge-IIoTset Cyber Security/Edge-IIoTset dataset",
        "selected": "**/*.csv", "label": "Attack_type", "binary": "Attack_label",
    },
    "ton_iot": {
        "root": ROOT / "data/ton_iot/raw/TON_IoT Network Dataset",
        "selected": "**/*.csv", "label": "type", "binary": "label",
    },
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while block := stream.read(8 * 1024 * 1024):
            digest.update(block)
    return digest.hexdigest()


def sha256_and_rows(path: Path) -> tuple[str, int]:
    digest, newlines = hashlib.sha256(), 0
    with path.open("rb") as stream:
        while block := stream.read(8 * 1024 * 1024):
            digest.update(block)
            newlines += block.count(b"\n")
    return digest.hexdigest(), max(0, newlines - 1)


def line_count(path: Path) -> int:
    count = 0
    with path.open("rb") as stream:
        while block := stream.read(8 * 1024 * 1024):
            count += block.count(b"\n")
    return max(0, count - 1)


def detect_encoding(path: Path) -> str:
    with path.open("rb") as stream:
        prefix = stream.read(4)
    if prefix.startswith(b"\xef\xbb\xbf"):
        return "utf-8-sig"
    try:
        path.open(encoding="utf-8").read(65536)
        return "utf-8"
    except UnicodeDecodeError:
        return "latin-1"


def manifest(dataset: str, root: Path) -> pd.DataFrame:
    output_path = OUTPUT / f"{dataset}_manifest.csv"
    if output_path.exists():
        cached = pd.read_csv(output_path)
        current = {p.relative_to(root).as_posix(): p.stat().st_size for p in root.rglob("*") if p.is_file()}
        recorded = dict(zip(cached.relative_path, cached.size_bytes))
        if current == recorded:
            return cached
    rows = []
    for path in sorted(p for p in root.rglob("*") if p.is_file()):
        started = time.perf_counter()
        encoding = detect_encoding(path) if path.suffix.lower() in {".csv", ".txt"} else ""
        columns: list[str] = []
        nrows = None
        if path.suffix.lower() == ".csv":
            with path.open(encoding=encoding, newline="") as stream:
                columns = next(csv.reader(stream))
            checksum, nrows = sha256_and_rows(path)
        else:
            checksum = sha256(path)
        rows.append({
            "relative_path": path.relative_to(root).as_posix(), "file_name": path.name,
            "extension": path.suffix.lower(), "size_bytes": path.stat().st_size,
            "size_mib": round(path.stat().st_size / 2**20, 6), "size_gib": round(path.stat().st_size / 2**30, 6),
            "sha256": checksum, "file_type": "CSV" if path.suffix.lower() == ".csv" else path.suffix.lower().lstrip(".").upper(),
            "rows": nrows, "columns_count": len(columns) if columns else None,
            "columns": json.dumps(columns, ensure_ascii=False), "encoding": encoding,
            "inspection_seconds": round(time.perf_counter() - started, 6),
        })
    frame = pd.DataFrame(rows)
    frame.to_csv(output_path, index=False)
    return frame


def quote(identifier: str) -> str:
    return '"' + identifier.replace('"', '""') + '"'


def sql_list(paths: Iterable[Path]) -> str:
    return "[" + ",".join("'" + p.as_posix().replace("'", "''") + "'" for p in paths) + "]"


def relation_sql(dataset: str, paths: list[Path]) -> str:
    text_mode = ", all_varchar=true" if dataset == "edge_iiotset" else ""
    reader = f"read_csv({sql_list(paths)}, header=true, union_by_name=true, filename=true, sample_size=200000, null_padding=true, ignore_errors=false{text_mode})"
    if dataset == "cic_iot_2023":
        # Directory is the only label source in the distributed CSV collection.
        return f"SELECT * EXCLUDE(filename), filename AS source_file, regexp_extract(filename, '[\\\\/]([^\\\\/]+)[\\\\/][^\\\\/]+$', 1) AS original_label FROM {reader}"
    return f"SELECT * EXCLUDE(filename), filename AS source_file FROM {reader}"


def scalar(connection: duckdb.DuckDBPyConnection, query: str):
    return connection.execute(query).fetchone()[0]


def audit(dataset: str) -> dict:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    spec = SPECS[dataset]
    raw_manifest = manifest(dataset, spec["root"])
    selected = sorted(spec["root"].glob(spec["selected"]))
    if not selected:
        raise FileNotFoundError(f"No selected CSV files for {dataset}")
    database = ROOT / "data" / dataset / "interim" / "audit.duckdb"
    connection = duckdb.connect(str(database))
    connection.execute("SET threads TO 10")
    connection.execute("SET memory_limit='12GB'")
    connection.execute(f"SET temp_directory='{(ROOT / 'data' / dataset / 'interim' / 'duckdb_tmp').as_posix()}'")
    source = relation_sql(dataset, selected)
    existing = scalar(connection, "SELECT count(*) FROM information_schema.tables WHERE table_name='audit_source'")
    if not existing:
        connection.execute(f"CREATE TABLE audit_source AS {source}")
    schema = connection.execute("DESCRIBE audit_source").fetchdf()
    columns = schema.column_name.tolist()
    types = dict(zip(schema.column_name, schema.column_type))
    n = scalar(connection, "SELECT count(*) FROM audit_source")
    label = "original_label" if dataset == "cic_iot_2023" else spec["label"]
    binary_expr = "CASE WHEN original_label='Benign_Final' THEN 0 ELSE 1 END" if dataset == "cic_iot_2023" else quote(spec["binary"])
    labels = connection.execute(f"SELECT {quote(label)} AS label_value, count(*) AS row_count FROM audit_source GROUP BY 1 ORDER BY 2 DESC").fetchdf()
    binary = connection.execute(f"SELECT {binary_expr} AS binary_value, count(*) AS row_count FROM audit_source GROUP BY 1 ORDER BY 1").fetchdf()

    feature_rows = []
    numeric_tokens = ("TINYINT", "SMALLINT", "INTEGER", "BIGINT", "HUGEINT", "FLOAT", "DOUBLE", "DECIMAL")
    edge_text = {"frame.time", "ip.src_host", "ip.dst_host", "arp.dst.proto_ipv4", "arp.src.proto_ipv4",
                 "http.file_data", "http.request.uri.query", "http.request.method", "http.referer", "http.request.full_uri",
                 "http.request.version", "tcp.checksum", "tcp.flags", "tcp.options", "tcp.payload", "dns.qry.name",
                 "mqtt.msg_decoded_as", "mqtt.msg", "mqtt.protoname", "mqtt.topic", "Attack_type", "source_file"}
    expressions = []
    numeric_names = []
    for index, name in enumerate(columns):
        qn, dtype = quote(name), types[name]
        expressions.extend([f"count(*) FILTER (WHERE {qn} IS NULL) AS m{index}", f"approx_count_distinct({qn}) AS c{index}"])
        is_numeric = dtype.startswith(numeric_tokens) or (dataset == "edge_iiotset" and name not in edge_text)
        if is_numeric:
            numeric_names.append(name)
            numeric_value = f"try_cast({qn} AS DOUBLE)" if dataset == "edge_iiotset" else qn
            finite = f"CASE WHEN isfinite({numeric_value}) THEN {numeric_value} END"
            expressions.extend([f"min({finite}) AS lo{index}", f"max({finite}) AS hi{index}", f"avg({finite}) AS av{index}",
                                f"stddev_samp({finite}) AS sd{index}", f"count(*) FILTER (WHERE isinf({numeric_value}) AND {numeric_value}>0) AS pi{index}",
                                f"count(*) FILTER (WHERE isinf({numeric_value}) AND {numeric_value}<0) AS ni{index}",
                                f"approx_quantile({finite}, [0.01,0.05,0.25,0.5,0.75,0.95,0.99]) AS pq{index}"])
    aggregates = connection.execute("SELECT " + ",".join(expressions) + " FROM audit_source").fetchdf().iloc[0]
    for index, name in enumerate(columns):
        dtype = types[name]
        missing = int(aggregates[f"m{index}"])
        row = {"feature": name, "dtype": dtype, "missing": missing, "missing_pct": 100 * missing / n if n else 0,
               "cardinality_approx": int(aggregates[f"c{index}"])}
        if name in numeric_names:
            row["analysis_dtype"] = "DOUBLE_INFERRED" if dataset == "edge_iiotset" else dtype
            row.update({"min": aggregates[f"lo{index}"], "max": aggregates[f"hi{index}"], "mean": aggregates[f"av{index}"],
                        "std": aggregates[f"sd{index}"], "positive_inf": int(aggregates[f"pi{index}"]),
                        "negative_inf": int(aggregates[f"ni{index}"]), "percentiles_approx": aggregates[f"pq{index}"]})
        feature_rows.append(row)
    feature_stats = pd.DataFrame(feature_rows)
    feature_stats.to_csv(OUTPUT / f"{dataset}_feature_stats.csv", index=False)

    group_cols = [quote(c) for c in columns if c != "source_file"]
    duplicates = scalar(connection, f"SELECT coalesce(sum(c-1),0) FROM (SELECT count(*) c FROM audit_source GROUP BY {','.join(group_cols)} HAVING count(*)>1)")
    within = connection.execute(f"SELECT source_file, coalesce(sum(c-1),0) duplicate_rows FROM (SELECT source_file, count(*) c FROM audit_source GROUP BY source_file,{','.join(group_cols)} HAVING count(*)>1) GROUP BY source_file").fetchdf()
    within.to_csv(OUTPUT / f"{dataset}_duplicates_by_source.csv", index=False)

    constants = feature_stats.loc[feature_stats.cardinality_approx <= 1, "feature"].tolist()
    near_constants = []
    for name in feature_stats.loc[feature_stats.cardinality_approx <= 100, "feature"]:
        top = scalar(connection, f"SELECT max(c) FROM (SELECT count(*) c FROM audit_source GROUP BY {quote(name)})")
        if top and top / n >= .995 and name not in constants:
            near_constants.append(name)
    profile = {
        "dataset": dataset, "selected_files": [p.relative_to(spec["root"]).as_posix() for p in selected],
        "files_selected": len(selected), "total_size_bytes": int(sum(p.stat().st_size for p in selected)),
        "rows": int(n), "columns": len(columns), "column_names": columns, "dtypes": types,
        "original_label_column": label, "label_distribution": labels.to_dict("records"),
        "binary_mapping": {"normal_or_benign": 0, "attack": 1}, "binary_distribution": binary.to_dict("records"),
        "duplicate_rows_exact_excluding_source_file": int(duplicates), "duplicate_pct": 100 * duplicates / n if n else 0,
        "constant_features_approx_cardinality": constants, "near_constant_threshold": .995,
        "near_constant_features": near_constants,
        "statistics_note": "Rows, labels, missing, infinities and duplicates are exact. Cardinalities and quantiles use DuckDB approximate algorithms; see feature_stats CSV.",
        "manifest_files": int(len(raw_manifest)),
    }
    (OUTPUT / f"{dataset}_profile.json").write_text(json.dumps(profile, indent=2, default=str), encoding="utf-8")
    connection.close()
    return profile


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", required=True, choices=tuple(SPECS))
    args = parser.parse_args()
    print(json.dumps(audit(args.dataset), indent=2, default=str))
