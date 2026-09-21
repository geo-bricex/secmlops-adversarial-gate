from pathlib import Path
import duckdb,json,yaml
ROOT=Path(__file__).resolve().parents[2]; cfg=yaml.safe_load((ROOT/'configs/datasets/edge_iiotset.yaml').read_text()); nums=cfg['feature_policy']['model_numeric']; glob=(ROOT/'data/edge_iiotset/interim/canonical/*.parquet').as_posix(); q=lambda x:'"'+x+'"'; c=duckdb.connect(); c.execute("SET memory_limit='8GB'")
counts={}
for f in nums: counts[f]=c.execute(f"SELECT count(*) FROM read_parquet('{glob}',union_by_name=true) WHERE try_cast({q(f)} AS DOUBLE) IS NULL AND {q(f)} IS NOT NULL").fetchone()[0]
remaining=nums.copy(); removed=[]
while True:
 cond=' OR '.join(f"try_cast({q(x)} AS DOUBLE) IS NULL AND {q(x)} IS NOT NULL" for x in remaining)
 n=c.execute(f"SELECT count(*) FROM read_parquet('{glob}',union_by_name=true) WHERE {cond}").fetchone()[0] if cond else 0
 if n==0: break
 candidates=[]
 for f in remaining:
  bad=f"try_cast({q(f)} AS DOUBLE) IS NULL AND {q(f)} IS NOT NULL"; others=[x for x in remaining if x!=f]; other=' OR '.join(f"try_cast({q(x)} AS DOUBLE) IS NULL AND {q(x)} IS NOT NULL" for x in others)
  residual=c.execute(f"SELECT count(*) FROM read_parquet('{glob}',union_by_name=true) WHERE {other}").fetchone()[0] if other else 0; candidates.append((residual,f))
 best=min(candidates); removed.append(best[1]); remaining.remove(best[1])
 # stop at first dominant removal; user allows hybrid if residual meets row criteria
 break
out={'per_feature_nonnumeric':counts,'dominant_feature':removed,'residual_after_dominant':n if not removed else best[0],'remaining_numeric':remaining}; (ROOT/'results/data_profile/edge_iiotset_feature_removal_analysis.json').write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
