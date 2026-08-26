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
M = _load("ce_interval_characteristic_split", "verified_interval_characteristic_spectral_split.py")


def _zero_radii(n):
    return tuple(tuple((0, 0) for _ in range(n)) for _ in range(n))


def _split(matrix=((0, 0), (0, 10)), **overrides):
    values = dict(
        uncertainty_radii=_zero_radii(len(matrix)),
        center=0,
        radius=2,
        spectral_reference_scale=1,
        maximum_partitions=1024,
        maximum_factor_candidate_value_tuples=1_000_000,
        nodes=4,
        sqrt_precision=48,
    )
    values.update(overrides)
    return M.verified_interval_characteristic_spectral_split(matrix, **values)


def test_zero_uncertainty_transfers_exact_nominal_rank_and_projector() -> None:
    result = _split()
    assert result.validation_level == "VERIFIED_INTERVAL_CHARACTERISTIC_SPECTRAL_SPLIT_AND_RANK"
    assert result.nominal_projector_rank == 1
    assert result.family_projector_rank == 1
    assert result.nominal_exact_projector is not None
    assert result.exact_projector_perturbation_upper == 0
    assert result.all_family_members_have_same_projector_rank


def test_nonzero_rectangular_box_has_strict_robust_margin_and_rank_one() -> None:
    radii = (
        ((F(1, 100), F(1, 200)), (F(1, 1000), 0)),
        ((F(1, 1000), 0), (F(1, 100), F(1, 200))),
    )
    result = _split(uncertainty_radii=radii)
    assert result.validation_level is not None
    assert result.family_projector_rank == 1
    assert result.normalized_robust_contour_delta_lower is not None
    assert result.normalized_robust_contour_delta_lower > 0
    assert result.exact_projector_perturbation_upper is not None
    assert result.exact_projector_perturbation_upper > 0


def test_gaussian_matrix_nonreal_center_family_uses_automatic_nominal_rank() -> None:
    matrix = (((0, 1), 0), (0, (0, 5)))
    radii = (
        ((F(1, 100), F(1, 100)), (0, 0)),
        ((0, 0), (F(1, 100), F(1, 100))),
    )
    result = _split(matrix, uncertainty_radii=radii, center=(0, 1), radius=1)
    assert result.validation_level is not None
    assert result.nominal_discovery.center_shift_to_zero_verified
    assert result.family_projector_rank == 1


def test_uncertainty_equal_to_or_above_margin_fails_closed() -> None:
    result = _split(((0,),), uncertainty_radii=(((2, 0),),), radius=1)
    assert result.validation_level is None
    assert "INTERVAL_SPLIT_UNIFORM_CONTOUR_BRIDGE_UNAVAILABLE" in result.failure_codes
    assert result.family_projector_rank is None
    assert not result.homotopy_contour_crossing_excluded


def test_nominal_eigenvalue_on_contour_fails_both_rank_and_family_claim() -> None:
    result = _split(((2,),))
    assert result.validation_level is None
    assert "INTERVAL_SPLIT_NOMINAL_CHARACTERISTIC_DISCOVERY_UNAVAILABLE" in result.failure_codes
    assert result.family_projector_rank is None


def test_nominal_factor_budget_refusal_is_not_hidden_by_safe_interval_circle() -> None:
    matrix = (
        (0, 0, 0, -100),
        (100, 0, 0, 0),
        (0, 100, 0, 0),
        (0, 0, 100, 0),
    )
    result = _split(
        matrix,
        radius=1,
        maximum_factor_candidate_value_tuples=1,
    )
    assert result.validation_level is None
    assert result.nominal_discovery.status == "CHARACTERISTIC_Q_FACTORIZATION_BUDGET_EXCEEDED"
    assert result.interval_circle_bridge.validation_level is not None


def test_raw_unit_scaling_preserves_all_normalized_family_receipts() -> None:
    base = _split(uncertainty_radii=(((F(1, 100), 0), (0, 0)), ((0, 0), (F(1, 100), 0))))
    scaled = _split(
        ((0, 0), (0, 70)),
        uncertainty_radii=(((F(7, 100), 0), (0, 0)), ((0, 0), (F(7, 100), 0))),
        radius=14,
        spectral_reference_scale=7,
    )
    assert scaled.family_projector_rank == base.family_projector_rank
    assert scaled.normalized_uncertainty_upper == base.normalized_uncertainty_upper
    assert scaled.normalized_robust_contour_delta_lower == base.normalized_robust_contour_delta_lower
    assert scaled.exact_projector_perturbation_upper == base.exact_projector_perturbation_upper


def test_interval_factorization_and_root_tracking_are_explicitly_unnecessary() -> None:
    result = _split()
    assert not result.interval_characteristic_polynomial_factorization_required
    assert not result.interval_root_tracking_required
    assert not result.empirical_uncertainty_provenance_verified


def test_invalid_uncertainty_schema_is_delegated_to_strict_interval_parser() -> None:
    with pytest.raises(ValueError):
        _split(uncertainty_radii=(((0.0, 0), (0, 0)), ((0, 0), (0, 0))))


def test_partition_and_mesh_contracts_remain_strict() -> None:
    with pytest.raises(ValueError, match="at least two"):
        _split(maximum_partitions=1)
    with pytest.raises(ValueError, match="four-node"):
        _split(nodes=8)
