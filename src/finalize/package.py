from __future__ import annotations
import json
from pathlib import Path
import pandas as pd
ROOT=Path(__file__).resolve().parents[2]
def main():
 final=ROOT/'results/final';final.mkdir(parents=True,exist_ok=True)
 clean=pd.read_csv(ROOT/'results/baseline/phase2_runs.csv'); adv=pd.read_csv(ROOT/'results/adversarial/adversarial_results_long.csv'); gate=pd.read_csv(ROOT/'results/security_gate/gate_decisions_test.csv')
 clean.to_csv(final/'master_clean_results.csv',index=False)
 clean.groupby('dataset').agg(['mean','std']).to_csv(final/'table_clean_baselines.csv')
 adv.groupby(['dataset','attack','budget']).agg(['mean','std']).to_csv(final/'table_adversarial_results.csv')
 worst=adv.sort_values('attack_recall').groupby(['dataset','seed']).first().reset_index();worst['robustness_gap']=worst['attack_recall']+worst['clean_to_adv_attack_recall_drop']-worst['attack_recall'];worst.to_csv(final/'table_worst_case_robustness.csv',index=False)
 gate.merge(worst[['dataset','seed','robustness_gap']],on=['dataset','seed']).to_csv(final/'table_security_gate.csv',index=False)
 gate['clean_only_decision']=gate.clean_attack_recall.ge(.95).map({True:'PASS',False:'BLOCK'});gate['decision_changed']=gate.clean_only_decision.ne(gate.decision);gate.to_csv(final/'table_gate_value_added.csv',index=False);worst[['dataset','seed','robustness_gap']].to_csv(final/'table_robustness_gap.csv',index=False)
 adv.groupby(['dataset','attack','budget'])[['attack_recall','attack_success_rate','clean_to_adv_attack_recall_drop','runtime_seconds']].mean().reset_index().to_csv(final/'budget_response_analysis.csv',index=False)
 adv.groupby('dataset')[['runtime_seconds']].agg(['mean','std']).to_csv(final/'table_operational_cost.csv')
 clean.merge(gate[['dataset','seed','decision']],on=['dataset','seed']).to_csv(final/'master_results.csv',index=False)
if __name__=='__main__':main()
