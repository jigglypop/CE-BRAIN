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


G = _load("quantitative_graph_transform", "quantitative_graph_transform.py")
M = _load("ce_nonaffine_triangular_c1", "quantitative_c1_graph_transform.py")


def _certificate(mu):
    return M.quantitative_c1_triangular_graph_transform(
        base_dimension=3,
        base_reference_scale=1,
        fiber_reference_scale=1,
        fiber_radius=1,
        forcing_at_zero_upper=F(1, 4),
        base_inverse_lipschitz=mu,
        fiber_linear_norm_upper=F(1, 4),
        base_to_fiber_lipschitz=F(1, 4),
        fiber_nonlinear_lipschitz=F(1, 4),
        graph_slope_upper=1,
        base_derivative_fiber_variation=F(1, 4),
        fiber_derivative_fiber_variation=F(1, 4),
    )


def test_sine_perturbed_identity_has_exact_inverse_derivative_bound() -> None:
    assert M.sine_perturbed_base_inverse_lipschitz(0) == 1
    assert M.sine_perturbed_base_inverse_lipschitz(F(1, 4)) == F(4, 3)
    assert M.sine_perturbed_base_inverse_lipschitz("0.25") == F(4, 3)


def test_nonaffine_sine_bound_composes_with_existing_c1_certificate() -> None:
    mu = M.sine_perturbed_base_inverse_lipschitz(F(1, 4))
    result = _certificate(mu)
    assert result.status == "VERIFIED_QUANTITATIVE_C1_TRIANGULAR_GRAPH_TRANSFORM"
    assert result.derivative_bunching_factor_upper == F(2, 3)
    assert result.derivative_bunching_margin == F(1, 3)
    assert result.lipschitz_certificate.slope_margin == 0
    assert result.lipschitz_certificate.robust_interior is False


def test_nonaffine_inverse_bound_does_not_bypass_bunching() -> None:
    mu = M.sine_perturbed_base_inverse_lipschitz(F(1, 2))
    result = M.quantitative_c1_triangular_graph_transform(
        base_dimension=1, base_reference_scale=1, fiber_reference_scale=1,
        fiber_radius=1, forcing_at_zero_upper=F(1, 4),
        base_inverse_lipschitz=mu, fiber_linear_norm_upper=F(1, 4),
        base_to_fiber_lipschitz=0, fiber_nonlinear_lipschitz=F(1, 4),
        graph_slope_upper=1, base_derivative_fiber_variation=0,
        fiber_derivative_fiber_variation=0,
    )
    assert result.lipschitz_certificate.validation_level is not None
    assert result.derivative_bunching_factor_upper == 1
    assert result.status == "C1_DERIVATIVE_BUNCHING_NOT_STRICT"


@pytest.mark.parametrize("amplitude", [-1, 1, F(5, 4), True, 0.1, "01"])
def test_invalid_or_boundary_sine_amplitude_fails_closed(amplitude: object) -> None:
    with pytest.raises(ValueError):
        M.sine_perturbed_base_inverse_lipschitz(amplitude)


def test_exact_bound_is_monotone_in_declared_amplitude() -> None:
    amplitudes = (0, F(1, 10), F(1, 4), F(1, 2), F(3, 4))
    bounds = tuple(M.sine_perturbed_base_inverse_lipschitz(value) for value in amplitudes)
    assert bounds == tuple(sorted(bounds))
    assert all(left < right for left, right in zip(bounds, bounds[1:]))

