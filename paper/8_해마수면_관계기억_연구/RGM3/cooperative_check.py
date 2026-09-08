"""Exploratory follow-on after fixed affinity failed to generate WTA.

Not a fitted biological mechanism. All compared examples have the same known
symmetric occupancy, with on-rate set explicitly to maintain that equilibrium.
"""
from pathlib import Path
import json
import numpy as np
from scipy.integrate import solve_ivp
from scipy.linalg import eigvals
ROOT=Path(__file__).resolve().parent


def rhs(y,on,off,chi):
    p=y[0];b=y[1:];R=on*p*np.exp(chi*b)*(1-b)-off*b
    return np.r_[-R.sum(),R]


def generalized_energy(y,on,off,chi):
    from scipy.special import xlogy
    p=y[:,0];b=y[:,1:]
    return xlogy(p,p)-p+np.sum(xlogy(b,b)+xlogy(1-b,1-b)-b*np.log(on/off)-chi*b*b/2,axis=1)


def main():
    trials=[];times=np.linspace(0,40,2001)
    for chi in (2.,6.):
        bstar=.5;pstar=.2;off=1.;on=np.exp(-chi*bstar)/pstar
        for perturb in (-1e-4,1e-4):
            init=np.array([pstar,bstar+perturb,bstar-perturb])
            sol=solve_ivp(lambda t,y:rhs(y,on,off,chi),(0,times[-1]),init,t_eval=times,method='DOP853',rtol=2e-11,atol=2e-13)
            alt=solve_ivp(lambda t,y:rhs(y,on,off,chi),(0,times[-1]),init,t_eval=times,method='Radau',rtol=2e-10,atol=2e-12)
            assert sol.success and alt.success
            y=sol.y.T;E=generalized_energy(y,on,off,chi)
            eigen_antisym=off*(chi*bstar-1/(1-bstar))
            eq=np.array([pstar,bstar,bstar]);v=np.array([0.,1.,-1.]);eps=1e-6
            numerical=(rhs(eq+eps*v,on,off,chi)-rhs(eq-eps*v,on,off,chi))/(2*eps)
            residual=np.max(np.abs(numerical-eigen_antisym*v))
            assert y[:,0].min()>0 and y[:,1:].min()>0 and y[:,1:].max()<1
            assert np.max(np.diff(E))<1e-9
            trials.append({'chi':chi,'on_rate':float(on),'off_rate':off,'initial':init.tolist(),
                'final':y[-1].tolist(),'antisymmetric_eigenvalue':float(eigen_antisym),
                'eigenvector_finite_difference_error':float(residual),
                'max_total_error':float(np.max(np.abs(y.sum(axis=1)-1.2))),
                'independent_ode_error':float(np.max(np.abs(sol.y-alt.y))),
                'entropy_max_increase':float(np.max(np.diff(E)))})
    out={'status':'exploratory hypothesis added after fixed-affinity no-WTA finding, not predeclared confirmatory test',
        'model':'R_i=k0*p*exp(chi*b_i)*(1-b_i)-d*b_i; identical unit capacities and closed resource total=1.2',
        'condition':'antisymmetric instability iff chi*b_star*(1-b_star)>1; chi>4 is necessary within THIS exponential-response family, not a universal biological number',
        'matched_equilibrium':'b1=b2=.5, p=.2, d=1; k0=exp(-chi/2)/.2 adjusted by formula, not held fixed or fitted to data',
        'trials':trials}
    (ROOT/'cooperative_results.json').write_text(json.dumps(out,indent=2)+'\n')
    print(json.dumps(out,indent=2))

if __name__=='__main__':main()
