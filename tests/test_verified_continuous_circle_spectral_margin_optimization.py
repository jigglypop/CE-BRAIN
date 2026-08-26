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


_load("verified_rational_contour", "verified_rational_contour.py")
_load("verified_interval_contour", "verified_interval_contour.py")
_load("verified_interval_tightening", "verified_interval_tightening.py")
_load("verified_interval_residual", "verified_interval_residual.py")
_load("verified_algebraic_riesz_projector", "verified_algebraic_riesz_projector.py")
_load("verified_polynomial_spectral_projector_construction", "verified_polynomial_spectral_projector_construction.py")
_load("verified_complete_q_polynomial_factorization", "verified_complete_q_polynomial_factorization.py")
_load("verified_characteristic_spectral_split_discovery", "verified_characteristic_spectral_split_discovery.py")
M = _load("ce_continuous_circle_optimization", "verified_continuous_circle_spectral_margin_optimization.py")


def _optimize(**overrides):
    values = dict(
        nominal_transition=((0, 0), (0, 4)),
        eigenvectors=((1, 0), (0, 1)),
        eigenvalues=(0, 4),
        target_inside_labels=(True, False),
        center_real_interval=(-1, 1),
        center_imag_interval=(-1, 1),
        radius_interval=(1, 3),
        spectral_reference_scale=1,
        normalized_optimality_tolerance=F(1, 10),
        maximum_cells=4096,
        maximum_partitions=1024,
        maximum_factor_candidate_value_tuples=1_000_000,
        sqrt_precision=48,
    )
    values.update(overrides)
    return M.verified_continuous_circle_spectral_margin_optimization(**values)


def test_continuous_box_is_covered_with_epsilon_global_optimum_and_rank() -> None:
    result = _optimize()
    assert result.validation_level == "VERIFIED_CONTINUOUS_CIRCLE_SPECTRAL_MARGIN_OPTIMUM"
    assert result.epsilon_global_optimality_verified
    assert result.certified_optimality_gap is not None
    assert result.certified_optimality_gap <= F(1, 10)
    assert result.selected_projector_rank == 1
    assert result.rank_consistency_verified
    assert result.continuous_parameter_box_covered
    assert not result.finite_grid_only


def test_degenerate_parameter_box_is_an_exact_global_optimization() -> None:
    result = _optimize(
        center_real_interval=(0, 0),
        center_imag_interval=(0, 0),
        radius_interval=(2, 2),
        normalized_optimality_tolerance=0,
        maximum_cells=1,
    )
    assert result.validation_level is not None
    assert result.cells_evaluated == 1
    assert result.certified_optimality_gap == 0
    assert result.selected_signed_squared_margin == 4


def test_selected_margin_is_positive_for_every_target_label() -> None:
    result = _optimize()
    assert result.selected_normalized_center is not None
    assert result.selected_normalized_radius is not None
    center = result.selected_normalized_center
    radius = result.selected_normalized_radius
    for value, inside in zip(result.normalized_eigenvalues, result.target_inside_labels, strict=True):
        distance_squared = (value - center).abs_squared()
        signed = radius * radius - distance_squared if inside else distance_squared - radius * radius
        assert signed >= result.selected_signed_squared_margin > 0


def test_raw_unit_scaling_preserves_normalized_optimum_receipt() -> None:
    base = _optimize()
    scaled = _optimize(
        nominal_transition=((0, 0), (0, 28)),
        eigenvalues=(0, 28),
        center_real_interval=(-7, 7),
        center_imag_interval=(-7, 7),
        radius_interval=(7, 21),
        spectral_reference_scale=7,
    )
    assert scaled.selected_normalized_center == base.selected_normalized_center
    assert scaled.selected_normalized_radius == base.selected_normalized_radius
    assert scaled.selected_signed_squared_margin == base.selected_signed_squared_margin
    assert scaled.certified_optimality_gap == base.certified_optimality_gap


def test_gaussian_rational_nonreal_centers_are_allowed_in_continuous_box() -> None:
    result = _optimize(
        nominal_transition=(((0, 1), 0), (0, (0, 5))),
        eigenvalues=((0, 1), (0, 5)),
        center_real_interval=(-1, 1),
        center_imag_interval=(1, 3),
        radius_interval=(1, 3),
    )
    assert result.validation_level is not None
    assert result.selected_projector_rank == 1
    assert result.selected_characteristic_discovery is not None
    assert result.selected_characteristic_discovery.center_shift_to_zero_verified


def test_invalid_diagonalization_witness_fails_without_global_claim() -> None:
    result = _optimize(eigenvectors=((1, 1), (0, 1)))
    assert result.validation_level is None
    assert "CONTINUOUS_CIRCLE_EXACT_DIAGONALIZATION_WITNESS_FAILED" in result.failure_codes
    assert not result.epsilon_global_optimality_verified


def test_cell_budget_exhaustion_fails_closed() -> None:
    result = _optimize(normalized_optimality_tolerance=0, maximum_cells=1)
    assert result.status == "CONTINUOUS_CIRCLE_OPTIMIZATION_CELL_BUDGET_EXCEEDED"
    assert result.validation_level is None
    assert not result.continuous_parameter_box_covered


def test_impossible_target_labels_have_no_positive_margin() -> None:
    result = _optimize(
        nominal_transition=((0, 0), (0, 0)),
        eigenvalues=(0, 0),
        target_inside_labels=(True, False),
        center_real_interval=(0, 0),
        center_imag_interval=(0, 0),
        radius_interval=(1, 1),
        normalized_optimality_tolerance=0,
        maximum_cells=1,
    )
    assert result.status == "CONTINUOUS_CIRCLE_NO_POSITIVE_TARGET_MARGIN"
    assert result.selected_projector_rank is None


def test_rank_zero_and_full_targets_are_supported() -> None:
    zero = _optimize(
        target_inside_labels=(False, False),
        center_real_interval=(2, 2),
        center_imag_interval=(0, 0),
        radius_interval=(F(1, 2), F(1, 2)),
        normalized_optimality_tolerance=0,
        maximum_cells=1,
    )
    assert zero.validation_level is not None
    assert zero.selected_projector_rank == 0
    full = _optimize(
        target_inside_labels=(True, True),
        center_real_interval=(2, 2),
        center_imag_interval=(0, 0),
        radius_interval=(3, 3),
        normalized_optimality_tolerance=0,
        maximum_cells=1,
    )
    assert full.validation_level is not None
    assert full.selected_projector_rank == 2


@pytest.mark.parametrize(
    "overrides",
    [
        {"target_inside_labels": (1, False)},
        {"center_real_interval": (1, -1)},
        {"radius_interval": (0, 1)},
        {"normalized_optimality_tolerance": -1},
        {"maximum_cells": True},
    ],
)
def test_parameter_and_label_contracts_are_strict(overrides) -> None:
    with pytest.raises(ValueError):
        _optimize(**overrides)


def test_empirical_provenance_remains_false() -> None:
    result = _optimize()
    assert not result.empirical_matrix_provenance_verified
