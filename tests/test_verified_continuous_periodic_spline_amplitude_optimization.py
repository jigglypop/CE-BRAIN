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
_load("verified_continuous_axis_aligned_ellipse_spectral_margin_optimization", "verified_continuous_axis_aligned_ellipse_spectral_margin_optimization.py")
_load("verified_continuous_stereographic_ellipse_spectral_margin_optimization", "verified_continuous_stereographic_ellipse_spectral_margin_optimization.py")
_load("verified_continuous_periodic_spline_knot_optimization", "verified_continuous_periodic_spline_knot_optimization.py")
A = _load("ce_verified_spline_amplitude", "verified_continuous_periodic_spline_amplitude_optimization.py")


BOXES = ((F(-3, 2), F(-3, 4)), (F(-1, 4), F(1, 4)), (F(3, 4), F(3, 2)))
AMPS = ((0, F(1, 25)), (0, F(1, 100)), (0, F(3, 100)), (0, F(1, 50)))


def _run(**overrides):
    args = dict(
        knot_parameter_intervals=BOXES, amplitude_intervals=AMPS,
        junction_order=1, normalized_radial_maximum_cap=F(33, 25),
        normalized_knot_optimality_tolerance=F(1, 32),
        maximum_knot_cells=16384, sqrt_precision=48,
    )
    args.update(overrides)
    return A.verified_continuous_periodic_spline_amplitude_optimization(**args)


def test_exact_separable_global_amplitude_optimum() -> None:
    result = _run()
    assert result.validation_level is not None
    assert result.per_patch_amplitude_cap == F(1, 50)
    assert result.selected_amplitudes == (F(1, 50), F(1, 100), F(1, 50), F(1, 50))
    assert result.selected_total_amplitude_objective == F(7, 100)
    assert result.certified_global_total_amplitude_upper == F(7, 100)
    assert result.exact_global_amplitude_optimum_verified


def test_selected_whole_amplitude_box_obeys_radial_cap() -> None:
    result = _run()
    assert result.selected_admissible_amplitude_box == tuple((F(0), value) for value in result.selected_amplitudes)
    assert result.selected_box_radial_minimum_lower == 1
    assert result.selected_box_radial_maximum_upper == F(33, 25)
    assert result.continuous_amplitude_box_covered


def test_gradient_lipschitz_and_original_box_receipts_are_exact() -> None:
    result = _run()
    assert result.original_box_radial_maximum_upper == F(41, 25)
    assert result.selected_box_radial_gradient_upper == F(16, 25)
    assert result.selected_box_radial_lipschitz_upper == F(49, 25)


def test_automatic_cq_junction_is_uniform_over_amplitude_box() -> None:
    result = _run(junction_order=6, normalized_radial_maximum_cap=1 + F(1, 2**14))
    assert result.validation_level is not None
    assert result.automatic_vanishing_exponent == 7
    assert result.selected_box_automatic_periodic_cq_junction_verified


def test_cap_infeasible_below_a_lower_amplitude() -> None:
    result = _run(
        amplitude_intervals=((F(1, 40), F(1, 25)),) + AMPS[1:],
        normalized_radial_maximum_cap=F(33, 25),
    )
    assert result.validation_level is None
    assert "CONTINUOUS_SPLINE_AMPLITUDE_CAP_INFEASIBLE" in result.failure_codes


def test_unit_cap_selects_zero_amplitudes() -> None:
    result = _run(normalized_radial_maximum_cap=1)
    assert result.validation_level is not None
    assert result.selected_amplitudes == (0, 0, 0, 0)
    assert result.selected_box_radial_lipschitz_upper == 1


def test_large_cap_selects_original_upper_corner() -> None:
    result = _run(normalized_radial_maximum_cap=2)
    assert result.selected_amplitudes == tuple(upper for _, upper in AMPS)
    assert result.selected_total_amplitude_objective == F(1, 10)


def test_knot_budget_failure_is_not_promoted() -> None:
    result = _run(normalized_knot_optimality_tolerance=0, maximum_knot_cells=1)
    assert result.validation_level is None
    assert "CONTINUOUS_SPLINE_AMPLITUDE_KNOT_OPTIMIZATION_FAILED" in result.failure_codes


def test_invalid_amplitude_and_cap_inputs_fail_closed() -> None:
    with pytest.raises(ValueError, match="nonnegative and ordered"):
        _run(amplitude_intervals=((F(-1, 10), 0),) + AMPS[1:])
    with pytest.raises(ValueError, match="at least one"):
        _run(normalized_radial_maximum_cap=F(9, 10))
    with pytest.raises(ValueError, match="exact"):
        _run(normalized_radial_maximum_cap=1.5)


def test_spectral_empirical_and_4_6_claims_remain_false() -> None:
    result = _run()
    assert not result.spectral_split_verified
    assert not result.empirical_matrix_provenance_verified
