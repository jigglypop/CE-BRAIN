"""Optimizer-only Armijo overlay for the sealed Stage 1 Allen predecessor."""
from __future__ import annotations
import argparse, hashlib, importlib.util, json, math
from pathlib import Path
from typing import Any
import numpy as np

PREDECESSOR_MANIFEST="190f75971a6e7879e3f2d6825507950d018c954862257b88e0f938b4488a7169"
PREDECESSOR_SOURCE="35d265888afa39d16c0e0f398302b179ae8399c8d16f38983f611147ef26d2de"
STOP="STAGE1_APPARATUS_STOP"; LAMBDA=1e-4; C=1e-4; MIN_ALPHA=2.0**-40
MANIFEST="stage1-armijo-retry-manifest.json"; RESULT="stage1-armijo-retry-result.json"
PREREG_FILES=("00-retry-contract.md","10-optimizer-routes.md","20-audit.md","21-preexecution-validation.md","stage1_allen_armijo_retry.py","test_stage1_allen_armijo_retry.py")
def _sha(b:bytes)->str:return hashlib.sha256(b).hexdigest()
def _array_hash(*a:np.ndarray)->str:return _sha(b"".join(np.ascontiguousarray(x).tobytes() for x in a))
def _pivot()->Path:return Path(__file__).resolve().parent
def _parent_pivot()->Path:return _pivot().parent/"stage1-allen-single-cell-local-dynamics"
def _atomic(p:Path,x:dict[str,Any])->str:
 b=(json.dumps(x,sort_keys=True,indent=2)+"\n").encode();t=p.with_suffix(p.suffix+".tmp");t.write_bytes(b);t.replace(p);return _sha(b)

def _parent(raw:Path)->Any:
 root=_parent_pivot(); manifest=root/"stage1-preregistration-manifest.json"; source=root/"stage1_allen_local_dynamics.py"
 if not manifest.is_file() or _sha(manifest.read_bytes())!=PREDECESSOR_MANIFEST or not source.is_file() or _sha(source.read_bytes())!=PREDECESSOR_SOURCE:raise RuntimeError(f"{STOP}:predecessor hash")
 locked=json.loads(manifest.read_bytes())
 if set(locked.get("files",{}))!={"00-contract.md","10-data-lock.md","10-sources.md","20-hypotheses.md","30-models.md","40-metrics.md","50-gates.md","20-audit.md","21-preexecution-validation.md","stage1_allen_local_dynamics.py","test_stage1_allen_local_dynamics.py"}:raise RuntimeError(f"{STOP}:predecessor population")
 for rel,digest in locked["files"].items():
  if _sha((root/rel).read_bytes())!=digest:raise RuntimeError(f"{STOP}:predecessor mutation")
 spec=importlib.util.spec_from_file_location("sealed_stage1_parent",source); assert spec and spec.loader;module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);module.verify_manifest(raw,pivot=root);return module

def objective(design:np.ndarray,y:np.ndarray,beta:np.ndarray)->float:
 eta=design@beta;return float(np.sum(y*eta-np.logaddexp(0,eta))-0.5*LAMBDA*np.sum(beta[1:]**2))
def armijo_logistic(x:np.ndarray,y:np.ndarray)->tuple[np.ndarray,dict[str,Any]]:
 if not np.all(np.isfinite(x)) or not np.all(np.isfinite(y)):raise RuntimeError(f"{STOP}:armijo input")
 if np.min(y)==np.max(y):raise RuntimeError(f"{STOP}:degenerate spikes")
 d=np.c_[np.ones(len(x)),x];beta=np.zeros(d.shape[1]);pen=np.diag(np.r_[0.,np.full(x.shape[1],LAMBDA)]);minimum=1.;final_q=objective(d,y,beta)
 final_step=math.inf
 for it in range(1,51):
  eta=d@beta;p=1/(1+np.exp(-np.clip(eta,-50,50)));w=np.maximum(p*(1-p),1e-12);g=d.T@(y-p)-pen@beta;h=d.T@(w[:,None]*d)+pen
  gradient=float(np.max(np.abs(g)))
  if gradient<=1e-8:return beta,{"iterations":it-1,"final_objective":objective(d,y,beta),"final_gradient_inf":gradient,"final_step_inf":0.0 if it==1 else final_step,"minimum_accepted_alpha":minimum}
  try: direction=np.linalg.solve(h,g)
  except np.linalg.LinAlgError as e:raise RuntimeError(f"{STOP}:armijo solve") from e
  gd=float(g@direction)
  if not np.all(np.isfinite(direction)) or not math.isfinite(gd) or gd<=0:raise RuntimeError(f"{STOP}:armijo ascent")
  q=objective(d,y,beta);alpha=1.
  while alpha>=MIN_ALPHA:
   trial=objective(d,y,beta+alpha*direction)
   if math.isfinite(trial) and trial>=q+C*alpha*gd:break
   alpha*=.5
  if alpha<MIN_ALPHA:raise RuntimeError(f"{STOP}:armijo step")
  beta+=alpha*direction;final_q=objective(d,y,beta);step=float(np.max(np.abs(alpha*direction)));final_step=step;minimum=min(minimum,alpha)
  if final_q<q-1e-10:raise RuntimeError(f"{STOP}:armijo objective")
  post_p=1/(1+np.exp(-np.clip(d@beta,-50,50)));post_g=d.T@(y-post_p)-pen@beta;post_gradient=float(np.max(np.abs(post_g)))
  if post_gradient<=1e-8:return beta,{"iterations":it,"final_objective":final_q,"final_gradient_inf":post_gradient,"final_step_inf":step,"minimum_accepted_alpha":minimum}
 raise RuntimeError(f"{STOP}:armijo convergence")

def _fit(parent:Any,data:list[tuple[np.ndarray,np.ndarray,np.ndarray,np.ndarray]])->tuple[dict[str,Any],dict[str,Any]]:
 all0=np.vstack([r[0] for r in data]);all1=np.vstack([r[1] for r in data]);target=np.concatenate([r[2] for r in data]);event=np.concatenate([r[3] for r in data]);models={};receipts={}
 for name,features in (("M0",all0),("M1",all1)):
  z,mean,scale=parent._fit_standardize(features);voltage=parent._ridge(z,target);spike,receipt=armijo_logistic(z,event);models[name]={"mean":mean,"scale":scale,"voltage":voltage,"spike":spike,"parameter_sha256":_array_hash(mean,scale,voltage,spike)};receipts[name]=receipt
 return models,receipts

def seal(raw:Path,*,pivot:Path|None=None)->dict[str,Any]:
 pivot=_pivot() if pivot is None else pivot;parent=_parent(raw);files={}
 for rel in PREREG_FILES:
  p=pivot/rel
  if not p.is_file():raise RuntimeError(f"{STOP}:missing prereg:{rel}")
  files[rel]=_sha(p.read_bytes())
 root=_parent_pivot();payload={"schema":1,"predecessor_manifest_sha256":PREDECESSOR_MANIFEST,"predecessor_source_sha256":PREDECESSOR_SOURCE,"schema_receipt_sha256":_sha((root/parent.SCHEMA).read_bytes()),"raw_sha256":parent.RAW_SHA256,"files":files,"confirmation_opened":False};return {"manifest_sha256":_atomic(pivot/MANIFEST,payload),**payload}

def verify_manifest(raw:Path,*,pivot:Path|None=None)->tuple[Any,dict[str,Any]]:
 pivot=_pivot() if pivot is None else pivot;parent=_parent(raw);path=pivot/MANIFEST
 if not path.is_file():raise RuntimeError(f"{STOP}:missing manifest")
 payload=json.loads(path.read_bytes());root=_parent_pivot()
 if (payload.get("predecessor_manifest_sha256")!=PREDECESSOR_MANIFEST or payload.get("predecessor_source_sha256")!=PREDECESSOR_SOURCE or payload.get("schema_receipt_sha256")!=_sha((root/parent.SCHEMA).read_bytes()) or payload.get("raw_sha256")!=parent.RAW_SHA256 or payload.get("confirmation_opened") is not False or set(payload.get("files",{}))!=set(PREREG_FILES)):raise RuntimeError(f"{STOP}:manifest identity")
 for rel,digest in payload["files"].items():
  if _sha((pivot/rel).read_bytes())!=digest:raise RuntimeError(f"{STOP}:manifest mutation")
 return parent,payload

def _restore(parent:Any,serialized:dict[str,Any])->dict[str,Any]:return parent._restore_models(serialized)
def _verify_optimizer_receipts(receipts:Any)->None:
 if not isinstance(receipts,dict) or set(receipts)!={"M0","M1"}:raise RuntimeError(f"{STOP}:optimizer receipt")
 for r in receipts.values():
  if not isinstance(r,dict) or not 0<=r.get("iterations",-1)<=50 or not math.isfinite(float(r.get("final_objective",math.nan))) or not math.isfinite(float(r.get("final_gradient_inf",math.nan))) or float(r.get("final_gradient_inf",math.inf))>1e-8 or not math.isfinite(float(r.get("final_step_inf",math.nan))) or not MIN_ALPHA<=float(r.get("minimum_accepted_alpha",0))<=1:raise RuntimeError(f"{STOP}:optimizer receipt")
def verify_result(raw:Path,*,pivot:Path|None=None)->dict[str,Any]:
 pivot=_pivot() if pivot is None else pivot;parent,manifest=verify_manifest(raw,pivot=pivot);path=pivot/RESULT
 if not path.is_file():raise RuntimeError(f"{STOP}:missing result")
 body=path.read_bytes();x=json.loads(body)
 if (x.get("manifest_sha256")!=_sha((pivot/MANIFEST).read_bytes()) or x.get("predecessor_manifest_sha256")!=PREDECESSOR_MANIFEST or x.get("raw_sha256")!=parent.RAW_SHA256 or x.get("persistent_raw_bytes")!=0 or x.get("stage2_authorized") is not False):raise RuntimeError(f"{STOP}:result identity")
 models=_restore(parent,x.get("models"));rows=x.get("sweeps");parent._verify_rows(rows,models)
 receipts=x.get("optimizer_receipts",{});_verify_optimizer_receipts(receipts)
 if x.get("decision")!=parent.decision([r for r in rows if r["sweep"] in parent.CONFIRM]):raise RuntimeError(f"{STOP}:decision")
 return {"result_sha256":_sha(body),"result":x}

def execute(raw:Path,*,pivot:Path|None=None)->dict[str,Any]:
 pivot=_pivot() if pivot is None else pivot
 if (pivot/RESULT).exists():raise RuntimeError(f"{STOP}:existing result")
 parent,manifest=verify_manifest(raw,pivot=pivot);fit=[];rows=[]
 import h5py
 with h5py.File(raw,"r") as f:
  for s in parent.FIT:
   v,i,_=parent._load(f,s);fit.append(parent._rows(v,i,thin=True))
  models,receipts=_fit(parent,fit)
  for s in parent.DEV+parent.CONFIRM:
   v,i,dr=parent._load(f,s);r=parent._evaluate(models,v,i,s);r["data_receipt"]=dr;rows.append(r)
  for s in parent.FIT:
   v,i,dr=parent._load(f,s);r=parent._evaluate(models,v,i,s);r["data_receipt"]=dr;rows.append(r)
 parent._verify_rows(rows,models);x={"schema":1,"manifest_sha256":_sha((pivot/MANIFEST).read_bytes()),"predecessor_manifest_sha256":PREDECESSOR_MANIFEST,"raw_sha256":parent.RAW_SHA256,"models":parent._json_models(models),"optimizer_receipts":receipts,"sweeps":rows,"decision":parent.decision([r for r in rows if r["sweep"] in parent.CONFIRM]),"stage2_authorized":False,"persistent_raw_bytes":0};_atomic(pivot/RESULT,x);return {**x,"result_sha256":verify_result(raw,pivot=pivot)["result_sha256"]}
def main()->None:
 p=argparse.ArgumentParser();p.add_argument("--nwb",required=True);p.add_argument("--seal",action="store_true");p.add_argument("--verify-result",action="store_true");a=p.parse_args();raw=Path(a.nwb)
 if a.seal and a.verify_result:raise RuntimeError(f"{STOP}:mode")
 print(json.dumps(seal(raw) if a.seal else verify_result(raw) if a.verify_result else execute(raw),sort_keys=True))
if __name__=="__main__":main()
