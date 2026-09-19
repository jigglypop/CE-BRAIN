import importlib.util
from pathlib import Path

import numpy as np
import pytest

SPEC = importlib.util.spec_from_file_location('baseline_extrapolation',
    Path(__file__).resolve().parents[1] / 'verify/Q-NPF-04/allen_synphys/recovery_baseline_extrapolation.py')
module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(module)


def test_affine_baseline_is_removed_but_old_operator_retains_drift():
    fs, center = 100000, .05
    t = np.arange(10000) / fs
    result = module.measure(-.065 + .013 * t, fs, center)
    assert abs(result['linear_uV']) < 1e-8
    assert result['old_uV'] == pytest.approx(136.5)
    assert result['pre_slope_uV_per_ms'] == pytest.approx(13)


def test_added_post_response_is_preserved_and_cannot_change_baseline_slope():
    fs, center = 100000, .05
    t = np.arange(10000) / fs
    v = -.065 + .013 * t
    before = module.measure(v, fs, center)
    v[(t > center + .001) & (t < center + .009)] += .000250
    after = module.measure(v, fs, center)
    assert after['linear_uV'] == pytest.approx(250)
    assert after['pre_slope_uV_per_ms'] == before['pre_slope_uV_per_ms']
    assert after['old_uV'] - before['old_uV'] == pytest.approx(250)


def test_noise_formula_matches_explicit_operator_weights():
    tp, tq = module.window_times(100000)
    dt = tq.mean() - tp.mean()
    x = tp - tp.mean()
    weights = np.r_[-np.ones(len(tp))/len(tp) - dt*x/np.dot(x,x), np.ones(len(tq))/len(tq)]
    geometry = module.noise_geometry(100000)
    assert abs(weights.sum()) < 1e-12
    assert abs(np.dot(weights, np.r_[tp, tq])) < 1e-12
    assert np.dot(weights, weights) == pytest.approx(geometry['linear_weight_norm_squared'])
    assert geometry['sd_ratio'] > 5


def test_exponential_tail_is_not_exactly_removed_by_linear_extrapolation():
    fs, center = 100000, .05
    t = np.arange(10000) / fs
    result = module.measure(-.065 + .001*np.exp(-t/.020), fs, center)
    # Curved residuals survive: a linear fit is not a physical deconvolution.
    assert abs(result['linear_uV']) > 1
    assert result['linear_uV'] == pytest.approx(result['old_uV']-result['correction_uV'])


@pytest.mark.parametrize('fs,center', [(0,.05), (100000,.002), (100000,.099), (100000,float('nan'))])
def test_invalid_windows_fail_explicitly(fs, center):
    with pytest.raises(ValueError):
        module.measure(np.zeros(10000), fs, center)
