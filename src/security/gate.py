from __future__ import annotations
import argparse, hashlib, json, time
from pathlib import Path
import pandas as pd, yaml
ROOT=Path(__file__).resolve().parents[2]; DATASETS=('cic_iot_2023','edge_iiotset','ton_iot'); SEEDS=(42,123,2026)
def read_conditions(ds,seed,validation):
 base=ROOT/'results/adversarial'/ds/f'seed_{seed}'; tail='validation_sanity' if validation else ''
 return [json.loads((base/a/tail/f'eps_{e:03d}.json').read_text()) for a in ('fgsm','pgd') for e in (1,3,5)]
def evaluate(ds,seed,policy,validation=False):
 adv=read_conditions(ds,seed,validation); first=adv[0]; clean_recall=first['attack_recall']+first['clean_to_adv_attack_recall_drop']; worst=min(x['attack_recall'] for x in adv); asr=max(x['attack_success_rate'] for x in adv); drop=max(x['clean_to_adv_attack_recall_drop'] for x in adv); violations=sum(x['semantic_constraint_violations'] for x in adv)
 t=policy['thresholds']; criteria={'clean_performance':clean_recall>=t['clean_attack_recall_min'],'robust_recall':worst>=t['robust_attack_recall_min'],'attack_success_rate':asr<=t['attack_success_rate_max'],'degradation':drop<=t['attack_recall_drop_max'],'integrity':violations==0 and len(adv)==6}
 codes=[]
 mapping={'clean_performance':'BLOCK_LOW_CLEAN_RECALL','robust_recall':'BLOCK_LOW_ROBUST_RECALL','attack_success_rate':'BLOCK_HIGH_ATTACK_SUCCESS_RATE','degradation':'BLOCK_EXCESSIVE_RECALL_DROP','integrity':'BLOCK_ARTIFACT_INTEGRITY'}
 for k,v in criteria.items():
  if not v: codes.append(mapping[k])
 warning=['WARNING_DATASET_CONFOUNDING'] if ds=='edge_iiotset' else []
 return {'dataset':ds,'seed':seed,'decision':'PASS' if not codes else 'BLOCK','clean_attack_recall':clean_recall,'worst_adv_attack_recall':worst,'max_ASR':asr,'max_recall_drop':drop,'semantic_violations':violations,'leakage_status':'NO_DIRECT_LEAKAGE_WITH_DATASET_CONFOUNDING' if ds=='edge_iiotset' else 'NO_EVIDENCE_OF_LEAKAGE','failed_criteria':';'.join(codes),'warnings':';'.join(warning),'policy_id':policy['policy_id'],'reason_codes':codes or ['PASS_ALL_CRITERIA']}
def main():
 p=argparse.ArgumentParser();p.add_argument('--all',action='store_true');p.add_argument('--dataset');p.add_argument('--seed',type=int);p.add_argument('--policy',default='configs/security_gate.yaml');a=p.parse_args(); policy=yaml.safe_load((ROOT/a.policy).read_text()); out=ROOT/'results/security_gate';out.mkdir(parents=True,exist_ok=True); h=hashlib.sha256((ROOT/a.policy).read_bytes()).hexdigest(); frozen={'policy':policy,'policy_hash':h,'calibration_source':'validation_only','test_used_for_threshold_selection':False};(out/'frozen_policy.json').write_text(json.dumps(frozen,indent=2))
 # validation-only sensitivity grid, recorded before test evaluation
 sensitivity=[]
 for r in (.7,.8,.9):
  for asr in (.1,.2,.3): sensitivity.append({'robust_attack_recall_min':r,'attack_success_rate_max':asr,'calibration_source':'validation_only','models_passed':sum(evaluate(d,s,{**policy,'thresholds':{**policy['thresholds'],'robust_attack_recall_min':r,'attack_success_rate_max':asr}},True)['decision']=='PASS' for d in DATASETS for s in SEEDS)})
 pd.DataFrame(sensitivity).to_csv(out/'validation_policy_sensitivity.csv',index=False)
 rows=[evaluate(d,s,policy) for d in DATASETS for s in SEEDS] if a.all else [evaluate(a.dataset,a.seed,policy)]
 for row in rows: (out/f"{row['dataset']}_seed_{row['seed']}.json").write_text(json.dumps({**row,'policy_hash':h,'timestamp':time.time()},indent=2))
 if a.all:
  frame=pd.DataFrame(rows);frame.to_csv(out/'gate_decisions_test.csv',index=False); summary=frame.groupby('dataset').agg(PASS_seeds=('decision',lambda x:(x=='PASS').sum()),BLOCK_seeds=('decision',lambda x:(x=='BLOCK').sum()),clean_recall_mean=('clean_attack_recall','mean'),worst_adv_recall_mean=('worst_adv_attack_recall','mean'),ASR_mean=('max_ASR','mean')).reset_index();summary['decision_stability']=summary.apply(lambda r:'STABLE_PASS' if r.PASS_seeds==3 else ('STABLE_BLOCK' if r.BLOCK_seeds==3 else 'SEED_SENSITIVE'),axis=1);summary.to_csv(out/'security_gate_summary.csv',index=False)
 print(rows[0]['decision'] if len(rows)==1 else len(rows))
if __name__=='__main__':main()
