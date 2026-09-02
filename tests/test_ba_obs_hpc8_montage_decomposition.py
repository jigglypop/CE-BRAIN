import importlib.util,json,sys
from pathlib import Path
import numpy as np,pytest
from _run_paths import evidence_file
s=importlib.util.spec_from_file_location('h8',Path('examples/brain/ba_obs_hpc8_montage_decomposition.py'));h=importlib.util.module_from_spec(s);sys.modules['h8']=h;s.loader.exec_module(h)
v=importlib.util.spec_from_file_location('h8v',Path('examples/brain/ba_obs_hpc8_montage_decomposition_validator.py'));q=importlib.util.module_from_spec(v);v.loader.exec_module(q)
def rec(sp):
 names=[f'C{i}' for i in range(sp.nchan)];needed=[sp.clinical,sp.bipolar,*h.WRONG[sp.subject]]
 for i,n in enumerate(dict.fromkeys(needed)):names[i]=n
 return {'vhdr':{'nchan':sp.nchan,'channels':[{'name':n,'to_microvolts':1.} for n in names]},'qc_indices':list(range(len(sp.qc))),'bipolar_index':1,'annex_sha256':'a'*64,'annex_size':sp.blocks*sp.nchan*1000*4,'eeg':{'x-amz-version-id':'v','etag':'e'}}
def test_projection_algebra_shared_reference_and_target_only():
 sp=h.SPECS[0];r=rec(sp);x=np.zeros((sp.blocks,sp.nchan,1000));x[:,0]=7;x[:,1]=3;x[:,2]=11;x[:,3]=5
 y=h.project(x,sp,r);assert np.allclose(y['adjacent_bipolar'],4) and np.allclose(y['wrong_pair'],6)
 x[:]=9;x[:,0]=13;y=h.project(x,sp,r);assert np.allclose(y['adjacent_bipolar'],4) and np.allclose(y['car'],4)
def test_parity_rejection(monkeypatch):
 sp=h.SPECS[0];r=rec(sp);x=np.zeros((sp.blocks,sp.nchan,1000))
 class Z:
  def __enter__(self):return self
  def __exit__(self,*a):pass
  def __getitem__(self,k):return np.ones((sp.blocks,1 if 'clinical' in k else 1000,1000))
 monkeypatch.setattr(h.np,'load',lambda *a,**k:Z())
 with pytest.raises(ValueError,match='H6_QRAW_PARITY_FAIL'):h._qraw_parity(x,sp,r,0)
def test_split_ceiling_and_validator_tamper(tmp_path,monkeypatch):
 d={}
 for sp in h.SPECS:
  value=(1 if sp.protocol=='TS' else -1)*(1 if sp.phase=='post' else 0)
  for p in h.PROJECTIONS:d[(sp.protocol,sp.subject,sp.phase,p)]=np.ones((max(2,sp.blocks//10),999))*value
 out=h.evaluate(d);assert out['sealed_subject']=='p19' and out['scientific_outcome']['code'] in {'P19_REFERENCE_CONTRAST_PATTERN_SUPPORT','P19_CLINICAL_ONLY_PATTERN','P19_NONSPECIFIC_WRONG_PAIR_PATTERN','P19_REFERENCE_CONTRAST_PATTERN_NOT_SUPPORTED'} and 'bootstrap' not in json.dumps(out).lower()
 assert out['template_rank']==6
 data={f'{i:02d}_{p}':d[(sp.protocol,sp.subject,sp.phase,p)] for i,sp in enumerate(h.SPECS) for p in h.PROJECTIONS};w=tmp_path/'w.npz';np.savez_compressed(w,**data);meta={'file_sha256':h.sha(w),'file_size':w.stat().st_size,'arrays':h._manifest(data)}
 assert out['synthetic_controls']['hard_gate_pass'] and out['sealed']['clinical']['actual_session_swap_projection_microvolts']==-out['sealed']['clinical']['paired_ts_minus_pb_projection_microvolts']
 assert abs(out['sealed']['clinical']['q_reversal_control_microvolts'])<=abs(out['sealed']['clinical']['paired_ts_minus_pb_projection_microvolts'])
 # Validator has no producer import; a missing/forged lock is rejected before arithmetic.
 r=tmp_path/'r.json';h.dump(r,out|{'lock_sha256':'0'*64,'witness':meta,'qc':[]});assert not q.validate(r,w,tmp_path/'missing-lock.json')

def test_independent_validator_normal_and_lock_mask_baseline_result_tamper(tmp_path):
 h6=json.loads(evidence_file('brain-human-hippocampal-theta-full-endpoint-20260825','artifacts','raw_result.json').read_text());data={};d={}
 for i,sp in enumerate(h.SPECS):
  n=h6['records'][i]['clinical']['clean_count'];wave=np.zeros(999);wave[250:]=1 if sp.protocol=='TS' and sp.phase=='post' else (-1 if sp.protocol=='PB' and sp.phase=='post' else 0)
  for p in h.PROJECTIONS:data[f'{i:02d}_{p}']=np.tile(wave,(n,1));d[(sp.protocol,sp.subject,sp.phase,p)]=data[f'{i:02d}_{p}']
 w=tmp_path/'w.npz';np.savez_compressed(w,**data);meta={'file_sha256':h.sha(w),'file_size':w.stat().st_size,'arrays':h._manifest(data)}
 paths={'producer':'examples/brain/ba_obs_hpc8_montage_decomposition.py','validator':'examples/brain/ba_obs_hpc8_montage_decomposition_validator.py','h2':'examples/brain/ba_obs_hpc2_author_qc_reanalysis.py','h5':'examples/brain/ba_obs_hpc5_author_intended_recheck.py','h6':'examples/brain/ba_obs_hpc6_full_endpoint.py','h6_witness':str(evidence_file('brain-human-hippocampal-theta-full-endpoint-20260825','artifacts','source_witness.npz')),'h6_result':str(evidence_file('brain-human-hippocampal-theta-full-endpoint-20260825','artifacts','raw_result.json')),'pivot_contract':str(h.PIVOT/'contract.md'),'tests':'tests/test_ba_obs_hpc8_montage_decomposition.py'}
 lock=tmp_path/'l.json';lock.write_text(json.dumps({'schema':'HPC8_ANALYSIS_LOCK_V2','hashes':{k:h.sha(v) for k,v in paths.items()},'parameters':q.EXPECTED_PARAMETERS}))
 qc=[{'record':i,'projection':p,'common_keep_mask_sha256':h6['records'][i]['clinical']['keep_mask_sha256'],'qc':{}} for i in range(18) for p in h.PROJECTIONS];out=q.ev(d)|{'lock_sha256':h.sha(lock),'witness':meta,'qc':qc};r=tmp_path/'r.json';h.dump(r,out);assert q.validate(r,w,lock)
 forged=json.loads(r.read_text());forged['qc'][0]['common_keep_mask_sha256']='0'*64;h.dump(r,forged);assert not q.validate(r,w,lock);h.dump(r,out)
 bad=json.loads(lock.read_text());bad['parameters']['post']='bad';lock.write_text(json.dumps(bad));assert not q.validate(r,w,lock);lock.write_text(json.dumps({'schema':'HPC8_ANALYSIS_LOCK_V2','hashes':{k:h.sha(v) for k,v in paths.items()},'parameters':q.EXPECTED_PARAMETERS}))
 bad=np.load(w);changed={k:bad[k].copy() for k in bad.files};changed['00_clinical'][0,225]=1;np.savez_compressed(w,**changed);assert not q.validate(r,w,lock)
