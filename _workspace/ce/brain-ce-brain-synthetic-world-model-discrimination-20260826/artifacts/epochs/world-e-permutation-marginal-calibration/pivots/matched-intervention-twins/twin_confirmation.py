"""Outcome-blind matched-intervention twin confirmation for the frozen Stage 0 parent."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
from pathlib import Path
from typing import Any

import numpy as np


ROOT_SEED = 5230705416521308865218892620027730619
ROOT_DIGEST = "bb1a19f7c19bdc6e39893a28b065ef030cfa9b22d17a9bc7084fd6477bc85139"
ROOT_LABEL = "CE-BRAIN-STAGE0-TWIN-CONFIRMATION|v1|26082600"
PARENT_SHA256 = "7589e09f1d647d78f6e0f315e09ff5af15730a05ae55e87b0928db7001184b60"
WORLDS = tuple("ABCDEFG")
EXPECTED = {"A": "R", "B": "G", "C": "F", "D": "S", "E": "O", "F": "O", "G": "O"}
REPLICATES = 12
BLOCKS = 8
TWINS = 8
PERMUTATIONS = 999
TIMES = 64
NODES = 8
STOP = "TWIN_CONFIRMATION_STOP"
MANIFEST_NAME = "twin-confirmation-preregistration-manifest.json"
RESULT_NAME = "twin-confirmation-result.json"
PREREG_FILES = (
    "contract.md", "route.json", "10-data-lock.md", "20-hypotheses.md", "30-models.md",
    "40-metrics.md", "50-gates.md", "60-negative-controls.md", "twin_confirmation.py",
    "test_twin_confirmation.py", "20-audit.md", "21-preexecution-validation.md",
)


def _sha(body: bytes) -> str:
    return hashlib.sha256(body).hexdigest()


def _verify_root_seed() -> None:
    digest = hashlib.sha256(ROOT_LABEL.encode()).digest()
    if digest.hex() != ROOT_DIGEST or int.from_bytes(digest[:16], "little") != ROOT_SEED:
        raise RuntimeError(f"{STOP}:root seed derivation")


def _seed(world: str, replicate: int, purpose: str, *parts: int) -> int:
    if world not in WORLDS or type(replicate) is not int or not 0 <= replicate < REPLICATES:
        raise ValueError(f"{STOP}:seed identity")
    text = "|".join(map(str, ("CE-BRAIN-STAGE0-TWIN-CONFIRMATION", "v1", ROOT_SEED, world,
                                      replicate, purpose, *parts)))
    return int.from_bytes(hashlib.sha256(text.encode()).digest()[:16], "little")


def _parent_path(run_root: Path) -> Path:
    return run_root / "artifacts" / "stage0_synthetic_discrimination.py"


def _verify_parent_source(path: Path) -> None:
    if not path.is_file() or _sha(path.read_bytes()) != PARENT_SHA256:
        raise RuntimeError(f"{STOP}:parent source hash")


def _parent(run_root: Path) -> Any:
    path = _parent_path(run_root)
    _verify_parent_source(path)
    spec = importlib.util.spec_from_file_location("sealed_stage0_parent", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"{STOP}:parent import")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _array_hash(*arrays: np.ndarray) -> str:
    return _sha(b"".join(np.ascontiguousarray(array, dtype=np.float64).tobytes() for array in arrays))


def _pivot_path() -> Path:
    return Path(__file__).resolve().parent


def _run_root() -> Path:
    # matched-intervention-twins/pivots/world-e.../epochs/artifacts/<run-root>
    return _pivot_path().parents[4]


def _fresh_splits(parent: Any, world: str, replicate: int) -> tuple[dict[str, tuple[np.ndarray, np.ndarray]], dict[str, Any]]:
    coefficients = parent._coefficients(world, np.random.default_rng(_seed(world, replicate, "coefficients")))
    splits: dict[str, tuple[np.ndarray, np.ndarray]] = {}
    split_hashes: dict[str, str] = {}
    trajectory_hashes: dict[str, list[str]] = {}
    for split in ("train", "validation"):
        inputs = parent._inputs(np.random.default_rng(_seed(world, replicate, "inputs", 0 if split == "train" else 1)), split)
        states = parent._simulate(world, coefficients, inputs,
                                  np.random.default_rng(_seed(world, replicate, "state", 0 if split == "train" else 1)))
        splits[split] = (states, inputs)
        split_hashes[split] = _array_hash(states, inputs)
        trajectory_hashes[split] = [_array_hash(states[row], inputs[row]) for row in range(len(states))]
    flat = [item for rows in trajectory_hashes.values() for item in rows]
    if len(set(split_hashes.values())) != 2 or len(set(flat)) != len(flat):
        raise RuntimeError(f"{STOP}:split overlap")
    return splits, {"world": world, "replicate": replicate, "coefficient_sha256": parent._coefficient_hash(coefficients),
                     "split_sha256": split_hashes, "trajectory_sha256": trajectory_hashes}


def _serialized_selection(parent: Any, selection: dict[str, Any]) -> tuple[dict[str, Any], str]:
    candidates = {}
    for kind, row in sorted(selection["all"].items()):
        candidates[kind] = {"model_sha256": parent._model_hash(row["model"]), "validation_score": float(row["score"]),
                            "validation_metrics": parent._compact_metrics(row["metrics"])}
    record = {"winner": selection["descriptor"], "candidates": candidates}
    body = _selection_serialization_body(record)
    if record["winner"]["model_sha256"] != candidates[record["winner"]["kind"]]["model_sha256"]:
        raise RuntimeError(f"{STOP}:winner serialization")
    return record, _sha(body)


def _selection_serialization_body(record: dict[str, Any]) -> bytes:
    return (json.dumps(record, sort_keys=True, separators=(",", ":")) + "\n").encode()


def _pulse_inputs(block: int) -> tuple[np.ndarray, np.ndarray]:
    if not 0 <= block < BLOCKS:
        raise ValueError(f"{STOP}:block")
    arms = np.zeros((2, TIMES, NODES), dtype=np.float64)
    arms[0, 12:16, block] = 0.9
    arms[0, 31:35, block] = -0.45
    arms[1, 12:16, block] = -0.9
    arms[1, 31:35, block] = 0.45
    return arms[0], arms[1]


def _simulate_pair(parent: Any, world: str, coefficients: dict[str, Any], inputs: tuple[np.ndarray, np.ndarray], seed: int) -> tuple[np.ndarray, str]:
    """Two arms use the exact same simulator-side initial/hidden/noise arrays."""
    rng = np.random.default_rng(seed)
    initial = rng.uniform(-0.45, 0.45, size=NODES)
    initial_step = rng.normal(scale=0.03, size=NODES)
    hidden_initial = rng.normal(scale=0.18, size=parent.HIDDEN_NODES) if world == "F" else np.empty(0, dtype=np.float64)
    innovations = rng.normal(scale=parent.NOISE_SD, size=(TIMES - 2, NODES))
    states = np.zeros((2, TIMES, NODES), dtype=np.float64)
    for arm in range(2):
        states[arm, 0] = initial
        states[arm, 1] = initial + initial_step
        hidden = hidden_initial.copy() if world == "F" else None
        for time in range(1, TIMES - 1):
            current, previous, forcing = states[arm, time], states[arm, time - 1], inputs[arm][time]
            if world in {"A", "B"}:
                next_state = current @ coefficients["A"].T + forcing @ coefficients["B"].T
            elif world == "C":
                next_state = (current @ coefficients["A"].T + np.maximum(forcing, 0) @ coefficients["B_pos"].T
                              + np.minimum(forcing, 0) @ coefficients["B_neg"].T)
            elif world == "D":
                low, high = current @ coefficients["A0"].T, current @ coefficients["A1"].T
                next_state = np.where(current[:1] >= coefficients["threshold"], high, low) + forcing @ coefficients["B"].T
            elif world == "E":
                next_state = (current @ coefficients["A"].T + forcing @ coefficients["B"].T
                              + coefficients["quadratic"] * current ** 2 + coefficients["state_input"] * current * forcing)
            elif world == "F":
                assert hidden is not None
                next_state = current @ coefficients["Axx"].T + hidden @ coefficients["Axh"].T + forcing @ coefficients["Bx"].T
                hidden = hidden @ coefficients["Ahh"].T + current @ coefficients["Ahx"].T + forcing @ coefficients["Bh"].T
            elif world == "G":
                next_state = current @ coefficients["A1"].T + previous @ coefficients["A2"].T + forcing @ coefficients["B"].T
            else:
                raise ValueError(f"{STOP}:world")
            states[arm, time + 1] = next_state + innovations[time - 1]
    if not np.all(np.isfinite(states)) or np.max(np.abs(states)) >= parent.MAX_ABS_STATE:
        raise RuntimeError(f"{STOP}:twin state")
    return states, _array_hash(initial, initial_step, hidden_initial, innovations)


def _generate_twins(parent: Any, world: str, replicate: int, coefficients: dict[str, Any], serialized_sha: str | None) -> tuple[np.ndarray, np.ndarray, dict[str, Any]]:
    if not serialized_sha:
        raise RuntimeError(f"{STOP}:confirmation before serialization")
    actual = np.empty((BLOCKS, TWINS, 2, TIMES, NODES), dtype=np.float64)
    inputs = np.empty_like(actual)
    records: list[dict[str, Any]] = []
    for block in range(BLOCKS):
        pair_inputs = _pulse_inputs(block)
        for twin in range(TWINS):
            arm_states, common_sha = _simulate_pair(parent, world, coefficients, pair_inputs,
                                                     _seed(world, replicate, "twin", block, twin))
            actual[block, twin] = arm_states
            inputs[block, twin, 0], inputs[block, twin, 1] = pair_inputs
            arm_hashes = [_array_hash(arm_states[arm], pair_inputs[arm]) for arm in range(2)]
            records.append({"block": block, "twin": twin, "common_random_sha256": common_sha,
                            "arm_sha256": arm_hashes, "contrast_sha256": _array_hash(arm_states[1] - arm_states[0])})
    _verify_twin_receipts(records)
    return actual, inputs, {"descriptor_serialization_sha256": serialized_sha, "twins": records,
                            "confirmation_sha256": _array_hash(actual, inputs),
                            # Linear worlds intentionally repeat contrast identities across twins.
                            "unique_contrast_sha256_count": len({record["contrast_sha256"] for record in records})}


def _verify_twin_receipts(records: list[dict[str, Any]]) -> None:
    if len(records) != BLOCKS * TWINS:
        raise RuntimeError(f"{STOP}:twin receipt population")
    keys = {(record.get("block"), record.get("twin")) for record in records}
    arms = [digest for record in records for digest in record.get("arm_sha256", [])]
    contrasts = [record.get("contrast_sha256") for record in records]
    common = [record.get("common_random_sha256") for record in records]
    if (len(keys) != BLOCKS * TWINS or len(arms) != 2 * BLOCKS * TWINS or any(not item for item in contrasts)
            or len(common) != BLOCKS * TWINS or any(not item for item in common)
            or len(set(arms)) != len(arms) or len(set(common)) != len(common)):
        raise RuntimeError(f"{STOP}:twin receipt")


def _verify_cross_split_disjoint(identity: dict[str, Any], records: list[dict[str, Any]]) -> None:
    trajectory_hashes = identity.get("trajectory_sha256", {})
    train, validation = trajectory_hashes.get("train"), trajectory_hashes.get("validation")
    if (not isinstance(train, list) or not isinstance(validation, list) or len(train) != 96 or len(validation) != 48
            or any(not digest for digest in (*train, *validation))):
        raise RuntimeError(f"{STOP}:split receipt population")
    split_hashes = set(train) | set(validation)
    if len(split_hashes) != len(train) + len(validation):
        raise RuntimeError(f"{STOP}:split overlap")
    arm_hashes = {digest for record in records for digest in record["arm_sha256"]}
    if split_hashes & arm_hashes:
        raise RuntimeError(f"{STOP}:split twin overlap")


def _nrmse(prediction: np.ndarray, target: np.ndarray) -> float:
    observed, expected = prediction[..., 2:, :], target[..., 2:, :]
    scale = float(np.std(expected))
    if not math.isfinite(scale) or scale <= 0:
        raise RuntimeError(f"{STOP}:zero contrast scale")
    value = float(np.sqrt(np.mean((observed - expected) ** 2)) / scale)
    if not math.isfinite(value):
        raise RuntimeError(f"{STOP}:nonfinite loss")
    return value


def _fisher_yates(size: int, seed: int) -> np.ndarray:
    values = np.arange(size)
    rng = np.random.default_rng(seed)
    for index in range(size - 1, 0, -1):
        other = int(rng.integers(0, index + 1))
        values[index], values[other] = values[other], values[index]
    return values


def _permuted_loss(predicted: np.ndarray, target: np.ndarray, world: str, replicate: int, draw: int) -> float:
    if predicted.shape != target.shape or target.shape[:2] != (BLOCKS, TWINS):
        raise RuntimeError(f"{STOP}:cross block permutation")
    shuffled = np.empty_like(target)
    for block in range(BLOCKS):
        shuffled[block] = target[block, _fisher_yates(TWINS, _seed(world, replicate, "permutation", draw, block))]
    return _nrmse(predicted, shuffled)


def _twin_identity(target: np.ndarray) -> bool:
    residual = target - target.mean(axis=1, keepdims=True)
    return bool(np.max(np.abs(residual)) <= 1e-12 * max(1.0, float(np.max(np.abs(target)))))


def _equal_arm_control(target: np.ndarray) -> dict[str, float]:
    """A zero prediction is invariant to any within-block target reordering."""
    return {"equal_arm_nrmse": _nrmse(np.zeros_like(target), target), "equal_arm_advantage": 0.0,
            "equal_arm_p_value": 1.0}


def _score_winner(parent: Any, winner: dict[str, Any], actual: np.ndarray, inputs: np.ndarray,
                  world: str, replicate: int) -> dict[str, Any]:
    predicted = np.empty_like(actual)
    for block in range(BLOCKS):
        for twin in range(TWINS):
            for arm in range(2):
                predicted[block, twin, arm] = parent._rollout(winner, actual[block, twin, arm:arm + 1], inputs[block, twin, arm:arm + 1])[0]
    contrast, predicted_contrast = actual[:, :, 1] - actual[:, :, 0], predicted[:, :, 1] - predicted[:, :, 0]
    loss = _nrmse(predicted_contrast, contrast)
    equal_arm = _equal_arm_control(contrast)
    if world in {"D", "E"}:
        identifiable = bool(np.max(np.abs(contrast - contrast.mean(axis=1, keepdims=True))) > 1e-8 * max(1.0, float(np.max(np.abs(contrast)))))
        losses = [_permuted_loss(predicted_contrast, contrast, world, replicate, draw) for draw in range(PERMUTATIONS)]
        p_value = (1 + sum(item <= loss for item in losses)) / (PERMUTATIONS + 1)
        advantage = float(np.mean(losses) - loss)
    else:
        identifiable, losses, p_value, advantage = _twin_identity(contrast), [], 1.0, 0.0
    # The equal-arm vector is exactly zero, so every within-block shuffle has identical loss.
    return {"winner_twin_nrmse": loss, "identifiable_or_linear_identity": identifiable,
            "permutation_p_value": float(p_value), "pairing_advantage": advantage, **equal_arm,
            "predicted_contrast_sha256": _array_hash(predicted_contrast), "contrast_sha256": _array_hash(contrast),
            "permuted_loss_count": len(losses)}


def _run_replicate(run_root: Path, parent: Any, world: str, replicate: int) -> dict[str, Any]:
    splits, identity = _fresh_splits(parent, world, replicate)
    selection = parent.select_model(splits["train"], splits["validation"])
    serialized, serialization_sha = _serialized_selection(parent, selection)
    coefficients = parent._coefficients(world, np.random.default_rng(_seed(world, replicate, "coefficients")))
    actual, inputs, receipts = _generate_twins(parent, world, replicate, coefficients, serialization_sha)
    _verify_cross_split_disjoint(identity, receipts["twins"])
    scores = _score_winner(parent, selection["winner"], actual, inputs, world, replicate)
    return {"world": world, "replicate": replicate, "identity": identity, "selection": serialized,
            "selection_serialization_sha256": serialization_sha, "twin_receipts": receipts, "scores": scores}


def _verify_result_row(row: dict[str, Any]) -> None:
    world, replicate = row.get("world"), row.get("replicate")
    if world not in WORLDS or type(replicate) is not int or not 0 <= replicate < REPLICATES:
        raise RuntimeError(f"{STOP}:row identity")
    identity, selection, receipts = row.get("identity"), row.get("selection"), row.get("twin_receipts")
    if not isinstance(identity, dict) or identity.get("world") != world or identity.get("replicate") != replicate:
        raise RuntimeError(f"{STOP}:row split identity")
    if not isinstance(selection, dict) or not isinstance(receipts, dict):
        raise RuntimeError(f"{STOP}:row receipt")
    serialization_sha = _sha(_selection_serialization_body(selection))
    if (serialization_sha != row.get("selection_serialization_sha256")
            or serialization_sha != receipts.get("descriptor_serialization_sha256")):
        raise RuntimeError(f"{STOP}:selection serialization receipt")
    winner, candidates = selection.get("winner"), selection.get("candidates")
    if not isinstance(winner, dict) or not isinstance(candidates, dict) or winner.get("kind") not in candidates:
        raise RuntimeError(f"{STOP}:selection receipt")
    if winner.get("model_sha256") != candidates[winner["kind"]].get("model_sha256"):
        raise RuntimeError(f"{STOP}:winner receipt")
    records = receipts.get("twins")
    if not isinstance(records, list):
        raise RuntimeError(f"{STOP}:twin receipt")
    _verify_twin_receipts(records)
    _verify_cross_split_disjoint(identity, records)
    if not receipts.get("confirmation_sha256"):
        raise RuntimeError(f"{STOP}:confirmation receipt")


def aggregate(rows: list[dict[str, Any]]) -> dict[str, Any]:
    _verify_root_seed()
    expected_population = {(world, replicate) for world in WORLDS for replicate in range(REPLICATES)}
    if len(rows) != len(expected_population) or {(row["world"], row["replicate"]) for row in rows} != expected_population:
        raise RuntimeError(f"{STOP}:population")
    for row in rows:
        _verify_result_row(row)
    worlds: dict[str, Any] = {}
    full, structural, history = True, True, True
    for world in WORLDS:
        group = [row for row in rows if row["world"] == world]
        expected_wins = sum(row["selection"]["winner"]["kind"] == EXPECTED[world] for row in group)
        med_loss = float(np.median([row["scores"]["winner_twin_nrmse"] for row in group]))
        equal = all(row["scores"]["equal_arm_advantage"] == 0.0 and row["scores"]["equal_arm_p_value"] == 1.0 for row in group)
        identities = all(row["scores"]["identifiable_or_linear_identity"] for row in group)
        finite = all(all(math.isfinite(float(value)) for value in row["scores"].values() if isinstance(value, (int, float))) for row in group)
        gates = {"winner_frequency": expected_wins >= 10, "twin_nrmse": med_loss <= 0.50,
                 "equal_arm": equal, "identities": identities, "finite": finite}
        if world in {"D", "E"}:
            gates["permutation"] = sum(row["scores"]["permutation_p_value"] <= 0.01 for row in group) >= 10
        passed = all(gates.values())
        full &= passed
        if world in "ABCDE": structural &= passed
        else: history &= passed
        worlds[world] = {"expected": EXPECTED[world], "expected_wins": expected_wins,
                         "median_winner_twin_nrmse": med_loss, "gates": gates, "pass": passed}
    status = "TWIN_STAGE0_CONFIRMATION_PASS" if full else ("TWIN_STRUCTURE_CONFIRMATION_STOP" if not structural else "TWIN_HISTORY_CONFIRMATION_STOP")
    return {"status": status, "worlds": worlds, "stage1_authorized": full, "real_brain_geometry_claim": False}


def _atomic_json(path: Path, payload: dict[str, Any]) -> str:
    body = (json.dumps(payload, indent=2, sort_keys=True) + "\n").encode()
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_bytes(body)
    temporary.replace(path)
    return _sha(body)


def seal(run_root: Path, *, pivot: Path | None = None) -> dict[str, Any]:
    _verify_root_seed()
    _verify_parent_source(_parent_path(run_root))
    files = {}
    pivot = _pivot_path() if pivot is None else pivot
    for relative in PREREG_FILES:
        path = pivot / relative
        if not path.is_file():
            raise RuntimeError(f"{STOP}:missing prereg:{relative}")
        files[relative] = _sha(path.read_bytes())
    payload = {"schema": 1, "root_seed": ROOT_SEED, "root_seed_sha256": ROOT_DIGEST, "parent_source_sha256": PARENT_SHA256,
               "worlds": list(WORLDS), "replicates_per_world": REPLICATES, "files": files, "outcome_opened": False}
    digest = _atomic_json(pivot / MANIFEST_NAME, payload)
    return {"manifest_sha256": digest, **payload}


def verify_manifest(run_root: Path, *, pivot: Path | None = None) -> tuple[dict[str, Any], str]:
    _verify_root_seed()
    _verify_parent_source(_parent_path(run_root))
    pivot = _pivot_path() if pivot is None else pivot
    path = pivot / MANIFEST_NAME
    if not path.is_file():
        raise RuntimeError(f"{STOP}:missing manifest")
    body, payload = path.read_bytes(), json.loads(path.read_bytes())
    if (payload.get("outcome_opened") is not False or payload.get("root_seed") != ROOT_SEED
            or payload.get("root_seed_sha256") != ROOT_DIGEST or payload.get("parent_source_sha256") != PARENT_SHA256
            or set(payload.get("files", {})) != set(PREREG_FILES)):
        raise RuntimeError(f"{STOP}:manifest identity")
    for relative, digest in payload["files"].items():
        if _sha((pivot / relative).read_bytes()) != digest:
            raise RuntimeError(f"{STOP}:manifest mismatch:{relative}")
    return payload, _sha(body)


def execute(run_root: Path, *, pivot: Path | None = None) -> dict[str, Any]:
    pivot = _pivot_path() if pivot is None else pivot
    _, manifest_sha = verify_manifest(run_root, pivot=pivot)
    parent = _parent(run_root)
    rows = [_run_replicate(run_root, parent, world, replicate) for world in WORLDS for replicate in range(REPLICATES)]
    result = aggregate(rows)
    payload = {"schema": 1, "manifest_sha256": manifest_sha, "parent_source_sha256": PARENT_SHA256,
               "result": result, "replicates": rows, "persistent_raw_bytes": 0}
    digest = _atomic_json(pivot / RESULT_NAME, payload)
    print(json.dumps({"receipt_sha256": digest, **result}, sort_keys=True), flush=True)
    return payload


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seal", action="store_true")
    args = parser.parse_args()
    run_root = _run_root()
    if args.seal:
        print(json.dumps(seal(run_root), sort_keys=True), flush=True)
    else:
        execute(run_root)


if __name__ == "__main__":
    main()
