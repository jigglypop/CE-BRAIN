"""Preregistered CE-BRAIN Phase 2D model competition on subject 569070."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
from typing import Any

import h5py
import numpy as np
from scipy.signal import butter, sosfiltfilt


STOP = "PHASE2D_APPARATUS_STOP"
FS = 2_500.0
CURRENTS = (20, 40, 60)
CHANNELS = (0, 1, 5, 20, 22, 23, 24, 25, 26, 27, 28, 29)
STATES = ("awake", "isoflurane")
BOOTSTRAPS = 1_999
BOOTSTRAP_SEED = 20_260_903
PERMUTATIONS = 999
PERMUTATION_SEED = 20_261_903
SCHEMA_RECEIPT = "phase2d-schema-receipt.json"
MANIFEST = "phase2d-manifest.json"
RESULT = "phase2d-result.json"
VALIDATION = "phase2d-validation-receipt.json"

ROOT = Path(__file__).resolve().parents[2]
CONTRACT = ROOT / "paper" / "검증_원장" / "CE_BRAIN_PHASE2D_개체축_연산자_계약.md"
TEST_FILE = ROOT / "tests" / "test_ce_brain_phase2d_model_competition.py"

SPECS: dict[str, dict[str, Any]] = {
    "521885": {
        "bytes": 312_139_546, "sha256": "b80cd3a375ead36c05c451f562e92947573cd0679a30ffd573a04e44339b0171",
        "shape": (6_217_728, 30), "trial_count": 360,
        "valid_columns": (0, 1, 2, 3, 4, 5, 9, 19, 20, 22, 23, 24, 25, 26, 27, 28, 29),
        "gaps": (125_307,), "max_jitter": 2e-5,
        "segments": {"awake": (125_308, 6_217_728), "isoflurane": (125_308, 6_217_728)},
        "currents": (20,),
        "counts": {"awake/20/development": 30, "awake/20/confirmation": 30,
                   "isoflurane/20/development": 30, "isoflurane/20/confirmation": 30},
    },
    "521886": {
        "bytes": 504_307_581, "sha256": "a799afdf771a5f629e19312d37714b0990418cef0d2b7425b46e17574678fcb6",
        "shape": (10_564_096, 30), "trial_count": 900,
        "valid_columns": (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29),
        "gaps": (151_674,), "max_jitter": 3e-5,
        "segments": {"awake": (151_675, 10_564_096), "isoflurane": (151_675, 10_564_096)},
        "currents": (20,),
        "counts": {"awake/20/development": 53, "awake/20/confirmation": 46,
                   "isoflurane/20/development": 54, "isoflurane/20/confirmation": 46},
    },
    "521887": {
        "bytes": 428_192_135, "sha256": "716e5372de827ab0a72fae5036045527f5e884bcc5a48215bba278fbb516521e",
        "shape": (9_261_311, 30), "trial_count": 800,
        "valid_columns": (0, 1, 2, 3, 5, 6, 8, 10, 16, 17, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29),
        "gaps": (97_470, 2_354_430), "max_jitter": 3e-5,
        "segments": {"awake": (97_471, 2_354_431), "isoflurane": (2_354_431, 9_261_311)},
        "currents": (20,),
        "counts": {"awake/20/development": 95, "awake/20/confirmation": 95,
                   "isoflurane/20/development": 150, "isoflurane/20/confirmation": 150},
    },
    "569070": {
        "bytes": 1_124_308_400, "sha256": "c985835d707fa688de39968b3f2645150a7d67818ae7c81a9bd8c746d4c5202b",
        "shape": (22_065_920, 30), "trial_count": 1_440,
        "valid_columns": (0, 1, 5, 6, 7, 8, 9, 10, 11, 12, 14, 15, 16, 17, 18, 19,
                          20, 21, 22, 23, 24, 25, 26, 27, 28, 29),
        "gaps": (), "max_jitter": 3e-5,
        "segments": {"awake": (0, 22_065_920), "isoflurane": (0, 22_065_920)},
        "currents": CURRENTS,
        "counts": {
            "awake/20/development": 52, "awake/20/confirmation": 60,
            "awake/40/development": 54, "awake/40/confirmation": 58,
            "awake/60/development": 63, "awake/60/confirmation": 46,
            "isoflurane/20/development": 57, "isoflurane/20/confirmation": 63,
            "isoflurane/40/development": 56, "isoflurane/40/confirmation": 64,
            "isoflurane/60/development": 67, "isoflurane/60/confirmation": 53,
        },
    },
}


def canonical_json_bytes(value: Any) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n").encode()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while chunk := stream.read(8 * 1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def write_json_once(path: Path, value: Any) -> str:
    if path.exists():
        raise RuntimeError(f"{STOP}: refusing to overwrite {path.name}")
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = canonical_json_bytes(value)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    temporary.write_bytes(payload)
    temporary.replace(path)
    return hashlib.sha256(payload).hexdigest()


def raw_identity(path: Path, subject: str) -> dict[str, Any]:
    spec = SPECS[subject]
    if not path.is_file() or path.stat().st_size != spec["bytes"] or sha256_file(path) != spec["sha256"]:
        raise RuntimeError(f"{STOP}: {subject} raw identity")
    return {"subject": subject, "filename": path.name, "bytes": path.stat().st_size,
            "sha256": spec["sha256"]}


def decode(values: np.ndarray) -> np.ndarray:
    return np.asarray([x.decode() if isinstance(x, bytes) else str(x) for x in values])


def nearest_origins(timestamps: np.ndarray, starts: np.ndarray) -> np.ndarray:
    right = np.clip(np.searchsorted(timestamps, starts, side="left"), 1, len(timestamps) - 1)
    left = right - 1
    dr, dl = np.abs(timestamps[right] - starts), np.abs(timestamps[left] - starts)
    if np.any(np.isclose(dr, dl, rtol=0, atol=1e-12)):
        raise RuntimeError(f"{STOP}: timestamp tie")
    origins = np.where(dr < dl, right, left)
    if np.any(np.abs(timestamps[origins] - starts) > 0.5 / FS):
        raise RuntimeError(f"{STOP}: timestamp alignment")
    return origins.astype(np.int64)


def read_schema(nwb: h5py.File, subject: str, *, endpoint_opened: bool) -> dict[str, Any]:
    spec = SPECS[subject]
    data = nwb["/acquisition/ElectricalSeriesEEG/data"]
    timestamps = np.asarray(nwb["/acquisition/ElectricalSeriesEEG/timestamps"][...], dtype=np.float64)
    if data.shape != spec["shape"] or data.dtype != np.dtype("int16"):
        raise RuntimeError(f"{STOP}: {subject} EEG shape/dtype")
    conversion = float(data.attrs.get("conversion", np.nan))
    if conversion != 1.9499999284744263e-07:
        raise RuntimeError(f"{STOP}: {subject} conversion")
    deltas, median = np.diff(timestamps), float(np.median(np.diff(timestamps)))
    gaps = tuple(np.flatnonzero(deltas > 1.5 * median).tolist())
    ordinary = np.delete(deltas, spec["gaps"])
    if (timestamps.shape != (spec["shape"][0],) or np.any(deltas <= 0)
            or abs(1 / median - FS) > .02 or gaps != spec["gaps"]
            or float(np.max(np.abs(ordinary / median - 1))) > spec["max_jitter"]):
        raise RuntimeError(f"{STOP}: {subject} timestamp profile")
    region = np.asarray(nwb["/acquisition/ElectricalSeriesEEG/electrodes"][...], dtype=np.int64)
    valid = np.asarray(nwb["/general/extracellular_ephys/electrodes/is_data_valid"][...], dtype=bool)
    valid_columns = tuple(np.flatnonzero(valid[region]).tolist())
    if not np.array_equal(region, np.arange(30)) or valid_columns != spec["valid_columns"]:
        raise RuntimeError(f"{STOP}: {subject} electrodes")
    trials = nwb["/intervals/trials"]
    ids = np.asarray(trials["id"][...], dtype=np.int64)
    starts = np.asarray(trials["start_time"][...], dtype=np.float64)
    states = decode(trials["behavioral_epoch"][...])
    currents = decode(trials["estim_current"][...]).astype(np.int64)
    targets = decode(trials["estim_target_region"][...])
    descriptions = decode(trials["stimulus_description"][...])
    valid_trials = np.asarray(trials["is_valid"][...], dtype=bool)
    if not all(len(x) == spec["trial_count"] for x in
               (ids, starts, states, currents, targets, descriptions, valid_trials)):
        raise RuntimeError(f"{STOP}: {subject} trial length")
    origins = nearest_origins(timestamps, starts)
    eligible = valid_trials & np.isin(states, STATES) & np.isin(currents, spec["currents"])
    eligible &= (targets == "MOs") & (descriptions == "biphasic")
    for index in np.flatnonzero(eligible):
        lo, hi = spec["segments"][states[index]]
        eligible[index] = origins[index] - 2_500 >= lo and origins[index] + 1_250 < hi
    counts = {}
    for state in STATES:
        for current in spec["currents"]:
            for name, parity in (("development", 0), ("confirmation", 1)):
                counts[f"{state}/{current}/{name}"] = int(np.sum(
                    eligible & (states == state) & (currents == current) & (ids % 2 == parity)))
    if counts != spec["counts"]:
        raise RuntimeError(f"{STOP}: {subject} split counts {counts}")
    return {"confirmation_values_opened": endpoint_opened, "conversion": conversion,
            "eeg_shape": list(data.shape), "eligible": eligible, "fs_hz": 1 / median,
            "origins": origins, "segments": spec["segments"], "split_counts": counts,
            "trial_ids": ids, "trial_starts": starts, "trial_states": states,
            "trial_currents": currents, "valid_channels": list(CHANNELS)}


def public_schema(schema: dict[str, Any]) -> dict[str, Any]:
    hidden = {"eligible", "origins", "trial_ids", "trial_starts", "trial_states", "trial_currents"}
    return {key: value for key, value in schema.items() if key not in hidden}


def replace_artifacts(signal: np.ndarray, origins: np.ndarray) -> None:
    for origin in origins:
        signal[origin:origin + 5] = signal[origin - 5:origin]


def extract_waveforms(nwb: h5py.File, schema: dict[str, Any]) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    rows = np.flatnonzero(schema["eligible"])
    origins, states = schema["origins"][rows], schema["trial_states"][rows]
    raw = np.empty((len(rows), 249, len(CHANNELS)), dtype=np.float64)
    baseline = np.empty((len(rows), len(CHANNELS)), dtype=np.float64)
    data = nwb["/acquisition/ElectricalSeriesEEG/data"]
    sos = butter(3, (.1, 100.), btype="bandpass", fs=FS, output="sos")
    for out_channel, source_channel in enumerate(CHANNELS):
        for lo, hi in sorted(set(tuple(x) for x in schema["segments"].values())):
            selection = np.flatnonzero([tuple(schema["segments"][s]) == (lo, hi) for s in states])
            if not len(selection):
                continue
            relative = origins[selection] - lo
            continuous = np.asarray(data[lo:hi, source_channel], dtype=np.float64)
            replace_artifacts(continuous, relative)
            continuous *= schema["conversion"] * 1e6
            continuous = sosfiltfilt(sos, continuous)
            for trial_index, origin in zip(selection, relative, strict=True):
                baseline[trial_index, out_channel] = np.mean(continuous[origin - 1_250:origin - 25])
                raw[trial_index, :, out_channel] = continuous[origin + 5:origin + 1_250:5]
    raw -= raw.mean(axis=2, keepdims=True)
    baseline -= baseline.mean(axis=1, keepdims=True)
    raw -= baseline[:, None, :]
    flat = raw.reshape(len(raw), -1)
    norms = np.linalg.norm(flat, axis=1)
    if flat.shape[1] != 2_988 or not np.all(np.isfinite(flat)) or np.any(norms <= 0):
        raise RuntimeError(f"{STOP}: waveform")
    return flat, flat / norms[:, None], rows


def cells(values: np.ndarray, rows: np.ndarray, schema: dict[str, Any], *, parity: int | None) -> dict[str, np.ndarray]:
    ids, states = schema["trial_ids"][rows], schema["trial_states"][rows]
    currents = schema["trial_currents"][rows]
    output = {}
    for state in STATES:
        for current in sorted(set(currents.tolist())):
            select = (states == state) & (currents == current)
            if parity is not None:
                select &= ids % 2 == parity
            output[f"{state}/{current}"] = values[select]
            if len(output[f"{state}/{current}"]) < 20:
                raise RuntimeError(f"{STOP}: group {state}/{current}/{parity}")
    return output


def contrasts(grouped: dict[str, np.ndarray], currents: tuple[int, ...]) -> np.ndarray:
    return np.stack([grouped[f"isoflurane/{u}"].mean(0) - grouped[f"awake/{u}"].mean(0)
                     for u in currents])


def rank_one_axis(matrix: np.ndarray) -> np.ndarray:
    _, singular, vh = np.linalg.svd(matrix, full_matrices=False)
    if singular[0] <= 0:
        raise RuntimeError(f"{STOP}: rank one")
    axis = vh[0]
    if float(axis @ matrix.sum(0)) < 0:
        axis = -axis
    return axis


def predictions(source: np.ndarray, development: np.ndarray) -> dict[str, np.ndarray]:
    vg, vi = rank_one_axis(source), rank_one_axis(development)
    return {"Z": np.zeros_like(development), "G": (development @ vg)[:, None] * vg,
            "I": (development @ vi)[:, None] * vi, "K": development.copy()}


def score(predicted: dict[str, np.ndarray], confirmation: np.ndarray) -> dict[str, float]:
    return {name: float(np.mean(np.sum((confirmation - value) ** 2, axis=1)))
            for name, value in predicted.items()}


def improvements(errors: dict[str, float]) -> dict[str, float]:
    pairs = {"G_vs_Z": ("G", "Z"), "I_vs_Z": ("I", "Z"), "K_vs_Z": ("K", "Z"),
             "I_vs_G": ("I", "G"), "K_vs_I": ("K", "I")}
    return {name: (errors[b] - errors[a]) / errors[b] for name, (a, b) in pairs.items()}


def _means(rng: np.random.Generator, values: np.ndarray, batch: int) -> np.ndarray:
    n = len(values)
    return (rng.multinomial(n, np.full(n, 1 / n), size=batch) / n) @ values


def _batch_axis(matrix: np.ndarray) -> np.ndarray:
    gram = matrix @ np.swapaxes(matrix, 1, 2)
    _, vectors = np.linalg.eigh(gram)
    coeff = vectors[:, :, -1]
    axis = np.sum(coeff[:, :, None] * matrix, axis=1)
    axis /= np.linalg.norm(axis, axis=1)[:, None]
    orientation = np.sign(np.sum(axis * matrix.sum(1), axis=1))
    orientation[orientation == 0] = 1
    return axis * orientation[:, None]


def bootstrap(source_cells: list[dict[str, np.ndarray]], target_dev: dict[str, np.ndarray],
              target_conf: dict[str, np.ndarray], *, repetitions: int = BOOTSTRAPS,
              seed: int = BOOTSTRAP_SEED, batch_size: int = 32) -> dict[str, np.ndarray]:
    rng = np.random.Generator(np.random.PCG64(seed))
    out = {name: [] for name in ("G_vs_Z", "I_vs_Z", "K_vs_Z", "I_vs_G", "K_vs_I")}
    done = 0
    while done < repetitions:
        b = min(batch_size, repetitions - done)
        source = np.stack([_means(rng, c["isoflurane/20"], b) - _means(rng, c["awake/20"], b)
                           for c in source_cells], axis=1)
        dev = np.stack([_means(rng, target_dev[f"isoflurane/{u}"], b)
                        - _means(rng, target_dev[f"awake/{u}"], b) for u in CURRENTS], axis=1)
        conf = np.stack([_means(rng, target_conf[f"isoflurane/{u}"], b)
                         - _means(rng, target_conf[f"awake/{u}"], b) for u in CURRENTS], axis=1)
        vg, vi = _batch_axis(source), _batch_axis(dev)
        pred = {"Z": np.zeros_like(dev), "G": np.sum(dev * vg[:, None, :], axis=2)[:, :, None] * vg[:, None, :],
                "I": np.sum(dev * vi[:, None, :], axis=2)[:, :, None] * vi[:, None, :], "K": dev}
        errors = {name: np.mean(np.sum((conf - value) ** 2, axis=2), axis=1)
                  for name, value in pred.items()}
        for name, values in (("G_vs_Z", (errors["Z"] - errors["G"]) / errors["Z"]),
                             ("I_vs_Z", (errors["Z"] - errors["I"]) / errors["Z"]),
                             ("K_vs_Z", (errors["Z"] - errors["K"]) / errors["Z"]),
                             ("I_vs_G", (errors["G"] - errors["I"]) / errors["G"]),
                             ("K_vs_I", (errors["I"] - errors["K"]) / errors["I"])):
            out[name].append(values)
        done += b
    return {name: np.concatenate(parts) for name, parts in out.items()}


def permutation_p(awake: np.ndarray, iso: np.ndarray, current: int) -> dict[str, float | int]:
    observed = float(np.linalg.norm(iso.mean(0) - awake.mean(0)))
    pooled, rng = np.concatenate((awake, iso)), np.random.Generator(np.random.PCG64(PERMUTATION_SEED + current))
    exceed = 0
    for _ in range(PERMUTATIONS):
        order = rng.permutation(len(pooled))
        distance = np.linalg.norm(pooled[order[len(awake):]].mean(0) - pooled[order[:len(awake)]].mean(0))
        exceed += int(distance >= observed)
    return {"distance": observed, "exceedances": exceed, "p": (1 + exceed) / (PERMUTATIONS + 1),
            "permutations": PERMUTATIONS, "seed": PERMUTATION_SEED + current}


def gain_residual(awake: np.ndarray, iso: np.ndarray) -> dict[str, float]:
    a, i = awake.mean(0), iso.mean(0)
    alpha = max(0., float((i @ a) / (a @ a)))
    return {"alpha": alpha, "R": float(np.linalg.norm(i - alpha * a) / np.linalg.norm(i))}


def time_half_cells(values: np.ndarray, rows: np.ndarray, schema: dict[str, Any]) -> tuple[dict[str, np.ndarray], dict[str, np.ndarray]]:
    ids, states = schema["trial_ids"][rows], schema["trial_states"][rows]
    currents, starts = schema["trial_currents"][rows], schema["trial_starts"][rows]
    outputs = ({}, {})
    for state in STATES:
        for current in CURRENTS:
            ix = np.flatnonzero((states == state) & (currents == current) & (ids % 2 == 1))
            ix = ix[np.argsort(starts[ix], kind="stable")]
            mid = len(ix) // 2
            if min(mid, len(ix) - mid) < 20:
                raise RuntimeError(f"{STOP}: time halves")
            outputs[0][f"{state}/{current}"] = values[ix[:mid]]
            outputs[1][f"{state}/{current}"] = values[ix[mid:]]
    return outputs


def decide(observed: dict[str, float], lower: dict[str, float], errors: dict[str, float]) -> str:
    supported = lambda name: observed[name] >= .10 and lower[name] > 0
    if supported("K_vs_I") and supported("K_vs_Z"):
        return "CURRENT_SPECIFIC_OPERATOR_SUPPORTED"
    if supported("I_vs_G") and supported("I_vs_Z") and not supported("K_vs_I"):
        return "INDIVIDUAL_AXIS_SUPPORTED"
    if supported("G_vs_Z") and not supported("I_vs_G"):
        return "GLOBAL_AXIS_PARTIAL"
    if all(errors[name] >= errors["Z"] for name in ("G", "I", "K")):
        return "NO_STABLE_STATE_MODEL"
    return "HETEROGENEITY_OPERATOR_TENSION"


def preregistered_files() -> tuple[Path, ...]:
    return (Path(__file__).resolve(), TEST_FILE, CONTRACT)


def schema_receipt(paths: dict[str, Path], artifact_dir: Path) -> dict[str, Any]:
    raw = {s: raw_identity(p, s) for s, p in paths.items()}
    schemas = {}
    for subject, path in paths.items():
        with h5py.File(path, "r") as nwb:
            schemas[subject] = public_schema(read_schema(nwb, subject, endpoint_opened=False))
    receipt = {"confirmation_values_opened": False, "raw": raw, "schemas": schemas}
    receipt["receipt_sha256"] = write_json_once(artifact_dir / SCHEMA_RECEIPT, receipt)
    return receipt


def seal(paths: dict[str, Path], artifact_dir: Path) -> dict[str, Any]:
    receipt_path = artifact_dir / SCHEMA_RECEIPT
    raw = {s: raw_identity(p, s) for s, p in paths.items()}
    if not receipt_path.is_file():
        raise RuntimeError(f"{STOP}: receipt missing")
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    if receipt.get("raw") != raw or receipt.get("confirmation_values_opened") is not False:
        raise RuntimeError(f"{STOP}: receipt identity")
    files = {str(p.relative_to(ROOT)).replace("\\", "/"): sha256_file(p) for p in preregistered_files()}
    manifest = {"confirmation_values_opened": False, "files": files, "raw": raw,
                "schema_receipt_sha256": sha256_file(receipt_path)}
    manifest["manifest_sha256"] = write_json_once(artifact_dir / MANIFEST, manifest)
    return manifest


def verify_manifest(paths: dict[str, Path], artifact_dir: Path) -> str:
    path = artifact_dir / MANIFEST
    if not path.is_file():
        raise RuntimeError(f"{STOP}: manifest missing")
    manifest = json.loads(path.read_text(encoding="utf-8"))
    raw = {s: raw_identity(p, s) for s, p in paths.items()}
    files = {str(p.relative_to(ROOT)).replace("\\", "/"): sha256_file(p) for p in preregistered_files()}
    if (manifest.get("raw") != raw or manifest.get("files") != files
            or manifest.get("confirmation_values_opened") is not False
            or manifest.get("schema_receipt_sha256") != sha256_file(artifact_dir / SCHEMA_RECEIPT)):
        raise RuntimeError(f"{STOP}: manifest mutation")
    return sha256_file(path)


def compute_result(paths: dict[str, Path], artifact_dir: Path) -> dict[str, Any]:
    manifest_sha = verify_manifest(paths, artifact_dir)
    extracted = {}
    for subject, path in paths.items():
        with h5py.File(path, "r") as nwb:
            schema = read_schema(nwb, subject, endpoint_opened=True)
            raw, unit, rows = extract_waveforms(nwb, schema)
            extracted[subject] = (raw, unit, rows, schema)
    source_cells = [cells(extracted[s][1], extracted[s][2], extracted[s][3], parity=None)
                    for s in ("521885", "521886", "521887")]
    raw, unit, rows, schema = extracted["569070"]
    dev, conf = cells(unit, rows, schema, parity=0), cells(unit, rows, schema, parity=1)
    raw_conf = cells(raw, rows, schema, parity=1)
    source = np.stack([contrasts(c, (20,))[0] for c in source_cells])
    d_dev, d_conf = contrasts(dev, CURRENTS), contrasts(conf, CURRENTS)
    predicted = predictions(source, d_dev)
    errors = score(predicted, d_conf)
    observed = improvements(errors)
    boot_values = bootstrap(source_cells, dev, conf)
    lower = {name: float(np.quantile(values, .025)) for name, values in boot_values.items()}
    boot = {name: {"lower_95": lower[name], "median": float(np.median(values))}
            for name, values in boot_values.items()}
    halves = {}
    for name, half in zip(("early", "late"), time_half_cells(unit, rows, schema), strict=True):
        half_conf = contrasts(half, CURRENTS)
        half_errors = score(predicted, half_conf)
        halves[name] = {"errors": half_errors, "improvements": improvements(half_errors),
                        "ranking": sorted(half_errors, key=half_errors.get)}
    permutation = {str(u): permutation_p(conf[f"awake/{u}"], conf[f"isoflurane/{u}"], u)
                   for u in CURRENTS}
    gain = {str(u): gain_residual(raw_conf[f"awake/{u}"], raw_conf[f"isoflurane/{u}"])
            for u in CURRENTS}
    decision = decide(observed, lower, errors)
    result = {"bootstrap": {"comparisons": boot, "repetitions": BOOTSTRAPS, "seed": BOOTSTRAP_SEED},
              "claim_ceiling": "single-target-animal 20/40/60-uA MOs EEG model competition",
              "decision": decision, "errors": errors, "gain_control": gain,
              "improvements": observed, "manifest_sha256": manifest_sha,
              "permutation": permutation, "response_dimension": 2_988,
              "response_shape": [249, 12], "stage3_authorized": False, "time_halves": halves}
    validate_result(result)
    return result


def validate_result(result: dict[str, Any]) -> None:
    lower = {name: row["lower_95"] for name, row in result["bootstrap"]["comparisons"].items()}
    expected = decide(result["improvements"], lower, result["errors"])
    if result.get("decision") != expected or result.get("stage3_authorized") is not False:
        raise RuntimeError(f"{STOP}: decision")
    if result.get("response_dimension") != 2_988 or result["bootstrap"]["repetitions"] != BOOTSTRAPS:
        raise RuntimeError(f"{STOP}: schema")


def execute(paths: dict[str, Path], artifact_dir: Path) -> dict[str, Any]:
    if (artifact_dir / RESULT).exists():
        raise RuntimeError(f"{STOP}: refusing to overwrite {RESULT}")
    result = compute_result(paths, artifact_dir)
    result["result_sha256"] = write_json_once(artifact_dir / RESULT, result)
    return result


def verify_result(paths: dict[str, Path], artifact_dir: Path) -> dict[str, Any]:
    result_path = artifact_dir / RESULT
    stored = json.loads(result_path.read_text(encoding="utf-8"))
    validate_result(stored)
    if canonical_json_bytes(stored) != canonical_json_bytes(compute_result(paths, artifact_dir)):
        raise RuntimeError(f"{STOP}: raw recomputation mismatch")
    receipt = {"decision": stored["decision"], "manifest_sha256": stored["manifest_sha256"],
               "raw_recomputed": True, "result_sha256": sha256_file(result_path), "status": "PASS"}
    receipt["validation_receipt_sha256"] = write_json_once(artifact_dir / VALIDATION, receipt)
    return receipt


def main() -> None:
    parser = argparse.ArgumentParser()
    for flag in ("source-a", "source-b", "source-c", "target"):
        parser.add_argument(f"--{flag}", type=Path, required=True)
    parser.add_argument("--artifact-dir", type=Path,
                        default=ROOT / "artifacts" / "brain" / "ce_brain_phase2d_model_competition")
    mode = parser.add_mutually_exclusive_group(required=True)
    for flag in ("schema-only", "seal", "execute", "verify-result"):
        mode.add_argument(f"--{flag}", action="store_true")
    args = parser.parse_args()
    paths = {"521885": args.source_a, "521886": args.source_b,
             "521887": args.source_c, "569070": args.target}
    if args.schema_only:
        output = schema_receipt(paths, args.artifact_dir)
    elif args.seal:
        output = seal(paths, args.artifact_dir)
    elif args.execute:
        output = execute(paths, args.artifact_dir)
    else:
        output = verify_result(paths, args.artifact_dir)
    print(json.dumps(output, sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()
