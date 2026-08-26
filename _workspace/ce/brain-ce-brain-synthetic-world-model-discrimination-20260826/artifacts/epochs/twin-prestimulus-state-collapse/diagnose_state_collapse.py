"""Post-outcome exploratory diagnostic for the frozen twin-confirmation STOP."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any

import numpy as np


HERE = Path(__file__).resolve().parent
RUN = HERE.parents[2]
PIVOT = RUN / "artifacts" / "epochs" / "world-e-permutation-marginal-calibration" / "pivots" / "matched-intervention-twins"
TWIN_SOURCE = PIVOT / "twin_confirmation.py"
TWIN_SHA256 = "6900a26eeedda1c1294b4c692819a0fb86bdbaa22e0f9dc13b674f7646902f73"
RESULT = PIVOT / "twin-confirmation-result.json"
RESULT_SHA256 = "645a117c1441f8d666b1bba8aded0ffef42b556ac9e471bd5bb222c98a1f7048"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path: Path, name: str) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError("STATE_COLLAPSE_DIAGNOSTIC_STOP:import")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def between_twin_rms(states: np.ndarray, time: int) -> float:
    values = states[:, :, time]
    return float(np.sqrt(np.mean((values - values.mean(axis=1, keepdims=True)) ** 2)))


def diagnose_world(twin: Any, parent: Any, result_rows: list[dict[str, Any]], world: str) -> dict[str, Any]:
    rows = []
    for replicate in range(twin.REPLICATES):
        coefficients = parent._coefficients(world, np.random.default_rng(twin._seed(world, replicate, "coefficients")))
        actual = np.empty((twin.BLOCKS, twin.TWINS, 2, twin.TIMES, twin.NODES), dtype=np.float64)
        for block in range(twin.BLOCKS):
            pair_inputs = twin._pulse_inputs(block)
            for twin_index in range(twin.TWINS):
                states, _ = twin._simulate_pair(
                    parent, world, coefficients, pair_inputs,
                    twin._seed(world, replicate, "twin", block, twin_index),
                )
                actual[block, twin_index] = states
        baseline = actual[:, :, 0]
        contrast = actual[:, :, 1] - actual[:, :, 0]
        initial_rms = between_twin_rms(baseline, 1)
        residual = contrast - contrast.mean(axis=1, keepdims=True)
        contrast_rms = float(np.sqrt(np.mean(contrast[:, :, 2:] ** 2)))
        residual_rms = float(np.sqrt(np.mean(residual[:, :, 2:] ** 2)))
        result_row = next(row for row in result_rows if row["world"] == world and row["replicate"] == replicate)
        rows.append({
            "replicate": replicate,
            "between_twin_rms": {str(time): between_twin_rms(baseline, time) for time in (1, 5, 11, 12, 30)},
            "pre_pulse_retention_t12_over_t1": between_twin_rms(baseline, 12) / initial_rms,
            "contrast_rms": contrast_rms,
            "within_block_contrast_residual_rms": residual_rms,
            "contrast_pair_specific_fraction": residual_rms / contrast_rms,
            "permutation_p_value": result_row["scores"]["permutation_p_value"],
            "pairing_advantage": result_row["scores"]["pairing_advantage"],
        })
    return {
        "replicates": rows,
        "median_pre_pulse_retention": float(np.median([row["pre_pulse_retention_t12_over_t1"] for row in rows])),
        "median_pair_specific_fraction": float(np.median([row["contrast_pair_specific_fraction"] for row in rows])),
        "significant_pairing_replicates": sum(row["permutation_p_value"] <= 0.01 for row in rows),
    }


def main() -> None:
    if sha(TWIN_SOURCE) != TWIN_SHA256 or sha(RESULT) != RESULT_SHA256:
        raise RuntimeError("STATE_COLLAPSE_DIAGNOSTIC_STOP:frozen input hash")
    twin = load(TWIN_SOURCE, "sealed_twin_confirmation")
    parent = twin._parent(RUN)
    result = json.loads(RESULT.read_text(encoding="utf-8"))
    payload = {
        "schema": 1,
        "status": "POST_OUTCOME_EXPLORATORY",
        "twin_source_sha256": TWIN_SHA256,
        "result_sha256": RESULT_SHA256,
        "worlds": {world: diagnose_world(twin, parent, result["replicates"], world) for world in ("D", "E")},
    }
    body = (json.dumps(payload, indent=2, sort_keys=True) + "\n").encode()
    output = HERE / "state-collapse-diagnostic.json"
    temporary = output.with_suffix(".json.tmp")
    temporary.write_bytes(body)
    temporary.replace(output)
    print(json.dumps({
        "receipt_sha256": hashlib.sha256(body).hexdigest(),
        "D": {key: payload["worlds"]["D"][key] for key in ("median_pre_pulse_retention", "median_pair_specific_fraction", "significant_pairing_replicates")},
        "E": {key: payload["worlds"]["E"][key] for key in ("median_pre_pulse_retention", "median_pair_specific_fraction", "significant_pairing_replicates")},
    }, sort_keys=True))


if __name__ == "__main__":
    main()
