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


_load("quantitative_graph_transform", "quantitative_graph_transform.py")
M = _load("ce_conscious_moment_dimension_protocol", "conscious_moment_dimension_protocol.py")


def _scores(winner: int):
    return {
        dimension: tuple(
            F(100) - 10 * abs(dimension - winner) - F(dimension, 100)
            for _ in range(4)
        )
        for dimension in M.FROZEN_DIMENSION_MENU
    }


def _spectra(rank: int):
    spectrum = (F(1),) * rank + (F(0),) * (12 - rank)
    return (spectrum, spectrum, spectrum)


def _certificate(winner: int = 5, **overrides):
    values = dict(
        signal_covariance_spectra=_spectra(winner),
        ridge_regularization=F(1, 10),
        rank_tolerance=0,
        estimator_agreement_tolerance=1,
        conscious_fold_scores_by_dimension=_scores(winner),
        control_fold_scores_by_dimension={d: (0, 0, 0, 0) for d in M.FROZEN_DIMENSION_MENU},
        permutation_exceedances=0,
        permutation_repetitions=1000,
        permutation_alpha=F(1, 20),
        provenance_status=M.SYNTHETIC_FIXTURE,
        spectrum_kind=M.SIGNAL_SPECTRUM_KIND,
        permutation_scope=M.PERMUTATION_SCOPE,
    )
    values.update(overrides)
    return M.conscious_moment_dimension_identification_protocol(**values)


@pytest.mark.parametrize("winner", [4, 5, 6])
def test_complete_frozen_menu_can_support_each_candidate_rank_synthetically(winner: int) -> None:
    result = _certificate(winner)
    assert result.status == "VALIDATED_SYNTHETIC_4_6_DIMENSION_IDENTIFICATION_APPARATUS"
    assert result.selected_signal_rank == winner
    assert result.candidate_4_6_signal_rank_supported_by_supplied_summary is True
    assert result.source_locked_empirical_signal_rank_result is False
    assert result.consciousness_dimension_claim_admitted is False


def test_exact_session_estimators_remain_distinct() -> None:
    result = _certificate(5)
    for metric in result.session_metrics:
        assert metric.recorded_unit_count == 12
        assert metric.positive_spectrum_rank == 5
        assert metric.participation_ratio == 5
        assert metric.ridge_effective_dimension == F(50, 11)
        assert metric.stable_rank == 5


def test_heldout_and_state_contrast_winners_are_unique_and_above_two_se() -> None:
    result = _certificate()
    for gate in (result.conscious_selection, result.conscious_minus_control_selection):
        assert gate.selected_dimension == 5
        assert gate.runner_up_dimension == 4
        assert gate.selected_minus_runner_mean == F(999, 100)
        assert gate.selected_minus_runner_standard_error_squared == 0
        assert gate.exceeds_two_standard_errors_strictly is True


def test_max_menu_permutation_uses_plus_one_correction() -> None:
    result = _certificate()
    assert result.permutation_p_upper == F(1, 1001)
    assert result.permutation_p_upper < result.permutation_alpha


def test_source_locked_label_cannot_replace_an_external_observation_receipt() -> None:
    result = _certificate(provenance_status=M.SOURCE_LOCKED_EMPIRICAL)
    assert result.status == "VALIDATED_DECLARED_SOURCE_LOCKED_4_6_SIGNAL_RANK_SUMMARY_ONLY"
    assert result.external_source_receipt_verified is False
    assert result.source_locked_empirical_signal_rank_result is False
    assert result.neural_signal_rank_is_not_manifold_or_consciousness_dimension is True
    assert result.consciousness_dimension_claim_admitted is False


def test_outside_band_winner_fails_even_when_other_gates_pass() -> None:
    result = _certificate(3)
    assert result.status == "DIMENSION_PROTOCOL_SELECTED_RANK_OUTSIDE_FROZEN_4_6_BAND"
    assert result.validation_level is None


def test_tied_winner_fails_closed() -> None:
    tied = {dimension: (1, 1, 1, 1) for dimension in M.FROZEN_DIMENSION_MENU}
    result = _certificate(conscious_fold_scores_by_dimension=tied)
    assert result.status == "DIMENSION_PROTOCOL_CONSCIOUS_HELDOUT_WINNER_NOT_UNIQUE"


def test_advantage_below_two_standard_errors_fails() -> None:
    rows = _scores(5)
    rows[5] = (10, 0, 10, 0)
    rows[4] = (0, 9, 0, 9)
    for dimension in M.FROZEN_DIMENSION_MENU:
        if dimension not in (4, 5):
            rows[dimension] = (-100, -100, -100, -100)
    result = _certificate(conscious_fold_scores_by_dimension=rows)
    assert result.status == "DIMENSION_PROTOCOL_CONSCIOUS_HELDOUT_ADVANTAGE_NOT_ABOVE_TWO_SE"


def test_conscious_and_control_contrast_must_select_same_rank() -> None:
    control = {dimension: (0, 0, 0, 0) for dimension in M.FROZEN_DIMENSION_MENU}
    control[5] = (100, 100, 100, 100)
    result = _certificate(control_fold_scores_by_dimension=control)
    assert "DIMENSION_PROTOCOL_CONSCIOUS_AND_CONTRAST_WINNERS_DISAGREE" in result.failure_codes


def test_session_estimators_must_agree_with_selected_rank() -> None:
    result = _certificate(signal_covariance_spectra=_spectra(7))
    assert "DIMENSION_PROTOCOL_SESSION_0_HARD_RANK_DISAGREES" in result.failure_codes
    assert result.validation_level is None


def test_permutation_must_be_max_menu_and_significant() -> None:
    wrong_scope = _certificate(permutation_scope="SELECTED_ONLY")
    assert wrong_scope.status == "DIMENSION_PROTOCOL_PERMUTATION_NOT_MAX_OVER_FROZEN_MENU"
    weak = _certificate(permutation_exceedances=100)
    assert weak.status == "DIMENSION_PROTOCOL_MAX_MENU_PERMUTATION_NOT_SIGNIFICANT"


def test_raw_or_noise_inflated_spectrum_is_rejected() -> None:
    result = _certificate(spectrum_kind="RAW_SAMPLE_COVARIANCE")
    assert result.status == "DIMENSION_PROTOCOL_SPECTRUM_NOT_CROSS_VALIDATED_SIGNAL"


def test_complete_menu_is_mandatory() -> None:
    rows = _scores(5)
    rows.pop(12)
    with pytest.raises(ValueError, match="exactly"):
        _certificate(conscious_fold_scores_by_dimension=rows)


@pytest.mark.parametrize(
    "field,value",
    [
        ("ridge_regularization", 0),
        ("rank_tolerance", -1),
        ("estimator_agreement_tolerance", True),
        ("permutation_exceedances", -1),
        ("permutation_repetitions", True),
        ("permutation_alpha", 1),
        ("provenance_status", "UNLOCKED_REAL_DATA"),
        ("signal_covariance_spectra", ((1,) * 12, (1,) * 12)),
    ],
)
def test_invalid_protocol_inputs_fail_closed(field: str, value: object) -> None:
    with pytest.raises(ValueError):
        _certificate(**{field: value})


def test_claim_scope_forbids_rank_identity_claim() -> None:
    result = _certificate()
    assert "NEURAL_SIGNAL_RANK_PROTOCOL" in result.claim_scope
    assert "NOT_AN_AMBIENT_MANIFOLD_PHENOMENOLOGICAL_OR_CONSCIOUSNESS_DIMENSION" in result.claim_scope
