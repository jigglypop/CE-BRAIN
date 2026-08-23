"""Exact configured F2 generator; contains no candidate-Q or gate evaluation."""
from __future__ import annotations
import hashlib,json
from pathlib import Path
import numpy as np
from scipy.linalg import expm
from funnel_core_v2 import ROOT
def stream(s,b,name):return np.random.default_rng(int.from_bytes(hashlib.sha256(f'BA-SRM8-F2-SH-v2|{s}|{b}|{name}'.encode()).digest()[:8],'big'))
def generate(scenario,base):
 cfg=json.loads((ROOT/'f2-config.json').read_text());N,T=cfg['N'],cfg['T'];dt=np.empty(T,dtype=np.float64);dt[0]=0;dt[1:]=stream(scenario,base,'clock_base').uniform(.75,1.25,T-1);idx=np.sort(stream(scenario,base,'clock_gap_indices').choice(np.arange(1,T),3,replace=False));dt[idx]=stream(scenario,base,'clock_gap_sizes').uniform(4,8,3);clock=np.cumsum(dt,dtype=np.float64)
 def smooth(reverse=False):
  k=0
  while True:
   A=stream(scenario,base,f'skew:{k}').standard_normal((N,N));B=A-A.T;norm=np.linalg.norm(B,2)
   if norm>1e-12:break
   k+=1
  B/=norm;xi=stream(scenario,base,'latent').standard_normal((N,T));y=np.empty((N,T));
  for t in range(T):
   mu=np.exp(-np.arange(N)/(3.5+2*np.sin(2*np.pi*t/384)));x=expm(.35*np.sin(2*np.pi*t/256)*B)@(np.sqrt(mu)*xi[:,t]);y[:,t]=x if t==0 else (1-np.exp(-dt[t]/6))*x+np.exp(-dt[t]/6)*y[:,t-1]
  return y
 if scenario=='ZERO_NULL':clean=np.zeros((N,T))
 elif scenario=='ISO_NULL':clean=np.empty((N,T));xi=stream(scenario,base,'latent').standard_normal((N,T));clean[:,0]=xi[:,0];
 else:clean=smooth()
 if scenario=='JUMP':
  xi=stream(scenario,base,'latent').standard_normal((N,T));clean=np.empty((N,T));
  for t in range(T):
   mu=np.zeros(N);mu[:2 if t<384 else 8]=1;x=np.sqrt(mu)*xi[:,t];clean[:,t]=x if t==0 else (1-np.exp(-dt[t]/6))*x+np.exp(-dt[t]/6)*clean[:,t-1]
 p={'MISS30':.3,'MISS50':.5}.get(scenario,.1);mask=(stream(scenario,base,'mask_mcar').random((N,T))>=p).astype(np.uint8);sd=np.sqrt(np.mean(clean[:,:460]**2))/4;noisy=clean if scenario=='ZERO_NULL' else clean+stream(scenario,base,'noise').standard_normal((N,T))*sd;meta={'gap_indices':idx.tolist()}
 if scenario=='BLOCK30':
  starts=stream(scenario,base,'block_start').integers(0,T-int(.3*T)+1,N);meta['block_starts']=starts.tolist()
  for i,a in enumerate(starts):mask[i,a:a+int(.3*T)]=0
 if scenario=='ART10':
  select=stream(scenario,base,'artifact_select').random((N,T))<.01;sign=np.where(stream(scenario,base,'artifact_sign').random((N,T))<.5,-1.,1.);noisy=noisy+select*sign*(10*np.std(clean[:,:460],ddof=0));meta['artifact_count']=int(select.sum())
 if scenario=='REVERSE':clean,noisy,mask=clean[:,::-1],noisy[:,::-1],mask[:,::-1];clock=clock[-1]-clock[::-1]
 return {'clean':np.ascontiguousarray(clean,dtype=np.float64),'noisy':np.ascontiguousarray(noisy,dtype=np.float64),'mask':np.ascontiguousarray(mask,dtype=np.uint8),'clock':np.ascontiguousarray(clock,dtype=np.float64),'meta':meta}
