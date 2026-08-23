"""Self-contained BA-SRM8 F1 v6, no behavior/model access."""
from __future__ import annotations
import hashlib,json,math,os,time
from pathlib import Path
import numpy as np
from funnel_core_v2 import ROOT,causal_q,manifest,sha
OUT=ROOT/'f1-receipt-v6.json';F0=ROOT/'f0-receipt-v3.json'
def cb(x):return (json.dumps(x,allow_nan=False,sort_keys=True,separators=(',',':'))+'\n').encode()
def put(x):
 b=cb(x)
 with OUT.open('wb') as f:f.write(b);f.flush();os.fsync(f.fileno())
def raw(seed):
 g=np.random.default_rng(seed);N,T=8,192;c=np.cumsum(np.r_[0.,g.uniform(.75,1.35,T-1)]);p=np.linspace(0,6*np.pi,T);l=np.vstack([np.sin(p),np.cos(.7*p),np.sin(1.7*p),g.normal(size=T)]);drive=g.normal(size=(N,4))@(l*np.vstack([.15+1.4/(1+np.exp(-3*np.sin(p-s))) for s in np.linspace(0,2,4)]));y=np.zeros_like(drive)
 for t in range(1,T):a=np.exp(-(c[t]-c[t-1])/3);y[:,t]=a*y[:,t-1]+(1-a)*drive[:,t]
 noisy=y+g.normal(0,np.sqrt(np.mean(y[:,:115]**2))/4,y.shape);m=(g.random(y.shape)>=.1).astype(float);return y,noisy,m,c
def prep(x,m):
 z=np.zeros_like(x);d=np.sqrt(m[:,:115].mean(1));mu=[];sd=[]
 for i in range(8):
  a=x[i,:115][m[i,:115]==1];mu.append(a.mean());sd.append(a.std());z[i]=(x[i]-mu[-1])/sd[-1]
 z[m==0]=0;return z,d,np.array(mu),np.array(sd)
def rank(x):
 o=np.argsort(x,kind='stable');r=np.empty(len(x));i=0
 while i<len(x):
  j=i+1
  while j<len(x) and x[o[j]]==x[o[i]]:j+=1
  r[o[i:j]]=(i+j-1)/2;i=j
 return r
def rho(a,b):return float('nan') if len(a)<3 or np.ptp(a)==0 or np.ptp(b)==0 else float(np.corrcoef(rank(a),rank(b))[0,1])
def main():
 man,h=manifest();f0=json.loads(F0.read_text());ab={r['id'] for r in f0['candidates'] if r['status']=='ABSTAIN'};checks=[]
 for s in range(20260823,20260827):
  a,_,m,_=raw(s);z,d,mu,sd=prep(a,m);b=a.copy();b[:,115:]+=33;z2,d2,mu2,sd2=prep(b,m);assert np.array_equal(z[:,:115],z2[:,:115]) and np.array_equal(d,d2) and np.array_equal(mu,mu2) and np.array_equal(sd,sd2);checks.append({'seed':s,'prefix_invariant':True})
 rows=[]
 for c in man['candidates']:
  if c['id'] in ab:rows.append({'id':c['id'],'status':'ABSTAIN','reason':'ABSTAIN_NO_CALIBRATION_TERMS_AFTER_INSUFFICIENT_NEFF','metrics':{},'runtime_seconds':0.});continue
  st=time.perf_counter();per=[]
  for s in range(20260823,20260827):
   a,b,m,clock=raw(s);z,d,_,_=prep(a,m);zh,dh,_,_=prep(b,m);q=causal_q(c,z,m,clock,d,134)['Q'];qh=causal_q(c,zh,m,clock,dh,134)['Q'];co=np.isfinite(q)&np.isfinite(qh)
   if co.sum()<100:per.append({'status':'ABSTAIN_COMMON_ANCHORS','eligible_anchors':int(co.sum())});continue
   r=rho(q[co],qh[co])
   if not math.isfinite(r):per.append({'status':'ABSTAIN_CONSTANT_TRUTH','eligible_anchors':int(co.sum())});continue
   per.append({'status':'PASS','eligible_anchors':int(co.sum()),'spearman':r,'nmae_Q':float(np.mean(abs(q[co]-qh[co])) )})
  use=[x for x in per if x['status']=='PASS'];el=time.perf_counter()-st
  if len(use)!=4:rows.append({'id':c['id'],'status':'ABSTAIN','reason':'F1_INCOMPLETE_SEEDS','metrics':{'per_seed':per},'runtime_seconds':el});continue
  n=float(np.median([x['nmae_Q'] for x in use]));r=float(np.median([x['spearman'] for x in use]));status='PASS' if n<=.25 and r>=.75 else 'FUTILITY_KILL';rows.append({'id':c['id'],'status':status,'reason':None if status=='PASS' else 'F1_RECOVERY_FAILURE','metrics':{'median_nmae_Q':n,'median_spearman':r,'per_seed':per},'runtime_seconds':el})
 s=sorted([x for x in rows if x['status']=='PASS'],key=lambda x:(x['metrics']['median_nmae_Q'],-x['metrics']['median_spearman'],x['runtime_seconds'],x['id']));ids=[x['id'] for x in s[:32]]
 for x in rows:
  if x['id'] in ids:x['status']='PROMOTE'
  elif x['status']=='PASS':x['status']='DROPPED_BUDGET';x['reason']='F1 promotion cap 32'
 paths=['f1-receipt-v3.json','f1-receipt-v4.json','f1-receipt-v5.json'];rec={'schema':'BA-SRM8-F1-v6','behavior_loaded':False,'model_fit':False,'boundaries':{'T_D':115,'T_cal':134,'zero_based_exclusive':True},'candidates':rows,'promoted_ids':ids,'direct_future_prefix_check':checks,'input_hashes':{'runner':sha(Path(__file__)),'core':sha(ROOT/'funnel_core_v2.py'),'manifest':h,'f0_v3':sha(F0),**{p:sha(ROOT/p) for p in paths}},'supersedes':{'v4_v5':'fail_closed_constant_truth_P1'},'runtime_seconds':sum(x['runtime_seconds'] for x in rows)};put(rec);print({'promoted':len(ids)})
if __name__=='__main__':main()
