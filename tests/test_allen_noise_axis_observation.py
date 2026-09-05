from pathlib import Path
import sys

import numpy as np
import pytest

HERE=Path(__file__).resolve().parents[1]/"verify/Q-NPF-04/fixed_points_metric"
sys.path.insert(0,str(HERE))
import allen_noise_axis_observation as model


def cell(cid,values):
    good=all(v is not None for v in values)
    return dict(cell_id=cid,identity_checked=True,qc_pass_IC_count=len(values),
        qc_pass_IC_finite_noise_count=sum(v is not None for v in values),
        qc_pass_IC_records=[dict(clamp_mode="ic",qc_pass=1,baseline_noise_stdev=v) for v in values],
        mean_qc_pass_IC_noise_V=float(np.mean(values)) if len(values)>1 and good else None)


def test_missing_value_is_distinct_from_uncollected_cell():
    payload=dict(wanted_cells=2,cells=[cell(1,[1e-5,3e-5]),cell(2,[])])
    result=model.validate_noise(payload,[1,2])
    assert result[1]["mean_qc_pass_IC_noise_V"]==2e-5
    assert result[2]["mean_qc_pass_IC_noise_V"] is None
    with pytest.raises(ValueError,match="incomplete"):
        model.validate_noise(dict(wanted_cells=2,cells=payload["cells"][:1]),[1,2])
    payload["cells"][0]["mean_qc_pass_IC_noise_V"]=1e-5
    with pytest.raises(ValueError,match="not reproduced"):model.validate_noise(payload,[1,2])


def test_noise_preprocessing_uses_training_reference():
    raw=np.array([[1.,1.,2.,-10.],[3.,9.,4.,-8.],[np.nan,np.nan,np.nan,np.nan]])
    prep=model.depth.fit_transform(raw)
    out=model.transform(np.array([[100.,10000.,1000.,-5.],[np.nan,np.nan,np.nan,np.nan]]),prep)
    np.testing.assert_allclose(out[0],[98.,2498.75,997.,4.,0.,0.,0.])
    np.testing.assert_allclose(out[1],[0.,0.,0.,0.,1.,1.,1.])


def test_profile_objective_gradient_and_pack_prediction():
    context=np.array(["a","a","b","b"]);obs=np.array([[1.,0.],[0.,1.],[1.,1.],[-1.,0.]])
    features=np.array([[.1],[.6],[1.],[2.]])
    problem=model.ObservationProblem(context,[0,1,1,0],obs)
    params=np.array([-.7,.1,-.2,.3,.4,.5]);eps=1e-6
    analytic=problem.objective(params,features)[1];numeric=[]
    for j in range(len(params)):
        step=np.zeros_like(params);step[j]=eps
        numeric.append((problem.objective(params+step,features)[0]-problem.objective(params-step,features)[0])/(2*eps))
    np.testing.assert_allclose(analytic,numeric,atol=1e-9)
    packed=problem.pack(dict(params=params,objective=0.,iterations=0,gradient_max=0.))
    np.testing.assert_allclose(model.predict(packed,context,obs,features),-.7+params[1:3][problem.group]+obs@params[3:5]-features[:,0]*.5)
    np.testing.assert_allclose(model.predict(packed,np.array(["unseen"]),obs[:1],features[:1]),[-.45])


def test_profile_interface_preserves_observation_parameters_and_isotropy():
    rng=np.random.default_rng(903);n=50
    context=np.array(["a","b"]*(n//2));obs=rng.normal(size=(n,2));delta=rng.normal(size=(n,3))*100
    y=(rng.random(n)<.3).astype(float);problem=model.ObservationProblem(context,y,obs)
    distance=np.linalg.norm(delta,axis=1)[:,None]/100
    direct=problem.fit(distance);initial=direct["params"].copy();initial[-1]*=np.sqrt(2)
    components=model.axis_model.squared_components(delta,2)
    profile=model.axis_model.profile_radial(problem,components,initial)
    iso=profile["boundaries"]["0.5"]
    assert len(iso["observation_coefficients"])==2 and len(iso["coefficients"])==1
    a=model.predict(iso,context,obs,model.axis_model.radial_feature(components,.5))
    b=model.predict(problem.pack(direct),context,obs,distance)
    np.testing.assert_allclose(a,b,atol=1e-3)
    assert profile["fit"]["objective"]<=min(r["objective"] for r in profile["boundaries"].values())+1e-12


def test_main_refuses_to_fit_without_completed_collection(tmp_path,monkeypatch):
    monkeypatch.setattr(model,"OUTPUT",tmp_path/"result.json")
    monkeypatch.setattr(model,"ARRAYS",tmp_path/"arrays.npz")
    monkeypatch.setattr(model,"NOISE",tmp_path/"missing_noise.json")
    with pytest.raises(FileNotFoundError,match="Complete target-cell"):
        model.main()
    assert not (tmp_path/"result.json").exists()
