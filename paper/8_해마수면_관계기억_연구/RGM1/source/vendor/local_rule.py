"""Local BTSP-inspired candidate. No task labels, replay search or global loss input.

Empirical motifs motivate the state split; polynomial rate functions and all
parameters are explicitly model choices. Physical units are seconds for trace
decay. Execution dose is an uncalibrated effective duration, not a drug dose.
"""
from __future__ import annotations
from dataclasses import dataclass
import math
import numpy as np


def scalar(x, name, positive=False):
    if isinstance(x,(bool,np.bool_)) or not isinstance(x,(int,float,np.integer,np.floating)):
        raise TypeError(f'{name}: numeric, non-boolean value required')
    y=float(x)
    if not math.isfinite(y) or y<0 or (positive and y<=0):
        raise ValueError(f'{name}: finite {"positive" if positive else "nonnegative"} value required')
    return y

@dataclass(frozen=True)
class Parameters:
    tau_e_s: float=2.5
    tau_i_s: float=1.5
    tau_tag_s: float=60.
    tag_gain_per_s: float=1.
    tag_half: float=.2
    pot_rate: float=.8
    dep_rate: float=.15
    maximum: float=1.
    def __post_init__(self):
        for k,v in vars(self).items(): scalar(v,k,positive=k in ('tau_e_s','tau_i_s','tau_tag_s','tag_half','maximum'))


def tag_flow(e,i,tag,dt,p):
    """Exact between-event solution of E'=-E/tE, I'=-I/tI,
    T'=gain*E*I-T/tT. No saturation approximations to this stated ODE.
    """
    dt=scalar(dt,'dt')
    e,i,tag=np.broadcast_arrays(np.asarray(e,float),np.asarray(i,float),np.asarray(tag,float))
    if any(not np.isfinite(a).all() or np.any(a<0) for a in (e,i,tag)):
        raise ValueError('finite nonnegative trace arrays required')
    r=1/p.tau_e_s+1/p.tau_i_s;d=1/p.tau_tag_s
    if abs(r-d)<1e-12:
        bridge=dt*math.exp(-d*dt)
    else:
        # Difference of two bounded exponentials avoids overflow for either rate order.
        gap=abs(r-d)
        bridge=math.exp(-min(r,d)*dt)*(-math.expm1(-gap*dt))/gap
    return (e*math.exp(-dt/p.tau_e_s), i*math.exp(-dt/p.tau_i_s),
            tag*math.exp(-d*dt)+p.tag_gain_per_s*e*i*bridge)


def rates(tag,p):
    tag=np.asarray(tag,float)
    if not np.isfinite(tag).all() or np.any(tag<0): raise ValueError('invalid tags')
    u=tag/(p.tag_half+tag)
    # Nonproportional channels: equilibrium depends on tag strength.
    return p.pot_rate*u*u,p.dep_rate*u


def event_map(tag,dose,p):
    """Per-synapse affine map w+ = A*w + B for a shared execution pulse."""
    dose=scalar(dose,'dose');a,b=rates(tag,p);total=a+b
    fraction=-np.expm1(-dose*total)
    equilibrium=np.divide(p.maximum*a,total,out=np.zeros_like(a),where=total>0)
    return 1-fraction,equilibrium*fraction


def execute(weights,tag,dose,p):
    w=np.asarray(weights,float)
    if not np.isfinite(w).all() or np.any(w<0) or np.any(w>p.maximum):
        raise ValueError('expressed weights outside allowed range')
    A,B=event_map(tag,dose,p);out=A*w+B
    if not np.isfinite(out).all() or np.any(out<-1e-13) or np.any(out>p.maximum+1e-13):
        raise ArithmeticError('event left invariant range')
    return out


class LocalPlasticity:
    """Directed synapse list with fixed IDs/signs and branch-local event delivery.

    The reader of this class may compute a network output from expressed weights.
    The updater never receives desired output, future loss, hidden model label,
    gradient through the network, or a full synapse matrix.
    """
    def __init__(self,edge_ids,branches,weights,signs,parameters=None):
        self.p=parameters or Parameters()
        self.edge_ids=tuple(edge_ids)
        raw_branches=np.asarray(branches);raw_signs=np.asarray(signs)
        if raw_branches.dtype.kind not in 'iu' or raw_signs.dtype.kind not in 'iu':
            raise TypeError('integer branch IDs and signs required')
        self.branches=np.array(raw_branches,dtype=int,copy=True)
        self.signs=np.array(raw_signs,dtype=int,copy=True)
        self.weights=np.array(weights,dtype=float,copy=True)
        n=len(self.edge_ids)
        if any(not isinstance(x,str) or not x for x in self.edge_ids) or len(set(self.edge_ids))!=n or any(a.shape!=(n,) for a in (self.branches,self.signs,self.weights)):
            raise ValueError('unique IDs and aligned arrays required')
        if np.any(self.branches<0) or np.any(~np.isin(self.signs,[-1,1])):
            raise ValueError('branch IDs/signs invalid')
        execute(self.weights,np.zeros(n),0.,self.p)
        self.branches.setflags(write=False);self.signs.setflags(write=False)
        self.eligibility=np.zeros(n);self.instruction=np.zeros(n);self.tag=np.zeros(n);self.time=0.
    def advance_to(self,time):
        time=scalar(time,'time')
        if time<self.time:raise ValueError('events must be processed chronologically')
        e,i,t=tag_flow(self.eligibility,self.instruction,self.tag,time-self.time,self.p)
        self.eligibility,self.instruction,self.tag=e,i,t;self.time=time
    def presynaptic(self,edge,magnitude=1.):
        if type(edge) is not int or not 0<=edge<len(self.weights): raise ValueError('edge index required')
        magnitude=scalar(magnitude,'magnitude')
        self.eligibility[edge]+=magnitude
    def instruct(self,branch,magnitude=1.):
        if type(branch) is not int:raise ValueError('integer branch required')
        magnitude=scalar(magnitude,'magnitude')
        self.instruction[self.branches==branch]+=magnitude
    def burst(self,branch,dose=1.):
        if type(branch) is not int:raise ValueError('integer branch required')
        idx=self.branches==branch
        new=execute(self.weights[idx],self.tag[idx],dose,self.p)
        self.weights[idx]=new
    def expressed(self):return self.signs*self.weights


def count_moments(weights,tags,groups,mean_count,dose,p,noise_sd=0.):
    """Exact first and second moments, frozen tags, one Poisson count per group."""
    nu=scalar(mean_count,'mean_count');sigma=scalar(noise_sd,'noise_sd');dose=scalar(dose,'dose')
    w=np.asarray(weights,float);tags=np.asarray(tags,float);groups=np.asarray(groups)
    if w.ndim!=1 or tags.shape!=w.shape or groups.shape!=w.shape:
        raise ValueError('aligned one-dimensional weights, tags and groups required')
    execute(w,tags,0.,p)
    a,b=rates(tags,p);k=dose*(a+b)
    target=np.divide(p.maximum*a,a+b,out=np.array(w,copy=True),where=a+b>0)
    delta=w-target
    lap=np.exp(nu*np.expm1(-k))
    mean=target+delta*lap
    lap2=np.exp(nu*np.expm1(-(k[:,None]+k[None,:])))
    cov=np.outer(delta,delta)*(lap2-np.outer(lap,lap))
    cov*=groups[:,None]==groups[None,:]
    cov+=sigma*sigma*np.eye(len(w))
    naive=target+delta*np.exp(-nu*k)
    return mean,cov,naive


def moment_rhs(time,state,tag_at,groups,intensity,dose,p):
    """Exact moment ODE for state-independent Poisson jumps and deterministic tags.

    Covariance closure is exact because each weight's jump is affine. It is not
    valid unchanged for intensity driven by the random weights/network state.
    """
    groups=np.asarray(groups);n=len(groups);mu=state[:n];cov=state[n:].reshape(n,n)
    nu=float(intensity(time));A,B=event_map(tag_at(time),dose,p)
    if nu<0:raise ValueError('negative jump intensity')
    d=(A-1)*mu+B
    common=groups[:,None]==groups[None,:]
    cc=(A[:,None]*A[None,:]-1)*cov+np.outer(d,d)
    ii=((A-1)[:,None]+(A-1)[None,:])*cov
    return np.r_[nu*d,(nu*np.where(common,cc,ii)).ravel()]
