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


TENSOR = _load("physical_tensor_mobility", "physical_tensor_mobility.py")
M = _load("ce_physical_dissipative_skew_mobility", "physical_dissipative_skew_mobility.py")


def _certificate(**overrides):
    values = dict(
        state_reference_scales=(1, 1), energy_reference_scale=1,
        time_reference_scale=1, physical_mobility=((2, -2), (4, 2)),
        dimensionless_gradient=(1, -1), dimensionless_external_forcing=(0, 0),
        coercivity_lower_bound=1, polyak_lojasiewicz_constant=F(1, 2),
    )
    values.update(overrides)
    return M.physical_dissipative_skew_mobility_certificate(**values)


def test_nonsymmetric_mobility_splits_exactly_into_dissipation_and_skew_drift() -> None:
    result = _certificate()
    assert result.validation_level is not None
    assert result.normalized_symmetric_dissipative_part == ((2, 1), (1, 2))
    assert result.normalized_skew_drift_part == ((0, -3), (3, 0))
    assert result.skew_adjoint_exact is True
    assert result.normalized_symmetric_velocity == (-1, 1)
    assert result.normalized_skew_velocity == (-3, -3)
    assert result.normalized_total_velocity == (-4, -2)
    assert result.normalized_symmetric_dissipation == 2
    assert result.normalized_skew_power == 0


def test_coercivity_and_pl_hypothesis_give_exact_unforced_rate() -> None:
    result = _certificate(
        time_reference_scale=5,
        physical_mobility=((F(2, 5), F(-2, 5)), (F(4, 5), F(2, 5))),
    )
    assert result.coercivity_certified is True
    assert result.polyak_lojasiewicz_hypothesis_supplied is True
    assert result.unforced_exponential_potential_rate_normalized == 1
    assert result.unforced_exponential_potential_rate_physical == F(1, 5)
    assert result.robust_interior is False  # the declared lower eigenvalue is contacted exactly


def test_pure_skew_mobility_moves_state_without_changing_model_potential() -> None:
    result = _certificate(
        physical_mobility=((0, -2), (2, 0)),
        coercivity_lower_bound=0, polyak_lojasiewicz_constant=0,
    )
    assert result.validation_level is not None
    assert result.normalized_symmetric_dissipation == 0
    assert result.normalized_skew_power == 0
    assert result.normalized_total_velocity == (-2, -2)
    assert result.nonincreasing_model_potential_certified is True
    assert result.unforced_exponential_potential_rate_normalized is None


def test_zero_skew_reduces_to_the_symmetric_tensor_predecessor() -> None:
    physical = ((2, 1), (1, 2))
    split = _certificate(physical_mobility=physical)
    predecessor = TENSOR.physical_tensor_mobility_certificate(
        state_reference_scales=(1, 1), energy_reference_scale=1,
        time_reference_scale=1, physical_mobility=physical,
        dimensionless_gradient=(1, -1),
    )
    assert split.normalized_skew_drift_part == ((0, 0), (0, 0))
    assert split.normalized_total_velocity == predecessor.normalized_velocity
    assert split.normalized_symmetric_dissipation == predecessor.normalized_dissipation


def test_external_forcing_power_is_separate_and_can_overcome_dissipation() -> None:
    result = _certificate(dimensionless_external_forcing=(2, -2))
    assert result.normalized_external_input_power == 4
    assert result.normalized_net_dissipation_margin == -2
    assert result.nonincreasing_model_potential_certified is False
    assert result.unforced_exponential_potential_rate_normalized is None


def test_external_forcing_orthogonal_to_gradient_does_no_model_potential_work() -> None:
    result = _certificate(dimensionless_external_forcing=(1, 1))
    assert result.normalized_external_input_power == 0
    assert result.normalized_net_dissipation_margin == 2
    assert result.nonincreasing_model_potential_certified is True


def test_indefinite_symmetric_part_fails_even_if_full_matrix_is_nonsymmetric() -> None:
    result = _certificate(
        physical_mobility=((1, 3), (1, 1)), coercivity_lower_bound=0,
    )
    assert result.status == "TENSOR_MOBILITY_NOT_POSITIVE_SEMIDEFINITE"
    assert result.validation_level is None
    assert result.normalized_total_velocity is None


def test_overstated_coercivity_lower_bound_fails_closed() -> None:
    result = _certificate(coercivity_lower_bound=F(11, 10))
    assert "DISSIPATIVE_SKEW_COERCIVITY_LOWER_BOUND_INVALID" in result.failure_codes
    assert result.validation_level is None


def test_strictly_understated_coercivity_is_robust_interior() -> None:
    result = _certificate(coercivity_lower_bound=F(9, 10))
    assert result.validation_level is not None
    assert result.robust_interior is True


def test_mixed_unit_rescaling_preserves_normalized_split_and_dissipation() -> None:
    base = _certificate()
    scales, energy, time = (2, 3), 5, 7
    normalized = base.normalized_mobility
    physical = tuple(
        tuple(normalized[i][j] * scales[i] * scales[j] / (energy * time) for j in range(2))
        for i in range(2)
    )
    scaled = _certificate(
        state_reference_scales=scales, energy_reference_scale=energy,
        time_reference_scale=time, physical_mobility=physical,
    )
    assert scaled.normalized_mobility == base.normalized_mobility
    assert scaled.normalized_symmetric_dissipative_part == base.normalized_symmetric_dissipative_part
    assert scaled.normalized_skew_drift_part == base.normalized_skew_drift_part
    assert scaled.normalized_symmetric_dissipation == base.normalized_symmetric_dissipation
    assert scaled.physical_coordinate_velocities == tuple(
        scales[i] * base.normalized_total_velocity[i] / time for i in range(2)
    )


@pytest.mark.parametrize("dimension", [1, 4, 5, 6])
def test_finite_dimension_is_checked_not_selected(dimension: int) -> None:
    identity = tuple(tuple(1 if i == j else 0 for j in range(dimension)) for i in range(dimension))
    result = M.physical_dissipative_skew_mobility_certificate(
        state_reference_scales=(1,) * dimension, energy_reference_scale=1,
        time_reference_scale=1, physical_mobility=identity,
        dimensionless_gradient=(0,) * dimension,
        dimensionless_external_forcing=(0,) * dimension,
        coercivity_lower_bound=F(1, 2), polyak_lojasiewicz_constant=1,
    )
    assert result.validation_level is not None
    assert result.dimension == dimension
    assert result.infinite_dimensional_form_hypotheses_verified is False


def test_zero_gradient_has_zero_power_even_with_nonzero_forcing() -> None:
    result = _certificate(
        dimensionless_gradient=(0, 0), dimensionless_external_forcing=(9, -7)
    )
    assert result.normalized_symmetric_dissipation == 0
    assert result.normalized_skew_power == 0
    assert result.normalized_external_input_power == 0
    assert result.nonincreasing_model_potential_certified is True


@pytest.mark.parametrize(
    "field,value",
    [
        ("state_reference_scales", ()),
        ("state_reference_scales", (1, 0)),
        ("energy_reference_scale", 0),
        ("time_reference_scale", -1),
        ("physical_mobility", ((1, 0),)),
        ("dimensionless_gradient", (1,)),
        ("dimensionless_external_forcing", (1.0, 0)),
        ("coercivity_lower_bound", -1),
        ("polyak_lojasiewicz_constant", True),
    ],
)
def test_invalid_shapes_scales_and_constants_are_rejected(field, value) -> None:
    with pytest.raises(ValueError):
        _certificate(**{field: value})


def test_canonical_rational_strings_remain_exact() -> None:
    result = _certificate(
        coercivity_lower_bound="1", polyak_lojasiewicz_constant="0.5",
        dimensionless_gradient=("1", "-1"),
    )
    assert result.unforced_exponential_potential_rate_normalized == 1
