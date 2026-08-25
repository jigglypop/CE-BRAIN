from __future__ import annotations

import importlib.util
from pathlib import Path
import sys

import numpy as np
import pytest


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "reality_stone" / "python" / "reality_stone" / "clarus" / "finite_riesz.py"


def _load_standalone_module():
    name = "ce_finite_riesz"
    spec = importlib.util.spec_from_file_location(name, MODULE_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    try:
        spec.loader.exec_module(module)
    finally:
        sys.modules.pop(name, None)
    return module


_finite_riesz = _load_standalone_module()
finite_riesz_projection = _finite_riesz.finite_riesz_projection


def test_nonnormal_oblique_fixture_converges_and_realifies_to_distinct_q() -> None:
    transition = np.array([[0.2, 0.0, 12.0], [0.0, 0.8, 0.0], [0.0, 0.0, 1.4]])
    certificate = finite_riesz_projection(
        transition, center=0.5, radius=0.4, spectral_reference_scale=1.0, nodes=32
    )
    exact_projection = np.array([[1.0, 0.0, -10.0], [0.0, 1.0, 0.0], [0.0, 0.0, 0.0]])

    assert certificate.validation_level == "FINITE_A_POSTERIORI_CONTOUR_APPROXIMATION"
    assert certificate.quadrature_error_bound is None
    assert certificate.selected_eigenvalue_count == certificate.realified_numerical_rank == 2
    assert certificate.raw_sampled_min_singular_separation > 0.0
    assert certificate.raw_sampled_max_resolvent_norm > 0.0
    assert np.linalg.norm(certificate.refined_approximation - exact_projection, ord=2) < 1e-6
    assert certificate.refinement_difference_norm < np.linalg.norm(
        certificate.approximation - exact_projection, ord=2
    )
    assert np.allclose(certificate.orthogonal_range_projector, np.diag([1.0, 1.0, 0.0]), atol=1e-6)
    assert not np.allclose(certificate.refined_approximation.real, certificate.orthogonal_range_projector)
    assert certificate.finite_numerical_eigenvalue_margin is not None
    assert certificate.eigenvalue_margin_label == "FINITE_NUMERICAL_EIGENVALUE_MARGIN"
    assert certificate.normalized_refinement_residual < 2e-4
    assert certificate.effective_rank_threshold == pytest.approx(
        certificate.rank_tolerance
        * max(1.0, certificate.realified_range_singular_values[0])
    )


def test_scaled_transition_and_contour_preserve_normalized_decisions() -> None:
    transition = np.array([[0.2, 0.0, 12.0], [0.0, 0.8, 0.0], [0.0, 0.0, 1.4]])
    base = finite_riesz_projection(
        transition, center=0.5, radius=0.4, spectral_reference_scale=1.0, nodes=32
    )
    scaled = finite_riesz_projection(
        10.0 * transition,
        center=5.0,
        radius=4.0,
        spectral_reference_scale=10.0,
        nodes=32,
    )

    assert scaled.selected_eigenvalue_count == base.selected_eigenvalue_count
    assert scaled.realified_numerical_rank == base.realified_numerical_rank
    assert scaled.normalized_refinement_residual == pytest.approx(
        base.normalized_refinement_residual, rel=1e-8, abs=1e-12
    )
    assert scaled.normalized_idempotence_residual == pytest.approx(
        base.normalized_idempotence_residual, rel=1e-8, abs=1e-12
    )
    assert scaled.normalized_eigenvalue_margin == pytest.approx(
        base.normalized_eigenvalue_margin, rel=1e-8, abs=1e-12
    )


def test_contour_crossing_and_nonreal_center_are_rejected() -> None:
    with pytest.raises(ValueError, match="crosses the contour"):
        finite_riesz_projection(
            np.diag([0.9, 1.4]), center=0.5, radius=0.4, spectral_reference_scale=1.0
        )
    with pytest.raises(ValueError, match="finite real"):
        finite_riesz_projection(
            np.diag([0.2, 1.4]),
            center=0.5 + 0.1j,
            radius=0.4,
            spectral_reference_scale=1.0,
        )


def test_coarse_quadrature_preserves_the_rank_guard_and_strict_mode_can_reject() -> None:
    transition = np.diag([0.2, 1.4])
    with pytest.raises(ValueError, match="numerical rank disagrees"):
        finite_riesz_projection(
            transition, center=0.5, radius=0.4, spectral_reference_scale=1.0, nodes=4
        )

    coarse = finite_riesz_projection(
        transition, center=0.5, radius=0.4, spectral_reference_scale=1.0, nodes=8, rank_tolerance=0.1
    )

    assert (
        coarse.normalized_refinement_residual > 1e-3
        or coarse.normalized_idempotence_residual > 1e-3
    )
    with pytest.raises(ValueError, match="strict tolerance"):
        finite_riesz_projection(
            transition,
            center=0.5,
            radius=0.4,
            spectral_reference_scale=1.0,
            nodes=8,
            rank_tolerance=0.1,
            strict=True,
            certificate_tolerance=1e-3,
        )


def test_real_rotation_pair_is_conjugation_closed_and_realifies_to_rank_two() -> None:
    transition = np.array([[0.0, -0.2, 0.0], [0.2, 0.0, 0.0], [0.0, 0.0, 1.0]])
    certificate = finite_riesz_projection(
        transition, center=0.0, radius=0.4, spectral_reference_scale=1.0, nodes=32
    )

    assert certificate.selected_eigenvalue_count == certificate.realified_numerical_rank == 2
    assert np.allclose(certificate.orthogonal_range_projector, np.diag([1.0, 1.0, 0.0]), atol=1e-6)
    assert certificate.imaginary_residual < 1e-6


def test_pseudospectral_adversary_has_margin_but_large_sampled_resolvent() -> None:
    transition = np.array([[0.0, 100.0], [0.0, 1.0]])
    certificate = finite_riesz_projection(
        transition, center=0.0, radius=0.4, spectral_reference_scale=1.0, nodes=32
    )

    assert certificate.finite_numerical_eigenvalue_margin is not None
    assert certificate.finite_numerical_eigenvalue_margin > 0.0
    assert certificate.raw_sampled_max_resolvent_norm > 50.0
    assert certificate.validation_level == "FINITE_A_POSTERIORI_CONTOUR_APPROXIMATION"
    assert certificate.quadrature_error_bound is None
