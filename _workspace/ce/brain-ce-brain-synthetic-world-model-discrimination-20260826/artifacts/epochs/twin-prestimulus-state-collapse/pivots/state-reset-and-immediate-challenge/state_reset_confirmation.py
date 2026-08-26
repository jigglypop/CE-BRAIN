"""Outcome-blind paired-Hadamard reset confirmation for the sealed Stage 0 parent."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
from pathlib import Path
from typing import Any

import numpy as np


ROOT_LABEL = "CE-BRAIN-STAGE0-STATE-RESET-CONFIRMATION|v1|26082600"
ROOT_DIGEST = "0b3301db126c273dab5cd9594c0039d0506892f9434a01aba9d7806cdfeb7eca"
ROOT_SEED = 276775390093346278216380119786172003083
PARENT_SHA256 = "7589e09f1d647d78f6e0f315e09ff5af15730a05ae55e87b0928db7001184b60"
WORLDS, REPLICATES, BLOCKS, TWINS, TIMES, NODES, PERMUTATIONS = tuple("ABCDEFG"), 12, 8, 8, 64, 8, 999
EXPECTED = {"A": "R", "B": "G", "C": "F", "D": "S", "E": "O", "F": "O", "G": "O"}
STOP = "STATE_RESET_CONFIRMATION_STOP"
MANIFEST_NAME, RESULT_NAME = "state-reset-preregistration-manifest.json", "state-reset-result.json"
PREREG_FILES = (
    "contract.md", "route.json", "10-data-lock.md", "20-hypotheses.md", "30-models.md", "40-metrics.md",
    "50-gates.md", "60-negative-controls.md", "20-audit.md", "21-preexecution-validation.md",
    "state_reset_confirmation.py", "test_state_reset_confirmation.py",
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
    text = "|".join(map(str, ("CE-BRAIN-STAGE0-STATE-RESET-CONFIRMATION", "v1", ROOT_SEED,
                                world, replicate, purpose, *parts)))
    return int.from_bytes(hashlib.sha256(text.encode()).digest()[:16], "little")


def _pivot_path() -> Path:
    return Path(__file__).resolve().parent


def _run_root() -> Path:
    return _pivot_path().parents[4]


def _parent_path(run_root: Path) -> Path:
    return run_root / "artifacts" / "stage0_synthetic_discrimination.py"


def _verify_parent_source(path: Path) -> None:
    if not path.is_file() or _sha(path.read_bytes()) != PARENT_SHA256:
        raise RuntimeError(f"{STOP}:parent source hash")


def _parent(run_root: Path) -> Any:
    path = _parent_path(run_root)
    _verify_parent_source(path)
    spec = importlib.util.spec_from_file_location("sealed_stage0_parent_reset", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"{STOP}:parent import")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _array_hash(*arrays: np.ndarray) -> str:
    return _sha(b"".join(np.ascontiguousarray(item, dtype=np.float64).tobytes() for item in arrays))


def _hadamard_bank() -> np.ndarray:
    matrix = np.array([[1.0]])
    while matrix.shape[0] < NODES:
        matrix = np.block([[matrix, matrix], [matrix, -matrix]])
    bank = np.vstack((matrix[[0, 1, 2, 4]], -matrix[[0, 1, 2, 4]]))
    if (bank.shape != (NODES, NODES) or not np.array_equal(bank[:4] @ bank[:4].T, NODES * np.eye(4))
            or not np.array_equal(bank[4:], -bank[:4]) or not np.array_equal(bank.sum(axis=0), np.zeros(NODES))):
        raise RuntimeError(f"{STOP}:hadamard bank")
    return bank


def _state_for(block: int, row: int) -> np.ndarray:
    if not 0 <= block < BLOCKS or not 0 <= row < TWINS:
        raise ValueError(f"{STOP}:state bank index")
    return 0.30 * np.roll(_hadamard_bank()[row], block)


def _verify_bank(states: np.ndarray, *, expected_count: int | None = None, coordinate_balanced: bool = True) -> None:
    if states.shape[-1] != NODES or not np.all(np.isfinite(states)):
        raise RuntimeError(f"{STOP}:bank finite")
    if coordinate_balanced and not np.allclose(states.mean(axis=0), 0.0, atol=1e-15):
        raise RuntimeError(f"{STOP}:bank coordinate balance")
    if not np.isclose(float(np.sqrt(np.mean(states ** 2))), 0.30, atol=1e-15):
        raise RuntimeError(f"{STOP}:bank rms")
    if expected_count is not None:
        # Exact label counts are validated by the assignment constructor; this is a receipt shape guard.
        if len(states) != expected_count * TWINS:
            raise RuntimeError(f"{STOP}:bank population")


def _reset_assignment(count: int) -> tuple[np.ndarray, list[tuple[int, int]]]:
    labels = [(q % BLOCKS, ((q // BLOCKS) + (q % BLOCKS)) % TWINS) for q in range(count)]
    states = np.array([_state_for(block, row) for block, row in labels])
    expected = 12 if count == 96 else 6 if count == 48 else None
    if expected is None or [sum(row == item for _, row in labels) for item in range(TWINS)] != [expected] * TWINS:
        raise RuntimeError(f"{STOP}:reset assignment")
    _verify_bank(states, expected_count=expected, coordinate_balanced=False)
    return states, labels


def _verify_assignment_receipt(assignment: Any) -> None:
    if not isinstance(assignment, dict) or set(assignment) != {"train", "validation"}:
        raise RuntimeError(f"{STOP}:assignment receipt")
    for split, count, expected_row_count in (("train", 96, 12), ("validation", 48, 6)):
        actual = assignment[split]
        expected = [[q % BLOCKS, ((q // BLOCKS) + (q % BLOCKS)) % TWINS] for q in range(count)]
        if not isinstance(actual, list) or [list(value) for value in actual] != expected:
            raise RuntimeError(f"{STOP}:assignment formula")
        if ([sum(value[0] == block for value in actual) for block in range(BLOCKS)] != [expected_row_count] * BLOCKS
                or [sum(value[1] == row for value in actual) for row in range(TWINS)] != [expected_row_count] * TWINS):
            raise RuntimeError(f"{STOP}:assignment population")


def _inputs(parent: Any, world: str, replicate: int, split: str) -> np.ndarray:
    split_id = 0 if split == "train" else 1
    return parent._inputs(np.random.default_rng(_seed(world, replicate, "inputs", split_id)), split)


def _simulate_reset(parent: Any, world: str, coefficients: dict[str, Any], inputs: np.ndarray,
                    resets: np.ndarray, rng: np.random.Generator) -> tuple[np.ndarray, str]:
    """Parent equations, with only x0=x1 replaced by the observed reset state."""
    count = len(inputs)
    if resets.shape != (count, NODES):
        raise RuntimeError(f"{STOP}:reset shape")
    states = np.zeros((count, TIMES, NODES), dtype=np.float64)
    states[:, 0] = resets
    states[:, 1] = resets
    hidden_initial = rng.normal(scale=0.18, size=(count, parent.HIDDEN_NODES)) if world == "F" else np.empty(0)
    hidden = hidden_initial.copy() if world == "F" else None
    innovations = rng.normal(scale=parent.NOISE_SD, size=(count, TIMES - 2, NODES))
    for time in range(1, TIMES - 1):
        x, previous, forcing = states[:, time], states[:, time - 1], inputs[:, time]
        if world in {"A", "B"}:
            next_state = x @ coefficients["A"].T + forcing @ coefficients["B"].T
        elif world == "C":
            next_state = x @ coefficients["A"].T + np.maximum(forcing, 0) @ coefficients["B_pos"].T + np.minimum(forcing, 0) @ coefficients["B_neg"].T
        elif world == "D":
            next_state = np.where(x[:, :1] >= coefficients["threshold"], x @ coefficients["A1"].T, x @ coefficients["A0"].T) + forcing @ coefficients["B"].T
        elif world == "E":
            next_state = x @ coefficients["A"].T + forcing @ coefficients["B"].T + coefficients["quadratic"] * x ** 2 + coefficients["state_input"] * x * forcing
        elif world == "F":
            assert hidden is not None
            next_state = x @ coefficients["Axx"].T + hidden @ coefficients["Axh"].T + forcing @ coefficients["Bx"].T
            hidden = hidden @ coefficients["Ahh"].T + x @ coefficients["Ahx"].T + forcing @ coefficients["Bh"].T
        elif world == "G":
            next_state = x @ coefficients["A1"].T + previous @ coefficients["A2"].T + forcing @ coefficients["B"].T
        else:
            raise ValueError(f"{STOP}:world")
        states[:, time + 1] = next_state + innovations[:, time - 1]
    if not np.all(np.isfinite(states)) or np.max(np.abs(states)) >= parent.MAX_ABS_STATE:
        raise RuntimeError(f"{STOP}:reset simulation")
    return states, _array_hash(resets, hidden_initial, innovations)


def _fresh_splits(parent: Any, world: str, replicate: int) -> tuple[dict[str, tuple[np.ndarray, np.ndarray]], dict[str, Any]]:
    coefficients = parent._coefficients(world, np.random.default_rng(_seed(world, replicate, "coefficients")))
    splits, split_hashes, row_hashes, assignment = {}, {}, {}, {}
    for split, count, split_id in (("train", 96, 0), ("validation", 48, 1)):
        resets, labels = _reset_assignment(count)
        inputs = _inputs(parent, world, replicate, split)
        states, _ = _simulate_reset(parent, world, coefficients, inputs, resets,
                                    np.random.default_rng(_seed(world, replicate, "state", split_id)))
        if not np.array_equal(states[:, 0], resets) or not np.array_equal(states[:, 1], resets):
            raise RuntimeError(f"{STOP}:split reset")
        splits[split], split_hashes[split] = (states, inputs), _array_hash(states, inputs)
        row_hashes[split] = [_array_hash(states[q], inputs[q]) for q in range(count)]
        assignment[split] = [list(label) for label in labels]
    all_rows = [item for values in row_hashes.values() for item in values]
    if len(set(split_hashes.values())) != 2 or len(set(all_rows)) != len(all_rows):
        raise RuntimeError(f"{STOP}:split overlap")
    _verify_assignment_receipt(assignment)
    return splits, {"world": world, "replicate": replicate, "coefficient_sha256": parent._coefficient_hash(coefficients),
                     "split_sha256": split_hashes, "trajectory_sha256": row_hashes, "assignment": assignment}


def _selection_body(record: dict[str, Any]) -> bytes:
    return (json.dumps(record, sort_keys=True, separators=(",", ":")) + "\n").encode()


def _serialized_selection(parent: Any, selection: dict[str, Any]) -> tuple[dict[str, Any], str]:
    candidates = {kind: {"model_sha256": parent._model_hash(row["model"]), "validation_score": float(row["score"]),
                         "validation_metrics": parent._compact_metrics(row["metrics"])}
                  for kind, row in sorted(selection["all"].items())}
    record = {"winner": selection["descriptor"], "candidates": candidates}
    if record["winner"]["model_sha256"] != candidates[record["winner"]["kind"]]["model_sha256"]:
        raise RuntimeError(f"{STOP}:selection serialization")
    return record, _sha(_selection_body(record))


def _challenge_inputs(block: int) -> tuple[np.ndarray, np.ndarray]:
    if not 0 <= block < BLOCKS:
        raise ValueError(f"{STOP}:block")
    values = np.zeros((2, TIMES, NODES), dtype=np.float64)
    values[0, 1:5, block], values[0, 31:35, block] = 0.9, -0.45
    values[1, 1:5, block], values[1, 31:35, block] = -0.9, 0.45
    return values[0], values[1]


def _pair(parent: Any, world: str, coefficients: dict[str, Any], reset: np.ndarray,
          inputs: tuple[np.ndarray, np.ndarray], seed: int) -> tuple[np.ndarray, str]:
    repeated_reset = np.repeat(reset[None, :], 2, axis=0)
    paired_inputs = np.stack(inputs)
    # Each arm restarts the same one-row RNG stream, so initial hidden state and every innovation coincide.
    arms = []
    common_rng_seed = seed
    for arm in range(2):
        one, _ = _simulate_reset(parent, world, coefficients, paired_inputs[arm:arm + 1], reset[None, :], np.random.default_rng(common_rng_seed))
        arms.append(one[0])
    paired = np.stack(arms)
    if not np.array_equal(paired[:, 0], repeated_reset) or not np.array_equal(paired[:, 1], repeated_reset):
        raise RuntimeError(f"{STOP}:pair reset")
    # Receipt comes from the shared one-row latent RNG stream, never a model feature.
    _, receipt = _simulate_reset(parent, world, coefficients, paired_inputs[:1], reset[None, :], np.random.default_rng(common_rng_seed))
    return paired, receipt


def _verify_receipts(records: list[dict[str, Any]], *, unique_common: bool) -> None:
    if len(records) != BLOCKS * TWINS or {(row.get("block"), row.get("twin")) for row in records} != {(b, t) for b in range(BLOCKS) for t in range(TWINS)}:
        raise RuntimeError(f"{STOP}:receipt population")
    arms = [digest for row in records for digest in row.get("arm_sha256", [])]
    common = [row.get("common_random_sha256") for row in records]
    contrasts = [row.get("contrast_sha256") for row in records]
    if len(arms) != 2 * BLOCKS * TWINS or any(not item for item in arms + common + contrasts) or len(set(arms)) != len(arms):
        raise RuntimeError(f"{STOP}:receipt")
    if unique_common and len(set(common)) != len(common):
        raise RuntimeError(f"{STOP}:common receipt")


def _generate_main(parent: Any, world: str, replicate: int, coefficients: dict[str, Any], serialized_sha: str | None) -> tuple[np.ndarray, np.ndarray, dict[str, Any]]:
    if not serialized_sha:
        raise RuntimeError(f"{STOP}:confirmation before serialization")
    states, inputs, records = np.empty((BLOCKS, TWINS, 2, TIMES, NODES)), np.empty((BLOCKS, TWINS, 2, TIMES, NODES)), []
    for block in range(BLOCKS):
        pair_inputs = _challenge_inputs(block)
        for twin in range(TWINS):
            pair, common = _pair(parent, world, coefficients, _state_for(block, twin), pair_inputs, _seed(world, replicate, "main", block, twin))
            states[block, twin], inputs[block, twin, 0], inputs[block, twin, 1] = pair, pair_inputs[0], pair_inputs[1]
            records.append({"block": block, "twin": twin, "common_random_sha256": common,
                            "arm_sha256": [_array_hash(pair[0], pair_inputs[0]), _array_hash(pair[1], pair_inputs[1])],
                            "contrast_sha256": _array_hash(pair[1] - pair[0]),
                            "reset_sha256": _array_hash(_state_for(block, twin)),
                            "arm_reset_sha256": [_array_hash(pair[0, :2]), _array_hash(pair[1, :2])]})
    for block in range(BLOCKS):
        _verify_bank(np.array([_state_for(block, twin) for twin in range(TWINS)]))
    _verify_receipts(records, unique_common=True)
    _verify_main_reset_receipts(records)
    return states, inputs, {"descriptor_serialization_sha256": serialized_sha, "twins": records,
                            "confirmation_sha256": _array_hash(states, inputs)}


def _nrmse(prediction: np.ndarray, target: np.ndarray) -> float:
    scale = float(np.std(target[..., 2:, :]))
    value = float(np.sqrt(np.mean((prediction[..., 2:, :] - target[..., 2:, :]) ** 2)) / scale) if scale > 0 else math.inf
    if not math.isfinite(value):
        raise RuntimeError(f"{STOP}:nrmse")
    return value


def _fisher_yates(seed: int) -> np.ndarray:
    values, rng = np.arange(TWINS), np.random.default_rng(seed)
    for index in range(TWINS - 1, 0, -1):
        other = int(rng.integers(index + 1))
        values[index], values[other] = values[other], values[index]
    return values


def _permuted_loss(prediction: np.ndarray, target: np.ndarray, world: str, replicate: int, draw: int) -> float:
    if prediction.shape != target.shape or target.shape[:2] != (BLOCKS, TWINS):
        raise RuntimeError(f"{STOP}:cross block permutation")
    shuffled = np.empty_like(target)
    for block in range(BLOCKS):
        shuffled[block] = target[block, _fisher_yates(_seed(world, replicate, "permutation", draw, block))]
    return _nrmse(prediction, shuffled)


def _identity(contrast: np.ndarray) -> bool:
    return bool(np.max(np.abs(contrast - contrast.mean(axis=1, keepdims=True))) <= 1e-12 * max(1.0, float(np.max(np.abs(contrast)))))


def _score(parent: Any, winner: dict[str, Any], states: np.ndarray, inputs: np.ndarray, world: str, replicate: int) -> dict[str, Any]:
    predicted = np.empty_like(states)
    for block in range(BLOCKS):
        for twin in range(TWINS):
            for arm in range(2):
                predicted[block, twin, arm] = parent._rollout(winner, states[block, twin, arm:arm + 1], inputs[block, twin, arm:arm + 1])[0]
    target, forecast = states[:, :, 1] - states[:, :, 0], predicted[:, :, 1] - predicted[:, :, 0]
    loss = _nrmse(forecast, target)
    if world in {"D", "E"}:
        losses = [_permuted_loss(forecast, target, world, replicate, draw) for draw in range(PERMUTATIONS)]
        identifiable = not _identity(target)
        p, advantage = (1 + sum(item <= loss for item in losses)) / 1000, float(np.mean(losses) - loss)
    else:
        losses, identifiable, p, advantage = [], _identity(target), 1.0, 0.0
    return {"winner_twin_nrmse": loss, "identifiable_or_linear_identity": identifiable, "permutation_p_value": float(p),
            "pairing_advantage": advantage, "equal_arm_nrmse": _nrmse(np.zeros_like(target), target),
            "equal_arm_advantage": 0.0, "equal_arm_p_value": 1.0, "permuted_loss_count": len(losses),
            "contrast_sha256": _array_hash(target), "forecast_sha256": _array_hash(forecast)}


def _adverse_control(parent: Any, world: str, replicate: int, coefficients: dict[str, Any]) -> dict[str, Any]:
    contrasts, receipts = [], []
    for block in range(BLOCKS):
        pair_inputs, reset = _challenge_inputs(block), _state_for(block, 0)
        pair, receipt = _pair(parent, world, coefficients, reset, pair_inputs, _seed(world, replicate, "adverse", block))
        contrasts.extend([pair[1] - pair[0]] * TWINS)
        receipts.append(receipt)
    values = np.array(contrasts).reshape(BLOCKS, TWINS, TIMES, NODES)
    if len(set(receipts)) != BLOCKS or not _identity(values):
        raise RuntimeError(f"{STOP}:adverse control")
    return {"identity": True, "common_by_block_sha256": receipts, "contrast_sha256": _array_hash(values)}


def _verify_cross_split(identity: dict[str, Any], records: list[dict[str, Any]]) -> None:
    hashes = identity.get("trajectory_sha256", {})
    train, validation = hashes.get("train"), hashes.get("validation")
    if not isinstance(train, list) or not isinstance(validation, list) or len(train) != 96 or len(validation) != 48:
        raise RuntimeError(f"{STOP}:split receipt")
    split = set(train) | set(validation)
    arms = {value for row in records for value in row["arm_sha256"]}
    if len(split) != 144 or split & arms:
        raise RuntimeError(f"{STOP}:split arm overlap")


def _verify_main_reset_receipts(records: list[dict[str, Any]]) -> None:
    for record in records:
        block, twin = record.get("block"), record.get("twin")
        if type(block) is not int or type(twin) is not int or not 0 <= block < BLOCKS or not 0 <= twin < TWINS:
            raise RuntimeError(f"{STOP}:reset receipt identity")
        state = _state_for(block, twin)
        expected_state = _array_hash(state)
        expected_arms = [_array_hash(np.vstack((state, state))), _array_hash(np.vstack((state, state)))]
        if record.get("reset_sha256") != expected_state or record.get("arm_reset_sha256") != expected_arms:
            raise RuntimeError(f"{STOP}:reset receipt")


def _verify_row(row: dict[str, Any]) -> None:
    world, replicate = row.get("world"), row.get("replicate")
    if world not in WORLDS or type(replicate) is not int or not 0 <= replicate < REPLICATES:
        raise RuntimeError(f"{STOP}:row identity")
    identity, selection, receipts = row.get("identity"), row.get("selection"), row.get("receipts")
    if not isinstance(identity, dict) or identity.get("world") != world or identity.get("replicate") != replicate or not isinstance(selection, dict) or not isinstance(receipts, dict):
        raise RuntimeError(f"{STOP}:row receipt")
    digest = _sha(_selection_body(selection))
    if digest != row.get("selection_serialization_sha256") or digest != receipts.get("descriptor_serialization_sha256"):
        raise RuntimeError(f"{STOP}:selection receipt")
    winner, candidates = selection.get("winner"), selection.get("candidates")
    if not isinstance(winner, dict) or not isinstance(candidates, dict) or winner.get("kind") not in candidates or winner.get("model_sha256") != candidates[winner["kind"]].get("model_sha256"):
        raise RuntimeError(f"{STOP}:winner receipt")
    records = receipts.get("twins")
    if not isinstance(records, list) or not receipts.get("confirmation_sha256"):
        raise RuntimeError(f"{STOP}:confirmation receipt")
    _verify_receipts(records, unique_common=True)
    _verify_cross_split(identity, records)
    _verify_assignment_receipt(identity.get("assignment"))
    _verify_main_reset_receipts(records)
    if not row.get("adverse", {}).get("identity"):
        raise RuntimeError(f"{STOP}:adverse receipt")
    adverse_receipts = row["adverse"].get("common_by_block_sha256")
    if not isinstance(adverse_receipts, list) or len(adverse_receipts) != BLOCKS or len(set(adverse_receipts)) != BLOCKS:
        raise RuntimeError(f"{STOP}:adverse common receipt")


def _run_replicate(run_root: Path, parent: Any, world: str, replicate: int) -> dict[str, Any]:
    splits, identity = _fresh_splits(parent, world, replicate)
    selection = parent.select_model(splits["train"], splits["validation"])
    serialized, serialization_sha = _serialized_selection(parent, selection)
    coefficients = parent._coefficients(world, np.random.default_rng(_seed(world, replicate, "coefficients")))
    states, inputs, receipts = _generate_main(parent, world, replicate, coefficients, serialization_sha)
    _verify_cross_split(identity, receipts["twins"])
    return {"world": world, "replicate": replicate, "identity": identity, "selection": serialized,
            "selection_serialization_sha256": serialization_sha, "receipts": receipts,
            "scores": _score(parent, selection["winner"], states, inputs, world, replicate),
            "adverse": _adverse_control(parent, world, replicate, coefficients)}


def aggregate(rows: list[dict[str, Any]]) -> dict[str, Any]:
    _verify_root_seed()
    population = {(world, replicate) for world in WORLDS for replicate in range(REPLICATES)}
    if len(rows) != len(population) or {(row.get("world"), row.get("replicate")) for row in rows} != population:
        raise RuntimeError(f"{STOP}:population")
    for row in rows:
        _verify_row(row)
    worlds, full, structural, history = {}, True, True, True
    for world in WORLDS:
        group = [row for row in rows if row["world"] == world]
        wins = sum(row["selection"]["winner"]["kind"] == EXPECTED[world] for row in group)
        median = float(np.median([row["scores"]["winner_twin_nrmse"] for row in group]))
        gates = {"winner_frequency": wins >= 10, "nrmse": median <= .50,
                 "equal_arm": all(row["scores"]["equal_arm_advantage"] == 0 and row["scores"]["equal_arm_p_value"] == 1 for row in group),
                 "adverse": all(row["adverse"]["identity"] for row in group)}
        if world in {"D", "E"}:
            gates["pairing_or_identity"] = (all(row["scores"]["identifiable_or_linear_identity"] for row in group)
                                             and sum(row["scores"]["permutation_p_value"] <= .01 for row in group) >= 10)
        else:
            gates["pairing_or_identity"] = all(row["scores"]["identifiable_or_linear_identity"] for row in group)
        gates["finite"] = all(all(math.isfinite(float(value)) for value in row["scores"].values()
                                   if isinstance(value, (int, float))) for row in group)
        passed = all(gates.values()); full &= passed
        if world in "ABCDE": structural &= passed
        else: history &= passed
        worlds[world] = {"expected": EXPECTED[world], "expected_wins": wins, "median_winner_twin_nrmse": median, "gates": gates, "pass": passed}
    status = "STATE_RESET_STAGE0_PASS" if full else ("STATE_RESET_STRUCTURE_STOP" if not structural else "STATE_RESET_HISTORY_STOP")
    return {"status": status, "worlds": worlds, "stage1_authorized": full, "real_brain_geometry_claim": False}


def _atomic_json(path: Path, payload: dict[str, Any]) -> str:
    body = (json.dumps(payload, indent=2, sort_keys=True) + "\n").encode(); temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_bytes(body); temporary.replace(path); return _sha(body)


def seal(run_root: Path, *, pivot: Path | None = None) -> dict[str, Any]:
    _verify_root_seed(); _verify_parent_source(_parent_path(run_root)); pivot = _pivot_path() if pivot is None else pivot
    files = {}
    for relative in PREREG_FILES:
        path = pivot / relative
        if not path.is_file(): raise RuntimeError(f"{STOP}:missing prereg:{relative}")
        files[relative] = _sha(path.read_bytes())
    payload = {"schema": 1, "root_seed": ROOT_SEED, "root_seed_sha256": ROOT_DIGEST, "parent_source_sha256": PARENT_SHA256,
               "worlds": list(WORLDS), "replicates_per_world": REPLICATES, "files": files, "outcome_opened": False}
    return {"manifest_sha256": _atomic_json(pivot / MANIFEST_NAME, payload), **payload}


def verify_manifest(run_root: Path, *, pivot: Path | None = None) -> tuple[dict[str, Any], str]:
    _verify_root_seed(); _verify_parent_source(_parent_path(run_root)); pivot = _pivot_path() if pivot is None else pivot; path = pivot / MANIFEST_NAME
    if not path.is_file(): raise RuntimeError(f"{STOP}:missing manifest")
    body = path.read_bytes(); payload = json.loads(body)
    if (payload.get("outcome_opened") is not False or payload.get("root_seed") != ROOT_SEED or payload.get("root_seed_sha256") != ROOT_DIGEST
            or payload.get("parent_source_sha256") != PARENT_SHA256 or set(payload.get("files", {})) != set(PREREG_FILES)):
        raise RuntimeError(f"{STOP}:manifest identity")
    for relative, digest in payload["files"].items():
        if _sha((pivot / relative).read_bytes()) != digest: raise RuntimeError(f"{STOP}:manifest mismatch:{relative}")
    return payload, _sha(body)


def execute(run_root: Path, *, pivot: Path | None = None) -> dict[str, Any]:
    pivot = _pivot_path() if pivot is None else pivot; _, manifest_sha = verify_manifest(run_root, pivot=pivot); parent = _parent(run_root)
    rows = [_run_replicate(run_root, parent, world, replicate) for world in WORLDS for replicate in range(REPLICATES)]
    payload = {"schema": 1, "manifest_sha256": manifest_sha, "parent_source_sha256": PARENT_SHA256, "result": aggregate(rows), "replicates": rows, "persistent_raw_bytes": 0}
    digest = _atomic_json(pivot / RESULT_NAME, payload); print(json.dumps({"receipt_sha256": digest, **payload["result"]}, sort_keys=True), flush=True); return payload


def main() -> None:
    parser = argparse.ArgumentParser(); parser.add_argument("--seal", action="store_true"); args = parser.parse_args(); run_root = _run_root()
    if args.seal: print(json.dumps(seal(run_root), sort_keys=True), flush=True)
    else: execute(run_root)


if __name__ == "__main__":
    main()
