"""Corrected finite F2 generator; no candidate-Q calculation."""
from __future__ import annotations
import hashlib,json,numpy as np
from scipy.linalg import expm
from funnel_core_v2 import ROOT
def rng(s,b,n):return np.random.default_rng(int.from_bytes(hashlib.sha256(f'BA-SRM8-F2-SH-v2|{s}|{b}|{n}'.encode()).digest()[:8],'big'))
def generate(s,b):
 N,T=12,768;dt=np.empty(T);dt[0]=0;dt[1:]=rng(s,b,'clock_base').uniform(.75,1.25,T-1);gi=np.sort(rng(s,b,'clock_gap_indices').choice(np.arange(1,T),3,False));dt[gi]=rng(s,b,'clock_gap_sizes').uniform(4,8,3);clock=np.cumsum(dt)
 xi=rng(s,b,'latent').standard_normal((N,T)); y=np.zeros((N,T));
 if s=='ZERO_NULL': clean=np.zeros((N,T))
 else:
  if s=='ISO_NULL': B=None
  elif s=='JUMP': B='jump'
  else:
   k=0
   while True:
    A=rng(s,b,f'skew:{k}').standard_normal((N,N));B=A-A.T;n=np.linalg.norm(B,2)
    if n>1e-12:B/=n;break
    k+=1
  for t in range(T):
   if B is None:x=xi[:,t]
   elif isinstance(B,str) and B=='jump':mu=np.zeros(N);mu[:2 if t<384 else 8]=1;x=np.sqrt(mu)*xi[:,t]
   else:mu=np.exp(-np.arange(N)/(3.5+2*np.sin(2*np.pi*t/384)));x=expm(.35*np.sin(2*np.pi*t/256)*B)@(np.sqrt(mu)*xi[:,t])
   y[:,t]=x if t==0 else (1-np.exp(-dt[t]/6))*x+np.exp(-dt[t]/6)*y[:,t-1]
  clean=y
 p={'MISS30':.3,'MISS50':.5}.get(s,.1);mask=(rng(s,b,'mask_mcar').random((N,T))>=p).astype(np.uint8);sd=np.sqrt(np.mean(clean[:,:460]**2))/4;noisy=clean.copy() if s=='ZERO_NULL' else clean+rng(s,b,'noise').standard_normal((N,T))*sd;meta={'gap_indices':gi.tolist()}
 if s=='BLOCK30':
  st=rng(s,b,'block_start').integers(0,T-int(.3*T)+1,N);meta['block_starts']=st.tolist()
  for i,a in enumerate(st):mask[i,a:a+int(.3*T)]=0
 if s=='ART10':
  sel=rng(s,b,'artifact_select').random((N,T))<.01;sg=np.where(rng(s,b,'artifact_sign').random((N,T))<.5,-1.,1.);noisy+=sel*sg*(10*np.std(clean[:,:460],ddof=0));meta['artifact_count']=int(sel.sum())
 if s=='REVERSE':clean,noisy,mask=clean[:,::-1],noisy[:,::-1],mask[:,::-1];clock=clock[-1]-clock[::-1]
 return {'clean':np.ascontiguousarray(clean,dtype=np.float64),'noisy':np.ascontiguousarray(noisy,dtype=np.float64),'mask':np.ascontiguousarray(mask,dtype=np.uint8),'clock':np.ascontiguousarray(clock,dtype=np.float64),'meta':meta}
