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
HASH = "b" * 64


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


def _run(**overrides):
    args = dict(
        base_dimension_certificate=_base(), session_ids=("1", "2", "3"),
        conscious_window_ranks_by_session=((5, 5, 5, 4, 6) * 2,) * 3,
        control_window_ranks_by_session=((1, 2, 3, 8, 10) * 2,) * 3,
        block_bootstrap_ranks_by_session=((5,) * 18 + (4, 6),) * 3,
        window_partition_kind=S.WINDOW_PARTITION_KIND,
        block_bootstrap_kind=S.BLOCK_BOOTSTRAP_KIND, frozen_block_length=2,
        minimum_conscious_band_window_fraction=F(9, 10),
        minimum_selected_rank_window_fraction=F(1, 2),
        maximum_conscious_rank_transition_fraction=F(2, 3),
        minimum_selected_rank_longest_dwell_fraction=F(1, 4),
        minimum_conscious_control_band_gap=F(4, 5),
        minimum_bootstrap_band_fraction=F(9, 10),
        minimum_bootstrap_selected_rank_fraction=F(4, 5),
        heldout_window_summary_sha256=HASH, bootstrap_summary_sha256=HASH,
        stability_contract_sha256=HASH,
    )
    args.update(overrides)
    return S.conscious_moment_dimension_stability_protocol(**args)


def test_temporal_band_control_and_bootstrap_gates_pass_together() -> None:
    result = _run()
    assert result.validation_level is not None
    assert result.all_sessions_temporally_persistent
    assert result.all_sessions_control_separated
    assert result.all_sessions_block_bootstrap_stable
    assert result.candidate_4_6_temporal_stability_supported_by_supplied_summary


def test_session_metrics_are_exact_and_keep_band_distinct_from_rank() -> None:
    metric = _run().session_metrics[0]
    assert metric.conscious_band_window_fraction == 1
    assert metric.conscious_selected_rank_window_fraction == F(3, 5)
    assert metric.conscious_rank_transition_fraction == F(5, 9)
    assert metric.selected_rank_longest_dwell_fraction == F(3, 10)
    assert metric.control_band_window_fraction == 0
    assert metric.bootstrap_band_fraction == 1
    assert metric.bootstrap_selected_rank_fraction == F(9, 10)


def test_temporal_persistence_failure_is_session_named() -> None:
    rows = list(((5, 5, 5, 4, 6) * 2,) * 3); rows[1] = (1,) * 10
    result = _run(conscious_window_ranks_by_session=tuple(rows))
    assert "DIMENSION_STABILITY_SESSION_1_TEMPORAL_PERSISTENCE_FAILED" in result.failure_codes


def test_rapid_rank_switching_fails_even_when_band_occupancy_is_one() -> None:
    rows = ((4, 5) * 5,) * 3
    result = _run(
        conscious_window_ranks_by_session=rows,
        minimum_selected_rank_window_fraction=F(1, 2),
        minimum_selected_rank_longest_dwell_fraction=0,
    )
    assert "DIMENSION_STABILITY_SESSION_0_TEMPORAL_PERSISTENCE_FAILED" in result.failure_codes


def test_fragmented_selected_rank_fails_longest_dwell_gate() -> None:
    rows = ((5, 4, 5, 4, 5, 4, 5, 4, 5, 4),) * 3
    result = _run(
        conscious_window_ranks_by_session=rows,
        maximum_conscious_rank_transition_fraction=1,
        minimum_selected_rank_longest_dwell_fraction=F(1, 5),
    )
    assert "DIMENSION_STABILITY_SESSION_0_TEMPORAL_PERSISTENCE_FAILED" in result.failure_codes


def test_matched_control_separation_is_required() -> None:
    result = _run(control_window_ranks_by_session=((5,) * 10,) * 3)
    assert "DIMENSION_STABILITY_SESSION_0_CONTROL_SEPARATION_FAILED" in result.failure_codes


def test_block_bootstrap_selected_rank_support_is_required() -> None:
    rows = list(((5,) * 18 + (4, 6),) * 3); rows[2] = (4, 6) * 10
    result = _run(block_bootstrap_ranks_by_session=tuple(rows))
    assert "DIMENSION_STABILITY_SESSION_2_BLOCK_BOOTSTRAP_FAILED" in result.failure_codes


def test_base_certificate_failure_is_not_hidden() -> None:
    failed = _base(3)
    result = _run(base_dimension_certificate=failed)
    assert result.status == "DIMENSION_STABILITY_BASE_CERTIFICATE_NOT_VALIDATED"


def test_window_and_bootstrap_protocol_labels_are_frozen() -> None:
    window = _run(window_partition_kind="OVERLAPPING_POST_HOC_WINDOWS")
    bootstrap = _run(block_bootstrap_kind="IID_WINDOW_BOOTSTRAP")
    assert "DIMENSION_STABILITY_WINDOW_PARTITION_NOT_FROZEN" in window.failure_codes
    assert "DIMENSION_STABILITY_BOOTSTRAP_KIND_NOT_FROZEN" in bootstrap.failure_codes


def test_invalid_session_rows_thresholds_hash_and_float_fail_closed() -> None:
    with pytest.raises(ValueError, match="session IDs"):
        _run(session_ids=("01", "2", "3"))
    with pytest.raises(ValueError, match="same window"):
        _run(control_window_ranks_by_session=((1,) * 9,) * 3)
    with pytest.raises(ValueError, match="unit interval"):
        _run(minimum_bootstrap_band_fraction=2)
    with pytest.raises(ValueError, match="SHA-256"):
        _run(bootstrap_summary_sha256="bad")
    with pytest.raises(ValueError):
        _run(minimum_conscious_band_window_fraction=0.9)


def test_hashes_and_caller_summaries_do_not_create_external_receipt() -> None:
    result = _run()
    assert not result.external_time_series_receipt_verified
    assert not result.source_locked_empirical_temporal_result


def test_signal_rank_remains_distinct_from_consciousness_dimension() -> None:
    result = _run()
    assert result.signal_rank_is_not_consciousness_dimension
    assert not result.consciousness_dimension_claim_admitted
