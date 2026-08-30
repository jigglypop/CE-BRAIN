from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import numpy as np
import pytest


MODULE_PATH = Path(__file__).parents[1] / "examples" / "brain" / "ce_brain_phase2c_state_axis.py"
SPEC = importlib.util.spec_from_file_location("ce_brain_phase2c_state_axis", MODULE_PATH)
assert SPEC and SPEC.loader
phase2c = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = phase2c
SPEC.loader.exec_module(phase2c)


def _groups(effect: np.ndarray, seed: int, n: int = 24) -> dict[str, np.ndarray]:
    rng = np.random.default_rng(seed)
    awake = rng.normal(0, 0.01, size=(n, len(effect)))
    return {"awake": awake, "isoflurane": awake + effect}


def test_rank_one_axis_recovers_common_direction() -> None:
    direction = np.array([1.0, -2.0, 0.5])
    direction /= np.linalg.norm(direction)
    axis = phase2c.rank_one_axis(2 * direction, 5 * direction)
    assert np.allclose(axis, direction)


def test_axis_statistics_heldout_improvement() -> None:
    axis = np.array([1.0, 0.0, 0.0])
    stats = phase2c.axis_statistics(axis, np.array([0.8, 0.0, 0.0]), np.array([1.0, 0.0, 0.0]))
    assert stats["signed_cosine"] == pytest.approx(1.0)
    assert stats["improvement_over_zero"] == pytest.approx(0.96)


def test_bootstrap_is_deterministic_for_shared_axis_and_recovery() -> None:
    effect = np.array([0.5, -0.2, 0.1])
    source1 = _groups(effect, 1)
    source2 = _groups(1.2 * effect, 2)
    target_dev = _groups(0.9 * effect, 3)
    target_conf = _groups(effect, 4)
    recovery = target_conf["awake"] + 0.2 * effect
    first = phase2c.bootstrap(source1, source2, target_dev, target_conf, recovery,
                              repetitions=31, seed=77, batch_size=8)
    second = phase2c.bootstrap(source1, source2, target_dev, target_conf, recovery,
                               repetitions=31, seed=77, batch_size=8)
    for key in first:
        assert np.array_equal(first[key], second[key])
    assert np.quantile(first["improvement"], 0.025) > 0
    assert np.quantile(first["cosine"], 0.025) > 0


def _decision_inputs() -> tuple[dict, dict, dict, dict]:
    axis = {"improvement_over_zero": 0.4, "signed_cosine": 0.7}
    boot = {"improvement_lower_95": 0.1, "cosine_lower_95": 0.2}
    gain = {"R": 0.5}
    halves = {
        "early": {"improvement_over_zero": 0.2, "signed_cosine": 0.5},
        "late": {"improvement_over_zero": 0.2, "signed_cosine": 0.5},
    }
    return axis, boot, gain, halves


def test_decision_requires_recovery_for_stage3_authorization() -> None:
    axis, boot, gain, halves = _decision_inputs()
    assert phase2c.decide(axis, boot, 0.001, gain, 0.5, 0.8, halves) == (
        "STATE_AXIS_AND_RECOVERY_SUPPORTED"
    )
    assert phase2c.decide(axis, boot, 0.001, gain, 0.9, 1.1, halves) == (
        "STATE_AXIS_SUPPORTED_RECOVERY_NOT_ESTABLISHED"
    )
    assert phase2c.decide(axis, boot, 0.2, gain, 0.5, 0.8, halves) == (
        "STATE_AXIS_NOT_ESTABLISHED"
    )


def test_gain_residual_identifies_non_gain_shape() -> None:
    awake = np.tile(np.array([1.0, 0.0]), (20, 1))
    iso = np.tile(np.array([0.0, 1.0]), (20, 1))
    result = phase2c.gain_residual(awake, iso)
    assert result["alpha"] == 0
    assert result["R"] == pytest.approx(1.0)


def test_artifact_substitution() -> None:
    signal = np.arange(30.0)
    phase2c.replace_artifacts(signal, np.array([10]))
    assert np.array_equal(signal[10:15], np.arange(5.0, 10.0))


def test_contract_constants_cover_three_mouse_common_channels() -> None:
    assert phase2c.CHANNELS == (0, 1, 2, 3, 5, 20, 22, 23, 24, 25, 26, 27, 28, 29)
    assert phase2c.SPECS["521887"]["counts"]["awake/confirmation"] == 95
    assert phase2c.SPECS["521887"]["gaps"] == (97_470, 2_354_430)
    assert phase2c.BOOTSTRAPS == 1_999


def test_write_json_once_refuses_overwrite(tmp_path: Path) -> None:
    path = tmp_path / "receipt.json"
    phase2c.write_json_once(path, {"ok": True})
    with pytest.raises(RuntimeError, match="refusing to overwrite"):
        phase2c.write_json_once(path, {"ok": False})
