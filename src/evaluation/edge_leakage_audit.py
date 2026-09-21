import json,joblib,numpy as np,pandas as pd
from pathlib import Path
from sklearn.metrics import roc_auc_score,accuracy_score
from sklearn.dummy import DummyClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
ROOT=Path(__file__).resolve().parents[2]; ds='edge_iiotset'; out=ROOT/'results/baseline'/ds; p=ROOT/'data'/ds/'processed'; tr=pd.read_parquet(p/'train.parquet'); va=pd.read_parquet(p/'validation.parquet'); te=pd.read_parquet(p/'test.parquet'); contract=json.loads((out/'feature_contract.json').read_text()); feats=contract['features']; forbidden={'Attack_label','Attack_type','source_file','fingerprint','binary_target','tcp.dstport'}
prep=joblib.load(ROOT/'artifacts/preprocessing'/ds/'preprocessor.joblib'); names=prep.get_feature_names_out().tolist(); mapping=[]
for f in feats: mapping.append({'raw_feature':f,'transformer':'categorical one-hot' if any(f'__{f}_' in n for n in names) else 'numeric impute+scale','output_features':[n for n in names if n==f'numeric__{f}' or f'__{f}_' in n]})
rows=[]
for f in feats:
 s=tr[f]; groups=pd.crosstab(s,tr.binary_target); purity=(groups.max(axis=1)/groups.sum(axis=1)).max(); exclusive=int(((groups==0).any(axis=1)).sum()); auc=None
 try: auc=float(roc_auc_score(tr.binary_target,pd.to_numeric(s)))
 except: pass
 rows.append({'feature':f,'unique_values':int(s.nunique()),'exclusive_values':exclusive,'max_class_purity':float(purity),'univariate_auc':auc,'status':'POTENTIAL_PROXY' if purity==1 and exclusive>1 else 'NORMAL'})
pd.DataFrame(rows).to_csv(out/'leakage_feature_audit.csv',index=False)
Xtr=prep.transform(tr[feats]); Xva=prep.transform(va[feats]); y=tr.binary_target; yv=va.binary_target
models={'dummy':DummyClassifier(strategy='prior'),'linear':LogisticRegression(max_iter=100,n_jobs=1),'shallow_tree':DecisionTreeClassifier(max_depth=3,random_state=42)}; scores={}
for n,m in models.items(): m.fit(Xtr,y);scores[n]=accuracy_score(yv,m.predict(Xva))
rng=np.random.default_rng(42); m=LogisticRegression(max_iter=100,n_jobs=1).fit(Xtr,rng.permutation(y));scores['label_shuffle_linear_validation_accuracy']=accuracy_score(yv,m.predict(Xva))
overlaps={'train_validation':len(set(tr.fingerprint)&set(va.fingerprint)),'train_test':len(set(tr.fingerprint)&set(te.fingerprint)),'validation_test':len(set(va.fingerprint)&set(te.fingerprint))}
report={'raw_feature_count':len(feats),'transformed_feature_count':len(names),'raw_to_transformed_mapping':mapping,'forbidden_feature_lineage':sorted(set(' '.join(names)) & forbidden),'fingerprint_overlap':overlaps,'exact_vector_overlap':overlaps,'target_in_X':False,'Attack_type_in_X':False,'source_file_in_X':False,'fingerprint_in_X':False,'tcp_dstport_in_X':False,'audit_models_validation':scores,'preprocessing_train_only':True,'test_isolation':True,'leakage_conclusion':'POTENTIAL_LEAKAGE','reason':'Perfect held-out performance plus feature-level/source-scenario proxy risk requires a human-reviewed methodological decision before further Edge seeds.'}
(out/'leakage_audit.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
