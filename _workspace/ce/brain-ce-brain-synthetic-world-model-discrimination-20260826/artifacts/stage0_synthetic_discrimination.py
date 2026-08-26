"""CE-BRAIN Stage 0: preregistered synthetic structural discrimination."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from typing import Any, Iterable

import numpy as np


ROOT_SEED = 26082600
WORLDS = tuple("ABCDEFG")
EXPECTED = {"A": "R", "B": "G", "C": "F", "D": "S", "E": "O", "F": "O", "G": "O"}
CANDIDATES = ("F", "G", "O", "R", "S")
RIDGES = (1e-8, 1e-6, 1e-4, 1e-2)
THRESHOLD_QUANTILES = (0.25, 0.35, 0.50, 0.65, 0.75)
MIN_VALIDATION_MARGIN = 0.001
NODES = 8
HIDDEN_NODES = 24
TIMES = 64
DT = 0.05
NOISE_SD = 0.02
TRAJECTORIES = {"train": 96, "validation": 48, "unseen": 48}
MAX_ABS_STATE = 1e6
STOP = "STAGE0_SYNTHETIC_DISCRIMINATION_STOP"
MANIFEST_NAME = "stage0-preregistration-manifest.json"
RESULT_NAME = "stage0-result.json"
PREREG_FILES = (
    "00-contract.md", "10-data-lock.md", "20-hypotheses.md", "30-models.md",
    "40-metrics.md", "50-gates.md", "60-negative-controls.md", "10-sources.md",
    "11-math.md", "12-routes.md", "artifacts/stage0_synthetic_discrimination.py",
    "artifacts/test_stage0_synthetic_discrimination.py", "20-audit.md",
    "21-preexecution-validation.md",
)


def _sha(body: bytes) -> str:
    return hashlib.sha256(body).hexdigest()


def _seed(world: str, replicate: int) -> int:
    if world not in WORLDS or type(replicate) is not int or not 0 <= replicate < 12:
        raise ValueError(f"{STOP}:seed identity")
    body = f"CE-BRAIN-STAGE0|v1|{world}|{replicate}|{ROOT_SEED}".encode()
    return int.from_bytes(hashlib.sha256(body).digest()[:16], "little")


def _stable_radius(matrix: np.ndarray) -> float:
    return float(np.max(np.abs(np.linalg.eigvals(matrix))))


def _ring(forward: float, reverse: float = 0.0, *, n: int = NODES) -> np.ndarray:
    matrix = np.zeros((n, n), dtype=np.float64)
    for index in range(n):
        matrix[(index + 1) % n, index] = forward
        matrix[index, (index + 1) % n] = reverse
    return matrix


def _coefficients(world: str, rng: np.random.Generator) -> dict[str, Any]:
    identity = np.eye(NODES, dtype=np.float64)
    if world == "A":
        raw = rng.normal(size=(NODES, NODES))
        mobility = raw @ raw.T
        mobility /= np.linalg.norm(mobility, ord=2)
        a = 0.90 * identity - 0.18 * mobility
        out = {"A": a, "B": 0.30 * identity}
        if not np.allclose(a, a.T, atol=1e-12) or np.min(np.linalg.eigvalsh(identity - a)) <= 0:
            raise RuntimeError(f"{STOP}:A identity")
    elif world == "B":
        a = 0.62 * identity + _ring(0.24, 0.01)
        out = {"A": a, "B": 0.30 * identity}
        if np.max(np.abs(a - a.T)) < 0.20:
            raise RuntimeError(f"{STOP}:B identity")
    elif world == "C":
        a = 0.68 * identity + _ring(0.05, 0.05)
        out = {"A": a, "B_pos": 0.30 * identity, "B_neg": 0.68 * identity}
        if np.linalg.norm(out["B_pos"] - out["B_neg"], ord=2) < 0.30:
            raise RuntimeError(f"{STOP}:C identity")
    elif world == "D":
        a0 = 0.32 * identity + _ring(0.52, 0.01)
        a1 = 0.32 * identity + _ring(0.01, 0.52)
        out = {"A0": a0, "A1": a1, "B": 0.34 * identity, "threshold": 0.0}
        if np.linalg.norm(a0 - a1, ord=2) < 0.20:
            raise RuntimeError(f"{STOP}:D identity")
    elif world == "E":
        a = 0.20 * identity + _ring(0.04, 0.01)
        out = {"A": a, "B": 0.18 * identity,
               "quadratic": np.linspace(0.05, 0.08, NODES),
               "state_input": np.linspace(0.35, 0.50, NODES)}
        if (np.linalg.norm(out["quadratic"]) < 0.15
                or np.linalg.norm(out["state_input"]) < 1.0):
            raise RuntimeError(f"{STOP}:E identity")
    elif world == "F":
        ahh = 0.10 * np.eye(HIDDEN_NODES) + _ring(0.02, n=HIDDEN_NODES)
        axh = np.zeros((NODES, HIDDEN_NODES), dtype=np.float64)
        ahx = np.zeros((HIDDEN_NODES, NODES), dtype=np.float64)
        axh[:, :NODES] = 0.70 * identity
        ahx[:NODES, :] = 0.75 * identity
        axx = 0.10 * identity + _ring(0.02, 0.00)
        coupled = np.block([[axx, axh], [ahx, ahh]])
        coupled_radius = _stable_radius(coupled)
        if coupled_radius >= 0.95:
            scale = 0.94 / coupled_radius
            axx, axh, ahx, ahh = axx * scale, axh * scale, ahx * scale, ahh * scale
            coupled = np.block([[axx, axh], [ahx, ahh]])
        out = {"Axx": axx, "Axh": axh, "Ahx": ahx,
               "Ahh": ahh, "Bx": 0.28 * identity,
               "Bh": rng.normal(scale=0.010, size=(HIDDEN_NODES, NODES)),
               "coupled_radius": _stable_radius(coupled)}
        if (axh.shape[1] != HIDDEN_NODES or np.linalg.norm(axh @ ahx, ord=2) < 0.05
                or out["coupled_radius"] >= 0.95):
            raise RuntimeError(f"{STOP}:F identity")
    elif world == "G":
        a1 = 0.12 * identity + _ring(0.03, 0.00)
        a2 = 0.72 * identity
        out = {"A1": a1, "A2": a2, "B": 0.28 * identity}
        companion = np.block([[a1, a2], [identity, np.zeros_like(identity)]])
        if np.linalg.norm(a2, ord=2) < 0.25 or _stable_radius(companion) >= 0.99:
            raise RuntimeError(f"{STOP}:G identity")
    else:
        raise ValueError(f"{STOP}:world")
    for key, value in out.items():
        if isinstance(value, np.ndarray) and not np.all(np.isfinite(value)):
            raise RuntimeError(f"{STOP}:coefficient finite")
    for key in ("A", "A0", "A1", "Axx", "Ahh"):
        if key in out and _stable_radius(out[key]) >= 0.99:
            raise RuntimeError(f"{STOP}:generator stability:{key}")
    return out


def _inputs(rng: np.random.Generator, split: str) -> np.ndarray:
    count = TRAJECTORIES[split]
    values = np.zeros((count, TIMES, NODES), dtype=np.float64)
    if split == "train":
        amplitudes = (-0.8, -0.4, 0.4, 0.8)
    elif split == "validation":
        amplitudes = (-0.6, 0.6)
    elif split == "unseen":
        amplitudes = (-1.0, -0.3, 0.3, 1.0)
    else:
        raise ValueError(f"{STOP}:split")
    for row in range(count):
        node = row % NODES
        amplitude = amplitudes[(row // NODES) % len(amplitudes)]
        if split == "train":
            if row % 2 == 0:
                values[row, 10:, node] = amplitude
            else:
                start = 8 + (row % 9)
                values[row, start:start + 8, node] = amplitude
        elif split == "validation":
            if row % 2 == 0:
                values[row, 8:40, node] = np.linspace(0.0, amplitude, 32)
                values[row, 40:, node] = amplitude
            else:
                start = 19 + (row % 7)
                values[row, start:start + 6, node] = amplitude
        else:
            if row % 2 == 0:
                time = np.arange(TIMES - 8, dtype=np.float64)
                values[row, 8:, node] = amplitude * np.sin(0.015 * time ** 1.55)
            else:
                gap = (5, 11, 17)[row % 3]
                start = 9
                values[row, start:start + 4, node] = amplitude
                values[row, start + gap:start + gap + 4, node] = -0.7 * amplitude
    values += rng.normal(scale=1e-6, size=values.shape)
    return values


def _simulate(world: str, coefficients: dict[str, Any], inputs: np.ndarray,
              rng: np.random.Generator) -> np.ndarray:
    count = inputs.shape[0]
    states = np.zeros((count, TIMES, NODES), dtype=np.float64)
    states[:, 0] = rng.uniform(-0.45, 0.45, size=(count, NODES))
    states[:, 1] = states[:, 0] + rng.normal(scale=0.03, size=(count, NODES))
    hidden = None
    if world == "F":
        hidden = rng.normal(scale=0.18, size=(count, HIDDEN_NODES))
    for time in range(1, TIMES - 1):
        x = states[:, time]
        previous = states[:, time - 1]
        u = inputs[:, time]
        if world in {"A", "B"}:
            next_state = x @ coefficients["A"].T + u @ coefficients["B"].T
        elif world == "C":
            next_state = (x @ coefficients["A"].T + np.maximum(u, 0) @ coefficients["B_pos"].T
                          + np.minimum(u, 0) @ coefficients["B_neg"].T)
        elif world == "D":
            low = x @ coefficients["A0"].T
            high = x @ coefficients["A1"].T
            next_state = np.where((x[:, :1] >= coefficients["threshold"]), high, low)
            next_state += u @ coefficients["B"].T
        elif world == "E":
            next_state = (x @ coefficients["A"].T + u @ coefficients["B"].T
                          + coefficients["quadratic"] * x ** 2
                          + coefficients["state_input"] * x * u)
        elif world == "F":
            assert hidden is not None
            next_state = x @ coefficients["Axx"].T + hidden @ coefficients["Axh"].T + u @ coefficients["Bx"].T
            hidden = (hidden @ coefficients["Ahh"].T + x @ coefficients["Ahx"].T
                      + u @ coefficients["Bh"].T)
        elif world == "G":
            next_state = (x @ coefficients["A1"].T + previous @ coefficients["A2"].T
                          + u @ coefficients["B"].T)
        else:
            raise AssertionError("unreachable")
        states[:, time + 1] = next_state + rng.normal(scale=NOISE_SD, size=next_state.shape)
    if not np.all(np.isfinite(states)) or np.max(np.abs(states)) >= MAX_ABS_STATE:
        raise RuntimeError(f"{STOP}:generated state")
    return states


def generate(world: str, replicate: int) -> tuple[dict[str, tuple[np.ndarray, np.ndarray]], dict[str, Any]]:
    rng = np.random.default_rng(_seed(world, replicate))
    coefficients = _coefficients(world, rng)
    splits: dict[str, tuple[np.ndarray, np.ndarray]] = {}
    hashes: dict[str, str] = {}
    row_hashes: dict[str, list[str]] = {}
    for split in ("train", "validation", "unseen"):
        inputs = _inputs(rng, split)
        states = _simulate(world, coefficients, inputs, rng)
        body = (np.ascontiguousarray(states).tobytes() + np.ascontiguousarray(inputs).tobytes()
                + repr((states.shape, inputs.shape, "float64")).encode())
        hashes[split] = _sha(body)
        row_hashes[split] = [
            _sha(np.ascontiguousarray(states[row]).tobytes()
                 + np.ascontiguousarray(inputs[row]).tobytes())
            for row in range(len(states))
        ]
        splits[split] = (states, inputs)
    identity = {"world": world, "replicate": replicate, "seed": _seed(world, replicate),
                "split_sha256": hashes, "trajectory_sha256": row_hashes,
                "coefficient_sha256": _coefficient_hash(coefficients)}
    _verify_split_identity(identity)
    return splits, identity


def _verify_split_identity(identity: dict[str, Any]) -> None:
    split_hashes = identity.get("split_sha256", {})
    row_hashes = identity.get("trajectory_sha256", {})
    if set(split_hashes) != set(TRAJECTORIES) or set(row_hashes) != set(TRAJECTORIES):
        raise RuntimeError(f"{STOP}:split population")
    if any(len(row_hashes[split]) != TRAJECTORIES[split] for split in TRAJECTORIES):
        raise RuntimeError(f"{STOP}:trajectory population")
    flat = [digest for split in TRAJECTORIES for digest in row_hashes[split]]
    if len(set(split_hashes.values())) != len(split_hashes) or len(set(flat)) != len(flat):
        raise RuntimeError(f"{STOP}:split overlap")


def _coefficient_hash(coefficients: dict[str, Any]) -> str:
    parts: list[bytes] = []
    for key in sorted(coefficients):
        value = coefficients[key]
        parts.append(key.encode())
        parts.append(np.asarray(value, dtype=np.float64).tobytes())
    return _sha(b"".join(parts))


def _rows(states: np.ndarray, inputs: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    return (states[:, 1:-1].reshape(-1, NODES), states[:, :-2].reshape(-1, NODES),
            inputs[:, 1:-1].reshape(-1, NODES), states[:, 2:].reshape(-1, NODES))


def _features(kind: str, current: np.ndarray, previous: np.ndarray, inputs: np.ndarray) -> np.ndarray:
    ones = np.ones((len(current), 1), dtype=np.float64)
    if kind in {"R", "G", "S"}:
        return np.concatenate((ones, current, inputs), axis=1)
    if kind == "F":
        return np.concatenate((ones, current, np.maximum(inputs, 0), np.minimum(inputs, 0)), axis=1)
    if kind == "O":
        return np.concatenate((ones, current, previous, inputs, current ** 2, current * inputs), axis=1)
    raise ValueError(f"{STOP}:candidate")


def _ridge(features: np.ndarray, targets: np.ndarray, ridge: float) -> np.ndarray:
    means = np.zeros(features.shape[1], dtype=np.float64)
    scales = np.ones(features.shape[1], dtype=np.float64)
    means[1:] = features[:, 1:].mean(axis=0)
    scales[1:] = features[:, 1:].std(axis=0)
    scales[scales < 1e-12] = 1.0
    standardized = (features - means) / scales
    standardized[:, 0] = 1.0
    penalty = np.eye(features.shape[1], dtype=np.float64) * ridge
    penalty[0, 0] = 0.0
    gram = standardized.T @ standardized + penalty
    rhs = standardized.T @ targets
    try:
        weights_z = np.linalg.solve(gram, rhs)
    except np.linalg.LinAlgError:
        weights_z = np.linalg.lstsq(gram, rhs, rcond=None)[0]
    weights = weights_z / scales[:, None]
    weights[0] = weights_z[0] - (means[1:] / scales[1:]) @ weights_z[1:]
    return weights


def _fit_linear(kind: str, states: np.ndarray, inputs: np.ndarray, ridge: float,
                *, threshold: float | None = None) -> dict[str, Any]:
    current, previous, forcing, targets = _rows(states, inputs)
    features = _features(kind, current, previous, forcing)
    if kind == "S":
        if threshold is None:
            raise ValueError(f"{STOP}:switch threshold")
        mask = current[:, 0] >= threshold
        if min(int(mask.sum()), int((~mask).sum())) < 5 * features.shape[1]:
            raise RuntimeError(f"{STOP}:switch population")
        weights = (_ridge(features[~mask], targets[~mask], ridge),
                   _ridge(features[mask], targets[mask], ridge))
        parameters = int(sum(item.size for item in weights) + 1)
        return {"kind": kind, "weights": weights, "threshold": float(threshold),
                "ridge": ridge, "parameters": parameters}
    weights = _ridge(features, targets, ridge)
    if kind == "R":
        symmetric = 0.5 * (weights[1:1 + NODES] + weights[1:1 + NODES].T)
        residual = targets - current @ symmetric
        rest = np.concatenate((np.ones((len(current), 1)), forcing), axis=1)
        rest_weights = _ridge(rest, residual, ridge)
        weights = np.vstack((rest_weights[0], symmetric, rest_weights[1:]))
        parameters = NODES * (NODES + 1) // 2 + NODES * NODES + NODES
    else:
        parameters = int(weights.size)
    return {"kind": kind, "weights": weights, "ridge": ridge, "parameters": parameters}


def _predict(model: dict[str, Any], current: np.ndarray, previous: np.ndarray,
             forcing: np.ndarray) -> np.ndarray:
    features = _features(model["kind"], current, previous, forcing)
    if model["kind"] == "S":
        mask = current[:, 0] >= model["threshold"]
        output = np.empty((len(current), NODES), dtype=np.float64)
        output[~mask] = features[~mask] @ model["weights"][0]
        output[mask] = features[mask] @ model["weights"][1]
        return output
    return features @ model["weights"]


def _rollout(model: dict[str, Any], states: np.ndarray, inputs: np.ndarray) -> np.ndarray:
    predicted = np.empty_like(states)
    predicted[:, :2] = states[:, :2]
    for time in range(1, TIMES - 1):
        predicted[:, time + 1] = _predict(model, predicted[:, time], predicted[:, time - 1], inputs[:, time])
        if not np.all(np.isfinite(predicted[:, time + 1])) or np.max(np.abs(predicted[:, time + 1])) >= MAX_ABS_STATE:
            return np.full_like(states, np.nan)
    return predicted


def _metrics(model: dict[str, Any], states: np.ndarray, inputs: np.ndarray) -> dict[str, Any]:
    current, previous, forcing, targets = _rows(states, inputs)
    one = _predict(model, current, previous, forcing)
    rolled = _rollout(model, states, inputs)
    target_scale = float(np.std(targets))
    if target_scale <= 0 or not np.all(np.isfinite(one)) or not np.all(np.isfinite(rolled)):
        return {"one_step": math.inf, "rollout": math.inf, "composite": math.inf}
    one_error = float(np.sqrt(np.mean((one - targets) ** 2)) / target_scale)
    roll_error = float(np.sqrt(np.mean((rolled[:, 2:] - states[:, 2:]) ** 2)) / target_scale)
    return {"one_step": one_error, "rollout": roll_error, "composite": 0.5 * (one_error + roll_error),
            "one_step_prediction": one.reshape(states.shape[0], TIMES - 2, NODES)}


def _validation_score(metrics: dict[str, Any], parameters: int, states: np.ndarray) -> float:
    scalar_count = states.shape[0] * (TIMES - 2) * NODES
    return float(metrics["composite"] + 2.0 * parameters / scalar_count)


def _model_hash(model: dict[str, Any]) -> str:
    parts = [model["kind"].encode(), repr((model["ridge"], model["parameters"], model.get("threshold"))).encode()]
    weights: Iterable[np.ndarray] = model["weights"] if isinstance(model["weights"], tuple) else (model["weights"],)
    parts.extend(np.ascontiguousarray(item).tobytes() for item in weights)
    return _sha(b"".join(parts))


def select_model(train: tuple[np.ndarray, np.ndarray], validation: tuple[np.ndarray, np.ndarray]) -> dict[str, Any]:
    """Select using train/validation only; this API deliberately has no unseen argument."""
    train_states, train_inputs = train
    validation_states, validation_inputs = validation
    fitted: dict[str, dict[str, Any]] = {}
    for kind in CANDIDATES:
        options: list[dict[str, Any]] = []
        thresholds = (None,)
        if kind == "S":
            current = train_states[:, 1:-1, 0].reshape(-1)
            thresholds = tuple(sorted({0.0, *(float(np.quantile(current, quantile))
                                               for quantile in THRESHOLD_QUANTILES)}))
        for ridge in RIDGES:
            for threshold in thresholds:
                try:
                    model = _fit_linear(kind, train_states, train_inputs, ridge, threshold=threshold)
                    metrics = _metrics(model, validation_states, validation_inputs)
                    score = _validation_score(metrics, model["parameters"], validation_states)
                except (ValueError, RuntimeError, np.linalg.LinAlgError):
                    continue
                options.append({"model": model, "metrics": metrics, "score": score})
        if not options:
            raise RuntimeError(f"{STOP}:no candidate fit:{kind}")
        fitted[kind] = min(options, key=lambda row: (row["score"], row["model"]["parameters"],
                                                     row["model"].get("threshold", -math.inf), row["model"]["ridge"]))
    ordered = sorted(fitted.items(), key=lambda item: (item[1]["score"], item[1]["model"]["parameters"], item[0]))
    winner_kind, winner = ordered[0]
    descriptor = {"kind": winner_kind, "model_sha256": _model_hash(winner["model"]),
                  "validation_score": winner["score"], "validation_metrics": _compact_metrics(winner["metrics"]),
                  "runner_up": ordered[1][0], "runner_up_score": ordered[1][1]["score"],
                  "margin": ordered[1][1]["score"] - winner["score"]}
    return {"winner": winner["model"], "descriptor": descriptor, "all": fitted}


def _compact_metrics(metrics: dict[str, Any]) -> dict[str, float]:
    return {key: float(metrics[key]) for key in ("one_step", "rollout", "composite")}


def _persistence(states: np.ndarray) -> float:
    targets = states[:, 2:]
    scale = float(np.std(targets))
    one = states[:, 1:-1]
    rolled = np.repeat(states[:, 1:2], TIMES - 2, axis=1)
    return 0.5 * (float(np.sqrt(np.mean((one - targets) ** 2)) / scale)
                  + float(np.sqrt(np.mean((rolled - targets) ** 2)) / scale))


def _permutation_control(selection: dict[str, Any], validation: tuple[np.ndarray, np.ndarray], seed: int) -> float:
    states, _ = validation
    rng = np.random.default_rng(seed ^ 0x9E3779B97F4A7C15)
    permuted = states[rng.permutation(len(states))]
    winner = selection["descriptor"]["kind"]
    scores: dict[str, float] = {}
    for kind, row in selection["all"].items():
        prediction = row["metrics"]["one_step_prediction"]
        targets = permuted[:, 2:]
        scale = float(np.std(targets))
        one = float(np.sqrt(np.mean((prediction - targets) ** 2)) / scale)
        scores[kind] = one + 2.0 * row["model"]["parameters"] / targets.size
    return float(min(value for kind, value in scores.items() if kind != winner) - scores[winner])


def _run_replicate_after_manifest(world: str, replicate: int) -> dict[str, Any]:
    """Evaluate unseen data only from execute(), after manifest verification."""
    splits, identity = generate(world, replicate)
    selection = select_model(splits["train"], splits["validation"])
    serialized_winner = dict(selection["descriptor"])
    serialized_sha = _sha((json.dumps(serialized_winner, sort_keys=True, separators=(",", ":")) + "\n").encode())
    unseen_metrics = _metrics(selection["winner"], *splits["unseen"])
    train_metrics = _metrics(selection["winner"], *splits["train"])
    persistence = _persistence(splits["unseen"][0])
    improvement = 1.0 - unseen_metrics["composite"] / persistence
    control = _permutation_control(selection, splits["validation"], identity["seed"])
    if not all(math.isfinite(value) for value in (unseen_metrics["composite"], persistence, improvement, control)):
        raise RuntimeError(f"{STOP}:finite replicate")
    return {"world": world, "replicate": replicate, "identity": identity,
            "selected": serialized_winner, "selected_serialization_sha256": serialized_sha,
            "unseen_opened_after_selection": True, "unseen": _compact_metrics(unseen_metrics),
            "train": _compact_metrics(train_metrics),
            "persistence_unseen_composite": persistence, "persistence_improvement": improvement,
            "permuted_winner_advantage": control}


def aggregate(rows: list[dict[str, Any]]) -> dict[str, Any]:
    if len(rows) != 84 or {(row["world"], row["replicate"]) for row in rows} != {
            (world, replicate) for world in WORLDS for replicate in range(12)}:
        raise RuntimeError(f"{STOP}:replicate population")
    worlds: dict[str, Any] = {}
    full_pass = True
    geometry_pass = True
    history_pass = True
    for world in WORLDS:
        group = [row for row in rows if row["world"] == world]
        expected = EXPECTED[world]
        wins = sum(row["selected"]["kind"] == expected for row in group)
        margin = float(np.median([row["selected"]["margin"] for row in group]))
        unseen = float(np.median([row["unseen"]["composite"] for row in group]))
        improvements = sum(row["persistence_improvement"] >= 0.20 for row in group)
        controls = sum(row["permuted_winner_advantage"] <= 0.02 for row in group)
        gates = {"winner_frequency": wins >= 10,
                 "margin": True if world in "FG" else margin >= MIN_VALIDATION_MARGIN,
                 "unseen": unseen <= 0.50, "persistence": improvements >= 10, "permutation": controls >= 10}
        passed = all(gates.values())
        full_pass &= passed
        if world in "ABCDE":
            geometry_pass &= passed
        else:
            history_pass &= passed
        counts = {kind: sum(row["selected"]["kind"] == kind for row in group) for kind in CANDIDATES}
        worlds[world] = {"expected": expected, "winner_counts": counts, "expected_wins": wins,
                         "median_margin": margin, "median_unseen_composite": unseen,
                         "persistence_improvement_passes": improvements,
                         "permutation_control_passes": controls, "gates": gates, "pass": passed}
    if full_pass:
        status = "STAGE0_PASS"
    elif not geometry_pass:
        status = "STAGE0_STRUCTURE_DISCRIMINATION_STOP"
    elif not history_pass:
        status = "STAGE0_HISTORY_IDENTIFIABILITY_STOP"
    else:
        raise AssertionError("unreachable")
    return {"status": status, "worlds": worlds, "stage1_authorized": full_pass,
            "real_brain_geometry_claim": False}


def _atomic_json(path: Path, payload: dict[str, Any]) -> str:
    body = (json.dumps(payload, indent=2, sort_keys=True) + "\n").encode()
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_bytes(body)
    temporary.replace(path)
    return _sha(body)


def seal(run_root: Path) -> dict[str, Any]:
    files: dict[str, str] = {}
    for relative in PREREG_FILES:
        path = run_root / relative
        if not path.is_file():
            raise RuntimeError(f"{STOP}:missing prereg file:{relative}")
        files[relative] = _sha(path.read_bytes())
    payload = {"schema": 1, "root_seed": ROOT_SEED, "worlds": list(WORLDS),
               "replicates_per_world": 12, "files": files, "outcome_opened": False}
    digest = _atomic_json(run_root / "artifacts" / MANIFEST_NAME, payload)
    return {"manifest_sha256": digest, **payload}


def verify_manifest(run_root: Path) -> tuple[dict[str, Any], str]:
    path = run_root / "artifacts" / MANIFEST_NAME
    if not path.is_file():
        raise RuntimeError(f"{STOP}:missing manifest")
    body = path.read_bytes()
    payload = json.loads(body)
    if payload.get("outcome_opened") is not False or payload.get("root_seed") != ROOT_SEED:
        raise RuntimeError(f"{STOP}:manifest identity")
    for relative, expected in payload.get("files", {}).items():
        if _sha((run_root / relative).read_bytes()) != expected:
            raise RuntimeError(f"{STOP}:manifest mismatch:{relative}")
    if set(payload.get("files", {})) != set(PREREG_FILES):
        raise RuntimeError(f"{STOP}:manifest population")
    return payload, _sha(body)


def execute(run_root: Path) -> dict[str, Any]:
    _, manifest_sha = verify_manifest(run_root)
    rows = [_run_replicate_after_manifest(world, replicate)
            for world in WORLDS for replicate in range(12)]
    result = aggregate(rows)
    payload = {"schema": 1, "manifest_sha256": manifest_sha, "result": result, "replicates": rows,
               "persistent_raw_bytes": 0, "unseen_opened_once_after_selection": True}
    digest = _atomic_json(run_root / "artifacts" / RESULT_NAME, payload)
    print(json.dumps({"receipt_sha256": digest, **result}, sort_keys=True), flush=True)
    return payload


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seal", action="store_true")
    arguments = parser.parse_args()
    run_root = Path(__file__).resolve().parent.parent
    if arguments.seal:
        print(json.dumps(seal(run_root), sort_keys=True), flush=True)
    else:
        execute(run_root)


if __name__ == "__main__":
    main()
