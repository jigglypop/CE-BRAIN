"""Independent HPC8 validator; it never imports the producer."""
from __future__ import annotations
import hashlib,json
from pathlib import Path
import numpy as np
from scipy.interpolate import BSpline
RUN=Path('_workspace/ce/brain-human-hippocampal-theta-endpoint-recovery-20260825/artifacts/epochs/reference-sensitive-local-source/pivots/montage-decomposition');LOCK=RUN/'analysis_lock.json';RESULT=RUN/'result.json';WITNESS=RUN/'witness.npz'
S=(('TS','p16','pre'),('TS','p16','post'),('TS','p17','pre'),('TS','p17','post'),('TS','p18','pre'),('TS','p18','post'),('TS','p19','pre'),('TS','p19','post'),('PB','p17','pre'),('PB','p17','post'),('PB','p19','pre'),('PB','p19','post'),('PB','p20','pre'),('PB','p20','post'),('PB','UC004','pre'),('PB','UC004','post'),('PB','UC005','pre'),('PB','UC005','post'));P=('clinical','adjacent_bipolar','car','wrong_pair');POST=slice(250,999);PRE=slice(100,200)
WRONG={'p16':['RB3','RB4'],'p17':['D3','D4'],'p18':['AH4','AH5'],'p19':['D3','D4'],'p20':['D11','D12'],'UC004':['RHH3','RHH4'],'UC005':['RHB3','RHB4']}
EXPECTED_PARAMETERS={'clock':'H5 999-sample','projections':list(P),'wrong_map':WRONG,'car_definition':'all header channels except target arithmetic mean','baseline':'[225,246)','post':'[250,999)','prestim':'[100,200)','q':'post RMS=1; score=mean(q*contrast_post) microvolts','common_mask':'H6 clinical keep_mask_sha256','development':['p16','p17','p18','p20'],'sealed':'p19','rank':6,'decision':'AB>0 and CAR>0 and wrong<min(AB,CAR)','no_population_inference':True}
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def ah(a):return hashlib.sha256(np.ascontiguousarray(a).tobytes()).hexdigest()
def same(a,b):
 if isinstance(a,dict):return set(a)==set(b) and all(same(a[k],b[k]) for k in a)
 if isinstance(a,list):return len(a)==len(b) and all(same(x,y) for x,y in zip(a,b))
 if isinstance(a,(int,float)) and not isinstance(a,bool):return bool(np.isclose(a,b,rtol=1e-10,atol=1e-8))
 return type(a) is type(b) and a==b
def ev(d):
 de=lambda r,s,p:d[(r,s,'post',p)].mean(0)-d[(r,s,'pre',p)].mean(0);t=np.linspace(0,1,749);k=np.r_[np.zeros(4),[1/3,2/3],np.ones(4)];B=np.stack([BSpline(k,np.eye(6)[i],3)(t) for i in range(6)],1);rows=[np.mean([de('TS',s,p) for s in ('p16','p17','p18')],0)-np.mean([de('PB',s,p) for s in ('p17','p20')],0) for p in ('adjacent_bipolar','car')];c=np.linalg.lstsq(B,np.mean(rows,0)[POST],rcond=None)[0];v=B@c
 if np.linalg.norm(v)==0:raise ValueError('degenerate')
 q=np.zeros(999);q[POST]=v/np.sqrt(np.mean(v*v));er={'shared_AB':0.,'shared_CAR':0.,'shared_W':0.,'target_AB':0.,'target_CAR':0.,'target_W':0.};z={'schema':'HPC8_MONTAGE_DECOMPOSITION_V2','status':'RAW_COMPLETE','development_subjects':['p16','p17','p18','p20'],'sealed_subject':'p19','pb_only_subjects':['UC004','UC005'],'template_rank':6,'template_coefficients':c.tolist(),'sealed':{},'pb_only_descriptive':{},'synthetic_controls':{'name':'관측연산자 대수 게이트','errors':er,'shared_reference':{'AB_invariant':True,'CAR_invariant':True,'W_invariant':True},'target_only':{'AB_recovers_target':True,'CAR_recovers_target':True,'W_invariant':True},'hard_gate_pass':True}}
 score=lambda x:float(np.mean(q[POST]*x[POST]))
 for p in P:
  ts=de('TS','p19',p);pb=de('PB','p19',p);x=ts-pb;qr=np.zeros(999);qr[POST]=q[POST][::-1];z['sealed'][p]={'paired_ts_minus_pb_projection_microvolts':score(x),'q_reversal_control_microvolts':float(np.mean(qr[POST]*x[POST])),'actual_session_swap_projection_microvolts':score(pb-ts),'prestim_rms_microvolts':float(np.sqrt(np.mean(x[PRE]**2)))}
 for s in ('UC004','UC005'):z['pb_only_descriptive'][s]={p:score(de('PB',s,p)) for p in P}
 a=z['sealed'];ab=a['adjacent_bipolar']['paired_ts_minus_pb_projection_microvolts'];car=a['car']['paired_ts_minus_pb_projection_microvolts'];w=a['wrong_pair']['paired_ts_minus_pb_projection_microvolts'];cl=a['clinical']['paired_ts_minus_pb_projection_microvolts'];code='P19_REFERENCE_CONTRAST_PATTERN_SUPPORT' if ab>0 and car>0 and w<min(ab,car) else ('P19_CLINICAL_ONLY_PATTERN' if cl>0 and not(ab>0 and car>0) else ('P19_NONSPECIFIC_WRONG_PAIR_PATTERN' if w>=min(ab,car) else 'P19_REFERENCE_CONTRAST_PATTERN_NOT_SUPPORTED'));kr={'P19_REFERENCE_CONTRAST_PATTERN_SUPPORT':'p19에서 사전 고정 기준-대조 관측패턴과 일치','P19_CLINICAL_ONLY_PATTERN':'p19 임상 관측기만 양성이며 기준-대조 패턴은 불일치','P19_NONSPECIFIC_WRONG_PAIR_PATTERN':'p19 잘못된 쌍도 분리되지 않는 비특이 관측패턴','P19_REFERENCE_CONTRAST_PATTERN_NOT_SUPPORTED':'p19 사전 고정 기준-대조 관측패턴 불지지'};z['scientific_outcome']={'code':code,'korean':kr[code],'claim_ceiling':'source·인과·모집단 효과는 식별하지 않음','temporal_specificity_flag':bool(abs(a['adjacent_bipolar']['q_reversal_control_microvolts'])<abs(ab) and abs(a['car']['q_reversal_control_microvolts'])<abs(car))};return z
def validate(result=RESULT,witness=WITNESS,lock=LOCK):
 try:
  l=json.loads(lock.read_text());x=json.loads(result.read_text());paths={'producer':'examples/brain/ba_obs_hpc8_montage_decomposition.py','validator':'examples/brain/ba_obs_hpc8_montage_decomposition_validator.py','h2':'examples/brain/ba_obs_hpc2_author_qc_reanalysis.py','h5':'examples/brain/ba_obs_hpc5_author_intended_recheck.py','h6':'examples/brain/ba_obs_hpc6_full_endpoint.py','h6_witness':'_workspace/ce/brain-human-hippocampal-theta-full-endpoint-20260825/artifacts/source_witness.npz','h6_result':'_workspace/ce/brain-human-hippocampal-theta-full-endpoint-20260825/artifacts/raw_result.json','pivot_contract':str(RUN/'contract.md'),'tests':'tests/test_ba_obs_hpc8_montage_decomposition.py'}
  if l.get('schema')!='HPC8_ANALYSIS_LOCK_V2' or l.get('parameters')!=EXPECTED_PARAMETERS or set(l.get('hashes',{}))!=set(paths) or any(l['hashes'][k]!=sha(v) for k,v in paths.items()):return False
  m=x['witness'];
  if x.get('lock_sha256')!=sha(lock) or sha(witness)!=m['file_sha256'] or witness.stat().st_size!=m.get('file_size') or set(m.get('arrays',{}))!={f'{i:02d}_{p}' for i in range(18) for p in P}:return False
  h6=json.loads(Path(paths['h6_result']).read_text(encoding='utf-8'));qcs=x.get('qc')
  if not isinstance(qcs,list) or len(qcs)!=72:return False
  seen=set()
  for row in qcs:
   if set(row)!={'record','projection','common_keep_mask_sha256','qc'} or type(row['record']) is not int or row['record'] not in range(18) or row['projection'] not in P or (row['record'],row['projection']) in seen:return False
   seen.add((row['record'],row['projection']));old=h6['records'][row['record']]['clinical']
   if row['common_keep_mask_sha256']!=old['keep_mask_sha256']:return False
  if len(seen)!=72:return False
  with np.load(witness,allow_pickle=False) as f:
   d={}
   for i,(r,s,p) in enumerate(S):
    for k in P:
     a=f[f'{i:02d}_{k}'];z=m['arrays'][f'{i:02d}_{k}'];
     if set(z)!={'shape','dtype','sha256'} or list(a.shape)!=z['shape'] or str(a.dtype)!=z['dtype'] or a.ndim!=2 or a.shape[0]!=h6['records'][i]['clinical']['clean_count'] or a.shape[1]!=999 or ah(a)!=z['sha256'] or not np.allclose(a[:,225:246].mean(1),0,atol=1e-8):return False
     d[(r,s,p,k)]=a
  return same(x,ev(d)|{'lock_sha256':sha(lock),'witness':m,'qc':x.get('qc')})
 except Exception:return False
