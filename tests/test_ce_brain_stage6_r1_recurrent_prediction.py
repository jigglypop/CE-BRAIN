import numpy as np

from examples.brain import ce_brain_stage6_r1_recurrent_prediction as stage6


def test_repeat_slices_require_complete_movie_repeats():
    frames = np.tile(np.arange(900), 2)
    blocks = np.repeat([4, 12], 900)
    slices, repeat_blocks = stage6.repeat_slices(frames, blocks)
    assert [(s.start, s.stop) for s in slices] == [(0, 900), (900, 1800)]
    assert repeat_blocks == [4, 12]


def test_mode_destruction_removes_leading_singular_value():
    matrix = np.diag([4.0, 3.0, 2.0, 1.0])
    destroyed = stage6.destroy_modes(matrix)
    assert np.linalg.svd(destroyed, compute_uv=False)[0] == 3.0


def test_decision_requires_all_three_gates():
    passed = {"improvement": 0.02, "lower_95": 0.01, "median": 0.02}
    comparisons = {"R_vs_N": passed, "R_vs_D": passed, "R_vs_M": passed}
    assert stage6.decide(comparisons) == "DEVELOPMENT_RECURRENT_PREDICTIVE_MODES_SUPPORTED"
    comparisons["R_vs_M"] = {"improvement": 0.0, "lower_95": -0.01, "median": 0.0}
    assert stage6.decide(comparisons) == "HISTORY_USEFUL_RECURRENCE_NOT_ISOLATED"

