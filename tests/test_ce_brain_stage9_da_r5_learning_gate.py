import numpy as np

from examples.brain import ce_brain_stage9_da_r5_learning_gate as gate


def test_parse_merges_split_day_by_numeric_day():
    assert gate.parse(gate.Path("sub-60sD-F8_ses-day02a.nwb")) == ("sub-60sD-F8", 2)
    assert gate.parse(gate.Path("sub-60sD-F8_ses-day02b.nwb")) == ("sub-60sD-F8", 2)


def test_ridge_predict_uses_requested_feature_and_returns_finite_values():
    train = [{"x": float(i), "target": float(2 * i + 1)} for i in range(5)]
    prediction, coefficient = gate.ridge_predict(train, [{"x": 5.0, "target": 11.0}], ("x",))
    assert prediction.shape == (1,)
    assert np.isfinite(prediction[0]) and np.all(np.isfinite(coefficient))


def test_comparison_rewards_lower_error_with_positive_interval():
    target = np.arange(14, dtype=float); primary = target.copy(); baseline = target + 1
    row_subjects = ["a"] * 7 + ["b"] * 7
    result = gate.comparison(primary, baseline, target, row_subjects, ["a", "b"], 9)
    assert result["improvement"] == 1.0 and result["lower_95"] > 0
