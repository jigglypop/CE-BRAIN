from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import numpy as np
import pytest


MODULE_PATH = Path(__file__).parents[1] / "examples" / "brain" / "ce_brain_phase2d_model_competition.py"
SPEC = importlib.util.spec_from_file_location("ce_brain_phase2d_model_competition", MODULE_PATH)
assert SPEC and SPEC.loader
phase2d = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = phase2d
SPEC.loader.exec_module(phase2d)


def _cell(effect: np.ndarray, seed: int, n: int = 24) -> dict[str, np.ndarray]:
    rng = np.random.default_rng(seed)
    awake = rng.normal(0, .01, size=(n, len(effect)))
    return {"awake/20": awake, "isoflurane/20": awake + effect}


def test_rank_one_axis_recovers_direction() -> None:
    direction = np.array([1., -2., .5])
    direction /= np.linalg.norm(direction)
    assert np.allclose(phase2d.rank_one_axis(np.stack((direction, 2 * direction))), direction)


def test_predictions_distinguish_individual_axis_and_kernel() -> None:
    source = np.array([[0., 1.], [0., 2.], [0., 3.]])
    development = np.array([[1., 0.], [2., 0.], [3., 0.]])
    predicted = phase2d.predictions(source, development)
    assert np.allclose(predicted["G"], 0)
    assert np.allclose(predicted["I"], development)
    assert np.allclose(predicted["K"], development)


def test_score_and_improvements() -> None:
    confirmation = np.array([[1., 0.], [2., 0.], [3., 0.]])
    predicted = {"Z": np.zeros_like(confirmation), "G": np.zeros_like(confirmation),
                 "I": .9 * confirmation, "K": .9 * confirmation}
    result = phase2d.improvements(phase2d.score(predicted, confirmation))
    assert result["I_vs_Z"] == pytest.approx(.99)
    assert result["K_vs_I"] == pytest.approx(0)


def test_decision_ladder() -> None:
    base = {"G_vs_Z": 0., "I_vs_Z": .4, "K_vs_Z": .5, "I_vs_G": .4, "K_vs_I": .2}
    lower = {name: .01 for name in base}
    assert phase2d.decide(base, lower, {"Z": 1., "G": 1., "I": .6, "K": .5}) == "CURRENT_SPECIFIC_OPERATOR_SUPPORTED"
    base["K_vs_I"] = .05
    assert phase2d.decide(base, lower, {"Z": 1., "G": 1., "I": .6, "K": .57}) == "INDIVIDUAL_AXIS_SUPPORTED"
    flat = {name: 0. for name in base}
    assert phase2d.decide(flat, flat, {"Z": 1., "G": 1.1, "I": 1.2, "K": 1.3}) == "NO_STABLE_STATE_MODEL"


def test_bootstrap_deterministic() -> None:
    effect = np.array([.3, -.2, .1])
    sources = [_cell(effect * scale, seed) for scale, seed in ((1., 1), (1.2, 2), (.8, 3))]
    dev, conf = {}, {}
    for current, scale in zip(phase2d.CURRENTS, (1., 2., 3.), strict=True):
        for target, seed in ((dev, current), (conf, current + 1)):
            group = _cell(effect * scale, seed)
            target[f"awake/{current}"] = group["awake/20"]
            target[f"isoflurane/{current}"] = group["isoflurane/20"]
    first = phase2d.bootstrap(sources, dev, conf, repetitions=17, seed=7, batch_size=5)
    second = phase2d.bootstrap(sources, dev, conf, repetitions=17, seed=7, batch_size=5)
    for name in first:
        assert np.array_equal(first[name], second[name])


def test_contract_constants() -> None:
    assert len(phase2d.CHANNELS) == 12
    assert phase2d.SPECS["569070"]["trial_count"] == 1_440
    assert phase2d.SPECS["569070"]["counts"]["isoflurane/60/confirmation"] == 53
    assert phase2d.BOOTSTRAPS == 1_999


def test_artifact_substitution_and_write_once(tmp_path: Path) -> None:
    signal = np.arange(30.)
    phase2d.replace_artifacts(signal, np.array([10]))
    assert np.array_equal(signal[10:15], np.arange(5., 10.))
    path = tmp_path / "receipt.json"
    phase2d.write_json_once(path, {"ok": True})
    with pytest.raises(RuntimeError, match="refusing to overwrite"):
        phase2d.write_json_once(path, {"ok": False})
