import importlib.util
from pathlib import Path

import numpy as np

SPEC = importlib.util.spec_from_file_location("d1", Path(__file__).with_name("self_trajectory_d1.py"))
d1 = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(d1)


def test_area_reverse_and_shuffle_preserve_order_invariants():
    increments = np.array([[1., 0.], [0., 2.], [3., 1.]])
    assert np.allclose(d1.area(-increments[::-1]), -d1.area(increments))
    shuffled = increments[np.random.default_rng(3).permutation(3)]
    assert np.allclose(increments.mean(0), shuffled.mean(0))
    assert np.allclose(increments.min(0), shuffled.min(0))
    assert np.allclose(increments.max(0), shuffled.max(0))


def test_contract_feature_counts():
    assert d1.feature_count(4, "M0") == 53
    assert d1.feature_count(4, "M1") == 59


def test_fold_local_transform_does_not_use_holdout_window():
    rng = np.random.default_rng(7)
    train = [rng.normal(size=(126, 63)), rng.normal(size=(126, 63))]
    first = d1.fit_transform(train, 2)
    second = d1.fit_transform(train + [rng.normal(loc=5.0, size=(126, 63))], 2)
    assert not np.allclose(first["median"], second["median"])
    held = np.full((126, 63), 1e9)
    assert np.isfinite(d1.apply_transform(held, first)).all()


def test_ridge_leaves_intercept_unpenalized():
    x = np.column_stack((np.ones(8), np.zeros(8)))
    coefficient = d1.ridge_fit(x, np.full((8, 1), 3.0), 1e6)
    assert np.allclose(coefficient[0], 3.0)


def test_paired_folds_hold_one_trial_pair_together():
    folds = list(d1.paired_folds(4))
    assert [held for _, held in folds] == [0, 1, 2, 3]
    assert all(len(train) == 3 and held not in train for train, held in folds)


def test_execute_preserves_qc_when_every_pair_is_rejected(monkeypatch):
    diagnostics = [{"trial_hash": "x", "accepted": False, "windows": [{"qc": {"metric": 7.0}}]}]
    monkeypatch.setattr(d1, "load_d1", lambda *_: ([], diagnostics))
    receipt = d1.execute(Path("manifest"), Path("a0"), Path("a2"))
    assert receipt["status"] == "D1_FAIL_CLOSED"
    assert receipt["scientific_endpoint_opened"] is False
    assert receipt["model_outcome_computed"] is False
    assert receipt["accepted_pairs"] == 0
    assert receipt["rejected_pairs"] == 1
    assert receipt["pair_qc"] == diagnostics
