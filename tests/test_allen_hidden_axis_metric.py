import importlib.util
from pathlib import Path
import sys

import numpy as np

HERE=Path(__file__).resolve().parents[1]/"verify/Q-NPF-04/fixed_points_metric"
sys.path.insert(0,str(HERE))
spec=importlib.util.spec_from_file_location("hidden_axis",HERE/"allen_hidden_axis_metric.py")
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)


def test_radial_isotropic_and_exact_semidefinite_boundaries():
    delta=np.array([[30.,40.,12.],[60.,-20.,0.]])
    f=m.squared_components(delta,2)
    np.testing.assert_allclose(np.sqrt(2)*m.radial_feature(f,.5)[:,0],np.linalg.norm(delta,axis=1)/100)
    np.testing.assert_allclose(m.radial_feature(f,1)[:,0],abs(delta[:,2])/100)
    assert m.radial_metric(1.,0.,2)["rank"]==2
    assert m.radial_metric(1.,1.,2)["rank"]==1
    assert not m.radial_metric(1.,0.,2)["SPD"]
    assert m.radial_metric(1.,.3,2)["SPD"]


def test_convex_inner_analytic_gradient():
    rng=np.random.default_rng(23)
    p=m.TrainingProblem(np.array(['a','b','c']*10),rng.integers(0,2,30))
    f=rng.uniform(.1,2,(30,2));x=rng.normal(size=1+p.k+2)
    _,gradient=p.objective(x,f)
    numeric=[]
    for i in range(len(x)):
        step=np.zeros(len(x));step[i]=1e-6
        numeric.append((p.objective(x+step,f)[0]-p.objective(x-step,f)[0])/2e-6)
    np.testing.assert_allclose(gradient,numeric,atol=1e-8)


def test_negative_hidden_cost_is_not_forced_into_spd():
    plane=np.tile([.5,1.,1.5,2.],30);hidden=np.repeat([0.,1.,2.],40)
    y=(hidden>0).astype(float)
    p=m.TrainingProblem(np.array(['same']*len(y)),y)
    f=np.column_stack([plane,hidden])
    constrained=p.pack(p.fit(f));signed=p.pack(p.fit(f,signed=True))
    assert constrained['coefficients'][1]<1e-8
    assert signed['coefficients'][1]<0


def test_cost_is_symmetric_and_rotates_with_the_declared_axis():
    delta=np.array([[30.,20.,10.],[-5.,8.,12.]])
    g=np.diag(m.radial_metric(1.2,.3,2)['diagonal_per_um2'])
    q=np.einsum('ni,ij,nj->n',delta,g,delta)
    np.testing.assert_allclose(q,(1.2*m.radial_feature(m.squared_components(delta,2),.3)[:,0])**2)
    np.testing.assert_allclose(m.squared_components(delta,2),m.squared_components(-delta,2))
    perm=delta[:,[2,0,1]]
    np.testing.assert_allclose(m.squared_components(delta,2),m.squared_components(perm,0))


def test_unseen_context_keeps_distance_term():
    fitted=dict(intercept=.5,context_offsets={'known':.8},coefficients=[2.])
    np.testing.assert_allclose(m.predict(fitted,np.array(['unseen']),np.array([[.3]])),[-.1])
