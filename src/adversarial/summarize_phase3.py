from __future__ import annotations
import json
from pathlib import Path
import pandas as pd
ROOT=Path(__file__).resolve().parents[2]
def main():
 rows=[]
 for ds in ('cic_iot_2023','edge_iiotset','ton_iot'):
  for seed in (42,123,2026):
   for attack in ('fgsm','pgd'):
    for budget in (.01,.03,.05): rows.append(json.loads((ROOT/'results/adversarial'/ds/f'seed_{seed}'/attack/f'eps_{int(budget*100):03d}.json').read_text()))
 out=ROOT/'results/adversarial'; frame=pd.DataFrame(rows); frame.to_csv(out/'adversarial_results_long.csv',index=False)
 cols=['attack_recall','attack_success_rate','f1','mcc','accuracy','runtime_seconds','clean_to_adv_attack_recall_drop','clean_to_adv_F1_drop']
 summary=frame.groupby(['dataset','attack','budget'])[cols].agg(['mean','std','min','max']); summary.columns=['_'.join(x) for x in summary.columns]; summary.reset_index().to_csv(out/'adversarial_summary.csv',index=False)
if __name__=='__main__': main()
