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
    "verified_characteristic_spectral_split_discovery", "verified_interval_characteristic_spectral_split",
):
    _load(name, f"{name}.py")
D = _load("ce_verified_direct_interval_factors", "verified_direct_interval_coordinate_block_factors.py")


def _zero(n):
    return tuple(tuple((0, 0) for _ in range(n)) for _ in range(n))


def _run(matrix=((0, 0), (0, 10)), **overrides):
    args = dict(
        uncertainty_radii=_zero(len(matrix)), coordinate_inside_indices=(0,),
        center=0, radius=2, spectral_reference_scale=1,
        maximum_determinant_terms=100_000, maximum_partitions=1024,
        maximum_factor_candidate_value_tuples=1_000_000, nodes=4, sqrt_precision=48,
    )
    args.update(overrides)
    return D.verified_direct_interval_coordinate_block_factors(matrix, **args)


def test_direct_linear_interval_factors_are_emitted() -> None:
    radii = (((F(1, 10), 0), (0, 0)), ((0, 0), (F(1, 10), 0)))
    result = _run(uncertainty_radii=radii)
    assert result.validation_level is not None
    inside, outside = result.normalized_inside_factor_coefficient_boxes, result.normalized_outside_factor_coefficient_boxes
    assert inside[0] == D.QComplexRectangle(F(-1, 10), F(1, 10), 0, 0)
    assert outside[0] == D.QComplexRectangle(F(-101, 10), F(-99, 10), 0, 0)
    assert inside[1] == outside[1] == D.ONE_BOX


def test_factor_degrees_match_interval_family_rank() -> None:
    result = _run()
    assert result.inside_factor_degree == result.interval_spectral_split.family_projector_rank == 1
    assert result.outside_factor_degree == 1
    assert result.factor_degrees_match_family_rank
    assert result.monic_factor_coefficients_verified


def test_two_by_two_inside_block_outputs_quadratic_boxes() -> None:
    matrix = ((0, 1, 0), (0, 0, 0), (0, 0, 10))
    radii = list(list(row) for row in _zero(3)); radii[0][1] = (F(1, 10), 0)
    result = _run(matrix, uncertainty_radii=tuple(tuple(row) for row in radii), coordinate_inside_indices=(0, 1))
    # The exact determinant enclosure is still emitted, but the existing IVSPEC
    # contour bridge deliberately fails closed for this defective 3x3 example.
    assert result.validation_level is None
    assert "DIRECT_INTERVAL_FACTOR_IVSPEC_BRIDGE_FAILED" in result.failure_codes
    assert len(result.normalized_inside_factor_coefficient_boxes) == 3
    assert result.inside_factor_degree == 2


def test_complex_diagonal_factor_has_rectangular_constant() -> None:
    matrix = (((0, 1), 0), (0, (10, 2)))
    radii = (((F(1, 10), F(1, 20)), (0, 0)), ((0, 0), (0, 0)))
    result = _run(matrix, uncertainty_radii=radii, center=(0, 1), radius=2)
    assert result.validation_level is not None
    constant = result.normalized_inside_factor_coefficient_boxes[0]
    assert constant == D.QComplexRectangle(F(-1, 10), F(1, 10), F(-21, 20), F(-19, 20))


def test_cross_block_nominal_or_uncertainty_is_rejected() -> None:
    nominal = _run(((0, 1), (0, 10)))
    radii = (((0, 0), (F(1, 100), 0)), ((0, 0), (0, 0)))
    uncertain = _run(uncertainty_radii=radii)
    assert "DIRECT_INTERVAL_FACTOR_COORDINATE_BLOCK_NOT_INVARIANT" in nominal.failure_codes
    assert "DIRECT_INTERVAL_FACTOR_COORDINATE_BLOCK_NOT_INVARIANT" in uncertain.failure_codes


def test_coordinate_projector_mismatch_is_rejected() -> None:
    result = _run(coordinate_inside_indices=(1,))
    assert result.validation_level is None
    assert "DIRECT_INTERVAL_FACTOR_COORDINATE_PROJECTOR_MISMATCH" in result.failure_codes


def test_zero_and_full_rank_factors_are_supported() -> None:
    zero = _run(((10,),), coordinate_inside_indices=())
    full = _run(((0,),), coordinate_inside_indices=(0,))
    assert zero.validation_level is not None and zero.normalized_inside_factor_coefficient_boxes == (D.ONE_BOX,)
    assert full.validation_level is not None and full.normalized_outside_factor_coefficient_boxes == (D.ONE_BOX,)


def test_determinant_term_budget_fails_closed() -> None:
    result = _run(maximum_determinant_terms=2)
    assert result.validation_level is None
    assert "DIRECT_INTERVAL_FACTOR_DETERMINANT_TERM_BUDGET_EXCEEDED" in result.failure_codes


def test_raw_scale_covariance_of_normalized_factor_boxes() -> None:
    base = _run(uncertainty_radii=(((F(1, 10), 0), (0, 0)), ((0, 0), (F(1, 10), 0))))
    scaled = _run(
        ((0, 0), (0, 70)), spectral_reference_scale=7, radius=14,
        uncertainty_radii=(((F(7, 10), 0), (0, 0)), ((0, 0), (F(7, 10), 0))),
    )
    assert scaled.normalized_inside_factor_coefficient_boxes == base.normalized_inside_factor_coefficient_boxes
    assert scaled.normalized_outside_factor_coefficient_boxes == base.normalized_outside_factor_coefficient_boxes


def test_product_direct_intersection_and_honesty_flags() -> None:
    result = _run()
    assert result.product_and_direct_coefficient_intersections_verified
    assert result.direct_interval_characteristic_factor_output_verified
    assert not result.interval_root_tracking_required
    assert not result.empirical_uncertainty_provenance_verified
