import importlib.util
from pathlib import Path

import numpy as np

PATH=Path(__file__).resolve().parents[1]/"verify/Q-NPF-04/fixed_points_metric/allen_structural_metric_baseline.py"
spec=importlib.util.spec_from_file_location("structural_metric",PATH)
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)


def test_probed_boundary_and_nonsynaptic_class():
    assert not m.probed('ex',10,100)
    assert m.probed('ex',11,None)
    assert m.probed('in',None,11)
    assert not m.probed(None,11,10)
    assert m.probed('mixed',11,11)


def test_donor_parser_preserves_group_across_slices():
    a=m.donor_id('Pvalb-IRES-Cre;Ai14-276838.03.02')
    b=m.donor_id('Pvalb-IRES-Cre;Ai14-276838.04.02')
    assert a==b=='276838'
    assert m.fold_for_donor(a)==m.fold_for_donor(b)
    assert m.donor_id('unregistered') is None


def test_fixed_3D_isotropic_cost_is_rotation_invariant():
    displacement=np.array([[30.,40.,12.],[-3.,8.,20.]])
    rotation=np.array([[0.,-1.,0.],[1.,0.,0.],[0.,0.,1.]])
    beta=.7;g=beta*np.eye(3)/100**2
    cost=np.einsum('ni,ij,nj->n',displacement,g,displacement)
    np.testing.assert_allclose(cost,beta*m.features(np.linalg.norm(displacement,axis=1),'quadratic_metric')[:,0])
    np.testing.assert_allclose(cost,np.einsum('ni,ij,nj->n',displacement@rotation.T,rotation@g@rotation.T,displacement@rotation.T))


def test_negative_distance_slope_is_preserved_as_nonmetric_competitor():
    distance=np.tile([20.,80.,140.,200.],20)
    context=np.array(['fixed']*len(distance));y=np.tile([0.,0.,1.,1.],20)
    constrained=m.fit_model(distance,context,y,'quadratic_metric')
    free=m.fit_model(distance,context,y,'signed_quadratic')
    assert constrained['distance_coefficients'][0]<1e-8
    assert not constrained['metric']['interior_SPD']
    assert free['distance_coefficients'][0]<0
    unseen=m.predict(constrained,np.array([50.]),np.array(['unseen']))
    np.testing.assert_allclose(unseen,constrained['intercept'])


def test_cluster_comparison_preserves_constant_paired_difference():
    result=m.cluster_comparison(np.array(['a','a','b','c','c','c']),np.full(6,-.02))
    np.testing.assert_allclose(result['pair_weighted_cluster_percentile95'],[-.02,-.02])
    np.testing.assert_allclose(result['equal_donor_percentile95'],[-.02,-.02])
