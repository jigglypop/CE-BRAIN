import importlib.util,json,sys
from pathlib import Path
import numpy as np
import pytest
s=importlib.util.spec_from_file_location("h4",Path("examples/brain/ba_obs_hpc4_receipt_validator.py"));h=importlib.util.module_from_spec(s);sys.modules["h4"]=h;s.loader.exec_module(h)
def paths(t):return t/"p.json",t/"q.json",t/"r.json"
def loader(qcstop=False,bad=False,truncated=False):
 rng=np.random.default_rng(8)
 def f(sp,fr):
  n=sp.blocks-(1 if truncated else 0);q=rng.normal(size=(n,len(sp.qc),1000));b=q[:,0].copy()
  if qcstop and not truncated:
   q[:n-19]=1000;b[:n-19]=1000
  i={"expected_sha256":fr["annex_sha256"],"observed_sha256":fr["annex_sha256"],"expected_size":fr["annex_size"],"observed_size":fr["annex_size"],"version_id":fr["eeg"]["x-amz-version-id"],"etag":fr["eeg"]["etag"]}
  if bad:i["etag"]="x"
  return q,q[:,0],b,i
 return f
def raw(t):p,q,r=paths(t);h.run_attempt1(p,q,r,loader());return p,q,r,json.loads(r.read_text())
def test_cli_status_and_estimator_regression(tmp_path,capsys):
 p,q,r=paths(tmp_path);assert h.main(["raw-one-shot","--progress",str(p),"--qc-result",str(q),"--result",str(r)],loader=loader())=="RAW_COMPLETE";assert h.main(["status","--progress",str(p),"--qc-result",str(q),"--result",str(r)])=="RAW_COMPLETE";x=json.loads(r.read_text());assert h._same(x["analysis"],h.base.aggregate(x["files"]));assert "RAW_COMPLETE" in capsys.readouterr().out
@pytest.mark.parametrize("kind",["emptyfiles","emptyanalysis","extra","string","bool","null","nan","wave","p2p","negative","analysis"])
def test_raw_forgery_rejected(tmp_path,kind):
 p,q,r,x=raw(tmp_path)
 if kind=="emptyfiles":x["files"]=[{}]*18
 elif kind=="emptyanalysis":x["analysis"]={}
 elif kind=="extra":x["files"][0]["clinical"]["extra"]=1
 elif kind=="string":x["files"][0]["clinical"]["mean_waveform_microvolts"][0]="1"
 elif kind=="bool":x["files"][0]["clinical"]["mean_waveform_microvolts"][0]=True
 elif kind=="null":x["files"][0]["clinical"]["mean_waveform_microvolts"][0]=None
 elif kind=="nan":x["files"][0]["clinical"]["mean_waveform_microvolts"][0]=float("nan")
 elif kind=="wave":
  w=x["files"][0]["clinical"]["mean_waveform_microvolts"];ix=h.base.MASKS["late"]-50;w[int(ix[np.argmax(np.asarray(w)[ix])])]+=1e-5
 elif kind=="p2p":x["files"][0]["clinical"]["mean_p2p_microvolts"]["late"]+=1e-5
 elif kind=="negative":x["files"][0]["clinical"]["trial_p2p_microvolts"]["late"][0]=-1
 else:x["analysis"]["clinical"]["late"]["D"]+=1e-5
 r.write_text(json.dumps(x));assert h.resolve_transaction(p,q,r)=="INVALID_RAW_RESULT"
def test_qc_p20_bound_and_bad_types(tmp_path):
 p,q,r=paths(tmp_path);h.run_attempt1(p,q,r,loader(qcstop=True));x=json.loads(q.read_text());p20=next(v for v in x["source_qc_records"] if v["subject"]=="p20");p20["qc"]["clinical_exclusion_reasons"]["amplitude"]=3*(151-19);q.write_text(json.dumps(x));assert h.resolve_transaction(p,q,r)=="QC_STOP_MIN20"
 for value in (True,"1",None,float("nan"),3*151+1):
  z=json.loads(q.read_text());next(v for v in z["source_qc_records"] if v["subject"]=="p20")["qc"]["clinical_exclusion_reasons"]["amplitude"]=value;q.write_text(json.dumps(z));assert h.resolve_transaction(p,q,r)=="INVALID_QC_RESULT"
def test_progress_malformed_and_never_success(tmp_path):
 p,q,r=paths(tmp_path)
 for status in ("RAW_COMPLETE","QC_STOP_MIN20","RAW_IN_PROGRESS"):
  p.write_text(json.dumps({"status":status,"attempt_id":"ATTEMPT1","source_lock_sha256":h.LOCK_SHA,"completed_files":[]}));assert h.resolve_transaction(p,q,r)=="INCOMPLETE_AUTHORITY"
 p.write_text("{");assert h.resolve_transaction(p,q,r)=="INVALID_PROGRESS"
def test_source_invariant_and_prior(tmp_path,monkeypatch):
 p,q,r=paths(tmp_path);assert h.run_attempt1(p,q,r,loader(bad=True))["status"]=="SOURCE_STOP"
 d=tmp_path/"d";d.mkdir();p,q,r=paths(d);r.write_text("{}")
 with pytest.raises(ValueError):h.run_attempt1(p,q,r,lambda *_:(_ for _ in ()).throw(AssertionError("loader")))
 p,q,r=paths(tmp_path/"i");p.parent.mkdir();real=h.h3._frozen_lock
 def altered():
  a,b=real();k=next(iter(b));b[k]=dict(b[k],endpoint_index=b[k]["endpoint_index"]+1);return a,b
 monkeypatch.setattr(h.h3,"_frozen_lock",altered);assert h.run_attempt1(p,q,r,loader())["status"]=="IMPLEMENTATION_STOP"
def test_truncated_loader_and_receipts_are_rejected(tmp_path):
 p,q,r=paths(tmp_path);assert h.run_attempt1(p,q,r,loader(truncated=True))["status"]=="SOURCE_STOP"
 d=tmp_path/"raw";d.mkdir();p,q,r,x=raw(d);x["source_qc_records"][0]["qc"]["clinical_qc_clean"]-=1;r.write_text(json.dumps(x));assert h.resolve_transaction(p,q,r)=="INVALID_RAW_RESULT"
 p,q,r=paths(tmp_path/"qc");p.parent.mkdir();h.run_attempt1(p,q,r,loader(qcstop=True));x=json.loads(q.read_text());x["source_qc_records"][0]["qc"]["bipolar_clean"]-=1;q.write_text(json.dumps(x));assert h.resolve_transaction(p,q,r)=="INVALID_QC_RESULT"
def test_processing_and_writers(tmp_path):
 for name,endpoint,agg in (("endpoint",lambda x:(_ for _ in ()).throw(RuntimeError("x")),h.base.aggregate),("aggregate",h.base._endpoint,lambda x:(_ for _ in ()).throw(RuntimeError("x")))):
  d=tmp_path/name;d.mkdir();p,q,r=paths(d);assert h.run_attempt1(p,q,r,loader(),endpoint=endpoint,aggregator=agg)["status"]=="IMPLEMENTATION_STOP" and not r.exists()
 p,q,r=paths(tmp_path/"post");p.parent.mkdir()
 def post(path,b):h.h3._atomic_writer(path,b);raise OSError("post")
 assert h.run_attempt1(p,q,r,loader(),authority_writer=post)["status"]=="RAW_COMPLETE" and h.resolve_transaction(p,q,r)=="RAW_COMPLETE"
 p,q,r=paths(tmp_path/"journal");p.parent.mkdir()
 def journal(path,b):
  if path==p and r.exists():raise OSError("after authority")
  h.h3._atomic_writer(path,b)
 assert h.run_attempt1(p,q,r,loader(),journal_writer=journal)["status"]=="RAW_COMPLETE" and h.resolve_transaction(p,q,r)=="RAW_COMPLETE"
 p,q,r=paths(tmp_path/"pre");p.parent.mkdir();assert h.run_attempt1(p,q,r,loader(),authority_writer=lambda *_:(_ for _ in ()).throw(OSError("pre")))["status"]=="IMPLEMENTATION_STOP"
def test_malformed_authority_no_fallthrough(tmp_path):
 p,q,r=paths(tmp_path);p.write_text(json.dumps({"status":"SOURCE_STOP","attempt_id":"ATTEMPT1","source_lock_sha256":h.LOCK_SHA,"completed_files":[]}));r.write_text("{");assert h.resolve_transaction(p,q,r)=="INVALID_RAW_RESULT";r.unlink();q.write_text("{");assert h.resolve_transaction(p,q,r)=="INVALID_QC_RESULT"
