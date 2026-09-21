"""Directed, non-training type audit over already materialized Edge splits."""
from __future__ import annotations
import json
from pathlib import Path
import pandas as pd
ROOT=Path(__file__).resolve().parents[2]
def main():
 out=ROOT/'results'/'baseline'/'edge_iiotset'; contract=json.loads((out/'feature_contract.json').read_text())
 frames=[pd.read_parquet(ROOT/'data'/'edge_iiotset'/'processed'/f'{x}.parquet') for x in ('train','validation','test')]; df=pd.concat(frames,ignore_index=True)
 numeric=set(__import__('yaml').safe_load((ROOT/'configs'/'datasets'/'edge_iiotset.yaml').read_text())['feature_policy']['model_numeric']); rows=[]; details={}
 for f in contract['features']:
  s=df[f].astype('string'); parsed=pd.to_numeric(s,errors='coerce'); bad=s[parsed.isna() & s.notna()]
  rows.append({'feature':f,'expected_type':'numeric' if f in numeric else 'categorical','actual_numeric_count':int(parsed.notna().sum()) if f in numeric else None,'actual_non_numeric_count':int(bad.size) if f in numeric else None,'non_numeric_pct':float(100*bad.size/len(df)) if f in numeric else None})
  if len(bad): details[f]={'top_non_numeric_tokens':bad.value_counts().head(20).to_dict(),'ip_like_count':int(bad.str.fullmatch(r'(?:\d{1,3}\.){3}\d{1,3}').sum())}
 report={'rows':len(df),'features':rows,'problem_details':details}; (out/'edge_type_audit.json').write_text(json.dumps(report,indent=2)); print(json.dumps(report,indent=2))
if __name__=='__main__': main()
