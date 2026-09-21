"""Re-audit only Edge from canonical parquet, never audit_source."""
from pathlib import Path
import duckdb,json,yaml
ROOT=Path(__file__).resolve().parents[2]
cfg=yaml.safe_load((ROOT/'configs/datasets/edge_iiotset.yaml').read_text()); p=cfg['feature_policy']; features=p['model_numeric']+p['model_categorical']; glob=(ROOT/'data/edge_iiotset/interim/canonical/*.parquet').as_posix()
c=duckdb.connect(); c.execute("SET memory_limit='8GB'"); q=lambda x:'"'+x+'"'; cols=','.join(q(x) for x in features); fp='hash('+cols+')'
base=f"SELECT {cols}, \"Attack_label\"::INTEGER y, {fp} fp FROM read_parquet('{glob}', union_by_name=true)"
summary=c.execute(f"WITH b AS ({base}), g AS (SELECT fp,count(*) n,count(distinct y) labels FROM b GROUP BY 1) SELECT count(*),count(distinct fp),count(*)-count(distinct fp),count(*) FILTER(where n>1),coalesce(sum(n-1) filter(where n>1),0),count(*) filter(where labels>1),coalesce(sum(n) filter(where labels>1),0) FROM b join g using(fp)").fetchone()
checks=[]
for f in p['model_numeric']:
 checks.append(c.execute(f"SELECT '{f}',count(*),count(*) filter(where try_cast({q(f)} as double) is null and {q(f)} is not null),min(try_cast({q(f)} as double)),max(try_cast({q(f)} as double)) FROM read_parquet('{glob}',union_by_name=true)").fetchone())
out={'source':'canonical parquet','total_valid_rows':summary[0],'unique_feature_vectors':summary[1],'duplicate_rows':summary[2],'duplicate_groups':summary[3],'duplicate_rows_count':summary[4],'cross_label_duplicate_groups':summary[5],'cross_label_duplicate_rows':summary[6],'feature_checks':[dict(zip(['feature','rows','nonnumeric','min','max'],r)) for r in checks]}; out['duplicate_pct']=100*out['duplicate_rows']/out['total_valid_rows']; (ROOT/'results/data_profile/edge_iiotset_duplicate_audit.json').write_text(json.dumps(out,indent=2,default=str)); print(json.dumps(out,indent=2,default=str))
