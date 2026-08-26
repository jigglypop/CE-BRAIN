from __future__ import annotations

import json

import numpy as np
import pytest

import stage2_recovery_successor as target


def test_nearest_origins_and_tie_rejection() -> None:
    timestamps = np.arange(20, dtype=np.float64) / target.FS
    starts = np.asarray([timestamps[4] + 0.1 / target.FS, timestamps[9] - 0.1 / target.FS])
    assert target.nearest_origins(timestamps, starts).tolist() == [4, 9]
    with pytest.raises(RuntimeError, match="non-unique"):
        target.nearest_origins(timestamps, np.asarray([(timestamps[4] + timestamps[5]) / 2]))


def test_split_counts() -> None:
    ids = np.arange(12)
    states = np.asarray(["awake"] * 4 + ["isoflurane"] * 4 + ["recovery"] * 4)
    counts = target.split_counts(ids, states, np.ones(12, dtype=bool))
    assert counts == {
        "awake/development": 2, "awake/confirmation": 2,
        "isoflurane/development": 2, "isoflurane/confirmation": 2,
        "recovery/development": 2, "recovery/confirmation": 2,
    }


def test_finish_waveforms_shape_and_car() -> None:
    rng = np.random.default_rng(4)
    response = rng.normal(size=(3, 249, len(target.COMMON_CHANNELS)))
    baseline = rng.normal(size=(3, len(target.COMMON_CHANNELS)))
    finished = target.finish_waveforms(response, baseline)
    restored = finished.reshape(3, 249, len(target.COMMON_CHANNELS))
    assert finished.shape == (3, 249 * len(target.COMMON_CHANNELS))
    np.testing.assert_allclose(restored.mean(axis=2), 0.0, atol=1e-12)


def test_gain_residual_exact_scaling() -> None:
    rng = np.random.default_rng(5)
    awake = rng.normal(size=(30, 20))
    isoflurane = awake * 2.5
    gain, residual = target.gain_residual(awake, isoflurane)
    assert gain == pytest.approx(2.5)
    assert residual == pytest.approx(0.0, abs=1e-14)


def test_permutation_and_bootstrap_are_deterministic() -> None:
    rng = np.random.default_rng(6)
    awake = rng.normal(size=(20, 12))
    isoflurane = awake + 0.8
    recovery = awake + 0.1
    unit = {
        key: values / np.linalg.norm(values, axis=1, keepdims=True)
        for key, values in {"a": awake, "i": isoflurane, "r": recovery}.items()
    }
    first_p = target.permutation_p(unit["a"], unit["i"], 17)
    second_p = target.permutation_p(unit["a"], unit["i"], 17)
    assert first_p == second_p
    first_q = target.bootstrap_q(unit["a"], unit["i"], unit["r"], 18)
    second_q = target.bootstrap_q(unit["a"], unit["i"], unit["r"], 18)
    assert first_q == second_q
    assert first_q[0] < 1.0


def metric(*, state: bool, recovery: bool, q: float) -> dict[str, object]:
    return {"state_pass": state, "recovery_pass": recovery, "Q": q}


def test_decision_branches() -> None:
    assert target.decide([metric(state=True, recovery=True, q=0.4)] * 2) == "STAGE2_RECOVERY_REPLICATION_SUPPORTED"
    assert target.decide([
        metric(state=True, recovery=True, q=0.4),
        metric(state=True, recovery=False, q=0.8),
    ]) == "STAGE2_RECOVERY_REPLICATION_TENSION"
    assert target.decide([
        metric(state=False, recovery=False, q=1.2),
        metric(state=True, recovery=False, q=1.1),
    ]) == "STAGE2_RECOVERY_NOT_ESTABLISHED"
    assert target.decide([
        metric(state=True, recovery=False, q=0.90),
        metric(state=True, recovery=False, q=0.90),
    ]) == "STAGE2_RECOVERY_REPLICATION_TENSION"


def test_registered_pass_boundaries_and_common_intersection() -> None:
    assert target.registered_pass_flags(0.01, 0.10, 0.75, 0.999) == (True, True)
    assert target.registered_pass_flags(0.011, 0.10, 0.75, 0.999) == (False, True)
    assert target.registered_pass_flags(0.01, 0.099, 0.75, 0.999) == (False, True)
    assert target.registered_pass_flags(0.01, 0.10, 0.751, 0.999) == (True, False)
    assert target.registered_pass_flags(0.01, 0.10, 0.75, 1.0) == (True, False)
    intersection = set(target.SPECS["543393"]["valid_rows"]) & set(target.SPECS["543394"]["valid_rows"])
    assert tuple(sorted(intersection)) == target.COMMON_CHANNELS


def test_write_json_once_refuses_overwrite(tmp_path) -> None:
    path = tmp_path / "receipt.json"
    target.write_json_once(path, {"ok": True})
    assert json.loads(path.read_text()) == {"ok": True}
    with pytest.raises(FileExistsError):
        target.write_json_once(path, {"ok": False})
