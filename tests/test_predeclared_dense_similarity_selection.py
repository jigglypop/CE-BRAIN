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
_load("verified_dense_similarity_interval_residual", "verified_dense_similarity_interval_residual.py")
M = _load("ce_predeclared_dense_similarity_selection", "predeclared_dense_similarity_selection.py")


IDENTITY = ((1, 0), (0, 1))
ROT1 = ((F(9999, 10001), F(-200, 10001)), (F(200, 10001), F(9999, 10001)))
ROT2 = ((F(2499, 2501), F(-100, 2501)), (F(100, 2501), F(2499, 2501)))
ROT2_REVERSE = ((F(2499, 2501), F(100, 2501)), (F(-100, 2501), F(2499, 2501)))
ROT_LARGE = ((F(399, 401), F(-40, 401)), (F(40, 401), F(399, 401)))
ROT_LARGER = ((F(99, 101), F(-20, 101)), (F(20, 101), F(99, 101)))


def _exact_node_inverses(matrix):
    u = R._matrix(matrix, "matrix")
    directions = (R.ONE, R.QComplex(0, 1), R.QComplex(-1), R.QComplex(0, -1))
    witnesses = []
    for direction in directions:
        node = tuple(
            tuple((direction if i == j else R.ZERO) - u[i][j] for j in range(len(u)))
            for i in range(len(u))
        )
        inverse = R._inverse(node)
        assert inverse is not None
        witnesses.append(inverse)
    return tuple(witnesses)


def _menu():
    return M.predeclared_dense_similarity_menu(
        dimension=2,
        candidate_similarities_by_id={"identity": IDENTITY, "rot1": ROT1, "rot2": ROT2},
    )


def _selection(**overrides):
    matrix = ((0, 0), (0, 10))
    witnesses = _exact_node_inverses(matrix)
    zero = (((0, 0), (0, 0)), ((0, 0), (0, 0)))
    values = dict(
        menu=_menu(),
        nominal_transition=matrix,
        development_uncertainty_radii=zero,
        development_approximate_inverses=witnesses,
        heldout_uncertainty_radii=zero,
        heldout_approximate_inverses=witnesses,
        center=0,
        radius=1,
        spectral_reference_scale=1,
        minimum_development_advantage=0,
        sqrt_precision=40,
    )
    values.update(overrides)
    return M.predeclared_dense_similarity_selection(**values)


def test_unique_dense_winner_is_confirmed_on_selected_only_heldout() -> None:
    result = _selection()
    assert result.validation_level == result.status
    assert result.selected_candidate_id == "identity"
    assert result.runner_up_candidate_id == "rot1"
    assert result.development_advantage is not None and result.development_advantage > 0
    assert result.heldout_selected_dense_robust_delta_lower is not None
    assert result.heldout_selected_dense_robust_delta_lower > 0
    assert result.selected_dense_similarity_confirmed_on_heldout
    assert not result.heldout_alternative_candidates_evaluated
    assert not result.empirical_matrix_provenance_verified
    assert not result.post_hoc_dense_similarity_search_admitted


def test_common_complex_scaling_is_canonical_and_duplicate_rejected() -> None:
    scaled = tuple(tuple(2 * entry for entry in row) for row in IDENTITY)
    with pytest.raises(ValueError, match="proportional duplicate"):
        M.predeclared_dense_similarity_menu(
            dimension=2, candidate_similarities_by_id={"a": IDENTITY, "b": scaled}
        )


def test_menu_hash_and_order_are_deterministic() -> None:
    forward = M.predeclared_dense_similarity_menu(
        dimension=2, candidate_similarities_by_id={"a": IDENTITY, "b": ROT1}
    )
    reverse = M.predeclared_dense_similarity_menu(
        dimension=2, candidate_similarities_by_id={"b": ROT1, "a": IDENTITY}
    )
    assert forward == reverse
    assert len(forward.canonical_menu_sha256) == 64


def test_equal_dense_winners_fail_without_order_tie_breaking() -> None:
    menu = M.predeclared_dense_similarity_menu(
        dimension=2,
        candidate_similarities_by_id={"forward": ROT2, "reverse": ROT2_REVERSE},
    )
    result = _selection(menu=menu)
    assert result.status == "DENSE_MENU_DEVELOPMENT_WINNER_NOT_UNIQUE"
    assert result.selected_candidate_id is None
    assert result.heldout_certificate is None


def test_equal_dense_runners_fail_closed() -> None:
    menu = M.predeclared_dense_similarity_menu(
        dimension=2,
        candidate_similarities_by_id={
            "identity": IDENTITY, "forward": ROT2, "reverse": ROT2_REVERSE
        },
    )
    result = _selection(menu=menu)
    assert result.status == "DENSE_MENU_DEVELOPMENT_RUNNER_UP_NOT_UNIQUE"
    assert result.selected_candidate_id == "identity"
    assert result.heldout_certificate is None


def test_strict_advantage_equality_fails() -> None:
    baseline = _selection()
    assert baseline.development_advantage is not None
    result = _selection(minimum_development_advantage=baseline.development_advantage)
    assert result.status == "DENSE_MENU_DEVELOPMENT_ADVANTAGE_NOT_STRICT"
    assert result.heldout_certificate is None


def test_only_one_eligible_dense_candidate_has_no_runner() -> None:
    menu = M.predeclared_dense_similarity_menu(
        dimension=2,
        candidate_similarities_by_id={"identity": IDENTITY, "large": ROT_LARGE},
    )
    result = _selection(menu=menu)
    assert result.status == "DENSE_MENU_DEVELOPMENT_RUNNER_UP_UNAVAILABLE"
    assert result.selected_candidate_id == "identity"


def test_no_eligible_dense_candidate_fails_closed() -> None:
    menu = M.predeclared_dense_similarity_menu(
        dimension=2,
        candidate_similarities_by_id={"large": ROT_LARGE, "larger": ROT_LARGER},
    )
    result = _selection(menu=menu)
    assert result.status == "DENSE_MENU_NO_DEVELOPMENT_CANDIDATE_CERTIFIED"
    assert result.selected_candidate_id is None
    assert result.heldout_certificate is None


def test_selected_dense_candidate_must_itself_pass_heldout() -> None:
    bad = (((2, 0), (0, 0)), ((0, 0), (0, 0)))
    result = _selection(heldout_uncertainty_radii=bad)
    assert result.status == "DENSE_MENU_SELECTED_CANDIDATE_FAILED_HELDOUT_CONFIRMATION"
    assert result.heldout_certificate is not None
    assert not result.selected_dense_similarity_confirmed_on_heldout


def test_exactly_one_dense_heldout_evaluation_occurs(monkeypatch: pytest.MonkeyPatch) -> None:
    original = M.verified_dense_similarity_componentwise_residual_circle
    calls = []

    def counted(*args, **kwargs):
        calls.append(kwargs["similarity"])
        return original(*args, **kwargs)

    monkeypatch.setattr(M, "verified_dense_similarity_componentwise_residual_circle", counted)
    result = _selection()
    assert result.validation_level is not None
    assert len(calls) == len(result.menu.candidates) + 1
    assert calls[-1] == result.selected_normalized_similarity


def test_forged_menu_and_dimension_mismatch_are_rejected() -> None:
    valid = _menu()
    forged = M.PredeclaredDenseSimilarityMenu(valid.dimension, valid.candidates, "0" * 64)
    with pytest.raises(ValueError, match="unchanged output"):
        _selection(menu=forged)
    menu3 = M.predeclared_dense_similarity_menu(
        dimension=3,
        candidate_similarities_by_id={
            "a": ((1, 0, 0), (0, 1, 0), (0, 0, 1)),
            "b": ((1, 1, 0), (0, 1, 0), (0, 0, 1)),
        },
    )
    with pytest.raises(ValueError, match="dimension"):
        _selection(menu=menu3)


@pytest.mark.parametrize("candidate_id", ["A", "a b", "1a", "a.b", "", True])
def test_invalid_dense_candidate_ids_fail(candidate_id: object) -> None:
    with pytest.raises((TypeError, ValueError)):
        M.predeclared_dense_similarity_menu(
            dimension=2,
            candidate_similarities_by_id={candidate_id: IDENTITY, "valid": ROT1},
        )


@pytest.mark.parametrize(
    "candidate",
    [((1, 2), (2, 4)), ((1.0, 0), (0, 1)), ((True, 0), (0, 1)), ((1,),)],
)
def test_invalid_dense_candidates_fail(candidate: object) -> None:
    with pytest.raises(ValueError):
        M.predeclared_dense_similarity_menu(
            dimension=2, candidate_similarities_by_id={"a": candidate, "b": ROT1}
        )
