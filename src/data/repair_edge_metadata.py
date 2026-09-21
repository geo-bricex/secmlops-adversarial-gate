"""Repair metadata after successful Edge parquet writes; does not rematerialize."""
import json
from pathlib import Path
import pandas as pd
ROOT=Path(__file__).resolve().parents[2]; out=ROOT/'data/edge_iiotset/processed'; policy=json.loads((ROOT/'results/data_profile/edge_iiotset_cleaning_policy.json').read_text())
parts={n:pd.read_parquet(out/f'{n}.parquet') for n in ('train','validation','test')}
features=[c for c in parts['train'] if c not in {'binary_target','fingerprint'}]
overlap=sum(len(set(parts[a].fingerprint)&set(parts[b].fingerprint)) for a,b in [('train','validation'),('train','test'),('validation','test')])
if overlap: raise ValueError(f'fingerprint overlap={overlap}')
meta={'canonical_rows':policy['canonical_rows'],'structural_malformed_removed':policy['structural_malformed_removed'],'post_semantic_cleaning_rows':sum(len(x) for x in parts.values()),'experimental_N':sum(len(x) for x in parts.values()),'features':len(features),'fingerprint_overlap':overlap,'strategy':policy['strategy_selected'],'splits':{n:{'N':len(x),'class_counts':{str(k):int(v) for k,v in x.binary_target.value_counts().items()}} for n,x in parts.items()}}
(out/'metadata.json').write_text(json.dumps(meta,indent=2));print(json.dumps(meta,indent=2))
