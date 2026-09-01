from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import h5py
import numpy as np
import pytest


RUNNER_PATH = Path(__file__).with_name("run_stx3_reward_alignment_crossnobis_v1_1.py")
sys.path.insert(0, str(RUNNER_PATH.parent))
SPEC = importlib.util.spec_from_file_location("stx3_reward_runner", RUNNER_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"cannot import {RUNNER_PATH}")
RUNNER = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = RUNNER
SPEC.loader.exec_module(RUNNER)


def _trial(ordinal: int, lr: int, *, start: int = 0, stop: int = 1, block: int = 5):
    return RUNNER.Trial(
        ordinal=ordinal,
        block=block,
        lr=lr,
        aligned_start=start,
        aligned_end=stop,
        full_start=start,
        full_end=stop,
    )


def _minimal_session(day: int, arrays: np.ndarray) -> object:
    trials = [_trial(0, -1), _trial(1, -1), _trial(2, 1), _trial(3, 1)]
    return RUNNER.SessionData(
        subject="Ctrl_1",
        day=day,
        path=Path("fixture.nwb"),
        roi_indices=np.arange(arrays.shape[-1]),
        trials=trials,
        neural_bins=arrays,
        speed_bins=np.zeros(arrays.shape[:2]),
        lick_bins=np.zeros(arrays.shape[:2]),
        behavior=[],
        fold_ordinals={
            -1: {"A": [0], "B": [1], "H": []},
            1: {"A": [2], "B": [3], "H": []},
        },
    )


def _make_session_nwb(
    path: Path,
    *,
    subject: str = "Ctrl_1",
    day: int = 0,
    novel_arm: int = -1,
    full_block_offset: int = 0,
    changed_offset_trial: int | None = None,
    mismatch_vr_block: bool = False,
    mismatch_aligned_block: bool = False,
    mismatch_full_lr: bool = False,
    mismatch_full_trial_number: bool = False,
) -> None:
    trial_count = 24
    stride = 5
    length = trial_count * stride
    starts = np.arange(0, length, stride, dtype=np.int64)
    stops = starts + 4
    lr_by_trial = np.asarray([-1, 1] * 12, dtype=np.int64)
    block_by_trial = np.full(trial_count, 5, dtype=np.int64)
    vr_block_by_trial = block_by_trial - full_block_offset
    if changed_offset_trial is not None:
        vr_block_by_trial[changed_offset_trial] -= 1
    timestamps = np.arange(length, dtype=np.float64) / 30.0

    aligned_signals = (
        "position",
        "speed",
        "licks",
        "reward",
        "block",
        "left or right",
        "trial start",
        "trial end",
        "trial number",
    )
    full_signals = (
        "position",
        "speed",
        "non-consummatory licks",
        "reward",
        "manual rewards",
        "block",
        "left or right",
        "trial start",
        "trial end",
        "trial number",
    )

    aligned: dict[str, np.ndarray] = {
        signal: np.zeros(length, dtype=np.float64) for signal in aligned_signals
    }
    full: dict[str, np.ndarray] = {
        signal: np.zeros(length, dtype=np.float64) for signal in full_signals
    }
    for index, (start, stop, lr) in enumerate(zip(starts, stops, lr_by_trial, strict=True)):
        sl = slice(start, stop)
        for values in (aligned, full):
            values["position"][sl] = np.asarray([30.0, 31.0, 32.0, 33.0])
            values["speed"][sl] = 2.0 + index
            values["left or right"][sl] = lr
            values["trial number"][sl] = index
            values["trial start"][start] = 1
            values["trial end"][stop] = 1
        aligned["block"][sl] = block_by_trial[index]
        full["block"][sl] = vr_block_by_trial[index]
        aligned["licks"][start + 1] = 1
        # Manual delivery censors the event at start+3 and every later sample.
        full["non-consummatory licks"][start + 1] = 1
        full["non-consummatory licks"][start + 3] = 7
        full["manual rewards"][start + 3] = 1
    if mismatch_full_lr:
        full["left or right"][starts[0] : stops[0]] = 1
    if mismatch_full_trial_number:
        full["trial number"][starts[0] : stops[0]] = 99
    if mismatch_aligned_block:
        aligned["block"][starts[0] : stops[0]] = 4

    metadata = {
        "day": day,
        "mouse": subject,
        "mux": False,
        "novel_arm": novel_arm,
        "trial_start_inds": starts.tolist(),
        "teleport_inds": stops.tolist(),
        "trial_info": {
            "block_number": block_by_trial.astype(float).tolist(),
            "LR": lr_by_trial.astype(float).tolist(),
        },
        "vr_trial_info": {
            "block_number": vr_block_by_trial.astype(float).tolist(),
            "LR": lr_by_trial.astype(float).tolist(),
        },
    }
    if mismatch_vr_block:
        metadata["vr_trial_info"]["block_number"][0] -= 1.0
    with h5py.File(path, "w") as nwb:
        nwb.create_dataset(RUNNER.SUBJECT_PATH, data=np.bytes_(subject))
        nwb.create_dataset(
            RUNNER.ANNOTATION_PATH,
            data=np.asarray([json.dumps(metadata).encode("utf-8")]),
        )
        fluorescence = np.column_stack(
            [np.arange(length, dtype=np.float64) + 100.0 * column for column in range(3)]
        )
        nwb.create_dataset(RUNNER.F_DFF_PATH, data=fluorescence)
        nwb.create_dataset(RUNNER.FLUORESCENCE_PATH, data=fluorescence)
        nwb.create_dataset(RUNNER.NEUROPIL_PATH, data=fluorescence)
        for prefix, signals in (
            (RUNNER.ALIGNED_PREFIX, aligned),
            (RUNNER.FULL_PREFIX, full),
        ):
            for signal, values in signals.items():
                nwb.create_dataset(f"{prefix}/{signal}/data", data=values)
                nwb.create_dataset(f"{prefix}/{signal}/timestamps", data=timestamps)


def test_trial_bin_rules_are_start_stop_and_open_left_closed_right() -> None:
    values = np.asarray([[100.0], [2.0], [3.0], [4.0], [999.0]])
    positions = np.asarray([13.0, 14.0, 43.0, 42.5, 14.0])
    result = RUNNER._trial_bin_means(
        values, positions, [_trial(0, -1, start=0, stop=4)], aligned=True
    )
    assert result[0, 0, 0] == 2.0
    assert result[0, 29, 0] == 3.5
    assert np.nansum(result) == 5.5


def test_fold_average_weights_trials_not_frames() -> None:
    values = np.asarray([[0.0], [10.0], [10.0], [10.0]])
    positions = np.full(4, 14.0)
    trials = [
        _trial(0, -1, start=0, stop=1),
        _trial(1, -1, start=1, stop=4),
    ]
    binned = RUNNER._trial_bin_means(values, positions, trials, aligned=True)
    assert RUNNER._equal_trial_nanmean(binned)[0, 0] == 5.0
    assert float(np.mean(values)) == 7.5


def test_fold_cycle_is_arm_local_and_requires_four_each() -> None:
    trials = [_trial(index, lr) for index, lr in enumerate([-1, 1] * 12)]
    folds = RUNNER._build_fold_ordinals(trials)
    assert folds[-1] == {"A": [0, 6, 12, 18], "B": [2, 8, 14, 20], "H": [4, 10, 16, 22]}
    assert folds[1] == {"A": [1, 7, 13, 19], "B": [3, 9, 15, 21], "H": [5, 11, 17, 23]}
    with pytest.raises(RUNNER.ContractBlocked, match="fold counts"):
        RUNNER._build_fold_ordinals(trials[:-1])


def test_unsorted_roi_columns_preserve_requested_pair_order(tmp_path: Path) -> None:
    path = tmp_path / "columns.h5"
    matrix = np.arange(20, dtype=np.float64).reshape(5, 4)
    with h5py.File(path, "w") as handle:
        handle.create_dataset("x", data=matrix)
    with h5py.File(path, "r") as handle:
        observed = RUNNER._read_roi_columns(handle["x"], np.asarray([2, 0, 3]))
    np.testing.assert_array_equal(observed, matrix[:, [2, 0, 3]])


def test_malformed_source_rows_and_neural_rank_map_to_contract_domains(tmp_path: Path) -> None:
    with pytest.raises(RUNNER.ContractBlocked) as bad_asset:
        RUNNER._validate_asset_rows([{"path": "x.nwb", "size": "bad", "sha256": "x"}], label="selection")
    assert bad_asset.value.status == "STX3_SOURCE_BLOCKED"

    path = tmp_path / "rank.h5"
    with h5py.File(path, "w") as handle:
        handle.create_dataset("x", data=np.arange(5))
    with h5py.File(path, "r") as handle:
        with pytest.raises(RUNNER.ContractBlocked) as bad_rank:
            RUNNER._read_roi_columns(handle["x"], np.asarray([0]))
    assert bad_rank.value.status == "STX3_SCHEMA_BLOCKED"

    with pytest.raises(RUNNER.ContractBlocked) as bad_event:
        RUNNER._event_indices(np.asarray(["not-a-number"], dtype=object), "start")
    assert bad_event.value.status == "STX3_TRIAL_JOIN_BLOCKED"
    with pytest.raises(RUNNER.ContractBlocked) as bad_integer:
        RUNNER._integer_array(["not-a-number"], "metadata")
    assert bad_integer.value.status == "STX3_SCHEMA_BLOCKED"


def test_independent_full_trial_join_rejects_lr_mismatch(tmp_path: Path) -> None:
    path = tmp_path / "fixture.nwb"
    _make_session_nwb(path, mismatch_full_lr=True)
    with pytest.raises(RUNNER.ContractBlocked) as caught:
        RUNNER.load_session(
            path,
            expected_subject="Ctrl_1",
            expected_day=0,
            expected_ravel=0,
            expected_novel_arm=-1,
            roi_indices=np.asarray([2, 0]),
        )
    assert caught.value.status == "STX3_TRIAL_JOIN_BLOCKED"


@pytest.mark.parametrize(
    ("subject", "novel_arm", "offset"),
    [("Cre_1", -1, 1), ("Ctrl_4", 1, 2)],
)
def test_locked_full_block_offsets_preserve_global_endpoint_blocks(
    tmp_path: Path, subject: str, novel_arm: int, offset: int
) -> None:
    path = tmp_path / f"{subject}.nwb"
    _make_session_nwb(
        path,
        subject=subject,
        novel_arm=novel_arm,
        full_block_offset=offset,
    )
    session = RUNNER.load_session(
        path,
        expected_subject=subject,
        expected_day=0,
        expected_ravel=0,
        expected_novel_arm=novel_arm,
        roi_indices=np.asarray([2, 0]),
    )
    assert session.full_block_offset == offset
    assert {trial.block for trial in session.trials} == {5}
    assert session.boundary_timing_ms == {
        "start_min": 0.0,
        "start_max": 0.0,
        "start_max_abs": 0.0,
        "end_min": 0.0,
        "end_max": 0.0,
        "end_max_abs": 0.0,
    }


def test_nonconstant_full_block_offset_is_fail_closed(tmp_path: Path) -> None:
    path = tmp_path / "nonconstant-offset.nwb"
    _make_session_nwb(
        path,
        subject="Ctrl_4",
        novel_arm=1,
        full_block_offset=2,
        changed_offset_trial=7,
    )
    with pytest.raises(RUNNER.ContractBlocked) as caught:
        RUNNER.load_session(
            path,
            expected_subject="Ctrl_4",
            expected_day=0,
            expected_ravel=0,
            expected_novel_arm=1,
            roi_indices=np.asarray([0, 1]),
        )
    assert caught.value.status == "STX3_TRIAL_JOIN_BLOCKED"
    assert "offset mismatch" in str(caught.value)


def test_constant_but_unlocked_full_block_offset_is_fail_closed(tmp_path: Path) -> None:
    path = tmp_path / "unlocked-offset.nwb"
    _make_session_nwb(path, full_block_offset=1)
    with pytest.raises(RUNNER.ContractBlocked) as caught:
        RUNNER.load_session(
            path,
            expected_subject="Ctrl_1",
            expected_day=0,
            expected_ravel=0,
            expected_novel_arm=-1,
            roi_indices=np.asarray([0, 1]),
        )
    assert caught.value.status == "STX3_TRIAL_JOIN_BLOCKED"
    assert "locked=0" in str(caught.value)


def test_vr_trial_metadata_must_match_full_block_stream(tmp_path: Path) -> None:
    path = tmp_path / "vr-full-mismatch.nwb"
    _make_session_nwb(path, mismatch_vr_block=True)
    with pytest.raises(RUNNER.ContractBlocked) as caught:
        RUNNER.load_session(
            path,
            expected_subject="Ctrl_1",
            expected_day=0,
            expected_ravel=0,
            expected_novel_arm=-1,
            roi_indices=np.asarray([0, 1]),
        )
    assert caught.value.status == "STX3_TRIAL_JOIN_BLOCKED"
    assert "metadata=" in str(caught.value)


def test_neural_trial_metadata_must_match_aligned_block_stream(tmp_path: Path) -> None:
    path = tmp_path / "neural-aligned-mismatch.nwb"
    _make_session_nwb(path, mismatch_aligned_block=True)
    with pytest.raises(RUNNER.ContractBlocked) as caught:
        RUNNER.load_session(
            path,
            expected_subject="Ctrl_1",
            expected_day=0,
            expected_ravel=0,
            expected_novel_arm=-1,
            roi_indices=np.asarray([0, 1]),
        )
    assert caught.value.status == "STX3_TRIAL_JOIN_BLOCKED"
    assert "metadata=" in str(caught.value)


def test_aligned_full_trial_number_identity_is_fail_closed(tmp_path: Path) -> None:
    path = tmp_path / "trial-number-mismatch.nwb"
    _make_session_nwb(path, mismatch_full_trial_number=True)
    with pytest.raises(RUNNER.ContractBlocked) as caught:
        RUNNER.load_session(
            path,
            expected_subject="Ctrl_1",
            expected_day=0,
            expected_ravel=0,
            expected_novel_arm=-1,
            roi_indices=np.asarray([0, 1]),
        )
    assert caught.value.status == "STX3_TRIAL_JOIN_BLOCKED"
    assert "aligned/full number mismatch" in str(caught.value)


def test_manual_reward_censors_postdelivery_licks(tmp_path: Path) -> None:
    path = tmp_path / "fixture.nwb"
    _make_session_nwb(path)
    session = RUNNER.load_session(
        path,
        expected_subject="Ctrl_1",
        expected_day=0,
        expected_ravel=0,
        expected_novel_arm=-1,
        roi_indices=np.asarray([2, 0]),
    )
    assert session.neural_bins.shape[-1] == 2
    assert session.behavior[0]["whole_licks"] == 1.0
    assert session.behavior[0]["omitted"] is False


def test_event_and_trial_labels_reject_nonfinite_or_nonbinary_values() -> None:
    with pytest.raises(RUNNER.ContractBlocked) as nonfinite:
        RUNNER._event_indices(np.asarray([0.0, np.nan, 1.0]), "start")
    assert nonfinite.value.status == "STX3_TRIAL_JOIN_BLOCKED"
    with pytest.raises(RUNNER.ContractBlocked, match="binary"):
        RUNNER._event_indices(np.asarray([0.0, 2.0, 1.0]), "start")
    with pytest.raises(RUNNER.ContractBlocked, match="missing/nonfinite"):
        RUNNER._finite_unique(np.asarray([5.0, np.nan, 5.0]), "block")


def test_nonfinite_reward_marker_blocks_instead_of_becoming_omission(tmp_path: Path) -> None:
    path = tmp_path / "fixture.nwb"
    _make_session_nwb(path)
    with h5py.File(path, "r+") as nwb:
        nwb[f"{RUNNER.FULL_PREFIX}/manual rewards/data"][2] = np.nan
    with pytest.raises(RUNNER.ContractBlocked) as caught:
        RUNNER.load_session(
            path,
            expected_subject="Ctrl_1",
            expected_day=0,
            expected_ravel=0,
            expected_novel_arm=-1,
            roi_indices=np.asarray([2, 0]),
        )
    assert caught.value.status == "STX3_SCHEMA_BLOCKED"
    assert "nonfinite reward" in str(caught.value)


def test_optional_reward_front_annotation_must_match_frozen_values() -> None:
    RUNNER._validate_optional_reward_fronts(
        {"reward_zone_fronts": [RUNNER.LEFT_TFRONT, RUNNER.RIGHT_TFRONT]},
        Path("fixture.nwb"),
    )
    with pytest.raises(RUNNER.ContractBlocked) as caught:
        RUNNER._validate_optional_reward_fronts(
            {"reward_zone_fronts": [RUNNER.LEFT_TFRONT, 999.0]},
            Path("fixture.nwb"),
        )
    assert caught.value.status == "STX3_SCHEMA_BLOCKED"


def test_hand_calculated_crossvalidated_bilinear_proxy_and_shift_geometry() -> None:
    precision = np.ones(20)
    sessions: dict[int, object] = {}
    arrays: dict[int, np.ndarray] = {}
    for day, left_value in ((0, 2.0), (5, 3.0)):
        array = np.zeros((4, RUNNER.N_BINS, 20), dtype=np.float64)
        for fold_trial in (0, 1):
            array[fold_trial, RUNNER.LEFT_REWARD_FULL, 0] = left_value
        for fold_trial in (2, 3):
            array[fold_trial, RUNNER.RIGHT_REWARD_FULL, 0] = 1.0
        sessions[day] = _minimal_session(day, array)
        arrays[day] = array
    result = RUNNER.reward_alignment_bilinear_proxy(sessions, arrays, precision)
    assert result["day"]["0"]["true_bilinear_score"] == pytest.approx(0.05)
    assert result["day"]["0"]["wrong_shift_bilinear_median"] == pytest.approx(0.20)
    assert result["day"]["5"]["G"] == pytest.approx(0.25)
    assert result["delta_G"] == pytest.approx(0.10)


def test_rate_demean_removes_additive_common_gain_and_rejects_partial_vector() -> None:
    base = np.asarray([[[1.0, 2.0, 4.0], [3.0, 5.0, 9.0]]])
    shifted = base + 17.0
    np.testing.assert_allclose(RUNNER._cell_axis_demean(base), RUNNER._cell_axis_demean(shifted))
    partial = base.copy()
    partial[0, 0, 1] = np.nan
    assert np.all(np.isnan(RUNNER._cell_axis_demean(partial)[0, 0]))


def test_sensitivity_endpoint_rejects_any_required_trial_vector_nan() -> None:
    array = np.zeros((8, RUNNER.N_BINS, 20), dtype=float)
    trials = [_trial(index, -1 if index < 4 else 1) for index in range(8)]
    session = RUNNER.SessionData(
        subject="Ctrl_1",
        day=0,
        path=Path("fixture.nwb"),
        roi_indices=np.arange(20),
        trials=trials,
        neural_bins=array,
        speed_bins=np.zeros(array.shape[:2]),
        lick_bins=np.zeros(array.shape[:2]),
        behavior=[],
        fold_ordinals={
            -1: {"A": [0, 1], "B": [2, 3], "H": []},
            1: {"A": [4, 5], "B": [6, 7], "H": []},
        },
    )
    array[0, RUNNER.LEFT_REWARD_FULL[0], 0] = np.nan
    with pytest.raises(RUNNER.ContractBlocked) as caught:
        RUNNER._validate_endpoint_trial_vectors(array, session, variant="S_rate")
    assert caught.value.status == "STX3_NUMERICAL_BLOCKED"


def test_mapped_roi_endpoint_incompleteness_blocks_instead_of_selecting_cells() -> None:
    day0_array = np.zeros((4, RUNNER.N_BINS, 20), dtype=float)
    day5_array = day0_array.copy()
    complete_sessions = {
        0: _minimal_session(0, day0_array),
        5: _minimal_session(5, day5_array),
    }
    np.testing.assert_array_equal(
        RUNNER._require_complete_endpoint_population(
            complete_sessions, subject="Ctrl_1"
        ),
        np.ones(20, dtype=bool),
    )
    day5_array[0, RUNNER.LEFT_REWARD_FULL[0], 7] = np.nan
    with pytest.raises(RUNNER.ContractBlocked) as caught:
        RUNNER._require_complete_endpoint_population(
            complete_sessions, subject="Ctrl_1"
        )
    assert caught.value.status == "STX3_REGISTRATION_BLOCKED"
    assert "endpoint-based cell deletion is forbidden" in str(caught.value)


def test_zero_variance_roi_is_retained_by_precision_floor() -> None:
    training = np.asarray(
        [
            [5.0, 0.0, 0.0],
            [5.0, 1.0, 2.0],
            [5.0, 2.0, 4.0],
            [5.0, 10.0, 20.0],
            [5.0, 11.0, 22.0],
            [5.0, 12.0, 24.0],
        ]
    )
    result = RUNNER._estimate_precision(training, np.asarray([0, 0, 0, 1, 1, 1]))
    assert result["precision"].shape == (3,)
    assert result["variance_min"] == pytest.approx(0.0)
    assert np.all(np.isfinite(result["precision"]))
    assert result["precision"][0] == pytest.approx(1.0 / result["variance_floor"])


def test_fwl_recovers_known_speed_and_lick_coefficients() -> None:
    speed = np.asarray([-1, 1, -1, 1, -1, 1, -1, 1], dtype=float)
    lick = np.asarray([-1, -1, 1, 1, -1, -1, 1, 1], dtype=float)
    codes = np.asarray([0, 0, 0, 0, 1, 1, 1, 1])
    category_intercept = np.where(codes == 0, 10.0, -3.0)
    beta = np.asarray([2.0, 3.0])
    gamma = np.asarray([4.0, 5.0])
    response = category_intercept[:, None] + speed[:, None] * beta + lick[:, None] * gamma
    result = RUNNER._fit_motor_coefficients(response, codes, speed, lick)
    np.testing.assert_allclose(result["beta"], beta)
    np.testing.assert_allclose(result["gamma"], gamma)
    with pytest.raises(RUNNER.ContractBlocked, match="lick SD"):
        RUNNER._fit_motor_coefficients(response, codes, speed, np.ones_like(lick))
    with pytest.raises(RUNNER.ContractBlocked, match="design rank"):
        RUNNER._fit_motor_coefficients(response, codes, speed, speed.copy())


def test_behavior_uses_pooled_event_ratio_and_equal_arm_weight() -> None:
    records = []
    for ordinal, lr, whole, pre, speed in (
        (0, -1, 1, 1, 1),
        (1, -1, 9, 0, 3),
        (2, 1, 0, 0, 7),
        (3, 1, 0, 0, 9),
    ):
        records.append(
            {
                "ordinal": ordinal,
                "lr": lr,
                "block": 5,
                "whole_licks": float(whole),
                "pre_licks": float(pre),
                "whole_speed": float(speed),
                "omitted": False,
            }
        )
    array = np.zeros((4, RUNNER.N_BINS, 20))
    session = _minimal_session(0, array)
    session.behavior = records
    session.fold_ordinals = {
        -1: {"A": [], "B": [], "H": [0, 1]},
        1: {"A": [], "B": [], "H": [2, 3]},
    }
    result = RUNNER.heldout_behavior(session)
    assert result["arms"]["-1"]["concentration"] == pytest.approx(0.1)
    assert result["arms"]["1"]["concentration"] == 0.0
    assert result["B"] == pytest.approx(0.05)
    assert result["speed"] == pytest.approx(5.0)


def test_exact_label_p_includes_observed_assignment_without_add_one() -> None:
    groups = np.asarray(["Ctrl"] * 9 + ["Cre"] * 7)
    values = np.asarray([1.0] * 9 + [0.0] * 7)
    result = RUNNER.exact_group_label_test(values, groups)
    assert result["permutation_count"] == 11_440
    assert result["extreme_count"] == 1
    assert result["p_one_sided_exact"] == pytest.approx(1 / 11_440)


def test_midrank_association_replays_fixed_within_group_orders() -> None:
    groups = np.asarray(["Ctrl"] * 9 + ["Cre"] * 7)
    geometry = np.asarray([0, 0, 1, 2, 3, 4, 5, 6, 7, 0, 1, 1, 2, 3, 4, 5], dtype=float)
    behavior = geometry + np.asarray([0, 1] * 8, dtype=float) * 0.1
    orders = RUNNER._within_group_permutation_indices(groups, permutations=31, seed=17)
    first = RUNNER.treatment_adjusted_rank_association(
        geometry,
        behavior,
        groups,
        permutations=31,
        seed=17,
        permutation_indices=orders,
    )
    second = RUNNER.treatment_adjusted_rank_association(
        geometry,
        behavior,
        groups,
        permutations=31,
        seed=17,
        permutation_indices=orders,
    )
    assert first == second
    assert first["statistic_partial_spearman"] > 0
    assert first["permutation_scheme"] == (
        "freedman_lane_rank_residual_within_observed_group"
    )


def _freedman_lane_fixture() -> tuple[np.ndarray, ...]:
    groups = np.asarray(["Ctrl"] * 9 + ["Cre"] * 7)
    geometry = np.asarray(
        [11, 3, 15, 1, 8, 13, 5, 16, 6, 10, 2, 14, 4, 12, 7, 9],
        dtype=float,
    )
    behavior = np.asarray(
        [2, 5, 1, 9, 4, 8, 3, 7, 6, 13, 10, 16, 11, 15, 12, 14],
        dtype=float,
    )
    speed = np.asarray(
        [1, 2, 3, 4, 5, 6, 7, 8, 9, 1.5, 2.5, 3.5, 4.5, 5.5, 6.5, 7.5],
        dtype=float,
    )
    orders = np.asarray(
        [
            [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15],
            [8, 0, 1, 2, 3, 4, 5, 6, 7, 10, 11, 12, 13, 14, 15, 9],
            [8, 7, 6, 5, 4, 3, 2, 1, 0, 15, 14, 13, 12, 11, 10, 9],
            [1, 0, 3, 2, 5, 4, 7, 8, 6, 10, 9, 12, 11, 14, 13, 15],
        ],
        dtype=np.int64,
    )
    return geometry, behavior, speed, groups, orders


def test_freedman_lane_matches_manual_rank_residual_calculation() -> None:
    geometry, behavior, speed, groups, orders = _freedman_lane_fixture()
    x = RUNNER.rankdata(geometry, method="average")
    y = RUNNER.rankdata(behavior, method="average")
    controls = np.column_stack(
        [
            np.ones(16),
            (groups == "Cre").astype(float),
            RUNNER.rankdata(speed, method="average"),
        ]
    )
    residualizer = RUNNER._residualizer(controls)
    x_residual = residualizer @ x
    y_residual = residualizer @ y
    y_fitted = y - y_residual
    manual_statistics = []
    for order in orders:
        pseudo_residual = residualizer @ (y_fitted + y_residual[order])
        manual_statistics.append(
            np.dot(x_residual, pseudo_residual)
            / (np.linalg.norm(x_residual) * np.linalg.norm(pseudo_residual))
        )
    np.testing.assert_allclose(
        manual_statistics,
        [
            0.11023976098599614,
            -0.3141355103686881,
            0.2800840798116944,
            0.10090746164172845,
        ],
    )
    result = RUNNER.treatment_adjusted_rank_association(
        geometry,
        behavior,
        groups,
        speed=speed,
        permutations=4,
        permutation_indices=orders,
    )
    assert result["statistic_partial_spearman"] == pytest.approx(manual_statistics[0])
    assert result["extreme_count"] == 2
    assert result["p_one_sided_monte_carlo"] == pytest.approx(3 / 5)


def test_speed_confounded_raw_rank_permutation_differs_from_freedman_lane() -> None:
    geometry, behavior, speed, groups, orders = _freedman_lane_fixture()
    x = RUNNER.rankdata(geometry, method="average")
    y = RUNNER.rankdata(behavior, method="average")
    controls = np.column_stack(
        [
            np.ones(16),
            (groups == "Cre").astype(float),
            RUNNER.rankdata(speed, method="average"),
        ]
    )
    residualizer = RUNNER._residualizer(controls)
    x_residual = residualizer @ x
    raw_statistics = []
    for order in orders:
        raw_residual = residualizer @ y[order]
        raw_statistics.append(
            np.dot(x_residual, raw_residual)
            / (np.linalg.norm(x_residual) * np.linalg.norm(raw_residual))
        )
    np.testing.assert_allclose(
        raw_statistics,
        [
            0.11023976098599614,
            -0.24784488246610173,
            0.2790619741811728,
            0.19600018321580148,
        ],
    )
    assert raw_statistics[1] != pytest.approx(-0.3141355103686881)


def test_status_precedence_requires_robust_three_variant_conjunction() -> None:
    positive = {
        "conjunction_pass": True,
        "geometry": {"statistic_mean_ctrl_minus_cre": 1.0, "direction_positive": True, "p_one_sided_exact": 0.01},
        "association": {"statistic_partial_spearman": 0.5, "direction_positive": True},
    }
    results = {"primary": positive, "S_rate": positive, "S_motor": positive}
    assert RUNNER._final_status(results).endswith("CONFOUND_ROBUST_SUPPORTED")
    reversed_motor = {**positive, "geometry": {**positive["geometry"], "statistic_mean_ctrl_minus_cre": -0.1}}
    results = {"primary": positive, "S_rate": positive, "S_motor": reversed_motor}
    assert RUNNER._final_status(results).endswith("CONFOUND_COMPATIBLE_FAIL")
    null_primary = {
        **positive,
        "conjunction_pass": False,
        "geometry": {**positive["geometry"], "direction_positive": False, "p_one_sided_exact": 0.9},
    }
    reversed_association = {
        **positive,
        "conjunction_pass": False,
        "association": {"statistic_partial_spearman": -0.01, "direction_positive": False},
    }
    results = {"primary": positive, "S_rate": positive, "S_motor": reversed_association}
    assert RUNNER._final_status(results).endswith(
        "PRIMARY_ONLY_CONFOUND_SENSITIVE_NO_EVIDENCE_ELEVATION"
    )
    results = {"primary": null_primary, "S_rate": positive, "S_motor": reversed_association}
    assert RUNNER._final_status(results) == "STX3_COMPONENT_CONJUNCTION_NOT_SUPPORTED"
    assert RUNNER._primary_status(null_primary) == "STX3_PRIMARY_COMPONENT_CONJUNCTION_NOT_SUPPORTED"


def test_runtime_roi_reaudit_compares_pickle_and_ordered_pair_hashes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    subjects = ("Ctrl_1",)
    record = {
        "subject": "Ctrl_1",
        "group": "Ctrl",
        "pickle_sha256": "pickle",
        "day0_ravel_ind": 0,
        "day5_ravel_ind": 5,
        "common_roi_count": 20,
        "day0_roi_min": 0,
        "day0_roi_max": 19,
        "day5_roi_min": 0,
        "day5_roi_max": 19,
        "ordered_pairs_sha256": "pairs",
    }
    frozen = {
        "status": "STX3_ROI_ALIGNER_AUDIT_PASS",
        "canonical_day0_day5_pairs_sha256": "canonical",
        "subject_count": 1,
        "subjects": [record],
    }
    audit_path = tmp_path / "roi.json"
    audit_path.write_text(json.dumps(frozen), encoding="utf-8")
    monkeypatch.setattr(RUNNER, "SUBJECTS", subjects)
    monkeypatch.setattr(RUNNER, "ROI_AUDIT_SHA256", RUNNER.file_sha256(audit_path))
    monkeypatch.setattr(RUNNER, "ROI_PAIR_CANONICAL_SHA256", "canonical")
    monkeypatch.setattr(
        RUNNER,
        "audit_dense_maps",
        lambda root, minimum_common_rois: {**frozen, "subjects": [dict(record)]},
    )
    result = RUNNER.validate_runtime_roi_inputs(tmp_path, audit_path)
    assert result["subject_count"] == 1

    changed = dict(record)
    changed["pickle_sha256"] = "changed"
    monkeypatch.setattr(
        RUNNER,
        "audit_dense_maps",
        lambda root, minimum_common_rois: {**frozen, "subjects": [changed]},
    )
    with pytest.raises(RUNNER.ContractBlocked) as caught:
        RUNNER.validate_runtime_roi_inputs(tmp_path, audit_path)
    assert caught.value.status == "STX3_REGISTRATION_BLOCKED"


def test_frozen_code_source_hash_chain_rejects_tamper(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    contract = tmp_path / "contract.md"
    prior_addendum = tmp_path / "prior.md"
    statistical_addendum = tmp_path / "statistical.md"
    addendum = tmp_path / "current.md"
    blocked_preflight = tmp_path / "blocked-preflight.json"
    selection = tmp_path / "selection.json"
    official_root = tmp_path / "official"
    twoputils_root = tmp_path / "twoputils"
    official_root.mkdir()
    twoputils_root.mkdir()
    for path, value in (
        (contract, "contract"),
        (prior_addendum, "prior"),
        (statistical_addendum, "statistical"),
        (addendum, "current"),
        (selection, "selection"),
    ):
        path.write_text(value, encoding="utf-8")
    source_paths = {
        "mouse_metadata": official_root / "mouse_metadata.py",
        "official_session": official_root / "session.py",
        "official_behavior": official_root / "behavior.py",
        "official_utilities": official_root / "utilities.py",
        "official_reward_overrep": official_root / "reward_overrep.py",
        "twoputils_spatial_analyses": twoputils_root / "spatial_analyses.py",
        "twoputils_sess": twoputils_root / "sess.py",
    }
    for label, path in source_paths.items():
        path.write_text(label, encoding="utf-8")
    monkeypatch.setattr(RUNNER, "BASE_CONTRACT_SHA256", RUNNER.file_sha256(contract))
    monkeypatch.setattr(
        RUNNER, "PRIOR_ADDENDUM_SHA256", RUNNER.file_sha256(prior_addendum)
    )
    monkeypatch.setattr(
        RUNNER,
        "STATISTICAL_ADDENDUM_SHA256",
        RUNNER.file_sha256(statistical_addendum),
    )
    monkeypatch.setattr(RUNNER, "ADDENDUM_SHA256", RUNNER.file_sha256(addendum))
    blocked_preflight.write_text(
        json.dumps(
            {
                "status": "STX3_TRIAL_JOIN_BLOCKED",
                "biological_endpoint_evaluated": False,
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(
        RUNNER,
        "BLOCKED_PREFLIGHT_RECEIPT_SHA256",
        RUNNER.file_sha256(blocked_preflight),
    )
    monkeypatch.setattr(
        RUNNER, "SELECTION_RECEIPT_SHA256", RUNNER.file_sha256(selection)
    )
    constant_by_label = {
        "mouse_metadata": "MOUSE_METADATA_SHA256",
        "official_session": "OFFICIAL_SESSION_SHA256",
        "official_behavior": "OFFICIAL_BEHAVIOR_SHA256",
        "official_utilities": "OFFICIAL_UTILITIES_SHA256",
        "official_reward_overrep": "OFFICIAL_REWARD_OVERREP_SHA256",
        "twoputils_spatial_analyses": "TWOPUTILS_SPATIAL_ANALYSES_SHA256",
        "twoputils_sess": "TWOPUTILS_SESS_SHA256",
    }
    for label, constant in constant_by_label.items():
        monkeypatch.setattr(RUNNER, constant, RUNNER.file_sha256(source_paths[label]))
    monkeypatch.setattr(RUNNER, "DENSE_DAY0_DAY5_RAVEL", {})
    monkeypatch.setattr(RUNNER, "ROI_PAIR_CANONICAL_SHA256", "pairs")
    roi_audit = tmp_path / "roi-audit.json"
    roi_audit.write_text(
        json.dumps(
            {
                "status": "STX3_ROI_ALIGNER_AUDIT_PASS",
                "canonical_day0_day5_pairs_sha256": "pairs",
                "subjects": [],
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(RUNNER, "ROI_AUDIT_SHA256", RUNNER.file_sha256(roi_audit))
    frozen = RUNNER.validate_frozen_inputs(
        contract,
        prior_addendum,
        statistical_addendum,
        addendum,
        blocked_preflight,
        roi_audit,
        official_root,
        twoputils_root,
        source_paths["mouse_metadata"],
        selection,
    )
    assert frozen["twoputils_sess_sha256"] == RUNNER.TWOPUTILS_SESS_SHA256
    source_paths["official_session"].write_text("tampered", encoding="utf-8")
    with pytest.raises(RUNNER.ContractBlocked) as caught:
        RUNNER.validate_frozen_inputs(
            contract,
            prior_addendum,
            statistical_addendum,
            addendum,
            blocked_preflight,
            roi_audit,
            official_root,
            twoputils_root,
            source_paths["mouse_metadata"],
            selection,
        )
    assert caught.value.status == "STX3_SOURCE_BLOCKED"
    assert "official_session hash mismatch" in str(caught.value)


def test_preflight_visits_every_subject_day_before_any_endpoint(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    subjects = ("Ctrl_1", "Cre_1")
    monkeypatch.setattr(RUNNER, "SUBJECTS", subjects)
    calls: list[tuple[str, int]] = []
    monkeypatch.setattr(
        RUNNER,
        "_load_locked_day_pair",
        lambda root, subject: (np.arange(20), np.arange(20), 0, 5),
    )

    def fake_load(path: Path, **kwargs):
        subject = kwargs["expected_subject"]
        day = kwargs["expected_day"]
        calls.append((subject, day))
        arrays = np.zeros((4, RUNNER.N_BINS, 20))
        session = _minimal_session(day, arrays)
        session.subject = subject
        return session

    monkeypatch.setattr(RUNNER, "load_session", fake_load)
    assets = {
        (subject, day): {"local_path": tmp_path / f"{subject}_{day}.nwb", "sha256": f"{subject}-{day}"}
        for subject in subjects
        for day in (0, 5)
    }
    summaries = RUNNER.preflight_all_sessions(assets, tmp_path)
    assert calls == [("Ctrl_1", 0), ("Ctrl_1", 5), ("Cre_1", 0), ("Cre_1", 5)]
    assert len(summaries) == 4


def test_preflight_receipt_binds_script_environment_and_every_session_pass(
    tmp_path: Path,
) -> None:
    preflight_script = RUNNER_PATH.with_name("preflight_stx3_reward_alignment_v1_1.py")
    data_root = tmp_path / "data"
    roi_root = tmp_path / "roi"
    official_code_root = tmp_path / "official-code"
    twoputils_root = tmp_path / "twoputils"
    summaries = [
        {
            "subject": subject,
            "day": day,
            "mapped_common_roi_count": 20,
            "full_block_offset": RUNNER.LOCKED_FULL_BLOCK_OFFSETS[(subject, day)],
            "cross_family_boundary_timing_ms": {
                "start_min": 0.0,
                "start_max": 0.0,
                "start_max_abs": 0.0,
                "end_min": 0.0,
                "end_max": 0.0,
                "end_max_abs": 0.0,
            },
            "structural_validation": "PASS",
        }
        for subject in RUNNER.SUBJECTS
        for day in (0, 5)
    ]
    receipt = {
        "status": RUNNER.PREFLIGHT_STATUS,
        "contract_id": RUNNER.CONTRACT_ID,
        "biological_endpoint_evaluated": False,
        "preflight_script": preflight_script.resolve().as_posix(),
        "preflight_script_sha256": RUNNER.file_sha256(preflight_script),
        "runner_sha256": RUNNER.file_sha256(RUNNER_PATH),
        "roi_audit_module_sha256": RUNNER.file_sha256(Path(RUNNER.roi_audit_module.__file__).resolve()),
        "selection_receipt_sha256": "selection",
        "download_receipt_sha256": "download",
        "resolved_data_root": data_root.resolve().as_posix(),
        "resolved_roi_root": roi_root.resolve().as_posix(),
        "resolved_official_code_root": official_code_root.resolve().as_posix(),
        "resolved_twoputils_root": twoputils_root.resolve().as_posix(),
        "subject_count": 16,
        "session_count": 32,
        "session_summaries": summaries,
        "source_integrity": {"asset_count": 32, "total_bytes": 20_006_552_508},
        "runtime_roi": {
            "canonical_day0_day5_pairs_sha256": RUNNER.ROI_PAIR_CANONICAL_SHA256,
            "subject_count": 16,
        },
        "frozen_inputs": {
            "base_contract_sha256": RUNNER.BASE_CONTRACT_SHA256,
            "prior_addendum_sha256": RUNNER.PRIOR_ADDENDUM_SHA256,
            "statistical_addendum_sha256": RUNNER.STATISTICAL_ADDENDUM_SHA256,
            "addendum_sha256": RUNNER.ADDENDUM_SHA256,
            "blocked_preflight_receipt_sha256": (
                RUNNER.BLOCKED_PREFLIGHT_RECEIPT_SHA256
            ),
            "full_block_offset_map_sha256": RUNNER.FULL_BLOCK_OFFSET_MAP_SHA256,
            "mouse_metadata_sha256": RUNNER.MOUSE_METADATA_SHA256,
            "official_session_sha256": RUNNER.OFFICIAL_SESSION_SHA256,
            "official_behavior_sha256": RUNNER.OFFICIAL_BEHAVIOR_SHA256,
            "official_utilities_sha256": RUNNER.OFFICIAL_UTILITIES_SHA256,
            "official_reward_overrep_sha256": RUNNER.OFFICIAL_REWARD_OVERREP_SHA256,
            "twoputils_spatial_analyses_sha256": (
                RUNNER.TWOPUTILS_SPATIAL_ANALYSES_SHA256
            ),
            "twoputils_sess_sha256": RUNNER.TWOPUTILS_SESS_SHA256,
            "selection_receipt_sha256": RUNNER.SELECTION_RECEIPT_SHA256,
            "roi_audit_sha256": RUNNER.ROI_AUDIT_SHA256,
        },
        "environment": {
            "python_executable": Path(sys.executable).resolve().as_posix(),
            "python_version": RUNNER.platform.python_version(),
            "numpy_version": RUNNER.np.__version__,
            "scipy_version": RUNNER.scipy.__version__,
            "h5py_version": RUNNER.h5py.__version__,
        },
    }
    path = tmp_path / "preflight.json"
    path.write_text(json.dumps(receipt), encoding="utf-8")
    RUNNER._validate_preflight_receipt(
        path,
        preflight_script_path=preflight_script,
        runner_hash=receipt["runner_sha256"],
        audit_module_hash=receipt["roi_audit_module_sha256"],
        selection_hash="selection",
        download_receipt_hash="download",
        data_root=data_root,
        roi_root=roi_root,
        official_code_root=official_code_root,
        twoputils_root=twoputils_root,
    )
    receipt["session_summaries"][0]["structural_validation"] = "FAIL"
    path.write_text(json.dumps(receipt), encoding="utf-8")
    with pytest.raises(RUNNER.ContractBlocked) as caught:
        RUNNER._validate_preflight_receipt(
            path,
            preflight_script_path=preflight_script,
            runner_hash=receipt["runner_sha256"],
            audit_module_hash=receipt["roi_audit_module_sha256"],
            selection_hash="selection",
            download_receipt_hash="download",
            data_root=data_root,
            roi_root=roi_root,
            official_code_root=official_code_root,
            twoputils_root=twoputils_root,
        )
    assert caught.value.status == "STX3_PREFLIGHT_BLOCKED"


def test_lock_parser_rejects_duplicate_keys_and_attempt_marker_is_exclusive(
    tmp_path: Path,
) -> None:
    lock_path = tmp_path / "lock.tsv"
    lock_path.write_text("x\t1\nx\t2\n", encoding="utf-8")
    with pytest.raises(RUNNER.ContractBlocked, match="duplicate"):
        RUNNER._parse_execution_lock(lock_path)

    marker = tmp_path / "attempt.json"
    RUNNER._create_attempt_marker(marker, {"attempt_id": "one"})
    with pytest.raises(RUNNER.ContractBlocked) as caught:
        RUNNER._create_attempt_marker(marker, {"attempt_id": "two"})
    assert caught.value.status == "STX3_ONE_SHOT_ALREADY_CONSUMED"


def test_test_receipt_requires_the_complete_focused_suite(tmp_path: Path) -> None:
    runner_hash = RUNNER.file_sha256(RUNNER_PATH)
    receipt = {
        "status": RUNNER.TEST_STATUS,
        "contract_id": RUNNER.CONTRACT_ID,
        "exit_code": 0,
        "collected": RUNNER.EXPECTED_FOCUSED_TEST_COUNT,
        "passed": RUNNER.EXPECTED_FOCUSED_TEST_COUNT,
        "failed": 0,
        "errors": 0,
        "skipped": 0,
        "deselected": 0,
        "runner_sha256": runner_hash,
        "test_file_sha256": RUNNER.file_sha256(Path(__file__).resolve()),
    }
    path = tmp_path / "tests.json"
    path.write_text(json.dumps(receipt), encoding="utf-8")
    RUNNER._validate_test_receipt(path, runner_hash=runner_hash)
    receipt.update(
        {
            "collected": 1,
            "passed": 1,
            "deselected": RUNNER.EXPECTED_FOCUSED_TEST_COUNT - 1,
        }
    )
    path.write_text(json.dumps(receipt), encoding="utf-8")
    with pytest.raises(RUNNER.ContractBlocked) as caught:
        RUNNER._validate_test_receipt(path, runner_hash=runner_hash)
    assert caught.value.status == "STX3_TEST_BLOCKED"
