"""Clean Phase-2 MLP training.  Test data is loaded only after checkpoint selection."""
from __future__ import annotations
import argparse,json,random,time,subprocess
from pathlib import Path
import joblib,numpy as np,pandas as pd,psutil,torch,yaml
from torch.utils.data import DataLoader,TensorDataset
from src.data.materialize import materialize
from src.evaluation.metrics import binary_metrics
from src.models.mlp import MLP
from src.preprocessing.pipeline import build_preprocessor
from src.tracking.mlflow import configure_tracking

ROOT=Path(__file__).resolve().parents[2]
def seed_all(seed): random.seed(seed);np.random.seed(seed);torch.manual_seed(seed)
def train(ds,seed):
 out=ROOT/'results'/'baseline'/ds; out.mkdir(parents=True,exist_ok=True); processed=ROOT/'data'/ds/'processed'
 if not (processed/'metadata.json').exists(): materialize(ds)
 contract=json.loads((out/'feature_contract.json').read_text()); feats=contract['features']; forbidden=set(contract['removed'])|{'binary_target','fingerprint','source_file','Attack_type','type','label','Attack_label','original_label'}
 if set(feats)&forbidden: raise ValueError('Forbidden feature in contract')
 train_df=pd.read_parquet(processed/'train.parquet'); val_df=pd.read_parquet(processed/'validation.parquet')
 if set(train_df.fingerprint)&set(val_df.fingerprint): raise ValueError('Fingerprint overlap train/validation')
 numeric=yaml.safe_load((ROOT/'configs'/'datasets'/f'{ds}.yaml').read_text())['feature_policy'].get('model_numeric',[])+yaml.safe_load((ROOT/'configs'/'datasets'/f'{ds}.yaml').read_text())['feature_policy'].get('model_binary',[])
 categorical=[x for x in feats if x not in numeric]
 prep=build_preprocessor(numeric,categorical); t0=time.time()
 def transform(df,fit=False):
  # CIC's audited +inf Rate values become missing before the train-fitted imputer.
  values=df[feats].replace([np.inf,-np.inf],np.nan).copy()
  for column in numeric:
   values[column]=pd.to_numeric(values[column],errors='coerce')
  x=prep.fit_transform(values) if fit else prep.transform(values); x=x.toarray() if hasattr(x,'toarray') else x; x=np.nan_to_num(x.astype('float32')); return x,df.binary_target.to_numpy(dtype='float32')
 xtr,ytr=transform(train_df,True); xva,yva=transform(val_df); pre=time.time()-t0
 art=ROOT/'artifacts'/'preprocessing'/ds;art.mkdir(parents=True,exist_ok=True);joblib.dump(prep,art/'preprocessor.joblib')
 seed_all(seed); mc=yaml.safe_load((ROOT/'configs'/'model.yaml').read_text())['model']; model=MLP(xtr.shape[1],tuple(mc['hidden_layers']),mc['dropout']); opt=torch.optim.Adam(model.parameters(),lr=mc['learning_rate']); lossfn=torch.nn.CrossEntropyLoss()
 loader=DataLoader(TensorDataset(torch.from_numpy(xtr),torch.from_numpy(ytr.astype('int64'))),batch_size=mc['batch_size'],shuffle=True); best=float('inf');bad=0;hist=[]; ckpt=ROOT/'artifacts'/'models'/ds;ckpt.mkdir(parents=True,exist_ok=True); path=ckpt/f'mlp_seed_{seed}.pt'; start=time.time()
 for epoch in range(mc['max_epochs']):
  model.train(); losses=[]
  for x,y in loader:
   opt.zero_grad(); l=lossfn(model(x),y);l.backward();torch.nn.utils.clip_grad_norm_(model.parameters(),5.0);opt.step();losses.append(l.item())
  model.eval();
  with torch.no_grad(): vl=lossfn(model(torch.from_numpy(xva)),torch.from_numpy(yva.astype('int64'))).item()
  hist.append({'epoch':epoch+1,'train_loss':float(np.mean(losses)),'validation_loss':vl})
  if vl<best: best=vl;bad=0;torch.save({'state_dict':model.state_dict(),'input_dim':xtr.shape[1]},path)
  else: bad+=1
  if bad>=mc['early_stopping_patience']: break
 training=time.time()-start
 # Test is deliberately first read after checkpoint selection.
 test_df=pd.read_parquet(processed/'test.parquet');
 if (set(test_df.fingerprint)&set(train_df.fingerprint)) or (set(test_df.fingerprint)&set(val_df.fingerprint)): raise ValueError('Fingerprint overlap test')
 xte,yte=transform(test_df); saved=torch.load(path,weights_only=True);model.load_state_dict(saved['state_dict']);model.eval(); t=time.time()
 with torch.no_grad(): score=torch.softmax(model(torch.from_numpy(xte)),1)[:,1].numpy()
 infer=time.time()-t; pred=(score>=.5).astype(int); metrics=binary_metrics(yte,pred,score); metrics.update({'dataset':ds,'seed':seed,'threshold':.5,'best_epoch':int(np.argmin([h['validation_loss'] for h in hist])+1),'epochs':len(hist),'preprocessing_seconds':pre,'training_seconds':training,'inference_seconds':infer,'test_seconds':infer,'total_seconds':pre+training+infer,'feature_count':xtr.shape[1],'leakage_alarm':any(metrics[k]>.995 for k in ('accuracy','f1','roc_auc','attack_recall')),'device':'cpu','ram_mb':psutil.Process().memory_info().rss/1048576})
 (out/f'metrics_seed_{seed}.json').write_text(json.dumps(metrics,indent=2));pd.DataFrame(hist).to_csv(out/f'training_history_seed_{seed}.csv',index=False);pd.DataFrame([[metrics['tn'],metrics['fp']],[metrics['fn'],metrics['tp']]],index=['normal','attack'],columns=['normal','attack']).to_csv(out/f'confusion_matrix_seed_{seed}.csv');(out/f'timing_seed_{seed}.json').write_text(json.dumps({k:metrics[k] for k in metrics if k.endswith('seconds') or k in ('ram_mb','device')},indent=2))
 return metrics
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--dataset',required=True);p.add_argument('--seed',type=int,required=True);print(json.dumps(train(p.parse_args().dataset,p.parse_args().seed),indent=2))
