"""RGM-3: conservative, resource-limited local capture reference model.

Amounts p, bound amounts b, patch measures m, and concentrations p/m are
separate. CaMKII-like catalytic signals are NOT decremented as material.
This is a conditional model, not identified brain chemistry or neural code.
"""
from __future__ import annotations
import math
from dataclasses import dataclass
import numpy as np
from scipy.linalg import expm
from scipy.optimize import brentq


def vec(x, name, length=None, strictly_positive=False):
    raw = np.asarray(x)
    if raw.dtype.kind not in 'iuf' or raw.ndim != 1:
        raise TypeError(f'{name}: real, nonboolean vector required')
    v = np.array(raw, dtype=float, copy=True)
    if (length is not None and len(v) != length) or not np.isfinite(v).all():
        raise ValueError(f'{name}: invalid shape or nonfinite')
    if np.any(v <= 0 if strictly_positive else v < 0):
        raise ValueError(f'{name}: invalid sign')
    return v


def scalar(x, name, positive=False):
    if isinstance(x, (bool, np.bool_)) or not isinstance(x, (int,float,np.integer,np.floating)):
        raise TypeError(f'{name}: nonboolean real required')
    x=float(x)
    if not math.isfinite(x) or (x <= 0 if positive else x < 0):
        raise ValueError(f'{name}: invalid range')
    return x


@dataclass(frozen=True)
class Model:
    capacities: np.ndarray
    sites: np.ndarray
    conductance: np.ndarray
    on_rates: np.ndarray
    off_rates: np.ndarray

    def __post_init__(self):
        cap=vec(self.capacities,'capacity', strictly_positive=True)
        s=np.asarray(self.sites)
        if s.dtype.kind not in 'iu' or s.shape!=cap.shape or np.any(s<0):
            raise ValueError('sites must be aligned nonnegative integer indices')
        G=np.array(self.conductance,dtype=float,copy=True)
        if G.ndim!=2 or G.shape[0]!=G.shape[1] or not np.isfinite(G).all():
            raise ValueError('finite square conductance required')
        if np.any(G<0) or np.any(np.diag(G)!=0) or not np.allclose(G,G.T,rtol=0,atol=1e-13):
            raise ValueError('conductance must be symmetric, nonnegative, zero-diagonal')
        if max(s,default=-1)>=len(G):raise ValueError('site out of range')
        for name,v in [('capacities',cap),('sites',s.astype(np.int64,copy=True)),
                       ('conductance',G),('on_rates',vec(self.on_rates,'on',len(cap))),
                       ('off_rates',vec(self.off_rates,'off',len(cap)))]:
            v.setflags(write=False);object.__setattr__(self,name,v)

    def validate_state(self,p,b,area):
        p=vec(p,'free amount',len(self.conductance))
        b=vec(b,'bound amount',len(self.capacities))
        m=vec(area,'patch measure',len(p),strictly_positive=True)
        if np.any(b>self.capacities):raise ValueError('bound amount exceeds capacity')
        return p,b,m

    def rhs(self,t,y,area_fn,tag_fn=None):
        n=len(self.conductance);p=y[:n];b=y[n:]
        m=np.asarray(area_fn(t),float)
        tags=np.ones(len(b)) if tag_fn is None else np.asarray(tag_fn(t),float)
        c=p/m;S=np.diag(self.conductance.sum(axis=1))-self.conductance
        R=self.on_rates*tags*c[self.sites]*(self.capacities-b)-self.off_rates*b
        dp=-S@c
        np.add.at(dp,self.sites,-R)
        return np.r_[dp,R]


def binding_pair(p,b,capacity,on,off,dt):
    """Exact reversible binding in ONE frozen patch; on includes tag/area.

    b'=on*(p+b-b)*(capacity-b)-off*b, p+b constant.
    Stable Riccati solution, including no-reaction and double-root cases.
    """
    p=scalar(p,'p');b=scalar(b,'b');C=scalar(capacity,'capacity',True)
    a=scalar(on,'on');d=scalar(off,'off');dt=scalar(dt,'dt')
    if b>C:raise ValueError('bound amount above capacity')
    if dt==0:return p,b
    if (a==0 and d==0) or (d==0 and (p==0 or b==C)) or (a==0 and b==0):
        return p,b  # Exact stationary boundaries, without a one-ulp drift.
    q=p+b
    if a==0:
        bn=b*math.exp(-d*dt)
    else:
        disc=math.sqrt(d*d+2*a*d*(q+C)+(a*(q-C))**2)
        total=a*(q+C)+d
        root=2*a*q*C/(total+disc) if total+disc else 0.
        delta=b-root
        if disc==0:
            bn=root+delta/(1-a*delta*dt)
        else:
            e=math.exp(-disc*dt)
            den=1-a*delta*(-math.expm1(-disc*dt))/disc
            bn=root+delta*e/den
    tol=5e-13*max(1.,q,C)
    if bn < -tol or bn > min(q,C)+tol:raise ArithmeticError('pair invariant lost')
    # Remove only floating-point residue, never large unphysical excursions.
    bn=min(max(bn,0.),min(q,C))
    return q-bn,bn


def split_step(model,p,b,t,dt,area_fn,tag_fn=None):
    """Symmetric reaction sweeps / exact diffusion / reverse sweeps.

    Coefficients sampled at step midpoint. No source or loss in this reference.
    Exact subflows; the full noncommuting problem is second-order, not exact.
    """
    dt=scalar(dt,'dt');p,b,m=model.validate_state(p,b,area_fn(t+dt/2))
    tags=np.ones(len(b)) if tag_fn is None else vec(tag_fn(t+dt/2),'tag',len(b))
    if dt==0:return p,b
    rates=model.on_rates*tags/m[model.sites]
    def sweep(order):
        for j in order:
            i=model.sites[j]
            p[i],b[j]=binding_pair(p[i],b[j],model.capacities[j],rates[j],model.off_rates[j],dt/2)
    sweep(range(len(b)))
    S=np.diag(model.conductance.sum(axis=1))-model.conductance
    p=expm(-dt*S/m[None,:])@p
    if min(p,default=0)<-1e-12:raise ArithmeticError('transport positivity lost')
    p=np.maximum(p,0.)
    sweep(reversed(range(len(b))))
    return p,b


def integrate(model,p,b,times,area_fn,tag_fn=None):
    times=np.asarray(times,float)
    if times.ndim!=1 or len(times)<2 or not np.isfinite(times).all() or np.any(np.diff(times)<=0):
        raise ValueError('strictly increasing finite times required')
    p,b,_=model.validate_state(p,b,area_fn(times[0]));out=[np.r_[p,b]]
    for t,dt in zip(times[:-1],np.diff(times)):
        p,b=split_step(model,p,b,float(t),float(dt),area_fn,tag_fn)
        out.append(np.r_[p,b])
    return np.asarray(out)


def equilibrium(total,areas,capacities,kd):
    """Connected, fixed geometry, positive fixed affinities, closed pool.

    c* solves sum(areas)*c + sum(C*c/(Kd+c)) = total, strictly monotonic.
    """
    total=scalar(total,'total');m=vec(areas,'areas',strictly_positive=True)
    C=vec(capacities,'capacities',strictly_positive=True)
    K=vec(kd,'Kd',len(C),strictly_positive=True)
    if total==0:return np.zeros_like(m),np.zeros_like(C),0.
    mass=float(m.sum())
    c=brentq(lambda x:mass*x+np.sum(C*x/(K+x))-total,0,total/mass,xtol=1e-14)
    return m*c,C*c/(K+c),c


def entropy(p,b,pstar,bstar,cap):
    """Relative ideal-mixture free energy, fixed geometry and rates only."""
    from scipy.special import xlogy
    p=np.asarray(p);b=np.asarray(b);v=np.asarray(cap)-b
    return float(np.sum(xlogy(p,p/pstar)-p+pstar)+
                 np.sum(xlogy(b,b/bstar)+xlogy(v,v/(cap-bstar))))


def capacity_response(areas,capacities,kd,c):
    C=np.asarray(capacities);K=np.asarray(kd)
    slope=C*K/(K+c)**2
    denominator=np.sum(areas)+slope.sum()
    # Off-diagonal competition plus direct diagonal occupancy term.
    return np.diag(c/(K+c))-np.outer(slope,c/(K+c))/denominator


def microscopic_stationary(capacities,total,ratios):
    """Exact finite-pool CTMC weights; counts are an explicit toy assumption."""
    import itertools
    from scipy.special import gammaln, logsumexp
    cap=np.asarray(capacities)
    if cap.dtype.kind not in 'iu' or np.any(cap<1) or type(total) is not int or total<0:
        raise ValueError('positive integer capacities and nonnegative integer total required')
    r=vec(ratios,'on/off',len(cap),True)
    states=np.array([s for s in itertools.product(*(range(int(c)+1) for c in cap)) if sum(s)<=total],dtype=int)
    logs=np.sum(gammaln(cap+1)-gammaln(states+1)-gammaln(cap-states+1)+states*np.log(r),axis=1)-gammaln(total-states.sum(axis=1)+1)
    prob=np.exp(logs-logsumexp(logs));mean=prob@states
    centered=states-mean;cov=(centered*prob[:,None]).T@centered
    return states,prob,mean,cov
