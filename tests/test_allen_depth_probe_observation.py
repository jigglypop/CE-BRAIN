import importlib.util
import json
from pathlib import Path
import sys

import numpy as np

HERE=Path(__file__).resolve().parents[1]/"verify/Q-NPF-04/fixed_points_metric"
sys.path.insert(0,str(HERE))
import allen_depth_probe_observation as model
import allen_observation_medium_inputs as collector


def test_producer_features_keep_mean_rule_and_unknown_class():
    values,detail=model.source_features(-10e-6,110e-6,"ex",1000,7)
    np.testing.assert_allclose(values,[.5,.25,np.log1p(800)])
    assert detail["raw_mean_depth_um"]==50
    values,detail=model.source_features(400e-6,400e-6,"mixed",100,200)
    assert np.isnan(values).all()
    assert detail["depth_status"]=="mean_outside_0_300um"
    assert detail["selected_final_count"] is None


def test_preprocessing_uses_training_only_and_shared_depth_missing_flag():
    training=np.array([[1.,1.,2.],[3.,9.,4.],[np.nan,np.nan,np.nan]])
    prep=model.fit_transform(training)
    out=model.transform(np.array([[100.,10000.,1000.],[np.nan,np.nan,np.nan]]),prep)
    np.testing.assert_allclose(prep["mean"],[2.,5.,3.])
    np.testing.assert_allclose(out[0],[98.,2498.75,997.,0.,0.])
    np.testing.assert_allclose(out[1],[0.,0.,0.,1.,1.])


def test_penalized_objective_gradient_with_distance():
    problem=model.Problem(np.array(["a","a","b","b"]),np.array([0,1,1,0]),
                          np.array([[1.,0.],[0.,1.],[1.,1.],[-1.,0.]]),np.array([10.,60.,100.,200.]))
    params=np.array([-.7,.1,-.2,.3,.4,.5]);analytic=problem.objective(params)[1]
    eps=1e-6;numeric=[]
    for j in range(len(params)):
        step=np.zeros_like(params);step[j]=eps
        numeric.append((problem.objective(params+step)[0]-problem.objective(params-step)[0])/(2*eps))
    np.testing.assert_allclose(analytic,numeric,atol=1e-9)


def test_two_distinct_spd_costs_can_share_detected_labels():
    g1,g2,p1,p2,s1,s2=model.detection_equivalence(np.array([[1.,2.,3.],[-2.,1.,.1],[0.,0.,0.],[0.,0.,1.]]))
    assert np.linalg.eigvalsh(g1).min()>0 and np.linalg.eigvalsh(g2).min()>0
    assert not np.array_equal(g1,g2)
    assert np.all((s2>0)&(s2<=.8))
    np.testing.assert_allclose(s1*p1,s2*p2,rtol=1e-14,atol=1e-16)
    assert np.max(abs(p1-p2))>.01


def test_noise_mean_needs_two_good_ic_records_and_serializes():
    def row(mode,qc,value):return dict(clamp_mode=mode,qc_pass=qc,baseline_noise_stdev=value)
    result=collector.aggregate([row("ic",1,1e-5),row("ic",1,3e-5),row("vc",1,10.),row("ic",0,10.)])
    assert result["mean_qc_pass_IC_noise_V"]==2e-5
    assert result["qc_pass_IC_finite_noise_count"]==2
    json.dumps(result,allow_nan=False)
    assert collector.aggregate([row("ic",1,1e-5)])["mean_qc_pass_IC_noise_V"] is None
    assert collector.aggregate([row("ic",1,1e-5),row("ic",1,None)])["mean_qc_pass_IC_noise_V"] is None
