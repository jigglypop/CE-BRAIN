import numpy as np

from examples.brain.ce_brain_stage3e_vsd_source_generalization import (
    DEVELOPMENT_LABELS,
    STIM_LABELS,
    analyze_matrices,
    exact_signflip_p,
    locked_split,
    source_improvements,
)


def _positions() -> np.ndarray:
    return np.asarray([(i % 5, i // 5) for i in range(20)], dtype=float)


def _smooth_response() -> np.ndarray:
    positions = _positions()
    rows = []
    for label in DEVELOPMENT_LABELS:
        source = STIM_LABELS.index(label)
        distance = np.sqrt(np.square(positions - positions[source]).sum(axis=1))
        response = np.exp(-distance / 2.0)
        response[source] = 0.0
        rows.append(response)
    return np.asarray(rows)


def test_locked_source_split_is_stable() -> None:
    development, calibration, confirmation = locked_split()
    assert tuple(development) == DEVELOPMENT_LABELS
    assert len(calibration) == len(confirmation) == 4


def test_exact_signflip_detects_uniform_positive_values() -> None:
    assert exact_signflip_p(np.ones(12)) == 1 / 4096


def test_spatial_signal_beats_receiver_mean() -> None:
    response = _smooth_response()
    improvements = source_improvements(response, response, _positions())
    assert improvements["euclidean"].mean() > 0
    result = analyze_matrices(response, response, _positions())
    assert result["status"] in {
        "SPATIAL_GEOMETRY_SURVIVES_DEVELOPMENT",
        "GENERAL_KERNEL_PREFERRED_DEVELOPMENT",
        "GENERAL_KERNEL_SURVIVES_DEVELOPMENT",
    }
