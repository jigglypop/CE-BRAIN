"""Held-out source subtraction and singleton fallback checks."""

import importlib.util
from pathlib import Path

import numpy as np
import pytest

SPEC = importlib.util.spec_from_file_location(
    "malecns_type_closure", Path(__file__).resolve().parents[1] / "verify/MaleCNS/type_conditioned_closure.py")
module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(module)


def test_type_loo_beats_mixed_parent_without_reading_heldout_source():
    counts = np.array([[10, 0], [5, 0], [0, 10], [0, 5]])
    degree, peers, base, candidate = module.loo_scores(counts, [0] * 4, [0, 0, 1, 1], 1)
    assert peers.all()
    assert np.all(candidate < base)
    assert candidate[0] == pytest.approx(-10 * np.log(5.5 / 6))
    changed = counts.copy()
    changed[0] = [100, 0]
    changed_loss = module.loo_scores(changed, [0] * 4, [0, 0, 1, 1], 1)[3]
    assert changed_loss[0] / 100 == pytest.approx(candidate[0] / 10)


def test_singleton_type_and_zero_degree_peer_fall_back_to_parent():
    counts = np.array([[2, 5], [0, 0], [4, 3]])
    degree, peers, base, candidate = module.loo_scores(counts, [0, 0, 0], [0, 0, 1], 10)
    assert not peers.any()
    assert np.array_equal(base, candidate)
    summary = module.score_summary(degree, peers, base, candidate, np.ones(3, bool))
    assert summary["sources"] == 2
    assert summary["relative_loss_reduction"] == 0


def test_mismatched_type_can_hurt_prediction():
    counts = np.array([[10, 0], [0, 10], [10, 0], [0, 10]])
    _, _, base, candidate = module.loo_scores(counts, [0] * 4, [0, 0, 1, 1], 1)
    assert np.all(candidate > base)


def test_refinement_must_be_nested_and_smoothing_positive():
    with pytest.raises(ValueError, match="nest"):
        module.loo_scores(np.ones((2, 2), dtype=int), [0, 1], [0, 0], 1)
    with pytest.raises(ValueError, match="alpha"):
        module.loo_scores(np.ones((2, 2), dtype=int), [0, 0], [0, 0], 0)
