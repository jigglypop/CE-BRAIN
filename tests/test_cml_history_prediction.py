import importlib.util
from pathlib import Path

import numpy as np
import pytest

SOURCE = Path(__file__).resolve().parents[1] / 'verify/Q-NPF-04/hippocampal_reinstatement/cml_history_prediction.py'
spec = importlib.util.spec_from_file_location('cml_history_prediction_test', SOURCE)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


def test_native_forecast_support_does_not_cross_run_gap_or_use_target():
    values = np.arange(12 * 3, dtype=float).reshape(12, 3)
    runs = np.repeat([0, 1], 6)
    starts = np.r_[np.arange(6) * 800, 16000 + np.arange(6) * 800]
    design = m.make_design(values, runs, runs + 1, starts, 1, 1, 1)
    assert design['rows'].tolist() == [4, 5, 10, 11]
    assert design['histories'].tolist() == [[3, 2, 1, 0], [4, 3, 2, 1], [9, 8, 7, 6], [10, 9, 8, 7]]
    assert np.all(starts[design['histories']].max(axis=1) + 800 == design['starts'])
    changed = values.copy()
    changed[4] += 100000
    other = m.make_design(changed, runs, runs + 1, starts, 1, 1, 1)
    for key in design['designs']:
        np.testing.assert_array_equal(design['designs'][key][0], other['designs'][key][0])
    with pytest.raises(ValueError, match='duplicate native'):
        m.make_design(values, runs, runs + 1, np.zeros(12), 1, 1, 1)


def test_equal_list_weights_and_ridge_match_augmented_least_squares():
    rng = np.random.default_rng(410)
    x, y = rng.normal(size=(18, 24)), rng.normal(size=(18, 3))
    weights = m.list_weights([1] * 3 + [2] * 15)
    assert weights[:3].sum() == pytest.approx(.5)
    assert weights[3:].sum() == pytest.approx(.5)
    pred, fit = m.fit_predict(x, y, x[:4], weights)
    z = (x - fit['x_center']) / fit['x_scale']
    yz = (y - fit['y_center']) / fit['y_scale']
    a = np.vstack((np.sqrt(weights)[:, None] * z, np.eye(24)))
    b = np.vstack((np.sqrt(weights)[:, None] * yz, np.zeros((24, 3))))
    coefficient = np.linalg.lstsq(a, b, rcond=None)[0]
    np.testing.assert_allclose(fit['coefficient'], coefficient, atol=1e-12)
    np.testing.assert_allclose(pred, fit['y_center'] + z[:4] @ coefficient * fit['y_scale'], atol=1e-12)


def test_held_targets_cannot_change_held_fit_and_predictive_signal_beats_noise():
    rng = np.random.default_rng(841)
    lists = np.repeat([1, 2, 3], 80)
    c, h, control = (rng.normal(size=(240, 1)) for _ in range(3))
    y = 4 * h + rng.normal(scale=.1, size=(240, 1))
    designs = dict(c_current=c, c_history=c, c_history_h_current=np.c_[c, h],
                   c_history_h_history=np.c_[c, h], c_history_control_history=np.c_[c, control])
    data = dict(targets=y, lists=lists, designs=designs)
    result, arrays = m.evaluate(data)
    assert result['contrasts']['hippocampal_history']['equal_list'] > .2
    assert result['contrasts']['hippocampal_vs_control']['equal_list'] > .2
    modified = dict(data, targets=y.copy())
    modified['targets'][lists == 1] *= -100
    _, later = m.evaluate(modified)
    np.testing.assert_array_equal(arrays['fold_1_c_history_h_history_coefficient'],
                                  later['fold_1_c_history_h_history_coefficient'])
    np.testing.assert_array_equal(arrays['prediction_c_history_h_history'][lists == 1],
                                  later['prediction_c_history_h_history'][lists == 1])
