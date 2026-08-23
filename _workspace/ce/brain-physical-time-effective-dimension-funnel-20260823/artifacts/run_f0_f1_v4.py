"""BA-SRM8 floor-boundary F0/F1 correction; no behavior access."""
from __future__ import annotations
import json, math, os, statistics, time
from pathlib import Path
import numpy as np
from funnel_core_v2 import ROOT, causal_q, manifest, robust, sha, write
from run_f1_v3 import raw_synth, preprocess, spearman
F0=ROOT/'f0-receipt-v3.json'; F1=ROOT/'f1-receipt-v4.json'; CL=ROOT/'f0f1-classification-receipt.json'
def f0(man,h):
 g=np.random.default_rng(20260823); v=g.normal(size=(8,48));m=np.ones_like(v);c=np.cumsum(np.r_[0.,g.uniform(.5,1.5,47)]);d=np.linspace(.6,1,8);end=70*48//100; rows=[]; base=None
 for x in man['candidates']:
  status='PASS';reason=None; metrics={}; times=[]
  try:
   # one untimed warmup and five identical timed calls
   out=causal_q(x,v,m,c,d,end)
   for _ in range(5):
    q=time.perf_counter(); out=causal_q(x,v,m,c,d,end);times.append(time.perf_counter()-q)
   good=np.isfinite(out['Q'])
   if not good.any(): status='ABSTAIN';reason='ABSTAIN_NO_CALIBRATION_TERMS_AFTER_INSUFFICIENT_NEFF'
   else:
    mine=float(np.nanmin(out['min_eigs'])); alteredv=v.copy();alteredm=m.copy();alteredv[:,end:]+=99;alteredm[:,end:]=0;changed=causal_q(x,alteredv,alteredm,c,d,end)
    if mine < -1e-10 or abs(out['cG']-changed['cG'])>1e-12 or np.nanmax(abs(out['Q'][:end]-changed['Q'][:end]))>1e-12: raise ValueError('property failure')
    try: causal_q(x,np.zeros_like(v),m,c,d,end);raise ValueError('zero accepted')
    except ValueError as e:
     if str(e) not in {'invalid calibration scale','invalid calibration scale terms'}:raise
    try: causal_q(x,np.where(np.eye(8,48),np.nan,v),m,c,d,end);raise ValueError('nonfinite accepted')
    except ValueError as e:
     if str(e)!='nonfinite input':raise
    b=robust(x,np.full(8,1e6));kind=x['formula_components']['robust_map']['parameters']['kind']
    if kind!='identity' and np.linalg.norm(b)>3*math.sqrt(8)+1e-10:raise ValueError('robust bound')
    metrics={'anchors':int(good.sum()),'cG':out['cG'],'min_covariance_eigenvalue':mine,'T_cal':end}
  except ValueError as e:
   status='ABSTAIN' if str(e)=='invalid calibration scale terms' else 'INVALID_KILL';reason='ABSTAIN_NO_CALIBRATION_TERMS_AFTER_INSUFFICIENT_NEFF' if status=='ABSTAIN' else str(e)
  med=statistics.median(times) if times else 0.;
  if x['id']=='EXP_theta10__gamma1__identity':base=med
  rows.append({'id':x['id'],'metrics':metrics,'reason':reason,'runtime_seconds_median_5':med,'status':status})
 for r in rows:
  r['runtime_ratio_to_EXP_theta10_gamma1_identity']=r['runtime_seconds_median_5']/base
  if r['status']=='PASS' and r['runtime_ratio_to_EXP_theta10_gamma1_identity']>4:r['status']='INVALID_KILL';r['reason']='runtime ratio exceeds 4'
 return {'schema':'BA-SRM8-F0-v3','behavior_loaded':False,'model_fit':False,'boundaries':{'T_cal':end,'T_D':60*48//100},'candidates':rows,'candidate_count':48,'input_hashes':{'manifest':h,'core':sha(ROOT/'funnel_core_v2.py'),'runner':sha(Path(__file__))},'supersedes':{'f0_v2_f1_v3_selection':'boundary_ceil_vs_contract_floor_only'}}
def main():
 man,h=manifest();a=f0(man,h);write(F0,a); abstain={r['id'] for r in a['candidates'] if r['status']=='ABSTAIN'};rows=[];td=60*192//100;tc=70*192//100
 check=[]
 for seed in range(20260823,20260827):
  clean,_,mask,_=raw_synth(seed);z,d,mu,sd=preprocess(clean,mask,td);changed=clean.copy();changed[:,td:]+=101;z2,d2,mu2,sd2=preprocess(changed,mask,td)
  if not(np.array_equal(z[:,:td],z2[:,:td]) and np.array_equal(d,d2) and np.array_equal(mu,mu2) and np.array_equal(sd,sd2)):raise ValueError('prefix future perturbation failure')
  check.append({'seed':seed,'prefix_mu_sigma_D_z_invariant':True})
 for x in man['candidates']:
  if x['id'] in abstain:rows.append({'id':x['id'],'metrics':{},'reason':'ABSTAIN_NO_CALIBRATION_TERMS_AFTER_INSUFFICIENT_NEFF','runtime_seconds':0.,'status':'ABSTAIN'});continue
  st=time.perf_counter();per=[]
  for seed in range(20260823,20260827):
   clean,noisy,mask,clock=raw_synth(seed);z,d,_,_=preprocess(clean,mask,td);zh,dh,_,_=preprocess(noisy,mask,td);truth=causal_q(x,z,mask,clock,d,tc)['Q'];est=causal_q(x,zh,mask,clock,dh,tc)['Q'];common=np.isfinite(truth)&np.isfinite(est)
   if common.sum()<100:per.append({'eligible_anchors':int(common.sum()),'status':'ABSTAIN_COMMON_ANCHORS'});continue
   s=spearman(truth[common],est[common]);per.append({'eligible_anchors':int(common.sum()),'nmae_Q':float(np.mean(abs(est[common]-truth[common]))),'spearman':s,'status':'PASS'})
  elapsed=time.perf_counter()-st;use=[z for z in per if z['status']=='PASS']
  if len(use)!=4:rows.append({'id':x['id'],'metrics':{'per_seed':per},'reason':'F1_ABSTAIN','runtime_seconds':elapsed,'status':'ABSTAIN'});continue
  n=float(np.median([z['nmae_Q'] for z in use]));s=float(np.median([z['spearman'] for z in use]));status='PASS' if s>=.75 and n<=.25 else 'FUTILITY_KILL';rows.append({'id':x['id'],'metrics':{'median_nmae_Q':n,'median_spearman':s,'per_seed':per},'reason':None if status=='PASS' else 'F1_RECOVERY_FAILURE','runtime_seconds':elapsed,'status':status})
 surv=sorted([r for r in rows if r['status']=='PASS'],key=lambda r:(r['metrics']['median_nmae_Q'],-r['metrics']['median_spearman'],r['runtime_seconds'],r['id']));ids=[r['id'] for r in surv[:32]]
 for r in rows:
  if r['id'] in ids:r['status']='PROMOTE'
  elif r['status']=='PASS':r['status']='DROPPED_BUDGET';r['reason']='F1 promotion cap 32'
 receipt={'schema':'BA-SRM8-F1-v4','behavior_loaded':False,'model_fit':False,'boundaries':{'T_cal':tc,'T_D':td,'zero_based_exclusive':True},'candidates':rows,'candidate_count':48,'promoted_ids':ids,'input_hashes':{'manifest':h,'core':sha(ROOT/'funnel_core_v2.py'),'runner':sha(Path(__file__)),'f0_v3':sha(F0),'f1_v3':sha(ROOT/'f1-receipt-v3.json'),'classification':sha(CL)},'supersedes':{'f0_v2_f1_v3_selection':'boundary_ceil_vs_contract_floor_only'},'direct_future_perturbation_preprocessing_check':check};write(F1,receipt);print({'promoted':len(ids),'f0':F0.name,'f1':F1.name})
if __name__=='__main__':main()
