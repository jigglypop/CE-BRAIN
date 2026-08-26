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
M = _load("ce_continuous_algebraic_optimization", "verified_continuous_algebraic_circle_margin_optimization.py")


def _optimize(matrix=((0, 1, 0), (0, 0, 0), (0, 0, 5)), **overrides):
    values = dict(
        nominal_transition=matrix,
        reference_center=0,
        reference_radius=2,
        center_real_interval=(F(-1, 4), F(1, 4)),
        center_imag_interval=(F(-1, 4), F(1, 4)),
        radius_interval=(F(3, 2), F(5, 2)),
        spectral_reference_scale=1,
        normalized_optimality_tolerance=F(1, 10),
        maximum_cells=4096,
        maximum_partitions=1024,
        maximum_factor_candidate_value_tuples=1_000_000,
        sqrt_precision=48,
    )
    values.update(overrides)
    return M.verified_continuous_algebraic_circle_margin_optimization(**values)


def test_defective_matrix_optimizes_without_diagonalization() -> None:
    result = _optimize()
    assert result.validation_level == "VERIFIED_CONTINUOUS_ALGEBRAIC_CIRCLE_MARGIN_OPTIMUM"
    assert not result.diagonalization_witness_required
    assert result.reference_projector_rank == 2
    assert result.selected_projector_rank == 2
    assert result.projector_identity_preserved
    assert result.epsilon_global_optimality_verified
    assert result.certified_optimality_gap <= F(1, 10)


def test_positive_margin_implies_both_frobenius_gates() -> None:
    result = _optimize()
    assert result.selected_algebraic_margin > 0
    selected = max(
        result.terminal_cells,
        key=lambda cell: cell.midpoint_algebraic_margin,
    )
    assert selected.midpoint_radius ** 2 > selected.inside_frobenius_squared
    assert selected.midpoint_radius ** 2 * selected.exterior_inverse_frobenius_squared < 1


def test_irreducible_quadratic_inside_block_needs_no_eigenvectors() -> None:
    matrix = ((0, 2, 0), (1, 0, 0), (0, 0, 5))
    result = _optimize(
        matrix,
        reference_radius=3,
        radius_interval=(F(5, 2), F(7, 2)),
    )
    assert result.validation_level is not None
    assert result.reference_projector_rank == 2


def test_degenerate_box_has_exact_zero_global_gap() -> None:
    result = _optimize(
        center_real_interval=(0, 0),
        center_imag_interval=(0, 0),
        radius_interval=(2, 2),
        normalized_optimality_tolerance=0,
        maximum_cells=1,
    )
    assert result.validation_level is not None
    assert result.certified_optimality_gap == 0


def test_raw_scale_covariance_preserves_normalized_receipt() -> None:
    base = _optimize()
    scaled = _optimize(
        ((0, 7, 0), (0, 0, 0), (0, 0, 35)),
        reference_radius=14,
        center_real_interval=(F(-7, 4), F(7, 4)),
        center_imag_interval=(F(-7, 4), F(7, 4)),
        radius_interval=(F(21, 2), F(35, 2)),
        spectral_reference_scale=7,
    )
    assert scaled.selected_normalized_center == base.selected_normalized_center
    assert scaled.selected_normalized_radius == base.selected_normalized_radius
    assert scaled.selected_algebraic_margin == base.selected_algebraic_margin
    assert scaled.certified_optimality_gap == base.certified_optimality_gap


def test_reference_failure_yields_no_cells_or_selection() -> None:
    result = _optimize(((2,),), reference_radius=2)
    assert result.status == "ALGEBRAIC_CONTINUOUS_REFERENCE_DISCOVERY_UNAVAILABLE"
    assert result.cells_evaluated == 0
    assert result.selected_discovery is None


def test_nonuniform_exterior_center_domain_fails_before_branching() -> None:
    result = _optimize(
        center_real_interval=(-6, 6),
        center_imag_interval=(-6, 6),
        radius_interval=(1, 3),
    )
    assert result.status == "ALGEBRAIC_CONTINUOUS_EXTERIOR_CENTER_DOMAIN_NOT_UNIFORM"
    assert not result.uniform_exterior_center_domain_verified
    assert result.cells_evaluated == 0


def test_cell_budget_exhaustion_fails_closed() -> None:
    result = _optimize(normalized_optimality_tolerance=0, maximum_cells=1)
    assert result.status == "ALGEBRAIC_CONTINUOUS_OPTIMIZATION_CELL_BUDGET_EXCEEDED"
    assert result.validation_level is None


def test_radius_box_with_no_positive_algebraic_margin_is_refused() -> None:
    result = _optimize(
        center_real_interval=(0, 0),
        center_imag_interval=(0, 0),
        radius_interval=(F(1, 2), F(1, 2)),
        normalized_optimality_tolerance=0,
        maximum_cells=1,
    )
    assert result.status == "ALGEBRAIC_CONTINUOUS_NO_POSITIVE_MARGIN"


@pytest.mark.parametrize(
    "overrides",
    [
        {"reference_center": 2},
        {"center_real_interval": (1, -1)},
        {"radius_interval": (0, 1)},
        {"normalized_optimality_tolerance": -1},
        {"maximum_cells": True},
    ],
)
def test_parameter_contracts_are_strict(overrides) -> None:
    with pytest.raises(ValueError):
        _optimize(**overrides)


def test_empirical_provenance_remains_false() -> None:
    result = _optimize()
    assert not result.empirical_matrix_provenance_verified
