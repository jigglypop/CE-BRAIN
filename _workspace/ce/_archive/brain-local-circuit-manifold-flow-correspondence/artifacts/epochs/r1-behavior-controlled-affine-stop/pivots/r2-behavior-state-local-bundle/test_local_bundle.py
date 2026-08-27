from __future__ import annotations

import importlib.util
from pathlib import Path

import numpy as np


HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location(
    "r2_local_bundle_under_test", HERE / "analyze_local_bundle_pivot.py"
)
r2 = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(r2)


def test_behavior_chart_fit_is_deterministic_and_behavior_only() -> None:
    rng = np.random.default_rng(17)
    anchors = np.array(
        [
            [-4.0, -2.0, 0.0, 0.0, 0.0, 0.0],
            [-1.0, 4.0, 0.0, 0.0, 0.0, 0.0],
            [2.0, -3.0, 0.0, 0.0, 0.0, 0.0],
            [4.0, 3.0, 0.0, 0.0, 0.0, 0.0],
        ]
    )
    phi = np.vstack([anchor + 0.08 * rng.normal(size=(80, 6)) for anchor in anchors])
    rows = np.arange(phi.shape[0])

    centers_a, meta_a = r2.fit_behavior_charts(phi, rows)
    centers_b, meta_b = r2.fit_behavior_charts(phi.copy(), rows.copy())
    labels = r2.assign_charts(phi, centers_a)

    assert np.array_equal(centers_a, centers_b)
    assert meta_a["iterations"] == meta_b["iterations"]
    assert sorted(np.bincount(labels, minlength=4).tolist()) == [80, 80, 80, 80]


def test_local_bundle_recovers_a_contracting_piecewise_affine_fixture() -> None:
    rng = np.random.default_rng(23)
    charts, units, dimension = 4, 6, 2
    pairs_per_chart = 120
    total_pairs = charts * pairs_per_chart
    x = np.zeros((2 * total_pairs, units))
    phi = np.zeros((2 * total_pairs, 6))
    labels = np.full(2 * total_pairs, -1, dtype=np.int64)
    train_rows = []
    development_rows = []
    cursor = 0

    for chart in range(charts):
        tangent, _ = np.linalg.qr(rng.normal(size=(units, dimension)))
        normal = np.eye(units) - tangent @ tangent.T
        mean = rng.normal(scale=0.5, size=units)
        base = np.diag([0.45 + 0.03 * chart, 0.25])
        base_input = rng.normal(scale=0.08, size=(6, dimension))
        normal_input = rng.normal(scale=0.04, size=(dimension + 6, units)) @ normal
        rho = 0.52 + 0.04 * chart
        for pair in range(pairs_per_chart):
            row = 2 * cursor
            behavior = rng.normal(size=6)
            z = rng.normal(scale=1.5, size=dimension)
            raw_normal = 0.08 * rng.normal(size=units)
            residual = raw_normal @ normal
            current = mean + z @ tangent.T + residual
            features = np.r_[z, behavior]
            next_z = z @ base + behavior @ base_input
            next_residual = rho * residual + features @ normal_input
            target = mean + next_z @ tangent.T + next_residual

            x[row], x[row + 1] = current, target
            phi[row] = phi[row + 1] = behavior
            labels[row] = labels[row + 1] = chart
            (train_rows if pair < 90 else development_rows).append(row)
            cursor += 1

    train_rows = np.asarray(train_rows, dtype=np.int64)
    development_rows = np.asarray(development_rows, dtype=np.int64)
    geometry = r2.prepare_geometry(x, train_rows, labels, charts)
    model = r2.fit_local_bundle(
        x, phi, train_rows, labels, geometry, dimension, lam=1e-4
    )
    estimate = r2.local_bundle_predict(model, x, phi, development_rows, labels)
    target = x[development_rows + 1]
    normalized_error = float(np.square(target - estimate).sum() / np.square(target).sum())
    contraction = r2.q_audit(model)

    assert normalized_error < 0.01
    assert contraction["passes"]
    assert contraction["q_max_upper_bound"] < 0.8


def test_shifted_chart_labels_never_wrap_between_splits() -> None:
    labels = np.arange(24, dtype=np.int64) % 4
    blocks = {"train": (0, 12), "development": (12, 24)}
    shifted = r2.shift_chart_labels(labels, blocks, shift=3)

    assert np.all(shifted[:3] == -1)
    assert np.all(shifted[12:15] == -1)
    assert np.array_equal(shifted[3:12], labels[:9])
    assert np.array_equal(shifted[15:24], labels[12:21])
