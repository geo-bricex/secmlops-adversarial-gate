"""Compute exact duplicate-row counts by original class from materialized audit tables."""
from pathlib import Path

import duckdb

from src.data.audit import OUTPUT, ROOT, SPECS, quote


def run(dataset: str) -> None:
    database = ROOT / "data" / dataset / "interim" / "audit.duckdb"
    connection = duckdb.connect(str(database), read_only=True, config={"memory_limit": "6GB", "threads": "6"})
    schema = connection.execute("DESCRIBE audit_source").fetchdf()
    columns = [name for name in schema.column_name.tolist() if name != "source_file"]
    label = "original_label" if dataset == "cic_iot_2023" else SPECS[dataset]["label"]
    grouped = ",".join(quote(name) for name in columns)
    query = f"""
        SELECT {quote(label)} AS label_value, sum(c - 1)::BIGINT AS duplicate_rows
        FROM (SELECT {grouped}, count(*) AS c FROM audit_source GROUP BY {grouped})
        WHERE c > 1 GROUP BY 1 ORDER BY 2 DESC
    """
    connection.execute(query).fetchdf().to_csv(OUTPUT / f"{dataset}_duplicates_by_class.csv", index=False)
    connection.close()


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", required=True, choices=tuple(SPECS))
    run(parser.parse_args().dataset)
