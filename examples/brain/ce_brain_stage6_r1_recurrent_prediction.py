"""Sealed Stage 6 R1 development test of recurrent predictive modes."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import sys
from pathlib import Path
from typing import Any

import h5py
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
CONTRACT = ROOT / "paper" / "검증_원장" / "CE_BRAIN_STAGE6_R1_순환예측_계약.md"
TEST_FILE = ROOT / "tests" / "test_ce_brain_stage6_r1_recurrent_prediction.py"
SCHEMA_CODE = ROOT / "examples" / "brain" / "ce_brain_stage6_allen_schema.py"
SCHEMA_RECEIPT = ROOT / "artifacts" / "brain" / "ce_brain_stage6_allen_apparatus" / "schema-receipt-721123822.json"
DEFAULT_NWB = ROOT / "data" / "external" / "ce_brain_stage6_allen_dev" / "sub-707296975_ses-721123822.nwb"
ARTIFACT = ROOT / "artifacts" / "brain" / "ce_brain_stage6_r1_recurrent_prediction"
EXPECTED_NWB_SHA256 = "4e284295a1be5c6cca49df84fab52ad38b4749d2361b2edebeb676051cf09921"
SEED = 20_260_908
BOOTSTRAPS = 1_999
RANKS = (4, 8, 16, 32)
RIDGES = (1e-3, 1e-2, 1e-1, 1.0)
MANIFEST = "manifest.json"
RESULT = "result.json"
VALIDATION = "validation-receipt.json"
STOP = "STAGE6_R1_APPARATUS_STOP"


def canonical_bytes(value: Any) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n").encode()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        while block := source.read(8 * 1024 * 1024):
            digest.update(block)
    return digest.hexdigest()


def write_once(path: Path, value: Any) -> str:
    if path.exists():
        raise RuntimeError(f"{STOP}: refusing overwrite {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = canonical_bytes(value)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    temporary.write_bytes(payload)
    temporary.replace(path)
    return hashlib.sha256(payload).hexdigest()


def as_text(values: np.ndarray) -> list[str]:
    return [x.decode() if hasattr(x, "decode") else str(x) for x in values]


def eligible_unit_indices(nwb: h5py.File) -> np.ndarray:
    electrode_ids = np.asarray(nwb["/general/extracellular_ephys/electrodes/id"])
    locations = as_text(nwb["/general/extracellular_ephys/electrodes/location"][()])
    location_for = dict(zip(electrode_ids.tolist(), locations))
    peaks = np.asarray(nwb["/units/peak_channel_id"])
    quality = as_text(nwb["/units/quality"][()])
    presence = np.asarray(nwb["/units/presence_ratio"])
    amplitude = np.asarray(nwb["/units/amplitude_cutoff"])
    isi = np.asarray(nwb["/units/isi_violations"])
    rate = np.asarray(nwb["/units/firing_rate"])
    unit_ids = np.asarray(nwb["/units/id"])
    keep = [
        i for i in range(len(unit_ids))
        if location_for.get(int(peaks[i]), "").startswith("VIS")
        and quality[i].lower() == "good"
        and np.isfinite(presence[i]) and presence[i] >= 0.95
        and np.isfinite(amplitude[i]) and amplitude[i] <= 0.1
        and np.isfinite(isi[i]) and isi[i] <= 0.5
        and np.isfinite(rate[i]) and rate[i] >= 0.1
    ]
    keep.sort(key=lambda i: int(unit_ids[i]))
    if len(keep) < 128:
        raise RuntimeError(f"{STOP}: only {len(keep)} eligible units")
    return np.asarray(keep[:256], dtype=int)


def repeat_slices(frames: np.ndarray, blocks: np.ndarray) -> tuple[list[slice], list[int]]:
    resets = np.flatnonzero(np.r_[True, frames[1:] <= frames[:-1]])
    ends = np.r_[resets[1:], len(frames)]
    slices = [slice(int(start), int(end)) for start, end in zip(resets, ends)]
    if any(s.stop - s.start != 900 for s in slices):
        raise RuntimeError(f"{STOP}: incomplete movie repeat")
    repeat_blocks = []
    for section in slices:
        values = np.unique(blocks[section])
        if len(values) != 1:
            raise RuntimeError(f"{STOP}: repeat crosses block")
        repeat_blocks.append(int(values[0]))
    return slices, repeat_blocks


def load_counts(nwb_path: Path) -> tuple[np.ndarray, dict[str, Any]]:
    with h5py.File(nwb_path, "r") as nwb:
        base = "/intervals/natural_movie_one_presentations"
        frames = np.asarray(nwb[f"{base}/frame"])
        starts = np.asarray(nwb[f"{base}/start_time"])
        stops = np.asarray(nwb[f"{base}/stop_time"])
        blocks = np.asarray(nwb[f"{base}/stimulus_block"])
        slices, repeat_blocks = repeat_slices(frames, blocks)
        first, second = sorted(np.unique(repeat_blocks).tolist())
        first_repeats = [i for i, value in enumerate(repeat_blocks) if value == first]
        second_repeats = [i for i, value in enumerate(repeat_blocks) if value == second]
        if len(first_repeats) != 10 or len(second_repeats) != 10:
            raise RuntimeError(f"{STOP}: expected 10+10 repeats")
        selected = eligible_unit_indices(nwb)
        unit_ids = np.asarray(nwb["/units/id"])[selected]
        ends = np.asarray(nwb["/units/spike_times_index"])
        spikes = nwb["/units/spike_times"]
        counts = np.empty((len(slices), 900, len(selected)), dtype=np.float32)
        for column, unit_index in enumerate(selected):
            lo = 0 if unit_index == 0 else int(ends[unit_index - 1])
            hi = int(ends[unit_index])
            unit_spikes = np.asarray(spikes[lo:hi])
            flat = np.searchsorted(unit_spikes, stops, side="left") - np.searchsorted(unit_spikes, starts, side="left")
            for repeat, section in enumerate(slices):
                counts[repeat, :, column] = flat[section]
        metadata = {
            "eligible_unit_count_used": int(len(selected)),
            "first_unit_id": int(unit_ids[0]),
            "last_unit_id": int(unit_ids[-1]),
            "train_repeats": first_repeats[:8],
            "validation_repeats": first_repeats[8:],
            "test_repeats": second_repeats,
            "stimulus_blocks": [first, second],
        }
        return counts, metadata


def pairs(z: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    return z[:, :-1, :].reshape(-1, z.shape[-1]), z[:, 1:, :].reshape(-1, z.shape[-1])


def fit_full(x: np.ndarray, y: np.ndarray, ridge: float) -> np.ndarray:
    return np.linalg.solve(x.T @ x + ridge * np.eye(x.shape[1]), x.T @ y)


def fit_diagonal(x: np.ndarray, y: np.ndarray, ridge: float) -> np.ndarray:
    values = np.sum(x * y, axis=0) / (np.sum(x * x, axis=0) + ridge)
    return np.diag(values)


def destroy_modes(matrix: np.ndarray) -> np.ndarray:
    u, singular, vt = np.linalg.svd(matrix, full_matrices=False)
    count = max(1, matrix.shape[0] // 4)
    singular[:count] = 0.0
    return (u * singular) @ vt


def shuffled_modes(matrix: np.ndarray) -> np.ndarray:
    rng = np.random.Generator(np.random.PCG64(SEED))
    rows = rng.permutation(matrix.shape[0])
    columns = rng.permutation(matrix.shape[1])
    return matrix[rows][:, columns]


def repeat_losses(data: np.ndarray, mean: np.ndarray, components: np.ndarray, matrix: np.ndarray | None) -> list[float]:
    losses = []
    for repeat in data:
        target = repeat[1:]
        if matrix is None:
            prediction = mean[1:]
        else:
            current = (repeat[:-1] - mean[:-1]) @ components.T
            prediction = mean[1:] + (current @ matrix) @ components
        losses.append(float(np.mean((target - prediction) ** 2)))
    return losses


def improvement(losses: dict[str, list[float]], better: str, baseline: str, offset: int) -> dict[str, float]:
    a = np.asarray(losses[better])
    b = np.asarray(losses[baseline])
    point = float((b.mean() - a.mean()) / b.mean())
    rng = np.random.Generator(np.random.PCG64(SEED + offset))
    values = np.empty(BOOTSTRAPS)
    for i in range(BOOTSTRAPS):
        index = rng.integers(0, len(a), len(a))
        values[i] = (b[index].mean() - a[index].mean()) / b[index].mean()
    return {"improvement": point, "lower_95": float(np.quantile(values, 0.025)), "median": float(np.median(values))}


def decide(comparisons: dict[str, dict[str, float]]) -> str:
    rn, rd, rm = comparisons["R_vs_N"], comparisons["R_vs_D"], comparisons["R_vs_M"]
    if rn["improvement"] >= 0.01 and rn["lower_95"] > 0 and rd["improvement"] >= 0.005 and rd["lower_95"] > 0 and rm["improvement"] >= 0.005 and rm["lower_95"] > 0:
        return "DEVELOPMENT_RECURRENT_PREDICTIVE_MODES_SUPPORTED"
    if rn["improvement"] >= 0.01 and rn["lower_95"] > 0:
        return "HISTORY_USEFUL_RECURRENCE_NOT_ISOLATED"
    return "RECURRENT_PREDICTIVE_DIMENSION_NOT_ESTABLISHED"


def analyze(nwb_path: Path) -> dict[str, Any]:
    counts, metadata = load_counts(nwb_path)
    transformed = np.sqrt(counts + 0.375)
    train = transformed[metadata["train_repeats"]]
    validation = transformed[metadata["validation_repeats"]]
    test = transformed[metadata["test_repeats"]]
    mean = train.mean(axis=0)
    flat = (train - mean).reshape(-1, train.shape[-1])
    _, singular, vt = np.linalg.svd(flat, full_matrices=False)
    validation_grid = []
    fitted: dict[tuple[int, float], tuple[np.ndarray, np.ndarray]] = {}
    for rank in RANKS:
        components = vt[:rank]
        ztrain = (train - mean) @ components.T
        x, y = pairs(ztrain)
        for ridge in RIDGES:
            matrix = fit_full(x, y, ridge)
            fitted[(rank, ridge)] = (components, matrix)
            loss = float(np.mean(repeat_losses(validation, mean, components, matrix)))
            validation_grid.append({"rank": rank, "ridge": ridge, "loss": loss})
    best = min(validation_grid, key=lambda row: (row["loss"], row["rank"], row["ridge"]))
    rank, ridge = int(best["rank"]), float(best["ridge"])
    components, recurrent = fitted[(rank, ridge)]
    ztrain = (train - mean) @ components.T
    x, y = pairs(ztrain)
    diagonal = fit_diagonal(x, y, ridge)
    destroyed = destroy_modes(recurrent)
    shuffled = shuffled_modes(recurrent)
    losses = {
        "N": repeat_losses(test, mean, components, None),
        "D": repeat_losses(test, mean, components, diagonal),
        "R": repeat_losses(test, mean, components, recurrent),
        "M": repeat_losses(test, mean, components, destroyed),
        "P": repeat_losses(test, mean, components, shuffled),
    }
    comparisons = {
        "R_vs_N": improvement(losses, "R", "N", 1),
        "R_vs_D": improvement(losses, "R", "D", 2),
        "R_vs_M": improvement(losses, "R", "M", 3),
        "R_vs_P": improvement(losses, "R", "P", 4),
    }
    mean_losses = {name: float(np.mean(values)) for name, values in losses.items()}
    total_variance = float(np.sum(singular**2))
    result = {
        "claim_ceiling": "single development subject; observational computational ablation",
        "coverage": metadata,
        "selected_rank": rank,
        "selected_ridge": ridge,
        "pca_variance_fraction": float(np.sum(singular[:rank] ** 2) / total_variance),
        "losses": mean_losses,
        "repeat_losses": losses,
        "comparisons": comparisons,
        "bootstrap": {"repetitions": BOOTSTRAPS, "seed": SEED},
        "confirmation_endpoint_opened": False,
        "dandi_001695_opened": False,
    }
    result["decision"] = decide(comparisons)
    return result


def source_files() -> tuple[Path, ...]:
    return (Path(__file__).resolve(), TEST_FILE, CONTRACT, SCHEMA_CODE, SCHEMA_RECEIPT)


def runtime() -> dict[str, str]:
    return {
        "executable": sys.executable,
        "python": platform.python_version(),
        "numpy": np.__version__,
        "h5py": h5py.__version__,
    }


def seal(nwb_path: Path, artifact_dir: Path) -> dict[str, Any]:
    if sha256(nwb_path) != EXPECTED_NWB_SHA256:
        raise RuntimeError(f"{STOP}: NWB hash")
    manifest = {
        "files": {str(path.relative_to(ROOT)).replace("\\", "/"): sha256(path) for path in source_files()},
        "nwb_sha256": EXPECTED_NWB_SHA256,
        "runtime": runtime(),
        "scores_opened": False,
        "confirmation_endpoint_opened": False,
        "dandi_001695_opened": False,
    }
    manifest["manifest_sha256"] = write_once(artifact_dir / MANIFEST, manifest)
    return manifest


def verify_manifest(nwb_path: Path, artifact_dir: Path) -> str:
    path = artifact_dir / MANIFEST
    manifest = json.loads(path.read_text(encoding="utf-8"))
    expected_files = {str(item.relative_to(ROOT)).replace("\\", "/"): sha256(item) for item in source_files()}
    if manifest.get("files") != expected_files or manifest.get("nwb_sha256") != sha256(nwb_path) or manifest.get("runtime") != runtime() or manifest.get("scores_opened") is not False:
        raise RuntimeError(f"{STOP}: manifest mutation")
    return sha256(path)


def execute(nwb_path: Path, artifact_dir: Path) -> dict[str, Any]:
    manifest_hash = verify_manifest(nwb_path, artifact_dir)
    result = analyze(nwb_path)
    result["manifest_sha256"] = manifest_hash
    result_hash = write_once(artifact_dir / RESULT, result)
    return {"result_sha256": result_hash, **result}


def verify_result(nwb_path: Path, artifact_dir: Path) -> dict[str, Any]:
    stored_path = artifact_dir / RESULT
    stored = json.loads(stored_path.read_text(encoding="utf-8"))
    fresh = analyze(nwb_path)
    fresh["manifest_sha256"] = verify_manifest(nwb_path, artifact_dir)
    if canonical_bytes(stored) != canonical_bytes(fresh):
        raise RuntimeError(f"{STOP}: raw recomputation mismatch")
    receipt = {"status": "PASS", "raw_recomputed": True, "decision": stored["decision"], "result_sha256": sha256(stored_path)}
    receipt["validation_receipt_sha256"] = write_once(artifact_dir / VALIDATION, receipt)
    return receipt


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--nwb", type=Path, default=DEFAULT_NWB)
    parser.add_argument("--artifact-dir", type=Path, default=ARTIFACT)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--seal", action="store_true")
    group.add_argument("--execute", action="store_true")
    group.add_argument("--verify-result", action="store_true")
    args = parser.parse_args()
    if args.seal:
        output = seal(args.nwb, args.artifact_dir)
    elif args.execute:
        output = execute(args.nwb, args.artifact_dir)
    else:
        output = verify_result(args.nwb, args.artifact_dir)
    print(json.dumps(output, sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()
