from __future__ import annotations

import importlib.util
from fractions import Fraction as F
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
MODULE_DIR = ROOT / "reality_stone" / "python" / "reality_stone" / "clarus"


def _load(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, MODULE_DIR / filename)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


for name in (
    "verified_rational_contour", "verified_interval_contour", "verified_interval_tightening",
    "verified_interval_residual", "verified_algebraic_riesz_projector",
    "verified_polynomial_spectral_projector_construction", "verified_complete_q_polynomial_factorization",
    "verified_characteristic_spectral_split_discovery",
    "verified_continuous_axis_aligned_ellipse_spectral_margin_optimization",
    "verified_continuous_stereographic_ellipse_spectral_margin_optimization",
    "verified_continuous_periodic_spline_knot_optimization",
    "verified_defective_conformal_moving_knot_spline_bridge",
):
    _load(name, f"{name}.py")
A = _load("ce_verified_automatic_defective_conformal", "verified_automatic_defective_conformal_moving_knot_spline_bridge.py")


BOXES = ((F(-3, 2), F(-3, 4)), (F(-1, 4), F(1, 4)), (F(3, 4), F(3, 2)))


def _run(matrix=((0, 1, 0), (0, 0, 0), (0, 0, 4)), **overrides):
    args = dict(
        center=0, conformal_scale=2, conformal_unit=1, spectral_reference_scale=1,
        knot_parameter_intervals=BOXES,
        patch_amplitudes=(F(1, 100), F(1, 200), F(1, 300), F(1, 400)),
        junction_order=1, normalized_knot_optimality_tolerance=F(1, 32),
        maximum_knot_cells=16384, maximum_partitions=1024,
        maximum_factor_candidate_value_tuples=1_000_000, sqrt_precision=48,
    )
    args.update(overrides)
    return A.verified_automatic_defective_conformal_moving_knot_spline_bridge(matrix, **args)


def test_defective_projector_and_inverse_are_automatically_discovered() -> None:
    result = _run()
    assert result.validation_level is not None
    assert result.projector_automatically_constructed
    assert result.exterior_inverse_automatically_constructed
    assert result.characteristic_factorization_automatically_discovered
    assert result.exact_projector_rank == 2
    assert not result.supplied_projector_or_inverse_required


def test_reference_circle_is_derived_from_uniform_radial_envelope() -> None:
    result = _run()
    assert result.reference_radius_raw == F(54, 25)
    assert result.defective_bridge.uniform_inner_radius_lower == 2
    assert result.defective_bridge.uniform_outer_radius_upper == F(58, 25)


def test_repeated_root_is_kept_as_one_defective_primary_atom() -> None:
    result = _run()
    zero = next(item for item in result.characteristic_discovery.rational_root_factors if item.root == 0)
    assert zero.multiplicity == 2
    assert result.defective_bridge.defective_matrix_admitted


def test_irrational_pair_is_discovered_without_root_listing() -> None:
    result = _run(((0, 2, 0), (1, 0, 0), (0, 0, 4)), conformal_scale=3)
    assert result.validation_level is not None
    assert result.characteristic_discovery.residual_irreducible_over_q_verified
    assert result.exact_projector_rank == 2


def test_partition_budget_failure_is_not_promoted() -> None:
    matrix = tuple(tuple(F(i) if i == j else F(0) for j in range(5)) for i in range(5))
    result = _run(matrix, conformal_scale=F(5, 2), maximum_partitions=8)
    assert result.validation_level is None
    assert "AUTOMATIC_DEFECTIVE_CONFORMAL_CHARACTERISTIC_DISCOVERY_FAILED" in result.failure_codes


def test_contour_crossing_atom_fails_honestly() -> None:
    result = _run(((2,),), conformal_scale=2, patch_amplitudes=(0, 0, 0, 0))
    assert result.validation_level is None
    assert "AUTOMATIC_DEFECTIVE_CONFORMAL_CHARACTERISTIC_DISCOVERY_FAILED" in result.failure_codes


def test_raw_scale_covariance() -> None:
    base = _run()
    scaled = _run(
        ((0, 7, 0), (0, 0, 0), (0, 0, 28)),
        conformal_scale=14, spectral_reference_scale=7,
    )
    assert scaled.exact_projector_rank == base.exact_projector_rank
    assert scaled.defective_bridge.normalized_conformal_scale == base.defective_bridge.normalized_conformal_scale


def test_diagonalization_shear_empirical_and_dimension_claims_remain_false() -> None:
    result = _run()
    assert not result.diagonalization_witness_required
    assert not result.general_shear_affine_verified
    assert not result.empirical_matrix_provenance_verified
