from __future__ import annotations

import importlib.util
from fractions import Fraction
from pathlib import Path
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "reality_stone" / "python" / "reality_stone" / "clarus" / "verified_rational_contour.py"


def _load():
    spec = importlib.util.spec_from_file_location("ce_verified_rational_contour", MODULE_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    try:
        spec.loader.exec_module(module)
    finally:
        sys.modules.pop(spec.name, None)
    return module


M = _load()
F = Fraction


def test_exact_parser_rejects_binary_and_python_complex_inputs() -> None:
    for value in (1.0, complex(1, 0), True, (F(1), 0.0), (F(1), True)):
        with pytest.raises(ValueError):
            M.parse_qcomplex(value)
    assert M.parse_qcomplex(("1/3", "-2.5")).real == F(1, 3)
    assert M.parse_qcomplex(("1/3", "-2.5")).imag == F(-5, 2)
    for text in ("01", "1/02", "1.0", "+1", "1_0", "1 /2", "1e2", "-0", "0.50"):
        with pytest.raises(ValueError):
            M.parse_qcomplex(text)


def test_exact_sqrt_enclosure_self_checks_and_inadequate_precision_remains_safe() -> None:
    lower, upper, lower_ok, upper_ok = M._dyadic_sqrt(F(2), 0)
    assert (lower, upper, lower_ok, upper_ok) == (F(1), F(2), True, True)
    lower, upper, lower_ok, upper_ok = M._dyadic_sqrt(F(2), 10)
    assert lower * lower <= F(2) <= upper * upper
    assert lower_ok and upper_ok
    with pytest.raises(ValueError):
        M._dyadic_sqrt(F(2), -1)


def test_exact_circle_reports_certificate_and_exact_p4() -> None:
    result = M.verified_rational_circle([[0]], center=0, radius=1, spectral_reference_scale=1, sqrt_precision=32)
    assert result.status == "VERIFIED_RATIONAL_FULL_CIRCLE_ENCLOSURE"
    assert result.validation_level == result.status
    assert result.projection_p4 == ((M.ONE,),)
    assert result.normalized_delta_lower is not None and result.normalized_delta_lower > 0
    assert result.raw_resolvent_upper == result.normalized_resolvent_upper
    assert all(lo * lo <= hi * hi for lo, hi in result.normalized_node_sqrt_brackets)
    assert result.sqrt2_bracket is not None and result.sqrt2_self_checks == (True, True)
    sqrt2_lower, sqrt2_upper = result.sqrt2_bracket
    assert sqrt2_lower * sqrt2_lower <= 2 <= sqrt2_upper * sqrt2_upper
    assert result.chord_factor_bracket is not None and result.chord_factor_self_checks == (True, True)
    factor_lower, factor_upper = result.chord_factor_bracket
    assert factor_lower * factor_lower <= 2 - sqrt2_lower <= factor_upper * factor_upper


def test_singular_node_and_nonpositive_controls_fail_closed() -> None:
    singular = M.verified_rational_circle([[1]], center=0, radius=1, spectral_reference_scale=1)
    assert singular.status == "VERIFIED_SAMPLED_NODE_SINGULAR"
    weak = M.verified_rational_circle([[F(1, 2)]], center=0, radius=1, spectral_reference_scale=1)
    assert weak.status == "VERIFIED_LOWER_BOUND_NONPOSITIVE"
    assert weak.validation_level is None
    assert weak.normalized_resolvent_upper is None


def test_rejects_unsupported_mesh_and_empty_or_invalid_rational_matrix() -> None:
    with pytest.raises(ValueError, match="four-node"):
        M.verified_rational_circle([[0]], center=0, radius=1, spectral_reference_scale=1, nodes=8)
    for matrix in ([], [[0, 1]], [[float("nan")]]):
        with pytest.raises(ValueError):
            M.verified_rational_circle(matrix, center=0, radius=1, spectral_reference_scale=1)


def test_normalize_first_is_exactly_invariant_under_common_rescaling() -> None:
    base = M.verified_rational_circle([[0]], center=0, radius=1, spectral_reference_scale=1, sqrt_precision=8)
    scaled = M.verified_rational_circle([[0]], center=0, radius=7, spectral_reference_scale=7, sqrt_precision=8)
    assert base.status == scaled.status
    assert base.normalized_node_sigma_lowers == scaled.normalized_node_sigma_lowers
    assert base.normalized_chord_upper == scaled.normalized_chord_upper
    assert base.normalized_delta_lower == scaled.normalized_delta_lower
    assert base.sqrt2_bracket == scaled.sqrt2_bracket
    assert base.sqrt2_self_checks == scaled.sqrt2_self_checks
    assert base.chord_factor_bracket == scaled.chord_factor_bracket
    assert base.chord_factor_self_checks == scaled.chord_factor_self_checks
    assert scaled.raw_delta_lower == 7 * base.raw_delta_lower
    assert scaled.raw_resolvent_upper == base.raw_resolvent_upper / 7


def test_valid_oblique_witness_returns_exact_projector_and_strip_certificate() -> None:
    # U = V diag(0, 4) V^-1 is oblique/non-normal but not adversarially ill-conditioned.
    result = M.verified_rational_analytic_strip(
        [[0, F(1, 25)], [0, 4]], center=0, radius=1, spectral_reference_scale=1,
        expansion_factor=F(3, 2), eigenvectors=[[1, F(1, 100)], [0, 1]], eigenvalues=[[0, 0], [0, 4]],
        sqrt_precision=40,
    )
    assert result.status == "VERIFIED_RATIONAL_ANALYTIC_STRIP_ENCLOSURE"
    assert result.exact_projection == ((M.ONE, M.QComplex(F(-1, 100))), (M.ZERO, M.ZERO))
    assert result.error_upper is not None and result.error_upper > 0
    assert result.central.projection_p4 == ((M.ONE, M.QComplex(F(-64, 6375))), (M.ZERO, M.QComplex(F(-1, 255))))


@pytest.mark.parametrize("value", [F(1, 2), F(2), F(3, 4)])
def test_closed_annulus_boundary_and_interior_eigenvalues_fail_closed(value: Fraction) -> None:
    result = M.verified_rational_analytic_strip(
        [[value]], center=0, radius=1, spectral_reference_scale=1, expansion_factor=2,
        eigenvectors=[[1]], eigenvalues=[[value]],
    )
    assert result.status == "VERIFIED_CLOSED_ANNULUS_NOT_CLEAR"
    assert result.validation_level is None
    assert result.exact_projection is None


def test_invalid_and_defective_witnesses_fail_closed() -> None:
    invalid = M.verified_rational_analytic_strip(
        [[0]], center=0, radius=1, spectral_reference_scale=1, expansion_factor=2,
        eigenvectors=[[1]], eigenvalues=[[1]],
    )
    assert invalid.status == "INVALID_DIAGONALIZATION_WITNESS"
    defective = M.verified_rational_analytic_strip(
        [[0, 1], [0, 0]], center=0, radius=1, spectral_reference_scale=1, expansion_factor=2,
        eigenvectors=[[1, 0], [0, 1]], eigenvalues=[[0, 0], [0, 0]],
    )
    assert defective.status == "INVALID_DIAGONALIZATION_WITNESS"
    with pytest.raises(ValueError):
        M.verified_rational_analytic_strip(
            [[0]], center=0, radius=1, spectral_reference_scale=1, expansion_factor=1,
            eigenvectors=[[1]], eigenvalues=[[0]],
        )
