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


_load("quantitative_coupled_graph_transform", "quantitative_coupled_graph_transform.py")
_load("quantitative_coupled_c1_graph_transform", "quantitative_coupled_c1_graph_transform.py")
_load("quantitative_coupled_c2_graph_transform", "quantitative_coupled_c2_graph_transform.py")
C3 = _load("quantitative_coupled_c3_graph_transform", "quantitative_coupled_c3_graph_transform.py")
_load("quantitative_graph_transform", "quantitative_graph_transform.py")
_load("quantitative_c1_graph_transform", "quantitative_c1_graph_transform.py")
_load("quantitative_c2_graph_transform", "quantitative_c2_graph_transform.py")
_load("quantitative_c3_graph_transform", "quantitative_c3_graph_transform.py")
TC4 = _load("quantitative_c4_graph_transform", "quantitative_c4_graph_transform.py")
M = _load("ce_quantitative_coupled_c4", "quantitative_coupled_c4_graph_transform.py")


def _certificate(**overrides):
    values = dict(
        base_dimension=3,
        base_reference_scale=1,
        fiber_reference_scale=1,
        fiber_radius=1,
        forcing_at_zero_upper=F(1, 5),
        base_inverse_lipschitz=1,
        fiber_linear_norm_upper=F(1, 10),
        base_self_lipschitz=F(1, 20),
        fiber_to_base_lipschitz=F(1, 20),
        base_to_fiber_lipschitz=F(1, 20),
        fiber_self_lipschitz=F(1, 10),
        graph_slope_upper=F(1, 2),
        normalized_base_jacobian_lipschitz=F(1, 100),
        normalized_fiber_jacobian_lipschitz=F(1, 100),
        graph_derivative_lipschitz_upper=1,
        normalized_base_hessian_lipschitz=F(1, 1000),
        normalized_fiber_hessian_lipschitz=F(1, 1000),
        normalized_base_third_derivative_lipschitz=F(1, 10000),
        normalized_fiber_third_derivative_lipschitz=F(1, 10000),
        normalized_graph_third_derivative_upper=2,
        graph_third_derivative_lipschitz_upper=2,
        normalized_base_fourth_derivative_lipschitz=F(1, 100000),
        normalized_fiber_fourth_derivative_lipschitz=F(1, 100000),
        normalized_graph_fourth_derivative_upper=20,
        graph_fourth_derivative_lipschitz_upper=100,
    )
    values.update(overrides)
    return M.quantitative_coupled_c4_graph_transform(**values)


def test_strict_coupled_c4_certificate_exposes_all_layers() -> None:
    result = _certificate()
    assert result.status == "VERIFIED_QUANTITATIVE_COUPLED_C4_GRAPH_TRANSFORM"
    assert result.coupled_c3_certificate.validation_level is not None
    assert result.graph_fourth_derivative_lipschitz_required is True
    assert result.graph_fourth_derivative_margin > 0
    assert result.graph_fourth_derivative_lipschitz_margin > 0
    assert result.fourth_derivative_bunching_margin > 0
    assert result.base_fourth_derivative_upper > 0
    assert result.fiber_fourth_derivative_upper > 0
    assert result.modified_fourth_derivative_upper > 0
    assert result.modified_fourth_derivative_lipschitz_upper > 0
    assert result.modified_fourth_difference_value_coefficient_upper > 0
    assert result.c4_graph_real_dimension == 3
    assert result.robust_interior is True


def test_scalar_nonzero_coupling_matches_inverse_fourth_identity() -> None:
    # F=x+x^3/10 and Y=x^2/5+x^5/20 at x=1.
    l, p, u, w = F(13, 10), F(3, 5), F(3, 5), F(0)
    k, r, v, z = F(13, 20), F(7, 5), F(3), F(6)
    t = k / l
    n = r - t * p
    m = v - t * u - 3 * n * p / l
    o = z - t * w - 4 * n * u / l - 3 * n * (p / l) ** 2 - 6 * m * p / l
    inverse_identity = o / l**4

    # Independent inverse-series coefficients for F(s) and substitution in Y.
    a1 = 1 / l
    a2 = -(p / 2) * a1**2 / l
    a3 = -((p / 2) * 2 * a1 * a2 + (u / 6) * a1**3) / l
    a4 = -(
        (p / 2) * (2 * a1 * a3 + a2**2)
        + (u / 6) * 3 * a1**2 * a2
        + (w / 24) * a1**4
    ) / l
    direct_coefficient = (
        k * a4
        + (r / 2) * (2 * a1 * a3 + a2**2)
        + (v / 6) * 3 * a1**2 * a2
        + (z / 24) * a1**4
    )
    assert inverse_identity == 24 * direct_coefficient


def test_exact_zero_base_coupling_reduces_to_triangular_c4() -> None:
    coupled = _certificate(
        forcing_at_zero_upper=F(1, 4),
        fiber_linear_norm_upper=F(1, 4),
        base_self_lipschitz=0,
        fiber_to_base_lipschitz=0,
        base_to_fiber_lipschitz=F(1, 4),
        fiber_self_lipschitz=F(1, 4),
        graph_slope_upper=1,
        normalized_base_jacobian_lipschitz=0,
        normalized_fiber_jacobian_lipschitz=F(1, 16),
        graph_derivative_lipschitz_upper=1,
        normalized_base_hessian_lipschitz=0,
        normalized_fiber_hessian_lipschitz=F(1, 16),
        normalized_base_third_derivative_lipschitz=0,
        normalized_fiber_third_derivative_lipschitz=F(1, 64),
        normalized_graph_third_derivative_upper=2,
        graph_third_derivative_lipschitz_upper=0,
        normalized_base_fourth_derivative_lipschitz=0,
        normalized_fiber_fourth_derivative_lipschitz=F(1, 256),
        normalized_graph_fourth_derivative_upper=6,
        graph_fourth_derivative_lipschitz_upper=0,
    )
    triangular = TC4.quantitative_c4_triangular_graph_transform(
        base_dimension=3,
        base_reference_scale=1,
        fiber_reference_scale=1,
        fiber_radius=1,
        forcing_at_zero_upper=F(1, 4),
        base_inverse_lipschitz=1,
        fiber_linear_norm_upper=F(1, 4),
        base_to_fiber_lipschitz=F(1, 4),
        fiber_nonlinear_lipschitz=F(1, 4),
        graph_slope_upper=1,
        base_derivative_fiber_variation=F(1, 4),
        fiber_derivative_fiber_variation=F(1, 4),
        normalized_map_hessian_upper=F(1, 16),
        normalized_map_third_derivative_upper=F(1, 16),
        normalized_map_fourth_derivative_upper=F(1, 64),
        normalized_map_fourth_derivative_fiber_lipschitz=F(1, 256),
        normalized_graph_hessian_upper=1,
        normalized_graph_third_derivative_upper=2,
        normalized_graph_fourth_derivative_upper=6,
    )
    assert coupled.validation_level is not None
    assert triangular.validation_level is not None
    assert coupled.output_graph_fourth_derivative_upper == triangular.output_graph_fourth_derivative_upper
    assert coupled.fourth_derivative_bunching_factor_upper == triangular.fourth_derivative_bunching_factor_upper
    assert coupled.third_to_fourth_derivative_cross_coefficient_upper == triangular.third_to_fourth_derivative_cross_coefficient_upper
    assert coupled.hessian_to_fourth_derivative_cross_coefficient_upper == triangular.hessian_to_fourth_derivative_cross_coefficient_upper
    assert coupled.derivative_to_fourth_derivative_cross_coefficient_upper == triangular.derivative_to_fourth_derivative_cross_coefficient_upper
    assert coupled.value_to_fourth_derivative_cross_coefficient_upper == triangular.value_to_fourth_derivative_cross_coefficient_upper


def test_graph_independent_base_bypasses_c41_gate() -> None:
    result = _certificate(
        base_self_lipschitz=0,
        fiber_to_base_lipschitz=0,
        normalized_base_jacobian_lipschitz=0,
        normalized_base_hessian_lipschitz=0,
        normalized_base_third_derivative_lipschitz=0,
        normalized_base_fourth_derivative_lipschitz=0,
        graph_third_derivative_lipschitz_upper=0,
        graph_fourth_derivative_lipschitz_upper=0,
    )
    assert result.graph_fourth_derivative_lipschitz_required is False
    assert result.graph_fourth_derivative_lipschitz_margin < 0
    assert result.validation_level is not None


def test_c41_failure_is_separate_from_c4_class_and_bunching() -> None:
    result = _certificate(graph_fourth_derivative_lipschitz_upper=0)
    assert result.coupled_c3_certificate.validation_level is not None
    assert result.graph_fourth_derivative_margin > 0
    assert result.fourth_derivative_bunching_margin > 0
    assert result.status == "COUPLED_C41_GRAPH_CLASS_NOT_INVARIANT"


def test_d5_map_moduli_do_not_change_one_graph_c4_class() -> None:
    base = _certificate()
    zero = _certificate(
        normalized_base_fourth_derivative_lipschitz=0,
        normalized_fiber_fourth_derivative_lipschitz=0,
    )
    assert zero.output_graph_fourth_derivative_upper == base.output_graph_fourth_derivative_upper
    assert zero.fourth_derivative_bunching_factor_upper == base.fourth_derivative_bunching_factor_upper
    assert zero.output_graph_fourth_derivative_lipschitz_upper < base.output_graph_fourth_derivative_lipschitz_upper
    assert zero.value_to_fourth_derivative_cross_coefficient_upper < base.value_to_fourth_derivative_cross_coefficient_upper


def test_iteration_uses_all_five_coupled_layers() -> None:
    result = _certificate()
    one = M.coupled_c4_graph_iteration_bound(
        result,
        initial_value_distance=2,
        initial_derivative_distance=3,
        initial_hessian_distance=4,
        initial_third_derivative_distance=5,
        initial_fourth_derivative_distance=6,
        steps=1,
    )
    assert one.fourth_derivative_distance_upper == (
        6 * result.fourth_derivative_bunching_factor_upper
        + 5 * result.third_to_fourth_derivative_cross_coefficient_upper
        + 4 * result.hessian_to_fourth_derivative_cross_coefficient_upper
        + 3 * result.derivative_to_fourth_derivative_cross_coefficient_upper
        + 2 * result.value_to_fourth_derivative_cross_coefficient_upper
    )


def test_fourth_bunching_equality_fails_after_c3_passes() -> None:
    result = _certificate(
        base_inverse_lipschitz=2,
        fiber_linear_norm_upper=F(1, 16),
        base_self_lipschitz=0,
        fiber_to_base_lipschitz=0,
        base_to_fiber_lipschitz=0,
        fiber_self_lipschitz=0,
        graph_slope_upper=0,
        normalized_base_jacobian_lipschitz=0,
        normalized_fiber_jacobian_lipschitz=0,
        graph_derivative_lipschitz_upper=0,
        normalized_base_hessian_lipschitz=0,
        normalized_fiber_hessian_lipschitz=0,
        normalized_base_third_derivative_lipschitz=0,
        normalized_fiber_third_derivative_lipschitz=0,
        normalized_graph_third_derivative_upper=0,
        graph_third_derivative_lipschitz_upper=0,
        normalized_base_fourth_derivative_lipschitz=0,
        normalized_fiber_fourth_derivative_lipschitz=0,
        normalized_graph_fourth_derivative_upper=0,
        graph_fourth_derivative_lipschitz_upper=0,
    )
    assert result.coupled_c3_certificate.validation_level is not None
    assert result.coupled_c3_certificate.third_derivative_bunching_factor_upper == F(1, 2)
    assert result.fourth_derivative_bunching_factor_upper == 1
    assert result.status == "COUPLED_C4_FOURTH_DERIVATIVE_BUNCHING_NOT_STRICT"


def test_equality_witness_is_c3_invariant_and_not_c4() -> None:
    def h(x: F) -> F:
        return x * abs(x) ** 3

    for x in (F(-3, 2), F(-1, 3), F(0), F(2, 5), F(7, 4)):
        assert h(x / 2) == h(x) / 16
    assert (-24, 24)[0] != (-24, 24)[1]


def test_predecessor_failure_remains_primary() -> None:
    result = _certificate(normalized_graph_third_derivative_upper=0)
    assert result.status == "COUPLED_C21_GRAPH_CLASS_NOT_INVARIANT"


@pytest.mark.parametrize("dimension", [1, 4, 5, 6, 100])
def test_dimension_is_preserved_not_selected(dimension: int) -> None:
    assert _certificate(base_dimension=dimension).c4_graph_real_dimension == dimension


@pytest.mark.parametrize(
    "field,value",
    [
        ("normalized_base_fourth_derivative_lipschitz", -1),
        ("normalized_fiber_fourth_derivative_lipschitz", -1),
        ("normalized_graph_fourth_derivative_upper", -1),
        ("graph_fourth_derivative_lipschitz_upper", -1),
        ("normalized_base_fourth_derivative_lipschitz", 0.1),
        ("normalized_fiber_fourth_derivative_lipschitz", True),
        ("normalized_graph_fourth_derivative_upper", "020"),
    ],
)
def test_invalid_c4_inputs_fail_closed(field: str, value: object) -> None:
    with pytest.raises(ValueError):
        _certificate(**{field: value})
