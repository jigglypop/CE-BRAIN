from __future__ import annotations

import importlib.util
import math
from fractions import Fraction as F
from pathlib import Path
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "reality_stone" / "python" / "reality_stone" / "clarus" / "physical_scale_mobility.py"


def _load():
    spec = importlib.util.spec_from_file_location("ce_physical_scale_mobility", MODULE_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


M = _load()


def _certificate(**overrides):
    values = dict(
        state_reference_scale=2,
        energy_reference_scale=3,
        time_reference_scale=5,
        physical_mobility=F(4, 15),
        dimensionless_window=F(1, 2),
        contraction_factor_upper=F(1, 2),
        dimensionless_gradient_norm_upper=3,
        logarithm_series_terms=4,
    )
    values.update(overrides)
    return M.physical_scale_mobility_certificate(**values)


def test_nonunit_mobility_and_physical_scales_are_exact() -> None:
    result = _certificate()
    assert result.status == "VERIFIED_PHYSICAL_SCALE_MOBILITY_MAP"
    assert result.normalized_mobility == 1
    assert result.physical_window == F(5, 2)
    assert result.velocity_reference_scale == F(2, 5)
    assert result.power_reference_scale == F(3, 5)
    assert result.physical_speed_upper == F(6, 5)
    assert result.euclidean_dissipation_upper == F(27, 5)


def test_predecessor_special_mobility_is_exactly_the_unit_slice() -> None:
    result = _certificate(
        state_reference_scale=7,
        energy_reference_scale=11,
        time_reference_scale=13,
        physical_mobility=F(49, 143),
    )
    assert result.normalized_mobility == 1


def test_logarithm_and_physical_decay_rate_enclosures_contain_oracle() -> None:
    result = _certificate(contraction_factor_upper=F(1, 2), logarithm_series_terms=5)
    assert result.logarithm_lower is not None and result.logarithm_upper is not None
    assert float(result.logarithm_lower) <= -math.log(0.5) <= float(result.logarithm_upper)
    expected_rate = -math.log(0.5) / 2.5
    assert float(result.decay_rate_lower) <= expected_rate <= float(result.decay_rate_upper)


def test_logarithm_enclosure_tightens_with_more_terms() -> None:
    coarse = _certificate(logarithm_series_terms=1)
    fine = _certificate(logarithm_series_terms=6)
    assert coarse.logarithm_lower < fine.logarithm_lower
    assert fine.logarithm_upper < coarse.logarithm_upper
    assert fine.logarithm_upper - fine.logarithm_lower < coarse.logarithm_upper - coarse.logarithm_lower


def test_q_zero_is_finite_window_collapse_without_log_rate() -> None:
    result = _certificate(contraction_factor_upper=0)
    assert result.status == "VERIFIED_FINITE_WINDOW_COLLAPSE_SCALE_MAP"
    assert result.validation_level == result.status
    assert result.logarithm_lower is None
    assert result.decay_rate_upper is None


def test_q_one_is_named_noncertificate_with_zero_positive_rate() -> None:
    result = _certificate(contraction_factor_upper=1)
    assert result.status == "NO_POSITIVE_CONTRACTION_RATE"
    assert result.validation_level is None
    assert result.failure_codes == ("CONTRACTION_NOT_STRICT",)
    assert result.decay_rate_lower == result.decay_rate_upper == 0


def test_consistent_unit_rescaling_preserves_normalized_dynamics() -> None:
    base = _certificate()
    scaled = _certificate(
        state_reference_scale=4,
        energy_reference_scale=9,
        time_reference_scale=25,
        physical_mobility=F(16, 225),
        dimensionless_window=F(1, 10),
    )
    assert scaled.normalized_mobility == base.normalized_mobility
    assert scaled.physical_window == base.physical_window
    assert scaled.logarithm_lower == base.logarithm_lower
    assert scaled.decay_rate_lower == base.decay_rate_lower


@pytest.mark.parametrize(
    "field,value",
    [
        ("state_reference_scale", 0),
        ("energy_reference_scale", -1),
        ("time_reference_scale", 0),
        ("physical_mobility", 0),
        ("dimensionless_window", -1),
        ("dimensionless_gradient_norm_upper", -1),
        ("contraction_factor_upper", F(-1, 2)),
        ("contraction_factor_upper", F(3, 2)),
        ("state_reference_scale", 1.0),
        ("physical_mobility", True),
        ("dimensionless_window", "01"),
    ],
)
def test_invalid_scales_exactness_and_bounds_fail_closed(field: str, value: object) -> None:
    with pytest.raises(ValueError):
        _certificate(**{field: value})


@pytest.mark.parametrize("terms", [0, -1, True, 1.0])
def test_invalid_logarithm_depth_fails_closed(terms: object) -> None:
    with pytest.raises(ValueError, match="logarithm_series_terms"):
        _certificate(logarithm_series_terms=terms)


def test_canonical_rational_strings_are_accepted_exactly() -> None:
    result = _certificate(
        state_reference_scale="2",
        energy_reference_scale="3",
        time_reference_scale="5",
        physical_mobility="4/15",
        contraction_factor_upper="0.5",
    )
    assert result.normalized_mobility == 1
