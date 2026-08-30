import numpy as np

from examples.brain import ce_brain_update_task_rapid_correction as correction


def test_fit_axis_recovers_held_out_choice_direction():
    rng = np.random.default_rng(7)
    target = np.tile(np.array([-1, 1]), 40)
    x = rng.normal(0, 0.2, (80, 5))
    x[:, 0] += target
    axis, normalization = correction._fit_axis(x[:56], target[:56])
    prediction = np.where(correction._project(x[56:], axis, normalization) >= 0, 1, -1)
    assert correction._balanced_accuracy(target[56:], prediction) > 0.95


def test_did_is_switch_change_minus_stay_change():
    delta = np.array([1.2, 0.8, 0.1, -0.1])
    update_type = np.array([2, 2, 3, 3])
    assert correction._did(delta, update_type) == 1.0
