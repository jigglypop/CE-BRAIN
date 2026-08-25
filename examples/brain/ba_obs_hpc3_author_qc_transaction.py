"""HPC3 one-shot author-QC analysis with authoritative transaction receipts."""
from __future__ import annotations
import argparse, hashlib, importlib.util, json, sys
from pathlib import Path
import numpy as np

_s=importlib.util.spec_from_file_location("hpc3_base",Path("examples/brain/ba_obs_hpc2_author_qc_reanalysis.py"));base=importlib.util.module_from_spec(_s);sys.modules["hpc3_base"]=base;assert _s.loader;_s.loader.exec_module(base)
RUN=Path("_workspace/ce/brain-human-hippocampal-theta-transaction-seal-20260825")
LOCK=Path("_workspace/ce/brain-human-hippocampal-theta-author-qc-reanalysis-20260825/artifacts/source_lock.json")
STATIC=Path("_workspace/ce/brain-human-hippocampal-theta-author-qc-reanalysis-20260825/artifacts/author-code-static-receipt.md")
LOCK_SHA=base.SOURCE_LOCK_SHA256; STATIC_SHA=base.STATIC_RECEIPT_SHA256; SPECS=base.SPECS

def _json_bytes(x): return json.dumps(x,indent=2,allow_nan=False).encode()
def _load(p): return json.loads(p.read_text(encoding="utf-8"),parse_constant=lambda x:(_ for _ in ()).throw(ValueError(x)))
def _atomic_writer(p,b):
 t=p.with_suffix(p.suffix+".tmp");t.write_bytes(b);t.replace(p)
def _exact(x,keys): return isinstance(x,dict) and set(x)==set(keys)
def _int(x,lo,hi): return type(x) is int and lo<=x<=hi
def _num(x): return type(x) in (int,float) and np.isfinite(x)
def _allfinite(x):
 if isinstance(x,dict): return all(_allfinite(v) for v in x.values())
 if isinstance(x,list): return all(_allfinite(v) for v in x)
 return not isinstance(x,float) or np.isfinite(x)
def _ids(): return {(s.protocol,s.subject,s.phase) for s in SPECS}

def _frozen_lock():
 raw=LOCK.read_bytes()
 if hashlib.sha256(raw).hexdigest()!=LOCK_SHA: raise ValueError("STOP_SOURCE_IDENTITY: frozen lock hash")
 if hashlib.sha256(STATIC.read_bytes()).hexdigest()!=STATIC_SHA: raise ValueError("STOP_SOURCE_IDENTITY: static receipt hash")
 lock=json.loads(raw,parse_constant=lambda x:(_ for _ in ()).throw(ValueError(x)));base.validate_lock(lock)
 records={(r["protocol"],r["subject"],r["phase"]):r for r in lock["records"]}
 if set(records)!=_ids() or len(records)!=18: raise ValueError("STOP_SOURCE_IDENTITY: frozen record map")
 return lock,records
def _preflight(progress,qc,result):
 if any(p.exists() for p in (progress,qc,result)): raise ValueError("IMPLEMENTATION_INVALID: prior receipt")
 lock,records=_frozen_lock();return lock,records,hashlib.sha256(LOCK.read_bytes()).hexdigest()

def _integrity_ok(x,f):
 keys=("expected_sha256","observed_sha256","expected_size","observed_size","version_id","etag")
 return _exact(x,keys) and x["expected_sha256"]==x["observed_sha256"]==f["annex_sha256"] and x["expected_size"]==x["observed_size"]==f["annex_size"] and x["version_id"]==f["eeg"]["x-amz-version-id"] and x["etag"]==f["eeg"]["etag"]
def _qc_ok(x,blocks):
 r=("amplitude","kurtosis","zscore","nonfinite");keys=("clinical_qc_clean","bipolar_clean","clinical_exclusion_reasons","bipolar_exclusion_reasons")
 return _exact(x,keys) and _int(x["clinical_qc_clean"],0,blocks) and _int(x["bipolar_clean"],0,blocks) and _exact(x["clinical_exclusion_reasons"],r) and _exact(x["bipolar_exclusion_reasons"],r) and all(_int(x[k][v],0,blocks) for k in keys[2:] for v in r)
def _records_ok(rows,minimum=None):
 _,frozen=_frozen_lock();keys=("protocol","subject","phase","task","integrity","qc")
 if not isinstance(rows,list) or len(rows)!=18:return False
 seen=set()
 for x in rows:
  if not _exact(x,keys):return False
  ident=(x["protocol"],x["subject"],x["phase"])
  if ident in seen or ident not in frozen:return False
  f=frozen[ident]
  if x["task"]!=f["task"] or not _integrity_ok(x["integrity"],f) or not _qc_ok(x["qc"],f["blocks"]):return False
  if minimum is not None and min(x["qc"]["clinical_qc_clean"],x["qc"]["bipolar_clean"])<minimum:return False
  seen.add(ident)
 return seen==_ids()
def _endpoint_ok(x,n):
 if not _exact(x,("mean_waveform_microvolts","trial_p2p_microvolts","mean_p2p_microvolts")):return False
 if not isinstance(x["mean_waveform_microvolts"],list) or len(x["mean_waveform_microvolts"])!=599:return False
 w={"early","late","prestim"}
 return set(x["trial_p2p_microvolts"])==w and set(x["mean_p2p_microvolts"])==w and _allfinite(x) and all(isinstance(x["trial_p2p_microvolts"][v],list) and len(x["trial_p2p_microvolts"][v])==n for v in w)
def _analysis_ok(x):
 if not _exact(x,("clinical","bipolar","status_lattice")):return False
 names=("p16","p17","p18","p19","p20","UC004","UC005")
 for ref in ("clinical","bipolar"):
  if set(x[ref])!={"early","late","prestim"}:return False
  for z in x[ref].values():
   if not _exact(z,("ts_deltas","pb_deltas","D","bootstrap","loo","paired_p17_p19")):return False
   if not(isinstance(z["ts_deltas"],list) and len(z["ts_deltas"])==4 and isinstance(z["pb_deltas"],list) and len(z["pb_deltas"])==5 and isinstance(z["bootstrap"],list) and len(z["bootstrap"])==3 and _num(z["bootstrap"][2]) and 0<=z["bootstrap"][2]<=1 and isinstance(z["loo"],dict) and tuple(z["loo"])==names and _allfinite(z)):return False
 y=x["status_lattice"]
 return _exact(y,("same_data_status","flags","published_model_status","estimand_discordance")) and isinstance(y["flags"],list) and all(isinstance(v,str) for v in y["flags"]) and y["published_model_status"]=="PUBLISHED_MODEL_ENGINE_UNAVAILABLE"
def _raw_ok(x):
 keys=("schema","status","attempt_id","source_lock_sha256","model_lane","source_qc_records","files","analysis")
 if not(_exact(x,keys) and x["schema"]=="HPC3_RAW_V1" and x["status"]=="RAW_COMPLETE" and x["attempt_id"]=="ATTEMPT1" and x["source_lock_sha256"]==LOCK_SHA and x["model_lane"]=="PUBLISHED_MODEL_ENGINE_UNAVAILABLE" and _records_ok(x["source_qc_records"],20) and isinstance(x["files"],list) and len(x["files"])==18):return False
 counts={(v["protocol"],v["subject"],v["phase"]):v["qc"] for v in x["source_qc_records"]};seen=set()
 for v in x["files"]:
  if not _exact(v,("protocol","subject","phase","clinical","bipolar")):return False
  ident=(v["protocol"],v["subject"],v["phase"])
  if ident in seen or ident not in counts or not _endpoint_ok(v["clinical"],counts[ident]["clinical_qc_clean"]) or not _endpoint_ok(v["bipolar"],counts[ident]["bipolar_clean"]):return False
  seen.add(ident)
 return seen==_ids() and _analysis_ok(x["analysis"])
def _contains_endpoint(x):
 bad=("endpoint","waveform","p2p","delta","bootstrap","loo","status_lattice","analysis")
 if isinstance(x,dict):return any(any(v in str(k).lower() for v in bad) or _contains_endpoint(v) for k,v in x.items())
 return isinstance(x,list) and any(_contains_endpoint(v) for v in x)
def _qc_receipt_ok(x):
 keys=("schema","status","attempt_id","source_lock_sha256","source_qc_records")
 return _exact(x,keys) and x["schema"]=="HPC3_QC_V1" and x["status"]=="QC_STOP_MIN20" and x["attempt_id"]=="ATTEMPT1" and x["source_lock_sha256"]==LOCK_SHA and _records_ok(x["source_qc_records"]) and any(min(v["qc"]["clinical_qc_clean"],v["qc"]["bipolar_clean"])<20 for v in x["source_qc_records"]) and not _contains_endpoint(x)

def resolve_transaction(progress,qc,result):
 for path,valid,good,bad in ((result,_raw_ok,"RAW_COMPLETE","INVALID_RAW_RESULT"),(qc,_qc_receipt_ok,"QC_STOP_MIN20","INVALID_QC_RESULT")):
  if path.exists():
   try:return good if valid(_load(path)) else bad
   except Exception:return bad
 if not progress.exists():return "RAW_IN_PROGRESS"
 try:x=_load(progress)
 except Exception:return "INVALID_PROGRESS"
 schemas=(("status","attempt_id","source_lock_sha256","completed_files"),("status","attempt_id","source_lock_sha256","completed_files","error"))
 if not any(_exact(x,z) for z in schemas) or x.get("attempt_id")!="ATTEMPT1" or x.get("source_lock_sha256")!=LOCK_SHA or not isinstance(x.get("completed_files"),list):return "INVALID_PROGRESS"
 return x["status"] if x["status"] in ("SOURCE_STOP","IMPLEMENTATION_STOP") else "INCOMPLETE_AUTHORITY"
def _terminal(journal,progress,writer,status,exc):
 out={**journal,"status":status,"error":f"{type(exc).__name__}: {exc}"}
 try:writer(progress,_json_bytes(out))
 except Exception:pass
 return out
def _committed(path,payload,valid,writer):
 try:writer(path,payload)
 except Exception:
  if path.exists():
   try:
    x=_load(path)
    if valid(x):return x
   except Exception:pass
  raise
 x=_load(path)
 if not valid(x):raise ValueError("authority commit validation")
 return x

def run_attempt1(progress,qc,result,loader=base.default_loader,endpoint=base._endpoint,aggregator=base.aggregate,authority_writer=_atomic_writer,journal_writer=_atomic_writer,terminal_writer=_atomic_writer):
 _,records,locksha=_preflight(progress,qc,result);journal={"status":"RAW_IN_PROGRESS","attempt_id":"ATTEMPT1","source_lock_sha256":locksha,"completed_files":[]}
 try:journal_writer(progress,_json_bytes(journal))
 except Exception as e:return _terminal(journal,progress,terminal_writer,"IMPLEMENTATION_STOP",e)
 memory=[];low=False
 for sp in SPECS:
  f=records[(sp.protocol,sp.subject,sp.phase)]
  try:
   q,_,b,integrity=loader(sp,f)
   if not _integrity_ok(integrity,f):raise ValueError("full-object identity receipt")
  except Exception as e:return _terminal(journal,progress,terminal_writer,"SOURCE_STOP",e)
  try:
   if f["endpoint_index"]!=f["qc_indices"][0]:raise ValueError("endpoint/QC order")
   qx,bad,reason=base.author_qc(q,sp.subject);bx,bbad,breason=base.author_qc(b[:,None,:],sp.subject)
   row={"protocol":sp.protocol,"subject":sp.subject,"phase":sp.phase,"task":sp.task,"integrity":integrity,"qc":{"clinical_qc_clean":int((~bad).sum()),"bipolar_clean":int((~bbad).sum()),"clinical_exclusion_reasons":reason,"bipolar_exclusion_reasons":breason}}
   if not(_integrity_ok(integrity,f) and _qc_ok(row["qc"],f["blocks"])):raise ValueError("QC receipt schema")
   journal["completed_files"].append(row);journal_writer(progress,_json_bytes(journal));low|=min(row["qc"]["clinical_qc_clean"],row["qc"]["bipolar_clean"])<20;memory.append((sp,qx[:,0],~bad,bx[:,0],~bbad))
  except Exception as e:return _terminal(journal,progress,terminal_writer,"IMPLEMENTATION_STOP",e)
 if low:
  cand={"schema":"HPC3_QC_V1","status":"QC_STOP_MIN20","attempt_id":"ATTEMPT1","source_lock_sha256":locksha,"source_qc_records":journal["completed_files"]}
  try:committed=_committed(qc,_json_bytes(cand),_qc_receipt_ok,authority_writer)
  except Exception as e:return _terminal(journal,progress,terminal_writer,"IMPLEMENTATION_STOP",e)
  try:journal_writer(progress,_json_bytes({**journal,"status":"QC_STOP_MIN20"}))
  except Exception:pass
  return committed
 try:
  files=[{"protocol":sp.protocol,"subject":sp.subject,"phase":sp.phase,"clinical":endpoint(x[k]),"bipolar":endpoint(b[bk])} for sp,x,k,b,bk in memory]
  cand={"schema":"HPC3_RAW_V1","status":"RAW_COMPLETE","attempt_id":"ATTEMPT1","source_lock_sha256":locksha,"model_lane":"PUBLISHED_MODEL_ENGINE_UNAVAILABLE","source_qc_records":journal["completed_files"],"files":files,"analysis":aggregator(files)};committed=_committed(result,_json_bytes(cand),_raw_ok,authority_writer)
 except Exception as e:return _terminal(journal,progress,terminal_writer,"IMPLEMENTATION_STOP",e)
 try:journal_writer(progress,_json_bytes({**journal,"status":"RAW_COMPLETE"}))
 except Exception:pass
 return committed
def main(argv=None,loader=base.default_loader):
 p=argparse.ArgumentParser();p.add_argument("stage",choices=("raw-one-shot","status"));p.add_argument("--progress",type=Path,default=RUN/"artifacts/raw_progress.json");p.add_argument("--qc-result",type=Path,default=RUN/"artifacts/qc_result.json");p.add_argument("--result",type=Path,default=RUN/"artifacts/raw_result.json");a=p.parse_args(argv)
 out=resolve_transaction(a.progress,a.qc_result,a.result) if a.stage=="status" else run_attempt1(a.progress,a.qc_result,a.result,loader=loader)["status"];print(out);return out
if __name__=="__main__":main()
