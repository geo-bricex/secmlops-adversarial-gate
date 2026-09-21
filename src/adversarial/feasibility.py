"""Frozen, conservative Phase-3 attackability contract."""
from __future__ import annotations
import csv, json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CONTRACT = {
    'cic_iot_2023': {'Time_To_Live': ('MUTABLE_DISCRETE', 'round_to_integer_and_train_bounds', 'integer TTL operationally controllable by packet construction')},
    'edge_iiotset': {'udp.time_delta': ('CONDITIONALLY_MUTABLE_PROJECTABLE', 'clip_to_train_bounds', 'inter-packet timing is traffic-influenceable; no retained dependency is altered')},
    'ton_iot': {'duration': ('CONDITIONALLY_MUTABLE_PROJECTABLE', 'clip_to_train_bounds', 'flow duration is traffic-influenceable and directly projectable to nonnegative train domain')},
}

def write_audit(dataset: str, feature_names: list[str], numeric: list[str], train) -> dict:
    attackable = CONTRACT[dataset]
    rows=[]
    for feature in feature_names:
        status, rule, why = attackable.get(feature, ('IMMUTABLE', 'preserve_exactly', 'not independently attackable under conservative projected model'))
        is_num = feature in numeric
        rows.append({'raw_feature':feature, 'semantic_type':'numeric' if is_num else 'categorical', 'predictive_status':'PREDICTOR', 'adversarial_status':status, 'discrete': feature == 'Time_To_Live', 'projection_rule':rule, 'lower_bound': float(train[feature].min()) if is_num else '', 'upper_bound': float(train[feature].max()) if is_num else '', 'step':1 if feature == 'Time_To_Live' else '', 'dependency_group':'none', 'justification':why})
    path=ROOT/'results'/'adversarial'/dataset; path.mkdir(parents=True,exist_ok=True)
    with (path/'feature_attack_map.csv').open('w',newline='',encoding='utf-8') as f: csv.DictWriter(f,fieldnames=rows[0].keys()).writeheader(); csv.DictWriter(f,fieldnames=rows[0].keys()).writerows(rows)
    counts={'continuous_mutable':sum(r['adversarial_status']=='MUTABLE_CONTINUOUS' for r in rows),'discrete_mutable':sum(r['adversarial_status']=='MUTABLE_DISCRETE' for r in rows),'conditionally_mutable_projectable':sum(r['adversarial_status']=='CONDITIONALLY_MUTABLE_PROJECTABLE' for r in rows)}
    report={'dataset':dataset,'total_predictive_features':len(feature_names),**counts,'immutable':len(feature_names)-sum(counts.values()),'attackable_total':sum(counts.values()),'attackable_features':list(attackable),'projection_rules':{k:v[1] for k,v in attackable.items()},'threat_model':'PROJECTED_CONSTRAINED_TABULAR_EVASION'}
    (path/'feasibility_audit.json').write_text(json.dumps(report,indent=2)); return report
