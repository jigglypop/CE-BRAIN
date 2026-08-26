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
    "verified_rational_contour", "verified_continuous_axis_aligned_ellipse_spectral_margin_optimization",
    "verified_continuous_stereographic_ellipse_spectral_margin_optimization",
    "verified_continuous_periodic_spline_knot_optimization",
    "verified_continuous_periodic_spline_amplitude_optimization",
    "verified_moving_knot_spline_spectral_rank_bridge",
):
    _load(name, f"{name}.py")
S = _load("ce_verified_spectral_amplitude", "verified_spectral_spline_amplitude_optimization.py")


BOXES = ((F(-3, 2), F(-3, 4)), (F(-1, 4), F(1, 4)), (F(3, 4), F(3, 2)))
AMPS = ((0, F(1, 10)),) * 4


def _run(**overrides):
    args = dict(
        nominal_transition=((0, 0), (0, 3)), eigenvectors=((1, 0), (0, 1)),
        eigenvalues=(0, 3), target_inside_labels=(True, False), center=0,
        axis_u=1, axis_v=(0, 1), spectral_reference_scale=1,
        amplitude_intervals=AMPS, normalized_radial_safety_margin=F(1, 2),
        normalized_radial_cap_ceiling=2,
        knot_parameter_intervals=BOXES, junction_order=1,
        normalized_knot_optimality_tolerance=F(1, 32),
        maximum_knot_cells=16384, sqrt_precision=48,
    )
    args.update(overrides)
    return S.verified_spectral_spline_amplitude_optimization(**args)


def test_spectral_cap_drives_exact_amplitude_global_optimum() -> None:
    result = _run()
    assert result.validation_level is not None
    assert result.per_outside_eigenvalue_radius_lower == (3,)
    assert result.spectral_derived_radial_cap == 2
    assert result.selected_amplitudes == (F(1, 16),) * 4
    assert result.selected_total_amplitude_objective == F(1, 4)
    assert result.exact_global_amplitude_optimum_verified


def test_entire_selected_amplitude_and_knot_box_preserves_rank() -> None:
    result = _run()
    assert result.entire_selected_amplitude_and_knot_box_spectral_split_verified
    assert result.exact_projector_rank == 1
    assert result.quantitative_resolvent_norm_bound is not None
    assert not result.finite_grid_only


def test_general_affine_inverse_radii_determine_cap() -> None:
    result = _run(
        nominal_transition=((0, 0), (0, 6)), eigenvalues=(0, 6),
        axis_u=2, axis_v=(1, 1), normalized_radial_cap_ceiling=4,
    )
    assert result.normalized_affine_inverse_coordinate_squared == (0, 9)
    assert result.spectral_derived_radial_cap == F(5, 2)


def test_full_rank_uses_predeclared_ceiling_without_outside_values() -> None:
    result = _run(
        nominal_transition=((0,),), eigenvectors=((1,),), eigenvalues=(0,),
        target_inside_labels=(True,), normalized_radial_cap_ceiling=F(3, 2),
    )
    assert result.validation_level is not None
    assert result.per_outside_eigenvalue_radius_lower == ()
    assert result.spectral_derived_radial_cap == F(3, 2)
    assert result.exact_projector_rank == 1


def test_inside_value_outside_unit_core_fails_before_optimization() -> None:
    result = _run(
        nominal_transition=((1,),), eigenvectors=((1,),), eigenvalues=(1,),
        target_inside_labels=(True,),
    )
    assert result.validation_level is None
    assert "SPECTRAL_AMPLITUDE_INSIDE_UNIT_CORE_VIOLATED" in result.failure_codes


def test_excessive_safety_margin_fails_closed() -> None:
    result = _run(normalized_radial_safety_margin=F(5, 2))
    assert result.validation_level is None
    assert "SPECTRAL_AMPLITUDE_RADIAL_CAP_BELOW_UNIT_CORE" in result.failure_codes


def test_oblique_projector_and_conditioned_resolvent_are_retained() -> None:
    result = _run(
        nominal_transition=((0, 3), (0, 3)), eigenvectors=((1, 1), (0, 1)),
    )
    assert result.validation_level is not None
    assert result.spectral_bridge.projector_identity_verified
    assert result.quantitative_resolvent_norm_bound > _run().quantitative_resolvent_norm_bound


def test_raw_scale_covariance() -> None:
    base = _run()
    scaled = _run(
        nominal_transition=((0, 0), (0, 21)), eigenvalues=(0, 21),
        axis_u=7, axis_v=(0, 7), spectral_reference_scale=7,
    )
    assert scaled.spectral_derived_radial_cap == base.spectral_derived_radial_cap
    assert scaled.selected_amplitudes == base.selected_amplitudes


def test_knot_budget_and_empirical_boundaries() -> None:
    result = _run(normalized_knot_optimality_tolerance=0, maximum_knot_cells=1)
    assert result.validation_level is None
    assert "SPECTRAL_AMPLITUDE_GEOMETRY_OPTIMIZATION_FAILED" in result.failure_codes
    assert not _run().empirical_matrix_provenance_verified
