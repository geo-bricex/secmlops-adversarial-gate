"""Record the frozen residual semantic exclusion after tcp.dstport removal."""
from __future__ import annotations
import json
from pathlib import Path
import duckdb
import yaml

ROOT = Path(__file__).resolve().parents[2]

def quote(name: str) -> str:
    return '"' + name.replace('"', '""') + '"'

def main() -> None:
    cfg = yaml.safe_load((ROOT / 'configs/datasets/edge_iiotset.yaml').read_text())
    numeric = cfg['feature_policy']['model_numeric']
    source = (ROOT / 'data/edge_iiotset/interim/canonical/*.parquet').as_posix()
    invalid = ' OR '.join(f'try_cast({quote(feature)} AS DOUBLE) IS NULL AND {quote(feature)} IS NOT NULL' for feature in numeric)
    con = duckdb.connect()
    table = f"read_parquet('{source}', union_by_name=true)"
    total, residual = con.execute(f"SELECT count(*), count(*) FILTER (WHERE {invalid}) FROM {table}").fetchone()
    classes = con.execute(f"SELECT Attack_label::INTEGER, count(*), count(*) FILTER (WHERE {invalid}) FROM {table} GROUP BY 1 ORDER BY 1").fetchall()
    removal_rates = {label: removed / count * 100 for label, count, removed in classes}
    max_attack_loss = con.execute(f"SELECT max(removed::DOUBLE / total * 100) FROM (SELECT Attack_type, count(*) total, count(*) FILTER (WHERE {invalid}) removed FROM {table} GROUP BY 1) WHERE total > 0").fetchone()[0]
    binary_shift = abs(removal_rates[0] - removal_rates[1])
    report = {'post_feature_removal_rows': total, 'semantic_rows_removed': residual, 'final_clean_universe_rows': total - residual, 'residual_semantic_pct': residual / total * 100, 'residual_binary_shift_pp': binary_shift, 'residual_max_attack_type_removed_pct': max_attack_loss, 'threshold_global_pass': residual / total <= .01, 'threshold_binary_balance_pass': binary_shift < .5, 'threshold_attack_type_pass': max_attack_loss < 10, 'nonnumeric_numeric_features_after_exclusion': 0}
    policy_path = ROOT / 'results/data_profile/edge_iiotset_cleaning_policy.json'
    policy = json.loads(policy_path.read_text())
    policy.update(report)
    policy['initial_features'] = 23
    policy_path.write_text(json.dumps(policy, indent=2), encoding='utf-8')
    (ROOT / 'results/data_profile/edge_iiotset_semantic_residual_audit.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps(report, indent=2))

if __name__ == '__main__':
    main()
