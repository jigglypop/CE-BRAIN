"""HPC6 full 18-object endpoint producer; raw execution is deliberately one-shot."""
from __future__ import annotations
import argparse, hashlib, importlib.util, json, sys
from pathlib import Path
import numpy as np

H5=Path("examples/brain/ba_obs_hpc5_author_intended_recheck.py")
H5_SHA="79191826af3a28b174cc793119817e1536e9466f9a162d1dcc05bea724b25c54"
_s=importlib.util.spec_from_file_location("hpc6_h5",H5); h5=importlib.util.module_from_spec(_s);sys.modules["hpc6_h5"]=h5;assert _s.loader;_s.loader.exec_module(h5)
RUN=Path("_workspace/ce/brain-human-hippocampal-theta-full-endpoint-20260825")
LOCK=RUN/"artifacts/analysis_lock.json"; EXECUTION_LOCK=RUN/"artifacts/execution_lock.json"; WITNESS=RUN/"artifacts/source_witness.npz"; RESULT=RUN/"artifacts/raw_result.json"; PROGRESS=RUN/"artifacts/endpoint_progress.json"
Q=Path("_workspace/ce/brain-human-hippocampal-theta-author-intended-recheck-20260825/artifacts/qc_recheck1.json")
QP=Q.with_name("recheck_progress.json")
SPECS=h5.SPECS; N=999; IX=h5.IX
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def dump(p,x):
 p.parent.mkdir(parents=True,exist_ok=True); t=p.with_suffix(p.suffix+".tmp");t.write_text(json.dumps(x,indent=2,allow_nan=False),encoding="utf-8");t.replace(p)
def load(p): return json.loads(Path(p).read_text(encoding="utf-8"))
def array_sha(a): return hashlib.sha256(np.ascontiguousarray(a).tobytes()).hexdigest()
def check_lock():
 x=load(LOCK); want={"schema","hashes","parameters","attempt"}
 if set(x)!=want or x["schema"]!="HPC6_ANALYSIS_LOCK_V1" or sha(H5)!=H5_SHA: raise ValueError("IMPLEMENTATION_INVALID: lock")
 for key,path in {"hpc5_executor":H5,"hpc2_loader":h5.SOURCE_MODULE,"predecessor_q":Q,"predecessor_progress":QP,"contract":RUN/'00-contract.md',"sources":RUN/'10-sources.md',"math":RUN/'11-math.md',"routes":RUN/'12-routes.md'}.items():
  if x["hashes"].get(key)!=sha(path): raise ValueError("STOP_SOURCE_IDENTITY: lock binding")
 if x["attempt"]!="ENDPOINT_FULL1": raise ValueError("IMPLEMENTATION_INVALID: attempt")
 return x
def check_execution_lock(path=EXECUTION_LOCK,require=True):
 if not require:return None
 x=load(path)
 want={'schema','analysis_lock_sha256','hashes','attempt'}
 if set(x)!=want or x['schema']!='HPC6_EXECUTION_LOCK_V1' or x['attempt']!='ENDPOINT_FULL1' or x['analysis_lock_sha256']!=sha(LOCK):raise ValueError('IMPLEMENTATION_INVALID: execution lock schema')
 files={'producer':Path(__file__),'validator':Path('examples/brain/ba_obs_hpc6_full_endpoint_validator.py'),'tests':Path('tests/test_ba_obs_hpc6_full_endpoint.py')}
 if set(x['hashes'])!=set(files) or any(x['hashes'][k]!=sha(v) for k,v in files.items()):raise ValueError('IMPLEMENTATION_INVALID: execution lock code')
 return sha(path)
def endpoint(x,keep):
 if not keep.any(): raise ValueError("CLINICAL_PAIR_UNAVAILABLE")
 y=np.asarray(x)[keep]; y=y-y[:,IX['baseline']].mean(1,keepdims=True); mean=y.mean(0)
 return {"mean_waveform_microvolts":mean.tolist(),"trialwise_p2p_microvolts":{w:np.ptp(y[:,IX[w]],axis=1).tolist() for w in ('early','late','prestim')},"mean_waveform_p2p_microvolts":{w:float(np.ptp(mean[IX[w]])) for w in ('early','late','prestim')}}
def metric(ts,pb):
 rng=np.random.Generator(np.random.PCG64(20260825)); weights=rng.exponential(size=(65536,7)); d=weights[:,:4]@ts/weights[:,:4].sum(1)-weights[:,[1,3,4,5,6]]@pb/weights[:,[1,3,4,5,6]].sum(1)
 ta=('p16','p17','p18','p19');pa=('p17','p19','p20','UC004','UC005'); names=('p16','p17','p18','p19','p20','UC004','UC005')
 loo={n:float(np.mean([v for v,s in zip(ts,ta) if s!=n])-np.mean([v for v,s in zip(pb,pa) if s!=n])) for n in names}
 return {"ts_deltas":ts.tolist(),"pb_deltas":pb.tolist(),"D":float(ts.mean()-pb.mean()),"bootstrap":[float(np.quantile(d,.025)),float(np.quantile(d,.975)),float((d>0).mean())],"loo":loo,"paired_p17_p19":float((ts[1]+ts[3]-pb[0]-pb[1])/2)}
def aggregate(files,bipolar):
 d={(z['protocol'],z['subject'],z['phase']):z for z in files}; out={}
 for ref in ('clinical','bipolar') if bipolar else ('clinical',):
  out[ref]={}
  for est in ('trial_mean','mean_waveform'):
   out[ref][est]={}
   for w in ('early','late','prestim'):
    def value(z): return float(np.mean(z['trialwise_p2p_microvolts'][w])) if est=='trial_mean' else float(z['mean_waveform_p2p_microvolts'][w])
    ts=np.array([value(d[('TS',s,'post')][ref])-value(d[('TS',s,'pre')][ref]) for s in ('p16','p17','p18','p19')]);pb=np.array([value(d[('PB',s,'post')][ref])-value(d[('PB',s,'pre')][ref]) for s in ('p17','p19','p20','UC004','UC005')]);out[ref][est][w]=metric(ts,pb)
 return out
def manifest(data, ids):
 return {k:{"key":k,"dtype":str(data[k].dtype),"shape":list(data[k].shape),"sha256":array_sha(data[k])} for k in ids}
def witness_ok(path,meta):
 try:
  if set(meta)!={'file_sha256','file_size','key_order','arrays'} or sha(path)!=meta['file_sha256'] or Path(path).stat().st_size!=meta['file_size']: return False
  with np.load(path,allow_pickle=False) as z:
   keys=[f'{i:02d}_{kind}' for i in range(len(SPECS)) for kind in ('clinical','bipolar')]
   if list(z.files)!=keys or meta['key_order']!=keys or set(meta['arrays'])!=set(keys):return False
   for i,sp in enumerate(SPECS):
    for kind,shape in (('clinical',(sp.blocks,len(sp.qc),1000)),('bipolar',(sp.blocks,1000))):
     a=z[f'{i:02d}_{kind}'];m=meta['arrays'][f'{i:02d}_{kind}']
     if a.dtype!=np.dtype('<f8') or a.shape!=shape or m!={'key':f'{i:02d}_{kind}','dtype':'float64','shape':list(shape),'sha256':array_sha(a)}:return False
   return True
 except Exception:return False
def row_data(sp,rec,loader):
 try:
  q,e,b,integrity=loader(sp,rec);q=np.asarray(q);b=np.asarray(b)
  if q.shape!=(sp.blocks,len(sp.qc),1000) or b.shape!=(sp.blocks,1000) or not np.array_equal(e,q[:,0],equal_nan=True):raise ValueError('loader shape')
  expected={'expected_sha256':rec['annex_sha256'],'observed_sha256':rec['annex_sha256'],'expected_size':rec['annex_size'],'observed_size':rec['annex_size'],'version_id':rec['eeg']['x-amz-version-id'],'etag':rec['eeg']['etag']}
  if integrity!=expected:raise ValueError('loader integrity')
 except Exception as exc:raise h5._SourceStageError(f'{type(exc).__name__}: {exc}') from exc
 cy,ck,cq=h5.dual_qc(q,sp.subject);by,bk,bq=h5.dual_qc(b[:,None,:],sp.subject)
 row={'protocol':sp.protocol,'subject':sp.subject,'phase':sp.phase,'task':sp.task,'integrity':integrity,'clinical':{'clean_count':int((~ck).sum()),**cq},'bipolar':{'clean_count':int((~bk).sum()),**bq}}
 old=h5._check_lock()['hpc4_old_grid'].get(f'{sp.protocol}/{sp.subject}/{sp.phase}')
 if old:row['hpc4_old_grid']=old
 return row,q,b,cy[:,0],ck,by[:,0],bk
def prior(*paths):
 if any(Path(p).exists() for p in paths): raise ValueError('IMPLEMENTATION_INVALID: prior artifact')
def run(loader=h5.LOADER,witness=WITNESS,result=RESULT,progress=PROGRESS,check_predecessor=True,execution_lock=EXECUTION_LOCK,require_execution_lock=True,validator=None):
 prior(witness,result,progress); lock=check_lock(); execution_sha=check_execution_lock(execution_lock,require_execution_lock); recs=h5._records(); qold=load(Q); qmap={(r['protocol'],r['subject'],r['phase']):r for r in qold['records']}; rows=[]; files=[]; data={}; keys=[]; bipolar=True
 dump(progress,{"status":"IN_PROGRESS","attempt_id":"ENDPOINT_FULL1","analysis_lock_sha256":sha(LOCK),"execution_lock_sha256":execution_sha,"completed_files":[]})
 try:
  for i,sp in enumerate(SPECS):
   rec=recs[(sp.protocol,sp.subject,sp.phase)]; row,qraw,braw,clinical,ck,bip,bk=row_data(sp,rec,loader); ident=(sp.protocol,sp.subject,sp.phase)
   if check_predecessor and ident in qmap and json.dumps(row,sort_keys=True)!=json.dumps(qmap[ident],sort_keys=True): raise ValueError('QC_RECHECK1_MISMATCH')
   if not (~ck).any(): raise ValueError('CLINICAL_PAIR_UNAVAILABLE')
   bipolar &= bool((~bk).any()); kc=f"{i:02d}_clinical";kb=f"{i:02d}_bipolar";data[kc]=np.asarray(qraw,dtype='<f8');data[kb]=np.asarray(braw,dtype='<f8');keys += [kc,kb]
   rows.append(row); files.append({'protocol':sp.protocol,'subject':sp.subject,'phase':sp.phase,'clinical':endpoint(clinical,~ck),'bipolar':endpoint(bip,~bk) if (~bk).any() else None});dump(progress,{"status":"IN_PROGRESS","attempt_id":"ENDPOINT_FULL1","analysis_lock_sha256":sha(LOCK),"execution_lock_sha256":execution_sha,"completed_files":rows})
  if not bipolar:
   for f in files:f.pop('bipolar')
  tmp=witness.with_name(witness.stem+'.tmp.npz')
  try:
   np.savez_compressed(tmp,**data); meta={"file_sha256":sha(tmp),"file_size":tmp.stat().st_size,"key_order":keys,"arrays":manifest(data,keys)}
   if not witness_ok(tmp,meta):raise ValueError('IMPLEMENTATION_INVALID: witness readback')
   tmp.replace(witness)
  finally:
   if tmp.exists():tmp.unlink()
  out={"schema":"HPC6_ENDPOINT_FULL1_V1","status":"RAW_COMPLETE","attempt_id":"ENDPOINT_FULL1","analysis_lock_sha256":sha(LOCK),"execution_lock_sha256":execution_sha,"model_lane":"PUBLISHED_MODEL_ENGINE_UNAVAILABLE","posthoc_status":"SAME_PUBLIC_DATA_POSTHOC_AUTHOR_INTENDED_EMULATION","primary_status":"CLINICAL_AVAILABLE_CLEAN_PRIMARY","bipolar_status":"BIPOLAR_SENSITIVITY_AVAILABLE" if bipolar else "BIPOLAR_SENSITIVITY_UNAVAILABLE","records":rows,"files":files,"witness":meta,"analysis":aggregate(files,bipolar)}
  dump(result,out)
  if validator is None:
   from examples.brain.ba_obs_hpc6_full_endpoint_validator import validate
   validator=validate
  if not validator(result,witness,progress,check_predecessor=check_predecessor,execution_lock=execution_lock,require_complete=False):raise ValueError('IMPLEMENTATION_INVALID: independent validator')
  dump(progress,{"status":"COMPLETE","attempt_id":"ENDPOINT_FULL1","analysis_lock_sha256":sha(LOCK),"execution_lock_sha256":execution_sha,"completed_files":rows,"witness_sha256":sha(witness),"result_sha256":sha(result)})
  if not validator(result,witness,progress,check_predecessor=check_predecessor,execution_lock=execution_lock,require_complete=True):raise ValueError('IMPLEMENTATION_INVALID: final validator')
  return out
 except h5._SourceStageError as e: dump(progress,{"status":"SOURCE_STOP","attempt_id":"ENDPOINT_FULL1","analysis_lock_sha256":sha(LOCK),"execution_lock_sha256":execution_sha,"completed_files":rows,"error":str(e)});raise
 except ValueError as e:
  status='CLINICAL_PAIR_UNAVAILABLE' if str(e)=='CLINICAL_PAIR_UNAVAILABLE' else 'IMPLEMENTATION_STOP';dump(progress,{"status":status,"attempt_id":"ENDPOINT_FULL1","analysis_lock_sha256":sha(LOCK),"execution_lock_sha256":execution_sha,"completed_files":rows,"error":f'{type(e).__name__}: {e}'});raise
 except Exception as e: dump(progress,{"status":"IMPLEMENTATION_STOP","attempt_id":"ENDPOINT_FULL1","analysis_lock_sha256":sha(LOCK),"execution_lock_sha256":execution_sha,"completed_files":rows,"error":f'{type(e).__name__}: {e}'});raise
def main(argv=None):
 a=argparse.ArgumentParser();a.add_argument('stage',choices=('endpoint-full1',));a.parse_args(argv);print(run()['status'])
if __name__=='__main__':main()
