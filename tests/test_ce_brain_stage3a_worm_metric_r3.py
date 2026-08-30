from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import numpy as np


MODULE_PATH = Path(__file__).parents[1] / "examples" / "brain" / "ce_brain_stage3a_worm_metric_r3.py"
SPEC = importlib.util.spec_from_file_location("ce_brain_stage3a_worm_metric_r3", MODULE_PATH)
assert SPEC and SPEC.loader
stage3a_r3 = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = stage3a_r3
SPEC.loader.exec_module(stage3a_r3)


def test_residual_z_uses_per_receiver_finite_observations() -> None:
    rng = np.random.default_rng(7)
    timestamps = np.arange(100, dtype=float)
    red = rng.normal(size=(100, 20))
    green = .4 * red + rng.normal(scale=.2, size=(100, 20))
    red[:25, :10] = np.nan
    green[:25, :10] = np.nan
    z, finite = stage3a_r3.residual_z_finite(
        green, red, timestamps, np.array([50.]), np.array([50.5]))
    assert np.all(np.isnan(z[:25, :10]))
    assert np.all(np.isfinite(z[25:, :10]))
    assert np.array_equal(finite, np.isfinite(z))


def test_r3_freezes_prior_revisions() -> None:
    paths = stage3a_r3.preregistered_files()
    assert len(paths) == 9
    assert all(path.is_file() for path in paths)
    assert stage3a_r3.R2_PATH in paths
    assert stage3a_r3.CONTRACT in paths
