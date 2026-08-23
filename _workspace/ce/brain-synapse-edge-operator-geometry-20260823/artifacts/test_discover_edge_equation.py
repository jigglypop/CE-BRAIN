from __future__ import annotations

import importlib.util
from collections import Counter
from pathlib import Path
import sys

import numpy as np


MODULE_PATH = Path(__file__).with_name("discover_edge_equation.py")
SPEC = importlib.util.spec_from_file_location("discover_edge_equation", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
discover = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = discover
SPEC.loader.exec_module(discover)


def test_group_fold_is_deterministic_and_group_atomic():
    groups = ["a", "a", "b", "b", "c"]
    folds = [discover.deterministic_fold(group, "salt", 5) for group in groups]
    assert folds[0] == folds[1]
    assert folds[2] == folds[3]
    assert folds == [discover.deterministic_fold(group, "salt", 5) for group in groups]


def test_robust_scaler_imputes_missing_without_infinities():
    values = np.asarray([[1.0, np.nan], [2.0, 4.0], [3.0, 6.0]])
    location, scale = discover.robust_location_scale(values)
    transformed = discover.transform(values, location, scale)
    assert np.all(np.isfinite(transformed))
    assert np.all(scale > 0.0)
    assert transformed[0, 1] == 0.0


def test_interaction_jacobian_matches_finite_difference():
    base = np.asarray([[0.4, -0.2]])
    interactions = [(0, 1)]
    selected = [0, 1, 2]
    beta = np.asarray([[0.0], [2.0], [3.0], [5.0]])
    analytic = discover.jacobians_from_equation(
        base, beta, selected, 2, interactions
    )[0, 0]

    def value(point):
        terms = discover.build_terms(np.asarray([point]), interactions)[:, selected]
        return float(discover.predict_ridge(beta, terms)[0, 0])

    numeric = []
    step = 1e-6
    for column in range(2):
        plus = base[0].copy()
        minus = base[0].copy()
        plus[column] += step
        minus[column] -= step
        numeric.append((value(plus) - value(minus)) / (2.0 * step))
    assert np.allclose(analytic, numeric, rtol=1e-7, atol=1e-7)


def test_greedy_group_cv_finds_simple_signal():
    rng = np.random.default_rng(7)
    groups = np.repeat(np.asarray([f"g{idx}" for idx in range(40)]), 2)
    x = rng.normal(size=(groups.size, 3))
    y = np.column_stack([2.0 * x[:, 0] + 0.05 * rng.normal(size=groups.size)])
    folds = np.asarray(
        [discover.deterministic_fold(group, "synthetic", 4) for group in groups]
    )
    result = discover.greedy_select(x, y, groups, folds, 3, [])
    assert result["selected"]
    assert result["selected"][0] == 0
    assert result["cv_mse"] < 0.1


def test_stability_core_requires_three_folds_and_interaction_parents():
    names = ["a", "b", "(a)*(b)"]
    interactions = [(0, 1)]
    assert discover.stability_core_indices(
        names, Counter({"a": 5, "b": 2, "(a)*(b)": 4}), 2, interactions
    ) == [0]
    assert discover.stability_core_indices(
        names, Counter({"a": 5, "b": 3, "(a)*(b)": 4}), 2, interactions
    ) == [0, 1, 2]


def test_finite_geometry_receipt_has_bounded_effective_dimension():
    rng = np.random.default_rng(9)
    base = rng.normal(size=(80, 2))
    beta = np.asarray([[0.0, 0.0], [1.0, 0.0], [0.0, 2.0]])
    residual = rng.normal(scale=0.2, size=(80, 2))
    receipt = discover.geometry_receipt(
        base,
        beta,
        selected=[0, 1],
        base_names=["a", "b"],
        interactions=[],
        standardized_oof_residual=residual,
    )
    assert receipt["status"] == "DISCOVERY_ONLY_TRACE_CLASS_REFERENCE_RECEIPT"
    assert receipt["finite_basis_dimension"] == 2
    assert set(receipt["pointwise_rank_counts"]) == {2}
    for summary in receipt["effective_dimension"].values():
        assert 0.0 <= summary["q50"] <= 2.0
