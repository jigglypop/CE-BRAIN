"""HPC8: one-epoch, full-montage observation-operator test.

Raw BrainVision voltage exists only for one object at a time.  The persistent
witness contains only four pre-specified projected waveforms, never the raw
full montage.  This is intentionally a measurement-model test, not a new
population inference.
"""
from __future__ import annotations
import argparse, hashlib, importlib.util, json, sys
from types import SimpleNamespace
from pathlib import Path
from urllib.parse import quote
from urllib.request import Request, urlopen
import numpy as np
from scipy.interpolate import BSpline

H6_PATH=Path('examples/brain/ba_obs_hpc6_full_endpoint.py')
_s=importlib.util.spec_from_file_location('hpc8_h6',H6_PATH); h6=importlib.util.module_from_spec(_s);sys.modules['hpc8_h6']=h6;assert _s.loader;_s.loader.exec_module(h6)
h5=h6.h5; SPECS=h6.SPECS; N=1000
PIVOT=Path('_workspace/ce/brain-human-hippocampal-theta-endpoint-recovery-20260825/artifacts/epochs/reference-sensitive-local-source/pivots/montage-decomposition')
LOCK=PIVOT/'analysis_lock.json'; PROGRESS=PIVOT/'progress.json'; RESULT=PIVOT/'result.json'; WITNESS=PIVOT/'witness.npz'
WRONG={'p16':('RB3','RB4'),'p17':('D3','D4'),'p18':('AH4','AH5'),'p19':('D3','D4'),'p20':('D11','D12'),'UC004':('RHH3','RHH4'),'UC005':('RHB3','RHB4')}
PROJECTIONS=('clinical','adjacent_bipolar','car','wrong_pair')
DEV=('p16','p17','p18','p20'); SEALED='p19'; PB_ONLY=('UC004','UC005')
POST=slice(250,999); PRESTIM=slice(100,200); BASELINE=slice(225,246)

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def arr_sha(a): return hashlib.sha256(np.ascontiguousarray(a).tobytes()).hexdigest()
def dump(p,x):
 p.parent.mkdir(parents=True,exist_ok=True); t=p.with_suffix(p.suffix+'.tmp');t.write_text(json.dumps(x,indent=2,allow_nan=False),encoding='utf-8');t.replace(p)
def load(p): return json.loads(Path(p).read_text(encoding='utf-8'))
def _atomic_npz(p, data):
 t=p.with_name(p.stem+'.tmp.npz');np.savez_compressed(t,**data);t.replace(p)
def _integrity(rec, observed_sha=None, observed_size=None):
 return {'expected_sha256':rec['annex_sha256'],'observed_sha256':observed_sha or rec['annex_sha256'],'expected_size':rec['annex_size'],'observed_size':observed_size or rec['annex_size'],'version_id':rec['eeg']['x-amz-version-id'],'etag':rec['eeg']['etag']}
def _records(): return h5._records()
def _header_indices(rec, names):
 header=[x['name'] for x in rec['vhdr']['channels']]
 if len(header)!=rec['vhdr']['nchan'] or len(set(header))!=len(header) or any(n not in header for n in names):raise ValueError('STOP_SOURCE_IDENTITY: required channel absent')
 return header,{n:header.index(n) for n in names}
def default_full_loader(sp,rec):
 """Version-pinned full-object decode; raw data is released before return."""
 url=f"{h5.source.S3}/{quote(sp.eeg)}?versionId={quote(rec['eeg']['x-amz-version-id'])}"; digest=hashlib.sha256(); raw=bytearray()
 with urlopen(Request(url),timeout=180) as z:
  head={k.lower():v for k,v in z.headers.items()}
  if head.get('x-amz-version-id')!=rec['eeg']['x-amz-version-id'] or head.get('etag')!=rec['eeg']['etag'] or head.get('content-length')!=str(rec['annex_size']):raise ValueError('STOP_SOURCE_IDENTITY: GET headers')
  while True:
   b=z.read(1024*1024)
   if not b:break
   digest.update(b);raw.extend(b)
 if len(raw)!=rec['annex_size'] or digest.hexdigest()!=rec['annex_sha256']:raise ValueError('STOP_SOURCE_IDENTITY: digest')
 a=np.frombuffer(raw,dtype='<f4').reshape(sp.blocks,N,sp.nchan).transpose(0,2,1).copy();del raw
 scales=np.asarray([c['to_microvolts'] for c in rec['vhdr']['channels']],dtype=float)
 a*=scales.astype(np.float32)[None,:,None]
 return a,_integrity(rec,digest.hexdigest(),int(a.nbytes))
def project(full,sp,rec):
 _,ix=_header_indices(rec,(sp.clinical,sp.bipolar,*WRONG[sp.subject]))
 if full.shape!=(sp.blocks,sp.nchan,N):raise ValueError('STOP_SOURCE_IDENTITY: full montage shape')
 target=full[:,ix[sp.clinical]]; out={'clinical':target.copy(),'adjacent_bipolar':target-full[:,ix[sp.bipolar]],'car':target-(full.sum(1)-target)/(sp.nchan-1),'wrong_pair':full[:,ix[WRONG[sp.subject][0]]]-full[:,ix[WRONG[sp.subject][1]]]}
 return out
def _qraw_parity(full,sp,rec,index):
 with np.load(h6.WITNESS,allow_pickle=False) as z:
  q=np.asarray(z[f'{index:02d}_clinical']); b=np.asarray(z[f'{index:02d}_bipolar'])
 qix=np.asarray(rec['qc_indices']);sc=np.asarray([rec['vhdr']['channels'][i]['to_microvolts'] for i in qix])
 expected=full[:,qix]
 if not np.allclose(expected,q,rtol=0,atol=1e-5,equal_nan=True):raise ValueError('H6_QRAW_PARITY_FAIL')
 target=expected[:,0]; bi=full[:,rec['bipolar_index']]
 if not np.allclose(target-bi,b,rtol=0,atol=1e-5,equal_nan=True):raise ValueError('H6_BRAW_PARITY_FAIL')
def qc_projected(x,subject):
 y,bad,diag=h5.dual_qc(x[:,None,:],subject)
 if y.shape[-1]!=999:raise ValueError('H5_999_SAMPLE_FAIL')
 return y[:,0],bad,diag
def h6_common_mask(full,sp,rec,index):
 _qraw_parity(full,sp,rec,index); q=np.asarray(full[:,rec['qc_indices']]);y,bad,diag=h5.dual_qc(q,sp.subject)
 if y.shape[-1]!=999:raise ValueError('H5_999_SAMPLE_FAIL')
 raw=load(h6.RESULT);row=raw['records'][index]['clinical']
 if diag['keep_mask_sha256']!=row['keep_mask_sha256'] or int((~bad).sum())!=row['clean_count']:raise ValueError('H6_CLINICAL_MASK_PARITY_FAIL')
 return ~bad,diag
def mean_wave(x): return np.asarray(x,float).mean(0)
def _delta(d,protocol,subject,projection): return mean_wave(d[(protocol,subject,'post',projection)])-mean_wave(d[(protocol,subject,'pre',projection)])
def _basis():
 t=np.linspace(0,1,749);knots=np.r_[np.zeros(4),[1/3,2/3],np.ones(4)];eye=np.eye(6)
 return np.stack([BSpline(knots,eye[i],3,extrapolate=False)(t) for i in range(6)],1)
def template(d):
 """Fixed rank-6 cubic template from development subjects only."""
 rows=[]
 for p in ('adjacent_bipolar','car'):
  ts=np.mean([_delta(d,'TS',s,p) for s in ('p16','p17','p18')],0);pb=np.mean([_delta(d,'PB',s,p) for s in ('p17','p20')],0);rows.append(ts-pb)
 raw=np.mean(rows,0)[POST];B=_basis();coef=np.linalg.lstsq(B,raw,rcond=None)[0];v=B@coef
 if not np.isfinite(v).all() or np.linalg.norm(v)==0:raise ValueError('DEVELOPMENT_TEMPLATE_DEGENERATE')
 q=v/np.sqrt(np.mean(v*v));full=np.zeros(999);full[POST]=q;return full,coef
def _score(v,q): return float(np.mean(q[POST]*np.asarray(v)[POST]))
def synthetic_controls():
 """관측연산자 대수 게이트: QC나 생물학 검증이 아니다."""
 sp=SimpleNamespace(blocks=2,nchan=6,clinical='RB1',bipolar='RB2',subject='p16');names=[f'X{i}' for i in range(sp.nchan)];need=(sp.clinical,sp.bipolar,*WRONG[sp.subject])
 for i,n in enumerate(dict.fromkeys(need)):names[i]=n
 rec={'vhdr':{'nchan':sp.nchan,'channels':[{'name':n} for n in names]}};n=N;s=np.linspace(-1,1,n);shared=np.full(n,7.)
 def run(target,other,rest):
  x=np.broadcast_to(rest,(sp.blocks,sp.nchan,n)).copy();x[:,0]=target;x[:,1]=other;x[:,2]=rest;x[:,3]=rest;return project(x,sp,rec)
 a=run(s+shared,shared,shared);b=run(s,np.zeros(n),np.zeros(n));err={'shared_AB':float(np.max(abs(a['adjacent_bipolar'][0]-s))),'shared_CAR':float(np.max(abs(a['car'][0]-s))),'shared_W':float(np.max(abs(a['wrong_pair'][0]))),'target_AB':float(np.max(abs(b['adjacent_bipolar'][0]-s))),'target_CAR':float(np.max(abs(b['car'][0]-s))),'target_W':float(np.max(abs(b['wrong_pair'][0])))};ok=all(v<1e-12 for v in err.values())
 if not ok:raise ValueError('OBSERVATION_OPERATOR_ALGEBRA_GATE_FAIL')
 return {'name':'관측연산자 대수 게이트','errors':err,'shared_reference':{'AB_invariant':True,'CAR_invariant':True,'W_invariant':True},'target_only':{'AB_recovers_target':True,'CAR_recovers_target':True,'W_invariant':True},'hard_gate_pass':True}
def evaluate(d):
 q,coef=template(d);out={'schema':'HPC8_MONTAGE_DECOMPOSITION_V2','status':'RAW_COMPLETE','development_subjects':list(DEV),'sealed_subject':SEALED,'pb_only_subjects':list(PB_ONLY),'template_rank':6,'template_coefficients':coef.tolist(),'sealed':{},'pb_only_descriptive':{},'synthetic_controls':synthetic_controls()}
 for p in PROJECTIONS:
  ts=_delta(d,'TS',SEALED,p);pb=_delta(d,'PB',SEALED,p)
  contrast=ts-pb
  qrev=np.zeros(999);qrev[POST]=q[POST][::-1]
  out['sealed'][p]={'paired_ts_minus_pb_projection_microvolts':_score(contrast,q),'q_reversal_control_microvolts':_score(contrast,qrev),'actual_session_swap_projection_microvolts':_score(pb-ts,q),'prestim_rms_microvolts':float(np.sqrt(np.mean(contrast[PRESTIM]**2)))}
 for s in PB_ONLY:
  out['pb_only_descriptive'][s]={p:_score(_delta(d,'PB',s,p),q) for p in PROJECTIONS}
 z=out['sealed'];ab=z['adjacent_bipolar']['paired_ts_minus_pb_projection_microvolts'];car=z['car']['paired_ts_minus_pb_projection_microvolts'];w=z['wrong_pair']['paired_ts_minus_pb_projection_microvolts'];cl=z['clinical']['paired_ts_minus_pb_projection_microvolts']
 supportive=ab>0 and car>0 and w<min(ab,car)
 code='P19_REFERENCE_CONTRAST_PATTERN_SUPPORT' if supportive else ('P19_CLINICAL_ONLY_PATTERN' if cl>0 and not (ab>0 and car>0) else ('P19_NONSPECIFIC_WRONG_PAIR_PATTERN' if w>=min(ab,car) else 'P19_REFERENCE_CONTRAST_PATTERN_NOT_SUPPORTED'))
 out['scientific_outcome']={'code':code,'korean':{'P19_REFERENCE_CONTRAST_PATTERN_SUPPORT':'p19에서 사전 고정 기준-대조 관측패턴과 일치','P19_CLINICAL_ONLY_PATTERN':'p19 임상 관측기만 양성이며 기준-대조 패턴은 불일치','P19_NONSPECIFIC_WRONG_PAIR_PATTERN':'p19 잘못된 쌍도 분리되지 않는 비특이 관측패턴','P19_REFERENCE_CONTRAST_PATTERN_NOT_SUPPORTED':'p19 사전 고정 기준-대조 관측패턴 불지지'}[code],'claim_ceiling':'source·인과·모집단 효과는 식별하지 않음','temporal_specificity_flag':bool(abs(z['adjacent_bipolar']['q_reversal_control_microvolts'])<abs(ab) and abs(z['car']['q_reversal_control_microvolts'])<abs(car))}
 return out
def _manifest(data):return {k:{'shape':list(v.shape),'dtype':str(v.dtype),'sha256':arr_sha(v)} for k,v in data.items()}
def witness_ok(path,meta):
 try:
  if sha(path)!=meta['file_sha256'] or path.stat().st_size!=meta['file_size']:return False
  with np.load(path,allow_pickle=False) as z:return set(z.files)==set(meta['arrays']) and all(tuple(z[k].shape)==tuple(meta['arrays'][k]['shape']) and str(z[k].dtype)==meta['arrays'][k]['dtype'] and arr_sha(z[k])==meta['arrays'][k]['sha256'] for k in z.files)
 except Exception:return False
def make_lock(lock=LOCK):
 if lock.exists():raise ValueError('IMMUTABLE_LOCK_EXISTS')
 hashes={k:sha(v) for k,v in {'producer':Path(__file__),'validator':Path('examples/brain/ba_obs_hpc8_montage_decomposition_validator.py'),'h2':h5.SOURCE_MODULE,'h5':h6.H5,'h6':H6_PATH,'h6_witness':h6.WITNESS,'h6_result':h6.RESULT,'pivot_contract':PIVOT/'contract.md'}.items()}
 hashes['tests']=sha(Path('tests/test_ba_obs_hpc8_montage_decomposition.py'))
 x={'schema':'HPC8_ANALYSIS_LOCK_V2','hashes':hashes,'parameters':{'clock':'H5 999-sample','projections':list(PROJECTIONS),'wrong_map':WRONG,'car_definition':'all header channels except target arithmetic mean','baseline':'[225,246)','post':'[250,999)','prestim':'[100,200)','q':'post RMS=1; score=mean(q*contrast_post) microvolts','common_mask':'H6 clinical keep_mask_sha256','development':list(DEV),'sealed':SEALED,'rank':6,'decision':'AB>0 and CAR>0 and wrong<min(AB,CAR)','no_population_inference':True}}
 dump(lock,x);return x
def check_lock(lock=LOCK):
 x=load(lock)
 if x.get('schema')!='HPC8_ANALYSIS_LOCK_V2' or x.get('parameters',{}).get('clock')!='H5 999-sample' or x['parameters'].get('rank')!=6 or x['parameters'].get('post')!='[250,999)':raise ValueError('IMPLEMENTATION_INVALID: lock')
 paths={'producer':Path(__file__),'validator':Path('examples/brain/ba_obs_hpc8_montage_decomposition_validator.py'),'h2':h5.SOURCE_MODULE,'h5':h6.H5,'h6':H6_PATH,'h6_witness':h6.WITNESS,'h6_result':h6.RESULT,'pivot_contract':PIVOT/'contract.md','tests':Path('tests/test_ba_obs_hpc8_montage_decomposition.py')}
 if set(x['hashes'])!=set(paths) or any(x['hashes'][k]!=sha(v) for k,v in paths.items()):raise ValueError('IMMUTABLE_LOCK_MISMATCH')
 return x
def run(loader=default_full_loader,lock=LOCK,witness=WITNESS,result=RESULT,progress=PROGRESS,require_parity=True,validator=None):
 if witness.exists() or result.exists() or (progress.exists() and load(progress).get('status')!='SOURCE_STOP'):raise ValueError('IMMUTABLE_OUTPUT_EXISTS')
 check_lock(lock);recs=_records();data={};diags=[];dump(progress,{'status':'IN_PROGRESS','completed_files':[],'lock_sha256':sha(lock)})
 try:
  for i,sp in enumerate(SPECS):
   rec=recs[(sp.protocol,sp.subject,sp.phase)];full,integ=loader(sp,rec)
   if integ!=_integrity(rec):raise ValueError('STOP_SOURCE_IDENTITY: integrity')
   full=np.asarray(full,dtype=np.float32)
   common,common_diag=h6_common_mask(full,sp,rec,i) if require_parity else (np.ones(sp.blocks,bool),{})
   ps=project(full,sp,rec);del full
   for name,value in ps.items():
    y,_,diag=qc_projected(value,sp.subject);clean=y[common];clean=clean-clean[:,BASELINE].mean(1,keepdims=True)
    if clean.shape[-1]!=999:raise ValueError('H5_999_SAMPLE_FAIL')
    data[f'{i:02d}_{name}']=clean;diags.append({'record':i,'projection':name,'common_keep_mask_sha256':common_diag.get('keep_mask_sha256'),'qc':diag})
   dump(progress,{'status':'IN_PROGRESS','completed_files':list(range(i+1)),'lock_sha256':sha(lock)})
  _atomic_npz(witness,data);meta={'file_sha256':sha(witness),'file_size':witness.stat().st_size,'arrays':_manifest(data)}
  if not witness_ok(witness,meta):raise ValueError('WITNESS_READBACK_FAIL')
  with np.load(witness,allow_pickle=False) as z:
   d={(sp.protocol,sp.subject,sp.phase,p):np.asarray(z[f'{i:02d}_{p}']) for i,sp in enumerate(SPECS) for p in PROJECTIONS}
  out=evaluate(d)|{'lock_sha256':sha(lock),'witness':meta,'qc':diags};dump(result,out)
  if validator is None:
   from examples.brain.ba_obs_hpc8_montage_decomposition_validator import validate
   validator=validate
  if not validator(result,witness,lock):raise ValueError('INDEPENDENT_VALIDATOR_FAIL')
  dump(progress,{'status':'COMPLETE','completed_files':list(range(18)),'lock_sha256':sha(lock),'result_sha256':sha(result)});return out
 except Exception as e:
  status='SOURCE_STOP' if 'STOP_SOURCE_IDENTITY' in str(e) or isinstance(e, OSError) else 'IMPLEMENTATION_STOP';dump(progress,{'status':status,'completed_files':list(range(len(data)//4)),'lock_sha256':sha(lock),'error':f'{type(e).__name__}: {e}'});raise
def status(lock=LOCK,witness=WITNESS,result=RESULT,progress=PROGRESS):
 if progress.exists():
  state=load(progress)['status']
  if state=='COMPLETE':
   from examples.brain.ba_obs_hpc8_montage_decomposition_validator import validate
   return 'COMPLETE_VALIDATED' if validate(result,witness,lock) else 'INVALID'
  return state
 return 'LOCKED' if lock.exists() else 'UNINITIALIZED'
def main(argv=None):
 p=argparse.ArgumentParser();p.add_argument('stage',choices=('make-lock','run','status','validate'));a=p.parse_args(argv)
 if a.stage=='make-lock':print(make_lock()['schema'])
 elif a.stage=='run':print(run()['status'])
 elif a.stage=='status':print(status())
 else:
  from examples.brain.ba_obs_hpc8_montage_decomposition_validator import validate
  print('PASS' if validate() else 'FAIL')
if __name__=='__main__':main()
