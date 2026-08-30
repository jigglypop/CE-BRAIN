"""Exploratory Stage 3C: condition-specific refit versus calibrated WT structure."""
from __future__ import annotations
import argparse, hashlib, importlib.util, json, os, sys
from pathlib import Path
from typing import Any
import numpy as np

ROOT=Path(__file__).resolve().parents[2]
R2_PATH=ROOT/"examples"/"brain"/"ce_brain_stage3b_unc31_replication_r2.py"
SPEC=importlib.util.spec_from_file_location("stage3b_r2_sealed_for_stage3c",R2_PATH)
if SPEC is None or SPEC.loader is None: raise RuntimeError("STAGE3C_APPARATUS_STOP: Stage3B unavailable")
r2=importlib.util.module_from_spec(SPEC);sys.modules[SPEC.name]=r2;SPEC.loader.exec_module(r2)
b=r2.base;s3a=b.s3a
STOP="STAGE3C_APPARATUS_STOP";SEED=20_260_907;BOOTSTRAPS=1_999
CONTRACT=ROOT/"paper"/"검증_원장"/"CE_BRAIN_STAGE3C_조건의존연산자_계약.md"
TEST_FILE=ROOT/"tests"/"test_ce_brain_stage3c_condition_operator.py"
ARTIFACT=ROOT/"artifacts"/"brain"/"ce_brain_stage3c_condition_operator"
STAGE3B_ARTIFACT=ROOT/"artifacts"/"brain"/"ce_brain_stage3b_unc31_replication_r2"
MANIFEST="stage3c-manifest.json";RESULT="stage3c-result.json";VALIDATION="stage3c-validation-receipt.json"

def cbytes(x:Any)->bytes:return (json.dumps(x,indent=2,sort_keys=True,allow_nan=False)+"\n").encode()
def sha(path:Path)->str:
 d=hashlib.sha256()
 with path.open("rb") as f:
  while q:=f.read(8*1024*1024):d.update(q)
 return d.hexdigest()
def write_once(path:Path,x:Any)->str:
 if path.exists():raise RuntimeError(f"{STOP}: refusing overwrite {path.name}")
 path.parent.mkdir(parents=True,exist_ok=True);payload=cbytes(x);tmp=path.with_name(f".{path.name}.{os.getpid()}.tmp")
 tmp.write_bytes(payload);tmp.replace(path);return hashlib.sha256(payload).hexdigest()

def development_subject(subject:int)->bool:
 token=f"CE-BRAIN-STAGE3C-20260906|{subject}".encode()
 return int(hashlib.sha256(token).hexdigest()[:8],16)%10<7

def preregistered_files():
 return (Path(__file__).resolve(),TEST_FILE,CONTRACT,R2_PATH,r2.BASE_PATH,b.STAGE3A_PATH)

def seal(data_dir:Path,artifact_dir:Path)->dict[str,Any]:
 b.verify_inventory(data_dir,STAGE3B_ARTIFACT,hash_files=True)
 stage3b_result=STAGE3B_ARTIFACT/b.RESULT;stage3b_validation=STAGE3B_ARTIFACT/b.VALIDATION
 if not stage3b_result.is_file() or not stage3b_validation.is_file():raise RuntimeError(f"{STOP}: Stage3B evidence")
 files={str(p.relative_to(ROOT)).replace("\\","/"):sha(p) for p in preregistered_files()}
 manifest={"confirmation_endpoints_opened":True,"stage3b_model_scores_opened":True,
           "stage3c_model_scores_opened":False,"files":files,
           "runtime":b.verify_runtime(),"stage3b_result_sha256":sha(stage3b_result),
           "stage3b_validation_sha256":sha(stage3b_validation)}
 manifest["manifest_sha256"]=write_once(artifact_dir/MANIFEST,manifest);return manifest

def verify_manifest(data_dir:Path,artifact_dir:Path)->str:
 path=artifact_dir/MANIFEST;manifest=json.loads(path.read_text())
 files={str(p.relative_to(ROOT)).replace("\\","/"):sha(p) for p in preregistered_files()}
 b.verify_inventory(data_dir,STAGE3B_ARTIFACT,hash_files=True)
 if (manifest.get("stage3c_model_scores_opened") is not False or manifest.get("files")!=files
     or manifest.get("runtime")!=b.verify_runtime()
     or manifest.get("stage3b_result_sha256")!=sha(STAGE3B_ARTIFACT/b.RESULT)
     or manifest.get("stage3b_validation_sha256")!=sha(STAGE3B_ARTIFACT/b.VALIDATION)):
  raise RuntimeError(f"{STOP}: manifest mutation")
 return sha(path)

def calibrate(probability:np.ndarray,y:np.ndarray)->dict[str,Any]:
 x=np.log(np.clip(probability,1e-6,1-1e-6)/np.clip(1-probability,1e-6,1))[:,None]
 return s3a.fit_logistic(x,y,1e-4,maxiter=200)
def calibrated_predict(model:dict[str,Any],probability:np.ndarray)->np.ndarray:
 x=np.log(np.clip(probability,1e-6,1-1e-6)/np.clip(1-probability,1e-6,1))[:,None]
 return s3a.predict_logistic(model,x)

def comparison(losses:dict[str,dict[int,float]],better:str,baseline:str,offset:int)->dict[str,float]:
 rng=np.random.Generator(np.random.PCG64(SEED+offset));values=s3a.bootstrap_improvement(losses,better,baseline,rng)
 means=s3a.mean_losses(losses)
 return {"improvement":(means[baseline]-means[better])/means[baseline],
         "lower_95":float(np.quantile(values,.025)),"median":float(np.median(values))}

def decide(result:dict[str,Any])->str:
 winner=result["condition_specific_ranking"][0];family=winner.split("_",1)[1]
 gain=result["comparisons"][f"{winner}_vs_C_{family}"];null=result["comparisons"][f"{winner}_vs_U_N"]
 runner=result["comparisons"]["winner_vs_runner"]
 if (gain["improvement"]>=.03 and gain["lower_95"]>0 and null["improvement"]>=.05
     and null["lower_95"]>0 and runner["improvement"]>=.03 and runner["lower_95"]>0):
  return f"EXPLORATORY_CONDITION_DEPENDENT_{family}_SUPPORTED"
 base=result["comparisons"]["U_N_vs_W_N"]
 if base["improvement"]>=.03 and base["lower_95"]>0:return "EXPLORATORY_GENOTYPE_BASE_RATE_SHIFT_ONLY"
 return "CONDITION_DEPENDENT_OPERATOR_NOT_ESTABLISHED"

def build_result(data_dir:Path,artifact_dir:Path)->dict[str,Any]:
 manifest_sha=verify_manifest(data_dir,artifact_dir);template=b.load_positions(data_dir/"anatlas_neuron_positions.txt")
 wt=b.cohort_rows(data_dir,"WT",template);wt=[x for x in wt if not s3a.source_holdout(x["source"])]
 unc=b.cohort_rows(data_dir,"UNC31",template);ud=[x for x in unc if development_subject(x["subject"]) and not s3a.source_holdout(x["source"])]
 uc=[x for x in unc if not development_subject(x["subject"]) and not s3a.source_holdout(x["source"])]
 wp={(x["source"],x["receiver"]) for x in wt};up={(x["source"],x["receiver"]) for x in ud}
 ud=[x for x in ud if (x["source"],x["receiver"]) in wp]
 uc=[x for x in uc if (x["source"],x["receiver"]) in wp and (x["source"],x["receiver"]) in up]
 if len(ud)<8_000 or len(uc)<5_000 or len({x["subject"] for x in ud})<5 or len({x["subject"] for x in uc})<5:
  raise RuntimeError(f"{STOP}: coverage")
 wa=s3a.feature_arrays(wt,template);uda=s3a.feature_arrays(ud,template);uca=s3a.feature_arrays(uc,template)
 wm=s3a.fit_models(wa,template);um=s3a.fit_models(uda,template)
 wdev=s3a.predict_models(wm,uda,include_graph=True);wconf=s3a.predict_models(wm,uca,include_graph=True)
 uconf=s3a.predict_models(um,uca,include_graph=True)
 predictions={"W_N":wconf["N"],"U_N":uconf["N"]}
 for family in ("R","F","S","O","G"):
  cal=calibrate(wdev[family],uda["y"]);predictions[f"C_{family}"]=calibrated_predict(cal,wconf[family])
  predictions[f"U_{family}"]=uconf[family]
 losses=s3a.subject_losses(uca,predictions);means=s3a.mean_losses(losses)
 ranking=sorted((f"U_{f}" for f in ("R","F","S","O","G")),key=means.get);winner,runner=ranking[:2]
 comps={"U_N_vs_W_N":comparison(losses,"U_N","W_N",10)}
 for i,family in enumerate(("R","F","S","O","G")):
  comps[f"U_{family}_vs_C_{family}"]=comparison(losses,f"U_{family}",f"C_{family}",20+i)
  comps[f"U_{family}_vs_U_N"]=comparison(losses,f"U_{family}","U_N",30+i)
 comps["winner_vs_runner"]={"better":winner,"baseline":runner,**comparison(losses,winner,runner,50)}
 result={"bootstrap":{"repetitions":BOOTSTRAPS,"seed":SEED},"claim_ceiling":"post-endpoint exploratory genotype-conditioned representation",
         "comparisons":comps,"condition_specific_ranking":ranking,"coverage":{"unc31_development_rows":len(ud),
         "unc31_development_subjects":len({x['subject'] for x in ud}),"unc31_confirmation_rows":len(uc),
         "unc31_confirmation_subjects":len({x['subject'] for x in uc}),"wt_rows":len(wt)},
         "losses":means,"manifest_sha256":manifest_sha,"stage4_authorized":False}
 result["decision"]=decide(result);validate(result);return result

def validate(r:dict[str,Any])->None:
 if r.get("decision")!=decide(r) or r.get("stage4_authorized") is not False:raise RuntimeError(f"{STOP}: decision")
def execute(data_dir:Path,artifact_dir:Path)->dict[str,Any]:
 r=build_result(data_dir,artifact_dir);h=write_once(artifact_dir/RESULT,r);return {"result_sha256":h,**r}
def verify_result(data_dir:Path,artifact_dir:Path)->dict[str,Any]:
 path=artifact_dir/RESULT;stored=json.loads(path.read_text());validate(stored);fresh=build_result(data_dir,artifact_dir)
 if cbytes(stored)!=cbytes(fresh):raise RuntimeError(f"{STOP}: recomputation")
 row={"decision":stored["decision"],"raw_recomputed":True,"result_sha256":sha(path),"status":"PASS"}
 row["validation_receipt_sha256"]=write_once(artifact_dir/VALIDATION,row);return row

def main():
 p=argparse.ArgumentParser();p.add_argument("--data-dir",type=Path,default=b.DEFAULT_DATA);p.add_argument("--artifact-dir",type=Path,default=ARTIFACT)
 g=p.add_mutually_exclusive_group(required=True)
 for a in ("seal","execute","verify-result"):g.add_argument(f"--{a}",action="store_true")
 a=p.parse_args();o=seal(a.data_dir,a.artifact_dir) if a.seal else execute(a.data_dir,a.artifact_dir) if a.execute else verify_result(a.data_dir,a.artifact_dir)
 print(json.dumps(o,sort_keys=True,allow_nan=False))
if __name__=="__main__":main()
