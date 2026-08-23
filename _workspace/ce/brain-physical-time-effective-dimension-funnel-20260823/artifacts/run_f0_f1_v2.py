"""One-shot BA-SRM8 v2 F0/F1.  No behavior values or models are loaded."""
from __future__ import annotations
import math, time
from pathlib import Path
import numpy as np
from funnel_core_v2 import ROOT, causal_q, manifest, robust, sha, spearman, write

F0=ROOT/'f0-receipt-v2.json'; F1=ROOT/'f1-receipt-v2.json'
OLD={"f0_receipt_sha256":"addb3d43f844b961b19bd92f8624fb3a3fc35fedfc8a54266906b5f351300e41","f1_receipt_sha256":"50cfd85099a1f20d25f39e9667bebf2fc03286110355349d36443e184a0f3c46","funnel_core_sha256":"b6aa6c7a86d7d3f45dd417a9e97479a8071190677540a0891e0b131a6b3ab3ec","run_script_sha256":"2beea4ee4ec4875e931f2bfb277e1eea881ca42e658bed63c4f6cdc99ecacc6c"}
SUPER={"attempt_00_promotion_valid":False,"erroneous_source_hash":"unavailable_not_retained","exact_fault":"future perturbation began inside the then-used compressed calibration set","outputs_used_for_selection":False,"status":"INVALID_NOT_A_RECEIPT"}

def synth(seed):
    g=np.random.default_rng(seed); n,T=8,192; clock=np.cumsum(np.r_[0.,g.uniform(.75,1.35,T-1)]); p=np.linspace(0,6*np.pi,T)
    latent=np.vstack([np.sin(p),np.cos(.7*p),np.sin(1.7*p),g.normal(size=T)]); load=g.normal(size=(n,4)); env=np.vstack([.15+1.4/(1+np.exp(-3*np.sin(p-s))) for s in np.linspace(0,2,4)])
    drive=load@(latent*env); calcium=np.zeros_like(drive)
    for t in range(1,T):
        a=math.exp(-(clock[t]-clock[t-1])/3); calcium[:,t]=a*calcium[:,t-1]+(1-a)*drive[:,t]
    clean=calcium/np.maximum(calcium.std(1,keepdims=True),1e-9); noisy=clean+g.normal(0,.25,clean.shape); mask=(g.random(clean.shape)>=.10).astype(float)
    return clean,noisy,mask,clock

def base_receipt(schema,mhash):
    return {"schema":schema,"behavior_loaded":False,"model_fit":False,"old_attempt_hashes":OLD,"supersedes_unreceipted_attempt":SUPER,"input_hashes":{"manifest_sha256":mhash,"core_sha256":sha(ROOT/'funnel_core_v2.py'),"runner_sha256":sha(Path(__file__))}}

def f0(man,mhash):
    g=np.random.default_rng(20260823); v=g.normal(size=(8,48)); m=np.ones_like(v); clock=np.cumsum(np.r_[0.,g.uniform(.5,1.5,47)]); d=np.linspace(.6,1,8); end=math.ceil(.7*48); rows=[]; base=None
    for c in man['candidates']:
        start=time.perf_counter(); status='PASS'; reason=None; metric={}
        try:
            out=causal_q(c,v,m,clock,d,end); good=np.isfinite(out['Q'])
            if not good.any(): status,reason='ABSTAIN','NO_ELIGIBLE_ANCHORS'
            else:
                mine=float(np.nanmin(out['min_eigs']));
                if mine < -1e-10: raise ValueError('actual covariance PSD failure')
                altered_v=v.copy(); altered_m=m.copy(); altered_v[:,end:]+=23; altered_m[:,end:]=0
                altered=causal_q(c,altered_v,altered_m,clock,d,end)
                delta=float(np.nanmax(np.abs(out['Q'][:end]-altered['Q'][:end]))); cgdelta=abs(out['cG']-altered['cG'])
                if delta>1e-12 or cgdelta>1e-12: raise ValueError('future perturbation changed calibration or earlier Q')
                z=np.zeros_like(v)
                try: causal_q(c,z,m,clock,d,end); raise ValueError('zero did not fail closed')
                except ValueError as exc:
                    if str(exc) not in {'invalid calibration scale','invalid calibration scale terms'}: raise
                try: causal_q(c,np.where(np.eye(8,48),np.nan,v),m,clock,d,end); raise ValueError('nonfinite did not fail closed')
                except ValueError as exc:
                    if str(exc) != 'nonfinite input': raise
                b=robust(c,np.full(8,1e6)); kind=c['formula_components']['robust_map']['parameters']['kind']
                if kind!='identity' and np.linalg.norm(b)>3*math.sqrt(8)+1e-10: raise ValueError('robust bound failure')
                metric={"anchors":int(good.sum()),"cG":out['cG'],"cG_future_delta":cgdelta,"earlier_Q_future_delta":delta,"min_covariance_eigenvalue":mine,"min_neff_positive":float(out['n_eff'][out['n_eff']>0].min()),"q_min":float(out['q'].min()),"q_max":float(out['q'].max()),"rstar_max":float(out['r_star'].max())}
        except (ValueError,np.linalg.LinAlgError,FloatingPointError) as e: status,reason='INVALID_KILL',str(e)
        elapsed=time.perf_counter()-start
        if c['id']=='EXP_theta10__gamma1__identity': base=elapsed
        rows.append({"id":c['id'],"metrics":metric,"reason":reason,"runtime_seconds":elapsed,"status":status})
    for r in rows:
        r['runtime_ratio_to_EXP_theta10_gamma1_identity']=r['runtime_seconds']/base
        if r['status']=='PASS' and r['runtime_ratio_to_EXP_theta10_gamma1_identity']>4:r['status']='INVALID_KILL';r['reason']='runtime ratio exceeds 4'
    x=base_receipt('BA-SRM8-F0-v2',mhash); x.update({"candidate_count":48,"calibration_end":end,"candidates":rows,"runtime_seconds":sum(r['runtime_seconds'] for r in rows)}); return x

def f1(man,mhash,f0r):
    good={r['id'] for r in f0r['candidates'] if r['status']=='PASS'}; f0stat={r['id']:r['status'] for r in f0r['candidates']}; rows=[]
    for c in man['candidates']:
        if c['id'] not in good: rows.append({"id":c['id'],"metrics":{},"reason":"F0_"+f0stat[c['id']],"runtime_seconds":0.,"status":f0stat[c['id']]}); continue
        start=time.perf_counter(); per=[]
        for seed in range(20260823,20260827):
            clean,noisy,mask,clock=synth(seed); end=math.ceil(.7*192); d=np.sqrt(mask[:,:int(.6*192)].mean(1))
            a=causal_q(c,clean,mask,clock,d,end)['Q']; b=causal_q(c,noisy,mask,clock,d,end)['Q']; common=np.isfinite(a)&np.isfinite(b)
            if common.sum()<100: per.append({"eligible_anchors":int(common.sum()),"status":"ABSTAIN_COMMON_ANCHORS"}); continue
            s=spearman(a[common],b[common])
            if not math.isfinite(s): per.append({"eligible_anchors":int(common.sum()),"status":"ABSTAIN_CONSTANT_TRUTH"}); continue
            per.append({"eligible_anchors":int(common.sum()),"nmae_Q":float(np.mean(abs(a[common]-b[common]))),"spearman":s,"status":"PASS"})
        elapsed=time.perf_counter()-start; use=[z for z in per if z['status']=='PASS']
        if len(use)!=4: rows.append({"id":c['id'],"metrics":{"per_seed":per},"reason":"F1_ABSTAIN","runtime_seconds":elapsed,"status":"ABSTAIN"}); continue
        mn=float(np.median([z['nmae_Q'] for z in use])); ms=float(np.median([z['spearman'] for z in use]))
        status='PASS' if ms>=.75 and mn<=.25 else 'INVALID_KILL'; rows.append({"id":c['id'],"metrics":{"median_nmae_Q":mn,"median_spearman":ms,"per_seed":per},"reason":None if status=='PASS' else 'F1_ABSOLUTE_GATE',"runtime_seconds":elapsed,"status":status})
    survivors=sorted([r for r in rows if r['status']=='PASS'],key=lambda r:(r['metrics']['median_nmae_Q'],-r['metrics']['median_spearman'],r['runtime_seconds'],r['id'])); promote=[r['id'] for r in survivors[:32]]
    for r in rows:
        if r['id'] in promote:r['status']='PROMOTE'
        elif r['status']=='PASS':r['status']='DROPPED_BUDGET';r['reason']='F1 promotion cap 32'
    x=base_receipt('BA-SRM8-F1-v2',mhash); x.update({"apparatus":{"N":8,"T":192,"seeds":[20260823,20260824,20260825,20260826],"calcium":"causal exponential decay tau=3 clock units","noise":"Gaussian SNR 4","missingness":"MCAR 10 percent, same dropout mask for truth and estimate","truth":"clean observed Q using same mask/D/clock/candidate","behavior_free":True},"candidate_count":48,"candidates":rows,"promoted_ids":promote,"runtime_seconds":sum(r['runtime_seconds'] for r in rows),"f0_receipt_v2_sha256":sha(F0)}); return x

def main():
    man,h=manifest(); a=f0(man,h); write(F0,a); b=f1(man,h,a); write(F1,b); print({'f0':F0.name,'f1':F1.name,'promoted':len(b['promoted_ids'])})
if __name__=='__main__':main()
