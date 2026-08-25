from __future__ import annotations

import importlib.util
from fractions import Fraction as F
from pathlib import Path
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "reality_stone" / "python" / "reality_stone" / "clarus" / "quantitative_coupled_graph_transform.py"


def _load():
    spec = importlib.util.spec_from_file_location("ce_quantitative_coupled_graph", MODULE_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


M = _load()


def _certificate(**overrides):
    values = dict(
        base_dimension=3,
        base_reference_scale=1,
        fiber_reference_scale=1,
        fiber_radius=1,
        forcing_at_zero_upper=F(1, 4),
        base_inverse_lipschitz=1,
        fiber_linear_norm_upper=F(1, 4),
        base_self_lipschitz=F(1, 8),
        fiber_to_base_lipschitz=F(1, 8),
        base_to_fiber_lipschitz=F(1, 8),
        fiber_self_lipschitz=F(1, 4),
        graph_slope_upper=1,
    )
    values.update(overrides)
    return M.quantitative_coupled_graph_transform(**values)


def test_strict_coupled_certificate_exposes_exact_constants_and_margins() -> None:
    result = _certificate()
    assert result.status == "VERIFIED_QUANTITATIVE_COUPLED_GRAPH_TRANSFORM"
    assert result.base_invertibility_lower == F(3, 4)
    assert result.base_fixed_point_factor_upper == F(1, 4)
    assert result.fiber_factor_upper == F(1, 2)
    assert result.tube_margin == F(1, 4)
    assert result.slope_margin == F(1, 8)
    assert result.transform_contraction_factor_upper == F(29, 48)
    assert result.transform_contraction_margin == F(19, 48)
    assert result.graph_real_dimension == 3
    assert result.robust_interior is True


def test_tube_and_slope_boundaries_pass_but_are_not_robust() -> None:
    result = _certificate(forcing_at_zero_upper=F(1, 2), base_to_fiber_lipschitz=F(1, 4))
    assert result.validation_level is not None
    assert result.tube_margin == 0
    assert result.slope_margin == 0
    assert result.robust_interior is False


def test_closed_base_invertibility_boundary_fails_with_named_statuses() -> None:
    result = _certificate(base_self_lipschitz=F(7, 8))
    assert result.base_invertibility_lower == 0
    assert result.status == "COUPLED_BASE_INVERTIBILITY_NOT_STRICT"
    assert "COUPLED_GRAPH_TRANSFORM_CONTRACTION_NOT_STRICT" in result.failure_codes
    assert result.transform_contraction_factor_upper is None


def test_closed_transform_contraction_boundary_fails_even_when_other_gates_pass() -> None:
    result = _certificate(
        forcing_at_zero_upper=F(2, 5),
        fiber_linear_norm_upper=F(7, 20),
        fiber_self_lipschitz=F(1, 4),
        base_self_lipschitz=0,
        fiber_to_base_lipschitz=F(2, 5),
        base_to_fiber_lipschitz=0,
    )
    assert result.base_invertibility_lower == F(3, 5)
    assert result.tube_margin == 0
    assert result.slope_margin == 0
    assert result.transform_contraction_factor_upper == 1
    assert result.failure_codes == ("COUPLED_GRAPH_TRANSFORM_CONTRACTION_NOT_STRICT",)


def test_tube_and_slope_failures_are_independent_and_accumulate() -> None:
    tube = _certificate(forcing_at_zero_upper=F(3, 4))
    assert tube.failure_codes == ("COUPLED_GRAPH_TUBE_NOT_INVARIANT",)
    slope = _certificate(base_to_fiber_lipschitz=F(1, 2))
    assert "COUPLED_GRAPH_SLOPE_NOT_INVARIANT" in slope.failure_codes
    both = _certificate(forcing_at_zero_upper=F(3, 4), base_to_fiber_lipschitz=F(1, 2))
    assert "COUPLED_GRAPH_TUBE_NOT_INVARIANT" in both.failure_codes
    assert "COUPLED_GRAPH_SLOPE_NOT_INVARIANT" in both.failure_codes


def test_zero_base_coupling_recovers_triangular_constants_exactly() -> None:
    result = _certificate(
        base_self_lipschitz=0,
        fiber_to_base_lipschitz=0,
        base_to_fiber_lipschitz=F(1, 4),
    )
    assert result.base_invertibility_lower == 1
    assert result.transform_contraction_factor_upper == result.fiber_factor_upper == F(1, 2)
    assert result.slope_margin == F(1, 4)


def test_independent_base_fiber_unit_rescaling_preserves_normalized_outputs() -> None:
    base = _certificate()
    scaled = _certificate(
        base_reference_scale=5,
        fiber_reference_scale=7,
        fiber_radius=7,
        forcing_at_zero_upper=F(7, 4),
        fiber_to_base_lipschitz=F(5, 56),
        base_to_fiber_lipschitz=F(7, 40),
        graph_slope_upper=F(7, 5),
    )
    assert scaled.status == base.status
    assert scaled.normalized_fiber_radius == base.normalized_fiber_radius
    assert scaled.normalized_forcing_at_zero_upper == base.normalized_forcing_at_zero_upper
    assert scaled.normalized_fiber_to_base_lipschitz == base.normalized_fiber_to_base_lipschitz
    assert scaled.normalized_base_to_fiber_lipschitz == base.normalized_base_to_fiber_lipschitz
    assert scaled.normalized_graph_slope_upper == base.normalized_graph_slope_upper
    assert scaled.transform_contraction_factor_upper == base.transform_contraction_factor_upper


@pytest.mark.parametrize("dimension", [1, 4, 5, 6, 100])
def test_any_positive_dimension_is_preserved_not_selected(dimension: int) -> None:
    result = _certificate(base_dimension=dimension)
    assert result.validation_level is not None
    assert result.graph_real_dimension == dimension


@pytest.mark.parametrize(
    "field,value",
    [
        ("base_dimension", 0),
        ("base_dimension", True),
        ("base_reference_scale", 0),
        ("fiber_reference_scale", -1),
        ("fiber_radius", 0),
        ("base_inverse_lipschitz", 0),
        ("forcing_at_zero_upper", -1),
        ("fiber_linear_norm_upper", -1),
        ("base_self_lipschitz", 0.1),
        ("fiber_to_base_lipschitz", True),
        ("base_to_fiber_lipschitz", "01"),
        ("fiber_self_lipschitz", -1),
        ("graph_slope_upper", -1),
    ],
)
def test_invalid_inputs_fail_closed(field: str, value: object) -> None:
    with pytest.raises(ValueError):
        _certificate(**{field: value})


def test_canonical_rational_strings_are_exact() -> None:
    result = _certificate(
        base_self_lipschitz="1/8",
        fiber_to_base_lipschitz="0.125",
        base_to_fiber_lipschitz="1/8",
    )
    assert result.validation_level is not None
    assert result.transform_contraction_factor_upper == F(29, 48)

