from __future__ import annotations

import importlib.util
from fractions import Fraction as F
from pathlib import Path
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "reality_stone" / "python" / "reality_stone" / "clarus" / "physical_tensor_mobility.py"


def _load():
    spec = importlib.util.spec_from_file_location("ce_physical_tensor_mobility", MODULE_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


M = _load()


def test_scalar_case_recovers_unit_normalized_mobility() -> None:
    result = M.physical_tensor_mobility_certificate(
        state_reference_scales=[2], energy_reference_scale=3,
        time_reference_scale=5, physical_mobility=[[F(4, 15)]],
        dimensionless_gradient=[3],
    )
    assert result.validation_level is not None
    assert result.normalized_mobility == ((1,),)
    assert result.normalized_velocity == (-3,)
    assert result.physical_coordinate_velocities == (F(-6, 5),)
    assert result.normalized_dissipation == 9
    assert result.physical_model_potential_dissipation == F(27, 5)


def test_heterogeneous_coupled_tensor_velocity_and_dissipation_are_exact() -> None:
    scales = [2, 3]
    energy, time = 5, 7
    normalized = [[2, 1], [1, 2]]
    physical = [
        [F(normalized[i][j] * scales[i] * scales[j], energy * time) for j in range(2)]
        for i in range(2)
    ]
    result = M.physical_tensor_mobility_certificate(
        state_reference_scales=scales, energy_reference_scale=energy,
        time_reference_scale=time, physical_mobility=physical,
        dimensionless_gradient=[1, -1],
    )
    assert result.normalized_mobility == ((2, 1), (1, 2))
    assert result.positive_semidefinite is True
    assert result.positive_definite is True
    assert result.normalized_velocity == (-1, 1)
    assert result.physical_coordinate_velocities == (F(-2, 7), F(3, 7))
    assert result.normalized_dissipation == 2
    assert result.physical_model_potential_dissipation == F(10, 7)


def test_singular_psd_tensor_allows_nonzero_zero_dissipation_direction() -> None:
    result = M.physical_tensor_mobility_certificate(
        state_reference_scales=[1, 1], energy_reference_scale=1,
        time_reference_scale=1, physical_mobility=[[1, 1], [1, 1]],
        dimensionless_gradient=[1, -1],
    )
    assert result.validation_level is not None
    assert result.positive_semidefinite is True
    assert result.positive_definite is False
    assert result.normalized_velocity == (0, 0)
    assert result.normalized_dissipation == 0
    assert any(minor.determinant == 0 for minor in result.principal_minors)


def test_indefinite_symmetric_tensor_fails_with_exact_negative_minor() -> None:
    result = M.physical_tensor_mobility_certificate(
        state_reference_scales=[1, 1], energy_reference_scale=1,
        time_reference_scale=1, physical_mobility=[[1, 2], [2, 1]],
        dimensionless_gradient=[1, -1],
    )
    assert result.status == "TENSOR_MOBILITY_NOT_POSITIVE_SEMIDEFINITE"
    assert result.validation_level is None
    assert result.first_negative_principal_minor is not None
    assert result.first_negative_principal_minor.indices == (1, 2)
    assert result.first_negative_principal_minor.determinant == -3
    assert result.normalized_dissipation is None


def test_nonsymmetric_tensor_fails_without_silent_symmetrization() -> None:
    result = M.physical_tensor_mobility_certificate(
        state_reference_scales=[1, 1], energy_reference_scale=1,
        time_reference_scale=1, physical_mobility=[[1, 1], [0, 1]],
        dimensionless_gradient=[1, 1],
    )
    assert result.status == "TENSOR_MOBILITY_NOT_SYMMETRIC"
    assert result.principal_minors == ()
    assert result.normalized_velocity is None


def test_zero_gradient_has_zero_velocity_and_dissipation() -> None:
    result = M.physical_tensor_mobility_certificate(
        state_reference_scales=[2, 3], energy_reference_scale=5,
        time_reference_scale=7, physical_mobility=[[1, 0], [0, 1]],
        dimensionless_gradient=[0, 0],
    )
    assert result.validation_level is not None
    assert result.normalized_velocity == (0, 0)
    assert result.physical_model_potential_dissipation == 0


def test_consistent_coordinate_energy_time_rescaling_preserves_normalized_tensor() -> None:
    base = M.physical_tensor_mobility_certificate(
        state_reference_scales=[2, 3], energy_reference_scale=5,
        time_reference_scale=7,
        physical_mobility=[[F(8, 35), F(6, 35)], [F(6, 35), F(18, 35)]],
        dimensionless_gradient=[1, -1],
    )
    new_scales, new_energy, new_time = [10, 21], 15, 35
    normalized = base.normalized_mobility
    physical = [
        [normalized[i][j] * new_scales[i] * new_scales[j] / (new_energy * new_time) for j in range(2)]
        for i in range(2)
    ]
    scaled = M.physical_tensor_mobility_certificate(
        state_reference_scales=new_scales, energy_reference_scale=new_energy,
        time_reference_scale=new_time, physical_mobility=physical,
        dimensionless_gradient=[1, -1],
    )
    assert scaled.normalized_mobility == base.normalized_mobility
    assert scaled.normalized_velocity == base.normalized_velocity
    assert scaled.normalized_dissipation == base.normalized_dissipation


@pytest.mark.parametrize("dimension", [1, 4, 5, 6])
def test_any_declared_finite_dimension_is_checked_not_selected(dimension: int) -> None:
    identity = [[1 if i == j else 0 for j in range(dimension)] for i in range(dimension)]
    result = M.physical_tensor_mobility_certificate(
        state_reference_scales=[1] * dimension, energy_reference_scale=1,
        time_reference_scale=1, physical_mobility=identity,
        dimensionless_gradient=[0] * dimension,
    )
    assert result.validation_level is not None
    assert result.dimension == dimension
    assert result.positive_definite is True


@pytest.mark.parametrize(
    "field,value",
    [
        ("state_reference_scales", []),
        ("state_reference_scales", [1, 0]),
        ("state_reference_scales", [1.0]),
        ("energy_reference_scale", 0),
        ("time_reference_scale", -1),
        ("physical_mobility", [[1, 0]]),
        ("physical_mobility", [[True]]),
        ("dimensionless_gradient", [1, 2]),
        ("dimensionless_gradient", [1.0]),
    ],
)
def test_invalid_shapes_scales_and_exactness_fail_closed(field: str, value: object) -> None:
    values = dict(
        state_reference_scales=[1], energy_reference_scale=1,
        time_reference_scale=1, physical_mobility=[[1]],
        dimensionless_gradient=[1],
    )
    values[field] = value
    with pytest.raises(ValueError):
        M.physical_tensor_mobility_certificate(**values)


def test_canonical_rational_strings_are_exact() -> None:
    result = M.physical_tensor_mobility_certificate(
        state_reference_scales=["2"], energy_reference_scale="3",
        time_reference_scale="5", physical_mobility=[["4/15"]],
        dimensionless_gradient=["0.5"],
    )
    assert result.validation_level is not None
    assert result.normalized_mobility == ((1,),)
    assert result.normalized_dissipation == F(1, 4)

