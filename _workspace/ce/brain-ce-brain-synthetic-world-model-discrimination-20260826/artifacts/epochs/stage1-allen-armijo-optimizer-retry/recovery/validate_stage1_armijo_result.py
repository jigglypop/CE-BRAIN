"""Read-only forensic validator for the sealed Armijo retry result."""
from __future__ import annotations
import argparse, hashlib, importlib.util, json, math
from pathlib import Path
from typing import Any
import h5py, numpy as np

MANIFEST_SHA="ccc2299ab21296afdbfe6591b2290f8e490b99870565074f6fd42c93891ed65e"
RESULT_SHA="64b48fb80763bd08d08d08a6048ec6bd641e8c0f225c05109e2d50a4a0c6a395"
TOL=1e-12
def _sha(b:bytes)->str:return hashlib.sha256(b).hexdigest()
def _root()->Path:return Path(__file__).resolve().parent.parent
def _source()->Path:return _root()/"stage1_allen_armijo_retry.py"
def _load_retry()->Any:
 p=_source()
 if not p.is_file():raise RuntimeError("RECOVERY:missing retry source")
 s=importlib.util.spec_from_file_location("sealed_retry_recovery",p);assert s and s.loader;m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def _dtype(name:str,key:str)->np.dtype:return np.dtype(np.float32 if name=="M0" and key in {"mean","scale"} else np.float64)
def _legacy_model(retry:Any,name:str,item:dict[str,Any])->dict[str,np.ndarray]:
 keys=("mean","scale","voltage","spike")
 out={key:np.asarray(item[key],dtype=_dtype(name,key)) for key in keys}
 if any(not np.all(np.isfinite(value)) for value in out.values()) or np.any(out["scale"]<=0):raise RuntimeError("RECOVERY:model finite")
 digest=retry._array_hash(*(out[key] for key in keys))
 if digest!=item.get("parameter_sha256"):raise RuntimeError("RECOVERY:legacy parameter hash")
 return out
def _legacy_models(retry:Any,models:Any)->dict[str,dict[str,np.ndarray]]:
 if not isinstance(models,dict) or set(models)!={"M0","M1"}:raise RuntimeError("RECOVERY:model population")
 return {name:_legacy_model(retry,name,models[name]) for name in ("M0","M1")}
def _same(a:Any,b:Any)->bool:
 if isinstance(a,float) or isinstance(b,float):return math.isclose(float(a),float(b),rel_tol=TOL,abs_tol=TOL)
 return a==b
def _compare_row(stored:dict[str,Any],fresh:dict[str,Any])->None:
 for key in ("sweep","origins","target_sha256","persistence_rmse_mv","relative_voltage_improvement","relative_brier_improvement"):
  if key not in stored or key not in fresh or not _same(stored[key],fresh[key]):raise RuntimeError(f"RECOVERY:row:{key}")
 for name in ("M0","M1"):
  for key in ("rmse_mv","nrmse","brier","brier_sum","count","prevalence","persistence_improvement"):
   if not _same(stored[name][key],fresh[name][key]):raise RuntimeError(f"RECOVERY:metric:{stored['sweep']}:{name}:{key}")
 for key in ("sweep","response_path","stimulus_path","units","conversions","rates","index_inclusive","aligned_half_open","bins","voltage_sha256","current_sha256"):
  if stored.get("data_receipt",{}).get(key)!=fresh.get("data_receipt",{}).get(key):raise RuntimeError(f"RECOVERY:data receipt:{stored['sweep']}:{key}")
def validate(raw:Path)->dict[str,Any]:
 retry=_load_retry();root=_root();manifest_path=root/retry.MANIFEST;result_path=root/retry.RESULT
 if _sha(manifest_path.read_bytes())!=MANIFEST_SHA or _sha(result_path.read_bytes())!=RESULT_SHA:raise RuntimeError("RECOVERY:sealed artifact hash")
 parent,manifest=retry.verify_manifest(raw,pivot=root);result=json.loads(result_path.read_bytes())
 if result.get("manifest_sha256")!=MANIFEST_SHA or result.get("raw_sha256")!=parent.RAW_SHA256:raise RuntimeError("RECOVERY:result link")
 legacy=_legacy_models(retry,result["models"])
 fit=[]
 with h5py.File(raw,"r") as f:
  for sweep in parent.FIT:
   v,i,_=parent._load(f,sweep);fit.append(parent._rows(v,i,thin=True))
  models,receipts=retry._fit(parent,fit)
  for name in ("M0","M1"):
   for key in ("mean","scale","voltage","spike"):
    target=np.asarray(models[name][key],dtype=_dtype(name,key))
    if not np.array_equal(target,legacy[name][key]):raise RuntimeError(f"RECOVERY:fit parameter:{name}:{key}")
   if receipts[name]!=result.get("optimizer_receipts",{}).get(name):raise RuntimeError(f"RECOVERY:optimizer receipt:{name}")
  fresh=[]
  for sweep in parent.DEV+parent.CONFIRM+parent.FIT:
   v,i,receipt=parent._load(f,sweep);row=parent._evaluate(models,v,i,sweep);row["data_receipt"]=receipt;fresh.append(row)
 stored={row["sweep"]:row for row in result.get("sweeps",[])}
 if set(stored)!={*parent.FIT,*parent.DEV,*parent.CONFIRM} or len(stored)!=len(result["sweeps"]):raise RuntimeError("RECOVERY:sweep population")
 for row in fresh:_compare_row(stored[row["sweep"]],row)
 if result.get("decision")!=parent.decision([stored[s] for s in parent.CONFIRM]):raise RuntimeError("RECOVERY:decision")
 receipt={"validator":"stage1-armijo-legacy-dtype-v1","manifest_sha256":MANIFEST_SHA,"result_sha256":RESULT_SHA,"raw_sha256":parent.RAW_SHA256,"m0_legacy_dtype":{"mean":"float32","scale":"float32","voltage":"float64","spike":"float64"},"m1_legacy_dtype":"float64","status":"PASS"}
 return {"validation_sha256":_sha((json.dumps(receipt,sort_keys=True,separators=(",",":"))+"\n").encode()),**receipt}
def main()->None:
 p=argparse.ArgumentParser();p.add_argument("--nwb",required=True);a=p.parse_args();print(json.dumps(validate(Path(a.nwb)),sort_keys=True))
if __name__=="__main__":main()
