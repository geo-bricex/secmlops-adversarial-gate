"""Materialize frozen Phase-2 populations from Phase-1.5 DuckDB audit tables."""
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path
import duckdb, pandas as pd, yaml
from sklearn.model_selection import train_test_split

ROOT=Path(__file__).resolve().parents[2]
def q(x): return '"'+x.replace('"','""')+'"'
def config(ds): return yaml.safe_load((ROOT/'configs'/'datasets'/f'{ds}.yaml').read_text())
def label_expr(ds): return "CASE WHEN original_label = 'Benign_Final' THEN 0 ELSE 1 END" if ds=='cic_iot_2023' else q(config(ds)['target'])+'::INTEGER'
def fingerprint_cols(ds, cols):
    excluded={'cic_iot_2023':{'source_file','original_label'},'edge_iiotset':{'source_file','Attack_label','Attack_type'},'ton_iot':{'source_file','label','type'}}[ds]
    return [c for c in cols if c not in excluded]
def split_groups(frame, target, group, seed, ratios):
    """Deterministic class-stratified assignment of complete fingerprint groups."""
    out=[]
    for label, part in frame.groupby(target, sort=True):
        sizes=part.groupby(group, sort=False).size().reset_index(name='n')
        sizes['_order']=pd.util.hash_pandas_object(sizes[group].astype(str)+f'/{seed}', index=False).astype('uint64')
        sizes=sizes.sort_values('_order')
        targets=[len(part)*ratios[0],len(part)*ratios[1],len(part)*ratios[2]]; used=[0,0,0]; assigned={}
        for _, row in sizes.iterrows():
            deficits=[targets[i]-used[i] for i in range(3)]
            bucket=max(range(3), key=lambda i:(deficits[i],-i))
            assigned[row[group]]=bucket; used[bucket]+=int(row.n)
        for i in range(3): out.append(part[part[group].map(assigned)==i].assign(_split=i))
    result=pd.concat(out, ignore_index=True)
    return tuple(result[result._split==i].drop(columns='_split').reset_index(drop=True) for i in range(3))
def materialize(ds):
    cfg=config(ds); policy=cfg['feature_policy']; features=policy.get('model_numeric',[])+policy.get('model_binary',[])+policy.get('model_categorical',[])
    out=ROOT/'data'/ds/'processed'; out.mkdir(parents=True,exist_ok=True)
    db=ROOT/'data'/ds/'interim'/'audit.duckdb'
    temp=ROOT/'data'/ds/'interim'/'phase2_duckdb_tmp'; temp.mkdir(parents=True,exist_ok=True)
    con=duckdb.connect(str(db),read_only=True,config={'memory_limit':'6GB','threads':'6','temp_directory':str(temp),'max_temp_directory_size':'100GB'})
    if ds == 'edge_iiotset':
        source = f"read_parquet('{(ROOT/'data/edge_iiotset/interim/canonical/*.parquet').as_posix()}', union_by_name=true)"
        numeric = policy['model_numeric']; invalid = ' OR '.join(f"try_cast({q(x)} AS DOUBLE) IS NULL AND {q(x)} IS NOT NULL" for x in numeric)
        select = ', '.join(q(c) for c in features); fp = 'hash('+select+')'
        base = f"SELECT {select}, \"Attack_label\"::INTEGER AS binary_target, {fp} AS fingerprint FROM {source} WHERE NOT ({invalid})"
        cleaned = base
        # Edge uses its canonical source and a fresh fingerprint; never audit_source.
    else:
        cleaned = None
    if ds != 'edge_iiotset':
     cols=con.execute('DESCRIBE audit_source').fetchdf().column_name.tolist(); fpcols=fingerprint_cols(ds,cols)
     fp='hash('+','.join(q(c) for c in fpcols)+')'; y=label_expr(ds); select=', '.join(q(c) for c in features)
     base=f"SELECT {select}, {y} AS binary_target, {fp} AS fingerprint FROM audit_source"
    # Every fingerprint is label-consistent for Edge/ToN; CIC conflicts are explicitly excluded.
    if ds != 'edge_iiotset': cleaned=f"WITH base AS ({base}), g AS (SELECT fingerprint, count(DISTINCT binary_target) labels FROM base GROUP BY 1) SELECT base.* FROM base JOIN g USING(fingerprint) WHERE labels=1"
    if cfg['duplicate_policy']=='deduplicate_then_stratified':
        # All rows in a fingerprint share every predictive field.  Aggregating a
        # representative avoids an expensive window over tens of millions rows.
        representative=', '.join(f'any_value({q(c)}) AS {q(c)}' for c in features)
        cleaned=f"WITH base AS ({base}) SELECT {representative}, min(binary_target) AS binary_target, fingerprint FROM base GROUP BY fingerprint HAVING count(DISTINCT binary_target)=1"
    # sample whole groups for Edge, deterministic rows for deduplicated datasets
    n=cfg.get('sample_max_rows');
    if n:
        audit=json.loads((ROOT/'results'/'data_profile'/f'{ds}_duplicate_audit.json').read_text())
        counts=[(x['binary_label'],x['deduplicated_rows']) for x in audit['label_summary']] if cfg['duplicate_policy']=='deduplicate_then_stratified' else con.execute(f"SELECT binary_target, count(*) FROM ({cleaned}) GROUP BY 1 ORDER BY 1").fetchall()
        total=sum(x[1] for x in counts); limits={int(k):max(1,round(n*v/total)) for k,v in counts}; limits[max(limits)]+=n-sum(limits.values())
        if cfg['duplicate_policy']=='duplicate_aware_stratified':
            # Deterministic quota-aware greedy packing.  Unlike a cumulative
            # prefix, it can accept later small groups after a large group does
            # not fit; no fingerprint is ever split.
            chosen=f"WITH c AS ({cleaned}), groups AS (SELECT fingerprint,binary_target,count(*) n FROM c GROUP BY 1,2), ranked AS (SELECT *, row_number() OVER(PARTITION BY binary_target ORDER BY hash(fingerprint,42)) rn FROM groups), packed AS (SELECT *, sum(n) OVER(PARTITION BY binary_target ORDER BY n, rn ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) cum_small FROM ranked) SELECT c.* FROM c JOIN packed USING(fingerprint,binary_target) WHERE cum_small <= CASE binary_target " + ' '.join(f"WHEN {k} THEN {v}" for k,v in limits.items())+' END'
        else:
            chosen=f"WITH c AS ({cleaned}), ranked AS (SELECT *,row_number() OVER(PARTITION BY binary_target ORDER BY hash(fingerprint,42)) rn FROM c) SELECT * EXCLUDE(rn) FROM ranked WHERE rn <= CASE binary_target " + ' '.join(f"WHEN {k} THEN {v}" for k,v in limits.items())+' END'
    else: chosen=cleaned
    selected=con.execute(chosen).fetchdf(); con.close()
    # Preserve numerical values; conversion happens train-only in preprocessing.
    ratios=cfg['split']; parts=split_groups(selected,'binary_target','fingerprint',ratios['seed'],[ratios['train'],ratios['validation'],ratios['test']])
    for name, frame in zip(('train','validation','test'),parts): frame.to_parquet(out/f'{name}.parquet',index=False)
    contract={'dataset':ds,'features':features,'feature_count':len(features),'removed':policy['remove'],'target':cfg['target'],'split_strategy':cfg['duplicate_policy'],'seed':ratios['seed']}
    contract['config_id']=hashlib.sha256(json.dumps(contract,sort_keys=True).encode()).hexdigest()
    (ROOT/'results'/'baseline'/ds).mkdir(parents=True,exist_ok=True)
    (ROOT/'results'/'baseline'/ds/'feature_contract.json').write_text(json.dumps(contract,indent=2))
    if ds == 'edge_iiotset':
        policy_report=json.loads((ROOT/'results/data_profile/edge_iiotset_cleaning_policy.json').read_text())
        metadata={'canonical_rows':policy_report['canonical_rows'],'structural_malformed_removed':policy_report['structural_malformed_removed'],'original_N':policy_report['canonical_rows'],'post_cleaning_N':len(selected),'experimental_N':len(selected),'features':len(features),'seed':ratios['seed'],'strategy':cfg['duplicate_policy'],'canonical_source':'interim/canonical'}
    else:
        metadata={'original_N':int(json.load(open(ROOT/'results'/'data_profile'/f'{ds}_duplicate_audit.json'))['rows_total']),'post_cleaning_N':len(selected),'experimental_N':len(selected),'features':len(features),'seed':ratios['seed'],'strategy':cfg['duplicate_policy']}
    metadata['splits']={n:{'N':len(f),'class_counts':{str(k):int(v) for k,v in f.binary_target.value_counts().items()}} for n,f in zip(('train','validation','test'),parts)}
    (out/'metadata.json').write_text(json.dumps(metadata,indent=2)); return metadata
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--dataset',required=True); print(json.dumps(materialize(p.parse_args().dataset),indent=2))
