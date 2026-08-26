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
_load("verified_interval_contour", "verified_interval_contour.py")
_load("verified_interval_tightening", "verified_interval_tightening.py")
_load("verified_interval_residual", "verified_interval_residual.py")
_load("verified_rational_polygon_residual", "verified_rational_polygon_residual.py")
_load("verified_polygon_riesz_quadrature", "verified_polygon_riesz_quadrature.py")
M = _load("ce_verified_adaptive_polygon", "verified_adaptive_polygon_riesz.py")


SQUARE = ((-1, -1), (1, -1), (1, 1), (-1, 1))


def _run(**overrides):
    values = dict(
        nominal_transition=((0,),),
        uncertainty_radii=(((0, 0),),),
        vertices=SQUARE,
        spectral_reference_scale=1,
        initial_subdivisions=1,
        maximum_refinements=8,
        strategy="UNIFORM",
        subdivision_multiplier=2,
        sqrt_precision=48,
        machin_terms=8,
    )
    values.update(overrides)
    return M.verified_adaptive_polygon_midpoint_riesz_rank(**values)


def test_uniform_refinement_resolves_a_coarse_rank_ambiguity() -> None:
    result = _run()
    assert result.validation_level == "VERIFIED_ADAPTIVE_RATIONAL_POLYGON_RIESZ_RANK"
    assert result.certified_nominal_rank == 1
    assert result.family_rank_verified
    assert len(result.rounds) > 1
    assert not result.rounds[0].quadrature.nominal_rank_verified
    assert result.rounds[-1].quadrature.nominal_rank_verified
    assert result.rounds[-1].refined_edges_after_round == ()
    for previous, current in zip(result.rounds, result.rounds[1:]):
        assert current.subdivisions == tuple(2 * value for value in previous.subdivisions)


def test_zero_refinement_budget_preserves_unresolved_status() -> None:
    result = _run(maximum_refinements=0)
    assert result.status == "ADAPTIVE_RATIONAL_POLYGON_RIESZ_REFINEMENT_EXHAUSTED"
    assert result.validation_level is None
    assert result.refinement_budget_exhausted
    assert len(result.rounds) == 1
    assert result.certified_nominal_rank is None


def test_max_error_ties_refines_only_the_current_largest_error_edges() -> None:
    result = _run(
        initial_subdivisions=(1, 2, 4, 8),
        strategy="MAX_ERROR_TIES",
        maximum_refinements=1,
    )
    assert result.rounds[0].refined_edges_after_round == (0,)
    assert result.rounds[1].subdivisions == (2, 2, 4, 8)


def test_all_exact_error_ties_are_refined_together() -> None:
    result = _run(strategy="MAX_ERROR_TIES", maximum_refinements=1)
    assert result.rounds[0].refined_edges_after_round == (0, 1, 2, 3)


def test_refinement_receipt_is_deterministic() -> None:
    first = _run(strategy="MAX_ERROR_TIES")
    second = _run(strategy="MAX_ERROR_TIES")
    assert first == second


def test_interval_family_inherits_the_adaptively_resolved_rank() -> None:
    result = _run(uncertainty_radii=(((F(1, 10), 0),),))
    assert result.certified_nominal_rank == 1
    assert result.family_rank_verified
    assert result.final_quadrature.polygon_certificate.rank_preserved_for_entire_family


def test_nonbinary_multiplier_is_applied_exactly() -> None:
    result = _run(subdivision_multiplier=3)
    for previous, current in zip(result.rounds, result.rounds[1:]):
        assert current.subdivisions == tuple(3 * value for value in previous.subdivisions)


def test_raw_scale_covariance_preserves_every_refinement_receipt() -> None:
    base = _run()
    scaled_vertices = tuple((7 * x, 7 * y) for x, y in SQUARE)
    scaled = _run(vertices=scaled_vertices, spectral_reference_scale=7)
    assert tuple(round_.subdivisions for round_ in scaled.rounds) == tuple(
        round_.subdivisions for round_ in base.rounds
    )
    assert tuple(round_.quadrature.possible_ranks for round_ in scaled.rounds) == tuple(
        round_.quadrature.possible_ranks for round_ in base.rounds
    )
    assert scaled.certified_nominal_rank == base.certified_nominal_rank


@pytest.mark.parametrize("maximum_refinements", [-1, True, 1.0])
def test_invalid_refinement_budget_fails_closed(maximum_refinements: object) -> None:
    with pytest.raises(ValueError, match="maximum_refinements"):
        _run(maximum_refinements=maximum_refinements)


@pytest.mark.parametrize("multiplier", [0, 1, True, 2.0])
def test_invalid_multiplier_fails_closed(multiplier: object) -> None:
    with pytest.raises(ValueError, match="subdivision_multiplier"):
        _run(subdivision_multiplier=multiplier)


def test_unknown_strategy_fails_closed() -> None:
    with pytest.raises(ValueError, match="strategy"):
        _run(strategy="LOOK_AT_THE_DATA")


def test_honesty_flags_keep_geometry_and_empirical_claims_separate() -> None:
    result = _run()
    assert result.deterministic_refinement_verified
    assert result.polygon_geometry_held_fixed
    assert not result.empirical_matrix_provenance_verified
    assert not result.data_dependent_contour_discovery_used
