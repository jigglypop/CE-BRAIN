from _run_paths import evidence_file, find_evidence_file
import hashlib, importlib.util, json, sys
from pathlib import Path
import numpy as np
import pytest

s=importlib.util.spec_from_file_location("h3",Path("examples/brain/ba_obs_hpc3_author_qc_transaction.py"));h=importlib.util.module_from_spec(s);sys.modules["h3"]=h;s.loader.exec_module(h)
# Every test here reads the frozen source lock of the hpc3 run; the producer module keeps a
# repository-relative _workspace path, so resolve it through the evidence search order and
# skip the module when the run is not available (fresh clone without ce-runs).
_LOCK=find_evidence_file("brain-human-hippocampal-theta-author-qc-reanalysis-20260825","artifacts","source_lock.json")
if _LOCK is None:pytest.skip("CE run evidence source_lock.json for hpc3 not found (set CE_RUNS_PATH or clone ce-runs)",allow_module_level=True)
h.LOCK=_LOCK
def paths(t):return t/"p.json",t/"q.json",t/"r.json"
def loader(n=24,bad=False):
 rng=np.random.default_rng(72)
 def f(sp,fr):
  q=rng.normal(size=(n,len(sp.qc),1000));i={"expected_sha256":fr["annex_sha256"],"observed_sha256":fr["annex_sha256"],"expected_size":fr["annex_size"],"observed_size":fr["annex_size"],"version_id":fr["eeg"]["x-amz-version-id"],"etag":fr["eeg"]["etag"]}
  if bad:i["etag"]="bad"
  return q,q[:,0],q[:,0]-.1,i
 return f
def test_cli_injected_no_network_and_status(tmp_path,capsys):
 p,q,r=paths(tmp_path);assert h.main(["raw-one-shot","--progress",str(p),"--qc-result",str(q),"--result",str(r)],loader=loader())=="RAW_COMPLETE";assert h.main(["status","--progress",str(p),"--qc-result",str(q),"--result",str(r)])=="RAW_COMPLETE";assert "RAW_COMPLETE" in capsys.readouterr().out
def test_resolver_malformed_and_progress_not_authority(tmp_path):
 p,q,r=paths(tmp_path);p.write_text(json.dumps({"status":"SOURCE_STOP","attempt_id":"ATTEMPT1","source_lock_sha256":h.LOCK_SHA,"completed_files":[]}));r.write_text("{");assert h.resolve_transaction(p,q,r)=="INVALID_RAW_RESULT";r.unlink();q.write_text("{");assert h.resolve_transaction(p,q,r)=="INVALID_QC_RESULT";q.unlink()
 for status in ("RAW_COMPLETE","QC_STOP_MIN20","RAW_IN_PROGRESS"):
  p.write_text(json.dumps({"status":status,"attempt_id":"ATTEMPT1","source_lock_sha256":h.LOCK_SHA,"completed_files":[]}));assert h.resolve_transaction(p,q,r)=="INCOMPLETE_AUTHORITY"
 p.write_text("{");assert h.resolve_transaction(p,q,r)=="INVALID_PROGRESS"
def test_raw_schema_adversaries(tmp_path):
 p,q,r=paths(tmp_path);h.run_attempt1(p,q,r,loader());raw=json.loads(r.read_text());raw["files"]=[{}]*18;r.write_text(json.dumps(raw));assert h.resolve_transaction(p,q,r)=="INVALID_RAW_RESULT"
 for which in ("analysis","extra"):
  d=tmp_path/which;d.mkdir();p,q,r=paths(d);h.run_attempt1(p,q,r,loader());raw=json.loads(r.read_text())
  if which=="analysis":raw["analysis"]={}
  else:raw["files"][0]["clinical"]["extra"]=1
  r.write_text(json.dumps(raw));assert h.resolve_transaction(p,q,r)=="INVALID_RAW_RESULT"
def test_qc_schema_nan_and_endpoint_free(tmp_path):
 p,q,r=paths(tmp_path);assert h.run_attempt1(p,q,r,loader(19))["status"]=="QC_STOP_MIN20";assert h.resolve_transaction(p,q,r)=="QC_STOP_MIN20";x=json.loads(q.read_text());assert not any(z in q.read_text().lower() for z in ("waveform","p2p","bootstrap","analysis","endpoint"));x["source_qc_records"][0]["qc"]["clinical_qc_clean"]=float("nan");q.write_text(json.dumps(x));assert h.resolve_transaction(p,q,r)=="INVALID_QC_RESULT"
@pytest.mark.parametrize("kind",["endpoint","aggregate","nan"])
def test_processing_failures_terminal(tmp_path,kind):
 p,q,r=paths(tmp_path);endpoint=h.base._endpoint;aggregate=h.base.aggregate
 if kind=="endpoint":endpoint=lambda x:(_ for _ in ()).throw(RuntimeError("e"))
 if kind=="aggregate":aggregate=lambda x:(_ for _ in ()).throw(RuntimeError("a"))
 if kind=="nan":aggregate=lambda x:{"bad":float("nan")}
 out=h.run_attempt1(p,q,r,loader(),endpoint=endpoint,aggregator=aggregate);assert out["status"]=="IMPLEMENTATION_STOP" and not q.exists() and not r.exists() and h.resolve_transaction(p,q,r)=="IMPLEMENTATION_STOP"
def test_source_stop_endpoint_invariant_and_prior(tmp_path,monkeypatch):
 p,q,r=paths(tmp_path);assert h.run_attempt1(p,q,r,loader(bad=True))["status"]=="SOURCE_STOP"
 d=tmp_path/"prior";d.mkdir();p,q,r=paths(d);q.write_text("{}")
 with pytest.raises(ValueError):h.run_attempt1(p,q,r,lambda *_:(_ for _ in ()).throw(AssertionError("loader")))
 p,q,r=paths(tmp_path/"inv");p.parent.mkdir();real=h._frozen_lock
 def altered():
  lock,rows=real();k=next(iter(rows));rows[k]=dict(rows[k],endpoint_index=rows[k]["endpoint_index"]+1);return lock,rows
 monkeypatch.setattr(h,"_frozen_lock",altered);assert h.run_attempt1(p,q,r,loader())["status"]=="IMPLEMENTATION_STOP"
def test_writer_commit_cases(tmp_path):
 p,q,r=paths(tmp_path)
 def post(path,b):h._atomic_writer(path,b);raise OSError("post")
 assert h.run_attempt1(p,q,r,loader(),authority_writer=post)["status"]=="RAW_COMPLETE" and h.resolve_transaction(p,q,r)=="RAW_COMPLETE"
 p,q,r=paths(tmp_path/"j");p.parent.mkdir()
 def journal(path,b):
  if path==p and r.exists():raise OSError("after")
  h._atomic_writer(path,b)
 assert h.run_attempt1(p,q,r,loader(),journal_writer=journal)["status"]=="RAW_COMPLETE" and h.resolve_transaction(p,q,r)=="RAW_COMPLETE"
 p,q,r=paths(tmp_path/"pre");p.parent.mkdir();out=h.run_attempt1(p,q,r,loader(),authority_writer=lambda *_:(_ for _ in ()).throw(OSError("pre")));assert out["status"]=="IMPLEMENTATION_STOP" and not r.exists()
def test_tamper_and_version_pinned_reader(tmp_path,monkeypatch):
 bad=tmp_path/"lock";bad.write_bytes(h.LOCK.read_bytes()+b"x");monkeypatch.setattr(h,"LOCK",bad)
 with pytest.raises(ValueError):h._preflight(*paths(tmp_path/"x"))
 monkeypatch.setattr(h,"LOCK",evidence_file("brain-human-hippocampal-theta-author-qc-reanalysis-20260825","artifacts","source_lock.json"));sp=h.base.Spec("TS","x","pre","task",1,3,"A","C",("A","B"));raw=np.arange(3000,dtype="<f4").reshape(1000,3).tobytes();sha=hashlib.sha256(raw).hexdigest();rec={"eeg":{"x-amz-version-id":"v","etag":"e"},"annex_size":len(raw),"annex_sha256":sha,"qc_indices":[0,1],"endpoint_index":0,"bipolar_index":2,"vhdr":{"channels":[{"to_microvolts":2},{"to_microvolts":3},{"to_microvolts":4}]}}
 class R:
  headers={"x-amz-version-id":"v","etag":"e","content-length":str(len(raw))}
  def __enter__(self):self.i=0;return self
  def __exit__(self,*x):pass
  def read(self,n):z=raw[self.i:self.i+n];self.i+=len(z);return z
 seen=[];monkeypatch.setattr(h.base,"urlopen",lambda req,timeout:(seen.append(req.full_url) or R()));q,e,b,g=h.base.default_loader(sp,rec);assert "versionId=v" in seen[0] and q[0,0,1]==6 and e[0,1]==6 and b[0,1]==-14 and g["observed_sha256"]==sha
