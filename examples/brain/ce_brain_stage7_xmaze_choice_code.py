"""Preregistered development test for an X-maze choice-related neural code."""
from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path

import h5py
import numpy as np
from scipy.optimize import minimize

try:
    from examples.brain import ce_brain_stage7_xmaze_apparatus as apparatus
except ModuleNotFoundError:  # Direct script execution from the repository root.
    import ce_brain_stage7_xmaze_apparatus as apparatus

WINDOW_START = -1.25
WINDOW_STOP = -0.25
BIN_SECONDS = 0.25
PCA_DIMS = (5, 10, 20)
PENALTIES = (0.01, 0.1, 1.0, 10.0, 100.0)
BOOTSTRAPS = 2000
PERMUTATIONS = 200
SEED = 731071
EXPECTED_EVENTS = {"BaggySweatpants": 102, "Franklin": 101}


@dataclass
class Prepared:
    behavior: np.ndarray
    static_neural: np.ndarray
    temporal_neural: np.ndarray
    labels: np.ndarray
    unit_ids: np.ndarray
    split: tuple[int, int]


def _decode(value: object) -> str:
    return value.decode() if isinstance(value, bytes) else str(value)


def _event_matrix(path: Path, expected_hash: str) -> Prepared:
    if apparatus.digest(path) != expected_hash:
        raise RuntimeError("STAGE7_XMAZE_CHOICE_STOP: SHA-256")
    with h5py.File(path, "r") as nwb:
        position_group = nwb["processing/behavior/Position/position"]
        position = np.asarray(position_group["data"])
        rate = float(position_group["starting_time"].attrs["rate"])
        head_direction = np.asarray(nwb["processing/behavior/CompassDirection/head direction/data"])
        if len(head_direction) != len(position):
            raise RuntimeError("STAGE7_XMAZE_CHOICE_STOP: behavior length")
        spike_times = np.asarray(nwb["units/spike_times"])
        spike_index = np.asarray(nwb["units/spike_times_index"], dtype=int)
        unit_ids = np.asarray(nwb["units/id"], dtype=int)
        unit_locations = []
        for reference in nwb["units/electrode_group"]:
            unit_locations.append(_decode(nwb[reference].attrs.get("location", "unknown")))

    normalized, _, _ = apparatus.normalize_position(position)
    visits = apparatus.endpoint_visits(position, rate)
    transitions = [
        transition for transition in apparatus.cross_maze_transitions(visits, rate)
        if transition["direction"] == "east_to_west"
    ]
    rows: list[list[float]] = []
    labels: list[int] = []
    centers: list[float] = []
    previous_choice = 0
    previous_known = 0
    for event_number, transition in enumerate(transitions):
        exit_index = int(round(float(transition["origin_exit_seconds"]) * rate))
        entry_index = int(round(float(transition["destination_entry_seconds"]) * rate))
        crossing_candidates = np.flatnonzero(normalized[exit_index:entry_index, 0] <= 0.5)
        if not len(crossing_candidates):
            continue
        center_index = exit_index + int(crossing_candidates[0])
        start = center_index + int(round(WINDOW_START * rate))
        stop = center_index + int(round(WINDOW_STOP * rate))
        if start < 0 or stop <= start:
            continue
        segment = normalized[start:stop]
        angles = np.deg2rad(head_direction[start:stop])
        finite = np.isfinite(segment).all(axis=1) & np.isfinite(angles)
        if finite.mean() < 0.90:
            continue
        segment = segment[finite]
        angles = angles[finite]
        origin_north = int(int(transition["origin_endpoint"]) % 2 == 1)
        choice_north = int(transition["destination_arm"] == "north")
        rows.append([
            float(origin_north),
            float(previous_choice),
            float(previous_known),
            float(segment[-1, 0]),
            float(segment[-1, 1]),
            float(np.sin(angles).mean()),
            float(np.cos(angles).mean()),
            float(segment[-1, 0] - segment[0, 0]),
            float(segment[-1, 1] - segment[0, 1]),
            float(event_number / max(1, len(transitions) - 1)),
        ])
        labels.append(choice_north)
        centers.append(center_index / rate)
        previous_choice = choice_north
        previous_known = 1

    behavior = np.asarray(rows, dtype=float)
    labels_array = np.asarray(labels, dtype=int)
    centers_array = np.asarray(centers, dtype=float)
    if len(labels_array) < 80:
        raise RuntimeError("STAGE7_XMAZE_CHOICE_STOP: eligible events")
    first = int(0.60 * len(labels_array))
    second = int(0.80 * len(labels_array))
    for subset in (labels_array[:first], labels_array[first:second], labels_array[second:]):
        if np.bincount(subset, minlength=2).min() < 5:
            raise RuntimeError("STAGE7_XMAZE_CHOICE_STOP: split balance")

    starts = np.r_[0, spike_index[:-1]]
    duration = len(position) / rate
    firing_rates = (spike_index - starts) / duration
    rate_eligible = firing_rates >= 0.05
    bins = int(round((WINDOW_STOP - WINDOW_START) / BIN_SECONDS))
    temporal = np.zeros((len(labels_array), len(unit_ids), bins), dtype=float)
    for unit, (left, right) in enumerate(zip(starts, spike_index)):
        if not rate_eligible[unit]:
            continue
        spikes = spike_times[left:right]
        for event, center in enumerate(centers_array):
            edges = center + np.linspace(WINDOW_START, WINDOW_STOP, bins + 1)
            temporal[event, unit] = np.diff(np.searchsorted(spikes, edges))
    train_nonzero = (temporal[:first].sum(axis=2) > 0).mean(axis=0) >= 0.05
    keep = rate_eligible & train_nonzero
    if keep.sum() < 10:
        raise RuntimeError("STAGE7_XMAZE_CHOICE_STOP: eligible units")
    temporal = temporal[:, keep]
    static = temporal.sum(axis=2)
    temporal_flat = temporal.transpose(0, 2, 1).reshape(len(labels_array), -1)
    # Retain IDs and locations in deterministic unit order; locations are reported later.
    kept_ids = unit_ids[keep]
    kept_locations = np.asarray(unit_locations, dtype=object)[keep]
    prepared = Prepared(behavior, static, temporal_flat, labels_array, kept_ids, (first, second))
    prepared.kept_locations = kept_locations  # type: ignore[attr-defined]
    return prepared


def _standardize(train: np.ndarray, other: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    mean = train.mean(axis=0)
    scale = train.std(axis=0)
    scale[scale < 1e-9] = 1.0
    return (train - mean) / scale, (other - mean) / scale


def _logistic_fit(x: np.ndarray, y: np.ndarray, penalty: float) -> np.ndarray:
    design = np.column_stack((np.ones(len(x)), x))

    def objective(weights: np.ndarray) -> tuple[float, np.ndarray]:
        score = np.clip(design @ weights, -35, 35)
        probability = 1.0 / (1.0 + np.exp(-score))
        loss = np.logaddexp(0.0, score).sum() - np.dot(y, score)
        loss += 0.5 * penalty * np.dot(weights[1:], weights[1:])
        gradient = design.T @ (probability - y)
        gradient[1:] += penalty * weights[1:]
        return float(loss), gradient

    result = minimize(
        objective,
        np.zeros(design.shape[1]),
        method="L-BFGS-B",
        jac=True,
        options={"maxiter": 500, "ftol": 1e-12},
    )
    if not result.success:
        raise RuntimeError(f"STAGE7_XMAZE_CHOICE_STOP: optimizer {result.message}")
    return np.asarray(result.x)


def _predict(x: np.ndarray, weights: np.ndarray) -> np.ndarray:
    score = np.clip(np.column_stack((np.ones(len(x)), x)) @ weights, -35, 35)
    return 1.0 / (1.0 + np.exp(-score))


def _loss_rows(y: np.ndarray, probability: np.ndarray) -> np.ndarray:
    probability = np.clip(probability, 1e-9, 1 - 1e-9)
    return -(y * np.log(probability) + (1 - y) * np.log(1 - probability))


def _balanced_accuracy(y: np.ndarray, probability: np.ndarray) -> float:
    prediction = probability >= 0.5
    return float(np.mean([prediction[y == label].mean() if label else (~prediction[y == label]).mean() for label in (0, 1)]))


def _pca_features(train: np.ndarray, validation: np.ndarray, test: np.ndarray, dimensions: int) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    train_z, validation_z = _standardize(train, validation)
    _, test_z = _standardize(train, test)
    _, _, right = np.linalg.svd(train_z, full_matrices=False)
    dimensions = min(dimensions, len(right), len(train) - 1)
    basis = right[:dimensions].T
    train_pca = train_z @ basis
    validation_pca = validation_z @ basis
    test_pca = test_z @ basis
    mean = train_pca.mean(axis=0)
    scale = train_pca.std(axis=0)
    scale[scale < 1e-9] = 1.0
    return (
        (train_pca - mean) / scale,
        (validation_pca - mean) / scale,
        (test_pca - mean) / scale,
    )


def _fixed_model(prepared: Prepared, neural: np.ndarray, dimensions: int, penalty: float) -> dict[str, object]:
    first, second = prepared.split
    behavior_train, _ = _standardize(prepared.behavior[:first], prepared.behavior[first:second])
    _, behavior_test = _standardize(prepared.behavior[:first], prepared.behavior[second:])
    p_train, _, p_test = _pca_features(neural[:first], neural[first:second], neural[second:], dimensions)
    train = np.column_stack((behavior_train, p_train))
    test = np.column_stack((behavior_test, p_test))
    weights = _logistic_fit(train, prepared.labels[:first], penalty)
    probability = _predict(test, weights)
    y_test = prepared.labels[second:]
    return {
        "test_probability": probability,
        "test_loss_rows": _loss_rows(y_test, probability),
        "test_log_loss": float(_loss_rows(y_test, probability).mean()),
        "test_balanced_accuracy": _balanced_accuracy(y_test, probability),
    }


def _select_model(prepared: Prepared, neural: np.ndarray | None) -> dict[str, object]:
    first, second = prepared.split
    y_train, y_validation, y_test = prepared.labels[:first], prepared.labels[first:second], prepared.labels[second:]
    behavior_train, behavior_validation = _standardize(prepared.behavior[:first], prepared.behavior[first:second])
    _, behavior_test = _standardize(prepared.behavior[:first], prepared.behavior[second:])
    candidates: list[tuple[float, int, float, np.ndarray, np.ndarray]] = []
    dimensions_grid = (0,) if neural is None else PCA_DIMS
    for dimensions in dimensions_grid:
        if neural is None:
            train, validation, test = behavior_train, behavior_validation, behavior_test
        else:
            p_train, p_validation, p_test = _pca_features(
                neural[:first], neural[first:second], neural[second:], dimensions
            )
            train = np.column_stack((behavior_train, p_train))
            validation = np.column_stack((behavior_validation, p_validation))
            test = np.column_stack((behavior_test, p_test))
        for penalty in PENALTIES:
            weights = _logistic_fit(train, y_train, penalty)
            validation_probability = _predict(validation, weights)
            validation_loss = float(_loss_rows(y_validation, validation_probability).mean())
            candidates.append((validation_loss, dimensions, penalty, weights, test))
    validation_loss, dimensions, penalty, weights, test = min(candidates, key=lambda item: (item[0], item[1], item[2]))
    probability = _predict(test, weights)
    return {
        "validation_log_loss": validation_loss,
        "pca_dimensions": dimensions,
        "penalty": penalty,
        "test_probability": probability,
        "test_loss_rows": _loss_rows(y_test, probability),
        "test_log_loss": float(_loss_rows(y_test, probability).mean()),
        "test_balanced_accuracy": _balanced_accuracy(y_test, probability),
    }


def _improvement_interval(reference: np.ndarray, candidate: np.ndarray, rng: np.random.Generator) -> tuple[float, float, float]:
    observed = float((reference.mean() - candidate.mean()) / reference.mean())
    samples = np.empty(BOOTSTRAPS)
    for index in range(BOOTSTRAPS):
        selection = rng.integers(0, len(reference), len(reference))
        ref = reference[selection].mean()
        samples[index] = (ref - candidate[selection].mean()) / ref
    low, high = np.quantile(samples, (0.025, 0.975))
    return observed, float(low), float(high)


def analyze(path: Path, expected_hash: str) -> dict[str, object]:
    prepared = _event_matrix(path, expected_hash)
    first, second = prepared.split
    behavior = _select_model(prepared, None)
    static = _select_model(prepared, prepared.static_neural)
    temporal = _select_model(prepared, prepared.temporal_neural)
    rng = np.random.default_rng(SEED)
    t_vs_b = _improvement_interval(behavior["test_loss_rows"], temporal["test_loss_rows"], rng)  # type: ignore[arg-type]
    t_vs_s = _improvement_interval(static["test_loss_rows"], temporal["test_loss_rows"], rng)  # type: ignore[arg-type]

    # Fixed-hyperparameter permutation control. PCA is unsupervised and remains fixed by the same data rows.
    permutation_scores = []
    for _ in range(PERMUTATIONS):
        permuted = Prepared(
            prepared.behavior,
            prepared.static_neural,
            prepared.temporal_neural,
            rng.permutation(prepared.labels),
            prepared.unit_ids,
            prepared.split,
        )
        permutation_scores.append(float(_fixed_model(
            permuted,
            prepared.temporal_neural,
            int(temporal["pca_dimensions"]),
            float(temporal["penalty"]),
        )["test_balanced_accuracy"]))
    permutation_threshold = float(np.quantile(permutation_scores, 0.95))

    shifted = Prepared(
        prepared.behavior,
        prepared.static_neural,
        np.roll(prepared.temporal_neural, 1, axis=0),
        prepared.labels,
        prepared.unit_ids,
        prepared.split,
    )
    shifted_temporal = _fixed_model(
        shifted,
        shifted.temporal_neural,
        int(temporal["pca_dimensions"]),
        float(temporal["penalty"]),
    )
    behavior_overfit_stop = float(behavior["test_balanced_accuracy"]) >= 0.90
    passed = bool(
        t_vs_b[0] >= 0.05 and t_vs_b[1] > 0
        and t_vs_s[0] >= 0.03 and t_vs_s[1] > 0
        and float(temporal["test_balanced_accuracy"]) >= 0.60
        and float(temporal["test_balanced_accuracy"]) > permutation_threshold
        and float(temporal["test_log_loss"]) < float(shifted_temporal["test_log_loss"])
        and not behavior_overfit_stop
    )
    static_candidate = bool(
        float(static["test_log_loss"]) <= 0.95 * float(behavior["test_log_loss"])
        and float(static["test_balanced_accuracy"]) >= 0.60
    )
    locations, counts = np.unique(getattr(prepared, "kept_locations"), return_counts=True)
    def summary(model: dict[str, object]) -> dict[str, object]:
        return {key: value for key, value in model.items() if key not in {"test_probability", "test_loss_rows"}}
    subject = next((name for name in EXPECTED_EVENTS if name in path.name), "")
    contract_match = len(prepared.labels) == EXPECTED_EVENTS.get(subject, -1)
    return {
        "decision": (
            "APPARATUS_CONTRACT_MISMATCH_EXPLORATORY" if not contract_match
            else "CHOICE_RELATED_TEMPORAL_CODE_CANDIDATE" if passed
            else "STATIC_CHOICE_CODE_CANDIDATE" if static_candidate
            else "ALTERNATIVE_MEMORY_CODE_NOT_ESTABLISHED"
        ),
        "file": path.name,
        "events": len(prepared.labels),
        "contract_expected_events": EXPECTED_EVENTS.get(subject),
        "contract_event_count_match": contract_match,
        "split_train_validation_test": [first, second - first, len(prepared.labels) - second],
        "label_counts_total": np.bincount(prepared.labels, minlength=2).tolist(),
        "eligible_units": len(prepared.unit_ids),
        "eligible_unit_locations": {str(location): int(count) for location, count in zip(locations, counts)},
        "behavior_model": summary(behavior),
        "static_model": summary(static),
        "temporal_model": summary(temporal),
        "temporal_vs_behavior_improvement_and_95ci": list(t_vs_b),
        "temporal_vs_static_improvement_and_95ci": list(t_vs_s),
        "permutation_balanced_accuracy_95pct": permutation_threshold,
        "shifted_temporal_test_log_loss": float(shifted_temporal["test_log_loss"]),
        "behavior_overfit_stop": behavior_overfit_stop,
        "claim_ceiling": "choice-related code candidate only; trial semantics absent",
    }


def run() -> dict[str, object]:
    results = {name: analyze(path, expected_hash) for name, (path, expected_hash) in apparatus.FILES.items()}
    mismatch = any(not result["contract_event_count_match"] for result in results.values())
    replicated = all(result["decision"] == "CHOICE_RELATED_TEMPORAL_CODE_CANDIDATE" for result in results.values())
    return {
        "decision": (
            "APPARATUS_CONTRACT_MISMATCH_EXPLORATORY" if mismatch
            else "CHOICE_RELATED_TEMPORAL_CODE_REPLICATED_DEVELOPMENT" if replicated
            else "ALTERNATIVE_MEMORY_CODE_NOT_ESTABLISHED_REPLICATED"
        ),
        "sessions": results,
        "claim_ceiling": "development only; no correct/reward/retrieval/correction claim",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = run()
    payload = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        if args.output.exists():
            raise RuntimeError(f"refusing overwrite: {args.output}")
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload, encoding="utf-8")
    print(payload, end="")


if __name__ == "__main__":
    main()
