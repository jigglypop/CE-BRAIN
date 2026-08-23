"""BA-SRM8 F2-A only; behavior-free 32->24 screen."""
from __future__ import annotations
import hashlib,json,math,os,time
from pathlib import Path
import numpy as np
from funnel_core_v2 import ROOT,causal_q,manifest,sha
from f2_common_v2 import generate
OUT=ROOT/'f2a-receipt.json'
def rank(x):
 o=np.argsort(x,kind='stable');r=np.empty(len(x));i=0
 while i<len(x):
  j=i+1
  while j<len(x) and x[o[j]]==x[o[i]]:j+=1
  r[o[i:j]]=(i+j-1)/2;i=j
 return r
def rho(a,b):return float('nan') if np.ptp(a)==0 or np.ptp(b)==0 else float(np.corrcoef(rank(a),rank(b))[0,1])
def prep(x,m):
 N,T=x.shape;z=np.zeros_like(x);d=np.empty(N)
 for i in range(N):
  a=x[i,:460][m[i,:460]==1]
  if len(a)<2 or a.std()<=1e-12:raise ValueError('prefix scale')
  z[i]=(x[i]-a.mean())/a.std();d[i]=np.sqrt(m[i,:460].mean())
 z[m==0]=0;return z,d
def main():
 man,h=manifest();cfg=json.loads((ROOT/'f2-config-v4.json').read_text());ids=cfg['promoted_ids'];assert len(ids)==32
 files={'manifest':ROOT/'candidate-manifest.json','core':ROOT/'funnel_core_v2.py','f0_v3':ROOT/'f0-receipt-v3.json','f1_v6':ROOT/'f1-receipt-v6.json','config':ROOT/'f2-config-v4.json','config_receipt':ROOT/'f2-config-v4-receipt.json','common':ROOT/'f2_common_v2.py','fixture':ROOT/'f2-generator-fixture-v3.json'}; hashes={k:sha(v) for k,v in files.items()};cache={}
 for s in ['ZERO_NULL','ISO_NULL','JUMP']:
  for seed in (range(20261001,20261017) if s=='ISO_NULL' else range(20261101,20261109)):
   x=generate(s,seed);cache[s,seed]=(x, None if s=='ZERO_NULL' else (prep(x['clean'],x['mask']),prep(x['noisy'],x['mask'])))
 rows=[]
 for c in [x for x in man['candidates'] if x['id'] in ids]:
  st=time.perf_counter();pool=[];bad=False
  for seed in range(20261001,20261017):
   x,p=cache['ISO_NULL',seed];(z,d),(zh,dh)=p
   try:q=causal_q(c,z,x['mask'],x['clock'],d,537)['Q'];qh=causal_q(c,zh,x['mask'],x['clock'],dh,537)['Q'];A=np.isfinite(q)&np.isfinite(qh);B=A[1:]&A[:-1]
   except ValueError:bad=True;break
   if A.sum()<100 or B.sum()<100:bad=True;break
   pool.extend(abs(np.diff(qh)[B])/(np.diff(x['clock'])[B]/np.median(np.diff(x['clock']))))
  if bad or not pool:rows.append({'id':c['id'],'status':'ABSTAIN','reason':'ISO_CALIBRATION_INSUFFICIENT','metrics':{},'runtime_seconds':time.perf_counter()-st});continue
  th=float(np.quantile(pool,.95,method='linear'));iso=[];jump=[];zero_ok=True
  for seed in range(20261101,20261109):
   try:
    z0=cache['ZERO_NULL',seed][0]
    try: prep(z0['clean'],z0['mask']);zero_ok=False
    except ValueError:pass
    x,p=cache['ISO_NULL',seed];(z,d),(zh,dh)=p;q=causal_q(c,z,x['mask'],x['clock'],d,537)['Q'];qh=causal_q(c,zh,x['mask'],x['clock'],dh,537)['Q'];A=np.isfinite(q)&np.isfinite(qh);B=A[1:]&A[:-1]
    if A.sum()<100 or B.sum()<100:bad=True;break
    v=abs(np.diff(qh)[B])/(np.diff(x['clock'])[B]/np.median(np.diff(x['clock'])));iso.append({'seed':seed,'nmae':float(np.mean(abs(q[A]-qh[A]))),'far':float(np.mean(v>th))})
    x,p=cache['JUMP',seed];(z,d),(zh,dh)=p;q=causal_q(c,z,x['mask'],x['clock'],d,537)['Q'];qh=causal_q(c,zh,x['mask'],x['clock'],dh,537)['Q'];A=np.isfinite(q)&np.isfinite(qh);B=A[1:]&A[:-1]
    if A.sum()<100 or B.sum()<100:bad=True;break
    v=abs(np.diff(qh)[B])/(np.diff(x['clock'])[B]/np.median(np.diff(x['clock'])));ix=np.where(B)[0]+1;pk=int(ix[np.argmax(v)]);jump.append({'seed':seed,'nmae':float(np.mean(abs(q[A]-qh[A]))),'rho':rho(q[A],qh[A]),'detected':bool(288<=pk<=480 and v.max()>th)})
   except ValueError:bad=True;break
  el=time.perf_counter()-st
  if bad:rows.append({'id':c['id'],'status':'ABSTAIN','reason':'E_A_INSUFFICIENT','metrics':{'theta':th},'runtime_seconds':el});continue
  if not zero_ok:rows.append({'id':c['id'],'status':'INVALID_KILL','reason':'ZERO_NOT_ABSTAIN','metrics':{'theta':th},'runtime_seconds':el});continue
  mjr=float(np.median([x['rho'] for x in jump]));mjn=float(np.median([x['nmae'] for x in jump]));mi=float(np.median([x['nmae'] for x in iso]));far=float(np.mean([x['far'] for x in iso]));det=sum(x['detected'] for x in jump);status='PASS' if mjr>=.8 and mjn<=.2 and far<=.2 and det>=4 else 'FUTILITY_KILL';rows.append({'id':c['id'],'status':status,'reason':None if status=='PASS' else 'F2A_NUMERIC_FUTILITY','metrics':{'theta':th,'ISO':iso,'JUMP':jump,'median_iso_nmae':mi,'median_jump_nmae':mjn,'median_jump_rho':mjr,'mean_iso_far':far,'detections':det},'runtime_seconds':el})
 good=sorted([r for r in rows if r['status']=='PASS'],key=lambda r:(max(r['metrics']['median_iso_nmae'],r['metrics']['median_jump_nmae']),-r['metrics']['median_jump_rho'],r['metrics']['mean_iso_far'],r['runtime_seconds'],r['id']));prom=[r['id'] for r in good[:24]]
 for r in rows:
  if r['id'] in prom:r['status']='PROMOTE'
  elif r['status']=='PASS':r['status']='DROPPED_BUDGET';r['reason']='F2A cap24'
 rec={'schema':'BA-SRM8-F2A-v1','behavior_loaded':False,'model_fit':False,'candidate_Q_run':True,'numerical_F2A':True,'biological_claim':False,'input_hashes':hashes,'candidates':rows,'promoted_ids':prom,'promoted_ids_sha256':hashlib.sha256(json.dumps(prom,separators=(',',':')).encode()).hexdigest(),'runtime_seconds':sum(r['runtime_seconds'] for r in rows)};b=json.dumps(rec,allow_nan=False,sort_keys=True,separators=(',',':'))+'\n';
 with OUT.open('w') as f:f.write(b);f.flush();os.fsync(f.fileno())
 print({'promoted':len(prom)})
if __name__=='__main__':main()
