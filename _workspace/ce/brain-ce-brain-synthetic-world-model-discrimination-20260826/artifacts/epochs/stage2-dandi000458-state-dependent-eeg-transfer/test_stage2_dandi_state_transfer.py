"""Synthetic-only tests; never open the real DANDI EEG values."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import numpy as np
import pytest


MODULE_PATH = Path(__file__).with_name("stage2_dandi_state_transfer.py")
SPEC = importlib.util.spec_from_file_location("stage2_dandi_state_transfer", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
stage2 = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(stage2)


def test_nearest_origins_and_timing_gate() -> None:
    timestamps = np.arange(20, dtype=float) / stage2.FS
    assert stage2.nearest_origins(timestamps, np.asarray([2.1 / stage2.FS])).tolist() == [2]
    with pytest.raises(RuntimeError, match="timing"):
        stage2.nearest_origins(timestamps, np.asarray([-1.0]))
    with pytest.raises(RuntimeError, match="non-unique"):
        stage2.nearest_origins(timestamps, np.asarray([2.5 / stage2.FS]))


def test_electrical_series_mapping_is_explicit() -> None:
    valid = np.zeros(30, dtype=bool)
    valid[list(stage2.VALID_CHANNELS)] = True
    rows = np.arange(30)
    assert stage2.valid_series_columns(
        rows, valid, "/general/extracellular_ephys/electrodes"
    ) == stage2.VALID_CHANNELS
    with pytest.raises(RuntimeError, match="table reference"):
        stage2.valid_series_columns(rows, valid, "/wrong/table")
    with pytest.raises(RuntimeError, match="channel columns"):
        stage2.valid_series_columns(rows[::-1], valid, "/general/extracellular_ephys/electrodes")


def test_registered_timestamp_gap_profile() -> None:
    deltas = np.full(125_400, 1.0 / stage2.FS)
    deltas[125_307] *= 2
    timestamps = np.concatenate(([0.0], np.cumsum(deltas)))
    median, segment_start = stage2.validate_timestamp_profile(timestamps)
    assert median == pytest.approx(1.0 / stage2.FS)
    assert segment_start == 125_308
    deltas[100] *= 2
    with pytest.raises(RuntimeError, match="uniformity"):
        stage2.validate_timestamp_profile(np.concatenate(([0.0], np.cumsum(deltas))))


def test_registered_split_count_logic() -> None:
    ids = np.arange(12)
    states = np.asarray(["awake"] * 6 + ["isoflurane"] * 6)
    currents = np.asarray([20, 20, 50, 50, 100, 100] * 2)
    counts = stage2.split_counts(ids, states, currents, np.ones(12, dtype=bool))
    assert sum(counts.values()) == 12
    assert counts["awake/20/development"] == 1
    assert counts["isoflurane/100/confirmation"] == 1


def test_artifact_replacement_is_exact_and_local() -> None:
    signal = np.arange(30, dtype=float)
    stage2.replace_artifacts(signal, np.asarray([10]))
    assert signal[10:15].tolist() == [5, 6, 7, 8, 9]
    assert signal[:10].tolist() == list(range(10))
    assert signal[15:].tolist() == list(range(15, 30))


def test_finish_waveforms_car_baseline_and_shape() -> None:
    rng = np.random.default_rng(1)
    response = rng.normal(size=(3, 249, 17))
    baseline = rng.normal(size=(3, 17))
    finished = stage2.finish_waveforms(response, baseline)
    assert finished.shape == (3, 249, 17)
    assert np.allclose(finished.mean(axis=2), 0.0, atol=1e-12)
    with pytest.raises(RuntimeError, match="shape"):
        stage2.finish_waveforms(response[:, :-1], baseline)


def test_global_gain_is_compatible_and_deterministic() -> None:
    rng = np.random.default_rng(2)
    awake = rng.normal(size=(24, 249, 17))
    first = stage2.current_statistics(awake, 2.0 * awake, 20)
    second = stage2.current_statistics(awake, 2.0 * awake, 20)
    assert first == second
    assert first["alpha_nonnegative_global_gain"] == pytest.approx(2.0)
    assert first["R_mean_waveform_gain_residual"] < 1e-12
    assert first["permutation_p"] > 0.05


def test_state_mean_cancellation_fails_closed() -> None:
    vector = np.ones((249, 17))
    cancelling = np.stack([vector, -vector] * 10)
    valid = np.stack([vector] * 20)
    with pytest.raises(RuntimeError, match="state mean"):
        stage2.current_statistics(cancelling, valid, 20)


def test_decision_partition_and_revised_names() -> None:
    def row(p_value: float, residual: float) -> dict[str, float]:
        return {"permutation_p": p_value, "R_mean_waveform_gain_residual": residual}

    compatible = {current: row(0.1, 0.01) for current in stage2.CURRENTS}
    assert stage2.decide(compatible) == "STAGE2_GLOBAL_GAIN_COMPATIBLE_AT_REGISTERED_RESOLUTION"
    difference = {20: row(0.01, 0.2), 50: row(0.01, 0.2), 100: row(0.05, 0.01)}
    assert stage2.decide(difference) == "STAGE2_STATE_ASSOCIATED_TRANSFER_DIFFERENCE"
    tension = {20: row(0.01, 0.2), 50: row(0.2, 0.01), 100: row(0.2, 0.01)}
    assert stage2.decide(tension) == "STAGE2_TRANSFER_TENSION"


def test_manifest_file_map_rejects_mutation(tmp_path: Path) -> None:
    files = {}
    for relative in stage2.PREREGISTERED_FILES:
        path = tmp_path / relative
        path.write_text(relative, encoding="utf-8")
        files[relative] = stage2.sha256_file(path)
    stage2.verify_file_map(tmp_path, files)
    (tmp_path / stage2.PREREGISTERED_FILES[0]).write_text("mutated", encoding="utf-8")
    with pytest.raises(RuntimeError, match="mutation"):
        stage2.verify_file_map(tmp_path, files)


def test_independent_result_validator_exact_compare(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    metrics = {
        current: {
            "D_trial_normalized_waveform": 0.1,
            "R_mean_waveform_gain_residual": 0.01,
            "alpha_nonnegative_global_gain": 1.0,
            "awake_confirmation_trials": 20,
            "isoflurane_confirmation_trials": 20,
            "permutation_exceedances": 99,
            "permutation_p": 0.1,
            "permutations": 999,
        }
        for current in stage2.CURRENTS
    }
    result = {
        "confirmation_metrics": {str(current): metrics[current] for current in stage2.CURRENTS},
        "decision": "STAGE2_GLOBAL_GAIN_COMPATIBLE_AT_REGISTERED_RESOLUTION",
        "manifest_sha256": "m",
        "raw": {"sha256": "r"},
    }
    (tmp_path / stage2.RESULT).write_bytes(stage2.canonical_json_bytes(result))
    monkeypatch.setattr(stage2, "compute_result", lambda raw_path, pivot=None: result)
    receipt = stage2.verify_result_from_raw(tmp_path / "unused.nwb", pivot=tmp_path)
    assert receipt["status"] == "PASS"
    (tmp_path / stage2.VALIDATION_RECEIPT).unlink()
    changed = {**result, "manifest_sha256": "changed"}
    monkeypatch.setattr(stage2, "compute_result", lambda raw_path, pivot=None: changed)
    with pytest.raises(RuntimeError, match="recomputation mismatch"):
        stage2.verify_result_from_raw(tmp_path / "unused.nwb", pivot=tmp_path)
