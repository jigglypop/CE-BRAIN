"""Independent scalar recomputation and boundary checks for ARTC-1.
Run after verify_artc.py. All arrays here come from stored results or fixed seeds.
"""
import json
import math
from pathlib import Path
import numpy as np
from scipy.integrate import quad
from scipy.optimize import minimize_scalar
from verify_artc import lag_optimum, resource, terminal_kernel, solve_nonnegative_budget

ROOT=Path(__file__).resolve().parent
cfg=json.loads((ROOT/'protocol.json').read_text())
result=json.loads((ROOT/'results.json').read_text())
errors=[];checks={}
for row in result['rows']:
    rng=np.random.default_rng(row['seed']);dim=cfg['dimension']
    X=rng.normal(size=(cfg['observations'],dim))/math.sqrt(dim)
    truth=rng.normal(size=dim);y=X@truth+cfg['observation_noise']*rng.normal(size=len(X))
    rng.choice(len(X),cfg['events'],replace=False)
    rng.uniform(0,.25,size=(dim,dim));rng.uniform(.15,1.5,size=dim);rng.permutation(cfg['events'])
    XT=rng.normal(size=(cfg['test_rows'],dim))/math.sqrt(dim)
    for rec in row['results'].values():
        w=rec['slow_weight'];a=rec['amplitudes']
        energy=math.fsum(v*v for v in a)
        mse=math.fsum((math.fsum(float(z)*(wi-ti) for z,wi,ti in zip(x,w,truth)))**2 for x in XT)/len(XT)
        train=math.fsum((math.fsum(float(z)*wi for z,wi in zip(x,w))-float(target))**2 for x,target in zip(X,y))/len(X)
        objective=.5*train+.5*cfg['ridge']*math.fsum(v*v for v in w)+.5*cfg['write_penalty']*energy
        errors.extend([abs(mse-rec['test_mse']),abs(objective-rec['objective']),abs(energy-rec['write_energy'])])
checks['independent_scalar_metric_count']=len(errors)
checks['max_metric_error']=max(errors)
assert max(errors)<1e-10
# Equal rise/decay rates have a finite analytic limit, not a singular optimum.
a=1.0;b=.7
opt=minimize_scalar(lambda r:-quad(lambda u:math.exp(-a*u)*resource(r+u,b,b),0,np.inf)[0],
                    bounds=(0,10),method='bounded')
checks['equal_rate_optimum_time_error']=abs(opt.x-lag_optimum(a,b,b))
assert checks['equal_rate_optimum_time_error']<1e-5
# Increasing tag decay shifts the optimum towards, but never beyond, resource peak.
rates=np.geomspace(.01,100,64);lags=np.array([lag_optimum(v,2,.25) for v in rates])
checks['lag_monotonic_64']=bool(np.all(np.diff(lags)>0) and lags[0]>0 and lags[-1]<math.log(8)/1.75)
assert checks['lag_monotonic_64']
checks['zero_remaining_time_kernel_norm']=float(np.linalg.norm(terminal_kernel(np.eye(2),cfg['horizon'],cfg)))
assert checks['zero_remaining_time_kernel_norm']==0
rng=np.random.default_rng(9381);worst=0.0
for _ in range(32):
    Z=rng.normal(size=(4,4));Q=Z.T@Z+.1*np.eye(4);linear=rng.normal(size=4)
    values=[solve_nonnegative_budget(Q,linear,b)[1] for b in (.1,.5,1,3)]
    worst=max(worst,float(np.max(np.diff(values))))
checks['larger_budget_objective_max_increase']=worst
assert worst<1e-9
checks['rerun_results_byte_identical']=(ROOT/'results.json').read_bytes()==(ROOT/'results_first.json').read_bytes() if (ROOT/'results_first.json').exists() else None
checks['startup_corrections']='Two implementation fixes before successful result: missing slots argument and NumPy integer JSON serialization. No protocol parameters changed.'
(ROOT/'validation.json').write_text(json.dumps(checks,indent=2)+'\n')
print(json.dumps(checks,indent=2))
