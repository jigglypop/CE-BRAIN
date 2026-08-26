from __future__ import annotations

import importlib.util
from fractions import Fraction as F
from pathlib import Path
import sys


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
T = _load("verified_dimension_projector_training_execution")
HASH = "e" * 64


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


def _development():
    rows = []
    for index in range(12):
        amplitude = 12 - index
        rows.extend((_unit(index, amplitude), _unit(index, -amplitude)))
    return (tuple(rows),) * 3


def _basis():
    identity = tuple(_unit(index) for index in range(12))
    return (identity,) * 3


def _vector(rank: int):
    return tuple(F(int(i < rank)) for i in range(12))


def _windows(ranks):
    return tuple((_vector(rank), _vector(rank)) for rank in ranks)


CONSCIOUS = (5, 5, 5, 4, 6, 5, 5, 5, 4, 6)
CONTROL = (2,) * 10


def _schedule():
    rows = []
    for shift in range(20):
        starts = tuple((shift + 2 * block) % 10 for block in range(5))
        rows.append(tuple(index for start in starts for index in (start, (start + 1) % 10)))
    return (tuple(rows),) * 3


def _run(**overrides):
    args = dict(
        base_dimension_certificate=_base(), session_ids=("1", "2", "3"),
        centered_development_observations_by_session=_development(),
        covariance_eigenbasis_witnesses_by_session=_basis(),
        conscious_heldout_observations_by_session=(_windows(CONSCIOUS),) * 3,
        control_heldout_observations_by_session=(_windows(CONTROL),) * 3,
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
        development_observation_sha256=HASH, eigenbasis_witness_sha256=HASH,
        heldout_observation_sha256=HASH, bootstrap_schedule_sha256=HASH,
        execution_contract_sha256=HASH,
    )
    args.update(overrides)
    return T.verified_dimension_projector_training_execution(**args)


def test_exact_covariance_eigenbasis_builds_projectors_and_executes_heldout() -> None:
    result = _run()
    assert result.validation_level is not None
    assert result.development_projector_training_verified
    assert result.heldout_execution.validation_level is not None
    assert result.heldout_execution.generated_conscious_window_ranks_by_session == (CONSCIOUS,) * 3


def test_development_covariance_and_eigenvalues_are_recomputed_exactly() -> None:
    receipt = _run().training_receipts[0]
    assert receipt.exact_zero_mean_verified
    assert receipt.ordered_eigenvalues[:3] == (12, F(121, 12), F(25, 3))
    assert receipt.ordered_eigenvalues[-1] == F(1, 12)
    assert receipt.covariance_matrix[0][0] == 12
    assert receipt.covariance_matrix[0][1] == 0


def test_prefix_projection_menu_has_exact_requested_traces() -> None:
    menu = dict(_run().training_receipts[0].projection_menu)
    for rank, projector in menu.items():
        assert sum(projector[i][i] for i in range(12)) == rank


def test_noncentered_development_observations_fail_closed() -> None:
    sessions = list(_development()); sessions[1] = sessions[1][:-1]
    result = _run(centered_development_observations_by_session=tuple(sessions))
    assert "DIMENSION_TRAINING_SESSION_1_DEVELOPMENT_NOT_EXACTLY_CENTERED" in result.failure_codes
    assert result.heldout_execution is None


def test_orthonormal_but_misordered_eigenbasis_fails_strict_pca_order() -> None:
    bases = list(_basis()); row = list(bases[0]); row[0], row[1] = row[1], row[0]; bases[0] = tuple(row)
    result = _run(covariance_eigenbasis_witnesses_by_session=tuple(bases))
    assert "DIMENSION_TRAINING_SESSION_0_EIGENVALUES_NOT_STRICTLY_ORDERED" in result.failure_codes


def test_orthonormal_rotated_basis_fails_eigen_equation() -> None:
    bases = list(_basis()); row = list(bases[0])
    row[0] = (F(3, 5), F(4, 5)) + (F(0),) * 10
    row[1] = (F(-4, 5), F(3, 5)) + (F(0),) * 10
    bases[0] = tuple(row)
    result = _run(covariance_eigenbasis_witnesses_by_session=tuple(bases))
    assert "DIMENSION_TRAINING_SESSION_0_COVARIANCE_EIGEN_EQUATION_FAILED" in result.failure_codes


def test_heldout_failure_propagates_after_valid_training() -> None:
    result = _run(complexity_penalty=1)
    assert result.development_projector_training_verified
    assert result.heldout_execution.validation_level is None
    assert any("WINNER_NOT_UNIQUE" in code for code in result.failure_codes)


def test_hashes_do_not_authenticate_development_or_preprocessing() -> None:
    result = _run()
    assert result.exact_development_covariance_recomputed
    assert result.exact_eigenbasis_witness_verified
    assert not result.external_development_bytes_receipt_verified
    assert not result.preprocessing_execution_verified
    assert not result.source_locked_empirical_dimension_result
    assert not result.consciousness_dimension_claim_admitted
