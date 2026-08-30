from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import h5py
import numpy as np


MODULE_PATH = Path(__file__).parents[1] / "examples" / "brain" / "ce_brain_stage3a_worm_metric.py"
SPEC = importlib.util.spec_from_file_location("ce_brain_stage3a_worm_metric", MODULE_PATH)
assert SPEC and SPEC.loader
stage3a = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = stage3a
SPEC.loader.exec_module(stage3a)


def test_preregistered_subject_split_is_stable() -> None:
    subjects = list(range(113))
    assert sum(stage3a.subject_development(subject) for subject in subjects if subject not in (20, 23, 33)) == 77
    assert stage3a.subject_development(0)
    assert not stage3a.subject_development(2)


def test_similarity_alignment_recovers_transform() -> None:
    rng = np.random.default_rng(1)
    source = rng.normal(size=(20, 3))
    rotation, _ = np.linalg.qr(rng.normal(size=(3, 3)))
    target = (source - np.array([1., 2., 3.])) @ rotation * 2 + np.array([4., 5., 6.])
    fitted_r, fitted_s, source_mean, target_mean = stage3a.similarity_align(source, target)
    reconstructed = (source - source_mean) @ fitted_r * fitted_s + target_mean
    assert np.allclose(reconstructed, target)


def test_metric_fit_prefers_near_pairs() -> None:
    rng = np.random.default_rng(2)
    delta = rng.normal(size=(2_000, 3))
    probability = stage3a.expit(1.5 - np.sum(delta * delta, axis=1))
    y = rng.binomial(1, probability).astype(float)
    model = stage3a.fit_metric(delta, y, 1e-3, directional=False)
    predicted = stage3a.predict_metric(model, np.array([[0., 0., 0.], [3., 0., 0.]]))
    assert predicted[0] > predicted[1]


def test_directional_model_learns_signed_displacement() -> None:
    rng = np.random.default_rng(3)
    delta = rng.normal(size=(3_000, 3))
    probability = stage3a.expit(-.5 - .2*np.sum(delta*delta, axis=1) + 1.5*delta[:, 0])
    y = rng.binomial(1, probability).astype(float)
    symmetric = stage3a.fit_metric(delta, y, 1e-3, directional=False)
    directional = stage3a.fit_metric(delta, y, 1e-3, directional=True)
    assert stage3a.log_loss(y, stage3a.predict_metric(directional, delta)) < stage3a.log_loss(
        y, stage3a.predict_metric(symmetric, delta))


def test_graph_uses_ordered_pairs() -> None:
    pairs = np.asarray([("A", "B"), ("A", "B"), ("B", "A"), ("B", "A")], dtype=object)
    model = stage3a.graph_fit(pairs, np.array([1., 1., 0., 0.]))
    prediction = stage3a.graph_predict(model, np.asarray([("A", "B"), ("B", "A")], dtype=object))
    assert prediction[0] > prediction[1]


def test_consecutive_quality_gate() -> None:
    values = np.array([[0., 0.], [4.1, 3.1], [4.2, 0.], [0., -3.2], [0., -3.3]])
    assert np.array_equal(stage3a.consecutive(values, 4, positive=True), [True, False])
    assert np.array_equal(stage3a.consecutive(values, 3, positive=False), [True, True])


def _score(winner: str) -> dict:
    names = ("N", "R", "F", "S", "O")
    losses = {name: 1.0 for name in names}
    losses[winner] = .7
    comparisons = {f"{name}_vs_N": {"improvement": .3 if name == winner else 0.,
                                      "lower_95": .1 if name == winner else -.1}
                   for name in names if name != "N"}
    comparisons["winner_vs_runner"] = {"better": winner, "improvement": .3, "lower_95": .1}
    return {"losses": losses, "comparisons": comparisons, "ranking": [winner, "N"]}


def test_decision_ladder_operator_and_tension() -> None:
    symmetry = {"median_abs_difference": .2}
    triangle = {"violation_upper_95": .2}
    directional = {"improvement": 0., "lower_95": -.1}
    assert stage3a.decide(_score("O"), _score("O"), symmetry, triangle, directional) == (
        "GENERAL_TRANSITION_OPERATOR_RETAINED")
    assert stage3a.decide(_score("R"), _score("O"), symmetry, triangle, directional) == (
        "REPRESENTATION_TENSION")


def test_canonical_map_resolves_single_integer_reference(tmp_path: Path) -> None:
    path = tmp_path / "minimal.h5"
    with h5py.File(path, "w") as nwb:
        pump = nwb.create_group("processing/ophys/PumpProbeGreenSegmentations/PumpProbeGreenPlaneSegmentation")
        pump.create_dataset("id", data=np.array([4, 5]))
        pump.create_dataset("neuropal_ids", data=np.array([b"0", b""]))
        pump.create_dataset("centroids", data=np.array([[1., 2., 3.], [4., 5., 6.]]))
        neuropal = nwb.create_group("processing/ophys/NeuroPALSegmentations/NeuroPALPlaneSegmentation")
        neuropal.create_dataset("labels", data=np.array([b"AVAL"]))
    with h5py.File(path, "r") as nwb:
        names, coords = stage3a.canonical_map(nwb)
    assert names == {4: "AVAL"}
    assert np.array_equal(coords[4], [1., 2., 3.])


def test_canonical_map_excludes_out_of_range_legacy_reference(tmp_path: Path) -> None:
    path = tmp_path / "legacy.h5"
    with h5py.File(path, "w") as nwb:
        pump = nwb.create_group("processing/ophys/PumpProbeGreenSegmentations/PumpProbeGreenPlaneSegmentation")
        pump.create_dataset("id", data=np.array([4]))
        pump.create_dataset("neuropal_ids", data=np.array([b"1124"]))
        pump.create_dataset("centroids", data=np.array([[1., 2., 3.]]))
        neuropal = nwb.create_group("processing/ophys/NeuroPALSegmentations/NeuroPALPlaneSegmentation")
        neuropal.create_dataset("labels", data=np.array([b"AVAL"]))
    with h5py.File(path, "r") as nwb:
        names, coords = stage3a.canonical_map(nwb)
    assert names == {}
    assert coords == {}


def test_runtime_is_frozen() -> None:
    identity = stage3a.verify_runtime()
    assert all(identity[key] == value for key, value in stage3a.EXPECTED_RUNTIME.items())
    assert Path(identity["executable"]).is_file()
