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


def test_coupled_c1_inverse_jacobian_recurrence_is_dimensionless() -> None:
    normalized_core = [
        Quantity("H_f", 0.01),
        Quantity("H_g", 0.01),
        Quantity("Lambda", 1.0),
        Quantity("alpha", 37.0 / 40.0),
        Quantity("Q", 77.0 / 370.0),
        Quantity("beta_c", 308.0 / 1369.0),
        Quantity("c_c", 0.1),
    ]
    assert audit_dimensionless(
        normalized_core,
        context="coupled C1 inverse-Jacobian recurrence core",
    ).passed


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


def test_c2_graph_hessian_class_and_recurrence_are_dimensionless() -> None:
    normalized_core = [
        Quantity("K_2", 1.0 / 16.0),
        Quantity("K_3", 1.0 / 16.0),
        Quantity("Lambda_2", 1.0),
        Quantity("Lambda_2_out", 3.0 / 4.0),
        Quantity("beta_2", 1.0 / 2.0),
        Quantity("c_21", 1.0 / 4.0),
        Quantity("c_20", 5.0 / 16.0),
    ]
    assert audit_dimensionless(
        normalized_core,
        context="C2 graph Hessian recurrence core",
    ).passed


def test_coupled_c2_inverse_map_hessian_recurrence_is_dimensionless() -> None:
    normalized_core = [
        Quantity("H_f", 0.01),
        Quantity("H_g", 0.01),
        Quantity("T_f", 0.001),
        Quantity("T_g", 0.001),
        Quantity("Lambda", 1.0),
        Quantity("Xi", 1.0),
        Quantity("alpha", 37.0 / 40.0),
        Quantity("Q", 77.0 / 370.0),
        Quantity("beta_2_c", 12320.0 / 50653.0),
        Quantity("c_21_c", 0.1),
        Quantity("c_20_c", 0.1),
    ]
    assert audit_dimensionless(
        normalized_core,
        context="coupled C2 inverse-map Hessian recurrence core",
    ).passed


def test_nonaffine_triangular_c2_inverse_curvature_terms_are_dimensionless() -> None:
    normalized_core = [
        Quantity("mu", 4.0 / 3.0),
        Quantity("nu", 16.0 / 27.0),
        Quantity("Lambda_2_out", 214.0 / 27.0),
        Quantity("beta_2", 8.0 / 9.0),
        Quantity("c_21_nonaffine", 20.0 / 27.0),
        Quantity("c_20_nonaffine", 38.0 / 27.0),
    ]
    assert audit_dimensionless(
        normalized_core,
        context="nonaffine triangular C2 inverse-curvature recurrence core",
    ).passed


def test_local_nonaffine_c2_domain_coverage_is_dimensionless_after_scaling() -> None:
    base = dim(0, 1, 0, 0)
    domain_radius = Quantity("R_x", 5.0, base)
    inverse_image_radius = Quantity("R_pre", 20.0 / 7.0, base)
    reference_scale = Quantity("X_0", 5.0, base)
    normalized_domain_dims = tuple(
        radius - scale
        for radius, scale in zip(domain_radius.dims, reference_scale.dims)
    )
    normalized_inverse_dims = tuple(
        radius - scale
        for radius, scale in zip(inverse_image_radius.dims, reference_scale.dims)
    )
    assert normalized_domain_dims == normalized_inverse_dims == DIMENSIONLESS
    assert audit_dimensionless(
        [
            Quantity("r_x", 1.0),
            Quantity("r_pre", 4.0 / 7.0),
            Quantity("coverage_margin", 3.0 / 7.0),
        ],
        context="local nonaffine C2 inverse-domain coverage core",
    ).passed


def test_matched_local_c2_forward_and_inverse_contacts_share_base_units() -> None:
    base = dim(0, 1, 0, 0)
    x0 = Quantity("X_0", 5.0, base)
    raw_radii = [
        Quantity("R_input", 5.0, base),
        Quantity("R_output", 5.0, base),
        Quantity("R_inverse_exact", 5.0, base),
        Quantity("R_forward_exact", 5.0, base),
    ]
    for radius in raw_radii:
        assert tuple(r - s for r, s in zip(radius.dims, x0.dims)) == DIMENSIONLESS
    assert audit_dimensionless(
        [
            Quantity("inverse_contact_residual", 0.0),
            Quantity("forward_contact_residual", 0.0),
            Quantity("beta_2", 0.5),
            Quantity("c_21", 1.5),
        ],
        context="matched local nonaffine C2 boundary-contact core",
    ).passed


def test_nonaffine_coupled_c1_base_curvature_terms_are_dimensionless() -> None:
    normalized_core = [
        Quantity("H_phi", 1.0 / 1000.0),
        Quantity("C_F_nonaffine", 147.0 / 2000.0),
        Quantity("Lambda_out_nonaffine", 69388.0 / 253265.0),
        Quantity("A_delta_nonaffine", 351.0 / 18500.0),
        Quantity("beta_1", 308.0 / 1369.0),
        Quantity("c_10_nonaffine", 41212.0 / 1266325.0),
    ]
    assert audit_dimensionless(
        normalized_core,
        context="nonaffine coupled C1 base-curvature recurrence core",
    ).passed


def test_nonaffine_coupled_c2_base_curvature_terms_are_dimensionless() -> None:
    normalized_core = [
        Quantity("H_phi", 1.0 / 1000.0),
        Quantity("T_phi", 1.0 / 1000.0),
        Quantity("C_P_nonaffine", 0.1),
        Quantity("C_N_nonaffine", 0.3),
        Quantity("Xi_out_nonaffine", 0.5),
        Quantity("beta_2_c", 12320.0 / 50653.0),
        Quantity("c_21_nonaffine", 0.1),
        Quantity("c_20_nonaffine", 0.1),
    ]
    assert audit_dimensionless(
        normalized_core,
        context="nonaffine coupled C2 base-curvature recurrence core",
    ).passed


def test_nonaffine_coupled_c3_base_curvature_terms_are_dimensionless() -> None:
    normalized_core = [
        Quantity("H_phi", 1.0 / 1000.0),
        Quantity("T_phi", 1.0 / 1000.0),
        Quantity("U_phi", 1.0 / 1000.0),
        Quantity("C_U_nonaffine", 0.1),
        Quantity("C_U1_nonaffine", 0.2),
        Quantity("C_M_nonaffine", 0.3),
        Quantity("Lambda_3_out_nonaffine", 0.4),
        Quantity("Xi_3_out_nonaffine", 0.5),
        Quantity("beta_3_c_nonaffine", 0.6),
        Quantity("c_32_c_nonaffine", 0.1),
        Quantity("c_31_c_nonaffine", 0.1),
        Quantity("c_30_c_nonaffine", 0.1),
    ]
    assert audit_dimensionless(
        normalized_core,
        context="nonaffine coupled C3 base-curvature recurrence core",
    ).passed


def test_affine_triangular_c4_recurrence_is_dimensionless() -> None:
    normalized_core = [
        Quantity("K_4", 1.0 / 64.0),
        Quantity("K_5", 1.0 / 256.0),
        Quantity("Lambda_4", 6.0),
        Quantity("Lambda_4_out", 95.0 / 16.0),
        Quantity("beta_4", 0.5),
        Quantity("c_43", 0.5),
        Quantity("c_42", 15.0 / 8.0),
        Quantity("c_41", 2.5),
        Quantity("c_40", 2.0),
    ]
    assert audit_dimensionless(
        normalized_core,
        context="affine triangular C4 five-layer recurrence core",
    ).passed


def test_affine_coupled_c4_modified_tensor_core_is_dimensionless() -> None:
    normalized_core = [
        Quantity("C_W", 1.0),
        Quantity("C_Z", 4.0),
        Quantity("C_O", 5.0),
        Quantity("Lambda_4_out_coupled", 6.0),
        Quantity("Xi_4_out_coupled", 40.0),
        Quantity("beta_4_coupled", 0.3),
        Quantity("c_43_coupled", 0.3),
        Quantity("c_42_coupled", 0.7),
        Quantity("c_41_coupled", 2.3),
        Quantity("c_40_coupled", 2.8),
    ]
    assert audit_dimensionless(
        normalized_core,
        context="affine coupled C4 modified-tensor recurrence core",
    ).passed


def test_nonaffine_triangular_c4_inverse_chain_core_is_dimensionless() -> None:
    normalized_core = [
        Quantity("mu", 10.0 / 9.0),
        Quantity("nu", 100.0 / 729.0),
        Quantity("tau", 14000.0 / 59049.0),
        Quantity("upsilon", 620000.0 / 1594323.0),
        Quantity("Lambda_4_out_nonaffine", 152045000.0 / 1594323.0),
        Quantity("beta_4_nonaffine", 5000.0 / 6561.0),
        Quantity("c_43_nonaffine", 25000.0 / 19683.0),
        Quantity("c_42_nonaffine", 2320000.0 / 531441.0),
        Quantity("c_41_nonaffine", 15940000.0 / 1594323.0),
        Quantity("c_40_nonaffine", 31673125.0 / 1594323.0),
    ]
    assert audit_dimensionless(
        normalized_core,
        context="nonaffine triangular C4 inverse-chain recurrence core",
    ).passed


def test_nonaffine_coupled_c4_modified_tensor_core_is_dimensionless() -> None:
    normalized_core = [
        Quantity("U_phi", 0.001),
        Quantity("V_phi", 0.001),
        Quantity("C_W_nonaffine", 1.0),
        Quantity("C_O_nonaffine", 5.0),
        Quantity("Lambda_4_out_nonaffine_coupled", 6.5),
        Quantity("Xi_4_out_nonaffine_coupled", 38.7),
        Quantity("beta_4_nonaffine_coupled", 0.284),
        Quantity("c_43_nonaffine_coupled", 0.3),
        Quantity("c_42_nonaffine_coupled", 0.71),
        Quantity("c_41_nonaffine_coupled", 2.27),
        Quantity("c_40_nonaffine_coupled", 2.79),
    ]
    assert audit_dimensionless(
        normalized_core,
        context="nonaffine coupled C4 modified-tensor recurrence core",
    ).passed


def test_local_matched_nonaffine_coupled_c4_collars_are_dimensionless() -> None:
    assert audit_dimensionless(
        [
            Quantity("r_input", 1.0),
            Quantity("r_output", 1.0),
            Quantity("eta_input_c4", 0.1),
            Quantity("eta_output_c4", 0.05),
            Quantity("r_inverse_c4_collar", 1.05),
            Quantity("c4_collar_margin", 0.05),
            Quantity("inverse_contact", 0.0),
            Quantity("forward_contact", 0.0),
            Quantity("graph_boundary_residual", 0.0),
            Quantity("fiber_boundary_residual", 0.0),
        ],
        context="local matched nonaffine coupled C4 collar and contact core",
    ).passed


def test_affine_arbitrary_order_bell_hierarchy_is_dimensionless() -> None:
    assert audit_dimensionless(
        [
            Quantity("Lambda_5", 40.0),
            Quantity("Lambda_6", 400.0),
            Quantity("K_6", 1.0 / 1024.0),
            Quantity("K_7", 1.0 / 4096.0),
            Quantity("Lambda_5_out", 133.0 / 4.0),
            Quantity("Lambda_6_out", 2283.0 / 8.0),
            Quantity("beta_5", 0.5),
            Quantity("beta_6", 0.5),
            Quantity("c_50", 153.0 / 16.0),
            Quantity("c_60", 1199.0 / 16.0),
        ],
        context="affine arbitrary-order Bell-polynomial hierarchy core",
    ).passed


def test_nonaffine_arbitrary_order_inverse_bell_hierarchy_is_dimensionless() -> None:
    assert audit_dimensionless(
        [
            Quantity("I_5", 488600.0 / 129140163.0),
            Quantity("I_6", 3797600.0 / 1162261467.0),
            Quantity("Lambda_5_out_nonaffine", 116441578775.0 / 43046721.0),
            Quantity("Lambda_6_out_nonaffine", 75171452147900.0 / 387420489.0),
            Quantity("beta_5_nonaffine", 50000.0 / 59049.0),
            Quantity("beta_6_nonaffine", 500000.0 / 531441.0),
        ],
        context="nonaffine arbitrary-order inverse Bell hierarchy core",
    ).passed


def test_coupled_arbitrary_order_implicit_jet_recurrence_is_dimensionless() -> None:
    assert audit_dimensionless(
        [
            Quantity("alpha_implicit", 1.0),
            Quantity("F_1_implicit", 2.0),
            Quantity("F_2_implicit", 1.0),
            Quantity("Y_4_implicit", 1.0),
            Quantity("B_4_implicit", 360.0),
            Quantity("X_4_implicit", 360.0),
            Quantity("beta_4_implicit", 0.25),
            Quantity("c_40_implicit", 4.0),
        ],
        context="coupled arbitrary-order conditional implicit-jet Bell recurrence",
    ).passed


def test_coupled_arbitrary_order_raw_jet_generator_is_dimensionless() -> None:
    assert audit_dimensionless(
        [
            Quantity("R_1_coupled_cn", 2.0),
            Quantity("R_4_coupled_cn", 4.0),
            Quantity("K_4_coupled_cn", 7.0),
            Quantity("A_4_coupled_cn", 468.0),
            Quantity("r_x_coupled_cn", 0.1),
            Quantity("state_coupling_coupled_cn", 1.2),
            Quantity("Lambda_6_out_coupled_cn", 4119.86),
            Quantity("beta_6_coupled_cn", 0.0398),
        ],
        context="coupled arbitrary-order raw-jet generator and implicit composition",
    ).passed


def test_local_matched_coupled_arbitrary_order_collars_are_dimensionless() -> None:
    base = dim(0, 1, 0, 0)
    fiber = dim(0, 0, 0, 1)
    x_reference = Quantity("X_0_local_cn", 5.0, base)
    y_reference = Quantity("Y_0_local_cn", 7.0, fiber)
    for radius in [
        Quantity("R_input_cn", 5.0, base),
        Quantity("R_output_cn", 5.0, base),
        Quantity("R_inverse_cn", 5.0, base),
        Quantity("eta_input_cn", 0.5, base),
        Quantity("R_inverse_collar_cn", 5.25, base),
    ]:
        assert tuple(r - s for r, s in zip(radius.dims, x_reference.dims)) == DIMENSIONLESS
    for boundary in [
        Quantity("graph_boundary_cn", 0.0, fiber),
        Quantity("fiber_boundary_cn", 0.0, fiber),
    ]:
        assert tuple(r - s for r, s in zip(boundary.dims, y_reference.dims)) == DIMENSIONLESS
    assert audit_dimensionless(
        [
            Quantity("r_input_cn", 1.0),
            Quantity("r_output_cn", 1.0),
            Quantity("r_inverse_cn", 1.0),
            Quantity("eta_input_cn", 0.1),
            Quantity("eta_output_cn", 0.05),
            Quantity("r_inverse_collar_cn", 1.05),
            Quantity("collar_margin_cn", 0.05),
            Quantity("inverse_contact_cn", 0.0),
            Quantity("forward_contact_cn", 0.0),
        ],
        context="local matched coupled arbitrary-order collar and contact core",
    ).passed


def test_analytic_implicit_graph_transform_majorants_are_dimensionless() -> None:
    assert audit_dimensionless(
        [
            Quantity("r_complex_in", 0.25),
            Quantity("x_F_analytic", 0.25),
            Quantity("N_r_analytic", 1.0 / 120.0),
            Quantity("theta_r_analytic", 7.0 / 90.0),
            Quantity("inverse_factor_analytic", 7.0 / 90.0),
            Quantity("rho_available_analytic", 29.0 / 120.0),
            Quantity("rho_requested_analytic", 0.2),
            Quantity("M_T_analytic", 1.0 / 30.0),
            Quantity("analytic_rate", 15.0),
            Quantity("q_complex", 0.5),
        ],
        context="complex-ball analytic implicit graph-transform majorant",
    ).passed


def test_conscious_moment_dimension_protocol_metrics_are_dimensionless() -> None:
    assert audit_dimensionless(
        [
            Quantity("d_participation", 5.0),
            Quantity("d_ridge", 50.0 / 11.0),
            Quantity("d_stable", 5.0),
            Quantity("d_hard", 5.0),
            Quantity("heldout_delta", 9.99),
            Quantity("heldout_se2", 0.0),
            Quantity("p_max_menu", 1.0 / 1001.0),
            Quantity("rank_agreement_tolerance", 1.0),
        ],
        context="held-out conscious-moment neural signal-rank protocol",
    ).passed


def test_full_c0_to_cn_adapter_contacts_and_recurrence_are_dimensionless() -> None:
    assert audit_dimensionless(
        [
            Quantity("alpha_full_cn", 0.9),
            Quantity("lambda_1_full_cn", 1.0),
            Quantity("r_x_full_cn", 0.1),
            Quantity("s_full_cn", 0.01),
            Quantity("q_0_full_cn", 0.011),
            Quantity("delta_0_full_cn", 1.0),
            Quantity("delta_6_full_cn", 1.0),
            Quantity("constant_contact_residual", 0.0),
        ],
        context="same-version full coupled C0-to-finite-Cn adapter",
    ).passed


def test_smooth_projective_triangular_prefix_is_dimensionless() -> None:
    assert audit_dimensionless(
        [
            Quantity("q0_projective", 0.011),
            Quantity("beta_1_projective", 0.1),
            Quantity("beta_6_projective", 0.5),
            Quantity("max_diagonal_projective", 0.5),
            Quantity("triangular_margin_projective", 0.5),
            Quantity("cn_prefix_distance", 1.0),
        ],
        context="nonanalytic smooth projective finite-prefix recurrence",
    ).passed


def test_neural_measurement_bridge_normalization_and_coverage_core_are_dimensionless() -> None:
    base = dim(0, 1, 0, 0)
    fiber = dim(0, 0, 0, 1)
    x_reference = Quantity("X0_neural_bridge", 5.0, base)
    y_reference = Quantity("Y0_neural_bridge", 7.0, fiber)
    fy_raw = tuple(x - y for x, y in zip(base, fiber))
    gx_raw = tuple(y - x for x, y in zip(base, fiber))
    assert tuple(a + y - x for a, y, x in zip(fy_raw, y_reference.dims, x_reference.dims)) == DIMENSIONLESS
    assert tuple(a + x - y for a, x, y in zip(gx_raw, x_reference.dims, y_reference.dims)) == DIMENSIONLESS
    for radius in (
        Quantity("R_input_bridge", 5.0, base),
        Quantity("R_inverse_bridge", 5.0, base),
        Quantity("R_collar_bridge", 5.25, base),
    ):
        assert tuple(r - x for r, x in zip(radius.dims, x_reference.dims)) == DIMENSIONLESS
    assert audit_dimensionless(
        [
            Quantity("alpha_bridge", 0.9),
            Quantity("r_x_bridge", 0.1),
            Quantity("graph_D2_bridge", 1.0),
            Quantity("familywise_error_bridge", 0.01),
            Quantity("coverage_family_size_bridge", 1.0),
            Quantity("heldout_violation_count_bridge", 0.0),
        ],
        context="source-locked neural envelope to graph-transform bridge",
    ).passed


def test_dissipative_skew_mobility_split_and_rate_are_dimensionless() -> None:
    time = dim(0, 0, 1, 0)
    rate = tuple(-entry for entry in time)
    assert Quantity("physical_skew_decay_rate", 0.2, rate).dims == rate
    assert audit_dimensionless(
        [
            Quantity("normalized_M", 2.0),
            Quantity("normalized_S", 2.0),
            Quantity("normalized_K", 3.0),
            Quantity("coercivity_m", 1.0),
            Quantity("PL_lambda", 0.5),
            Quantity("normalized_decay_rate", 1.0),
            Quantity("skew_power", 0.0),
            Quantity("forcing_power", 0.0),
            Quantity("net_dissipation_margin", 2.0),
        ],
        context="mixed-unit dissipative/skew mobility and PL rate core",
    ).passed


def test_binary64_normalized_residual_witness_core_is_dimensionless() -> None:
    assert audit_dimensionless(
        [
            Quantity("decoded_binary64_witness", 1.0),
            Quantity("exact_residual", 0.0),
            Quantity("interval_residual_q", 0.1),
            Quantity("normalized_sigma_lower", 0.9),
            Quantity("normalized_chord", 0.75),
            Quantity("normalized_delta", 0.15),
        ],
        context="exact decoding of normalized binary64 residual witnesses",
    ).passed


def test_local_nonaffine_coupled_c2_domain_gate_is_dimensionless_after_scaling() -> None:
    base = dim(0, 1, 0, 0)
    reference = Quantity("X_0", 5.0, base)
    raw_radii = [
        Quantity("R_input", 5.0, base),
        Quantity("R_output", 5.0, base),
        Quantity("R_pre_uniform", 3.0, base),
    ]
    for radius in raw_radii:
        assert tuple(r - s for r, s in zip(radius.dims, reference.dims)) == DIMENSIONLESS
    assert audit_dimensionless(
        [
            Quantity("r_input", 1.0),
            Quantity("r_output", 1.0),
            Quantity("r_pre_uniform", 3.0 / 5.0),
            Quantity("domain_margin", 2.0 / 5.0),
            Quantity("beta_2_c", 7520.0 / 109503.0),
        ],
        context="local nonaffine coupled C2 inverse-domain core",
    ).passed


def test_matched_local_nonaffine_coupled_c2_contacts_are_dimensionless_after_scaling() -> None:
    base = dim(0, 1, 0, 0)
    fiber = dim(0, 0, 0, 1)
    x_reference = Quantity("X_0", 5.0, base)
    y_reference = Quantity("Y_0", 7.0, fiber)
    for radius in [
        Quantity("R_input", 5.0, base),
        Quantity("R_output", 5.0, base),
        Quantity("R_pre_exact", 5.0, base),
        Quantity("R_fwd_exact", 5.0, base),
    ]:
        assert tuple(r - s for r, s in zip(radius.dims, x_reference.dims)) == DIMENSIONLESS
    for boundary in [
        Quantity("graph_boundary", 0.0, fiber),
        Quantity("fiber_boundary_forcing", 0.0, fiber),
    ]:
        assert tuple(r - s for r, s in zip(boundary.dims, y_reference.dims)) == DIMENSIONLESS
    assert audit_dimensionless(
        [
            Quantity("inverse_contact", 0.0),
            Quantity("forward_contact", 0.0),
            Quantity("graph_boundary_residual", 0.0),
            Quantity("fiber_boundary_residual", 0.0),
            Quantity("beta_2_c", 6272.0 / 59319.0),
        ],
        context="matched local nonaffine coupled C2 boundary-contact core",
    ).passed


def test_local_nonaffine_coupled_c3_collars_are_dimensionless_after_scaling() -> None:
    base = dim(0, 1, 0, 0)
    reference = Quantity("X_0", 5.0, base)
    for radius in [
        Quantity("R_input", 5.0, base),
        Quantity("R_output", 5.0, base),
        Quantity("eta_input_c3", 0.5, base),
        Quantity("eta_output_c3", 0.25, base),
        Quantity("R_pre_c3_collar", 5.25, base),
    ]:
        assert tuple(r - s for r, s in zip(radius.dims, reference.dims)) == DIMENSIONLESS
    assert audit_dimensionless(
        [
            Quantity("r_input", 1.0),
            Quantity("eta_input_c3", 0.1),
            Quantity("eta_output_c3", 0.05),
            Quantity("r_pre_c3_collar", 1.05),
            Quantity("c3_collar_margin", 0.05),
            Quantity("beta_3_c_nonaffine", 0.6),
        ],
        context="local nonaffine coupled C3 extension-collar core",
    ).passed


def test_matched_local_nonaffine_coupled_c3_contacts_and_collars_are_separate() -> None:
    assert audit_dimensionless(
        [
            Quantity("inverse_contact", 0.0),
            Quantity("forward_contact", 0.0),
            Quantity("input_c3_collar", 0.1),
            Quantity("output_c3_collar", 0.05),
            Quantity("inverse_c3_collar_margin", 0.05),
            Quantity("graph_boundary_residual", 0.0),
            Quantity("fiber_boundary_residual", 0.0),
        ],
        context="matched local nonaffine coupled C3 contact and collar core",
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


def test_predeclared_weight_menu_selection_core_is_dimensionless() -> None:
    assert audit_dimensionless(
        [
            Quantity("normalized_diagonal_weight", 1.1),
            Quantity("weighted_only_robust_delta_lower", 0.12),
            Quantity("minimum_development_advantage", 0.01),
            Quantity("development_advantage", 0.02),
            Quantity("heldout_selected_weight_robust_delta_lower", 0.11),
        ],
        context="predeclared development-only diagonal-weight selection core",
    ).passed


def test_dense_similarity_residual_translation_core_is_dimensionless() -> None:
    assert audit_dimensionless(
        [
            Quantity("similarity_entry", 1.0),
            Quantity("similarity_inverse_entry", 1.0),
            Quantity("transformed_uncertainty", 0.1),
            Quantity("similarity_condition_two_upper", 1.2),
            Quantity("dense_only_robust_delta_lower", 0.05),
            Quantity("normalized_robust_resolvent_upper", 20.0),
        ],
        context="exact dense-similarity residual translation core",
    ).passed


def test_rational_unit_circle_mesh_residual_core_is_dimensionless() -> None:
    assert audit_dimensionless(
        [
            Quantity("unit_direction_dot", 0.8),
            Quantity("unit_direction_cross", 0.6),
            Quantity("maximum_chord_factor", 0.5),
            Quantity("normalized_mesh_chord", 0.5),
            Quantity("normalized_mesh_residual_delta", 0.1),
            Quantity("normalized_mesh_resolvent", 10.0),
        ],
        context="ordered rational unit-circle residual mesh core",
    ).passed


def test_algebraic_riesz_projector_split_core_is_dimensionless() -> None:
    assert audit_dimensionless(
        [
            Quantity("projector_idempotence_residual", 0.0),
            Quantity("commutator_residual", 0.0),
            Quantity("normalized_inside_operator_norm", 1.0),
            Quantity("normalized_radius", 2.0),
            Quantity("normalized_inside_margin", 1.0),
            Quantity("radius_times_exterior_inverse_norm", 0.5),
            Quantity("exterior_reciprocal_margin", 0.5),
            Quantity("projector_rank", 2.0),
        ],
        context="exact algebraic Riesz projector split core",
    ).passed


def test_predeclared_dense_similarity_selection_core_is_dimensionless() -> None:
    assert audit_dimensionless(
        [
            Quantity("normalized_similarity_entry", 1.0),
            Quantity("dense_candidate_score", 0.1),
            Quantity("minimum_dense_development_advantage", 0.01),
            Quantity("dense_development_advantage", 0.02),
            Quantity("heldout_selected_dense_delta", 0.09),
        ],
        context="predeclared development-only dense-similarity menu core",
    ).passed


def test_interval_similarity_residual_core_is_dimensionless_after_spectral_scaling() -> None:
    assert audit_dimensionless(
        [
            Quantity("nominal_similarity_entry", 1.0),
            Quantity("similarity_uncertainty_radius", 0.01),
            Quantity("relative_similarity_contraction", 0.02),
            Quantity("inverse_similarity_envelope", 1.03),
            Quantity("normalized_transformed_uncertainty", 0.1),
            Quantity("uniform_similarity_condition", 1.06),
            Quantity("normalized_interval_similarity_delta", 0.04),
            Quantity("normalized_interval_similarity_resolvent", 25.0),
        ],
        context="supplied interval-valued similarity residual core",
    ).passed


def test_rational_polygon_residual_core_is_dimensionless_after_spectral_scaling() -> None:
    assert audit_dimensionless(
        [
            Quantity("normalized_polygon_vertex", 1.0),
            Quantity("normalized_edge_length", 0.5),
            Quantity("normalized_half_edge_cover", 0.25),
            Quantity("normalized_vertex_sigma_lower", 0.6),
            Quantity("normalized_polygon_delta", 0.35),
            Quantity("normalized_polygon_perimeter", 8.0),
            Quantity("normalized_polygon_resolvent", 20.0 / 7.0),
            Quantity("riesz_projector_perturbation", 0.1),
        ],
        context="simple rational polygonal Jordan residual core",
    ).passed


def test_polygon_riesz_quadrature_core_is_dimensionless() -> None:
    assert audit_dimensionless(
        [
            Quantity("normalized_polygon_midpoint", 1.0),
            Quantity("normalized_edge_resolvent", 2.0),
            Quantity("unscaled_midpoint_quadrature", 6.2),
            Quantity("unscaled_quadrature_error", 0.01),
            Quantity("rational_pi_lower", 3.1415),
            Quantity("inverse_two_pi", 0.1592),
            Quantity("scaled_projector_entry", 1.0),
            Quantity("scaled_projector_error", 0.002),
            Quantity("certified_polygon_rank", 1.0),
        ],
        context="verified polygon midpoint Riesz quadrature core",
    ).passed


def test_adaptive_polygon_riesz_refinement_core_is_dimensionless() -> None:
    assert audit_dimensionless(
        [
            Quantity("edge_quadrature_error", 0.1),
            Quantity("maximum_edge_error", 0.1),
            Quantity("subdivision_multiplier", 2.0),
            Quantity("refinement_round", 3.0),
            Quantity("refinement_budget", 8.0),
            Quantity("possible_rank_count", 1.0),
            Quantity("adaptive_certified_rank", 1.0),
        ],
        context="deterministic fixed-polygon Riesz subdivision refinement core",
    ).passed


def test_rational_affine_ellipse_residual_core_is_dimensionless_after_scaling() -> None:
    assert audit_dimensionless(
        [
            Quantity("normalized_ellipse_center", 0.0),
            Quantity("normalized_ellipse_axis", 2.0),
            Quantity("ellipse_orientation_determinant", 2.0),
            Quantity("ellipse_axis_operator_norm", 2.0),
            Quantity("ellipse_mesh_chord", 0.9),
            Quantity("ellipse_residual_delta", 0.1),
            Quantity("ellipse_resolvent", 10.0),
            Quantity("ellipse_projector_perturbation", 0.2),
        ],
        context="rational affine-ellipse smooth residual contour core",
    ).passed


def test_ellipse_polygon_homotopy_rank_bridge_core_is_dimensionless() -> None:
    assert audit_dimensionless(
        [
            Quantity("normalized_sector_homotopy_cover", 0.9),
            Quantity("normalized_sector_homotopy_margin", 0.1),
            Quantity("inscribed_polygon_rank", 1.0),
            Quantity("smooth_ellipse_rank", 1.0),
            Quantity("ellipse_projector_quadrature_entry", 1.0),
            Quantity("ellipse_projector_operator_error", 0.002),
            Quantity("ellipse_refinement_budget", 8.0),
        ],
        context="ellipse-to-inscribed-polygon verified Riesz-rank homotopy core",
    ).passed


def test_affine_linear_radial_smooth_contour_core_is_dimensionless() -> None:
    assert audit_dimensionless(
        [
            Quantity("radial_base", 1.0),
            Quantity("radial_linear_norm", 0.25),
            Quantity("radial_positivity_margin", 0.75),
            Quantity("radial_lipschitz", 1.5),
            Quantity("normalized_radial_cover", 0.7),
            Quantity("normalized_radial_delta", 0.05),
            Quantity("radial_projector_perturbation", 0.1),
        ],
        context="positive affine-linear radial smooth residual contour core",
    ).passed


def test_radial_polygon_homotopy_rank_bridge_core_is_dimensionless() -> None:
    assert audit_dimensionless(
        [
            Quantity("normalized_radial_sector_cover", 0.7),
            Quantity("normalized_radial_homotopy_margin", 0.05),
            Quantity("inscribed_radial_polygon_rank", 1.0),
            Quantity("smooth_radial_rank", 1.0),
            Quantity("radial_projector_quadrature_entry", 1.0),
            Quantity("radial_projector_operator_error", 0.002),
            Quantity("radial_refinement_budget", 8.0),
        ],
        context="radial-to-inscribed-polygon verified Riesz-rank homotopy core",
    ).passed


def test_polynomial_radial_rank_bridge_core_is_dimensionless() -> None:
    assert audit_dimensionless(
        [
            Quantity("polynomial_radial_base", 1.0),
            Quantity("polynomial_linear_norm", 0.2),
            Quantity("higher_radial_amplitude", 0.1),
            Quantity("higher_radial_gradient", 0.2),
            Quantity("polynomial_radial_lipschitz", 1.5),
            Quantity("normalized_polynomial_cover", 0.6),
            Quantity("normalized_polynomial_delta", 0.1),
            Quantity("polynomial_radial_rank", 1.0),
            Quantity("polynomial_projector_error", 0.002),
        ],
        context="finite polynomial radial residual and polygon-rank bridge core",
    ).passed


def test_piecewise_polynomial_radial_spline_core_is_dimensionless() -> None:
    assert audit_dimensionless(
        [
            Quantity("spline_junction_order", 2.0),
            Quantity("spline_knot_derivative_value", 0.0),
            Quantity("spline_patch_positivity", 0.8),
            Quantity("spline_patch_lipschitz", 1.4),
            Quantity("normalized_spline_cover", 0.6),
            Quantity("normalized_spline_delta", 0.1),
            Quantity("spline_numeric_rank", 1.0),
            Quantity("spline_projector_error", 0.002),
        ],
        context="periodic piecewise-polynomial radial Cq spline rank bridge core",
    ).passed


def test_piecewise_rational_radial_spline_core_is_dimensionless() -> None:
    assert audit_dimensionless(
        [
            Quantity("rational_spline_numerator_lower", 0.8),
            Quantity("rational_spline_numerator_upper", 1.2),
            Quantity("rational_spline_denominator_lower", 0.7),
            Quantity("rational_spline_denominator_upper", 1.3),
            Quantity("rational_spline_quotient_jet", 0.0),
            Quantity("rational_spline_lipschitz", 2.0),
            Quantity("normalized_rational_spline_cover", 0.6),
            Quantity("rational_spline_numeric_rank", 1.0),
            Quantity("rational_spline_projector_error", 0.002),
        ],
        context="pole-free piecewise-rational radial Cq spline rank bridge core",
    ).passed


def test_predeclared_rational_contour_selection_core_is_dimensionless() -> None:
    assert audit_dimensionless(
        [
            Quantity("contour_menu_size", 3.0),
            Quantity("development_contour_score", 0.3),
            Quantity("development_contour_advantage", 0.1),
            Quantity("minimum_contour_advantage", 0.05),
            Quantity("heldout_contour_delta", 0.2),
            Quantity("development_contour_rank", 1.0),
            Quantity("heldout_contour_rank", 1.0),
        ],
        context="predeclared finite rational contour selection core",
    ).passed


def test_polynomial_spectral_projector_construction_core_is_dimensionless() -> None:
    assert audit_dimensionless(
        [
            Quantity("inside_factor_coefficient", 1.0),
            Quantity("outside_factor_coefficient", -4.0),
            Quantity("bezout_coefficient", 0.25),
            Quantity("projector_entry", 1.0),
            Quantity("complement_entry", 0.0),
            Quantity("normalized_center", 0.0),
            Quantity("normalized_radius", 2.0),
            Quantity("exterior_inverse_entry", 0.25),
            Quantity("constructed_projector_rank", 1.0),
        ],
        context="coprime polynomial spectral projector construction core",
    ).passed


def test_characteristic_spectral_split_discovery_core_is_dimensionless() -> None:
    assert audit_dimensionless(
        [
            Quantity("characteristic_coefficient", -4.0),
            Quantity("rational_spectral_root", 4.0),
            Quantity("root_multiplicity", 2.0),
            Quantity("residual_factor_degree", 2.0),
            Quantity("spectral_atom_count", 3.0),
            Quantity("partition_budget", 16.0),
            Quantity("partitions_evaluated", 8.0),
            Quantity("discovered_projector_rank", 1.0),
        ],
        context="exact characteristic spectral split discovery core",
    ).passed


def test_complete_q_polynomial_factorization_core_is_dimensionless() -> None:
    assert audit_dimensionless(
        [
            Quantity("primitive_polynomial_coefficient", 81.0),
            Quantity("trial_factor_degree", 4.0),
            Quantity("evaluation_point", -2.0),
            Quantity("factor_value_divisor", 5.0),
            Quantity("candidate_value_tuple_budget", 1024.0),
            Quantity("candidate_value_tuples_examined", 680.0),
            Quantity("irreducible_factor_multiplicity", 3.0),
            Quantity("spectral_primary_atom_count", 2.0),
        ],
        context="Gauss-Kronecker complete exact Q polynomial factorization core",
    ).passed


def test_gaussian_rational_real_characteristic_envelope_core_is_dimensionless() -> None:
    assert audit_dimensionless(
        [
            Quantity("real_part_of_normalized_entry", 0.0),
            Quantity("imaginary_part_of_normalized_entry", 3.0),
            Quantity("real_center", 0.0),
            Quantity("normalized_complex_center_imaginary_part", 1.0),
            Quantity("center_shifted_entry", 2.0),
            Quantity("normalized_radius", 2.0),
            Quantity("realification_block_entry", -3.0),
            Quantity("real_envelope_coefficient", 10.0),
            Quantity("envelope_primary_atom_count", 2.0),
            Quantity("original_complex_projector_rank", 1.0),
        ],
        context="Gaussian-rational real characteristic envelope spectral split core",
    ).passed


def test_interval_characteristic_spectral_split_core_is_dimensionless() -> None:
    assert audit_dimensionless(
        [
            Quantity("normalized_rectangular_uncertainty_squared", 0.0005),
            Quantity("normalized_uncertainty_upper", 0.023),
            Quantity("normalized_nominal_contour_delta_lower", 0.4),
            Quantity("normalized_robust_contour_delta_lower", 0.377),
            Quantity("normalized_projector_perturbation_upper", 0.31),
            Quantity("homotopy_parameter", 0.5),
            Quantity("nominal_projector_rank", 1.0),
            Quantity("family_projector_rank", 1.0),
        ],
        context="automatic nominal characteristic split to interval family rank bridge core",
    ).passed


def test_continuous_circle_spectral_margin_optimization_core_is_dimensionless() -> None:
    assert audit_dimensionless(
        [
            Quantity("normalized_center_real", 0.0),
            Quantity("normalized_center_imaginary", 0.0),
            Quantity("normalized_radius", 2.0),
            Quantity("normalized_eigenvalue_real", 4.0),
            Quantity("normalized_signed_squared_margin", 4.0),
            Quantity("normalized_cell_variation_upper", 0.125),
            Quantity("normalized_global_score_upper", 4.1),
            Quantity("normalized_optimality_tolerance", 0.1),
            Quantity("branch_cell_count", 127.0),
            Quantity("selected_projector_rank", 1.0),
        ],
        context="continuous circle signed spectral margin branch-and-bound core",
    ).passed


def test_continuous_algebraic_circle_margin_optimization_core_is_dimensionless() -> None:
    assert audit_dimensionless(
        [
            Quantity("normalized_reference_center", 0.0),
            Quantity("normalized_reference_radius", 2.0),
            Quantity("normalized_center_displacement_upper", 0.5),
            Quantity("projector_frobenius_upper", 1.5),
            Quantity("exterior_inverse_frobenius_upper", 0.2),
            Quantity("inside_frobenius_squared", 1.0),
            Quantity("exterior_inverse_frobenius_squared", 0.04),
            Quantity("normalized_algebraic_margin", 0.84),
            Quantity("normalized_optimality_gap", 0.1),
            Quantity("selected_projector_rank", 2.0),
        ],
        context="continuous no-diagonalization algebraic circle margin core",
    ).passed


def test_continuous_axis_aligned_ellipse_margin_optimization_core_is_dimensionless() -> None:
    assert audit_dimensionless(
        [
            Quantity("normalized_ellipse_center_real", 0.0),
            Quantity("normalized_ellipse_center_imaginary", 0.0),
            Quantity("rational_orientation_component", 0.8),
            Quantity("normalized_semiaxis_u", 2.0),
            Quantity("normalized_semiaxis_v", 1.0),
            Quantity("normalized_rotated_spectral_coordinate", 0.5),
            Quantity("normalized_quartic_ellipse_margin", 3.0),
            Quantity("normalized_quartic_cell_upper", 3.1),
            Quantity("normalized_quartic_optimality_tolerance", 0.1),
            Quantity("ellipse_branch_cell_count", 255.0),
            Quantity("ellipse_selected_projector_rank", 1.0),
        ],
        context="continuous fixed-orientation ellipse quartic spectral margin core",
    ).passed


def test_continuous_stereographic_ellipse_margin_core_is_dimensionless() -> None:
    assert audit_dimensionless(
        [
            Quantity("stereographic_orientation_parameter", 0.5),
            Quantity("stereographic_orientation_denominator", 1.25),
            Quantity("rational_orientation_unit_component", 0.6),
            Quantity("normalized_stereographic_semiaxis_u", 2.0),
            Quantity("normalized_stereographic_semiaxis_v", 1.0),
            Quantity("normalized_orientation_invariant_margin", 3.0),
            Quantity("normalized_orientation_cell_upper", 3.1),
            Quantity("normalized_orientation_optimality_tolerance", 0.1),
            Quantity("orientation_branch_cell_count", 511.0),
            Quantity("orientation_selected_projector_rank", 1.0),
        ],
        context="continuous stereographic-orientation ellipse margin core",
    ).passed


def test_continuous_general_affine_ellipse_margin_core_is_dimensionless() -> None:
    assert audit_dimensionless(
        [
            Quantity("general_affine_orientation_parameter", 0.5),
            Quantity("normalized_general_affine_semiaxis_u", 2.0),
            Quantity("normalized_general_affine_semiaxis_v", 1.0),
            Quantity("normalized_general_affine_shear", 0.3),
            Quantity("normalized_affine_axis_determinant", 2.0),
            Quantity("normalized_affine_inverse_coordinate", 0.4),
            Quantity("normalized_affine_ellipse_margin", 3.0),
            Quantity("normalized_affine_cell_upper", 3.1),
            Quantity("normalized_affine_optimality_tolerance", 0.1),
            Quantity("affine_selected_projector_rank", 1.0),
        ],
        context="continuous general-affine ellipse QR/shear margin core",
    ).passed


def test_continuous_periodic_spline_knot_core_is_dimensionless() -> None:
    assert audit_dimensionless(
        [
            Quantity("stereographic_knot_parameter", -1.0),
            Quantity("spline_junction_order", 3.0),
            Quantity("automatic_vanishing_exponent", 4.0),
            Quantity("radial_patch_amplitude", 0.01),
            Quantity("minimum_knot_spacing_score", 2.0),
            Quantity("maximum_endpoint_chord_squared", 2.0),
            Quantity("radial_spline_lipschitz_upper", 1.8),
            Quantity("normalized_spline_cover_chord", 0.4),
            Quantity("normalized_knot_optimality_tolerance", 0.1),
            Quantity("knot_branch_cell_count", 511.0),
        ],
        context="continuous automatic-Cq periodic spline knot-spacing core",
    ).passed


def test_moving_knot_spline_spectral_rank_bridge_core_is_dimensionless() -> None:
    assert audit_dimensionless(
        [
            Quantity("normalized_affine_inverse_coordinate_squared", 9.0),
            Quantity("uniform_radial_minimum", 1.0),
            Quantity("uniform_radial_maximum", 1.16),
            Quantity("uniform_inside_squared_margin", 1.0),
            Quantity("uniform_outside_squared_margin", 7.65),
            Quantity("affine_minimum_singular_value_squared_lower", 0.5),
            Quantity("normalized_contour_distance_squared_lower", 0.25),
            Quantity("eigenvector_frobenius_condition_squared_upper", 4.0),
            Quantity("normalized_resolvent_norm_upper", 4.0),
            Quantity("moving_knot_family_rank", 1.0),
            Quantity("knot_box_member_parameter", 0.5),
            Quantity("homotopy_parameter", 0.5),
        ],
        context="moving-knot spline quantitative spectral split and rank bridge core",
    ).passed


def test_interval_moving_knot_neumann_and_projector_core_is_dimensionless() -> None:
    assert audit_dimensionless(
        [
            Quantity("normalized_matrix_uncertainty_frobenius_upper", 0.125),
            Quantity("normalized_nominal_resolvent_norm_upper", 4.0),
            Quantity("neumann_product_upper", 0.5),
            Quantity("neumann_margin_lower", 0.5),
            Quantity("normalized_perturbed_resolvent_norm_upper", 8.0),
            Quantity("normalized_contour_length_over_two_pi_upper", 2.0),
            Quantity("interval_projector_perturbation_norm_upper", 8.0),
            Quantity("interval_family_rank", 1.0),
        ],
        context="interval moving-knot Neumann rank and projector bridge core",
    ).passed


def test_defective_conformal_moving_knot_algebraic_core_is_dimensionless() -> None:
    assert audit_dimensionless(
        [
            Quantity("normalized_conformal_scale", 2.0),
            Quantity("uniform_inner_radius_lower", 2.0),
            Quantity("uniform_outer_radius_upper", 2.32),
            Quantity("inside_block_norm_upper", 1.0),
            Quantity("exterior_inverse_norm_upper", 0.25),
            Quantity("inside_algebraic_gap_lower", 1.0),
            Quantity("exterior_reciprocal_gap_lower", 0.42),
            Quantity("algebraic_uniform_resolvent_norm_upper", 2.0),
            Quantity("defective_projector_rank", 2.0),
        ],
        context="defective conformal moving-knot algebraic spectral core",
    ).passed


def test_interval_defective_conformal_neumann_core_is_dimensionless() -> None:
    assert audit_dimensionless(
        [
            Quantity("normalized_defective_uncertainty", 0.25),
            Quantity("algebraic_resolvent_upper", 1.6),
            Quantity("defective_neumann_product", 0.4),
            Quantity("defective_neumann_margin", 0.6),
            Quantity("perturbed_algebraic_resolvent_upper", 2.7),
            Quantity("defective_interval_projector_bound", 2.0),
            Quantity("defective_interval_rank", 2.0),
        ],
        context="interval defective conformal moving-knot Neumann core",
    ).passed


def test_automatic_defective_characteristic_discovery_core_is_dimensionless() -> None:
    assert audit_dimensionless(
        [
            Quantity("normalized_reference_radius", 2.16),
            Quantity("characteristic_factor_degree", 2.0),
            Quantity("bezout_identity_residual", 0.0),
            Quantity("automatic_projector_rank", 2.0),
            Quantity("factor_partition_count", 2.0),
            Quantity("automatic_defective_resolvent_upper", 1.6),
        ],
        context="automatic defective characteristic projector discovery core",
    ).passed


def test_defective_general_affine_singular_sandwich_core_is_dimensionless() -> None:
    assert audit_dimensionless(
        [
            Quantity("affine_determinant", 8.0),
            Quantity("affine_frobenius_squared", 24.0),
            Quantity("affine_minimum_singular_squared_lower", 8.0 / 3.0),
            Quantity("uniform_affine_inner_radius_lower", 1.6),
            Quantity("uniform_affine_outer_radius_upper", 5.7),
            Quantity("general_affine_inside_gap", 0.6),
            Quantity("general_affine_exterior_gap", 0.3),
            Quantity("general_affine_defective_rank", 2.0),
        ],
        context="defective general-affine moving-knot singular sandwich core",
    ).passed


def test_automatic_interval_defective_general_affine_core_is_dimensionless() -> None:
    assert audit_dimensionless(
        [
            Quantity("automatic_affine_reference_radius", 3.7),
            Quantity("automatic_shear_projector_rank", 2.0),
            Quantity("normalized_shear_uncertainty", 0.0625),
            Quantity("shear_neumann_product", 0.2),
            Quantity("shear_neumann_margin", 0.8),
            Quantity("perturbed_shear_resolvent", 2.0),
            Quantity("shear_interval_projector_bound", 1.0),
        ],
        context="automatic interval defective general-affine moving-knot core",
    ).passed


def test_continuous_spline_amplitude_box_optimization_core_is_dimensionless() -> None:
    assert audit_dimensionless(
        [
            Quantity("amplitude_radial_cap", 1.32),
            Quantity("per_patch_amplitude_cap", 0.02),
            Quantity("total_amplitude_objective", 0.07),
            Quantity("amplitude_box_radial_gradient", 0.64),
            Quantity("amplitude_box_radial_lipschitz", 1.96),
            Quantity("amplitude_box_cell_count", 4.0),
        ],
        context="continuous automatic-Cq spline amplitude box optimization core",
    ).passed


def test_spectral_spline_amplitude_optimization_core_is_dimensionless() -> None:
    assert audit_dimensionless(
        [
            Quantity("outside_affine_radius_lower", 3.0),
            Quantity("radial_safety_margin", 0.5),
            Quantity("spectral_derived_radial_cap", 2.0),
            Quantity("spectral_amplitude_cap", 0.0625),
            Quantity("spectral_total_amplitude_objective", 0.25),
            Quantity("spectral_amplitude_rank", 1.0),
            Quantity("spectral_amplitude_resolvent_upper", 4.0),
        ],
        context="spectral-derived moving-knot spline amplitude optimization core",
    ).passed


def test_defective_algebraic_spline_amplitude_optimization_core_is_dimensionless() -> None:
    assert audit_dimensionless(
        [
            Quantity("algebraic_exterior_safety", 0.25),
            Quantity("algebraic_amplitude_radial_cap", 1.2),
            Quantity("defective_total_amplitude_objective", 0.05),
            Quantity("defective_amplitude_resolvent", 2.0),
            Quantity("defective_amplitude_uncertainty", 0.01),
            Quantity("defective_amplitude_neumann_margin", 0.98),
            Quantity("defective_amplitude_projector_bound", 0.1),
            Quantity("defective_amplitude_rank", 2.0),
        ],
        context="defective algebraic shear spline amplitude optimization core",
    ).passed


def test_direct_interval_coordinate_block_factor_core_is_dimensionless() -> None:
    assert audit_dimensionless(
        [
            Quantity("normalized_inside_factor_degree", 2.0),
            Quantity("normalized_outside_factor_degree", 1.0),
            Quantity("normalized_factor_real_lower", -0.1),
            Quantity("normalized_factor_real_upper", 0.1),
            Quantity("normalized_factor_imaginary_lower", -1.05),
            Quantity("normalized_factor_imaginary_upper", -0.95),
            Quantity("determinant_term_count", 10.0),
            Quantity("interval_family_projector_rank", 2.0),
        ],
        context="direct interval coordinate-block characteristic-factor core",
    ).passed


def test_continuous_spline_general_coefficient_optimization_core_is_dimensionless() -> None:
    assert audit_dimensionless(
        [
            Quantity("spline_basis_power", 3.0),
            Quantity("coefficient_box_upper", 0.01),
            Quantity("basis_radial_weight", 64.0),
            Quantity("basis_gradient_weight", 192.0),
            Quantity("patch_radial_capacity", 0.72),
            Quantity("weighted_coefficient_objective", 0.34),
            Quantity("automatic_junction_order", 1.0),
        ],
        context="continuous automatic-Cq general spline coefficient optimization core",
    ).passed


def test_split_conformal_matrix_uncertainty_coverage_core_is_dimensionless() -> None:
    assert audit_dimensionless(
        [
            Quantity("calibration_max_score", 1.8),
            Quantity("conformal_order_index", 18.0),
            Quantity("simultaneous_coverage_lower", 0.9),
            Quantity("normalized_component_radius", 0.009),
            Quantity("heldout_coverage_fraction", 1.0),
            Quantity("undercoverage_audit_p_upper", 0.011529),
        ],
        context="split conformal simultaneous matrix uncertainty coverage core",
    ).passed


def test_conformal_interval_characteristic_bridge_core_is_dimensionless() -> None:
    assert audit_dimensionless(
        [
            Quantity("normalized_conformal_radius", 0.009),
            Quantity("interval_contour_radius", 2.0),
            Quantity("conditional_family_rank", 1.0),
            Quantity("coverage_probability_lower", 0.9),
        ],
        context="conformal interval characteristic rank bridge core",
    ).passed


def test_conscious_moment_dimension_stability_core_is_dimensionless() -> None:
    assert audit_dimensionless(
        [
            Quantity("candidate_signal_rank", 5.0),
            Quantity("band_window_fraction", 1.0),
            Quantity("selected_rank_window_fraction", 0.6),
            Quantity("rank_transition_fraction", 5.0 / 9.0),
            Quantity("selected_rank_longest_dwell_fraction", 0.3),
            Quantity("control_band_fraction", 0.0),
            Quantity("bootstrap_band_fraction", 1.0),
            Quantity("bootstrap_selected_fraction", 0.9),
            Quantity("frozen_block_length", 2.0),
        ],
        context="candidate 4--6 temporal and block-bootstrap signal-rank stability core",
    ).passed


def test_dimension_time_series_execution_core_is_dimensionless() -> None:
    assert audit_dimensionless(
        [
            Quantity("ambient_signal_coordinate_count", 12.0),
            Quantity("projector_trace_rank", 5.0),
            Quantity("heldout_reconstruction_score", -2.5),
            Quantity("rank_complexity_penalty", 0.5),
            Quantity("moving_block_length", 2.0),
            Quantity("window_selected_rank", 5.0),
            Quantity("bootstrap_selected_rank", 5.0),
        ],
        context="exact heldout time-series dimension and moving-block execution core",
    ).passed


def test_dimension_projector_training_execution_core_is_dimensionless() -> None:
    assert audit_dimensionless(
        [
            Quantity("development_observation_count", 24.0),
            Quantity("development_covariance_eigenvalue", 12.0),
            Quantity("eigenbasis_norm_squared", 1.0),
            Quantity("projector_idempotence_residual", 0.0),
            Quantity("prefix_projector_rank", 5.0),
            Quantity("heldout_selected_rank", 5.0),
        ],
        context="exact development covariance PCA and heldout dimension execution core",
    ).passed


def test_dimension_preprocessing_execution_core_is_dimensionless() -> None:
    assert audit_dimensionless(
        [
            Quantity("raw_coordinate_reference_scale", 7.0),
            Quantity("development_coordinate_mean", 20.0),
            Quantity("normalized_development_sum", 0.0),
            Quantity("normalized_heldout_signal_coordinate", 1.0),
            Quantity("preprocessed_selected_rank", 5.0),
            Quantity("heldout_reestimated_statistic_count", 0.0),
        ],
        context="development-only dimension preprocessing execution core",
    ).passed


def test_dimension_observation_manifest_core_is_dimensionless() -> None:
    assert audit_dimensionless(
        [
            Quantity("canonical_observation_id_count", 144.0),
            Quantity("development_heldout_overlap_count", 0.0),
            Quantity("payload_hash_match_indicator", 1.0),
            Quantity("immutable_split_indicator", 1.0),
            Quantity("content_addressed_chain_indicator", 1.0),
            Quantity("external_source_signature_indicator", 0.0),
        ],
        context="content-addressed dimension observation manifest core",
    ).passed


def test_dimension_source_bytes_receipt_core_is_dimensionless() -> None:
    assert audit_dimensionless(
        [
            Quantity("canonical_archive_domain_count", 6.0),
            Quantity("archive_bundle_hash_match_indicator", 1.0),
            Quantity("archive_session_mismatch_count", 0.0),
            Quantity("archive_contract_mismatch_count", 0.0),
            Quantity("canonical_byte_roundtrip_indicator", 1.0),
            Quantity("external_acquisition_signature_indicator", 0.0),
        ],
        context="canonical dimension source archive bytes receipt core",
    ).passed


def test_dimension_signed_acquisition_receipt_core_is_dimensionless() -> None:
    assert audit_dimensionless(
        [
            Quantity("ed25519_scalar_to_group_order_ratio", 0.5),
            Quantity("public_key_fingerprint_match_indicator", 1.0),
            Quantity("detached_signature_equation_indicator", 1.0),
            Quantity("signed_bundle_domain_count", 6.0),
            Quantity("externally_frozen_trust_anchor_indicator", 0.0),
            Quantity("device_native_converter_receipt_indicator", 0.0),
        ],
        context="strict Ed25519 signed dimension acquisition bundle core",
    ).passed


def test_edge_metric_to_effective_dimension_bridge_core_is_dimensionless() -> None:
    assert audit_dimensionless(
        [
            Quantity("normalized_edge_weight", 0.75),
            Quantity("normalized_metric_eigenvalue", 2.0),
            Quantity("normalized_observed_gram_eigenvalue", 0.5),
            Quantity("normalized_ridge_parameter", 0.1),
            Quantity("ridge_effective_dimension", 5.0),
            Quantity("ridge_dimension_edge_derivative", -0.4),
            Quantity("robust_candidate_band_lower", 4.0),
            Quantity("robust_candidate_band_upper", 6.0),
        ],
        context="positive edge metric to observed ridge effective dimension bridge core",
    ).passed


def test_edge_noise_effective_dimension_bridge_core_is_dimensionless() -> None:
    assert audit_dimensionless(
        [
            Quantity("normalized_forcing_covariance_eigenvalue", 1.9),
            Quantity("normalized_response_covariance_eigenvalue", 0.5),
            Quantity("edge_noise_commutator_residual", 0.0),
            Quantity("noise_aware_ridge_effective_dimension", 4.5),
            Quantity("commuting_edge_dimension_derivative", -0.8),
            Quantity("noncommuting_edge_dimension_derivative", 0.1),
            Quantity("noise_robust_candidate_band_lower", 4.0),
            Quantity("noise_robust_candidate_band_upper", 6.0),
        ],
        context="commuting and noncommuting edge forcing-noise dimension bridge core",
    ).passed


def test_edge_disconnection_spectral_rank_core_is_dimensionless() -> None:
    assert audit_dimensionless(
        [
            Quantity("normalized_coupling_parameter", 1.0),
            Quantity("normalized_fixed_contour_radius", 2.0),
            Quantity("normalized_disconnected_spectral_gap", 1.72),
            Quantity("normalized_coupling_frobenius_squared", 1.8432),
            Quantity("normalized_robust_gap_squared", 1.1152),
            Quantity("connected_component_count", 6.0),
            Quantity("disconnected_component_count", 7.0),
            Quantity("fixed_contour_spectral_rank", 6.0),
        ],
        context="topological edge disconnection and fixed-contour spectral rank core",
    ).passed


def test_nonnormal_edge_disconnection_spectral_rank_core_is_dimensionless() -> None:
    assert audit_dimensionless(
        [
            Quantity("nonnormal_eigenvector_condition_upper", 8.0),
            Quantity("normalized_circle_spectral_gap", 0.25),
            Quantity("normalized_resolvent_upper", 32.0),
            Quantity("normalized_directed_coupling_norm_upper", 0.01),
            Quantity("nonnormal_neumann_product", 0.32),
            Quantity("nonnormal_neumann_margin", 0.68),
            Quantity("riesz_projector_movement_upper", 256.0 / 17.0),
            Quantity("fixed_circle_algebraic_rank", 6.0),
        ],
        context="diagonalizable nonnormal directed-edge disconnection resolvent core",
    ).passed


def test_defective_edge_disconnection_spectral_rank_core_is_dimensionless() -> None:
    assert audit_dimensionless(
        [
            Quantity("algebraic_inside_gap_lower", 1.0),
            Quantity("algebraic_exterior_reciprocal_gap_lower", 0.5),
            Quantity("algebraic_projector_norm_upper", 1.0),
            Quantity("defective_resolvent_norm_upper", 1.5),
            Quantity("defective_directed_coupling_upper", 0.01),
            Quantity("defective_neumann_product", 0.015),
            Quantity("defective_neumann_margin", 0.985),
            Quantity("defective_fixed_circle_rank", 6.0),
        ],
        context="defective algebraic Riesz directed-edge disconnection core",
    ).passed


def test_interval_defective_edge_disconnection_spectral_rank_core_is_dimensionless() -> None:
    assert audit_dimensionless(
        [
            Quantity("normalized_baseline_operator_uncertainty", 0.005),
            Quantity("normalized_nominal_directed_coupling", 0.01),
            Quantity("normalized_coupling_uncertainty", 0.002),
            Quantity("normalized_total_family_perturbation", 0.017),
            Quantity("interval_defective_neumann_product", 0.0255),
            Quantity("interval_defective_neumann_margin", 0.9745),
            Quantity("interval_projector_movement_upper", 153.0 / 1949.0),
            Quantity("interval_fixed_circle_rank", 6.0),
        ],
        context="interval defective directed-edge disconnection robustness core",
    ).passed


def test_conformal_interval_defective_edge_rank_core_is_dimensionless() -> None:
    assert audit_dimensionless(
        [
            Quantity("split_conformal_miscoverage_alpha", 0.1),
            Quantity("split_conformal_order_ratio", 0.9),
            Quantity("simultaneous_score_threshold", 1.0),
            Quantity("conditional_simultaneous_coverage_lower", 0.9),
            Quantity("conformal_baseline_radius", 0.005),
            Quantity("conformal_coupling_radius", 0.002),
            Quantity("conformal_interval_neumann_product", 0.0255),
            Quantity("conditional_rank_six_indicator", 1.0),
        ],
        context="split-conformal interval defective directed-edge rank composition core",
    ).passed


def test_signed_conformal_interval_defective_edge_rank_core_is_dimensionless() -> None:
    assert audit_dimensionless(
        [
            Quantity("canonical_calibration_content_hash_match", 1.0),
            Quantity("canonical_heldout_content_hash_match", 1.0),
            Quantity("coverage_contract_hash_match", 1.0),
            Quantity("signer_key_fingerprint_match", 1.0),
            Quantity("strict_ed25519_signature_indicator", 1.0),
            Quantity("signed_conditional_rank_coverage_lower", 0.9),
            Quantity("externally_frozen_trust_anchor_indicator", 0.0),
            Quantity("source_locked_empirical_rank_indicator", 0.0),
        ],
        context="signed canonical conformal interval defective edge-rank bundle core",
    ).passed


def test_cidisc_trust_converter_receipt_core_is_dimensionless() -> None:
    assert audit_dimensionless(
        [
            Quantity("trust_anchor_validity_window_indicator", 1.0),
            Quantity("root_key_fingerprint_match_indicator", 1.0),
            Quantity("root_authorization_signature_indicator", 1.0),
            Quantity("coverage_key_certificate_match_indicator", 1.0),
            Quantity("converter_content_signature_indicator", 1.0),
            Quantity("two_signature_content_chain_indicator", 1.0),
            Quantity("external_root_distribution_indicator", 0.0),
            Quantity("hardware_converter_execution_attestation_indicator", 0.0),
        ],
        context="CIDISC institutional trust and native converter content receipt core",
    ).passed
