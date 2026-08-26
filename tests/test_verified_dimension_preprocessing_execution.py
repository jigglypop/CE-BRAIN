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
_load("verified_dimension_time_series_execution")
_load("verified_dimension_projector_training_execution")
P = _load("verified_dimension_preprocessing_execution")
HASH = "f" * 64
MEAN = tuple(F(20 + j) for j in range(12))
SCALES = tuple(F(j + 1) for j in range(12))


def _scores(winner: int):
    return {d: tuple(F(100) - 10 * abs(d - winner) - F(d, 100) for _ in range(4)) for d in D.FROZEN_DIMENSION_MENU}


def _base():
    spectrum = (F(1),) * 5 + (F(0),) * 7
    return D.conscious_moment_dimension_identification_protocol(
        signal_covariance_spectra=(spectrum,) * 3,
        ridge_regularization=F(1, 10), rank_tolerance=0, estimator_agreement_tolerance=1,
        conscious_fold_scores_by_dimension=_scores(5),
        control_fold_scores_by_dimension={d: (0, 0, 0, 0) for d in D.FROZEN_DIMENSION_MENU},
        permutation_exceedances=0, permutation_repetitions=1000, permutation_alpha=F(1, 20),
        provenance_status=D.SYNTHETIC_FIXTURE, spectrum_kind=D.SIGNAL_SPECTRUM_KIND,
        permutation_scope=D.PERMUTATION_SCOPE,
    )


def _unit(index: int, amplitude=1):
    return tuple(F(amplitude if j == index else 0) for j in range(12))


def _raw(vector, mean=MEAN, scales=SCALES):
    return tuple(mean[j] + scales[j] * vector[j] for j in range(12))


def _development():
    rows = []
    for index in range(12):
        amplitude = 12 - index
        rows.extend((_raw(_unit(index, amplitude)), _raw(_unit(index, -amplitude))))
    return (tuple(rows),) * 3


def _basis():
    identity = tuple(_unit(index) for index in range(12))
    return (identity,) * 3


def _vector(rank: int):
    return tuple(F(int(i < rank)) for i in range(12))


def _windows(ranks):
    return tuple((_raw(_vector(rank)), _raw(_vector(rank))) for rank in ranks)


CONSCIOUS = (5, 5, 5, 4, 6, 5, 5, 5, 4, 6)
CONTROL = (2,) * 10


def _schedule():
    rows = []
    for shift in range(20):
        starts = tuple((shift + 2 * block) % 10 for block in range(5))
        rows.append(tuple(index for start in starts for index in (start, (start + 1) % 10)))
    return (tuple(rows),) * 3


def _args():
    return dict(
        base_dimension_certificate=_base(), session_ids=("1", "2", "3"),
        raw_development_observations_by_session=_development(),
        raw_conscious_heldout_observations_by_session=(_windows(CONSCIOUS),) * 3,
        raw_control_heldout_observations_by_session=(_windows(CONTROL),) * 3,
        coordinate_reference_scales_by_session=(SCALES,) * 3,
        covariance_eigenbasis_witnesses_by_session=_basis(),
        complexity_penalty=F(1, 2), bootstrap_window_indices_by_session=_schedule(),
        frozen_block_length=2, window_partition_kind=S.WINDOW_PARTITION_KIND,
        block_bootstrap_kind=S.BLOCK_BOOTSTRAP_KIND,
        minimum_conscious_band_window_fraction=F(9, 10),
        minimum_selected_rank_window_fraction=F(1, 2),
        maximum_conscious_rank_transition_fraction=F(2, 3),
        minimum_selected_rank_longest_dwell_fraction=F(1, 4),
        minimum_conscious_control_band_gap=F(4, 5),
        minimum_bootstrap_band_fraction=F(9, 10),
        minimum_bootstrap_selected_rank_fraction=F(4, 5),
        raw_development_sha256=HASH, raw_heldout_sha256=HASH,
        preprocessing_contract_sha256=HASH, eigenbasis_witness_sha256=HASH,
        bootstrap_schedule_sha256=HASH, execution_contract_sha256=HASH,
    )


def _run(**overrides):
    args = _args()
    args.update(overrides)
    return P.verified_dimension_preprocessing_execution(**args)


def test_raw_vectors_are_preprocessed_and_full_dimension_chain_passes() -> None:
    result = _run()
    assert result.validation_level is not None
    assert result.preprocessing_to_training_and_heldout_chain_composed
    nested = result.projector_training_execution.heldout_execution
    assert nested.generated_conscious_window_ranks_by_session == (CONSCIOUS,) * 3


def test_development_mean_and_reference_scales_are_exact() -> None:
    receipt = _run().preprocessing_receipts[0]
    assert receipt.development_coordinate_mean == MEAN
    assert receipt.frozen_coordinate_reference_scales == SCALES
    assert receipt.normalized_development_coordinate_sum == (0,) * 12


def test_same_development_transform_is_used_for_both_heldout_conditions() -> None:
    receipt = _run().preprocessing_receipts[0]
    assert receipt.development_mean_used_for_all_splits
    assert not receipt.heldout_statistics_reestimated
    assert not _run().heldout_statistic_leakage_detected


def test_heldout_shift_is_not_silently_recentered() -> None:
    shifted = tuple(
        tuple(tuple(tuple(value + 100 for value in vector) for vector in window) for window in session)
        for session in ((_windows(CONSCIOUS),) * 3)
    )
    result = _run(raw_conscious_heldout_observations_by_session=shifted)
    assert result.validation_level is None


def test_raw_scale_covariance_preserves_normalized_execution() -> None:
    new_scales = tuple(7 * value for value in SCALES)
    def rescale(raw):
        return tuple(MEAN[j] + 7 * (raw[j] - MEAN[j]) for j in range(12))
    development = tuple(tuple(rescale(row) for row in session) for session in _development())
    conscious = tuple(tuple(tuple(rescale(row) for row in window) for window in session) for session in ((_windows(CONSCIOUS),) * 3))
    control = tuple(tuple(tuple(rescale(row) for row in window) for window in session) for session in ((_windows(CONTROL),) * 3))
    result = _run(
        raw_development_observations_by_session=development,
        raw_conscious_heldout_observations_by_session=conscious,
        raw_control_heldout_observations_by_session=control,
        coordinate_reference_scales_by_session=(new_scales,) * 3,
    )
    assert result.validation_level is not None
    assert result.projector_training_execution.heldout_execution.generated_conscious_window_ranks_by_session == (CONSCIOUS,) * 3


def test_nonpositive_scale_and_float_fail_closed() -> None:
    bad = list(SCALES); bad[0] = 0
    with pytest.raises(ValueError, match="positive"):
        _run(coordinate_reference_scales_by_session=(tuple(bad),) * 3)
    bad_float = list(SCALES); bad_float[0] = 1.0
    with pytest.raises(ValueError):
        _run(coordinate_reference_scales_by_session=(tuple(bad_float),) * 3)


def test_training_failure_propagates_through_preprocessing() -> None:
    bases = list(_basis()); row = list(bases[0]); row[0], row[1] = row[1], row[0]; bases[0] = tuple(row)
    result = _run(covariance_eigenbasis_witnesses_by_session=tuple(bases))
    assert result.validation_level is None
    assert "DIMENSION_TRAINING_SESSION_0_EIGENVALUES_NOT_STRICTLY_ORDERED" in result.failure_codes


def test_hashes_do_not_authenticate_raw_bytes() -> None:
    result = _run()
    assert result.raw_development_vectors_parsed_exactly
    assert result.development_means_recomputed_exactly
    assert not result.external_raw_bytes_receipt_verified
    assert not result.source_locked_empirical_dimension_result
    assert not result.consciousness_dimension_claim_admitted
