"""Exact Hessian Newton steps for the unchanged categorical logistic objective.

The intercept and ridge-penalized context offsets are eliminated from each
quadratic Newton subproblem. At most three bounded geometry coordinates remain.
No data compression, label weighting, or extra regularization is introduced.
"""
import itertools

import numpy as np
from scipy.special import expit


def bounded_quadratic_step(hessian,gradient,beta,signed):
    """Solve the small convex quadratic subproblem over beta + step >= 0."""
    dimension=len(beta)
    if not dimension:return np.empty(0)
    candidates=[]
    for flags in ([tuple(False for _ in beta)] if signed else itertools.product([False,True],repeat=dimension)):
        active=np.array(flags,dtype=bool);free=~active;step=np.zeros(dimension);step[active]=-beta[active]
        if free.any():
            step[free]=np.linalg.solve(hessian[np.ix_(free,free)],-gradient[free]-hessian[np.ix_(free,active)]@step[active])
        if not signed and np.any(beta[free]+step[free]<0):continue
        candidates.append((float(gradient@step+.5*step@hessian@step),step))
    if not candidates:raise RuntimeError("No feasible Newton face")
    return min(candidates,key=lambda item:item[0])[1]


def newton_direction(problem,parameters,features,signed):
    k=problem.k;u=parameters[1:1+k];beta=parameters[1+k:]
    z=parameters[0]+u[problem.group]-features@beta
    probability=expit(z);r=probability-problem.y
    # Product form avoids expit(z) rounding to 1 in positive tails.
    w=expit(z)*expit(-z)
    rc=np.bincount(problem.group,weights=r,minlength=k)
    wc=np.bincount(problem.group,weights=w,minlength=k);den=1+wc
    gu=rc+u;ga=float(rc.sum());gb=-features.T@r
    t=np.column_stack([np.bincount(problem.group,weights=w*features[:,i],minlength=k) for i in range(features.shape[1])]) if features.shape[1] else np.empty((k,0))
    aa=float(np.sum(wc/den))
    if aa<=0:raise RuntimeError("Unidentifiable intercept curvature")
    # Eliminate context offsets, then the intercept. Stable identities are used
    # for terms whose naive formulas subtract two large nearly equal sums.
    ab=-np.sum(t/den[:,None],axis=0)
    bb=features.T@(w[:,None]*features)-t.T@(t/den[:,None])
    ga_reduced=float(np.sum(rc/den-u*wc/den))
    gb_reduced=gb+t.T@(gu/den)
    hessian=bb-np.outer(ab,ab)/aa
    gradient=gb_reduced-ab*ga_reduced/aa
    db=bounded_quadratic_step(hessian,gradient,beta,signed)
    da=(-ga_reduced-ab@db)/aa
    du=(-gu-wc*da+t@db)/den
    return np.r_[da,du,db],np.r_[ga,gu,gb]


def fit_newton(problem,features,signed=False,initial=None):
    if initial is None:
        initial=np.zeros(1+problem.k+features.shape[1]);mean=float(problem.y.mean())
        if not 0<mean<1:raise ValueError("Both labels are required")
        initial[0]=np.log(mean/(1-mean))
    parameters=np.array(initial,dtype=float,copy=True)
    line_search_evaluations=0
    for iteration in range(100):
        loss,scaled_gradient=problem.objective(parameters,features)
        gradient=scaled_gradient*problem.n;projected=gradient.copy()
        if not signed:
            boundary=parameters[1+problem.k:]==0
            projected[1+problem.k:][boundary]=np.minimum(projected[1+problem.k:][boundary],0)
        residual=float(np.max(abs(projected)))
        if residual<=1e-5:break
        direction,check_gradient=newton_direction(problem,parameters,features,signed)
        if not np.allclose(check_gradient,gradient,atol=1e-7,rtol=1e-10):raise RuntimeError("Gradient mismatch")
        slope=float(scaled_gradient@direction)
        if slope>=0:raise RuntimeError("Newton step is not a descent direction")
        for backtrack in range(45):
            alpha=2.**(-backtrack);candidate=parameters+alpha*direction
            if not signed:candidate[1+problem.k:]=np.maximum(candidate[1+problem.k:],0)
            new_loss,_=problem.objective(candidate,features);line_search_evaluations+=1
            if new_loss<=loss+1e-4*alpha*slope+2e-15:
                parameters=candidate;break
        else:raise RuntimeError("Newton line search failed")
    else:raise RuntimeError("Newton iteration limit reached")
    fitted=dict(intercept=float(parameters[0]),context_offsets={str(c):float(v) for c,v in zip(problem.categories,parameters[1:1+problem.k])},
        coefficients=parameters[1+problem.k:].tolist(),objective=float(loss),iterations=iteration,
        gradient_max=float(np.max(abs(scaled_gradient))),projected_gradient_max_unscaled=residual,
        line_search_evaluations=line_search_evaluations,optimizer_message="Exact Hessian Schur Newton; bound-constrained quadratic step; projected gradient <= 1e-5 before division by N")
    return fitted,parameters
