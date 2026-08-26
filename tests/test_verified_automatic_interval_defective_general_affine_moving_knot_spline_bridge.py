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
    "verified_defective_general_affine_moving_knot_spline_bridge",
):
    _load(name, f"{name}.py")
M = _load("ce_verified_auto_interval_gadef", "verified_automatic_interval_defective_general_affine_moving_knot_spline_bridge.py")


BOXES = ((F(-3, 2), F(-3, 4)), (F(-1, 4), F(1, 4)), (F(3, 4), F(3, 2)))


def _run(matrix=((0, 1, 0), (0, 0, 0), (0, 0, 8)), **overrides):
    args = dict(
        center=0, axis_u=4, axis_v=(2, 2), spectral_reference_scale=1,
        matrix_uncertainty_frobenius_upper=F(1, 16),
        knot_parameter_intervals=BOXES,
        patch_amplitudes=(F(1, 100), F(1, 200), F(1, 300), F(1, 400)),
        junction_order=1, normalized_knot_optimality_tolerance=F(1, 32),
        maximum_knot_cells=16384, maximum_partitions=1024,
        maximum_factor_candidate_value_tuples=1_000_000, sqrt_precision=48,
    )
    args.update(overrides)
    return M.verified_automatic_interval_defective_general_affine_moving_knot_spline_bridge(matrix, **args)


def test_shear_defective_witnesses_and_interval_rank_are_automatic() -> None:
    result = _run()
    assert result.validation_level is not None
    assert result.projector_automatically_constructed
    assert result.exterior_inverse_automatically_constructed
    assert result.automatic_general_shear_interval_rank_verified
    assert result.exact_projector_rank == 2
    assert not result.supplied_projector_or_inverse_required


def test_reference_circle_uses_affine_singular_sandwich() -> None:
    result = _run()
    bridge = result.general_affine_bridge
    expected = (
        bridge.uniform_euclidean_inner_radius_lower
        + bridge.uniform_euclidean_outer_radius_upper
    ) / 2
    assert result.reference_radius_raw == expected


def test_neumann_and_projector_receipts_are_positive_and_exactly_related() -> None:
    result = _run()
    assert result.neumann_product_upper == result.nominal_algebraic_resolvent_norm_upper / 16
    assert result.neumann_margin_lower == 1 - result.neumann_product_upper
    assert result.perturbed_algebraic_resolvent_norm_upper == result.nominal_algebraic_resolvent_norm_upper / result.neumann_margin_lower
    assert result.interval_projector_perturbation_norm_upper > 0


def test_neumann_equality_fails_closed() -> None:
    base = _run(matrix_uncertainty_frobenius_upper=0)
    equality = 1 / base.nominal_algebraic_resolvent_norm_upper
    result = _run(matrix_uncertainty_frobenius_upper=equality)
    assert result.validation_level is None
    assert "AUTO_INTERVAL_GADEF_NEUMANN_MARGIN_NONPOSITIVE" in result.failure_codes


def test_characteristic_budget_failure_is_not_promoted() -> None:
    matrix = tuple(tuple(F(i) if i == j else F(0) for j in range(5)) for i in range(5))
    result = _run(matrix, maximum_partitions=8, matrix_uncertainty_frobenius_upper=0)
    assert result.validation_level is None
    assert "AUTO_INTERVAL_GADEF_CHARACTERISTIC_DISCOVERY_FAILED" in result.failure_codes


def test_zero_uncertainty_reduces_to_automatic_nominal_shear_bridge() -> None:
    result = _run(matrix_uncertainty_frobenius_upper=0)
    assert result.validation_level is not None
    assert result.neumann_margin_lower == 1
    assert result.interval_projector_perturbation_norm_upper == 0


def test_raw_scale_covariance_includes_axes_and_uncertainty() -> None:
    base = _run()
    scaled = _run(
        ((0, 7, 0), (0, 0, 0), (0, 0, 56)),
        axis_u=28, axis_v=(14, 14), spectral_reference_scale=7,
        matrix_uncertainty_frobenius_upper=F(7, 16),
    )
    assert scaled.exact_projector_rank == base.exact_projector_rank
    assert scaled.neumann_margin_lower == base.neumann_margin_lower


def test_diagonalization_supplied_witness_empirical_and_4_6_remain_false() -> None:
    result = _run()
    assert not result.diagonalization_witness_required
    assert not result.supplied_projector_or_inverse_required
    assert not result.empirical_matrix_provenance_verified
