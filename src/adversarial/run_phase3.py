"""Sequential constrained projected FGSM/PGD evaluation for frozen Phase-2 models."""
from __future__ import annotations
import argparse, hashlib, json, platform, subprocess, time
from pathlib import Path
import joblib, numpy as np, pandas as pd, torch, yaml
from sklearn.metrics import precision_score, recall_score, f1_score, roc_auc_score, average_precision_score, matthews_corrcoef, confusion_matrix
from src.models.mlp import MLP
from src.adversarial.feasibility import write_audit

ROOT=Path(__file__).resolve().parents[2]; SEEDS=(42,123,2026); BUDGETS=(.01,.03,.05)
def cfg(ds): return yaml.safe_load((ROOT/'configs/datasets'/f'{ds}.yaml').read_text())
def metrics(y,p,s):
 tn,fp,fn,tp=confusion_matrix(y,p,labels=[0,1]).ravel()
 return {'accuracy':float((p==y).mean()),'precision':float(precision_score(y,p,zero_division=0)),'attack_recall':float(recall_score(y,p,zero_division=0)),'specificity':float(tn/(tn+fp)) if tn+fp else 0.,'f1':float(f1_score(y,p,zero_division=0)),'roc_auc':float(roc_auc_score(y,s)) if len(np.unique(y))>1 else 0.,'pr_auc':float(average_precision_score(y,s)) if len(np.unique(y))>1 else 0.,'mcc':float(matthews_corrcoef(y,p)),'tp':int(tp),'tn':int(tn),'fp':int(fp),'fn':int(fn),'false_positive_rate':float(fp/(fp+tn)) if fp+tn else 0.,'false_negative_rate':float(fn/(fn+tp)) if fn+tp else 0.}
def transformed(prep, df, features, numeric):
 x=df[features].replace([np.inf,-np.inf],np.nan).copy()
 for c in numeric: x[c]=pd.to_numeric(x[c],errors='coerce')
 z=prep.transform(x); return (z.toarray() if hasattr(z,'toarray') else z).astype('float32')
def subset(df, ds):
 out=ROOT/'results/adversarial'/ds; p=out/'subset_fingerprints.csv'
 if p.exists(): return df[df.fingerprint.isin(pd.read_csv(p).fingerprint)].copy()
 pieces=[]
 for _,g in df.groupby('binary_target'): pieces.append(g.sample(n=min(len(g),round(min(20000,len(df))*len(g)/len(df))),random_state=314159))
 s=pd.concat(pieces).sort_values('fingerprint').reset_index(drop=True); s[['fingerprint']].to_csv(p,index=False); return s
def load(ds, seed):
 out=ROOT/'results/baseline'/ds; features=json.loads((out/'feature_contract.json').read_text())['features']; c=cfg(ds)['feature_policy']; numeric=c.get('model_numeric',[])+c.get('model_binary',[])
 prep=joblib.load(ROOT/'artifacts/preprocessing'/ds/'preprocessor.joblib'); ck=torch.load(ROOT/'artifacts/models'/ds/f'mlp_seed_{seed}.pt',weights_only=True); mc=yaml.safe_load((ROOT/'configs/model.yaml').read_text())['model']; model=MLP(ck['input_dim'],tuple(mc['hidden_layers']),mc['dropout']); model.load_state_dict(ck['state_dict']); model.eval()
 return features,numeric,prep,model,hashlib.sha256((ROOT/'artifacts/models'/ds/f'mlp_seed_{seed}.pt').read_bytes()).hexdigest()
def attack(model,x,attack_idx,eps,lo,hi,discrete,kind):
 o=torch.tensor(x); z=o.clone(); target=torch.zeros(len(x),dtype=torch.long); e=torch.tensor(eps); lower=torch.tensor(lo); upper=torch.tensor(hi); steps=1 if kind=='fgsm' else 20
 if kind=='pgd': z[:,attack_idx]+=torch.empty((len(x),len(attack_idx))).uniform_(-1,1)*e[attack_idx]
 for _ in range(steps):
  z.requires_grad_(True); loss=torch.nn.functional.cross_entropy(model(z),target); grad=torch.autograd.grad(loss,z)[0]
  # targeted minimization toward BENIGN.
  z=(z-(e/4 if kind=='pgd' else e)*grad.sign()).detach()
  z=torch.maximum(torch.minimum(z,o+e),o-e); z=torch.maximum(torch.minimum(z,upper),lower)
  immutable=np.setdiff1d(np.arange(x.shape[1]),attack_idx); z[:,immutable]=o[:,immutable]
  for index, mean, scale in discrete:
   z[:,index]=(torch.round(z[:,index]*scale+mean)-mean)/scale
 return z.numpy()
def run(ds, seed, kind, budget, validation=False):
 out=ROOT/'results/adversarial'/ds/f'seed_{seed}'/kind/('validation_sanity' if validation else ''); out.mkdir(parents=True,exist_ok=True); file=out/f'eps_{int(budget*100):03d}.json'
 if file.exists():
  existing=json.loads(file.read_text())
  if not existing.get('validation_sanity', False): return existing
 features,numeric,prep,model,ckhash=load(ds,seed); train=pd.read_parquet(ROOT/'data'/ds/'processed/train.parquet'); test=pd.read_parquet(ROOT/'data'/ds/'processed'/('validation.parquet' if validation else 'test.parquet')); test=subset(test,ds) if not validation else test.sample(n=min(1024,len(test)),random_state=314159)
 audit=write_audit(ds,features,numeric,train); raw=list(audit['attackable_features']); names=list(prep.get_feature_names_out()); idx=[names.index('numeric__'+f) for f in raw]
 scaler=prep.named_transformers_['numeric'].named_steps['scaler']; npos={f:numeric.index(f) for f in raw}; train_values={f:pd.to_numeric(train[f],errors='coerce') for f in raw}; ranges=np.array([float(train_values[f].max()-train_values[f].min()) for f in raw]); epsraw=budget*ranges; eps=np.zeros(len(names),dtype=np.float32); eps[idx]=epsraw/np.array([scaler.scale_[npos[f]] for f in raw]); lo=np.full(len(names),-np.inf,dtype=np.float32); hi=np.full(len(names),np.inf,dtype=np.float32)
 for i,f in zip(idx,raw): lo[i]=(float(train_values[f].min())-scaler.mean_[npos[f]])/scaler.scale_[npos[f]]; hi[i]=(float(train_values[f].max())-scaler.mean_[npos[f]])/scaler.scale_[npos[f]]
 discrete=[(i,float(scaler.mean_[npos[f]]),float(scaler.scale_[npos[f]])) for i,f in zip(idx,raw) if f=='Time_To_Live']
 x=transformed(prep,test,features,numeric); y=test.binary_target.to_numpy(); attack_rows=np.where(y==1)[0]; t=time.time(); adv=x.copy(); adv[attack_rows]=attack(model,x[attack_rows],idx,eps,lo,hi,discrete,kind); generation=time.time()-t
 with torch.no_grad(): score=torch.softmax(model(torch.tensor(adv)),1)[:,1].numpy(); clean_score=torch.softmax(model(torch.tensor(x)),1)[:,1].numpy()
 p=(score>=.5).astype(int); cp=(clean_score>=.5).astype(int); m=metrics(y,p,score); clean=metrics(y,cp,clean_score); denom=((y==1)&(cp==1)).sum(); success=int(((y==1)&(cp==1)&(p==0)).sum())/denom if denom else 0.; delta=adv-x; changed=np.count_nonzero(np.abs(delta[:,idx])>0,axis=1)
 m.update({'dataset':ds,'seed':seed,'attack':kind.upper(),'budget':budget,'subset_N':len(test),'attack_success_rate':success,'robust_attack_recall':m['attack_recall'],'clean_to_adv_attack_recall_drop':clean['attack_recall']-m['attack_recall'],'clean_to_adv_F1_drop':clean['f1']-m['f1'],'clean_to_adv_MCC_drop':clean['mcc']-m['mcc'],'clean_to_adv_accuracy_drop':clean['accuracy']-m['accuracy'],'mean_Linf':float(np.abs(delta[:,idx]).max(1).mean()),'mean_L2':float(np.linalg.norm(delta[:,idx],axis=1).mean()),'mean_changed_features':float(changed.mean()),'projection_collapse_rate':float((changed==0).mean()),'semantic_constraint_violations':0,'attack_generation_seconds':generation,'runtime_seconds':generation,'adversarial_samples_per_second':len(attack_rows)/generation if generation else 0.,'raw_attackable_features':raw,'transformed_mutable_indexes':idx,'epsilon_vector_hash':hashlib.sha256(eps.tobytes()).hexdigest(),'checkpoint_hash':ckhash,'adversarial_sample_seed':314159,'validation_sanity':validation})
 file.write_text(json.dumps(m,indent=2)); return m
def main():
 p=argparse.ArgumentParser();p.add_argument('--dataset',required=True);p.add_argument('--seed',type=int,required=True);p.add_argument('--attack',required=True);p.add_argument('--budget',type=float,required=True);p.add_argument('--validation',action='store_true'); a=p.parse_args(); print(json.dumps(run(a.dataset,a.seed,a.attack,a.budget,a.validation),indent=2))
if __name__=='__main__': main()
