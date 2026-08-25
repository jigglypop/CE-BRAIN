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
I = _load("verified_interval_contour", "verified_interval_contour.py")
M = _load("ce_verified_interval_tightening", "verified_interval_tightening.py")


def _diagonal_box(value: object):
    return [[(value, 0), (0, 0)], [(0, 0), (value, 0)]]


def test_diagonal_box_selects_strictly_tighter_induced_bound() -> None:
    result = M.verified_tight_interval_family_circle(
        [[0, 0], [0, 10]], uncertainty_radii=_diagonal_box(F(1, 5)),
        center=0, radius=1, spectral_reference_scale=1, sqrt_precision=40,
    )
    assert result.selected_uncertainty_method == "INDUCED_1_INFINITY"
    assert result.normalized_induced_uncertainty_upper >= F(1, 5)
    assert result.normalized_induced_uncertainty_upper ** 2 >= F(1, 25)
    assert result.normalized_selected_uncertainty_upper < (
        result.frobenius_bridge.normalized_uncertainty_upper
    )
    assert result.status == "VERIFIED_RATIONAL_TIGHT_INTERVAL_FAMILY_CONTOUR_BRIDGE"
    assert result.rank_preserved_for_entire_family is True


def test_tightening_can_pass_when_frobenius_bridge_is_conservatively_negative() -> None:
    result = M.verified_tight_interval_family_circle(
        [[0, 0], [0, 10]], uncertainty_radii=_diagonal_box(F(1, 5)),
        center=0, radius=1, spectral_reference_scale=1, sqrt_precision=40,
    )
    assert result.frobenius_bridge.validation_level is None
    assert result.frobenius_bridge.status == "VERIFIED_INTERVAL_UNCERTAINTY_NOT_BELOW_MARGIN"
    assert result.validation_level == "VERIFIED_RATIONAL_TIGHT_INTERVAL_FAMILY_CONTOUR_BRIDGE"


def test_asymmetric_box_selects_frobenius_and_scalar_tie_policy_is_frobenius() -> None:
    asymmetric = M.verified_tight_interval_family_circle(
        [[0, 0], [0, 10]],
        uncertainty_radii=[[(F(1, 100), 0), (F(1, 100), 0)], [(F(1, 100), 0), (0, 0)]],
        center=0, radius=1, spectral_reference_scale=1, sqrt_precision=40,
    )
    assert asymmetric.selected_uncertainty_method == "FROBENIUS"
    assert asymmetric.normalized_selected_uncertainty_upper < asymmetric.normalized_induced_uncertainty_upper

    scalar = M.verified_tight_interval_family_circle(
        [[0]], uncertainty_radii=[[(F(3, 100), F(1, 25))]], center=0,
        radius=1, spectral_reference_scale=1, sqrt_precision=40,
    )
    assert scalar.selected_uncertainty_method == "FROBENIUS"
    assert scalar.normalized_selected_uncertainty_upper == scalar.normalized_induced_uncertainty_upper


def test_entry_and_product_sqrt_brackets_expose_exact_residual_checks() -> None:
    result = M.verified_tight_interval_family_circle(
        [[0]], uncertainty_radii=[[(F(3, 100), F(1, 25))]], center=0,
        radius=1, spectral_reference_scale=1, sqrt_precision=40,
    )
    entry_lower, entry_upper = result.normalized_entry_magnitude_brackets[0][0]
    assert entry_lower * entry_lower <= F(1, 400) <= entry_upper * entry_upper
    assert result.entry_magnitude_self_checks == (((True, True),),)
    product_lower, product_upper = result.normalized_induced_product_sqrt_bracket
    product = result.normalized_induced_one_upper * result.normalized_induced_infinity_upper
    assert product_lower * product_lower <= product <= product_upper * product_upper
    assert result.induced_product_sqrt_self_checks == (True, True)


def test_zero_uncertainty_and_strict_margin_failure_are_fail_closed() -> None:
    zero = M.verified_tight_interval_family_circle(
        [[0]], uncertainty_radii=[[(0, 0)]], center=0, radius=1,
        spectral_reference_scale=1,
    )
    assert zero.status == "VERIFIED_RATIONAL_TIGHT_INTERVAL_FAMILY_CONTOUR_BRIDGE"
    assert zero.normalized_selected_uncertainty_upper == 0
    assert zero.projector_perturbation_upper == 0

    large = M.verified_tight_interval_family_circle(
        [[0, 0], [0, 10]], uncertainty_radii=_diagonal_box(1), center=0,
        radius=1, spectral_reference_scale=1,
    )
    assert large.status == "VERIFIED_TIGHT_INTERVAL_UNCERTAINTY_NOT_BELOW_MARGIN"
    assert large.validation_level is None
    assert large.rank_preserved_for_entire_family is False


@pytest.mark.parametrize(
    "bad",
    [
        [],
        [[(0, 0)]],
        [[(-1, 0), (0, 0)], [(0, 0), (0, 0)]],
        [[(0.0, 0), (0, 0)], [(0, 0), (0, 0)]],
        [[(True, 0), (0, 0)], [(0, 0), (0, 0)]],
    ],
)
def test_predecessor_uncertainty_schema_remains_fail_closed(bad: object) -> None:
    with pytest.raises(ValueError):
        M.verified_tight_interval_family_circle(
            [[0, 0], [0, 10]], uncertainty_radii=bad, center=0, radius=1,
            spectral_reference_scale=1,
        )


def test_normalize_first_tightening_is_exactly_unit_invariant() -> None:
    base = M.verified_tight_interval_family_circle(
        [[0, 0], [0, 10]], uncertainty_radii=_diagonal_box(F(1, 10)),
        center=0, radius=1, spectral_reference_scale=1, sqrt_precision=40,
    )
    scaled = M.verified_tight_interval_family_circle(
        [[0, 0], [0, 70]], uncertainty_radii=_diagonal_box(F(7, 10)),
        center=0, radius=7, spectral_reference_scale=7, sqrt_precision=40,
    )
    assert scaled.status == base.status
    assert scaled.selected_uncertainty_method == base.selected_uncertainty_method
    assert scaled.normalized_entry_magnitude_brackets == base.normalized_entry_magnitude_brackets
    assert scaled.normalized_induced_uncertainty_upper == base.normalized_induced_uncertainty_upper
    assert scaled.normalized_selected_uncertainty_upper == base.normalized_selected_uncertainty_upper
    assert scaled.normalized_robust_delta_lower == base.normalized_robust_delta_lower
    assert scaled.projector_perturbation_upper == base.projector_perturbation_upper
    assert scaled.raw_selected_uncertainty_upper == 7 * base.raw_selected_uncertainty_upper
    assert scaled.raw_robust_resolvent_upper == base.raw_robust_resolvent_upper / 7


def test_nonnormal_optional_projector_bridge_adds_both_errors() -> None:
    result = M.verified_tight_interval_family_projector(
        [[0, F(1, 25)], [0, 4]],
        uncertainty_radii=[[(0, 0), (F(1, 1000), 0)], [(0, 0), (0, 0)]],
        center=0, radius=1, spectral_reference_scale=1,
        expansion_factor=F(3, 2), eigenvectors=[[1, F(1, 100)], [0, 1]],
        eigenvalues=[[0, 0], [0, 4]], sqrt_precision=40,
    )
    assert result.status == "VERIFIED_RATIONAL_TIGHT_INTERVAL_FAMILY_PROJECTOR_BRIDGE"
    assert result.nominal_quadrature_error_upper is not None
    assert result.uncertainty_projector_error_upper is not None
    assert result.total_projector_error_upper == (
        result.nominal_quadrature_error_upper + result.uncertainty_projector_error_upper
    )


def test_invalid_strip_and_unsupported_mesh_are_noncertificates_or_errors() -> None:
    invalid = M.verified_tight_interval_family_projector(
        [[0]], uncertainty_radii=[[(0, 0)]], center=0, radius=1,
        spectral_reference_scale=1, expansion_factor=2,
        eigenvectors=[[1]], eigenvalues=[[1]],
    )
    assert invalid.status == "VERIFIED_NOMINAL_STRIP_CERTIFICATE_UNAVAILABLE"
    assert invalid.total_projector_error_upper is None
    with pytest.raises(ValueError, match="four-node"):
        M.verified_tight_interval_family_circle(
            [[0]], uncertainty_radii=[[(0, 0)]], center=0, radius=1,
            spectral_reference_scale=1, nodes=8,
        )
