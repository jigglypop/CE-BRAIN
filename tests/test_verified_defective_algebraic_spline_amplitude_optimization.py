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
    "verified_continuous_periodic_spline_amplitude_optimization",
    "verified_defective_general_affine_moving_knot_spline_bridge",
    "verified_automatic_interval_defective_general_affine_moving_knot_spline_bridge",
):
    _load(name, f"{name}.py")
D = _load("ce_verified_defective_algebraic_amplitude", "verified_defective_algebraic_spline_amplitude_optimization.py")


BOXES = ((F(-3, 2), F(-3, 4)), (F(-1, 4), F(1, 4)), (F(3, 4), F(3, 2)))
AMPS = ((0, F(1, 10)),) * 4


def _run(matrix=((0, 1, 0), (0, 0, 0), (0, 0, 8)), **overrides):
    args = dict(
        center=0, axis_u=4, axis_v=(2, 2), spectral_reference_scale=1,
        amplitude_intervals=AMPS, normalized_exterior_safety_margin=F(1, 4),
        normalized_radial_cap_ceiling=2,
        matrix_uncertainty_frobenius_upper=F(1, 100),
        knot_parameter_intervals=BOXES, junction_order=1,
        normalized_knot_optimality_tolerance=F(1, 32),
        maximum_knot_cells=16384, maximum_partitions=1024,
        maximum_factor_candidate_value_tuples=1_000_000, sqrt_precision=48,
    )
    args.update(overrides)
    return D.verified_defective_algebraic_spline_amplitude_optimization(matrix, **args)


def test_defective_shear_amplitude_optimum_is_fully_automatic() -> None:
    result = _run()
    assert result.validation_level is not None
    assert result.entire_amplitude_knot_matrix_product_family_verified
    assert result.exact_projector_rank == 2
    assert not result.diagonalization_witness_required
    assert not result.supplied_projector_or_inverse_required
    assert result.selected_total_amplitude_objective > 0


def test_algebraic_cap_enforces_predeclared_exterior_safety() -> None:
    result = _run()
    bridge = result.final_general_affine_bridge
    product = bridge.affine_operator_norm_upper * result.algebraic_derived_radial_cap * bridge.exterior_inverse_norm_upper
    assert product <= 1 - F(1, 4)
    assert bridge.exterior_affine_reciprocal_gap_lower >= F(1, 4)


def test_selected_amplitude_box_and_interval_projector_are_verified() -> None:
    result = _run()
    assert result.selected_admissible_amplitude_box is not None
    assert result.interval_neumann_product_upper < 1
    assert result.interval_neumann_margin_lower > 0
    assert result.perturbed_algebraic_resolvent_norm_upper > 0
    assert result.interval_projector_perturbation_norm_upper > 0


def test_zero_uncertainty_keeps_projector_bound_zero() -> None:
    result = _run(matrix_uncertainty_frobenius_upper=0)
    assert result.validation_level is not None
    assert result.interval_neumann_margin_lower == 1
    assert result.interval_projector_perturbation_norm_upper == 0


def test_neumann_equality_is_rejected() -> None:
    base = _run(matrix_uncertainty_frobenius_upper=0)
    equality = 1 / base.final_algebraic_resolvent_norm_upper
    result = _run(matrix_uncertainty_frobenius_upper=equality)
    assert result.validation_level is None
    assert "DEFECTIVE_ALGEBRAIC_AMPLITUDE_INTERVAL_NEUMANN_MARGIN_NONPOSITIVE" in result.failure_codes


def test_exterior_safety_can_make_amplitude_cap_infeasible() -> None:
    result = _run(normalized_exterior_safety_margin=F(9, 10))
    assert result.validation_level is None
    assert "DEFECTIVE_ALGEBRAIC_AMPLITUDE_CAP_BELOW_UNIT_CORE" in result.failure_codes


def test_characteristic_budget_failure_is_not_promoted() -> None:
    matrix = tuple(tuple(F(i) if i == j else F(0) for j in range(5)) for i in range(5))
    result = _run(matrix, maximum_partitions=8, matrix_uncertainty_frobenius_upper=0)
    assert result.validation_level is None
    assert "DEFECTIVE_ALGEBRAIC_AMPLITUDE_SEED_DISCOVERY_FAILED" in result.failure_codes


def test_raw_scale_covariance_includes_axes_and_uncertainty() -> None:
    base = _run()
    scaled = _run(
        ((0, 7, 0), (0, 0, 0), (0, 0, 56)),
        axis_u=28, axis_v=(14, 14), spectral_reference_scale=7,
        matrix_uncertainty_frobenius_upper=F(7, 100),
    )
    assert scaled.algebraic_derived_radial_cap == base.algebraic_derived_radial_cap
    assert scaled.selected_amplitudes == base.selected_amplitudes
    assert scaled.interval_neumann_margin_lower == base.interval_neumann_margin_lower


def test_grid_empirical_and_4_6_claims_remain_false() -> None:
    result = _run()
    assert not result.finite_grid_only
    assert not result.empirical_matrix_provenance_verified
