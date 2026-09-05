import importlib.util
from pathlib import Path
import sys

import numpy as np
from scipy.special import expit

HERE=Path(__file__).resolve().parents[1]/"verify/Q-NPF-04/fixed_points_metric"
sys.path.insert(0,str(HERE))
spec=importlib.util.spec_from_file_location("radial_direction",HERE/"microns_radial_direction_observation.py")
analysis=importlib.util.module_from_spec(spec);spec.loader.exec_module(analysis)


def toy():
    rng=np.random.default_rng(3906);n=700
    squared=rng.normal(size=(n,3))**2;strata=np.arange(n)%4;context=strata*2+rng.integers(0,2,n)
    distance,_,_=analysis.radial([.6,-.4],squared)
    y=rng.binomial(1,expit(.3+np.linspace(-.7,.7,8)[context]-distance*np.array([.4,.8,1.2,.7])[strata]))
    problem=analysis.base.Problem(context,y)
    p=np.zeros(1+problem.k+4);p[0]=np.log(y.mean()/(1-y.mean()));p[-4:]=.5
    return context,y,squared,strata,p


def test_radial_derivative_and_zero_displacement():
    squared=np.array([[0.,0.,0.],[1.,4.,9.],[3.,0.,2.]])
    theta=np.array([.8,-.5]);distance,gradient,w=analysis.radial(theta,squared)
    assert distance[0]==0 and np.array_equal(gradient[0],[0,0])
    for k in range(2):
        direction=np.eye(2)[k]*1e-6
        numeric=(analysis.radial(theta+direction,squared)[0]-analysis.radial(theta-direction,squared)[0])/(2e-6)
        np.testing.assert_allclose(gradient[:,k],numeric,rtol=2e-8,atol=2e-9)
    np.testing.assert_allclose(distance**2,squared@w)


def test_stratum_design_contains_common_gain():
    context,y,squared,strata,p=toy();d,_,_=analysis.radial([.2,-.3],squared)
    np.testing.assert_allclose(analysis.features(d,strata,True)@np.repeat(.7,4),d*.7)
    problem=analysis.base.Problem(context,y)
    common=np.r_[p[:-4],.7];split=np.r_[p[:-4],np.repeat(.7,4)]
    assert abs(problem.objective(common,d[:,None])[0]-problem.objective(split,analysis.features(d,strata,True))[0])<1e-14


def test_profile_envelope_gradient():
    context,y,squared,strata,p=toy();profile=analysis.Profile(context,y,squared,strata,True,p)
    theta=np.array([.25,-.3]);_,gradient,_=profile.evaluate(theta)
    for k in range(2):
        change=np.eye(2)[k]*2e-4
        plus=profile.evaluate(theta+change)[0]["objective"];minus=profile.evaluate(theta-change)[0]["objective"]
        np.testing.assert_allclose(gradient[k],(plus-minus)/(4e-4),rtol=3e-4,atol=5e-7)


def test_bounded_search_retains_isotropic_candidate():
    context,y,squared,strata,p=toy();profile=analysis.Profile(context,y,squared,strata,True,p)
    isotropic=profile.evaluate([0.,0.])[0]["objective"]
    selected,_=profile.search()
    assert selected["fit"]["objective"]<=isotropic+1e-12
    assert np.all(abs(np.array(selected["theta"]))<=analysis.LOG_BOUND)
    assert selected["shape_projected_gradient_max"]<=5e-7
    assert all(r["inner_projected_gradient_max_unscaled"]<=1e-5 for r in selected["evaluations"])


def test_box_kkt_and_zero_gain_interpretation():
    bound=analysis.LOG_BOUND
    np.testing.assert_equal(analysis.projected_shape_gradient([-bound,bound],[2.,-3.]),[0,0])
    np.testing.assert_equal(analysis.projected_shape_gradient([-bound,bound],[-2.,3.]),[-2,3])
    cost=analysis.describe_cost([0.,0.],[0.],False)
    assert cost["common_effective_metric_per_um2"] is None
    assert cost["zero_attenuation_components"]==1
    signed=analysis.describe_cost([0.,0.],[-.2,.1,.2,.3],True,True)
    assert signed["negative_attenuation_components"]==1
