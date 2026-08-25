"""BA-OBS-HPC2 author-order QC seal; raw mode is implemented, audit-gated, and uninvoked."""
from __future__ import annotations
import argparse, hashlib, json, re
from dataclasses import dataclass, asdict
from pathlib import Path
from urllib.parse import quote
from urllib.request import Request, urlopen
import numpy as np
from scipy.signal import butter, filtfilt
from scipy.stats import kurtosis

RUN=Path("_workspace/ce/brain-human-hippocampal-theta-author-qc-reanalysis-20260825")
COMMIT="14fdb3d852dcaba48a65d1185d3a6dfa2f83dba4"; FS=499.5; N=1000
RAW="https://raw.githubusercontent.com/OpenNeuroDatasets/ds006065/"+COMMIT; S3="https://s3.amazonaws.com/openneuro.org/ds006065"
STATIC_RECEIPT_SHA256="20008069771a37a7e7669e996d0bb799cabed1ad09e0e010c6c1f0ec33b93496"
SOURCE_LOCK_SHA256="66cac4202971cabb0838b3ddb93710c160c88325133411f58c8595c89e7c5810"
AUTHOR_TIME=np.arange(N)/999*(1000/FS)-.5
MASKS={"first999":np.arange(999),"latency":np.arange(50,649),"baseline":np.arange(225,245),"early":np.arange(257,275),"late":np.arange(275,375),"prestim":np.arange(100,200)}

@dataclass(frozen=True)
class Spec:
 protocol:str; subject:str; phase:str; task:str; blocks:int; nchan:int; clinical:str; bipolar:str; qc:tuple[str,...]
 @property
 def eeg(self): return f"sub-{self.subject}/ieeg/sub-{self.subject}_task-{self.task}_ieeg.eeg"
 @property
 def vhdr(self): return self.eeg[:-3]+"vhdr"
def _specs():
 r=[("TS","p16","pre","eppre",90,168,"RB1","RB2"),("TS","p16","post","eppost",60,168,"RB1","RB2"),("TS","p17","pre","eppre",63,175,"D1","D2"),("TS","p17","post","eppost",59,175,"D1","D2"),("TS","p18","pre","eppre",60,82,"AH2","AH3"),("TS","p18","post","eppost",60,82,"AH2","AH3"),("TS","p19","pre","eppre",60,168,"D1","D2"),("TS","p19","post","eppost",60,168,"D1","D2"),("PB","p17","pre","epcontrolpre",60,175,"D1","D2"),("PB","p17","post","epcontrolpost",60,175,"D1","D2"),("PB","p19","pre","epcontrolpre",60,168,"D1","D2"),("PB","p19","post","epcontrolpost",60,168,"D1","D2"),("PB","p20","pre","epcontrolpre",151,181,"D9","D10"),("PB","p20","post","epcontrolpost",149,181,"D9","D10"),("PB","UC004","pre","epcontrolpre",40,43,"RHH1","RHH2"),("PB","UC004","post","epcontrolpost",40,43,"RHH1","RHH2"),("PB","UC005","pre","epcontrolpre",40,68,"RHB1","RHB2"),("PB","UC005","post","epcontrolpost",40,68,"RHB1","RHB2")]
 return tuple(Spec(*x, ("D9","C1","C'1") if x[1]=="p20" else (x[6],)) for x in r)
SPECS=_specs()
def _req(url,method="GET"):
 with urlopen(Request(url,method=method),timeout=60) as z:return {k.lower():v for k,v in z.headers.items()},(z.read() if method=="GET" else b"")
def _atomic(p,x):
 t=p.with_suffix(p.suffix+".tmp");t.write_text(json.dumps(x,indent=2),encoding="utf-8");t.replace(p)
def _head(path):
 h,_=_req(f"{S3}/{quote(path)}","HEAD");return {k:h[k] for k in ("x-amz-version-id","etag","content-length","accept-ranges")}
def _header(blob,expect):
 s=blob.decode("utf-8-sig"); f=dict(x.split("=",1) for x in s.splitlines() if "=" in x)
 if f.get("DataFormat")!="BINARY" or f.get("DataOrientation")!="MULTIPLEXED" or f.get("BinaryFormat")!="IEEE_FLOAT_32" or f.get("UseBigEndianOrder","NO")!="NO" or f.get("DataFile")!=Path(expect).name: raise ValueError("STOP_SOURCE_IDENTITY: BrainVision format")
 ch=[]
 for i in range(1,int(f["NumberOfChannels"])+1):
  q=f[f"Ch{i}"].split(","); unit=q[3] if len(q)>3 and q[3] else "µV"; scale={"µV":1,"uV":1,"mV":1000,"V":1e6}.get(unit)
  if scale is None: raise ValueError("STOP_SOURCE_IDENTITY: unit")
  ch.append({"name":q[0],"resolution":float(q[2]),"unit":unit,"to_microvolts":float(q[2])*scale})
 return {"sha256":hashlib.sha256(blob).hexdigest(),"nchan":len(ch),"sampling_interval_us":float(f["SamplingInterval"]),"channels":ch,"little_endian":True}
def build_lock():
 rows=[]
 for sp in SPECS:
  _,ptr=_req(f"{RAW}/{quote(sp.eeg)}");m=re.search(rb"SHA256E-s(\d+)--([0-9a-f]{64})\.eeg",ptr)
  if not m: raise ValueError("STOP_SOURCE_IDENTITY: annex")
  eh=_head(sp.eeg); vh=_head(sp.vhdr); hg,b=_req(f"{S3}/{quote(sp.vhdr)}?versionId={quote(vh['x-amz-version-id'])}")
  if hg.get("etag")!=vh["etag"] or hg.get("x-amz-version-id")!=vh["x-amz-version-id"]: raise ValueError("STOP_SOURCE_IDENTITY: vhdr version")
  hd=_header(b,sp.eeg); names=[x["name"] for x in hd["channels"]]; sel=sp.qc+(sp.bipolar,)
  if any(x not in names for x in sel) or hd["nchan"]!=sp.nchan or int(m[1])!=4*sp.nchan*sp.blocks*N or int(eh["content-length"])!=int(m[1]): raise ValueError("STOP_SOURCE_IDENTITY: aperture")
  rows.append(asdict(sp)|{"annex_sha256":m[2].decode(),"annex_size":int(m[1]),"eeg":eh,"vhdr":vh|hd,"qc_indices":[names.index(x) for x in sp.qc],"bipolar_index":names.index(sp.bipolar),"endpoint_index":names.index(sp.clinical)})
 return {"status":"SOURCE_LOCK_PASS","commit":COMMIT,"fs":FS,"masks":{k:v.tolist() for k,v in MASKS.items()},"static_receipt_sha256":STATIC_RECEIPT_SHA256,"records":rows}
def validate_lock(x):
 if x.get("status")!="SOURCE_LOCK_PASS" or x.get("commit")!=COMMIT or x.get("fs")!=FS or x.get("masks")!={k:v.tolist() for k,v in MASKS.items()} or len(x.get("records",[]))!=18: raise ValueError("STOP_SOURCE_IDENTITY: lock")
 keys={(r["protocol"],r["subject"],r["phase"]) for r in x["records"]}
 if keys!={(s.protocol,s.subject,s.phase) for s in SPECS}: raise ValueError("STOP_SOURCE_IDENTITY: keys")
def _verify_prereqs(lock_bytes):
 if hashlib.sha256(lock_bytes).hexdigest()!=SOURCE_LOCK_SHA256: raise ValueError("STOP_SOURCE_IDENTITY: frozen lock hash")
 if hashlib.sha256((RUN/"artifacts/author-code-static-receipt.md").read_bytes()).hexdigest()!=STATIC_RECEIPT_SHA256: raise ValueError("AUTHOR_QC_CALL_AMBIGUITY")
 lock=json.loads(lock_bytes);validate_lock(lock);return lock
def default_loader(sp,r):
 """Full-object, version-pinned loader; never range-reads or persists voltage."""
 url=f"{S3}/{quote(sp.eeg)}?versionId={quote(r['eeg']['x-amz-version-id'])}"; digest=hashlib.sha256(); chunks=[]
 with urlopen(Request(url),timeout=120) as z:
  h={k.lower():v for k,v in z.headers.items()}
  if h.get("x-amz-version-id")!=r["eeg"]["x-amz-version-id"] or h.get("etag")!=r["eeg"]["etag"] or h.get("content-length")!=str(r["annex_size"]):raise ValueError("STOP_SOURCE_IDENTITY: GET headers")
  while b:=z.read(1024*1024):digest.update(b);chunks.append(b)
 raw=bytearray().join(chunks); del chunks
 if len(raw)!=r["annex_size"] or digest.hexdigest()!=r["annex_sha256"]:raise ValueError("STOP_SOURCE_IDENTITY: digest")
 observed=len(raw); a=np.frombuffer(raw,dtype="<f4").reshape(-1,sp.nchan).T; q=np.array(r["qc_indices"]); bi=r["bipolar_index"]; scales=np.array([r["vhdr"]["channels"][i]["to_microvolts"] for i in q]); qc=(a[q].reshape(len(q),sp.blocks,N).transpose(1,0,2)*scales[None,:,None]).copy(); endpoint=qc[:,0].copy(); bipolar=(a[r["endpoint_index"]].reshape(sp.blocks,N)*r["vhdr"]["channels"][r["endpoint_index"]]["to_microvolts"]-a[bi].reshape(sp.blocks,N)*r["vhdr"]["channels"][bi]["to_microvolts"]).copy(); del a,raw; return qc,endpoint,bipolar,{"expected_sha256":r["annex_sha256"],"observed_sha256":digest.hexdigest(),"expected_size":r["annex_size"],"observed_size":observed,"version_id":h["x-amz-version-id"],"etag":h["etag"]}
def run_raw_cli(lock_path,progress_path,qc_result_path,result_path,loader_factory=lambda:default_loader,attempt=None):
 if any(p.exists() for p in (progress_path,qc_result_path,result_path)): raise ValueError("IMPLEMENTATION_INVALID: prior transaction")
 b=lock_path.read_bytes(); lock=_verify_prereqs(b); return (run_attempt1 if attempt is None else attempt)(lock,hashlib.sha256(b).hexdigest(),progress_path,qc_result_path,result_path,loader_factory())
def author_qc(trials,subject):
 """trials: trial x selected-QC-channel x 1000; author-order, prebaseline QC."""
 if trials.ndim!=3 or trials.shape[2]!=N: raise ValueError("IMPLEMENTATION_INVALID")
 x=trials[:,:,MASKS["first999"]].astype(float); initial_nonfinite=~np.isfinite(x).all(2); x=np.nan_to_num(x,nan=0.,posinf=0.,neginf=0.)
 t=AUTHOR_TIME[MASKS["first999"]]; A=np.stack([np.ones(999),*[q for f in (60,120,180) for q in (np.sin(2*np.pi*f*t),np.cos(2*np.pi*f*t))]],1); b=np.linalg.lstsq(A,x.reshape(-1,999).T,rcond=None)[0]; x=x-(A@b).T.reshape(x.shape)+b[0].reshape(x.shape[:2])[...,None]
 if subject=="p17": x=filtfilt(*butter(10,80,fs=FS),x,axis=2)
 x=x[:,:,MASKS["latency"]]; amp=np.max(np.abs(x[:,:, (AUTHOR_TIME[MASKS["latency"]]> .05)|(AUTHOR_TIME[MASKS["latency"]]<-.05)]),2)>=500; kur=kurtosis(x[:,:,AUTHOR_TIME[MASKS["latency"]]>.05],axis=2,fisher=False,bias=False)>=5; valid=~initial_nonfinite.any(1); xv=x[valid]; sd=xv.std(0,ddof=1); z=np.divide(xv-xv.mean(0),sd,out=np.zeros_like(xv),where=sd!=0); zz=np.zeros(x.shape[:2],bool);zz[valid]=np.any(abs(z)>5,2); non=initial_nonfinite; bad=amp|kur|zz|non; return x,bad.any(1),{"amplitude":int(amp.sum()),"kurtosis":int(kur.sum()),"zscore":int(zz.sum()),"nonfinite":int(non.sum())}
def _p2p(x,mask): return float(np.ptp(x[mask]))
def _endpoint(clean):
 # clean: trial x latency samples; latency global masks are shifted by 50.
 offs={k:v-50 for k,v in MASKS.items() if k in ("baseline","early","late","prestim")}
 y=clean-clean[:,offs["baseline"]].mean(1,keepdims=True); mean=y.mean(0)
 return {"mean_waveform_microvolts":mean.tolist(),"trial_p2p_microvolts":{k:np.ptp(y[:,v],axis=1).tolist() for k,v in offs.items() if k!="baseline"},"mean_p2p_microvolts":{k:_p2p(mean,v) for k,v in offs.items() if k!="baseline"}}
def _finish(result,progress_path,result_path):
 _atomic(result_path,result); p=json.loads(progress_path.read_text(encoding="utf-8"));p["status"]="RAW_COMPLETE";p["raw_result_sha256"]=hashlib.sha256(result_path.read_bytes()).hexdigest();_atomic(progress_path,p)
def _boot(ts,pb,draws=65536,seed=20260825):
 rng=np.random.Generator(np.random.PCG64(seed)); w=rng.exponential(size=(draws,7)); ix={n:i for i,n in enumerate(("p16","p17","p18","p19","p20","UC004","UC005"))}
 a=w[:,[ix[x] for x in ("p16","p17","p18","p19")]]; b=w[:,[ix[x] for x in ("p17","p19","p20","UC004","UC005")]]; d=(a@ts/a.sum(1))-(b@pb/b.sum(1)); return [float(np.quantile(d,.025)),float(np.quantile(d,.975)),float((d>0).mean())]
def _loo(ts,pb):
 names=("p16","p17","p18","p19","p20","UC004","UC005"); ta=("p16","p17","p18","p19");pa=("p17","p19","p20","UC004","UC005")
 return {n:float(ts[[i for i,x in enumerate(ta) if x!=n]].mean()-pb[[i for i,x in enumerate(pa) if x!=n]].mean()) for n in names}
def _lattice(a):
 c=a["clinical"]["late"];b=a["bipolar"]["late"]; flags=[]
 if c["D"]<=0:return {"same_data_status":"SAME_DATA_REANALYSIS_NOT_SUPPORTED","flags":["CLINICAL_DIRECTION_NONPOSITIVE"],"published_model_status":"PUBLISHED_MODEL_ENGINE_UNAVAILABLE","estimand_discordance":"UNASSESSABLE_MODEL_ENGINE_UNAVAILABLE"}
 if c["bootstrap"][0]<=0:flags.append("CI_LIMITED")
 if b["D"]<=0 or b["bootstrap"][0]<=0:flags.append("REFERENCE_SENSITIVE_OR_UNCERTAIN")
 if c["paired_p17_p19"]<=0:flags.append("PAIRED_SENSITIVITY_FAIL")
 if a["clinical"]["prestim"]["bootstrap"][0]>0:flags.append("BASELINE_ARTIFACT_CONCERN")
 if any(x<=0 for x in c["loo"].values()):flags.append("PARTICIPANT_SENSITIVE")
 return {"same_data_status":"SAME_DATA_REANALYSIS_REFERENCE_ROBUST_SUPPORT" if not flags else "SAME_DATA_REANALYSIS_SUPPORT_SENSITIVITY_LIMITED","flags":flags,"published_model_status":"PUBLISHED_MODEL_ENGINE_UNAVAILABLE","estimand_discordance":"UNASSESSABLE_MODEL_ENGINE_UNAVAILABLE"}
def aggregate(files):
 by={(x["protocol"],x["subject"],x["phase"]):x for x in files}; out={}
 for ref in ("clinical","bipolar"):
  out[ref]={}
  for win in ("early","late","prestim"):
   ts=np.array([by[("TS",s,"post")][ref]["mean_p2p_microvolts"][win]-by[("TS",s,"pre")][ref]["mean_p2p_microvolts"][win] for s in ("p16","p17","p18","p19")]);pb=np.array([by[("PB",s,"post")][ref]["mean_p2p_microvolts"][win]-by[("PB",s,"pre")][ref]["mean_p2p_microvolts"][win] for s in ("p17","p19","p20","UC004","UC005")]);out[ref][win]={"ts_deltas":ts.tolist(),"pb_deltas":pb.tolist(),"D":float(ts.mean()-pb.mean()),"bootstrap":_boot(ts,pb),"loo":_loo(ts,pb),"paired_p17_p19":float((ts[1]+ts[3]-pb[0]-pb[1])/2)}
 out["status_lattice"]=_lattice(out);return out
def run_attempt1(lock,lock_sha,progress_path,qc_result_path,result_path,loader):
 """Injectable static one-shot: loader(spec,record)->(qc,endpoint,bipolar,integrity)."""
 if any(p.exists() for p in (progress_path,qc_result_path,result_path)): raise ValueError("IMPLEMENTATION_INVALID: prior transaction")
 validate_lock(lock)
 progress={"status":"RAW_IN_PROGRESS","attempt_id":"ATTEMPT1","source_lock_sha256":lock_sha,"completed_files":[]};_atomic(progress_path,progress)
 by={(r["protocol"],r["subject"],r["phase"]):r for r in lock["records"]}; memory=[]; failed=False
 for sp in SPECS:
  try: qc,endpoint,bipolar,integrity=loader(sp,by[(sp.protocol,sp.subject,sp.phase)])
  except Exception as e:
   progress|={"status":"SOURCE_STOP","error":f"{type(e).__name__}: {e}"};_atomic(progress_path,progress);return progress
  try: qx,bad,reasons=author_qc(qc,sp.subject); bx,bbad,breasons=author_qc(bipolar[:,None,:],sp.subject)
  except Exception as e:
   progress|={"status":"IMPLEMENTATION_STOP","error":f"{type(e).__name__}: {e}"};_atomic(progress_path,progress);return progress
  counts={"clinical_qc_clean":int((~bad).sum()),"bipolar_clean":int((~bbad).sum()),"clinical_exclusion_reasons":reasons,"bipolar_exclusion_reasons":breasons}
  progress["completed_files"].append({"protocol":sp.protocol,"subject":sp.subject,"phase":sp.phase,"task":sp.task,"integrity":integrity,"qc":counts});_atomic(progress_path,progress)
  failed |= min(counts["clinical_qc_clean"],counts["bipolar_clean"])<20
  # Endpoint is always the identically preprocessed first frozen QC channel.
  if by[(sp.protocol,sp.subject,sp.phase)]["endpoint_index"]!=by[(sp.protocol,sp.subject,sp.phase)]["qc_indices"][0]: raise ValueError("STOP_MEASUREMENT_APERTURE: endpoint/QC order")
  memory.append((sp,qx[:,0],~bad,bx[:,0],~bbad))
 if failed:
  qc={"status":"QC_STOP_MIN20","attempt_id":"ATTEMPT1","source_lock_sha256":lock_sha,"counts":[x["qc"] for x in progress["completed_files"]],"integrity":[x["integrity"] for x in progress["completed_files"]]};_atomic(qc_result_path,qc);progress["status"]="QC_STOP_MIN20";_atomic(progress_path,progress);return qc
 files=[]
 for sp,endpoint,keep,bx,bkeep in memory:
  files.append({"protocol":sp.protocol,"subject":sp.subject,"phase":sp.phase,"clinical":_endpoint(endpoint[keep]),"bipolar":_endpoint(bx[bkeep])})
 try: result={"status":"RAW_COMPLETE","attempt_id":"ATTEMPT1","source_lock_sha256":lock_sha,"model_lane":"PUBLISHED_MODEL_ENGINE_UNAVAILABLE","files":files,"analysis":aggregate(files)};_finish(result,progress_path,result_path);return result
 except Exception as e:
  progress|={"status":"IMPLEMENTATION_STOP","error":f"{type(e).__name__}: {e}"};_atomic(progress_path,progress);return progress
def main(argv=None,loader=default_loader):
 p=argparse.ArgumentParser();p.add_argument("stage",choices=("source-lock","raw-one-shot"));p.add_argument("--lock",type=Path,default=RUN/"artifacts/source_lock.json");p.add_argument("--progress",type=Path,default=RUN/"artifacts/raw_progress.json");p.add_argument("--qc-result",type=Path,default=RUN/"artifacts/qc_result.json");p.add_argument("--result",type=Path,default=RUN/"artifacts/raw_result.json");a=p.parse_args(argv)
 if a.stage=="source-lock":q=build_lock();_atomic(a.lock,q);print(q["status"]);return
 out=run_raw_cli(a.lock,a.progress,a.qc_result,a.result,lambda:loader);print(out["status"])
if __name__=="__main__":main()
