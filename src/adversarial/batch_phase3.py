"""Resume-safe sequential Phase-3 execution."""
from __future__ import annotations
import csv, json, time
from pathlib import Path
from src.adversarial.run_phase3 import run, SEEDS, BUDGETS, ROOT

def main():
 rows=[]
 for dataset in ('cic_iot_2023','edge_iiotset','ton_iot'):
  for seed in SEEDS:
   for attack in ('fgsm','pgd'):
    for budget in BUDGETS:
     started=time.time()
     try:
      metric=run(dataset,seed,attack,budget,validation=True); status='COMPLETED'; path=str(ROOT/'results/adversarial'/dataset/f'seed_{seed}'/attack/'validation_sanity'/f'eps_{int(budget*100):03d}.json')
     except Exception as exc:
      metric={'error':repr(exc)}; status='FAILED'; path=''
     rows.append({'dataset':dataset,'seed':seed,'attack':attack,'budget':budget,'status':status,'runtime_seconds':time.time()-started,'artifact_path':path})
     if status=='FAILED': raise RuntimeError(metric['error'])
 out=ROOT/'results/adversarial'; out.mkdir(parents=True,exist_ok=True)
 with (out/'phase3_manifest.csv').open('w',newline='',encoding='utf-8') as f: w=csv.DictWriter(f,fieldnames=rows[0]);w.writeheader();w.writerows(rows)
if __name__=='__main__': main()
