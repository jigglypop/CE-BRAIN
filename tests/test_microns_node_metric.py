from pathlib import Path
import sys

import numpy as np

HERE=Path(__file__).resolve().parents[1]/"verify/Q-NPF-04/fixed_points_metric"
sys.path.insert(0,str(HERE))
import microns_node_metric as model


def test_every_directed_pair_held_out_once_and_both_nodes_absent():
    groups=np.repeat(np.arange(5),2);pre,post=np.where(~np.eye(10,dtype=bool));coverage=np.zeros(len(pre),int)
    blocks=model.pair_blocks(groups,pre,post)
    np.testing.assert_array_equal(blocks,model.pair_blocks(groups,post,pre))
    for block,(a,b) in enumerate(model.BLOCKS):
        train,test=model.split_masks(groups,pre,post,block);coverage+=test
        tr=set(pre[train])|set(post[train]);te=set(pre[test])|set(post[test])
        assert tr.isdisjoint(te)
        assert len(tr)==(8 if a==b else 6)
    np.testing.assert_array_equal(coverage,1)


def test_objective_gradient_has_only_context_penalty():
    problem=model.Problem(np.array([1,1,3,3]),np.array([0,1,1,0]))
    features=np.array([[1.,2.,3.],[2.,1.,0.],[3.,4.,2.],[0.,1.,1.]])
    p=np.array([-.5,.1,-.2,.3,.2,.1]);eps=1e-6
    analytic=problem.objective(p,features)[1];numeric=[]
    for j in range(len(p)):
        step=np.zeros_like(p);step[j]=eps
        numeric.append((problem.objective(p+step,features)[0]-problem.objective(p-step,features)[0])/(2*eps))
    np.testing.assert_allclose(analytic,numeric,atol=1e-9)


def test_metric_boundary_signed_competitor_and_units():
    m=model.metric_for("typed_diagonal_quadratic",[1.,2.,3.])
    np.testing.assert_allclose(m["diagonal_per_um2"],[.0001,.0002,.0003]);assert m["SPD"]
    m=model.metric_for("typed_diagonal_quadratic",[1.,0.,3.]);assert m["PSD"] and not m["SPD"] and m["exact_zero_components"]==1
    m=model.metric_for("typed_signed_quadratic",[1.,-1.,3.]);assert not m["PSD"] and m["negative_components"]==1
    m=model.metric_for("strategy_isotropic_radial",[2.]);np.testing.assert_allclose(m["diagonal_per_um2"],[.0004]*3)


def test_unseen_context_keeps_global_intercept_and_geometry():
    fit=dict(intercept=-1.,context_offsets={"3":.2},coefficients=[.5])
    value=model.predict(fit,np.array([3,9]),np.array([[2.],[4.]]))
    np.testing.assert_allclose(value,[-1.8,-3.])


def test_covariant_cost_for_row_coordinate_transform():
    a=np.array([[.9,.2,0.],[-.1,1.1,.05],[0.,0.,1.2]])
    d=np.array([[1.,2.,3.],[-2.,1.,4.]]);g=np.diag([.1,.2,.4]);inverse=np.linalg.inv(a)
    q=d@a;gq=inverse@g@inverse.T
    np.testing.assert_allclose(np.einsum("ni,ij,nj->n",d,g,d),np.einsum("ni,ij,nj->n",q,gq,q),atol=1e-12)
