from __future__ import annotations

import importlib.util
from fractions import Fraction as F
from pathlib import Path
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]
MODULE_DIR = ROOT / "reality_stone" / "python" / "reality_stone" / "clarus"


def _load(name: str):
    spec = importlib.util.spec_from_file_location(name, MODULE_DIR / f"{name}.py")
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


_load("quantitative_graph_transform")
D = _load("conscious_moment_dimension_protocol")
S = _load("conscious_moment_dimension_stability_protocol")
E = _load("verified_dimension_time_series_execution")
HASH = "d" * 64


def _scores(winner: int):
    return {d: tuple(F(100) - 10 * abs(d - winner) - F(d, 100) for _ in range(4)) for d in D.FROZEN_DIMENSION_MENU}


def _base(winner: int = 5):
    spectrum = (F(1),) * winner + (F(0),) * (12 - winner)
    return D.conscious_moment_dimension_identification_protocol(
        signal_covariance_spectra=(spectrum,) * 3,
        ridge_regularization=F(1, 10), rank_tolerance=0, estimator_agreement_tolerance=1,
        conscious_fold_scores_by_dimension=_scores(winner),
        control_fold_scores_by_dimension={d: (0, 0, 0, 0) for d in D.FROZEN_DIMENSION_MENU},
        permutation_exceedances=0, permutation_repetitions=1000, permutation_alpha=F(1, 20),
        provenance_status=D.SYNTHETIC_FIXTURE, spectrum_kind=D.SIGNAL_SPECTRUM_KIND,
        permutation_scope=D.PERMUTATION_SCOPE,
    )


def _projector(rank: int):
    return tuple(tuple(F(int(i == j and i < rank)) for j in range(12)) for i in range(12))


def _menus():
    menu = {d: _projector(d) for d in D.FROZEN_DIMENSION_MENU}
    return (menu, menu, menu)


def _vector(rank: int):
    return tuple(F(int(i < rank)) for i in range(12))


def _windows(ranks):
    return tuple((_vector(rank), _vector(rank)) for rank in ranks)


CONSCIOUS_RANKS = (5, 5, 5, 4, 6, 5, 5, 5, 4, 6)
CONTROL_RANKS = (2,) * 10


def _schedule():
    replicates = []
    for shift in range(20):
        starts = tuple((shift + 2 * block) % 10 for block in range(5))
        row = tuple(index for start in starts for index in (start, (start + 1) % 10))
        replicates.append(row)
    return (tuple(replicates),) * 3


def _run(**overrides):
    args = dict(
        base_dimension_certificate=_base(), session_ids=("1", "2", "3"),
        conscious_heldout_observations_by_session=(_windows(CONSCIOUS_RANKS),) * 3,
        control_heldout_observations_by_session=(_windows(CONTROL_RANKS),) * 3,
        projection_menus_by_session=_menus(), complexity_penalty=F(1, 2),
        bootstrap_window_indices_by_session=_schedule(), frozen_block_length=2,
        window_partition_kind=S.WINDOW_PARTITION_KIND,
        block_bootstrap_kind=S.BLOCK_BOOTSTRAP_KIND,
        minimum_conscious_band_window_fraction=F(9, 10),
        minimum_selected_rank_window_fraction=F(1, 2),
        maximum_conscious_rank_transition_fraction=F(2, 3),
        minimum_selected_rank_longest_dwell_fraction=F(1, 4),
        minimum_conscious_control_band_gap=F(4, 5),
        minimum_bootstrap_band_fraction=F(9, 10),
        minimum_bootstrap_selected_rank_fraction=F(4, 5),
        heldout_observation_sha256=HASH, projector_menu_sha256=HASH,
        bootstrap_schedule_sha256=HASH, execution_contract_sha256=HASH,
    )
    args.update(overrides)
    return E.verified_dimension_time_series_execution(**args)


def test_raw_heldout_vectors_reproduce_window_and_bootstrap_ranks() -> None:
    result = _run()
    assert result.validation_level is not None
    assert result.generated_conscious_window_ranks_by_session == (CONSCIOUS_RANKS,) * 3
    assert result.generated_control_window_ranks_by_session == (CONTROL_RANKS,) * 3
    assert result.generated_block_bootstrap_ranks_by_session == ((5,) * 20,) * 3


def test_exact_reconstruction_score_selects_rank_five() -> None:
    receipt = _run().window_execution_receipts[0]
    scores = dict(receipt.conscious_scores_by_window[0])
    assert scores[4] == F(-3)
    assert scores[5] == F(-5, 2)
    assert scores[6] == F(-3)
    assert receipt.aggregate_conscious_selected_rank == 5


def test_projection_menu_is_verified_exactly() -> None:
    result = _run()
    assert result.exact_projection_menu_verified
    assert result.ambient_dimension == 12


def test_nonprojector_menu_fails_closed() -> None:
    menus = list(_menus()); bad = dict(menus[0]); matrix = [list(row) for row in bad[5]]
    matrix[0][1] = 1
    bad[5] = tuple(tuple(row) for row in matrix); menus[0] = bad
    result = _run(projection_menus_by_session=tuple(menus))
    assert "DIMENSION_EXECUTION_PROJECTION_MENU_NOT_EXACT_ORTHOGONAL_PROJECTORS" in result.failure_codes


def test_moving_block_schedule_is_verified_and_bad_chunk_fails() -> None:
    assert _run().moving_block_schedule_verified
    schedule = [list(map(list, session)) for session in _schedule()]
    schedule[1][0][1] = 9
    result = _run(bootstrap_window_indices_by_session=tuple(tuple(tuple(row) for row in session) for session in schedule))
    assert "DIMENSION_EXECUTION_BOOTSTRAP_SCHEDULE_NOT_MOVING_BLOCK" in result.failure_codes


def test_score_tie_is_not_broken_post_hoc() -> None:
    result = _run(complexity_penalty=1)
    assert any("WINNER_NOT_UNIQUE" in code for code in result.failure_codes)
    assert result.validation_level is None


def test_raw_aggregate_must_match_base_complete_menu_rank() -> None:
    result = _run(base_dimension_certificate=_base(4))
    assert "DIMENSION_EXECUTION_SESSION_0_AGGREGATE_RANK_DISAGREES_WITH_BASE" in result.failure_codes


def test_generated_summaries_are_composed_into_stability_certificate() -> None:
    result = _run()
    assert result.stability_certificate.validation_level is not None
    assert result.stability_composed_from_generated_summaries
    assert result.stability_certificate.session_metrics[0].selected_rank_longest_dwell_fraction == F(3, 10)


def test_invalid_menu_schedule_hash_and_float_fail_closed() -> None:
    menus = list(_menus()); menus[0] = {1: _projector(1)}
    with pytest.raises(ValueError, match="complete"):
        _run(projection_menus_by_session=tuple(menus))
    with pytest.raises(ValueError, match="divisible"):
        _run(frozen_block_length=3)
    with pytest.raises(ValueError, match="SHA-256"):
        _run(projector_menu_sha256="bad")
    with pytest.raises(ValueError):
        _run(complexity_penalty=0.5)


def test_hashes_do_not_verify_external_bytes_or_projector_training() -> None:
    result = _run()
    assert result.heldout_scores_recomputed_from_observations
    assert result.bootstrap_ranks_recomputed_from_frozen_schedule
    assert not result.external_observation_bytes_receipt_verified
    assert not result.projector_training_execution_verified
    assert not result.source_locked_empirical_dimension_result
    assert not result.consciousness_dimension_claim_admitted
