import importlib.util
from pathlib import Path

import numpy as np
import pytest

PATH = Path(__file__).resolve().parents[1]/"verify/Q-NPF-04/fixed_points_metric/allen_cortical_registration_audit.py"
spec = importlib.util.spec_from_file_location("registration_audit", PATH)
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)


def test_similarity_preserves_image_reflection_and_generalization():
    x = np.array([[0.,0.,1.],[20.,0.,4.],[0.,30.,2.],[20.,30.,9.]])
    b = np.array([[0.,-.8],[-.8,0.],[0.,0.]])
    y = x@b+[500.,300.]
    fitted = m.fit(x,y,"xy_similarity")
    test = np.array([[17.,-23.,123.]])
    np.testing.assert_allclose(m.predict(fitted,test),test@b+[500.,300.])


def test_affine_rejects_unidentified_out_of_plane_coordinate():
    x = np.array([[0.,0.,0.],[1.,0.,0.],[0.,1.,0.],[1.,1.,0.]])
    assert m.fit(x,x[:,:2],"xyz_affine") is None
    assert m.fit(x,x[:,:2],"xy_affine") is not None


def test_cell_holdout_affine_recovers_known_transform():
    rng = np.random.default_rng(12)
    x = rng.normal(size=(8,3))*100
    b = np.array([[.8,.1],[-.2,-.9],[.3,-.1]])
    y = x@b+[2000.,700.]
    for i in range(len(x)):
        mask=np.arange(len(x))!=i
        f=m.fit(x[mask],y[mask],"xyz_affine")
        np.testing.assert_allclose(m.predict(f,x[i]),y[i],atol=1e-10)


def test_hidden_direction_allows_distinct_spd_completions():
    b=np.array([[.8,.2],[-.1,.9],[.3,-.2]])
    g1,k=m.metric_completion(b,.25);g2,_=m.metric_completion(b,4.)
    assert np.linalg.eigvalsh(g1).min()>0 and np.linalg.eigvalsh(g2).min()>0
    np.testing.assert_allclose(k@b,0,atol=1e-14)
    np.testing.assert_allclose(b.T@(g2-g1)@b,0,atol=1e-16)
    assert k@g2@k>k@g1@k
    with pytest.raises(ValueError):m.metric_completion(b,0)


def test_image_plane_does_not_identify_pia_tilt():
    # Fields f_a(x,y,z)=y+a*z agree on image plane z=0 but have different normals.
    points=np.array([[0.,0.,0.],[2.,1.,0.],[-1.,3.,0.]])
    n1=np.array([0.,1.,0.]);n2=np.array([0.,1.,2.])
    np.testing.assert_allclose(points@n1,points@n2)
    assert not np.allclose(n1/np.linalg.norm(n1),n2/np.linalg.norm(n2))
