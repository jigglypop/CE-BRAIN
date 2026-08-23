import hashlib,numpy as np
from scipy.linalg import expm
from pathlib import Path
import sys
OLD=Path(__file__).resolve().parents[2]/'brain-physical-time-effective-dimension-funnel-20260823'/'artifacts';sys.path.insert(0,str(OLD));import f2_common_v2 as old
def _rng(seed):return np.random.default_rng(int.from_bytes(hashlib.sha256(f'BA-SRM9-F2-SH-v1|JUMP|{seed}|jump_mixing'.encode()).digest()[:8],'big'))
def generate(s,seed):
 if s!='JUMP':return old.generate(s,seed)
 N,T=12,768;dt=np.empty(T);dt[0]=0;dt[1:]=old.rng(s,seed,'clock_base').uniform(.75,1.25,T-1);gi=np.sort(old.rng(s,seed,'clock_gap_indices').choice(np.arange(1,T),3,False));dt[gi]=old.rng(s,seed,'clock_gap_sizes').uniform(4,8,3);clock=np.cumsum(dt);Z=_rng(seed).standard_normal((N,N));H,R=np.linalg.qr(Z,mode='reduced');sign=np.sign(np.diag(R));sign[sign==0]=1;H=np.ascontiguousarray(H*sign);xi=old.rng(s,seed,'latent').standard_normal((N,T));y=np.zeros((N,T));x=np.zeros((N,T))
 for t in range(T):
  r=2 if t<384 else 8;x[:,t]=H[:,:r]@xi[:r,t];a=np.exp(-dt[t]/6) if t else 0;y[:,t]=x[:,t] if t==0 else (1-a)*x[:,t]+a*y[:,t-1]
 m=(old.rng(s,seed,'mask_mcar').random((N,T))>=.1).astype(np.uint8);noisy=y+old.rng(s,seed,'noise').standard_normal((N,T))*np.sqrt(np.mean(y[:,:460]**2))/4
 return {'clean':np.ascontiguousarray(y),'noisy':np.ascontiguousarray(noisy),'mask':np.ascontiguousarray(m),'clock':np.ascontiguousarray(clock),'meta':{'gap_indices':gi.tolist(),'H':H,'x':x,'support_pre':2,'support_post':8}}
