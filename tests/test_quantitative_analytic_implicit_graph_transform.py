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


_load("quantitative_graph_transform", "quantitative_graph_transform.py")
M = _load(
    "ce_quantitative_analytic_implicit_graph_transform",
    "quantitative_analytic_implicit_graph_transform.py",
)


def _certificate(**overrides):
    values = dict(
        base_dimension=5,
        maximum_reported_derivative_order=6,
        base_linear_conorm_lower=1,
        complex_input_radius=F(1, 4),
        base_nonlinear_derivative_amplitude=F(1, 10),
        base_nonlinear_derivative_rate=1,
        requested_complex_output_radius=F(1, 5),
        fiber_value_at_center_upper=0,
        fiber_derivative_amplitude=F(1, 10),
        fiber_derivative_rate=1,
        analytic_graph_sup_upper=F(1, 20),
        complex_c0_contraction_factor_upper=F(1, 2),
    )
    values.update(overrides)
    return M.quantitative_analytic_implicit_graph_transform(**values)


def test_exact_geometric_majorant_sums_and_inverse_radius() -> None:
    result = _certificate()
    assert result.base_majorant_argument == F(1, 4)
    assert result.base_majorant_convergence_margin == F(3, 4)
    assert result.nonlinear_displacement_upper == F(1, 120)
    assert result.nonlinear_derivative_upper == F(7, 90)
    assert result.inverse_contraction_factor_upper == F(7, 90)
    assert result.inverse_contraction_margin == F(83, 90)
    assert result.available_complex_output_radius_lower == F(29, 120)
    assert result.output_radius_margin == F(1, 24)


def test_fiber_sup_class_and_safe_frechet_cauchy_bounds_are_exact() -> None:
    result = _certificate()
    assert result.transformed_graph_sup_upper == F(1, 30)
    assert result.analytic_graph_class_margin == F(1, 60)
    assert result.analytic_factorial_rate_upper == 15
    assert result.frechet_derivative_bounds_upper[:4] == (
        F(1, 2), F(15), F(675), F(40500)
    )


def test_verified_analytic_fixed_point_implies_c_infinity_and_all_gevrey_s_at_least_one() -> None:
    result = _certificate()
    assert result.status == "VERIFIED_CONDITIONAL_ANALYTIC_IMPLICIT_GRAPH_TRANSFORM_FIXED_POINT"
    assert result.robust_interior is True
    assert result.analytic_fixed_point_certified is True
    assert result.c_infinity_certified is True
    assert result.gevrey_s_for_every_real_s_at_least_one_certified is True


def test_integer_gevrey_weakening_keeps_amplitude_and_rate() -> None:
    analytic = _certificate()
    g1 = M.integer_gevrey_envelope_from_analytic_certificate(analytic, gevrey_order=1)
    g2 = M.integer_gevrey_envelope_from_analytic_certificate(analytic, gevrey_order=2)
    assert g1.derivative_bounds_upper == analytic.frechet_derivative_bounds_upper
    assert g2.amplitude_upper == g1.amplitude_upper == F(1, 30)
    assert g2.rate_upper == g1.rate_upper == 15
    assert all(b2 >= b1 for b1, b2 in zip(g1.derivative_bounds_upper, g2.derivative_bounds_upper))


def test_complex_c0_iteration_has_exact_geometric_rate() -> None:
    result = M.analytic_fixed_point_iteration_bound(
        _certificate(), initial_sup_distance=3, steps=5
    )
    assert result.sup_distance_upper == F(3, 32)


@pytest.mark.parametrize(
    "overrides,code",
    [
        ({"complex_input_radius": 1}, "ANALYTIC_BASE_MAJORANT_RADIUS_NOT_STRICT"),
        ({"fiber_derivative_rate": 4}, "ANALYTIC_FIBER_MAJORANT_RADIUS_NOT_STRICT"),
        ({"complex_c0_contraction_factor_upper": 1}, "ANALYTIC_COMPLEX_C0_CONTRACTION_NOT_STRICT"),
        ({"base_nonlinear_derivative_amplitude": F(9, 7)}, "ANALYTIC_NONLINEAR_INVERSE_CONTRACTION_NOT_STRICT"),
        ({"requested_complex_output_radius": F(29, 120)}, "ANALYTIC_REQUESTED_OUTPUT_RADIUS_NOT_STRICTLY_COVERED"),
        ({"analytic_graph_sup_upper": F(1, 40)}, "ANALYTIC_GRAPH_SUP_CLASS_NOT_INVARIANT"),
    ],
)
def test_all_strict_analytic_boundaries_fail_closed(overrides: dict[str, object], code: str) -> None:
    assert _certificate(**overrides).status == code


def test_graph_sup_equality_passes_but_is_not_robust_interior() -> None:
    result = _certificate(analytic_graph_sup_upper=F(1, 30))
    assert result.validation_level is not None
    assert result.analytic_graph_class_margin == 0
    assert result.robust_interior is False


@pytest.mark.parametrize("dimension", [1, 4, 5, 6, 100])
def test_dimension_is_preserved_not_selected(dimension: int) -> None:
    assert _certificate(base_dimension=dimension).analytic_graph_real_dimension == dimension


@pytest.mark.parametrize(
    "field,value",
    [
        ("base_dimension", 0),
        ("base_dimension", True),
        ("maximum_reported_derivative_order", 0),
        ("base_linear_conorm_lower", 0),
        ("complex_input_radius", 1.0),
        ("requested_complex_output_radius", -1),
        ("fiber_derivative_amplitude", True),
        ("analytic_graph_sup_upper", -1),
    ],
)
def test_invalid_inputs_fail_closed(field: str, value: object) -> None:
    with pytest.raises(ValueError):
        _certificate(**{field: value})


def test_failed_certificate_cannot_be_used_for_gevrey_or_iteration() -> None:
    failed = _certificate(complex_c0_contraction_factor_upper=1)
    with pytest.raises(ValueError):
        M.integer_gevrey_envelope_from_analytic_certificate(failed, gevrey_order=1)
    with pytest.raises(ValueError):
        M.analytic_fixed_point_iteration_bound(failed, initial_sup_distance=1, steps=1)


def test_claim_scope_requires_complex_not_merely_real_majorants() -> None:
    assert "UNIFORM_HOLOMORPHIC_MAJORANTS" in _certificate().claim_scope
    assert "COMPLEX_C0_CONTRACTION" in _certificate().claim_scope
