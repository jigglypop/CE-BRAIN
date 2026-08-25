"""HPC5 corrected-clock, dual-implementation author-intended recheck.

This module deliberately reuses only HPC2's frozen source specifications and
version-pinned full-object loader.  Its clock, QC, endpoint and aggregation
are defined here; no predecessor analysis function is called.
"""
from __future__ import annotations
import argparse, hashlib, importlib.util, json, sys
from pathlib import Path
import numpy as np
from scipy.signal import butter, filtfilt, sosfiltfilt
from scipy.stats import kurtosis

SOURCE_MODULE=Path("examples/brain/ba_obs_hpc2_author_qc_reanalysis.py")
SOURCE_MODULE_SHA256="8e9358ea72217b4f0d48f96d174ec506f3b2faf4b55cb2d2ebcc3248a93fb85c"
_p=importlib.util.spec_from_file_location("hpc5_source",SOURCE_MODULE)
source=importlib.util.module_from_spec(_p);sys.modules["hpc5_source"]=source;assert _p.loader;_p.loader.exec_module(source)
SPECS=source.SPECS; LOADER=source.default_loader
RUN=Path("_workspace/ce/brain-human-hippocampal-theta-author-intended-recheck-20260825")
LOCK=RUN/"artifacts/analysis_lock.json"; SOURCE_LOCK=Path("_workspace/ce/brain-human-hippocampal-theta-author-qc-reanalysis-20260825/artifacts/source_lock.json")
STATIC=Path("_workspace/ce/brain-human-hippocampal-theta-author-qc-reanalysis-20260825/artifacts/author-code-static-receipt.md")
H4QC=Path("_workspace/ce/brain-human-hippocampal-theta-receipt-validator-20260825/artifacts/qc_result.json")
H4PROGRESS=Path("_workspace/ce/brain-human-hippocampal-theta-receipt-validator-20260825/artifacts/raw_progress.json")
DOCS={"contract_sha256":RUN/"00-contract.md","sources_sha256":RUN/"10-sources.md","math_sha256":RUN/"11-math.md","routes_sha256":RUN/"12-routes.md"}
ANALYSIS_LOCK_SHA256="5cce4a71f03090793ed21d8316cbf8fc0b9b4403ae077e331963d7c1cda2e470"
FS=499.5; N=1000; TIME=np.arange(N)/FS-.5
IX={"first999":np.arange(999),"latency":np.arange(50,650),"amp":np.r_[np.arange(50,225),np.arange(275,650)],"kurt":np.arange(275,650),"baseline":np.arange(225,246),"early":np.arange(258,275),"late":np.arange(275,375),"prestim":np.arange(100,200)}
EXPECTED={"source_lock_sha256":"66cac4202971cabb0838b3ddb93710c160c88325133411f58c8595c89e7c5810","static_receipt_sha256":"20008069771a37a7e7669e996d0bb799cabed1ad09e0e010c6c1f0ec33b93496","hpc4_qc_sha256":"5f9ce77000613de4761d24519a6b7c1309fbea55d465739aafbc2a7189038e17","hpc4_progress_sha256":"5b350ac0b568888ac6a8416f0084f04fad83242500ffbfd40451bb605e065e87","contract_sha256":"8a2675fe25199dfe3320bca67046f0777ef738470e9edb105e588a47d4b3eec0","sources_sha256":"2a500ae27c08f2985e0c685dc11e39f9dd583922c4b86a7a342efbf9cd9b0a29","math_sha256":"2b430c1af33151f9bc58af173eb57e808dfcf654d5f3cbd886837331e0bd5f27","routes_sha256":"f23422bd4fcd684d07d9a6474fa1869626d4dcca8b0a4ca048e47687999bc17d"}

def _bytes(x): return json.dumps(x,indent=2,allow_nan=False).encode()
def _write(p,x):
 p.parent.mkdir(parents=True,exist_ok=True);t=p.with_suffix(p.suffix+".tmp");t.write_bytes(_bytes(x));t.replace(p)
def _read(p): return json.loads(p.read_text(encoding="utf-8"),parse_constant=lambda x:(_ for _ in ()).throw(ValueError(x)))
def _sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def _mask_hash(m): return hashlib.sha256(np.asarray(m,dtype=np.uint8).tobytes()).hexdigest()
def _hex64(x): return isinstance(x,str) and len(x)==64 and all(c in "0123456789abcdef" for c in x)
def _finite(x):
 if isinstance(x,dict): return all(_finite(v) for v in x.values())
 if isinstance(x,list): return all(_finite(v) for v in x)
 return type(x) not in (float,np.float64) or bool(np.isfinite(x))
def _records():
 x=_read(SOURCE_LOCK);source.validate_lock(x);return {(r["protocol"],r["subject"],r["phase"]):r for r in x["records"]}
def _check_lock():
 x=_read(LOCK)
 if _sha(SOURCE_MODULE)!=SOURCE_MODULE_SHA256: raise ValueError("STOP_SOURCE_IDENTITY: source loader code")
 if _sha(LOCK)!=ANALYSIS_LOCK_SHA256 or x.get("schema")!="HPC5_ANALYSIS_LOCK_V2" or x.get("parameters",{}).get("time")!="j/499.5-0.5": raise ValueError("IMPLEMENTATION_INVALID: analysis lock")
 if set(x)!={"schema","hashes","parameters","stages","hpc4_old_grid"} or set(x["hashes"])!={"source_lock_sha256","static_receipt_sha256","hpc4_qc_sha256","contract_sha256","sources_sha256","math_sha256","routes_sha256","hpc4_progress_sha256"}:raise ValueError("IMPLEMENTATION_INVALID: analysis lock schema")
 for p,k in ((SOURCE_LOCK,"source_lock_sha256"),(STATIC,"static_receipt_sha256"),(H4QC,"hpc4_qc_sha256"),(H4PROGRESS,"hpc4_progress_sha256"),*[(v,k) for k,v in DOCS.items()]):
  if _sha(p)!=EXPECTED[k] or x.get("hashes",{}).get(k)!=EXPECTED[k]: raise ValueError("STOP_SOURCE_IDENTITY: lock binding")
 if x["stages"]!={"recheck":{"attempt_id":"QC_RECHECK1","targets":[["TS","p17","post","eppost"],["PB","p17","pre","epcontrolpre"]]},"endpoint":{"attempt_id":"ENDPOINT1","targets":18}}:raise ValueError("IMPLEMENTATION_INVALID: stage lock")
 return x

class _SourceStageError(RuntimeError):
 """A failure confined to the frozen source/loader/decode boundary."""

def _dft_a(x):
 t=TIME[IX["first999"]];A=np.stack([np.ones(999),*[z for f in (60,120,180) for z in (np.sin(2*np.pi*f*t),np.cos(2*np.pi*f*t))]],1)
 z=np.asarray(x,float)[...,:999];c=np.linalg.lstsq(A,z.reshape(-1,999).T,rcond=None)[0];return z-(A@c).T.reshape(z.shape)+c[0].reshape(z.shape[:-1])[...,None]
def _dft_b(x):
 z=np.asarray(x,float)[...,:999];n=np.arange(999);out=z.copy()
 for f in (60,120,180):
  e=np.exp(-2j*np.pi*f*n/FS);coef=np.tensordot(z,e,axes=(-1,0))/999
  out-=2*np.real(coef[...,None]*np.exp(2j*np.pi*f*n/FS))
 return out
def _filter(x,subject,kind):
 if subject!="p17": return x
 return filtfilt(*butter(10,80,fs=FS),x,axis=-1) if kind=="A" else sosfiltfilt(butter(10,80,fs=FS,output="sos"),x,axis=-1)
def _qc(x,subject,kind):
 x=np.asarray(x,float)
 if x.ndim!=3 or x.shape[-1]!=N: raise ValueError("IMPLEMENTATION_INVALID: QC shape")
 non=~np.isfinite(x).all((1,2));z=np.nan_to_num(x,nan=0.,posinf=0.,neginf=0.)
 y=_filter(_dft_a(z) if kind=="A" else _dft_b(z),subject,kind);lat=y[...,IX["latency"]]
 amp=np.max(np.abs(y[...,IX["amp"]]),axis=-1)>=500
 kur=kurtosis(y[...,IX["kurt"]],axis=-1,fisher=False,bias=False)>=5
 valid=~non; zz=np.zeros(x.shape[:2],bool)
 if valid.any():
  q=lat[valid];sd=q.std(0,ddof=1);v=np.divide(q-q.mean(0),sd,out=np.zeros_like(q),where=sd!=0);zz[valid]=np.any(abs(v)>5,axis=-1)
 channel={"amplitude":amp,"kurtosis":kur,"zscore":zz,"nonfinite":np.repeat(non[:,None],x.shape[1],axis=1)};reasons={k:v.any(1) for k,v in channel.items()};bad=np.logical_or.reduce(list(reasons.values()))
 diag={"reason_mask_sha256":{k:_mask_hash(v) for k,v in reasons.items()},"reason_channel_mask_sha256":{k:_mask_hash(v) for k,v in channel.items()},"reason_counts":{k:int(v.sum()) for k,v in reasons.items()},"reason_channel_counts":{k:int(v.sum()) for k,v in channel.items()},"trial_union_mask_sha256":_mask_hash(bad),"trial_union_count":int(bad.sum()),"trial_max_abs_amplitude_microvolts":np.max(np.abs(y[...,IX["amp"]]),axis=(1,2)).tolist(),"trial_amplitude_margin_microvolts":(500-np.max(np.abs(y[...,IX["amp"]]),axis=(1,2))).tolist()}
 return y,bad,diag,float(500-np.max(np.abs(y[...,IX["amp"]])))
def dual_qc(x,subject):
 a,ab,ad,am=_qc(x,subject,"A");b,bb,bd,bm=_qc(x,subject,"B")
 parity=("reason_mask_sha256","reason_channel_mask_sha256","reason_counts","reason_channel_counts","trial_union_mask_sha256","trial_union_count")
 if np.max(np.abs(a-b))>1e-6 or not np.array_equal(ab,bb) or any(ad[k]!=bd[k] for k in parity): raise ValueError("QC_IMPLEMENTATION_DISAGREEMENT")
 return a,ab,{"keep_mask_sha256":_mask_hash(~ab),**ad,"amplitude_margin_microvolts":am,"max_abs_path_difference_microvolts":float(np.max(np.abs(a-b)))}
def _file_row(sp,rec,loader):
 try:
  q,e,b,integrity=loader(sp,rec)
  q=np.asarray(q);e=np.asarray(e);b=np.asarray(b)
  if q.shape!=(sp.blocks,len(sp.qc),N) or e.shape!=(sp.blocks,N) or b.shape!=(sp.blocks,N) or not np.array_equal(e,q[:,0],equal_nan=True): raise ValueError("STOP_SOURCE_IDENTITY: loader shape")
  expected={"expected_sha256":rec["annex_sha256"],"observed_sha256":rec["annex_sha256"],"expected_size":rec["annex_size"],"observed_size":rec["annex_size"],"version_id":rec["eeg"]["x-amz-version-id"],"etag":rec["eeg"]["etag"]}
  if integrity!=expected:raise ValueError("STOP_SOURCE_IDENTITY: loader integrity")
 except Exception as exc:
  raise _SourceStageError(f"{type(exc).__name__}: {exc}") from exc
 cy,ck,cq=dual_qc(q,sp.subject);by,bk,bq=dual_qc(b[:,None,:],sp.subject)
 row={"protocol":sp.protocol,"subject":sp.subject,"phase":sp.phase,"task":sp.task,"integrity":integrity,"clinical":{"clean_count":int((~ck).sum()),**cq},"bipolar":{"clean_count":int((~bk).sum()),**bq}}
 old=_check_lock()["hpc4_old_grid"].get(f"{sp.protocol}/{sp.subject}/{sp.phase}")
 if old:row["hpc4_old_grid"]=old
 return row,cy[:,0],ck,by[:,0],bk

def _endpoint(x,keep):
 if not keep.any(): raise ValueError("CLINICAL_PAIR_UNAVAILABLE")
 y=x[keep];y=y-y[:,IX["baseline"]].mean(1,keepdims=True);mean=y.mean(0);wins=("early","late","prestim")
 return {"mean_waveform_microvolts":mean.tolist(),"trialwise_p2p_microvolts":{w:np.ptp(y[:,IX[w]],axis=1).tolist() for w in wins},"mean_waveform_p2p_microvolts":{w:float(np.ptp(mean[IX[w]])) for w in wins}}
def _pmean(v): return {w:float(np.mean(v["trialwise_p2p_microvolts"][w])) for w in ("early","late","prestim")}
def _boot(ts,pb):
 r=np.random.Generator(np.random.PCG64(20260825));w=r.exponential(size=(65536,7));a=w[:,:4];b=w[:,[1,3,4,5,6]];d=a@ts/a.sum(1)-b@pb/b.sum(1);return [float(np.quantile(d,.025)),float(np.quantile(d,.975)),float((d>0).mean())]
def _loo(ts,pb):
 names=("p16","p17","p18","p19","p20","UC004","UC005");ta=("p16","p17","p18","p19");pa=("p17","p19","p20","UC004","UC005");out={}
 for n in names:
  a=np.asarray([v for v,s in zip(ts,ta) if s!=n]);b=np.asarray([v for v,s in zip(pb,pa) if s!=n]);out[n]=float(a.mean()-b.mean())
 return out
def _metric(ts,pb): return {"ts_deltas":ts.tolist(),"pb_deltas":pb.tolist(),"D":float(ts.mean()-pb.mean()),"bootstrap":_boot(ts,pb),"loo":_loo(ts,pb),"paired_p17_p19":float((ts[1]+ts[3]-pb[0]-pb[1])/2)}
def _wave(v,w): return float(np.ptp(np.asarray(v["mean_waveform_microvolts"])[IX[w]]))
def aggregate(files,bipolar=True):
 d={(x["protocol"],x["subject"],x["phase"]):x for x in files};out={}
 for ref in (("clinical",) if not bipolar else ("clinical","bipolar")):
  out[ref]={}
  for estimand,fn in (("trial_mean",lambda v,w:_pmean(v)[w]),("mean_waveform",_wave)):
   out[ref][estimand]={}
   for w in ("early","late","prestim"):
    ts=np.array([fn(d[("TS",s,"post")][ref],w)-fn(d[("TS",s,"pre")][ref],w) for s in ("p16","p17","p18","p19")]);pb=np.array([fn(d[("PB",s,"post")][ref],w)-fn(d[("PB",s,"pre")][ref],w) for s in ("p17","p19","p20","UC004","UC005")]);out[ref][estimand][w]=_metric(ts,pb)
 return out

def _no_endpoint(x):
 bad=("endpoint","waveform","p2p","bootstrap","loo","analysis","delta","lattice")
 if isinstance(x,dict):return any(any(b in k.lower() for b in bad) or _no_endpoint(v) for k,v in x.items())
 return isinstance(x,list) and any(_no_endpoint(v) for v in x)
def recheck_ok(x):
 if not(isinstance(x,dict) and set(x)=={"schema","status","attempt_id","analysis_lock_sha256","records"} and x["schema"]=="HPC5_QC_RECHECK1_V1" and x["status"]=="QC_RECHECK1" and x["attempt_id"]=="QC_RECHECK1" and x["analysis_lock_sha256"]==ANALYSIS_LOCK_SHA256 and isinstance(x["records"],list) and len(x["records"])==2 and not _no_endpoint(x["records"]) and _finite(x)):return False
 try: frozen=_records()
 except Exception:return False
 want=[("TS","p17","post","eppost"),("PB","p17","pre","epcontrolpre")]
 for row,ident in zip(x["records"],want):
  sp=next((s for s in SPECS if (s.protocol,s.subject,s.phase,s.task)==ident),None)
  if sp is None or not _row_ok(row,sp,frozen[ident[:3]],need_old=True):return False
 return True
def _same(a,b):
 if type(a) in (int,float) and type(b) in (int,float):return type(a) is not bool and type(b) is not bool and bool(np.isclose(a,b,rtol=1e-10,atol=1e-8))
 if type(a) is not type(b):return False
 if isinstance(a,dict):return set(a)==set(b) and all(_same(a[k],b[k]) for k in a)
 if isinstance(a,list):return len(a)==len(b) and all(_same(u,v) for u,v in zip(a,b))
 return a==b
def _endpoint_ok(x,n):
 if not(isinstance(x,dict) and set(x)=={"mean_waveform_microvolts","trialwise_p2p_microvolts","mean_waveform_p2p_microvolts"}):return False
 w=x["mean_waveform_microvolts"]
 if not(isinstance(w,list) and len(w)==999 and all(type(v) in (int,float) and type(v) is not bool and np.isfinite(v) for v in w)):return False
 for k in ("early","late","prestim"):
  q=x["trialwise_p2p_microvolts"].get(k);m=x["mean_waveform_p2p_microvolts"].get(k)
  if not(isinstance(q,list) and len(q)==n and all(type(v) in (int,float) and type(v) is not bool and np.isfinite(v) and v>=0 for v in q) and type(m) in (int,float) and type(m) is not bool and np.isfinite(m) and np.isclose(m,np.ptp(np.asarray(w)[IX[k]]),rtol=1e-10,atol=1e-8)):return False
 return set(x["trialwise_p2p_microvolts"])==set(x["mean_waveform_p2p_microvolts"])=={"early","late","prestim"}
def _row_ok(row,sp,fr,need_old=False):
 oldkey=f"{sp.protocol}/{sp.subject}/{sp.phase}" in _check_lock()["hpc4_old_grid"]
 keys={"protocol","subject","phase","task","integrity","clinical","bipolar"}|({"hpc4_old_grid"} if (need_old or oldkey) else set())
 if not(isinstance(row,dict) and set(row)==keys and (row["protocol"],row["subject"],row["phase"],row["task"])==(sp.protocol,sp.subject,sp.phase,sp.task)):return False
 i=row["integrity"]
 if i!={"expected_sha256":fr["annex_sha256"],"observed_sha256":fr["annex_sha256"],"expected_size":fr["annex_size"],"observed_size":fr["annex_size"],"version_id":fr["eeg"]["x-amz-version-id"],"etag":fr["eeg"]["etag"]}:return False
 dkeys={"clean_count","keep_mask_sha256","reason_mask_sha256","reason_channel_mask_sha256","reason_counts","reason_channel_counts","trial_union_mask_sha256","trial_union_count","trial_max_abs_amplitude_microvolts","trial_amplitude_margin_microvolts","amplitude_margin_microvolts","max_abs_path_difference_microvolts"}
 for ref,nch in (("clinical",len(sp.qc)),("bipolar",1)):
  q=row[ref]
  if not(isinstance(q,dict) and set(q)==dkeys and type(q["clean_count"]) is int and 0<=q["clean_count"]<=sp.blocks and type(q["trial_union_count"]) is int and q["trial_union_count"]==sp.blocks-q["clean_count"]):return False
  reasons={"amplitude","kurtosis","zscore","nonfinite"}
  if not(all(_hex64(q[k]) for k in ("keep_mask_sha256","trial_union_mask_sha256")) and all(isinstance(q[k],dict) and set(q[k])==reasons and all(_hex64(v) for v in q[k].values()) for k in ("reason_mask_sha256","reason_channel_mask_sha256"))):return False
  if not(isinstance(q["reason_counts"],dict) and set(q["reason_counts"])==reasons and all(type(v) is int and 0<=v<=sp.blocks for v in q["reason_counts"].values())):return False
  if not(isinstance(q["reason_channel_counts"],dict) and set(q["reason_channel_counts"])==reasons and all(type(v) is int and 0<=v<=sp.blocks*nch for v in q["reason_channel_counts"].values())):return False
  if any(q["reason_channel_counts"][k]<q["reason_counts"][k] or q["reason_channel_counts"][k]>nch*q["reason_counts"][k] for k in reasons):return False
  if q["trial_union_count"]<max(q["reason_counts"].values()) or q["trial_union_count"]>min(sp.blocks,sum(q["reason_counts"].values())):return False
  if not(all(isinstance(q[k],list) and len(q[k])==sp.blocks and all(type(v) in (int,float) and type(v) is not bool and np.isfinite(v) for v in q[k]) for k in ("trial_max_abs_amplitude_microvolts","trial_amplitude_margin_microvolts"))):return False
  maxima=np.asarray(q["trial_max_abs_amplitude_microvolts"],float);margins=np.asarray(q["trial_amplitude_margin_microvolts"],float)
  if np.any(maxima<0) or not np.allclose(margins,500-maxima,rtol=0,atol=1e-9) or q["reason_counts"]["amplitude"]!=int((maxima>=500).sum()):return False
  scalar_margin=q["amplitude_margin_microvolts"];path_error=q["max_abs_path_difference_microvolts"]
  if not(type(scalar_margin) in (int,float) and type(scalar_margin) is not bool and np.isfinite(scalar_margin) and np.isclose(scalar_margin,margins.min(),rtol=0,atol=1e-9)):return False
  if not(type(path_error) in (int,float) and type(path_error) is not bool and np.isfinite(path_error) and 0<=path_error<=1e-6):return False
 if (need_old or oldkey) and row["hpc4_old_grid"]!=_check_lock()["hpc4_old_grid"][f"{sp.protocol}/{sp.subject}/{sp.phase}"]:return False
 return True
def result_ok(x):
 keys={"schema","status","attempt_id","analysis_lock_sha256","model_lane","posthoc_status","primary_status","bipolar_status","records","files","analysis"}
 if not(isinstance(x,dict) and set(x)==keys and x["schema"]=="HPC5_ENDPOINT1_V1" and x["status"]=="RAW_COMPLETE" and x["attempt_id"]=="ENDPOINT1" and x["analysis_lock_sha256"]==ANALYSIS_LOCK_SHA256 and x["model_lane"]=="PUBLISHED_MODEL_ENGINE_UNAVAILABLE" and x["posthoc_status"]=="SAME_PUBLIC_DATA_POSTHOC_AUTHOR_INTENDED_EMULATION" and x["primary_status"]=="CLINICAL_AVAILABLE_CLEAN_PRIMARY" and len(x["records"])==len(x["files"])==18):return False
 try:frozen=_records()
 except Exception:return False
 seen=set();bip=x["bipolar_status"]=="BIPOLAR_SENSITIVITY_AVAILABLE"
 if x["bipolar_status"] not in ("BIPOLAR_SENSITIVITY_AVAILABLE","BIPOLAR_SENSITIVITY_UNAVAILABLE"):return False
 for row,f in zip(x["records"],x["files"]):
  ident=(f.get("protocol"),f.get("subject"),f.get("phase"));sp=next((s for s in SPECS if (s.protocol,s.subject,s.phase)==ident),None)
  if sp is None or ident in seen or not _row_ok(row,sp,frozen[ident]) or set(f)!=( {"protocol","subject","phase","clinical","bipolar"} if bip else {"protocol","subject","phase","clinical"}) or not _endpoint_ok(f["clinical"],row["clinical"]["clean_count"]):return False
  if bip and not _endpoint_ok(f["bipolar"],row["bipolar"]["clean_count"]):return False
  seen.add(ident)
 if seen!=set(frozen):return False
 return _same(x["analysis"],aggregate(x["files"],bip))
def _progress_ok(x,attempt):
 if not isinstance(x,dict) or x.get("attempt_id")!=attempt or x.get("analysis_lock_sha256")!=ANALYSIS_LOCK_SHA256 or not isinstance(x.get("completed_files"),list) or _no_endpoint(x["completed_files"]):return False
 base={"status","attempt_id","analysis_lock_sha256","completed_files"};status=x.get("status")
 if status=="IN_PROGRESS":return set(x)==base
 if status=="COMPLETE":return set(x)==base|{"receipt_sha256"} and _hex64(x["receipt_sha256"])
 if status in ("SOURCE_STOP","IMPLEMENTATION_STOP"):return set(x)==base|{"error"} and isinstance(x["error"],str) and bool(x["error"])
 return False
def _recheck_authority_ok(recheck,progress):
 try:
  if not recheck.exists() or not progress.exists():return False
  q=_read(recheck);p=_read(progress)
  return recheck_ok(q) and _progress_ok(p,"QC_RECHECK1") and p["status"]=="COMPLETE" and p["receipt_sha256"]==_sha(recheck) and _bytes(p["completed_files"])==_bytes(q["records"])
 except Exception:return False
def resolve(recheck,result,recheck_progress=None,endpoint_progress=None):
 recheck_progress=recheck_progress or recheck.with_name(recheck.stem+".progress.json");endpoint_progress=endpoint_progress or result.with_name(result.stem+".progress.json")
 if result.exists():
  try:return "RAW_COMPLETE" if result_ok(_read(result)) else "INVALID_RAW_RESULT"
  except Exception:return "INVALID_RAW_RESULT"
 if endpoint_progress and endpoint_progress.exists():
  try:
   p=_read(endpoint_progress)
   return ("INCOMPLETE_AUTHORITY" if p.get("status")=="COMPLETE" else p["status"]) if _progress_ok(p,"ENDPOINT1") else "INVALID_PROGRESS"
  except Exception:return "INVALID_PROGRESS"
 if recheck.exists():
  if _recheck_authority_ok(recheck,recheck_progress):return "QC_RECHECK1"
  if recheck_progress.exists():
   try:
    p=_read(recheck_progress)
    if _progress_ok(p,"QC_RECHECK1") and p["status"] in ("SOURCE_STOP","IMPLEMENTATION_STOP"):return p["status"]
   except Exception:pass
  return "INVALID_QC_RECHECK1"
 if recheck_progress and recheck_progress.exists():
  try:
   p=_read(recheck_progress)
   return ("INCOMPLETE_AUTHORITY" if p.get("status")=="COMPLETE" else p["status"]) if _progress_ok(p,"QC_RECHECK1") else "INVALID_PROGRESS"
  except Exception:return "INVALID_PROGRESS"
 return "RAW_IN_PROGRESS"
def _prior(*paths):
 if any(p.exists() for p in paths): raise ValueError("IMPLEMENTATION_INVALID: prior authoritative receipt")
def _terminal(progress,attempt,rows,status,exc):
 _write(progress,{"status":status,"attempt_id":attempt,"analysis_lock_sha256":ANALYSIS_LOCK_SHA256,"completed_files":rows,"error":f"{type(exc).__name__}: {exc}"})
def _begin(progress,attempt):
 try:_write(progress,{"status":"IN_PROGRESS","attempt_id":attempt,"analysis_lock_sha256":ANALYSIS_LOCK_SHA256,"completed_files":[]})
 except Exception as exc:
  try:_terminal(progress,attempt,[],"IMPLEMENTATION_STOP",exc)
  except Exception:pass
  raise
def _commit_receipt(path,value,validator):
 try:_write(path,value)
 except Exception:
  try:
   if _bytes(_read(path))==_bytes(value) and validator(_read(path)):return
  except Exception:pass
  raise
def _finalize(progress,attempt,rows,receipt):
 value={"status":"COMPLETE","attempt_id":attempt,"analysis_lock_sha256":ANALYSIS_LOCK_SHA256,"completed_files":rows,"receipt_sha256":_sha(receipt)}
 try:_write(progress,value)
 except Exception as exc:
  try:
   if _bytes(_read(progress))==_bytes(value) and _progress_ok(_read(progress),attempt):return
  except Exception:pass
  try:_terminal(progress,attempt,rows,"IMPLEMENTATION_STOP",exc)
  except Exception:pass
  raise
def recheck_one_shot(recheck,result,loader=LOADER,recheck_progress=None,endpoint_progress=None):
 recheck_progress=recheck_progress or recheck.with_name(recheck.stem+".progress.json");_prior(recheck,result,recheck_progress,endpoint_progress or result.with_name(result.stem+".progress.json"));_check_lock();records=_records();want={("TS","p17","post"),("PB","p17","pre")};rows=[];_begin(recheck_progress,"QC_RECHECK1")
 try:
  for sp in SPECS:
   key=(sp.protocol,sp.subject,sp.phase)
   if key in want:
    rows.append(_file_row(sp,records[key],loader)[0]);_write(recheck_progress,{"status":"IN_PROGRESS","attempt_id":"QC_RECHECK1","analysis_lock_sha256":ANALYSIS_LOCK_SHA256,"completed_files":rows})
  x={"schema":"HPC5_QC_RECHECK1_V1","status":"QC_RECHECK1","attempt_id":"QC_RECHECK1","analysis_lock_sha256":_sha(LOCK),"records":rows}
  if not recheck_ok(x):raise ValueError("IMPLEMENTATION_INVALID: recheck receipt")
  _commit_receipt(recheck,x,recheck_ok)
 except _SourceStageError as e:
  _terminal(recheck_progress,"QC_RECHECK1",rows,"SOURCE_STOP",e);raise
 except Exception as e:
  _terminal(recheck_progress,"QC_RECHECK1",rows,"IMPLEMENTATION_STOP",e);raise
 _finalize(recheck_progress,"QC_RECHECK1",rows,recheck);return x
def endpoint_one_shot(recheck,result,loader=LOADER,recheck_progress=None,endpoint_progress=None):
 recheck_progress=recheck_progress or recheck.with_name(recheck.stem+".progress.json")
 if not _recheck_authority_ok(recheck,recheck_progress):raise ValueError("IMPLEMENTATION_INVALID: valid QC_RECHECK1 required")
 endpoint_progress=endpoint_progress or result.with_name(result.stem+".progress.json");_prior(result,endpoint_progress);_check_lock();records=_records();rows=[];files=[];bipolar=True;qrows={(x["protocol"],x["subject"],x["phase"]):x for x in _read(recheck)["records"]};_begin(endpoint_progress,"ENDPOINT1")
 try:
  for sp in SPECS:
   row,cy,ck,by,bk=_file_row(sp,records[(sp.protocol,sp.subject,sp.phase)],loader);rows.append(row);key=(sp.protocol,sp.subject,sp.phase)
   if key in qrows and _bytes(row)!=_bytes(qrows[key]):raise ValueError("QC_RECHECK1_MISMATCH")
   if not (~ck).any(): raise ValueError("CLINICAL_PAIR_UNAVAILABLE")
   if not (~bk).any():bipolar=False
   files.append({"protocol":sp.protocol,"subject":sp.subject,"phase":sp.phase,"clinical":_endpoint(cy,~ck),"bipolar":_endpoint(by,~bk) if (~bk).any() else None});_write(endpoint_progress,{"status":"IN_PROGRESS","attempt_id":"ENDPOINT1","analysis_lock_sha256":ANALYSIS_LOCK_SHA256,"completed_files":rows})
  if not bipolar:
   for f in files:f.pop("bipolar")
  x={"schema":"HPC5_ENDPOINT1_V1","status":"RAW_COMPLETE","attempt_id":"ENDPOINT1","analysis_lock_sha256":_sha(LOCK),"model_lane":"PUBLISHED_MODEL_ENGINE_UNAVAILABLE","posthoc_status":"SAME_PUBLIC_DATA_POSTHOC_AUTHOR_INTENDED_EMULATION","primary_status":"CLINICAL_AVAILABLE_CLEAN_PRIMARY","bipolar_status":"BIPOLAR_SENSITIVITY_AVAILABLE" if bipolar else "BIPOLAR_SENSITIVITY_UNAVAILABLE","records":rows,"files":files,"analysis":aggregate(files,bipolar)}
  if not result_ok(x):raise ValueError("IMPLEMENTATION_INVALID: endpoint receipt")
  _commit_receipt(result,x,result_ok)
 except _SourceStageError as e:
  _terminal(endpoint_progress,"ENDPOINT1",rows,"SOURCE_STOP",e);raise
 except Exception as e:
  _terminal(endpoint_progress,"ENDPOINT1",rows,"IMPLEMENTATION_STOP",e);raise
 _finalize(endpoint_progress,"ENDPOINT1",rows,result);return x
def main(argv=None,loader=LOADER):
 p=argparse.ArgumentParser();p.add_argument("stage",choices=("recheck-one-shot","endpoint-one-shot","status"));p.add_argument("--recheck",type=Path,default=RUN/"artifacts/qc_recheck1.json");p.add_argument("--result",type=Path,default=RUN/"artifacts/raw_result.json");p.add_argument("--recheck-progress",type=Path,default=RUN/"artifacts/recheck_progress.json");p.add_argument("--endpoint-progress",type=Path,default=RUN/"artifacts/endpoint_progress.json");a=p.parse_args(argv)
 out=resolve(a.recheck,a.result,a.recheck_progress,a.endpoint_progress) if a.stage=="status" else (recheck_one_shot(a.recheck,a.result,loader,a.recheck_progress,a.endpoint_progress) if a.stage=="recheck-one-shot" else endpoint_one_shot(a.recheck,a.result,loader,a.recheck_progress,a.endpoint_progress));print(out if isinstance(out,str) else out["status"]);return out if isinstance(out,str) else out["status"]
if __name__=="__main__":main()
