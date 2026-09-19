"""CE-HPI1 fixed-slot context learning: curated 2026-09-18 candidate.

Consolidated without changing the accepted function bodies from the user's
CE_HPI1_LEARNING_20260918 archive. See PROVENANCE.json. This is HMM/EM research,
not a new biological learning law, calcium fit, or MaleCNS reproduction.
"""
from __future__ import annotations
from collections import Counter, defaultdict
from pathlib import Path
import argparse, json, time
import numpy as np
from numba import njit
from scipy.sparse import csr_matrix, diags

@njit(cache=True)
def forward(T, seq):
    n=len(seq); k=T.shape[2]; ns=T.shape[0]
    a=np.empty((n,k)); scales=np.empty(n)
    a[0,:]=1.0/k; scales[0]=1.0/ns
    for t in range(1,n):
        mat=T[seq[t-1],seq[t]]
        z=0.
        a[t,:]=0.
        for i in range(k):
            for j in range(k):a[t,j]+=a[t-1,i]*mat[i,j]
        z=a[t,:].sum()
        if z<=0.:raise ValueError('zero likelihood')
        a[t,:]/=z; scales[t]=z
    return a, scales

@njit(cache=True)
def expectation(T, seq, lag=-1):
    """lag=-1: full HPI1 smoothing; lag>=1: bounded lookahead statistics.
    Lag counts future observations used to credit the transition at t.
    """
    a,scales=forward(T,seq); n,k=a.shape
    counts=np.zeros_like(T)
    if lag<0:
        b=np.ones((n,k))
        for t in range(n-2,-1,-1):
            mat=T[seq[t],seq[t+1]]
            for i in range(k):
                v=0.
                for j in range(k):v+=mat[i,j]*b[t+1,j]
                b[t,i]=v/scales[t+1]
            for i in range(k):
                for j in range(k):
                    counts[seq[t],seq[t+1],i,j]+=a[t,i]*mat[i,j]*b[t+1,j]/scales[t+1]
    else:
        if lag<1:raise ValueError('lag must be >= 1 or -1')
        for t in range(n-1):
            bnext=np.ones(k)
            for s in range(min(n-1,t+lag)-1,t,-1):
                mat=T[seq[s],seq[s+1]]
                new=np.zeros(k)
                for i in range(k):
                    for j in range(k):new[i]+=mat[i,j]*bnext[j]
                total=new.sum()
                if total<=0.:raise ValueError('backward mass lost')
                bnext=new/total
            mat=T[seq[t],seq[t+1]]
            norm=0.
            for i in range(k):
                for j in range(k):norm+=a[t,i]*mat[i,j]*bnext[j]
            for i in range(k):
                for j in range(k):counts[seq[t],seq[t+1],i,j]+=a[t,i]*mat[i,j]*bnext[j]/norm
    return counts, np.log(scales).sum()

@njit(cache=True)
def maximize(T, counts):
    ns,_,k,_=T.shape
    out=T.copy()
    for x in range(ns):
        for i in range(k):
            total=0.
            for y in range(ns):
                for j in range(k): total+=counts[x,y,i,j]
            if total>0:
                for y in range(ns):
                    for j in range(k):out[x,y,i,j]=counts[x,y,i,j]/total
    return out

@njit(cache=True)
def fit_steps(T,seq,iterations,lag=-1):
    scores=np.empty(iterations)
    for it in range(iterations):
        counts,ll=expectation(T,seq,lag)
        scores[it]=ll; T=maximize(T,counts)
    return T,scores

def expanded_beliefs(T,sequence):
    seq=np.asarray(sequence,np.int64); a,s=forward(T,seq)
    ns,_,k,_=T.shape
    out=np.zeros((len(seq),ns*k))
    for t,sym in enumerate(seq):out[t,sym*k:(sym+1)*k]=a[t]
    return out,s

NEAR=np.array([1,1,1,1,1,1,2,2,2,2,1,1,1,4,6,1,1,1,5,5,1,1,7,0,0,0],dtype=np.int64)

FAR =np.array([1,1,1,1,1,1,3,3,3,3,1,1,1,4,4,1,1,1,5,6,1,1,7,0,0,0],dtype=np.int64)

GREY_REGIONS=[np.arange(0,6),np.arange(10,13),np.arange(15,18),np.arange(20,22)]

def metrics(T):
    # A full previous near/far trial removes arbitrary beginning-of-record
    # initialization; average the two previous contexts, forward filtering only.
    states=[]
    for current in (NEAR,FAR):
        state=np.mean([expanded_beliefs(T,np.r_[previous,current])[0][-26:]
                       for previous in (NEAR,FAR)],axis=0)
        states.append(state)
    aa,bb=states
    aa=aa-aa.mean(1,keepdims=True);bb=bb-bb.mean(1,keepdims=True)
    norm=np.linalg.norm(aa,axis=1)[:,None]*np.linalg.norm(bb,axis=1)[None,:]
    corr=aa@bb.T/norm
    # Within-region cross-trial mean of diagonal correlations.
    r1=float(np.diag(corr)[10:13].mean())
    r2=float(np.diag(corr)[15:18].mean())
    off=[]
    for i,ri in enumerate(GREY_REGIONS):
        for j,rj in enumerate(GREY_REGIONS):
            if i!=j:off.extend(corr[np.ix_(ri,rj)].ravel())
    return np.array([np.mean(off),r2,r1,corr.mean()]),corr

@njit(cache=True)
def metrics_fast(T, near=NEAR, far=FAR):
    ns,_,k,_=T.shape; n=len(near); allp=np.zeros((2,n,k))
    for which in range(2):
        current=near if which==0 else far
        for prev in range(2):
            previous=near if prev==0 else far
            seq=np.concatenate((previous,current))
            a,_=forward(T,seq)
            allp[which]+=a[n:]/2.
    corr=np.empty((n,n)); base=1./(ns*k)
    for i in range(n):
        ni=0.
        for c in range(k): ni+=allp[0,i,c]**2
        ni-=base
        for j in range(n):
            nj=0.;dot=0.
            for c in range(k):
                nj+=allp[1,j,c]**2
                if near[i]==far[j]:dot+=allp[0,i,c]*allp[1,j,c]
            nj-=base
            corr[i,j]=(dot-base)/np.sqrt(max(ni*nj,1e-30))
    r1=(corr[10,10]+corr[11,11]+corr[12,12])/3
    r2=(corr[15,15]+corr[16,16]+corr[17,17])/3
    grey=np.array([0,1,2,3,4,5,10,11,12,15,16,17,20,21])
    regions=np.array([0,0,0,0,0,0,1,1,1,2,2,2,3,3])
    total=0.; count=0
    for i in range(len(grey)):
        for j in range(len(grey)):
            if regions[i]!=regions[j]:total+=corr[grey[i],grey[j]];count+=1
    # Four-position pre-reward windows used in the author model analysis.
    r2pre=(corr[15,15]+corr[16,16]+corr[17,17]+corr[18,18])/4.
    r1pre=(corr[10,10]+corr[11,11]+corr[12,12]+corr[13,13])/4.
    return np.array([total/count,r2,r1,corr.mean(),r2pre,r1pre])

@njit(cache=True)
def score(T,seq):
    k=T.shape[2];a=np.ones(k)/k;ll=-np.log(T.shape[0])
    for t in range(1,len(seq)):
        b=np.zeros(k);mat=T[seq[t-1],seq[t]]
        for i in range(k):
            for j in range(k):b[j]+=a[i]*mat[i,j]
        z=b.sum()
        if z<=0 or not np.isfinite(z):return -np.inf
        a=b/z;ll+=np.log(z)
    return ll

def dense(T):
    ns,_,k,_=T.shape
    return T.transpose(0,2,1,3).reshape(ns*k,ns*k).copy()

def block(D,ns,k):return D.reshape(ns,k,ns,k).transpose(0,2,1,3).copy()

def initialize(seed,k=100):
    raw=np.random.RandomState(seed).rand(8*k,8*k);raw/=raw.sum(1,keepdims=True)
    return raw.reshape(8,k,8,k).transpose(0,2,1,3).copy()

def make_streams(seed,stages=50):
    rng=np.random.default_rng(seed+239721)
    return np.stack([np.concatenate([NEAR if x==0 else FAR for x in rng.integers(0,2,20)]) for _ in range(stages)])

def crossing(y,thresh=.3):
    v=np.where(y<thresh)[0]
    if not len(v):return None
    i=int(v[0])
    if i==0:return 0.
    return float(i-1+(y[i-1]-thresh)/(y[i-1]-y[i]))

def evaluate(T):
 rng=np.random.default_rng(69759);types=np.tile([0,1],20);rng.shuffle(types)
 seq=np.concatenate([NEAR if c==0 else FAR for c in types]);a,_=forward(T,seq)
 p=[];targets=[]
 for i,kind in enumerate(types):
  for ix in [13,18]:
   t=i*26+ix;w=T[seq[t],6].sum(axis=1);p.append(float(a[t]@w));targets.append(float((kind==0 and ix==13) or (kind==1 and ix==18)))
 p=np.clip(np.array(p),0,1);y=np.array(targets);correct=np.where(p==.5,.5,(p>.5)==y)
 _,corr=metrics(T)
 return {'trials':40,'binary_reward_probes':80,'accuracy':float(np.mean(correct)),'brier':float(np.mean((p-y)**2)),
 'initial_region_correlation':float(np.mean(np.diag(corr)[:6])),
 'end_grey_correlation':float(np.mean(np.diag(corr)[20:22])),
 'pre_r2_correlation':float(np.mean(np.diag(corr)[15:19])),
 'pre_r1_correlation':float(np.mean(np.diag(corr)[10:14])),
 'probabilities':p.tolist(),'target':y.tolist(),
 'scope':'new trial ordering of trained templates; not novel cue/length transfer; not animal lick-rate fit'}

def propose_path(T,seq,history=6,entry_fraction=.1,min_occurrences=2):
    ns,_,k,_=T.shape;a,sc=forward(T,seq)
    occ=np.zeros((ns,k));context=defaultdict(Counter);where=defaultdict(list)
    for t in range(len(seq)):occ[seq[t]]+=a[t]
    for t in range(history-1,len(seq)-1):
        h=tuple(int(x) for x in seq[t-history+1:t+1]);y=int(seq[t+1]);context[h][y]+=1;where[(h,y)].append(t)
    ranked=[]
    for (h,y),times in where.items():
        if len(times)<min_occurrences:continue
        empirical=context[h][y]/sum(context[h].values())
        residual=sum(max(0.,np.log(empirical)-np.log(sc[t+1])) for t in times)
        ranked.append((residual,h,y,times))
    if not ranked:return None,{'reason':'insufficient_repeated_history'}
    residual,h,y,times=max(ranked,key=lambda z:z[0])
    if residual<.01:return None,{'reason':'no_material_predictable_surprise','residual':float(residual)}
    word=list(h)+[y];D=dense(T);syms=np.arange(ns*k)//k
    chosen=[]
    for symbol in word[1:]:
        pool=[int(j) for j in np.argsort(occ[symbol]) if symbol*k+int(j) not in chosen]
        if not pool:return None,{'reason':'fixed_slot_capacity_exhausted'}
        chosen.append(symbol*k+pool[0])
    oldmass=[float(occ[p//k,p%k]) for p in chosen]
    # Redirect each recycled slot to an active same-emission donor, preserving
    # immediate sensory mass for unmodified rows. Slot identity/emission stays.
    for ci in chosen:
        symbol=ci//k;pool=[symbol*k+int(j) for j in np.argsort(-occ[symbol]) if symbol*k+int(j) not in chosen]
        if not pool:return None,{'reason':'no_same_emission_donor'}
        donor=pool[0];D[:,donor]+=D[:,ci];D[:,ci]=0.
    # Keep the old predictive continuation at the last observed symbol.
    finalsymbol=word[-1];endbelief=np.mean([a[t+1] for t in times],axis=0)
    D[chosen[-1]]=endbelief@D[finalsymbol*k:(finalsymbol+1)*k]
    for left,right in zip(chosen[:-1],chosen[1:]):D[left]=0.;D[left,right]=1.
    entry=word[0];firstsymbol=word[1];first=chosen[0]
    for i in range(entry*k,(entry+1)*k):
        if i in chosen:continue
        inds=(syms==firstsymbol);mass=D[i,inds].sum()
        D[i,inds]*=1-entry_fraction;D[i,first]+=entry_fraction*mass
    rows=D.sum(1)
    if np.any(rows<=0) or np.any(D<0) or not np.isfinite(D).all():raise ArithmeticError('invalid path proposal')
    D/=rows[:,None]
    return block(D,ns,k),dict(word=word,occurrences=len(times),predictable_surprise=float(residual),reused_state_ids=chosen,reused_posterior_mass=oldmass,entry_fraction=entry_fraction,states_before=ns*k,states_after=ns*k)

def refine(T,seq,use_paths=True,rounds=4,iterations=40):
    events=[];curves=[metrics_fast(T)]
    for r in range(rounds):
        before=score(T,seq);oldmetric=metrics_fast(T)
        if use_paths:U,event=propose_path(T,seq)
        else:U=None;event={'reason':'plain_EM_control'}
        proposed=U is not None
        if U is None:U=T.copy()
        for it in range(iterations):C,_=expectation(U,seq);U=maximize(U,C)
        after=score(U,seq);accepted=np.isfinite(after) and after>=before-1e-12
        if accepted:T=U
        # A proposal is not committed until its complete refinement is evaluated.
        curves.extend([oldmetric.copy() for _ in range(iterations-1)]);curves.append(metrics_fast(T))
        event.update(round=r,proposed=proposed,before=float(before),after=float(after),accepted=bool(accepted),em_calls=iterations)
        events.append(event)
    return T,np.asarray(curves),events

@njit(cache=True)
def forward_safe(T,seq):
    n=len(seq);ns,_,k,_=T.shape;a=np.zeros((n,k));sc=np.zeros(n)
    a[0,:]=1./k;sc[0]=1./ns
    for t in range(1,n):
        for i in range(k):
            for j in range(k):a[t,j]+=a[t-1,i]*T[seq[t-1],seq[t],i,j]
        total=a[t].sum()
        if total<=0 or not np.isfinite(total):return a,sc,t
        a[t]/=total;sc[t]=total
    return a,sc,-1

def kernel(T,hold=.1,skip=.1,protected=True,reward_skip=None):
    T=np.asarray(T,dtype=float)
    if T.ndim!=4 or T.shape[0]!=T.shape[1] or T.shape[2]!=T.shape[3]:
        raise ValueError('T must have shape [symbols,symbols,clones,clones]')
    if not np.isfinite(T).all() or np.any(T<0) or not np.allclose(T.sum((1,3)),1.,atol=1e-12,rtol=0):
        raise ValueError('T must be finite, nonnegative, and row stochastic')
    if not (np.isfinite(hold) and np.isfinite(skip) and 0<=hold<=1 and 0<=skip<=1):
        raise ValueError('hold and skip must be probabilities')
    if reward_skip is not None and not (np.isfinite(reward_skip) and 0<=reward_skip<=1):
        raise ValueError('reward_skip must be a probability')
    ns,_,k,_=T.shape;n=ns*k
    if protected and ns<=6:raise ValueError('protected reward symbol 6 is not present')
    D=T.transpose(0,2,1,3).reshape(n,n)
    A=csr_matrix(D);s=np.full(n,skip,dtype=float)
    if protected:s[6*k:7*k]=0. if reward_skip is None else reward_skip
    S=diags(s);V=diags(1-s)
    # First, second, or third latent step is the next observed event.
    # The last term forces observation at the truncation; rows sum to 1.
    AS=A@S;K=A@V+AS@A@V+AS@AS@A
    K=(1-hold)*K+hold*diags(np.ones(n))
    dense=K.toarray()
    if not np.allclose(dense.sum(1),1,atol=1e-12):raise ArithmeticError('kernel mass lost')
    return dense.reshape(ns,k,ns,k).transpose(0,2,1,3).copy()

def stretch(seq,extra=5):
    return np.r_[seq[:13],np.ones(extra,dtype=np.int64),seq[13:18],np.ones(extra,dtype=np.int64),seq[18:]].astype(np.int64)

def templates(T):
    states=[]
    for current in (NEAR,FAR):
        p=np.mean([expanded_beliefs(T,np.r_[previous,current])[0][-26:] for previous in (NEAR,FAR)],axis=0)
        states.append(p)
    n,f=states
    rows=np.stack([(n[:6].mean(0)+f[:6].mean(0))/2,n[10:13].mean(0),f[10:13].mean(0),n[15:18].mean(0),f[15:18].mean(0),(n[20:22].mean(0)+f[20:22].mean(0))/2,n[13],f[13],f[14]])
    total=rows.sum(0);decoder=np.divide(rows,total[None,:],out=np.zeros_like(rows),where=total[None,:]>0)
    return decoder

def scenario(T,K,decoder,current,extra=5):
    s=stretch(current,extra);profiles=[];probes=[];scales=[];fails=[]
    k=T.shape[-1]
    for previous in (NEAR,FAR):
        seq=np.r_[previous,s].astype(np.int64);a,sc,fail=forward_safe(K,seq)
        fails.append(None if fail<0 else int(fail));scales.append(sc.tolist())
        if fail>=0:continue
        full=np.zeros((len(s),8*k))
        for i,sy in enumerate(s):full[i,sy*k:(sy+1)*k]=a[26+i]
        profiles.append(full@decoder.T)
        probes.append([float(a[26+ix]@K[seq[26+ix],6].sum(1)) for ix in [13+extra,18+2*extra]])
    if len(profiles)!=2:
        return dict(valid=False,failure_positions=fails,scales=scales)
    p=np.mean(profiles,axis=0);v=np.mean(probes,axis=0)
    return dict(valid=True,profiles=p.tolist(),added_grey_mean=p[13:13+extra].mean(0).tolist(),
                first_object_entry=p[13+extra].tolist(),reward_probes=v.tolist(),scales=scales,
                nll_nats_per_symbol=float(-np.log(np.array(scales)[:,26:]).mean()))

def assess(T,variant,hold=.1,skip=.1,extra=5,decoder=None):
    if decoder is None:decoder=templates(T)
    K=T if variant=='baseline' else kernel(T,hold,0. if variant=='hold_only' else skip,variant!='skip_all')
    n=scenario(T,K,decoder,NEAR,extra);f=scenario(T,K,decoder,FAR,extra)
    valid=n['valid'] and f['valid'];result=dict(variant=variant,hold=hold,skip=skip,extra=extra,near=n,far=f,valid=valid)
    if valid:
        nm=np.array(n['added_grey_mean']);fm=np.array(f['added_grey_mean'])
        pred=np.r_[n['reward_probes'],f['reward_probes']];targets=np.array([1,0,0,1])
        result.update(near_stay_mass=float(nm[1]),far_shift_mass=float(fm[4]),far_reanchor_entry_mass=float(f['first_object_entry'][7]),
                      near_stays=bool(nm[1]>.5),far_shifts=bool(fm[4]>.5),far_reanchors=bool(f['first_object_entry'][7]>.5),
                      all_three=bool(nm[1]>.5 and fm[4]>.5 and f['first_object_entry'][7]>.5),
                      stretch_reward_accuracy=float(np.mean((pred>.5)==targets)),stretch_reward_brier=float(np.mean((pred-targets)**2)))
    else:
        result.update(near_stays=False,far_shifts=False,far_reanchors=False,all_three=False,
                      stretch_reward_accuracy=None,stretch_reward_brier=None)
    result['normal_reward']=evaluate(K)
    return result

