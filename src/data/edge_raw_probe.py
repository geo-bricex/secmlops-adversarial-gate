"""Targeted structural probe for Edge CSV rows containing a known IPv4 token."""
import csv, json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
root=ROOT/'data/edge_iiotset/raw/Edge-IIoTset Cyber Security/Edge-IIoTset dataset'
token='192.168.0.128'; results=[]
for path in root.rglob('*.csv'):
 with path.open(encoding='utf-8',errors='replace',newline='') as f:
  reader=csv.reader(f); header=next(reader); expected=len(header)
  for line,row in enumerate(reader,2):
   if token in row:
    results.append({'file':str(path.relative_to(root)),'line':line,'expected_fields':expected,'parsed_fields':len(row),'arp_hw_size':row[5] if len(row)>5 else None,'row_prefix':row[:10]})
    if len(results)>=20: break
 if len(results)>=20: break
print(json.dumps(results,indent=2))
