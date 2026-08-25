import importlib.util, sys, json
from pathlib import Path
import numpy as np
import pytest
s=importlib.util.spec_from_file_location("hpc2",Path("examples/brain/ba_obs_hpc2_author_qc_reanalysis.py")); h=importlib.util.module_from_spec(s);sys.modules["hpc2"]=h;s.loader.exec_module(h)
def test_author_grid_prebaseline_p20_and_masks():
 assert {k:(v[0],v[-1],len(v)) for k,v in h.MASKS.items()}=={"first999":(0,998,999),"latency":(50,648,599),"baseline":(225,244,20),"early":(257,274,18),"late":(275,374,100),"prestim":(100,199,100)}
 x=np.full((24,3,1000),600.); _,bad,_=h.author_qc(x,"p20"); assert bad.all() # must fail before baseline
 rng=np.random.default_rng(2); x=rng.normal(size=(24,3,1000)); x[0,2,300]+=1e5; _,bad,_=h.author_qc(x,"p20"); assert bad[0] # third p20 QC channel is unioned
 x=rng.normal(size=(24,1,1000));x[0,0,100]=np.nan;_,bad,reasons=h.author_qc(x,"p16");assert bad[0] and reasons["nonfinite"]==1
 assert not np.allclose(h.AUTHOR_TIME[h.MASKS["first999"]],np.arange(999)/h.FS)
def test_lock_rejects_tamper_and_min20_has_no_endpoint():
 with pytest.raises(ValueError): h.validate_lock({})
 receipt={"status":"QC_STOP_MIN20","counts":[{"clean":19}],"integrity":[{}]}
 assert not ({"waveform","p2p","delta","endpoint"}&set(receipt))
def _lock():
 return {"status":"SOURCE_LOCK_PASS","commit":h.COMMIT,"fs":h.FS,"masks":{k:v.tolist() for k,v in h.MASKS.items()},"records":[{"protocol":s.protocol,"subject":s.subject,"phase":s.phase,"endpoint_index":0,"qc_indices":[0]} for s in h.SPECS]}
def _loader(n=24,fail_source=False):
 rng=np.random.default_rng(4)
 def load(s,r):
  if fail_source and s.subject=="p17": raise OSError("network")
  q=rng.normal(size=(n,len(s.qc),1000)); endpoint=q[:,0]; bipolar=rng.normal(size=(n,1000))
  return q,endpoint,bipolar,{"observed_sha256":"x","observed_size":1,"expected_sha256":"x","expected_size":1}
 return load
def test_qc_stop_all_counts_no_endpoint_and_source_stop(tmp_path):
 p,q,r=tmp_path/'p.json',tmp_path/'q.json',tmp_path/'r.json'; out=h.run_attempt1(_lock(),"lock",p,q,r,_loader(19))
 assert out["status"]=="QC_STOP_MIN20" and len(out["counts"])==18 and not r.exists()
 assert not any("p2p" in str(x).lower() or "waveform" in str(x).lower() for x in out.values())
 p,q,r=tmp_path/'p2.json',tmp_path/'q2.json',tmp_path/'r2.json'; out=h.run_attempt1(_lock(),"lock",p,q,r,_loader(fail_source=True))
 assert out["status"]=="SOURCE_STOP" and not q.exists() and not r.exists()
def test_all_pass_seals_result_before_progress_and_rejects_prior(tmp_path):
 p,q,r=tmp_path/'p.json',tmp_path/'q.json',tmp_path/'r.json'; out=h.run_attempt1(_lock(),"lock",p,q,r,_loader())
 assert out["status"]=="RAW_COMPLETE" and r.exists() and json.loads(p.read_text())["status"]=="RAW_COMPLETE"
 with pytest.raises(ValueError,match="prior transaction"): h.run_attempt1(_lock(),"lock",p,q,r,_loader())
def test_participant_aggregation_bootstrap_loo_paired_and_status():
 files=[]
 for i,s in enumerate(h.SPECS):
  # post-pre deltas: TS=2; PB=1, hence D=1 in all references/windows.
  val=(2 if s.protocol=="TS" else 1) if s.phase=="post" else 0
  e={"mean_p2p_microvolts":{w:float(val) for w in ("early","late","prestim")}}
  files.append({"protocol":s.protocol,"subject":s.subject,"phase":s.phase,"clinical":e,"bipolar":e})
 a=h.aggregate(files); late=a["clinical"]["late"]
 assert late["D"]==1 and late["paired_p17_p19"]==1 and len(late["loo"])==7
 assert late["bootstrap"]==h._boot(np.array([2]*4),np.array([1]*5))
 assert a["status_lattice"]["same_data_status"]=="SAME_DATA_REANALYSIS_SUPPORT_SENSITIVITY_LIMITED" # prestim is positive
 a["clinical"]["late"]["D"]=-1
 assert h._lattice(a)["same_data_status"]=="SAME_DATA_REANALYSIS_NOT_SUPPORTED"
def test_default_loader_multiplex_scaling_and_rejections(monkeypatch):
 sp=h.Spec("TS","x","pre","task",1,3,"A","C",("A","B")); raw=np.arange(3000,dtype="<f4").reshape(1000,3).tobytes(); sha=__import__("hashlib").sha256(raw).hexdigest()
 rec={"eeg":{"x-amz-version-id":"v","etag":"e"},"annex_size":len(raw),"annex_sha256":sha,"qc_indices":[0,1],"endpoint_index":0,"bipolar_index":2,"vhdr":{"channels":[{"to_microvolts":2},{"to_microvolts":3},{"to_microvolts":4}]}}
 class R:
  headers={"x-amz-version-id":"v","etag":"e","content-length":str(len(raw))}
  def __enter__(self):self.i=0;return self
  def __exit__(self,*x):pass
  def read(self,n):z=raw[self.i:self.i+n];self.i+=len(z);return z
 monkeypatch.setattr(h,"urlopen",lambda req,timeout:R()); qc,endpoint,bipolar,got=h.default_loader(sp,rec)
 assert qc[0,0,1]==6 and qc[0,1,1]==12 and endpoint[0,1]==6 and bipolar[0,1]==-14 and got["observed_sha256"]==sha and got["observed_size"]==len(raw)
 rec["annex_sha256"]="0"*64
 with pytest.raises(ValueError,match="digest"):h.default_loader(sp,rec)
def test_implementation_stop_and_early_control_does_not_downgrade(tmp_path,monkeypatch):
 p,q,r=tmp_path/'p',tmp_path/'q',tmp_path/'r'; monkeypatch.setattr(h,"author_qc",lambda *x:(_ for _ in ()).throw(RuntimeError("boom")))
 out=h.run_attempt1(_lock(),"lock",p,q,r,_loader());assert out["status"]=="IMPLEMENTATION_STOP" and not q.exists() and not r.exists()
 a={"clinical":{"late":{"D":1,"bootstrap":[.1,1,1],"paired_p17_p19":1,"loo":{"p16":1}},"prestim":{"bootstrap":[-.1,1,1]},"early":{"bootstrap":[1,2,1]}},"bipolar":{"late":{"D":1,"bootstrap":[.1,1,1]}}}
 assert h._lattice(a)["same_data_status"]=="SAME_DATA_REANALYSIS_REFERENCE_ROBUST_SUPPORT"
def test_cli_preflight_dispatch_without_network(tmp_path,monkeypatch):
 lock=Path("_workspace/ce/brain-human-hippocampal-theta-author-qc-reanalysis-20260825/artifacts/source_lock.json")
 p,q,r=tmp_path/'p.json',tmp_path/'q.json',tmp_path/'r.json'; calls=[]
 def factory(): calls.append("factory");return "loader"
 def attempt(*args): calls.append(args);return {"status":"MOCK"}
 out=h.run_raw_cli(lock,p,q,r,factory,attempt);assert out["status"]=="MOCK" and calls[0]=="factory" and len(calls)==2
 p.write_text("{}")
 with pytest.raises(ValueError,match="prior transaction"):h.run_raw_cli(lock,p,q,r,lambda:pytest.fail("loader"),attempt)
 bad=tmp_path/'bad.json';bad.write_bytes(lock.read_bytes()+b"x")
 with pytest.raises(ValueError,match="frozen lock hash"):h.run_raw_cli(bad,tmp_path/'a',tmp_path/'b',tmp_path/'c',lambda:pytest.fail("loader"),attempt)
