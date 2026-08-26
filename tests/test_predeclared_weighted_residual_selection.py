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


R = _load("verified_rational_contour", "verified_rational_contour.py")
_load("verified_interval_contour", "verified_interval_contour.py")
_load("verified_interval_tightening", "verified_interval_tightening.py")
_load("verified_interval_residual", "verified_interval_residual.py")
_load("verified_weighted_interval_residual", "verified_weighted_interval_residual.py")
M = _load("ce_predeclared_weighted_residual_selection", "predeclared_weighted_residual_selection.py")


def _exact_node_inverses(matrix, *, center=0, radius=1):
    u = R._matrix(matrix, "matrix")
    center_q = R.parse_qcomplex(center)
    radius_q = R._fraction(radius, "radius")
    directions = (R.ONE, R.QComplex(0, 1), R.QComplex(-1), R.QComplex(0, -1))
    witnesses = []
    for direction in directions:
        node_value = center_q + radius_q * direction
        node = tuple(
            tuple((node_value if i == j else R.ZERO) - u[i][j] for j in range(len(u)))
            for i in range(len(u))
        )
        inverse = R._inverse(node)
        assert inverse is not None
        witnesses.append(inverse)
    return tuple(witnesses)


def _menu():
    return M.predeclared_diagonal_weight_menu(
        dimension=2,
        candidate_weights_by_id={
            "balanced": (1, 1),
            "first11": (F(11, 10), 1),
            "second11": (1, F(11, 10)),
        },
    )


def _selection(**overrides):
    matrix = overrides.pop("nominal_transition", ((0, 1), (0, 5)))
    witnesses = _exact_node_inverses(matrix)
    development_radii = overrides.pop(
        "development_uncertainty_radii",
        (((F(1, 100), 0), (0, 0)), ((0, 0), (0, 0))),
    )
    heldout_radii = overrides.pop("heldout_uncertainty_radii", development_radii)
    values = dict(
        menu=_menu(),
        nominal_transition=matrix,
        development_uncertainty_radii=development_radii,
        development_approximate_inverses=witnesses,
        heldout_uncertainty_radii=heldout_radii,
        heldout_approximate_inverses=witnesses,
        center=0,
        radius=1,
        spectral_reference_scale=1,
        minimum_development_advantage=0,
        sqrt_precision=40,
    )
    values.update(overrides)
    return M.predeclared_weighted_residual_selection(**values)


def test_unique_development_winner_is_the_only_weight_confirmed_on_heldout() -> None:
    result = _selection()
    assert result.status == "VERIFIED_PREDECLARED_WEIGHT_SELECTION_AND_HELDOUT_RESIDUAL_CONFIRMATION"
    assert result.validation_level == result.status
    assert result.robust_interior
    assert result.selected_candidate_id == "balanced"
    assert result.runner_up_candidate_id == "first11"
    assert result.development_advantage is not None and result.development_advantage > 0
    assert result.heldout_certificate is not None
    assert result.heldout_selected_weight_robust_delta_lower is not None
    assert result.heldout_selected_weight_robust_delta_lower > 0
    assert result.selected_weight_confirmed_on_heldout
    assert not result.heldout_alternative_candidates_evaluated
    assert not result.empirical_matrix_provenance_verified
    assert not result.post_hoc_weight_search_admitted


def test_menu_identity_is_canonical_and_order_invariant() -> None:
    forward = M.predeclared_diagonal_weight_menu(
        dimension=2, candidate_weights_by_id={"a": (1, 1), "b": (2, 1)}
    )
    reverse = M.predeclared_diagonal_weight_menu(
        dimension=2, candidate_weights_by_id={"b": (2, 1), "a": (1, 1)}
    )
    assert forward == reverse
    assert len(forward.canonical_menu_sha256) == 64
    assert tuple(candidate.candidate_id for candidate in forward.candidates) == ("a", "b")


def test_common_scalings_cannot_create_duplicate_candidates() -> None:
    with pytest.raises(ValueError, match="duplicate normalized weights"):
        M.predeclared_diagonal_weight_menu(
            dimension=2, candidate_weights_by_id={"a": (1, 2), "b": (2, 4)}
        )


def test_equal_top_scores_fail_closed_without_order_tie_breaking() -> None:
    matrix = ((0, 0), (0, 5))
    menu = M.predeclared_diagonal_weight_menu(
        dimension=2,
        candidate_weights_by_id={"first": (F(11, 10), 1), "second": (1, F(11, 10))},
    )
    result = _selection(menu=menu, nominal_transition=matrix)
    assert result.status == "WEIGHT_MENU_DEVELOPMENT_WINNER_NOT_UNIQUE"
    assert result.selected_candidate_id is None
    assert result.heldout_certificate is None


def test_equal_runner_up_scores_fail_closed() -> None:
    matrix = ((0, 0), (0, 5))
    result = _selection(nominal_transition=matrix)
    assert result.status == "WEIGHT_MENU_DEVELOPMENT_RUNNER_UP_NOT_UNIQUE"
    assert result.selected_candidate_id == "balanced"
    assert result.runner_up_candidate_id is None
    assert result.heldout_certificate is None


def test_minimum_advantage_is_strict_and_predeclared() -> None:
    baseline = _selection()
    assert baseline.development_advantage is not None
    result = _selection(minimum_development_advantage=baseline.development_advantage)
    assert result.status == "WEIGHT_MENU_DEVELOPMENT_ADVANTAGE_NOT_STRICT"
    assert result.heldout_certificate is None


def test_no_weighted_development_certificate_fails_closed() -> None:
    matrix = ((0, 5), (0, 10))
    bad = (((0, 0), (0, 0)), ((0, 0), (2, 0)))
    result = _selection(
        nominal_transition=matrix,
        development_uncertainty_radii=bad,
        heldout_uncertainty_radii=bad,
    )
    assert result.status == "WEIGHT_MENU_NO_DEVELOPMENT_CANDIDATE_CERTIFIED"
    assert result.selected_candidate_id is None
    assert result.heldout_certificate is None


def test_only_one_eligible_candidate_has_no_declared_runner_up() -> None:
    menu = M.predeclared_diagonal_weight_menu(
        dimension=2,
        candidate_weights_by_id={"balanced": (1, 1), "first12": (F(6, 5), 1)},
    )
    result = _selection(menu=menu)
    assert result.status == "WEIGHT_MENU_DEVELOPMENT_RUNNER_UP_UNAVAILABLE"
    assert result.selected_candidate_id == "balanced"
    assert result.runner_up_candidate_id is None
    assert result.heldout_certificate is None


def test_selected_weight_must_itself_pass_heldout_not_merely_the_unweighted_fallback() -> None:
    bad_heldout = (((2, 0), (0, 0)), ((0, 0), (0, 0)))
    result = _selection(heldout_uncertainty_radii=bad_heldout)
    assert result.status == "WEIGHT_MENU_SELECTED_CANDIDATE_FAILED_HELDOUT_CONFIRMATION"
    assert result.selected_candidate_id == "balanced"
    assert result.heldout_certificate is not None
    assert not result.robust_interior
    assert not result.selected_weight_confirmed_on_heldout


def test_exactly_one_heldout_evaluation_occurs(monkeypatch: pytest.MonkeyPatch) -> None:
    original = M.verified_weighted_componentwise_residual_circle
    calls = []

    def counted(*args, **kwargs):
        calls.append(kwargs["diagonal_weights"])
        return original(*args, **kwargs)

    monkeypatch.setattr(M, "verified_weighted_componentwise_residual_circle", counted)
    result = _selection()
    assert result.validation_level is not None
    assert len(calls) == len(result.menu.candidates) + 1
    assert calls[-1] == result.selected_normalized_weights


@pytest.mark.parametrize(
    "candidate_id", ["A", "a b", "1a", "a.b", "", True]
)
def test_noncanonical_candidate_ids_fail_closed(candidate_id: object) -> None:
    with pytest.raises((TypeError, ValueError)):
        M.predeclared_diagonal_weight_menu(
            dimension=2, candidate_weights_by_id={candidate_id: (1, 1), "valid": (2, 1)}
        )


@pytest.mark.parametrize(
    "weights", [(0, 1), (-1, 1), (1.0, 1), (True, 1), (1,), (1, 1, 1)]
)
def test_invalid_candidate_weights_fail_closed(weights: object) -> None:
    with pytest.raises(ValueError):
        M.predeclared_diagonal_weight_menu(
            dimension=2, candidate_weights_by_id={"a": weights, "b": (2, 1)}
        )


def test_forged_or_dimension_mismatched_menu_is_rejected() -> None:
    valid = _menu()
    forged = M.PredeclaredDiagonalWeightMenu(valid.dimension, valid.candidates, "0" * 64)
    with pytest.raises(ValueError, match="unchanged output"):
        _selection(menu=forged)
    with pytest.raises(ValueError, match="dimension"):
        _selection(
            menu=M.predeclared_diagonal_weight_menu(
                dimension=3, candidate_weights_by_id={"a": (1, 1, 1), "b": (2, 1, 1)}
            )
        )
