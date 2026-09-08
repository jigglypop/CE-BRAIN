"""A small, exact reference for context-sensitive indexing and predictive geometry.

This is a clone-emission HMM, a pre-existing model class, NOT a novel biological
mechanism. Latent slot IDs and their emissions are fixed; only transitions are
learned. Missing observations are marginalized, never replaced with true state.
"""
from __future__ import annotations
from dataclasses import dataclass
import itertools
import numpy as np


def stochastic(x, name):
    a=np.array(x,dtype=float,copy=True)
    if a.ndim!=2 or not np.isfinite(a).all() or np.any(a<0) or not np.allclose(a.sum(1),1,atol=1e-12):
        raise ValueError(f'{name} must be a finite row-stochastic matrix')
    return a

@dataclass
class ContextModel:
    transition: np.ndarray
    emission: np.ndarray
    initial: np.ndarray

    def __post_init__(self):
        self.transition=stochastic(self.transition,'transition')
        self.emission=stochastic(self.emission,'emission')
        n=len(self.transition)
        self.initial=np.array(self.initial,dtype=float,copy=True)
        if self.transition.shape!=(n,n) or len(self.emission)!=n or self.initial.shape!=(n,) or np.any(self.initial<0) or not np.isfinite(self.initial).all() or not np.isclose(self.initial.sum(),1):
            raise ValueError('incompatible initial/transition/emission')
        self.emission.setflags(write=False);self.initial.setflags(write=False)

    def emission_at(self, symbol):
        if symbol is None: return np.ones(len(self.initial))
        if isinstance(symbol,(bool,np.bool_)) or not isinstance(symbol,(int,np.integer)) or not 0<=symbol<self.emission.shape[1]:
            raise ValueError('symbol must be a valid integer ID or missing (None)')
        return self.emission[:,symbol]

    def forward(self, observations):
        if not len(observations): raise ValueError('empty observation sequence')
        alphas=[];scales=[];prev=self.initial.copy()
        for t,y in enumerate(observations):
            pred=prev if t==0 else prev@self.transition
            un=pred*self.emission_at(y);norm=float(un.sum())
            if not norm>0: raise ValueError('observation has zero probability under model')
            prev=un/norm;alphas.append(prev);scales.append(norm)
        return np.asarray(alphas),np.asarray(scales)

    def posterior(self, observations):
        return self.forward(observations)[0][-1].copy()

    def expectation(self, observations):
        alpha,scales=self.forward(observations);n=len(self.initial)
        beta=np.ones_like(alpha);counts=np.zeros((n,n))
        for t in range(len(observations)-2,-1,-1):
            e=self.emission_at(observations[t+1])
            beta[t]=self.transition@(e*beta[t+1])/scales[t+1]
            pair=alpha[t,:,None]*self.transition*(e*beta[t+1])[None,:]/scales[t+1]
            counts+=pair
        return counts,float(np.log(scales).sum())

    def fit(self, sequences, iterations=120):
        if not sequences or type(iterations) is not int or iterations<0: raise ValueError('invalid training request')
        # Each past episode can be smoothed here. Evaluation always uses forward
        # filtering only. Replay does not add independent observations to the data.
        histories=[]
        for epoch in range(iterations+1):
            counts=np.zeros_like(self.transition);ll=0.
            for seq in sequences:
                c,v=self.expectation(seq);counts+=c;ll+=v
            histories.append(ll)
            if epoch==iterations:break
            sums=counts.sum(1);T=self.transition.copy();used=sums>0
            T[used]=counts[used]/sums[used,None]
            self.transition=T
        return np.asarray(histories)

    def future_likelihoods(self, horizon):
        """P(future *joint word* | present slot); exact, exponential in horizon.
        Observations start after the next transition, not at the present symbol.
        """
        if type(horizon) is not int or not 0<=horizon<=5:raise ValueError('reference horizon must be 0..5')
        n=len(self.initial);s=self.emission.shape[1];L=np.ones((n,1))
        for _ in range(horizon):
            L=np.concatenate([self.transition@(self.emission[:,y,None]*L) for y in range(s)],axis=1)
        if not np.allclose(L.sum(1),1,atol=2e-12):raise ArithmeticError('joint predictive mass lost')
        return L


def predictive_distribution(belief, likelihoods):
    b=np.asarray(belief,dtype=float);L=np.asarray(likelihoods,dtype=float)
    if b.shape!=(len(L),) or np.any(b<0) or not np.isfinite(b).all() or not np.isclose(b.sum(),1):raise ValueError('invalid belief')
    return b@L


def hellinger_chord_squared(p,q):
    p=np.asarray(p,float);q=np.asarray(q,float)
    if p.shape!=q.shape or np.any(p<0) or np.any(q<0) or not np.isfinite(p).all() or not np.isfinite(q).all() or not np.isclose(p.sum(),1) or not np.isclose(q.sum(),1):raise ValueError('invalid probability vectors')
    return float(4*np.sum((np.sqrt(p)-np.sqrt(q))**2))


def mixture_fisher(p,q,rho=.5):
    """1-D Fisher metric of rho*p+(1-rho)*q. No invented ridge directions."""
    if not 0<rho<1:raise ValueError('interior mixture required')
    hellinger_chord_squared(p,q)
    p=np.asarray(p);q=np.asarray(q);r=rho*p+(1-rho)*q;positive=r>0
    return float(np.sum((p[positive]-q[positive])**2/r[positive]))


def template(seed=0):
    # S,A,B,G,R1,R2,E. Six fixed G slots; no contextual label supplied to EM.
    slots=np.array([0,1,2,3,3,3,3,3,3,4,5,6]);n=len(slots)
    B=np.eye(7)[slots];rng=np.random.default_rng(seed)
    T=rng.gamma(1.,1.,(n,n));T/=T.sum(1,keepdims=True)
    initial=np.zeros(n);initial[0]=1
    return ContextModel(T,B,initial),slots


def toy_sequences():
    # A schematic disambiguation task, not the paper's complete 2ACDC stimulus
    # stream. Training length/order is not fit to the animal timing summaries.
    return [[0,1,3,3,3,4,6],[0,2,3,3,3,5,6]]


def initialize_from_past_episodes(model, sequences):
    """Observed-prefix / empirical-future quotient initialization.

    Uses complete *past training episodes*, not test futures or latent labels.
    Prefixes are merged only if current symbol AND complete empirical suffix law
    agree. Slots are drawn from the existing fixed emission-matched pool.
    This is a finite-data state construction, NOT a proven cortical plasticity
    rule or an identified biological learning trajectory. Complexity can grow
    with the number/length of episodes. Insufficient slot capacity raises.
    """
    from collections import Counter,defaultdict
    from fractions import Fraction
    if not sequences: raise ValueError('past episodes required')
    futures=defaultdict(Counter)
    for raw in sequences:
        if not len(raw):raise ValueError('empty episode')
        seq=tuple(raw)
        for symbol in seq:model.emission_at(symbol)
        if any(s is None for s in seq):raise ValueError('initializer requires complete past training episodes')
        for t in range(len(seq)):futures[seq[:t+1]][seq[t+1:]]+=1
    signatures={}
    for prefix,counts in futures.items():
        total=sum(counts.values())
        signatures[prefix]=(prefix[-1],tuple(sorted((suffix,Fraction(count,total)) for suffix,count in counts.items())))
    pool={y:list(np.where(model.emission[:,y]==1)[0]) for y in range(model.emission.shape[1])}
    bysignature={};mapping={}
    for prefix in sorted(signatures,key=lambda p:(len(p),p)):
        key=signatures[prefix];symbol=prefix[-1]
        if key not in bysignature:
            if not pool[symbol]:raise ValueError('fixed emission-matched slot budget exhausted')
            bysignature[key]=pool[symbol].pop(0)
        mapping[prefix]=bysignature[key]
    n=len(model.initial);counts=np.zeros((n,n));initial=np.zeros(n)
    for raw in sequences:
        seq=tuple(raw);initial[mapping[seq[:1]]]+=1
        for t in range(len(seq)-1):counts[mapping[seq[:t+1]],mapping[seq[:t+2]]]+=1
    T=model.transition.copy();rows=counts.sum(1)>0;T[rows]=counts[rows]/counts[rows].sum(1,keepdims=True)
    terminal_slots={mapping[p] for p,c in futures.items() if set(c)=={()}}
    for s in terminal_slots:T[s]=0;T[s,s]=1
    model.transition=T;model.initial=initial/initial.sum();model.initial.setflags(write=False)
    return {'prefix_count':len(mapping),'retained_slots':len(bysignature),'prefix_to_slot':{'/'.join(map(str,k)):int(v) for k,v in mapping.items()},
            'distinct_training_episodes':len(set(tuple(s) for s in sequences))}
