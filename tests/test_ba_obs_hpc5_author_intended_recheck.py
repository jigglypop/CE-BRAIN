import importlib.util,json,sys
from pathlib import Path
import numpy as np
import pytest
s=importlib.util.spec_from_file_location("h5",Path("examples/brain/ba_obs_hpc5_author_intended_recheck.py"));h=importlib.util.module_from_spec(s);sys.modules["h5"]=h;s.loader.exec_module(h)

def loader(zero=False,nonfinite=False):
 def f(sp,rec):
  x=np.zeros((sp.blocks,len(sp.qc),1000)) if zero else np.random.default_rng(sp.blocks).normal(size=(sp.blocks,len(sp.qc),1000))
  if nonfinite:x[0,0,0]=np.nan
  b=x[:,0].copy();i={"expected_sha256":rec["annex_sha256"],"observed_sha256":rec["annex_sha256"],"expected_size":rec["annex_size"],"observed_size":rec["annex_size"],"version_id":rec["eeg"]["x-amz-version-id"],"etag":rec["eeg"]["etag"]}
  return x,x[:,0],b,i
 return f
def test_integer_cycle_and_masks():
 assert np.array_equal(h.IX["latency"],np.arange(50,650));assert h.TIME[998]==pytest.approx(998/499.5-.5)
 x=np.sin(2*np.pi*60*h.TIME[:999])[None,None,:];x=np.pad(x,((0,0),(0,0),(0,1)))
 assert np.max(np.abs(h._dft_a(x)))<1e-10 and np.max(np.abs(h._dft_b(x)))<1e-10
def test_dual_masks_p17_nonfinite_and_reason_overlap():
 x=np.zeros((4,1,1000));x[0,0,300]=600;x[1,0,300]=np.nan
 y,keep,q=h.dual_qc(x,"p17");assert y.shape==(4,1,999) and keep[1]
 assert set(q["reason_mask_sha256"])=={"amplitude","kurtosis","zscore","nonfinite"}
def test_recheck_receipt_is_endpoint_free_and_diagnostics_tamper_rejected(tmp_path):
 q,r=tmp_path/'q.json',tmp_path/'r.json';x=h.recheck_one_shot(q,r,loader())
 assert x['status']=='QC_RECHECK1' and len(x['records'])==2 and h.recheck_ok(json.loads(q.read_text()))
 z=json.loads(q.read_text());z['analysis']={};q.write_text(json.dumps(z));assert h.resolve(q,r)=='INVALID_QC_RECHECK1'
 q2=tmp_path/'q2.json';h.recheck_one_shot(q2,r,loader());z=json.loads(q2.read_text());z['records'][0]['clinical']['reason_counts'].pop('amplitude');q2.write_text(json.dumps(z));assert h.resolve(q2,r)=='INVALID_QC_RECHECK1'
 q3=tmp_path/'q3.json';h.recheck_one_shot(q3,r,loader());z=json.loads(q3.read_text());z['records'][0]['D']=123;q3.write_text(json.dumps(z));assert h.resolve(q3,r)=='INVALID_QC_RECHECK1'
def test_prior_recheck_and_endpoint_precondition(tmp_path):
 q,r=tmp_path/'q.json',tmp_path/'r.json'
 with pytest.raises(ValueError):h.endpoint_one_shot(q,r,loader())
 q.write_text('{}')
 with pytest.raises(ValueError):h.recheck_one_shot(q,r,loader())
def test_endpoint_and_tamper(tmp_path):
 q,r=tmp_path/'q.json',tmp_path/'r.json';h.recheck_one_shot(q,r,loader());x=h.endpoint_one_shot(q,r,loader())
 assert x['status']=='RAW_COMPLETE' and len(x['files'])==18 and h.result_ok(json.loads(r.read_text()))
 z=json.loads(r.read_text());z['files'][0]['clinical']['mean_waveform_microvolts'][0]='bad';r.write_text(json.dumps(z));assert h.resolve(q,r)=='INVALID_RAW_RESULT'
def test_nzero_stops_and_bipolar_omission(tmp_path):
 q,r=tmp_path/'q.json',tmp_path/'r.json';h.recheck_one_shot(q,r,loader())
 def f(sp,rec):
  x=np.zeros((sp.blocks,len(sp.qc),1000));b=x[:,0].copy()
  if sp.subject=='p16' and sp.phase=='pre':x[:]=np.nan
  if sp.subject=='p17' and sp.protocol=='PB':b[:]=np.nan
  i={"expected_sha256":rec["annex_sha256"],"observed_sha256":rec["annex_sha256"],"expected_size":rec["annex_size"],"observed_size":rec["annex_size"],"version_id":rec["eeg"]["x-amz-version-id"],"etag":rec["eeg"]["etag"]};return x,x[:,0],b,i
 with pytest.raises(ValueError):h.endpoint_one_shot(q,r,f)
 q2,r2=tmp_path/'q2.json',tmp_path/'r2.json';h.recheck_one_shot(q2,r2,loader(zero=True));x=h.endpoint_one_shot(q2,r2,loader(zero=True));assert 'bipolar' in x['analysis']
def test_adversarial_result_and_recheck_leakage(tmp_path):
 q,r=tmp_path/'q.json',tmp_path/'r.json';h.recheck_one_shot(q,r,loader(zero=True));h.endpoint_one_shot(q,r,loader(zero=True))
 z=json.loads(r.read_text());z['analysis']['clinical']['trial_mean']['late']['D']=9;r.write_text(json.dumps(z));assert h.resolve(q,r)=='INVALID_RAW_RESULT'
 q2,r2=tmp_path/'q2.json',tmp_path/'r2.json';h.recheck_one_shot(q2,r2,loader(zero=True));z=json.loads(q2.read_text());z['records'][0]['D']=0;q2.write_text(json.dumps(z));assert h.resolve(q2,r2)=='INVALID_QC_RECHECK1'

def test_progress_source_and_implementation_classification(tmp_path,monkeypatch):
 q,r,p=tmp_path/'q.json',tmp_path/'r.json',tmp_path/'p.json'
 def broken_source(sp,rec):raise OSError('network unavailable')
 with pytest.raises(h._SourceStageError):h.recheck_one_shot(q,r,broken_source,p)
 assert json.loads(p.read_text())['status']=='SOURCE_STOP' and h.resolve(q,r,p)=='SOURCE_STOP'
 q2,r2,p2=tmp_path/'q2.json',tmp_path/'r2.json',tmp_path/'p2.json'
 monkeypatch.setattr(h,'dual_qc',lambda *a,**k:(_ for _ in ()).throw(ValueError('QC disagreement')))
 with pytest.raises(ValueError):h.recheck_one_shot(q2,r2,loader(),p2)
 assert json.loads(p2.read_text())['status']=='IMPLEMENTATION_STOP' and h.resolve(q2,r2,p2)=='IMPLEMENTATION_STOP'

def test_source_integrity_mismatch_and_zero_clean_q(tmp_path):
 q,r,p=tmp_path/'q.json',tmp_path/'r.json',tmp_path/'p.json'
 good=loader(zero=True)
 def forged(sp,rec):
  x,e,b,i=good(sp,rec);i=dict(i);i['observed_sha256']='0'*64;return x,e,b,i
 with pytest.raises(h._SourceStageError):h.recheck_one_shot(q,r,forged,p)
 assert json.loads(p.read_text())['status']=='SOURCE_STOP'
 q2,r2=tmp_path/'q2.json',tmp_path/'r2.json'
 def all_nonfinite(sp,rec):
  x=np.full((sp.blocks,len(sp.qc),1000),np.nan);b=x[:,0].copy();i={"expected_sha256":rec["annex_sha256"],"observed_sha256":rec["annex_sha256"],"expected_size":rec["annex_size"],"observed_size":rec["annex_size"],"version_id":rec["eeg"]["x-amz-version-id"],"etag":rec["eeg"]["etag"]};return x,x[:,0],b,i
 x=h.recheck_one_shot(q2,r2,all_nonfinite)
 assert all(row['clinical']['clean_count']==0 for row in x['records']) and h.resolve(q2,r2)=='QC_RECHECK1'

def test_recheck_authority_binds_progress_and_orphan_complete_is_not_success(tmp_path):
 q,r=tmp_path/'q.json',tmp_path/'r.json';h.recheck_one_shot(q,r,loader(zero=True))
 z=json.loads(q.read_text());z['records'][0]['clinical']['keep_mask_sha256']='0'*64;q.write_text(json.dumps(z))
 assert h.recheck_ok(z) and h.resolve(q,r)=='INVALID_QC_RECHECK1'
 oq,op=tmp_path/'orphan.json',tmp_path/'orphan.progress.json'
 op.write_text(json.dumps({'status':'COMPLETE','attempt_id':'QC_RECHECK1','analysis_lock_sha256':h.ANALYSIS_LOCK_SHA256,'completed_files':[],'receipt_sha256':'0'*64}))
 assert h.resolve(oq,r,op)=='INCOMPLETE_AUTHORITY'

def test_initial_journal_commit_then_raise_records_terminal(tmp_path,monkeypatch):
 q,r,p=tmp_path/'q.json',tmp_path/'r.json',tmp_path/'p.json';original=h._write;calls={'writes':0,'loads':0}
 def flaky(path,value):
  calls['writes']+=1;original(path,value)
  if calls['writes']==1:raise OSError('post-commit failure')
 def counted(sp,rec):calls['loads']+=1;return loader(zero=True)(sp,rec)
 monkeypatch.setattr(h,'_write',flaky)
 with pytest.raises(OSError):h.recheck_one_shot(q,r,counted,p)
 assert calls['loads']==0 and json.loads(p.read_text())['status']=='IMPLEMENTATION_STOP'

def test_receipt_commit_then_raise_is_recovered(tmp_path,monkeypatch):
 q,r,p=tmp_path/'q.json',tmp_path/'r.json',tmp_path/'p.json';original=h._write;raised={'done':False}
 def flaky(path,value):
  original(path,value)
  if path==q and not raised['done']:
   raised['done']=True;raise OSError('receipt post-commit failure')
 monkeypatch.setattr(h,'_write',flaky)
 assert h.recheck_one_shot(q,r,loader(zero=True),p)['status']=='QC_RECHECK1'
 assert h.resolve(q,r,p)=='QC_RECHECK1'

def test_final_progress_failures_are_recovered_or_terminal(tmp_path,monkeypatch):
 q,r,p=tmp_path/'q.json',tmp_path/'r.json',tmp_path/'p.json';original=h._write;raised={'done':False}
 def postcommit(path,value):
  original(path,value)
  if path==p and value.get('status')=='COMPLETE' and not raised['done']:
   raised['done']=True;raise OSError('progress post-commit failure')
 monkeypatch.setattr(h,'_write',postcommit)
 h.recheck_one_shot(q,r,loader(zero=True),p);assert h.resolve(q,r,p)=='QC_RECHECK1'
 monkeypatch.undo();q2,r2,p2=tmp_path/'q2.json',tmp_path/'r2.json',tmp_path/'p2.json';raised={'done':False}
 def precommit(path,value):
  if path==p2 and value.get('status')=='COMPLETE' and not raised['done']:
   raised['done']=True;raise OSError('progress pre-commit failure')
  original(path,value)
 monkeypatch.setattr(h,'_write',precommit)
 with pytest.raises(OSError):h.recheck_one_shot(q2,r2,loader(zero=True),p2)
 assert json.loads(p2.read_text())['status']=='IMPLEMENTATION_STOP' and h.resolve(q2,r2,p2)=='IMPLEMENTATION_STOP'

def test_frozen_source_loader_code_hash():
 assert h._sha(h.SOURCE_MODULE)==h.SOURCE_MODULE_SHA256

def test_receipt_validation_and_endpoint_failure_are_implementation_stop(tmp_path,monkeypatch):
 q,r,p=tmp_path/'q.json',tmp_path/'r.json',tmp_path/'p.json'
 monkeypatch.setattr(h,'recheck_ok',lambda x:False)
 with pytest.raises(ValueError):h.recheck_one_shot(q,r,loader(),p)
 assert json.loads(p.read_text())['status']=='IMPLEMENTATION_STOP'
 monkeypatch.undo();q2,r2,ep=tmp_path/'q2.json',tmp_path/'r2.json',tmp_path/'ep.json';h.recheck_one_shot(q2,r2,loader(zero=True))
 monkeypatch.setattr(h,'_endpoint',lambda *a,**k:(_ for _ in ()).throw(ValueError('endpoint failure')))
 with pytest.raises(ValueError):h.endpoint_one_shot(q2,r2,loader(zero=True),endpoint_progress=ep)
 assert json.loads(ep.read_text())['status']=='IMPLEMENTATION_STOP' and h.resolve(q2,r2,endpoint_progress=ep)=='IMPLEMENTATION_STOP'
