import importlib.util
from pathlib import Path

import numpy as np
from scipy.optimize import minimize
from scipy.special import expit

HERE=Path(__file__).resolve().parents[1]/"verify/Q-NPF-04/fixed_points_metric"


def module(name):
    spec=importlib.util.spec_from_file_location(name,HERE/(name+".py"));result=importlib.util.module_from_spec(spec);spec.loader.exec_module(result);return result


BASE=module("microns_node_metric")
SOLVER=module("microns_schur_solver")


def example():
    rng=np.random.default_rng(240906);features=rng.normal(size=(300,3))**2;context=rng.integers(0,9,300)
    probability=expit(-.8+np.linspace(-.9,.9,9)[context]-features@np.array([.3,-.15,.5]))
    return BASE.Problem(context,rng.binomial(1,probability)),features


def test_schur_direction_matches_full_hessian():
    problem,features=example();rng=np.random.default_rng(4);p=rng.normal(scale=.1,size=1+problem.k+3)
    direction,gradient=SOLVER.newton_direction(problem,p,features,True)
    design=np.column_stack([np.ones(problem.n),np.eye(problem.k)[problem.group],-features])
    z=design@p;w=expit(z)*expit(-z);penalty=np.diag(np.r_[0,np.ones(problem.k),np.zeros(3)])
    hessian=design.T@(w[:,None]*design)+penalty
    np.testing.assert_allclose(direction,np.linalg.solve(hessian,-gradient),rtol=2e-10,atol=2e-10)


def test_bounded_step_matches_direct_convex_solution():
    h=np.array([[4.,1.,.3],[1.,3.,.7],[.3,.7,2.]])
    gradient=np.array([2.,-1.,4.]);beta=np.array([.1,.4,0.])
    step=SOLVER.bounded_quadratic_step(h,gradient,beta,False)
    direct=minimize(lambda d:(gradient@d+.5*d@h@d,gradient+h@d),np.zeros(3),jac=True,method="L-BFGS-B",bounds=[(-b,None) for b in beta],options={"ftol":1e-15,"gtol":1e-12})
    np.testing.assert_allclose(step,direct.x,atol=2e-7)
    assert np.all(beta+step>=0)


def test_fit_matches_original_objective_and_predictions():
    problem,features=example()
    for signed in [False,True]:
        fit,p=SOLVER.fit_newton(problem,features,signed)
        initial=np.zeros(len(p));direct=minimize(problem.objective,initial,args=(features,),jac=True,method="L-BFGS-B",bounds=[(None,None)]*(1+problem.k)+[(None,None) if signed else (0,None)]*3,options={"ftol":1e-15,"gtol":1e-11,"maxiter":2000})
        assert direct.success
        assert abs(fit["objective"]-direct.fun)<1e-11
        z=p[0]+p[1:1+problem.k][problem.group]-features@p[1+problem.k:]
        ref=direct.x[0]+direct.x[1:1+problem.k][problem.group]-features@direct.x[1+problem.k:]
        np.testing.assert_allclose(z,ref,atol=2e-5)
        assert fit["projected_gradient_max_unscaled"]<=1e-5
        if not signed:assert (p[1+problem.k:]==0).any()


def test_context_only_stationary_equations():
    problem,_=example();fit,p=SOLVER.fit_newton(problem,np.empty((problem.n,0)))
    r=expit(p[0]+p[1:][problem.group])-problem.y
    assert abs(r.sum())<1e-5
    np.testing.assert_allclose(np.bincount(problem.group,weights=r,minlength=problem.k)+p[1:],0,atol=1e-5)
    assert abs(p[1:].sum())<1e-5
