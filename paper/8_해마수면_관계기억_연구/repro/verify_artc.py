"""ARTC-1: finite-horizon replay order and capture, with reproducible controls.

Run: OPENBLAS_NUM_THREADS=1 python verify_artc.py
Pure NumPy/SciPy, no network. Not a biological or full CE-BRAIN experiment.
"""
from __future__ import annotations
import hashlib
import itertools
import json
import math
import platform
from pathlib import Path
import numpy as np
import scipy
from scipy.integrate import quad, solve_ivp
from scipy.optimize import brentq, minimize, minimize_scalar

ROOT = Path(__file__).resolve().parent

def integral_exp(rate: np.ndarray, duration: float) -> np.ndarray:
    """Integral_0^duration exp(-rate*t) dt, including rate zero."""
    rate = np.asarray(rate, dtype=float)
    out = np.full_like(rate, duration)
    np.divide(-np.expm1(-rate * duration), rate, out=out,
              where=np.abs(rate) > 1e-12)
    return out

def resource(t: float, rise: float, decay: float) -> float:
    if t < 0:
        return 0.0
    if abs(rise - decay) < 1e-10:
        return rise * t * math.exp(-rise * t)
    return rise / (rise-decay) * (math.exp(-decay*t)-math.exp(-rise*t))

def lag_optimum(tag_decay: float, rise: float, decay: float) -> float:
    """Exact infinite-readout overlap optimum, one tag impulse at lag >= 0."""
    if not all(math.isfinite(x) and x > 0 for x in (tag_decay,rise,decay)):
        raise ValueError('positive finite rates required')
    if abs(rise-decay) < 1e-10:
        return tag_decay/(decay*(tag_decay+decay))
    return math.log(rise*(tag_decay+decay)/(decay*(tag_decay+rise)))/(rise-decay)

def terminal_kernel(C: np.ndarray, lag: float, cfg: dict) -> np.ndarray:
    """Exact trace-to-slow response; L=I; positive separated resource rates."""
    C = np.asarray(C, dtype=float)
    h, k, b, ds = (cfg[x] for x in ('horizon','resource_rise','resource_decay','slow_decay'))
    if C.ndim != 2 or C.shape[0] != C.shape[1] or not np.isfinite(C).all():
        raise ValueError('finite square C required')
    if not np.allclose(C,C.T) or not 0 <= lag <= h or k <= b:
        raise ValueError('symmetric C, valid lag and rise > decay required')
    lam,U = np.linalg.eigh(C)
    if min(lam) <= 0 or ds >= min(lam)+b:
        raise ValueError('positive decay spectrum required for this fixture')
    duration=h-lag
    coeff=k/(k-b)*math.exp(-ds*duration)*(
        math.exp(-b*lag)*integral_exp(lam+b-ds,duration)
        - math.exp(-k*lag)*integral_exp(lam+k-ds,duration))
    return (U*coeff)@U.T

def solve_nonnegative_budget(Q: np.ndarray, linear: np.ndarray, budget: float):
    """Global convex QCQP by support enumeration (small n only).

    Minimize .5*a.T@Q@a + linear.T@a, a>=0, ||a||^2<=budget.
    A positive write penalty makes Q SPD. Each support solves its secular root.
    """
    Q=np.asarray(Q,dtype=float); linear=np.asarray(linear,dtype=float)
    n=len(linear)
    if Q.shape!=(n,n) or not np.isfinite(Q).all() or not np.isfinite(linear).all():
        raise ValueError('invalid quadratic')
    if not np.allclose(Q,Q.T) or np.linalg.eigvalsh(Q).min()<=0:
        raise ValueError('SPD Q required')
    if not math.isfinite(budget) or budget <= 0 or n>8:
        raise ValueError('positive budget and at most 8 variables required')
    best=np.zeros(n); best_value=0.0; best_mu=0.0
    for size in range(1,n+1):
        for subset in itertools.combinations(range(n),size):
            idx=np.array(subset); mat=Q[np.ix_(idx,idx)]
            vals,U=np.linalg.eigh(mat); rhs=U.T@(-linear[idx])
            def solution(mu): return U@(rhs/(vals+2*mu))
            a=solution(0.0); mu=0.0
            if a@a > budget:
                hi=1.0
                while solution(hi)@solution(hi)>budget: hi*=2
                mu=brentq(lambda m: float(solution(m)@solution(m)-budget),
                          0,hi,xtol=1e-13,rtol=1e-13)
                a=solution(mu)
            if np.any(a < -1e-10): continue
            full=np.zeros(n);full[idx]=np.maximum(a,0.0)
            value=float(.5*full@Q@full+linear@full)
            if value<best_value:
                best,best_value,best_mu=full,value,mu
    grad=Q@best+linear+2*best_mu*best
    active=best>1e-9
    residual=max(float(np.max(np.abs(grad[active]),initial=0)),
                 float(np.max(np.maximum(-grad[~active],0),initial=0)),
                 abs(best_mu*(float(best@best)-budget)),
                 max(0.0,float(best@best)-budget))
    return best,best_value,residual

def best_order(kernels: list, directions: np.ndarray, H: np.ndarray,
               grad: np.ndarray, cfg: dict, orders=None):
    n=len(directions)
    orders=itertools.permutations(range(n)) if orders is None else orders
    best=None; worst_kkt=0.0
    for order in orders:
        V=np.column_stack([kernels[t]@directions[e] for t,e in enumerate(order)])
        Q=V.T@H@V+cfg['write_penalty']*np.eye(n)
        alpha,value,kkt=solve_nonnegative_budget(Q,V.T@grad,cfg['write_budget'])
        worst_kkt=max(worst_kkt,kkt)
        if best is None or value<best['value']:
            best={'order':tuple(order),'alpha':alpha,'value':value,'delta':V@alpha}
    best['max_kkt']=worst_kkt
    return best

def greedy(kernels,directions,H,grad,cfg):
    delta=np.zeros(len(grad));remaining=list(range(len(directions)))
    energy=cfg['write_budget']; order=[];alpha=[]
    for K in kernels:
        candidates=[]
        for e in remaining:
            v=K@directions[e]
            q=float(v@H@v+cfg['write_penalty']);l=float(v@(grad+H@delta))
            a=float(np.clip(-l/q,0,math.sqrt(max(energy,0))))
            candidates.append((a*l+.5*a*a*q,e,a,v))
        _,e,a,v=min(candidates,key=lambda z:(z[0],z[1]))
        delta+=a*v;energy=max(0.0,energy-a*a)
        remaining.remove(e);order.append(e);alpha.append(a)
    return {'order':tuple(order),'alpha':np.array(alpha),'delta':delta,'max_kkt':0.0}

def ode_terminal(C, directions, order, amplitudes, slots, cfg):
    """Independent adaptive integration, with impulses split at event times."""
    dim=C.shape[0];z=np.zeros(2*dim); now=0.0
    def rhs(t,v):
        return np.r_[-C@v[:dim],resource(t,cfg['resource_rise'],cfg['resource_decay'])*v[:dim]-cfg['slow_decay']*v[dim:]]
    for t,e,a in zip(slots,order,amplitudes):
        if t>now:
            sol=solve_ivp(rhs,(now,t),z,method='DOP853',rtol=2e-11,atol=2e-13)
            if not sol.success:raise RuntimeError(sol.message)
            z=sol.y[:,-1]
        z[:dim]+=a*directions[e];now=t
    sol=solve_ivp(rhs,(now,cfg['horizon']),z,method='DOP853',rtol=2e-11,atol=2e-13)
    if not sol.success:raise RuntimeError(sol.message)
    return sol.y[:,-1][dim:]

def diagnostics(cfg):
    rng=np.random.default_rng(87131); lag_errors=[];kernel_errors=[];optimizer_errors=[];kkts=[]
    for _ in range(32):
        a=float(rng.uniform(.2,3));b=float(rng.uniform(.1,1));k=b+float(rng.uniform(.3,3))
        exact=lag_optimum(a,k,b)
        def overlap(r):
            return quad(lambda u:math.exp(-a*u)*resource(r+u,k,b),0,np.inf,
                        epsabs=1e-11,epsrel=1e-11)[0]
        opt=minimize_scalar(lambda r:-overlap(r),bounds=(0,12/min(a,b)),method='bounded',options={'xatol':1e-11})
        lag_errors.append(abs(exact-opt.x))
        z=rng.normal(size=(4,4));C=.2*np.eye(4)+z.T@z/4
        directions=rng.normal(size=(4,4));directions/=np.linalg.norm(directions,axis=1)[:,None]
        order=tuple(rng.permutation(4));amps=rng.uniform(0,1,4)
        kernels=[terminal_kernel(C,t,cfg) for t in cfg['slots']]
        pred=sum((amps[i]*kernels[i]@directions[e] for i,e in enumerate(order)),np.zeros(4))
        actual=ode_terminal(C,directions,order,amps,cfg['slots'],cfg)
        kernel_errors.append(float(np.max(np.abs(actual-pred))))
        Z=rng.normal(size=(4,4));Q=Z.T@Z+.1*np.eye(4);l=rng.normal(size=4);budget=float(rng.uniform(.2,2))
        aa,v,kkt=solve_nonnegative_budget(Q,l,budget);kkts.append(kkt)
        ref=minimize(lambda x:.5*x@Q@x+l@x,np.zeros(4),jac=lambda x:Q@x+l,
                     bounds=[(0,None)]*4,constraints=[{'type':'ineq','fun':lambda x:budget-x@x,'jac':lambda x:-2*x}],
                     method='SLSQP',options={'ftol':1e-12,'maxiter':400})
        if not ref.success:raise RuntimeError(ref.message)
        optimizer_errors.append(abs(v-ref.fun))
    a,k,b=1.0,2.0,.25;r=lag_optimum(a,k,b)
    def gain(t):return k/(k-b)*(math.exp(-b*t)/(a+b)-math.exp(-k*t)/(a+k))
    # Same past observations but different order: no new independent evidence.
    x=np.array([1.,2.]);scale=.3
    order_gap=np.r_[-scale*x,scale*x]
    # An infinitely fast neighborhood has the Schur/quasistatic limit; a finite one has memory.
    C=np.diag([.3,1.7]);D=np.array([[1.,.2],[.1,1.]])
    schur_errors={str(t):float(np.linalg.norm(D@np.linalg.solve(C,np.eye(2)-np.diag(np.exp(-np.diag(C)*t))) - D@np.linalg.inv(C))) for t in (1.,10.,100.)}
    assert max(kernel_errors)<1e-8 and max(optimizer_errors)<1e-8 and max(kkts)<1e-7
    assert max(lag_errors)<2e-5
    return {'lag_cases':32,'lag_max_time_error':max(lag_errors),
            'lag_example':{'optimal_replay_delay':r,'overlap_at_zero':gain(0),'overlap_at_optimum':gain(r),
                           'resource_peak_time':math.log(k/b)/(k-b),'time_units':'dimensionless'},
            'kernel_ode_cases':32,'kernel_ode_max_abs_error':max(kernel_errors),
            'optimizer_cases':32,'optimizer_objective_max_error':max(optimizer_errors),'max_kkt_residual':max(kkts),
            'quasistatic_kernel_limit_errors':schur_errors,'write_capture_commutator':order_gap.tolist()}

def trial(seed,cfg):
    rng=np.random.default_rng(seed);dim=cfg['dimension']
    X=rng.normal(size=(cfg['observations'],dim))/math.sqrt(dim)
    wtrue=rng.normal(size=dim);y=X@wtrue+cfg['observation_noise']*rng.normal(size=len(X))
    init=np.zeros(dim); base=math.exp(-cfg['slow_decay']*cfg['horizon'])*init
    H=X.T@X/len(X)+cfg['ridge']*np.eye(dim);bb=X.T@y/len(X);grad=H@base-bb
    events=rng.choice(len(X),cfg['events'],replace=False)
    directions=np.sign(y[events])[:,None]*X[events]
    directions/=np.linalg.norm(directions,axis=1)[:,None]
    graph=rng.uniform(0,.25,size=(dim,dim));graph=(graph+graph.T)/2;np.fill_diagonal(graph,0)
    C=np.diag(rng.uniform(.15,1.5,size=dim))+np.diag(graph.sum(axis=1))-graph
    kernels=[terminal_kernel(C,t,cfg) for t in cfg['slots']]
    joint=best_order(kernels,directions,H,grad,cfg)
    random_order=tuple(rng.permutation(len(events)))
    randomized=best_order(kernels,directions,H,grad,cfg,[random_order])
    greedy_plan=greedy(kernels,directions,H,grad,cfg)
    static=[math.exp(-cfg['slow_decay']*(cfg['horizon']-t))*resource(t,cfg['resource_rise'],cfg['resource_decay'])*np.linalg.inv(C) for t in cfg['slots']]
    static_plan=best_order(static,directions,H,grad,cfg)
    direct=[math.exp(-cfg['slow_decay']*(cfg['horizon']-t))*np.eye(dim) for t in cfg['slots']]
    direct_plan=best_order(direct,directions,H,grad,cfg)
    plans=dict(zip(cfg['methods'],[joint,randomized,greedy_plan,static_plan,direct_plan]))
    # Test samples and their targets are generated only after all choices are fixed.
    XT=rng.normal(size=(cfg['test_rows'],dim))/math.sqrt(dim);yt=XT@wtrue
    result={};frozen=[]
    for name,p in plans.items():
        Ks=direct if name=='direct_slow' else kernels
        delta=sum((p['alpha'][i]*Ks[i]@directions[e] for i,e in enumerate(p['order'])),np.zeros(dim))
        w=base+delta;pred=XT@w;energy=float(p['alpha']@p['alpha'])
        objective=float(.5*np.mean((X@w-y)**2)+.5*cfg['ridge']*(w@w)+.5*cfg['write_penalty']*energy)
        assert energy<=cfg['write_budget']+1e-9
        result[name]={'objective':objective,'test_mse':float(np.mean((pred-yt)**2)),
                      'write_energy':energy,'order':[int(i) for i in p['order']],'amplitudes':p['alpha'].tolist(),
                      'max_kkt':p['max_kkt'],'slow_weight':w.tolist()}
        frozen.append(w)
    assert result['joint_kernel']['objective']<=result['random_order_joint_amplitudes']['objective']+1e-8
    assert result['joint_kernel']['objective']<=result['sequential_greedy']['objective']+1e-8
    assert result['joint_kernel']['objective']<=result['static_schur']['objective']+1e-8
    p=joint;predicted=p['delta'];actual=ode_terminal(C,directions,p['order'],p['alpha'],cfg['slots'],cfg)
    matched_alpha=np.full(cfg['events'],math.sqrt(cfg['write_budget']/cfg['events']))
    losses=[]
    for order in itertools.permutations(range(cfg['events'])):
        w=sum((matched_alpha[i]*kernels[i]@directions[e] for i,e in enumerate(order)),np.zeros(dim))
        losses.append(float(.5*np.mean((X@w-y)**2)+.5*cfg['ridge']*(w@w)))
    return {'seed':seed,'results':result,'exact_vs_ode':float(np.max(np.abs(actual-predicted))),
            'same_energy_order_loss_range':[min(losses),max(losses)],
            'unique_observations':len(X),'candidate_observed_indices':events.tolist(),
            'mode_label_changes_equations':False}

def main():
    cfg=json.loads((ROOT/'protocol.json').read_text());diag=diagnostics(cfg)
    rows=[trial(seed,cfg) for seed in cfg['seeds']]
    summary={}
    for name in cfg['methods']:
        summary[name]={k:float(np.mean([r['results'][name][k] for r in rows])) for k in ('objective','test_mse','write_energy')}
    rg=np.random.default_rng(90811);indices=rg.integers(0,len(rows),size=(5000,len(rows)));paired={}
    for name in cfg['methods'][1:]:
        paired[name]={}
        for metric in ('objective','test_mse'):
            diff=np.array([r['results']['joint_kernel'][metric]-r['results'][name][metric] for r in rows])
            paired[name][metric]={'mean_difference':float(diff.mean()),'seed_bootstrap_95':np.quantile(diff[indices].mean(axis=1),[.025,.975]).tolist(),
                                  'joint_better_seeds':int((diff<-1e-10).sum()),'joint_worse_seeds':int((diff>1e-10).sum())}
    result={'scope':'Known-model finite-dimensional mathematical and synthetic checks, not neural/hormone/CE-BRAIN validation.',
            'environment':{'python':platform.python_version(),'numpy':np.__version__,'scipy':scipy.__version__},
            'protocol_sha256':hashlib.sha256((ROOT/'protocol.json').read_bytes()).hexdigest(),
            'source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            'diagnostics':diag,'summary':summary,'paired_joint_minus_control':paired,
            'maximum_terminal_ode_error':max(r['exact_vs_ode'] for r in rows),
            'rows':rows}
    (ROOT/'results.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    print(json.dumps({k:result[k] for k in ('diagnostics','summary','paired_joint_minus_control','maximum_terminal_ode_error')},indent=2))

if __name__=='__main__':main()
