"""Focused tests for the BA-SRM10 R-A bounded-influence standardization.

Contract: paper/검증_원장/BA_SRM10_유효차원_강건성_계약.md. These tests cover
the frozen apparatus properties only; they do not rerun the sealed evaluation.
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import numpy as np
import pytest

_RUNNER = Path(__file__).resolve().parents[1] / "examples" / "brain" / "ba_srm10_ra_runner.py"


@pytest.fixture(scope="module")
def runner():
    spec = importlib.util.spec_from_file_location("ba_srm10_ra_runner", _RUNNER)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    try:
        spec.loader.exec_module(module)
        yield module
    finally:
        sys.modules.pop(spec.name, None)


def test_clean_gaussian_matches_moment_standardization(runner):
    rng = np.random.default_rng(7)
    x = rng.standard_normal((3, 1500))
    m = np.ones_like(x, dtype=np.uint8)
    cz, nz, d, counts = runner.robust_pair(x, x, m, 1500, runner.CLIP)
    mz = (x - x.mean(axis=1, keepdims=True)) / x.std(axis=1, keepdims=True)
    assert float(np.median(np.abs(cz - mz))) < 0.05
    assert float(np.mean(np.abs(cz) >= runner.CLIP)) < 1e-3
    assert np.array_equal(cz, nz)
    assert counts.tolist() == [1500, 1500, 1500]


def test_spike_contamination_has_bounded_influence(runner):
    rng = np.random.default_rng(11)
    clean = rng.standard_normal((1, 2000))
    contaminated = clean.copy()
    spikes = rng.choice(2000, size=20, replace=False)
    contaminated[0, spikes] = 10.0
    m = np.ones_like(clean, dtype=np.uint8)
    _, nz, _, _ = runner.robust_pair(clean, contaminated, m, 2000, runner.CLIP)
    # Spikes are clipped to the frozen bound and the robust scale barely moves.
    assert float(np.max(np.abs(nz))) <= runner.CLIP + 1e-12
    keep = np.setdiff1d(np.arange(2000), spikes)
    cz, _, _, _ = runner.robust_pair(clean, clean, m, 2000, runner.CLIP)
    ratio = np.abs(nz[0, keep]) / np.maximum(np.abs(cz[0, keep]), 1e-9)
    assert abs(float(np.median(ratio)) - 1.0) < 0.05


def test_zero_signal_fails_closed(runner):
    x = np.zeros((2, 600))
    m = np.ones_like(x, dtype=np.uint8)
    with pytest.raises(ValueError, match="PREFIX_ROBUST_SCALE"):
        runner.robust_pair(x, x, m, 600, runner.CLIP)


def test_mask_derived_d_matches_frozen_convention(runner):
    rng = np.random.default_rng(3)
    x = rng.standard_normal((2, 800))
    m = (rng.random((2, 800)) >= 0.1).astype(np.uint8)
    x_masked = np.where(m == 1, x, 0.0)
    _, _, d_robust, _ = runner.robust_pair(x_masked, x_masked, m, 460, runner.CLIP)
    _, _, d_moment, _ = runner.preprocess_pair(x_masked, x_masked, m, 460)
    assert np.array_equal(d_robust, d_moment)
