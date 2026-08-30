from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import numpy as np
import pytest


MODULE_PATH = Path(__file__).parents[1] / "examples" / "brain" / "ce_brain_phase2_state_input.py"
SPEC = importlib.util.spec_from_file_location("ce_brain_phase2_state_input", MODULE_PATH)
assert SPEC and SPEC.loader
phase2 = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = phase2
SPEC.loader.exec_module(phase2)


def _contrast_map(interactive: bool) -> tuple[dict[int, np.ndarray], dict[int, np.ndarray]]:
    source: dict[int, np.ndarray] = {}
    target: dict[int, np.ndarray] = {}
    for current in phase2.CURRENTS:
        if interactive:
            value = np.array([1.0, current / 100, 0.25])
        else:
            value = (0.5 + current / 200) * np.array([0.4, -0.2, 0.25])
        source[current] = value
        target[current] = value.copy() if interactive else value + np.array([0.01, 0.0, 0.0])
    return source, target


def _trial_groups(interactive: bool, seed: int = 7) -> tuple[dict, dict]:
    rng = np.random.default_rng(seed)
    source: dict[tuple[str, int], np.ndarray] = {}
    target: dict[tuple[str, int], np.ndarray] = {}
    for current in phase2.CURRENTS:
        awake_source = rng.normal(0, 0.01, size=(24, 3))
        awake_target = rng.normal(0, 0.01, size=(22, 3))
        effect = np.array([current / 100, 0.2, -0.1]) if interactive else np.array([0.5, 0.2, -0.1])
        source[("awake", current)] = awake_source
        source[("isoflurane", current)] = awake_source + effect
        target[("awake", current)] = awake_target
        target[("isoflurane", current)] = awake_target + effect
    return source, target


def test_interactive_model_wins_cross_animal_cross_current() -> None:
    source, target = _contrast_map(interactive=True)
    score = phase2.score_contrasts(source, target)
    assert score["mean_error_m2"] < 1e-24
    assert score["relative_m2_improvement"] > 0.99
    assert score["m2_better_currents"] == 3


def test_separable_model_is_retained_for_constant_contrast() -> None:
    source, target = _contrast_map(interactive=False)
    score = phase2.score_contrasts(source, target)
    assert score["mean_error_m1"] == pytest.approx(score["mean_error_m2"])
    assert score["m2_better_currents"] == 0


def test_rank_one_separable_prediction_allows_current_dependent_gain() -> None:
    direction = np.array([1.0, -2.0, 0.5])
    predicted = phase2.separable_prediction(2.0 * direction, 5.0 * direction, 0.5)
    assert np.allclose(predicted, 3.5 * direction)


def test_bootstrap_is_deterministic_and_detects_interaction() -> None:
    source, target = _trial_groups(interactive=True)
    first = phase2.bootstrap_improvements(source, target, repetitions=31, seed=123, batch_size=8)
    second = phase2.bootstrap_improvements(source, target, repetitions=31, seed=123, batch_size=8)
    assert np.array_equal(first, second)
    assert np.quantile(first, 0.025) > 0


@pytest.mark.parametrize(
    ("improvement", "lower", "upper", "better", "expected"),
    [
        (0.08, 0.01, 0.12, 2, "STATE_INPUT_INTERACTION_SUPPORTED"),
        (-0.08, -0.12, -0.01, 1, "STATE_INPUT_SEPARABLE_RETAINED"),
        (0.04, -0.01, 0.08, 2, "STATE_INPUT_NOT_ESTABLISHED"),
    ],
)
def test_decision_gate(improvement: float, lower: float, upper: float,
                       better: int, expected: str) -> None:
    score = {"relative_m2_improvement": improvement, "m2_better_currents": better}
    assert phase2.decide(score, lower, upper) == expected


def test_artifact_substitution_and_nearest_origin() -> None:
    signal = np.arange(30.0)
    phase2.replace_artifacts(signal, np.array([10]))
    assert np.array_equal(signal[10:15], np.arange(5.0, 10.0))
    timestamps = np.arange(20) / phase2.FS
    origins = phase2.nearest_origins(timestamps, timestamps[[3, 11]] + 0.1 / phase2.FS)
    assert np.array_equal(origins, np.array([3, 11]))


def test_manifest_constants_match_contract_scope() -> None:
    assert phase2.COMMON_CHANNELS == (0, 1, 2, 3, 4, 5, 9, 20, 22, 23, 24, 25, 26, 27, 28, 29)
    assert phase2.SPECS["521886"]["counts"]["recovery/20/confirmation"] == 45
    assert phase2.BOOTSTRAPS == 1_999


def test_time_half_groups_are_chronological_and_disjoint() -> None:
    rows = []
    ids = []
    states = []
    currents = []
    starts = []
    for state in phase2.STATES:
        for current in phase2.CURRENTS:
            for index in range(40):
                rows.append([float(index), float(current)])
                ids.append(2 * index + 1)
                states.append(state)
                currents.append(current)
                starts.append(float(100 - index))
    units = np.asarray(rows)
    eligible_rows = np.arange(len(units))
    schema = {
        "trial_ids": np.asarray(ids),
        "trial_states": np.asarray(states),
        "trial_currents": np.asarray(currents),
        "trial_starts": np.asarray(starts),
    }
    early, late = phase2.make_time_half_groups(units, eligible_rows, schema)
    assert len(early[("awake", 20)]) == len(late[("awake", 20)]) == 20
    assert early[("awake", 20)][:, 0].min() > late[("awake", 20)][:, 0].max()


def test_write_json_once_refuses_overwrite(tmp_path: Path) -> None:
    path = tmp_path / "receipt.json"
    phase2.write_json_once(path, {"ok": True})
    with pytest.raises(RuntimeError, match="refusing to overwrite"):
        phase2.write_json_once(path, {"ok": False})
