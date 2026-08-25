"""HPC4: HPC3 transaction semantics plus recomputed numeric receipts."""
from __future__ import annotations
import argparse, importlib.util, json, sys
from pathlib import Path
import numpy as np

_s=importlib.util.spec_from_file_location("hpc4_h3",Path("examples/brain/ba_obs_hpc3_author_qc_transaction.py"));h3=importlib.util.module_from_spec(_s);sys.modules["hpc4_h3"]=h3;assert _s.loader;_s.loader.exec_module(h3)
base=h3.base;SPECS=h3.SPECS;LOCK_SHA=h3.LOCK_SHA;STATIC_SHA=h3.STATIC_SHA
RUN=Path("_workspace/ce/brain-human-hippocampal-theta-receipt-validator-20260825")

def _is_number(x): return type(x) in (int,float) and np.isfinite(x)
def _same(a,b):
 if _is_number(a) or _is_number(b): return _is_number(a) and _is_number(b) and bool(np.isclose(a,b,rtol=1e-12,atol=1e-12))
 if type(a) is not type(b):return False
 if isinstance(a,dict):return set(a)==set(b) and all(_same(a[k],b[k]) for k in a)
 if isinstance(a,list):return len(a)==len(b) and all(_same(x,y) for x,y in zip(a,b))
 return a==b
def _numbers(x):
 if isinstance(x,dict):return all(_numbers(v) for v in x.values())
 if isinstance(x,list):return all(_numbers(v) for v in x)
 return _is_number(x)
def _endpoint_ok(x,n):
 if not h3._exact(x,("mean_waveform_microvolts","trial_p2p_microvolts","mean_p2p_microvolts")):return False
 wave=x["mean_waveform_microvolts"];windows=("early","late","prestim")
 if not(isinstance(wave,list) and len(wave)==599 and _numbers(wave) and set(x["trial_p2p_microvolts"])==set(windows) and set(x["mean_p2p_microvolts"])==set(windows)):return False
 for w in windows:
  trials=x["trial_p2p_microvolts"][w]; mean=x["mean_p2p_microvolts"][w]; ix=base.MASKS[w]-50
  if not(isinstance(trials,list) and len(trials)==n and _numbers(trials) and all(v>=0 for v in trials) and _is_number(mean) and mean>=0 and np.isclose(mean,np.ptp(np.asarray(wave)[ix]),rtol=1e-12,atol=1e-12)):return False
 return True
def _analysis_ok(x,files):
 if not h3._analysis_ok(x):return False
 # h3 performs schema/cardinality checks; this makes every numeric/categorical leaf auditable.
 return _same(x,base.aggregate(files))
def _qc_ok(x,blocks,nqc):
 keys=("clinical_qc_clean","bipolar_clean","clinical_exclusion_reasons","bipolar_exclusion_reasons");reasons=("amplitude","kurtosis","zscore","nonfinite")
 if not(h3._exact(x,keys) and h3._int(x["clinical_qc_clean"],0,blocks) and h3._int(x["bipolar_clean"],0,blocks) and h3._exact(x["clinical_exclusion_reasons"],reasons) and h3._exact(x["bipolar_exclusion_reasons"],reasons)):return False
 if not all(h3._int(x["clinical_exclusion_reasons"][r],0,blocks*nqc) and h3._int(x["bipolar_exclusion_reasons"][r],0,blocks) for r in reasons):return False
 for clean,key,cap in ((x["clinical_qc_clean"],"clinical_exclusion_reasons",nqc),(x["bipolar_clean"],"bipolar_exclusion_reasons",1)):
  excluded=blocks-clean;total=sum(x[key].values())
  if not (excluded<=total<=excluded*cap*4 and (excluded!=0 or total==0)):return False
 return True
def _records_ok(rows,minimum=None):
 _,frozen=h3._frozen_lock();keys=("protocol","subject","phase","task","integrity","qc")
 if not isinstance(rows,list) or len(rows)!=18:return False
 seen=set()
 for x in rows:
  if not h3._exact(x,keys):return False
  ident=(x["protocol"],x["subject"],x["phase"])
  if ident in seen or ident not in frozen:return False
  f=frozen[ident]
  if x["task"]!=f["task"] or not h3._integrity_ok(x["integrity"],f) or not _qc_ok(x["qc"],f["blocks"],len(f["qc_indices"])):return False
  if minimum is not None and min(x["qc"]["clinical_qc_clean"],x["qc"]["bipolar_clean"])<minimum:return False
  seen.add(ident)
 return seen==h3._ids()
def _raw_ok(x):
 keys=("schema","status","attempt_id","source_lock_sha256","model_lane","source_qc_records","files","analysis")
 if not(h3._exact(x,keys) and x["schema"]=="HPC3_RAW_V1" and x["status"]=="RAW_COMPLETE" and x["attempt_id"]=="ATTEMPT1" and x["source_lock_sha256"]==LOCK_SHA and x["model_lane"]=="PUBLISHED_MODEL_ENGINE_UNAVAILABLE" and _records_ok(x["source_qc_records"],20) and isinstance(x["files"],list) and len(x["files"])==18):return False
 counts={(r["protocol"],r["subject"],r["phase"]):r["qc"] for r in x["source_qc_records"]};seen=set()
 for f in x["files"]:
  if not h3._exact(f,("protocol","subject","phase","clinical","bipolar")):return False
  ident=(f["protocol"],f["subject"],f["phase"])
  if ident in seen or ident not in counts or not _endpoint_ok(f["clinical"],counts[ident]["clinical_qc_clean"]) or not _endpoint_ok(f["bipolar"],counts[ident]["bipolar_clean"]):return False
  seen.add(ident)
 return seen==h3._ids() and _analysis_ok(x["analysis"],x["files"])
def _qc_receipt_ok(x):
 keys=("schema","status","attempt_id","source_lock_sha256","source_qc_records")
 return h3._exact(x,keys) and x["schema"]=="HPC3_QC_V1" and x["status"]=="QC_STOP_MIN20" and x["attempt_id"]=="ATTEMPT1" and x["source_lock_sha256"]==LOCK_SHA and _records_ok(x["source_qc_records"]) and any(min(r["qc"]["clinical_qc_clean"],r["qc"]["bipolar_clean"])<20 for r in x["source_qc_records"]) and not h3._contains_endpoint(x)
def resolve_transaction(progress,qc,result):
 for p,valid,good,bad in ((result,_raw_ok,"RAW_COMPLETE","INVALID_RAW_RESULT"),(qc,_qc_receipt_ok,"QC_STOP_MIN20","INVALID_QC_RESULT")):
  if p.exists():
   try:return good if valid(h3._load(p)) else bad
   except Exception:return bad
 return h3.resolve_transaction(progress,qc,result)
def _committed(path,payload,valid,writer):
 try:writer(path,payload)
 except Exception:
  if path.exists():
   try:
    saved=h3._load(path)
    if valid(saved):return saved
   except Exception:pass
  raise
 saved=h3._load(path)
 if not valid(saved):raise ValueError("authority commit validation")
 return saved
def run_attempt1(progress,qc,result,loader=base.default_loader,endpoint=base._endpoint,aggregator=base.aggregate,authority_writer=h3._atomic_writer,journal_writer=h3._atomic_writer,terminal_writer=h3._atomic_writer):
 _,records,locksha=h3._preflight(progress,qc,result);journal={"status":"RAW_IN_PROGRESS","attempt_id":"ATTEMPT1","source_lock_sha256":locksha,"completed_files":[]}
 try:journal_writer(progress,h3._json_bytes(journal))
 except Exception as e:return h3._terminal(journal,progress,terminal_writer,"IMPLEMENTATION_STOP",e)
 memory=[];low=False
 for sp in SPECS:
  f=records[(sp.protocol,sp.subject,sp.phase)]
  try:
   q,e,b,integrity=loader(sp,f)
   q=np.asarray(q);e=np.asarray(e);b=np.asarray(b)
   if q.shape!=(f["blocks"],len(f["qc_indices"]),1000) or e.shape!=(f["blocks"],1000) or b.shape!=(f["blocks"],1000) or not np.allclose(e,q[:,0],rtol=0,atol=0,equal_nan=True):raise ValueError("loader shape/endpoint mirror")
   if not h3._integrity_ok(integrity,f):raise ValueError("full-object identity receipt")
  except Exception as e:return h3._terminal(journal,progress,terminal_writer,"SOURCE_STOP",e)
  try:
   if f["endpoint_index"]!=f["qc_indices"][0]:raise ValueError("endpoint/QC order")
   qx,bad,reason=base.author_qc(q,sp.subject);bx,bbad,breason=base.author_qc(b[:,None,:],sp.subject)
   row={"protocol":sp.protocol,"subject":sp.subject,"phase":sp.phase,"task":sp.task,"integrity":integrity,"qc":{"clinical_qc_clean":int((~bad).sum()),"bipolar_clean":int((~bbad).sum()),"clinical_exclusion_reasons":reason,"bipolar_exclusion_reasons":breason}}
   if not _qc_ok(row["qc"],f["blocks"],len(f["qc_indices"])):raise ValueError("QC receipt schema")
   journal["completed_files"].append(row);journal_writer(progress,h3._json_bytes(journal));low|=min(row["qc"]["clinical_qc_clean"],row["qc"]["bipolar_clean"])<20;memory.append((sp,qx[:,0],~bad,bx[:,0],~bbad))
  except Exception as e:return h3._terminal(journal,progress,terminal_writer,"IMPLEMENTATION_STOP",e)
 if low:
  x={"schema":"HPC3_QC_V1","status":"QC_STOP_MIN20","attempt_id":"ATTEMPT1","source_lock_sha256":locksha,"source_qc_records":journal["completed_files"]}
  try:out=_committed(qc,h3._json_bytes(x),_qc_receipt_ok,authority_writer)
  except Exception as e:return h3._terminal(journal,progress,terminal_writer,"IMPLEMENTATION_STOP",e)
  try:journal_writer(progress,h3._json_bytes({**journal,"status":"QC_STOP_MIN20"}))
  except Exception:pass
  return out
 try:
  files=[{"protocol":sp.protocol,"subject":sp.subject,"phase":sp.phase,"clinical":endpoint(a[k]),"bipolar":endpoint(b[bk])} for sp,a,k,b,bk in memory]
  x={"schema":"HPC3_RAW_V1","status":"RAW_COMPLETE","attempt_id":"ATTEMPT1","source_lock_sha256":locksha,"model_lane":"PUBLISHED_MODEL_ENGINE_UNAVAILABLE","source_qc_records":journal["completed_files"],"files":files,"analysis":aggregator(files)};out=_committed(result,h3._json_bytes(x),_raw_ok,authority_writer)
 except Exception as e:return h3._terminal(journal,progress,terminal_writer,"IMPLEMENTATION_STOP",e)
 try:journal_writer(progress,h3._json_bytes({**journal,"status":"RAW_COMPLETE"}))
 except Exception:pass
 return out
def main(argv=None,loader=base.default_loader):
 p=argparse.ArgumentParser();p.add_argument("stage",choices=("raw-one-shot","status"));p.add_argument("--progress",type=Path,default=RUN/"artifacts/raw_progress.json");p.add_argument("--qc-result",type=Path,default=RUN/"artifacts/qc_result.json");p.add_argument("--result",type=Path,default=RUN/"artifacts/raw_result.json");a=p.parse_args(argv);out=resolve_transaction(a.progress,a.qc_result,a.result) if a.stage=="status" else run_attempt1(a.progress,a.qc_result,a.result,loader=loader)["status"];print(out);return out
if __name__=="__main__":main()
