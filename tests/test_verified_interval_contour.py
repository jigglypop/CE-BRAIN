from __future__ import annotations

import importlib.util
from fractions import Fraction as F
from pathlib import Path
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]
MODULE_DIR = ROOT / "reality_stone" / "python" / "reality_stone" / "clarus"


def _load(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, MODULE_DIR / filename)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


R = _load("verified_rational_contour", "verified_rational_contour.py")
M = _load("ce_verified_interval_contour", "verified_interval_contour.py")


def test_zero_uncertainty_preserves_nominal_certificate_exactly() -> None:
    result = M.verified_interval_family_circle(
        [[0]], uncertainty_radii=[[(0, 0)]], center=0, radius=1,
        spectral_reference_scale=1, sqrt_precision=32,
    )
    assert result.status == "VERIFIED_RATIONAL_INTERVAL_FAMILY_CONTOUR_BRIDGE"
    assert result.validation_level == result.status
    assert result.rank_preserved_for_entire_family is True
    assert result.normalized_uncertainty_squared == 0
    assert result.normalized_uncertainty_sqrt_bracket == (0, 0)
    assert result.uncertainty_sqrt_self_checks == (True, True)
    assert result.normalized_robust_delta_lower == result.nominal.normalized_delta_lower
    assert result.projector_perturbation_upper == 0
    assert result.normalized_robust_resolvent_upper == result.nominal.normalized_resolvent_upper


def test_rectangular_box_gets_exact_outward_frobenius_enclosure() -> None:
    result = M.verified_interval_family_circle(
        [[0]], uncertainty_radii=[[(F(3, 100), F(1, 25))]], center=0,
        radius=1, spectral_reference_scale=1, sqrt_precision=40,
    )
    assert result.status == "VERIFIED_RATIONAL_INTERVAL_FAMILY_CONTOUR_BRIDGE"
    assert result.normalized_uncertainty_squared == F(1, 400)
    lower, upper = result.normalized_uncertainty_sqrt_bracket
    assert lower * lower <= F(1, 400) <= upper * upper
    assert result.uncertainty_sqrt_self_checks == (True, True)
    assert result.normalized_robust_delta_lower == (
        result.nominal.normalized_delta_lower - upper
    )
    assert result.projector_perturbation_upper is not None
    assert result.projector_perturbation_upper > 0


def test_equal_or_larger_uncertainty_and_nominal_failure_are_noncertificates() -> None:
    too_large = M.verified_interval_family_circle(
        [[0]], uncertainty_radii=[[(1, 0)]], center=0, radius=1,
        spectral_reference_scale=1,
    )
    assert too_large.status == "VERIFIED_INTERVAL_UNCERTAINTY_NOT_BELOW_MARGIN"
    assert too_large.validation_level is None
    assert too_large.rank_preserved_for_entire_family is False
    assert too_large.normalized_robust_delta_lower is not None
    assert too_large.normalized_robust_delta_lower <= 0
    assert too_large.normalized_robust_resolvent_upper is None
    assert too_large.projector_perturbation_upper is None

    singular_nominal = M.verified_interval_family_circle(
        [[1]], uncertainty_radii=[[(0, 0)]], center=0, radius=1,
        spectral_reference_scale=1,
    )
    assert singular_nominal.status == "VERIFIED_NOMINAL_CIRCLE_CERTIFICATE_UNAVAILABLE"
    assert singular_nominal.nominal.status == "VERIFIED_SAMPLED_NODE_SINGULAR"
    assert singular_nominal.validation_level is None
    assert singular_nominal.rank_preserved_for_entire_family is False


@pytest.mark.parametrize(
    "uncertainty",
    [
        [],
        [[(0, 0)], [(0, 0)]],
        [[(0,)]],
        [[(-1, 0)]],
        [[(0.0, 0)]],
        [[(True, 0)]],
        [[("01", 0)]],
    ],
)
def test_uncertainty_schema_rejects_shape_negative_and_nonexact_bounds(uncertainty: object) -> None:
    with pytest.raises(ValueError):
        M.verified_interval_family_circle(
            [[0]], uncertainty_radii=uncertainty, center=0, radius=1,
            spectral_reference_scale=1,
        )


def test_normalize_first_certificate_is_exactly_unit_invariant() -> None:
    base = M.verified_interval_family_circle(
        [[0]], uncertainty_radii=[[(F(1, 100), F(1, 50))]], center=0,
        radius=1, spectral_reference_scale=1, sqrt_precision=40,
    )
    scaled = M.verified_interval_family_circle(
        [[0]], uncertainty_radii=[[(F(7, 100), F(7, 50))]], center=0,
        radius=7, spectral_reference_scale=7, sqrt_precision=40,
    )
    assert scaled.status == base.status
    assert scaled.normalized_uncertainty_squared == base.normalized_uncertainty_squared
    assert scaled.normalized_uncertainty_sqrt_bracket == base.normalized_uncertainty_sqrt_bracket
    assert scaled.normalized_robust_delta_lower == base.normalized_robust_delta_lower
    assert scaled.normalized_robust_resolvent_upper == base.normalized_robust_resolvent_upper
    assert scaled.projector_perturbation_upper == base.projector_perturbation_upper
    assert scaled.raw_uncertainty_upper == 7 * base.raw_uncertainty_upper
    assert scaled.raw_robust_delta_lower == 7 * base.raw_robust_delta_lower
    assert scaled.raw_robust_resolvent_upper == base.raw_robust_resolvent_upper / 7


def test_nonnormal_nominal_matrix_is_supported_by_resolvent_route() -> None:
    result = M.verified_interval_family_circle(
        [[0, F(1, 25)], [0, 4]],
        uncertainty_radii=[[(0, 0), (F(1, 1000), 0)], [(0, 0), (0, 0)]],
        center=0, radius=1, spectral_reference_scale=1, sqrt_precision=40,
    )
    assert result.status == "VERIFIED_RATIONAL_INTERVAL_FAMILY_CONTOUR_BRIDGE"
    assert result.projector_perturbation_upper is not None


def test_optional_projector_bridge_adds_uncertainty_and_quadrature_errors() -> None:
    result = M.verified_interval_family_projector(
        [[0, F(1, 25)], [0, 4]],
        uncertainty_radii=[[(0, 0), (F(1, 1000), 0)], [(0, 0), (0, 0)]],
        center=0, radius=1, spectral_reference_scale=1,
        expansion_factor=F(3, 2),
        eigenvectors=[[1, F(1, 100)], [0, 1]],
        eigenvalues=[[0, 0], [0, 4]],
        sqrt_precision=40,
    )
    assert result.status == "VERIFIED_RATIONAL_INTERVAL_FAMILY_PROJECTOR_BRIDGE"
    assert result.nominal_quadrature_error_upper is not None
    assert result.uncertainty_projector_error_upper is not None
    assert result.total_projector_error_upper == (
        result.nominal_quadrature_error_upper + result.uncertainty_projector_error_upper
    )


def test_projector_bridge_fails_closed_when_nominal_strip_witness_is_invalid() -> None:
    result = M.verified_interval_family_projector(
        [[0]], uncertainty_radii=[[(0, 0)]], center=0, radius=1,
        spectral_reference_scale=1, expansion_factor=2,
        eigenvectors=[[1]], eigenvalues=[[1]],
    )
    assert result.status == "VERIFIED_NOMINAL_STRIP_CERTIFICATE_UNAVAILABLE"
    assert result.validation_level is None
    assert result.total_projector_error_upper is None


def test_unsupported_mesh_and_invalid_precision_remain_rejected() -> None:
    with pytest.raises(ValueError, match="four-node"):
        M.verified_interval_family_circle(
            [[0]], uncertainty_radii=[[(0, 0)]], center=0, radius=1,
            spectral_reference_scale=1, nodes=8,
        )
    with pytest.raises(ValueError, match="precision"):
        M.verified_interval_family_circle(
            [[0]], uncertainty_radii=[[(0, 0)]], center=0, radius=1,
            spectral_reference_scale=1, sqrt_precision=True,
        )
