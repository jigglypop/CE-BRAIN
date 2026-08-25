import importlib.util,sys,json
from pathlib import Path
import numpy as np
import pytest
s=importlib.util.spec_from_file_location('h6',Path('examples/brain/ba_obs_hpc6_full_endpoint.py'));h=importlib.util.module_from_spec(s);sys.modules['h6']=h;s.loader.exec_module(h)
v=importlib.util.spec_from_file_location('h6v',Path('examples/brain/ba_obs_hpc6_full_endpoint_validator.py'));q=importlib.util.module_from_spec(v);v.loader.exec_module(q)
def loader(bip_zero=False,clinical_zero=False,bad_integrity=False):
 def f(sp,rec):
  seed=sum((i+1)*ord(c) for i,c in enumerate(f'{sp.protocol}/{sp.subject}/{sp.phase}'))
  x=np.random.default_rng(seed).normal(0,2,(sp.blocks,len(sp.qc),1000));b=x[:,0].copy()
  if bip_zero and sp.protocol=='PB' and sp.subject=='p20' and sp.phase=='post':b[:]=np.nan
  if clinical_zero and sp.protocol=='TS' and sp.subject=='p16' and sp.phase=='pre':x[:]=np.nan
  i={'expected_sha256':rec['annex_sha256'],'observed_sha256':rec['annex_sha256'],'expected_size':rec['annex_size'],'observed_size':rec['annex_size'],'version_id':rec['eeg']['x-amz-version-id'],'etag':rec['eeg']['etag']}
  if bad_integrity:i['observed_sha256']='0'*64
  return x,x[:,0],b,i
 return f
def paths(t):return t/'w.npz',t/'r.json',t/'p.json'
def execution_lock(t):
 p=t/'execution_lock.json';p.write_text(json.dumps({'schema':'HPC6_EXECUTION_LOCK_V1','analysis_lock_sha256':h.sha(h.LOCK),'attempt':'ENDPOINT_FULL1','hashes':{'producer':h.sha(Path('examples/brain/ba_obs_hpc6_full_endpoint.py')),'validator':h.sha(Path('examples/brain/ba_obs_hpc6_full_endpoint_validator.py')),'tests':h.sha(Path('tests/test_ba_obs_hpc6_full_endpoint.py'))}}));return p
def test_full18_witness_validator_and_arrays(tmp_path):
 w,r,p=paths(tmp_path);el=execution_lock(tmp_path);x=h.run(loader(),w,r,p,False,el);assert len(x['files'])==18 and q.validate(r,w,p,False,el)
 with np.load(w) as z:assert len(z.files)==36 and z['00_clinical'].shape[-1]==1000
def test_trialwise_and_aggregate_coordinated_tamper_rejected(tmp_path):
 w,r,p=paths(tmp_path);el=execution_lock(tmp_path);h.run(loader(),w,r,p,False,el);x=json.loads(r.read_text());x['files'][0]['clinical']['trialwise_p2p_microvolts']['late'][0]+=1;x['analysis']['clinical']['trial_mean']['late']['D']+=1;r.write_text(json.dumps(x));assert not q.validate(r,w,p,False,el)
def test_mean_outside_scored_window_and_witness_tamper_rejected(tmp_path):
 w,r,p=paths(tmp_path);el=execution_lock(tmp_path);h.run(loader(),w,r,p,False,el);x=json.loads(r.read_text());x['files'][0]['clinical']['mean_waveform_microvolts'][0]+=9;r.write_text(json.dumps(x));assert not q.validate(r,w,p,False,el)
 w2,r2,p2=paths(tmp_path/'x');(tmp_path/'x').mkdir();el2=execution_lock(tmp_path/'x');h.run(loader(),w2,r2,p2,False,el2);b=bytearray(w2.read_bytes());b[-10]^=1;w2.write_bytes(b);assert not q.validate(r2,w2,p2,False,el2)
def test_bipolar_all_or_none_and_clinical_zero(tmp_path):
 w,r,p=paths(tmp_path);el=execution_lock(tmp_path);x=h.run(loader(bip_zero=True),w,r,p,False,el);assert x['bipolar_status'].endswith('UNAVAILABLE') and 'bipolar' not in x['analysis'] and q.validate(r,w,p,False,el)
 w2,r2,p2=paths(tmp_path/'z');(tmp_path/'z').mkdir()
 el2=execution_lock(tmp_path/'z')
 with pytest.raises(ValueError):h.run(loader(clinical_zero=True),w2,r2,p2,False,el2)
 assert json.loads(p2.read_text())['status']=='CLINICAL_PAIR_UNAVAILABLE'
def test_source_stop_prior_and_q_mismatch(tmp_path):
 w,r,p=paths(tmp_path)
 el=execution_lock(tmp_path)
 with pytest.raises(h.h5._SourceStageError):h.run(loader(bad_integrity=True),w,r,p,False,el)
 assert json.loads(p.read_text())['status']=='SOURCE_STOP'
 wq,rq,pq=paths(tmp_path/'q');(tmp_path/'q').mkdir()
 elq=execution_lock(tmp_path/'q')
 with pytest.raises(ValueError,match='QC_RECHECK1_MISMATCH'):h.run(loader(),wq,rq,pq,execution_lock=elq)
 assert json.loads(pq.read_text())['status']=='IMPLEMENTATION_STOP'
 w2,r2,p2=paths(tmp_path/'x');(tmp_path/'x').mkdir();w2.write_bytes(b'x')
 with pytest.raises(ValueError):h.run(loader(),w2,r2,p2)

def test_independent_qc_execution_lock_and_precomplete_barrier(tmp_path,monkeypatch):
 x=np.zeros((4,1,1000));x[0,0,300]=600;x[1,0,0]=np.nan
 for subject in ('p16','p17'):
  a,ab,ad=h.h5.dual_qc(x,subject);b,bb,bd=q.dual_qc(x,subject);assert np.array_equal(ab,bb) and q.same(ad,bd)
 w,r,p=paths(tmp_path);el=execution_lock(tmp_path);bad=json.loads(el.read_text());bad['hashes']['producer']='0'*64;el.write_text(json.dumps(bad))
 with pytest.raises(ValueError):h.run(loader(),w,r,p,False,el)
 el=execution_lock(tmp_path);w,r,p=tmp_path/'w2.npz',tmp_path/'r2.json',tmp_path/'p2.json'
 with pytest.raises(ValueError,match='independent validator'):h.run(loader(),w,r,p,False,el,True,lambda *a,**k:False)
 assert json.loads(p.read_text())['status']=='IMPLEMENTATION_STOP' and not q.validate(r,w,p,False,el,False)
 w3,r3,p3=tmp_path/'w3.npz',tmp_path/'r3.json',tmp_path/'p3.json';el3=execution_lock(tmp_path)
 monkeypatch.setattr(h.np,'savez_compressed',lambda *a,**k:(_ for _ in ()).throw(OSError('disk')))
 with pytest.raises(OSError):h.run(loader(),w3,r3,p3,False,el3)
 assert not w3.exists() and not w3.with_name('w3.tmp.npz').exists() and json.loads(p3.read_text())['status']=='IMPLEMENTATION_STOP'

def test_metadata_and_nonq_record_forgery_rejected(tmp_path):
 w,r,p=paths(tmp_path);el=execution_lock(tmp_path);h.run(loader(),w,r,p,False,el)
 base=json.loads(r.read_text());prog=json.loads(p.read_text())
 for key in ('model_lane','posthoc_status','primary_status'):
  x=json.loads(json.dumps(base));x[key]='FORGED';r.write_text(json.dumps(x));prog['result_sha256']=h.sha(r);p.write_text(json.dumps(prog));assert not q.validate(r,w,p,False,el)
 for key,value in (('protocol','FORGED'),('task','FORGED'),('integrity',{}),('hpc4_old_grid',{})):
  x=json.loads(json.dumps(base));x['records'][0][key]=value;r.write_text(json.dumps(x));prog['result_sha256']=h.sha(r);p.write_text(json.dumps(prog));assert not q.validate(r,w,p,False,el)
