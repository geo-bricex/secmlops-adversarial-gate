"""Build Edge canonical parquet from explicitly validated CSV records."""
from __future__ import annotations
import csv, hashlib, json, sys
from collections import Counter
from pathlib import Path
import pandas as pd

ROOT=Path(__file__).resolve().parents[2]
RAW=ROOT/'data/edge_iiotset/raw/Edge-IIoTset Cyber Security/Edge-IIoTset dataset'
OUT=ROOT/'data/edge_iiotset/interim/canonical'
REPORT=ROOT/'results/data_profile'
def main():
 csv.field_size_limit(sys.maxsize)
 OUT.mkdir(parents=True,exist_ok=True); REPORT.mkdir(parents=True,exist_ok=True); reports=[]; canonical=None
 for index,path in enumerate(sorted(RAW.rglob('*.csv'))):
  with path.open(encoding='utf-8',errors='strict',newline='') as f:
   r=csv.reader(f,delimiter=',',quotechar='"',escapechar='"'); header=next(r); expected=len(header)
   canonical=canonical or header; valid=invalid=0; observed=Counter(); rows=[]
   for row_no,row in enumerate(r,2):
    observed[len(row)]+=1
    if len(row)!=expected: invalid+=1; continue
    valid+=1; rows.append(dict(zip(header,row)))
    if len(rows)>=100000:
     pd.DataFrame(rows).reindex(columns=canonical).assign(source_file=str(path.relative_to(RAW))).to_parquet(OUT/f'part-{index}-{valid}.parquet',index=False); rows=[]
   if rows: pd.DataFrame(rows).reindex(columns=canonical).assign(source_file=str(path.relative_to(RAW))).to_parquet(OUT/f'part-{index}-{valid}.parquet',index=False)
  reports.append({'file':str(path.relative_to(RAW)),'rows_total':valid+invalid,'rows_valid':valid,'rows_invalid':invalid,'expected_columns':expected,'header_hash':hashlib.sha256(','.join(header).encode()).hexdigest(),'observed_column_counts':dict(observed),'header_matches_canonical':header==canonical})
 pd.DataFrame(reports).to_csv(REPORT/'edge_iiotset_parser_validation.csv',index=False)
 summary={'parser':'python csv.reader delimiter=, quotechar=\" escapechar=\"','files':len(reports),'rows_total':sum(x['rows_total'] for x in reports),'rows_valid':sum(x['rows_valid'] for x in reports),'rows_invalid':sum(x['rows_invalid'] for x in reports),'header_schema_groups':len(set(x['header_hash'] for x in reports))}
 summary['malformed_pct']=100*summary['rows_invalid']/summary['rows_total']; (REPORT/'edge_iiotset_parser_audit.json').write_text(json.dumps(summary,indent=2)); print(json.dumps(summary,indent=2))
if __name__=='__main__': main()
