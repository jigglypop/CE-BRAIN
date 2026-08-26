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
_load("verified_rational_mesh_residual", "verified_rational_mesh_residual.py")
_load("verified_rational_polygon_residual", "verified_rational_polygon_residual.py")
_load("verified_polygon_riesz_quadrature", "verified_polygon_riesz_quadrature.py")
_load("verified_adaptive_polygon_riesz", "verified_adaptive_polygon_riesz.py")
_load("verified_rational_ellipse_residual", "verified_rational_ellipse_residual.py")
_load("verified_polynomial_radial_contour_residual", "verified_polynomial_radial_contour_residual.py")
_load("verified_piecewise_polynomial_radial_contour_residual", "verified_piecewise_polynomial_radial_contour_residual.py")
_load("verified_piecewise_rational_radial_contour_residual", "verified_piecewise_rational_radial_contour_residual.py")
_load("verified_piecewise_rational_radial_polygon_rank_bridge", "verified_piecewise_rational_radial_polygon_rank_bridge.py")
M = _load("ce_predeclared_rational_contour_selection", "predeclared_rational_contour_selection.py")


RATIONAL_EIGHT = (
    (1, 0),
    (F(3, 5), F(4, 5)),
    (0, 1),
    (F(-3, 5), F(4, 5)),
    (-1, 0),
    (F(-3, 5), F(-4, 5)),
    (0, -1),
    (F(3, 5), F(-4, 5)),
)
ZERO1 = (((0, 0),),)


def _spec(radius, *, center=0):
    patch = ((radius, ()), (1, ()))
    return {
        "center": center,
        "axis_u": 1,
        "axis_v": (0, 1),
        "rational_patches": (patch,) * 8,
        "junction_order": 1,
        "directions": RATIONAL_EIGHT,
    }


def _menu():
    return M.predeclared_rational_contour_menu(
        candidate_specs_by_id={
            "large": _spec(F(6, 5)),
            "medium": _spec(1),
            "small": _spec(F(4, 5)),
        },
        sqrt_precision=48,
    )


def _selection(**overrides):
    values = dict(
        menu=_menu(),
        development_nominal_transition=((0,),),
        development_uncertainty_radii=ZERO1,
        heldout_nominal_transition=((0,),),
        heldout_uncertainty_radii=ZERO1,
        spectral_reference_scale=1,
        minimum_development_advantage=0,
        initial_subdivisions=1,
        maximum_refinements=8,
        sqrt_precision=48,
        machin_terms=8,
    )
    values.update(overrides)
    return M.predeclared_rational_contour_selection(**values)


def test_unique_development_winner_is_selected_only_on_heldout() -> None:
    result = _selection()
    assert result.validation_level == result.status
    assert result.selected_candidate_id == "large"
    assert result.runner_up_candidate_id == "medium"
    assert result.development_advantage is not None and result.development_advantage > 0
    assert result.development_selected_rank == 1
    assert result.heldout_selected_rank == 1
    assert result.selected_contour_confirmed_on_heldout
    assert result.heldout_rank_consistency_verified
    assert not result.heldout_alternative_candidates_evaluated
    assert not result.post_hoc_contour_search_admitted
    assert not result.continuous_contour_optimization_verified


def test_menu_hash_and_order_are_deterministic() -> None:
    forward = M.predeclared_rational_contour_menu(
        candidate_specs_by_id={"a": _spec(1), "b": _spec(F(6, 5))},
        sqrt_precision=48,
    )
    reverse = M.predeclared_rational_contour_menu(
        candidate_specs_by_id={"b": _spec(F(6, 5)), "a": _spec(1)},
        sqrt_precision=48,
    )
    assert forward == reverse
    assert len(forward.canonical_menu_sha256) == 64


def test_exact_duplicate_contours_are_rejected() -> None:
    with pytest.raises(ValueError, match="exact duplicate"):
        M.predeclared_rational_contour_menu(
            candidate_specs_by_id={"a": _spec(1), "b": _spec(1)},
            sqrt_precision=48,
        )


def test_equal_development_winners_fail_without_id_tie_breaking() -> None:
    menu = M.predeclared_rational_contour_menu(
        candidate_specs_by_id={
            "left": _spec(1, center=F(-1, 10)),
            "right": _spec(1, center=F(1, 10)),
        },
        sqrt_precision=48,
    )
    result = _selection(menu=menu)
    assert result.status == "CONTOUR_MENU_DEVELOPMENT_WINNER_NOT_UNIQUE"
    assert result.selected_candidate_id is None
    assert result.heldout_certificate is None


def test_equal_runners_fail_closed() -> None:
    menu = M.predeclared_rational_contour_menu(
        candidate_specs_by_id={
            "large": _spec(F(6, 5)),
            "left": _spec(1, center=F(-1, 10)),
            "right": _spec(1, center=F(1, 10)),
        },
        sqrt_precision=48,
    )
    result = _selection(menu=menu)
    assert result.status == "CONTOUR_MENU_DEVELOPMENT_RUNNER_UP_NOT_UNIQUE"
    assert result.selected_candidate_id == "large"
    assert result.heldout_certificate is None


def test_strict_advantage_equality_fails() -> None:
    baseline = _selection()
    assert baseline.development_advantage is not None
    result = _selection(minimum_development_advantage=baseline.development_advantage)
    assert result.status == "CONTOUR_MENU_DEVELOPMENT_ADVANTAGE_NOT_STRICT"
    assert result.heldout_certificate is None


def test_no_certified_development_candidate_fails_closed() -> None:
    bad = (((2, 0),),)
    result = _selection(development_uncertainty_radii=bad)
    assert result.status == "CONTOUR_MENU_NO_DEVELOPMENT_CANDIDATE_CERTIFIED"
    assert result.selected_candidate_id is None
    assert result.heldout_certificate is None


def test_selected_candidate_must_pass_heldout() -> None:
    result = _selection(heldout_nominal_transition=((F(6, 5),),))
    assert result.status == "CONTOUR_MENU_SELECTED_CANDIDATE_FAILED_HELDOUT_CONFIRMATION"
    assert result.heldout_certificate is not None
    assert not result.selected_contour_confirmed_on_heldout


def test_heldout_rank_mismatch_fails_even_when_contour_is_certified() -> None:
    result = _selection(heldout_nominal_transition=((2,),))
    assert result.status == "CONTOUR_MENU_SELECTED_CANDIDATE_HELDOUT_RANK_MISMATCH"
    assert result.heldout_selected_rank == 0
    assert not result.heldout_rank_consistency_verified


def test_exactly_one_heldout_contour_is_evaluated(monkeypatch: pytest.MonkeyPatch) -> None:
    original = M._evaluate_candidate
    calls = []

    def counted(candidate, **kwargs):
        calls.append(candidate.candidate_id)
        return original(candidate, **kwargs)

    monkeypatch.setattr(M, "_evaluate_candidate", counted)
    result = _selection()
    assert result.validation_level is not None
    assert len(calls) == len(result.menu.candidates) + 1
    assert calls[-1] == result.selected_candidate_id


def test_forged_menu_and_matrix_dimension_mismatch_are_rejected() -> None:
    valid = _menu()
    forged = M.PredeclaredRationalContourMenu(valid.candidates, "0" * 64)
    with pytest.raises(ValueError, match="unchanged output"):
        _selection(menu=forged)
    with pytest.raises(ValueError, match="dimensions must agree"):
        _selection(heldout_nominal_transition=((0, 0), (0, 0)))


@pytest.mark.parametrize("candidate_id", ["A", "a b", "1a", "a.b", "", True])
def test_invalid_candidate_ids_fail(candidate_id) -> None:
    with pytest.raises((TypeError, ValueError)):
        M.predeclared_rational_contour_menu(
            candidate_specs_by_id={candidate_id: _spec(1), "valid": _spec(F(6, 5))},
            sqrt_precision=48,
        )


def test_raw_scale_covariance_preserves_selection() -> None:
    base = _selection()
    scaled = _selection(spectral_reference_scale=7)
    assert scaled.selected_candidate_id == base.selected_candidate_id
    assert scaled.development_advantage == base.development_advantage
