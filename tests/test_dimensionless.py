from __future__ import annotations

import importlib.util
import math
from fractions import Fraction
from pathlib import Path
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]
CLARUS_DIR = ROOT / "reality_stone" / "python" / "reality_stone" / "clarus"


def _load_standalone_module(name: str, filename: str):
    """Load a math gate without importing the torch-backed package facade."""

    spec = importlib.util.spec_from_file_location(name, CLARUS_DIR / filename)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    try:
        spec.loader.exec_module(module)
    finally:
        sys.modules.pop(name, None)
    return module


_dimensionless = _load_standalone_module("ce_dimensionless_math", "dimensionless.py")
HAS_SYMPY = importlib.util.find_spec("sympy") is not None
_checker = _load_standalone_module("ce_dimensionless_checker", "dimensionless_checker.py")

CURVATURE = _dimensionless.CURVATURE
DIMENSIONLESS = _dimensionless.DIMENSIONLESS
LENGTH = _dimensionless.LENGTH
Quantity = _dimensionless.Quantity
audit_dimensionless = _dimensionless.audit_dimensionless
buckingham_pi_groups = _dimensionless.buckingham_pi_groups
check_dimensionless = _dimensionless.check_dimensionless
dim = _dimensionless.dim
evaluate_group = _dimensionless.evaluate_group
exp_argument = _dimensionless.exp_argument
exp_arguments = _dimensionless.exp_arguments
group_dimension = _dimensionless.group_dimension
nondimensionalize = _dimensionless.nondimensionalize
require_dimensionless = _dimensionless.require_dimensionless

Dimension = _checker.Dimension
DimensionVector = _checker.DimensionVector
DimensionlessChecker = _checker.DimensionlessChecker


def _assert_formula_pass(checker, formula) -> None:
    """Assert the backend-qualified ceiling without calling syntax a proof."""

    result = checker.check_formula(formula)
    assert result["parser_backend"] == checker.formula_parser_backend
    assert result["status"].startswith("PASS")
    if HAS_SYMPY:
        assert result["validation_level"] == "SYMPY_PARSE_HEURISTIC"
    else:
        assert result["validation_level"] == "SYNTAX_ONLY_HEURISTIC"
        assert result["status"] == "PASS_SYNTAX_ONLY"


def test_curvature_must_be_scaled_before_exponential() -> None:
    ricci = Quantity("R", 2.5, CURVATURE)
    length_c = Quantity("L_c", 3.0, LENGTH)

    with pytest.raises(ValueError, match="exponential"):
        exp_argument(ricci)

    r_tilde = nondimensionalize(ricci, [length_c])

    assert r_tilde.dims == DIMENSIONLESS
    assert math.isclose(r_tilde.value, 22.5)
    assert math.isclose(exp_argument(r_tilde), 22.5)


def test_mass_scale_lift_closes_as_ratio() -> None:
    m_phi = Quantity("m_phi", 29.65, dim(1, 0, 0, 0))
    m_p = Quantity("m_p", 938.2720813, dim(1, 0, 0, 0))

    ratio = nondimensionalize(m_phi, [m_p])

    assert ratio.dims == DIMENSIONLESS
    assert math.isclose(ratio.value, 29.65 / 938.2720813)


def test_ba_srm1_synapse_chart_and_kernel_arguments_are_dimensionless() -> None:
    # The checker tracks equality of dimensions; the electrical-current base is
    # not part of CE's four-axis registry, so voltage/resistance use distinct
    # nonzero representatives and are divided only by like-dimension scales.
    voltage = dim(1, 2, -3, 0)
    resistance = dim(1, 2, -2, 0)
    time = dim(0, 0, 1, 0)
    ratios = [
        nondimensionalize(
            Quantity("resting_psp", 8e-4, voltage),
            [Quantity("resting_psp_reference", 1e-3, voltage)],
        ),
        nondimensionalize(
            Quantity("soma_distance", 120e-6, LENGTH),
            [Quantity("metre", 1.0, LENGTH)],
        ),
        nondimensionalize(
            Quantity("input_resistance", 80e6, resistance),
            [Quantity("ohm", 1.0, resistance)],
        ),
        nondimensionalize(
            Quantity("membrane_tau", 18e-3, time),
            [Quantity("second", 1.0, time)],
        ),
        nondimensionalize(
            Quantity("late_pulse_psp", 6e-4, voltage),
            [Quantity("resting_psp_reference", 1e-3, voltage)],
        ),
        Quantity("log_variability", -0.3),
        Quantity("geodesic_over_bandwidth", 1.7),
    ]

    result = audit_dimensionless(ratios, context="BA-SRM1 log/Fisher/kernel core")

    assert result.passed
    assert all(quantity.dimensionless for quantity in result.unwrap())


def test_ba_srm2_event_history_target_and_kernel_are_dimensionless() -> None:
    voltage = dim(1, 2, -3, 0)
    current = dim(1, 2, -3, 0)
    resistance = dim(1, 2, -2, 0)
    capacitance = dim(-1, -2, 4, 0)
    time = dim(0, 0, 1, 0)
    temperature = dim(0, 0, 0, 1)

    ratios = [
        nondimensionalize(
            Quantity("pulse_interval", 20e-3, time),
            [Quantity("T0", 1e-3, time)],
        ),
        nondimensionalize(
            Quantity("ic_response", 8e-4, voltage),
            [Quantity("V0", 1e-3, voltage)],
        ),
        nondimensionalize(
            Quantity("stimulus_current", 50e-12, current),
            [Quantity("I0", 1e-12, current)],
        ),
        nondimensionalize(
            Quantity("input_resistance", 80e6, resistance),
            [Quantity("R0", 1e6, resistance)],
        ),
        nondimensionalize(
            Quantity("capacitance", 35e-12, capacitance),
            [Quantity("C0", 1e-12, capacitance)],
        ),
        nondimensionalize(
            Quantity("soma_distance", 120e-6, LENGTH),
            [Quantity("L0", 100e-6, LENGTH)],
        ),
        nondimensionalize(
            Quantity("bath_temperature", 307.0, temperature),
            [Quantity("Theta0", 310.0, temperature)],
        ),
        Quantity("pulse_count", 8.0),
        Quantity("pullback_line_element_sq", 1.4),
        Quantity("kernel_bandwidth_sq", 2.0),
    ]

    result = audit_dimensionless(ratios, context="BA-SRM2 event/Fisher/kernel core")

    assert result.passed
    assert all(quantity.dimensionless for quantity in result.unwrap())


def test_buckingham_pi_finds_reynolds_number_shape() -> None:
    rho = Quantity("rho", 1.2, dim(1, -3, 0, 0))
    velocity = Quantity("v", 3.0, dim(0, 1, -1, 0))
    length = Quantity("L", 2.0, dim(0, 1, 0, 0))
    viscosity = Quantity("mu", 1.8e-5, dim(1, -1, -1, 0))

    groups = buckingham_pi_groups([rho, velocity, length, viscosity])

    assert groups == [
        {"rho": Fraction(-1, 1), "v": Fraction(-1, 1), "L": Fraction(-1, 1), "mu": Fraction(1, 1)}
    ]
    assert group_dimension([rho, velocity, length, viscosity], groups[0]) == DIMENSIONLESS
    assert math.isclose(
        evaluate_group([rho, velocity, length, viscosity], groups[0]),
        1 / (1.2 * 3.0 * 2.0 / 1.8e-5),
    )


def test_dimensionless_guard_accepts_ce_core_ratio() -> None:
    epsilon2 = Quantity("epsilon^2", 0.04865)

    assert require_dimensionless(epsilon2).value == 0.04865


def test_interval_contour_bridge_units_close_before_core_use() -> None:
    spectral = dim(0, 0, -1, 0)
    reference = Quantity("spectral_reference_scale", 10.0, spectral)
    radius = Quantity("circle_radius", 2.0, spectral)
    uncertainty = Quantity("uncertainty_upper", 0.1, spectral)
    nominal_delta = Quantity("nominal_delta", 0.8, spectral)
    robust_delta = Quantity("robust_delta", 0.7, spectral)

    # Subtraction delta-epsilon is admitted only because both terms have the
    # same spectral dimension; the result keeps that dimension.
    assert uncertainty.dims == nominal_delta.dims == robust_delta.dims

    normalized = [
        nondimensionalize(quantity, [reference])
        for quantity in (radius, uncertainty, nominal_delta, robust_delta)
    ]
    assert audit_dimensionless(
        normalized, context="interval contour normalized certificate"
    ).passed

    projector_group = group_dimension(
        [radius, uncertainty, nominal_delta, robust_delta],
        {
            "circle_radius": Fraction(1),
            "uncertainty_upper": Fraction(1),
            "nominal_delta": Fraction(-1),
            "robust_delta": Fraction(-1),
        },
    )
    assert projector_group == DIMENSIONLESS

    raw_resolvent_dims = tuple(-power for power in robust_delta.dims)
    assert raw_resolvent_dims == dim(0, 0, 1, 0)


def test_interval_induced_norm_tightening_normalizes_row_column_bounds() -> None:
    spectral = dim(0, 0, -1, 0)
    reference = Quantity("spectral_reference_scale", 5.0, spectral)
    entry_radius = Quantity("entry_magnitude_upper", 0.2, spectral)
    one_norm = Quantity("induced_one_upper", 0.7, spectral)
    infinity_norm = Quantity("induced_infinity_upper", 0.8, spectral)

    normalized = [
        nondimensionalize(quantity, [reference])
        for quantity in (entry_radius, one_norm, infinity_norm)
    ]
    assert audit_dimensionless(
        normalized, context="interval induced-norm tightening"
    ).passed

    product_dims = tuple(
        left + right for left, right in zip(one_norm.dims, infinity_norm.dims)
    )
    assert product_dims == dim(0, 0, -2, 0)
    sqrt_product_dims = tuple(power / 2 for power in product_dims)
    assert sqrt_product_dims == spectral


def test_componentwise_residual_krawczyk_core_is_dimensionless() -> None:
    spectral = dim(0, 0, -1, 0)
    inverse_spectral = dim(0, 0, 1, 0)
    reference = Quantity("spectral_reference_scale", 5.0, spectral)
    node_matrix = Quantity("node_matrix", 2.0, spectral)
    inverse_witness = Quantity("inverse_witness", 0.5, inverse_spectral)
    uncertainty = Quantity("entry_uncertainty", 0.1, spectral)

    product_dims = tuple(
        left + right for left, right in zip(inverse_witness.dims, node_matrix.dims)
    )
    assert product_dims == DIMENSIONLESS

    normalized_node = nondimensionalize(node_matrix, [reference])
    normalized_uncertainty = nondimensionalize(uncertainty, [reference])
    normalized_inverse = Quantity("normalized_inverse_witness", 2.5)
    assert audit_dimensionless(
        [normalized_node, normalized_uncertainty, normalized_inverse],
        context="componentwise residual/Krawczyk core",
    ).passed

    # q = ||I-BA|| and the normalized inverse bounds are dimensionless.
    assert require_dimensionless(Quantity("residual_contraction_q", 0.2)).dimensionless
    assert require_dimensionless(Quantity("normalized_inverse_upper", 1.4)).dimensionless


def test_quantitative_graph_transform_normalizes_base_fiber_cross_slopes() -> None:
    base_unit = LENGTH
    fiber_unit = dim(1, 2, -3, 0)
    cross_unit = tuple(
        fiber_power - base_power
        for fiber_power, base_power in zip(fiber_unit, base_unit)
    )
    x_scale = Quantity("X_star", 2.0, base_unit)
    y_scale = Quantity("Y_star", 3.0, fiber_unit)
    fiber_radius = Quantity("fiber_radius", 3.0, fiber_unit)
    forcing = Quantity("forcing_at_zero", 0.75, fiber_unit)
    lx_raw = Quantity("L_x_raw", 0.375, cross_unit)
    slope_raw = Quantity("kappa_raw", 1.5, cross_unit)

    assert nondimensionalize(fiber_radius, [y_scale]).dimensionless
    assert nondimensionalize(forcing, [y_scale]).dimensionless
    for quantity in (lx_raw, slope_raw):
        normalized_dims = group_dimension(
            [quantity, x_scale, y_scale],
            {
                quantity.name: Fraction(1),
                "X_star": Fraction(1),
                "Y_star": Fraction(-1),
            },
        )
        assert normalized_dims == DIMENSIONLESS

    assert audit_dimensionless(
        [
            Quantity("mu", 1.0),
            Quantity("b", 0.25),
            Quantity("L_y", 0.25),
            Quantity("q", 0.5),
            Quantity("normalized_tube_margin", 0.25),
            Quantity("normalized_slope_margin", 0.25),
        ],
        context="quantitative triangular graph transform",
    ).passed


def test_dimensionless_gate_result_composes_value_transform() -> None:
    epsilon2 = Quantity("epsilon^2", 0.25)

    result = (
        check_dimensionless(epsilon2)
        .map(lambda q: q.value)
        .bind(lambda value: check_dimensionless(Quantity("sqrt_epsilon2", math.sqrt(value))))
    )

    assert result.passed
    assert math.isclose(result.unwrap().value, 0.5)


def test_dimensionless_audit_accumulates_all_failures() -> None:
    checks = [
        Quantity("epsilon^2", 0.04865),
        Quantity("R", 2.5, CURVATURE),
        Quantity("L", 3.0, LENGTH),
    ]

    result = audit_dimensionless(checks, context="CE selection gate")

    assert not result.passed
    assert len(result.errors) == 2
    assert "R must be dimensionless for CE selection gate" in result.errors[0]
    assert "L must be dimensionless for CE selection gate" in result.errors[1]
    with pytest.raises(ValueError, match="CE selection gate"):
        result.unwrap()


def test_exp_arguments_validates_batch_before_kernel_use() -> None:
    args = exp_arguments(
        [
            Quantity("D_eff", 0.31),
            Quantity("phi", 1.7),
        ]
    )

    assert args.passed
    assert args.unwrap() == (0.31, 1.7)


def test_checker_preserves_unnamed_inverse_time_dimension() -> None:
    inverse_time = Dimension.TIME**-1

    assert isinstance(inverse_time, DimensionVector)
    assert inverse_time.exponents == tuple(map(Fraction, (0, 0, -1, 0)))
    assert not inverse_time.is_dimensionless()


def test_checker_preserves_mass_squared_and_composes_back_to_mass() -> None:
    mass_squared = Dimension.MASS**2

    assert isinstance(mass_squared, DimensionVector)
    assert mass_squared.exponents == tuple(map(Fraction, (2, 0, 0, 0)))
    assert not mass_squared.is_dimensionless()
    assert mass_squared / Dimension.MASS == Dimension.MASS


def test_registered_rate_has_nontrivial_dimensions() -> None:
    formulas = {formula.name: formula for formula in DimensionlessChecker().formulas}

    rate = formulas["STDP learning rate upper bound"].expected_dim

    assert rate == Dimension.TIME**-1
    assert not rate.is_dimensionless()


def test_clarus_field_gate_and_phase_score_are_registered_dimensionless() -> None:
    checker = DimensionlessChecker()
    formulas = {formula.symbol: formula for formula in checker.formulas}

    assert formulas["g_CF"].expected_dim == Dimension.DIMENSIONLESS
    assert formulas["chi_CF"].expected_dim == Dimension.DIMENSIONLESS
    _assert_formula_pass(checker, formulas["g_CF"])
    _assert_formula_pass(checker, formulas["chi_CF"])


def test_unified_metric_surprise_and_condition_ratio_are_dimensionless() -> None:
    checker = DimensionlessChecker()
    formulas = {formula.symbol: formula for formula in checker.formulas}

    assert formulas["chi_UM"].expected_dim == Dimension.DIMENSIONLESS
    assert formulas["kappa_UM"].expected_dim == Dimension.DIMENSIONLESS
    _assert_formula_pass(checker, formulas["chi_UM"])
    _assert_formula_pass(checker, formulas["kappa_UM"])


def test_v16_metric_flow_residual_and_regret_are_dimensionless() -> None:
    checker = DimensionlessChecker()
    formulas = {formula.symbol: formula for formula in checker.formulas}

    assert formulas["r_V16"].expected_dim == Dimension.DIMENSIONLESS
    assert formulas["rho_V16"].expected_dim == Dimension.DIMENSIONLESS
    _assert_formula_pass(checker, formulas["r_V16"])
    _assert_formula_pass(checker, formulas["rho_V16"])


def test_v17_conditional_information_and_lift_margin_are_dimensionless() -> None:
    checker = DimensionlessChecker()
    formulas = {formula.symbol: formula for formula in checker.formulas}

    assert formulas["I_V17"].expected_dim == Dimension.DIMENSIONLESS
    assert formulas["delta_V17"].expected_dim == Dimension.DIMENSIONLESS
    _assert_formula_pass(checker, formulas["I_V17"])
    _assert_formula_pass(checker, formulas["delta_V17"])


def test_v18b_reward_decoder_and_classifier_increment_are_dimensionless() -> None:
    checker = DimensionlessChecker()
    formulas = {formula.symbol: formula for formula in checker.formulas}

    assert formulas["y_tilde_V18b"].expected_dim == Dimension.DIMENSIONLESS
    assert formulas["delta_w_V18b"].expected_dim == Dimension.DIMENSIONLESS
    _assert_formula_pass(checker, formulas["y_tilde_V18b"])
    _assert_formula_pass(checker, formulas["delta_w_V18b"])


def test_a4_a5_graph_metric_core_arguments_are_dimensionless() -> None:
    checker = DimensionlessChecker()
    formulas = {formula.symbol: formula for formula in checker.formulas}

    for symbol in ("a_A4", "r_w_A4", "chi_A5"):
        assert formulas[symbol].expected_dim == Dimension.DIMENSIONLESS
        _assert_formula_pass(checker, formulas[symbol])


def test_a6_pullback_and_reachability_ratios_are_dimensionless() -> None:
    checker = DimensionlessChecker()
    formulas = {formula.symbol: formula for formula in checker.formulas}

    for symbol in ("s_A6", "Lambda_A6", "delta_logV_A6", "rho_E_A6"):
        assert formulas[symbol].expected_dim == Dimension.DIMENSIONLESS
        _assert_formula_pass(checker, formulas[symbol])


def test_history_edge_metric_ratios_are_registered_dimensionless() -> None:
    checker = DimensionlessChecker()
    formulas = {formula.symbol: formula for formula in checker.formulas}

    for symbol in ("c_d_perp", "d_eff_mode", "eta_edge"):
        assert formulas[symbol].expected_dim == Dimension.DIMENSIONLESS
        _assert_formula_pass(checker, formulas[symbol])

    assert "orthogonal projection" in formulas["c_d_perp"].notes
    assert "identical" in formulas["d_eff_mode"].notes
    assert "epsilon_A < m0" in formulas["eta_edge"].notes
    assert checker.formula_parser_backend in {
        "sympy.parse_expr",
        "stdlib.ast.parse.syntax_only",
    }
    if not HAS_SYMPY:
        assert checker.formula_parser_backend == "stdlib.ast.parse.syntax_only"


def test_physical_scale_mobility_and_contraction_rate_units_close() -> None:
    state = dim(0, 1, 0, 0)
    energy = dim(1, 2, -2, 0)
    time = dim(0, 0, 1, 0)
    mobility = tuple(
        2 * state_power - energy_power - time_power
        for state_power, energy_power, time_power in zip(state, energy, time)
    )

    x0 = Quantity("state_reference", 2.0, state)
    v0 = Quantity("energy_reference", 3.0, energy)
    t0 = Quantity("time_reference", 5.0, time)
    mu = Quantity("physical_mobility", 4.0 / 15.0, mobility)

    normalized_mobility_dims = tuple(
        mu_power + energy_power + time_power - 2 * state_power
        for mu_power, energy_power, time_power, state_power in zip(
            mu.dims, v0.dims, t0.dims, x0.dims
        )
    )
    assert normalized_mobility_dims == DIMENSIONLESS

    q = Quantity("window_contraction", 0.5)
    z = Quantity("atanh_transform", (1.0 - q.value) / (1.0 + q.value))
    assert audit_dimensionless(
        [q, z], context="physical scale contraction core"
    ).passed

    velocity_dims = tuple(x - t for x, t in zip(x0.dims, t0.dims))
    power_dims = tuple(v - t for v, t in zip(v0.dims, t0.dims))
    rate_dims = tuple(-t for t in t0.dims)
    assert velocity_dims == dim(0, 1, -1, 0)
    assert power_dims == dim(1, 2, -3, 0)
    assert rate_dims == dim(0, 0, -1, 0)


def test_coupled_graph_transform_cross_lipschitz_normalization_closes() -> None:
    base = dim(0, 1, 0, 0)
    fiber = dim(1, 0, 0, 0)
    x0 = Quantity("base_reference", 5.0, base)
    y0 = Quantity("fiber_reference", 7.0, fiber)
    fiber_to_base = Quantity(
        "fiber_to_base_lipschitz", 5.0 / 56.0,
        tuple(x - y for x, y in zip(base, fiber)),
    )
    base_to_fiber = Quantity(
        "base_to_fiber_lipschitz", 7.0 / 40.0,
        tuple(y - x for x, y in zip(base, fiber)),
    )
    graph_slope = Quantity(
        "graph_slope", 7.0 / 5.0,
        tuple(y - x for x, y in zip(base, fiber)),
    )

    fy_dims = tuple(
        value + y - x
        for value, y, x in zip(fiber_to_base.dims, y0.dims, x0.dims)
    )
    gx_dims = tuple(
        value + x - y
        for value, x, y in zip(base_to_fiber.dims, x0.dims, y0.dims)
    )
    slope_dims = tuple(
        value + x - y
        for value, x, y in zip(graph_slope.dims, x0.dims, y0.dims)
    )
    assert fy_dims == gx_dims == slope_dims == DIMENSIONLESS

    core = [
        Quantity("mu", 1.0),
        Quantity("q", 0.5),
        Quantity("alpha", 0.75),
        Quantity("Q", 29.0 / 48.0),
    ]
    assert audit_dimensionless(core, context="coupled graph transform core").passed


def test_weighted_residual_similarity_and_condition_penalty_are_dimensionless() -> None:
    spectral = dim(0, 0, -1, 0)
    inverse_spectral = tuple(-power for power in spectral)
    node = Quantity("normalized_node_matrix", 2.0, spectral)
    witness = Quantity("normalized_inverse_witness", 0.5, inverse_spectral)
    weights = [Quantity("w1", 1.0), Quantity("w2", 3.0)]

    residual_dims = tuple(a + b for a, b in zip(node.dims, witness.dims))
    assert residual_dims == DIMENSIONLESS
    assert audit_dimensionless(
        weights
        + [
            Quantity("weight_condition_two", 3.0),
            Quantity("weighted_q_one", 0.4),
            Quantity("weighted_q_infinity", 0.5),
        ],
        context="weighted residual similarity core",
    ).passed

    transformed_node_dims = tuple(
        -left + value + right
        for left, value, right in zip(weights[0].dims, node.dims, weights[1].dims)
    )
    assert transformed_node_dims == spectral


def test_c1_graph_derivative_variation_and_bunching_are_dimensionless() -> None:
    base = dim(0, 1, 0, 0)
    fiber = dim(1, 0, 0, 0)
    hx_raw = Quantity(
        "base_derivative_fiber_variation",
        0.05,
        tuple(-power for power in base),
    )
    hy_raw = Quantity(
        "fiber_derivative_fiber_variation",
        1.0 / 28.0,
        tuple(-power for power in fiber),
    )
    x0 = Quantity("base_reference", 5.0, base)
    y0 = Quantity("fiber_reference", 7.0, fiber)
    hx_dims = tuple(h + x for h, x in zip(hx_raw.dims, x0.dims))
    hy_dims = tuple(h + y for h, y in zip(hy_raw.dims, y0.dims))
    assert hx_dims == hy_dims == DIMENSIONLESS
    assert audit_dimensionless(
        [
            Quantity("q", 0.5),
            Quantity("mu", 1.0),
            Quantity("beta", 0.5),
            Quantity("c_D", 0.5),
        ],
        context="C1 graph derivative bunching core",
    ).passed


def test_mixed_unit_tensor_mobility_congruence_closes_entrywise() -> None:
    time = dim(0, 0, 1, 0)
    energy = dim(1, 2, -2, 0)
    coordinate_i = dim(0, 1, 0, 0)
    coordinate_j = dim(0, 0, 0, 1)
    mobility_ij = tuple(
        xi + xj - e - t
        for xi, xj, e, t in zip(coordinate_i, coordinate_j, energy, time)
    )
    normalized_entry_dims = tuple(
        e + t - xi + m - xj
        for e, t, xi, m, xj in zip(
            energy, time, coordinate_i, mobility_ij, coordinate_j
        )
    )
    assert normalized_entry_dims == DIMENSIONLESS

    gradient_i = tuple(e - x for e, x in zip(energy, coordinate_i))
    velocity_i = tuple(m + g for m, g in zip(mobility_ij, tuple(e - x for e, x in zip(energy, coordinate_j))))
    assert velocity_i == tuple(x - t for x, t in zip(coordinate_i, time))
    dissipation = Quantity("g_transpose_M_g", 2.0)
    assert audit_dimensionless(
        [dissipation, Quantity("tensor_rank", 2.0)],
        context="mixed-unit tensor mobility core",
    ).passed
