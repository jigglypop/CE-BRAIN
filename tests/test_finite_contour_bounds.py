from __future__ import annotations

import importlib.util
from pathlib import Path
import sys

import numpy as np
import pytest


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "reality_stone" / "python" / "reality_stone" / "clarus" / "finite_contour_bounds.py"


def _load_standalone_module():
    name = "ce_finite_contour_bounds"
    spec = importlib.util.spec_from_file_location(name, MODULE_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    try:
        spec.loader.exec_module(module)
    finally:
        sys.modules.pop(name, None)
    return module


_bounds = _load_standalone_module()
circle_float64_estimate = _bounds.circle_float64_estimate
analytic_strip_float64_estimate = _bounds.analytic_strip_float64_estimate


def test_diagonal_circle_matches_dense_fixture_and_reports_only_estimates() -> None:
    transition = np.diag([0.2, 1.4]).astype(complex)
    coarse = circle_float64_estimate(
        transition, center=0.5, radius=0.4, nodes=32, spectral_reference_scale=1.0
    )
    dense = circle_float64_estimate(
        transition, center=0.5, radius=0.4, nodes=1024, spectral_reference_scale=1.0
    )
    exact = np.diag([1.0, 0.0])

    assert coarse.validation_level == "FLOAT64_UNVERIFIED_FULL_CIRCLE_ESTIMATE"
    assert coarse.delta_hat_positive
    assert coarse.resolvent_upper_estimate is not None
    assert np.linalg.norm(dense.projection_estimate - exact, ord=2) < 1e-8
    assert np.linalg.norm(coarse.projection_estimate - dense.projection_estimate, ord=2) < 1e-3
    assert coarse.normalized_delta_hat_estimate == pytest.approx(coarse.delta_hat_estimate)


def test_scaled_units_preserve_normalized_circle_estimates() -> None:
    transition = np.diag([0.2, 1.4]).astype(complex)
    base = circle_float64_estimate(
        transition, center=0.5, radius=0.4, nodes=32, spectral_reference_scale=1.0
    )
    scaled = circle_float64_estimate(
        10.0 * transition, center=5.0, radius=4.0, nodes=32, spectral_reference_scale=10.0
    )

    assert scaled.normalized_sampled_min_sigma_estimate == pytest.approx(base.normalized_sampled_min_sigma_estimate)
    assert scaled.normalized_chord_upper_estimate == pytest.approx(base.normalized_chord_upper_estimate)
    assert scaled.normalized_delta_hat_estimate == pytest.approx(base.normalized_delta_hat_estimate)


def test_coarse_sampling_can_have_nonpositive_delta_hat_estimate() -> None:
    estimate = circle_float64_estimate(
        np.diag([0.2, 2.0]), center=0.5, radius=0.4, nodes=4, spectral_reference_scale=1.0
    )

    assert not estimate.delta_hat_positive
    assert estimate.resolvent_upper_estimate is None


def test_nonnormal_pseudospectral_case_is_not_promoted_by_float_estimate() -> None:
    estimate = circle_float64_estimate(
        np.array([[0.0, 100.0], [0.0, 1.0]]),
        center=0.0,
        radius=0.4,
        nodes=32,
        spectral_reference_scale=1.0,
    )

    assert estimate.sampled_min_sigma_estimate > 0.0
    assert not estimate.delta_hat_positive
    assert estimate.validation_level == "FLOAT64_UNVERIFIED_FULL_CIRCLE_ESTIMATE"


def test_annulus_eigenvalue_suppresses_strip_estimate() -> None:
    estimate = analytic_strip_float64_estimate(
        np.diag([0.2, 1.1, 3.0]),
        center=0.0,
        radius=1.0,
        strip_half_width=0.2,
        nodes=64,
        spectral_reference_scale=1.0,
    )

    assert estimate.numerical_annulus_eigenvalue_count == 1
    assert estimate.annulus_status == "NUMERICAL_ANNULUS_OR_BOUNDARY_EIGENVALUE"
    assert estimate.inner_circle_estimate is None
    assert estimate.outer_circle_estimate is None
    assert estimate.integrand_M_estimate is None
    assert estimate.quadrature_error_estimate is None


def test_clean_diagonal_strip_fixture_estimate_exceeds_its_observed_error_only_here() -> None:
    transition = np.diag([0.2, 2.0]).astype(complex)
    strip = analytic_strip_float64_estimate(
        transition,
        center=0.0,
        radius=1.0,
        strip_half_width=0.5,
        nodes=32,
        spectral_reference_scale=1.0,
    )
    exact = np.diag([1.0, 0.0])
    observed_error = np.linalg.norm(strip.central_circle_estimate.projection_estimate - exact, ord=2)

    assert strip.validation_level == "FLOAT64_UNVERIFIED_ANALYTIC_STRIP_ESTIMATE"
    assert strip.numerical_annulus_eigenvalue_count == 0
    assert strip.annulus_status == "NUMERICAL_ANNULUS_CLEAR_FLOAT64"
    assert strip.inner_circle_estimate is not None
    assert strip.outer_circle_estimate is not None
    assert strip.integrand_M_estimate is not None
    assert strip.quadrature_error_estimate is not None
    assert observed_error < strip.quadrature_error_estimate


def test_boundary_eigenvalue_suppresses_strip_estimates() -> None:
    inner_radius = np.exp(-0.2)
    estimate = analytic_strip_float64_estimate(
        np.diag([0.2, inner_radius, 3.0]),
        center=0.0,
        radius=1.0,
        strip_half_width=0.2,
        nodes=64,
        spectral_reference_scale=1.0,
    )

    assert estimate.numerical_annulus_eigenvalue_count >= 1
    assert estimate.annulus_status == "NUMERICAL_ANNULUS_OR_BOUNDARY_EIGENVALUE"
    assert estimate.integrand_M_estimate is None
    assert estimate.quadrature_error_estimate is None


@pytest.mark.parametrize(
    ("transition", "center", "radius", "nodes", "scale"),
    [
        ([[float("nan")]], 0.0, 1.0, 8, 1.0),
        ([[0.0]], complex(float("nan"), 0.0), 1.0, 8, 1.0),
        ([[0.0]], 0.0, 0.0, 8, 1.0),
        ([[0.0]], 0.0, 1.0, 3, 1.0),
        ([[0.0]], 0.0, 1.0, 8, 0.0),
        ([[]], 0.0, 1.0, 8, 1.0),
    ],
)
def test_invalid_inputs_are_rejected(transition, center, radius, nodes, scale) -> None:
    with pytest.raises(ValueError):
        circle_float64_estimate(
            transition,
            center=center,
            radius=radius,
            nodes=nodes,
            spectral_reference_scale=scale,
        )


def test_extreme_strip_width_is_rejected_before_float_overflow() -> None:
    with pytest.raises(ValueError, match="strip radii"):
        analytic_strip_float64_estimate(
            [[0.2, 0.0], [0.0, 2.0]],
            center=0.0,
            radius=1.0,
            strip_half_width=1000.0,
            nodes=8,
            spectral_reference_scale=1.0,
        )
