"""Sealed independent confirmation of the CE-BRAIN rank-one state axis."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
from typing import Any

import h5py
import numpy as np
from scipy.signal import butter, sosfiltfilt


STOP = "PHASE2C_APPARATUS_STOP"
FS = 2_500.0
CURRENT = 20
CHANNELS = (0, 1, 2, 3, 5, 20, 22, 23, 24, 25, 26, 27, 28, 29)
STATES = ("awake", "isoflurane")
ALL_STATES = ("awake", "isoflurane", "recovery")
BOOTSTRAPS = 1_999
BOOTSTRAP_SEED = 20_260_902
PERMUTATIONS = 999
PERMUTATION_SEED = 20_261_902
SCHEMA_RECEIPT = "phase2c-schema-receipt.json"
MANIFEST = "phase2c-manifest.json"
RESULT = "phase2c-result.json"
VALIDATION = "phase2c-validation-receipt.json"

ROOT = Path(__file__).resolve().parents[2]
CONTRACT = ROOT / "paper" / "검증_원장" / "CE_BRAIN_PHASE2C_공통상태축_계약.md"
TEST_FILE = ROOT / "tests" / "test_ce_brain_phase2c_state_axis.py"

SPECS: dict[str, dict[str, Any]] = {
    "521885": {
        "bytes": 312_139_546,
        "sha256": "b80cd3a375ead36c05c451f562e92947573cd0679a30ffd573a04e44339b0171",
        "shape": (6_217_728, 30),
        "trial_count": 360,
        "valid_columns": (0, 1, 2, 3, 4, 5, 9, 19, 20, 22, 23, 24, 25, 26, 27, 28, 29),
        "gaps": (125_307,), "max_jitter": 2e-5,
        "segments": {"awake": (125_308, 6_217_728), "isoflurane": (125_308, 6_217_728)},
        "counts": {"awake/development": 30, "awake/confirmation": 30,
                   "isoflurane/development": 30, "isoflurane/confirmation": 30},
    },
    "521886": {
        "bytes": 504_307_581,
        "sha256": "a799afdf771a5f629e19312d37714b0990418cef0d2b7425b46e17574678fcb6",
        "shape": (10_564_096, 30),
        "trial_count": 900,
        "valid_columns": (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29),
        "gaps": (151_674,), "max_jitter": 3e-5,
        "segments": {state: (151_675, 10_564_096) for state in ALL_STATES},
        "counts": {"awake/development": 53, "awake/confirmation": 46,
                   "isoflurane/development": 54, "isoflurane/confirmation": 46},
    },
    "521887": {
        "bytes": 428_192_135,
        "sha256": "716e5372de827ab0a72fae5036045527f5e884bcc5a48215bba278fbb516521e",
        "shape": (9_261_311, 30),
        "trial_count": 800,
        "valid_columns": (0, 1, 2, 3, 5, 6, 8, 10, 16, 17, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29),
        "gaps": (97_470, 2_354_430), "max_jitter": 3e-5,
        "segments": {
            "awake": (97_471, 2_354_431),
            "isoflurane": (2_354_431, 9_261_311),
            "recovery": (2_354_431, 9_261_311),
        },
        "counts": {"awake/development": 95, "awake/confirmation": 95,
                   "isoflurane/development": 150, "isoflurane/confirmation": 150,
                   "recovery/development": 150, "recovery/confirmation": 150},
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
    if not path.is_file() or path.stat().st_size != spec["bytes"]:
        raise RuntimeError(f"{STOP}: {subject} raw size/path")
    digest = sha256_file(path)
    if digest != spec["sha256"]:
        raise RuntimeError(f"{STOP}: {subject} raw hash")
    return {"subject": subject, "filename": path.name, "bytes": path.stat().st_size, "sha256": digest}


def decode(values: np.ndarray) -> np.ndarray:
    return np.asarray([value.decode() if isinstance(value, bytes) else str(value) for value in values])


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
    timestamp_ds = nwb["/acquisition/ElectricalSeriesEEG/timestamps"]
    if data.shape != spec["shape"] or data.dtype != np.dtype("int16"):
        raise RuntimeError(f"{STOP}: {subject} EEG shape/dtype")
    conversion = float(data.attrs.get("conversion", np.nan))
    if conversion != 1.9499999284744263e-07:
        raise RuntimeError(f"{STOP}: {subject} conversion")
    timestamps = np.asarray(timestamp_ds[...], dtype=np.float64)
    deltas = np.diff(timestamps)
    median = float(np.median(deltas))
    gaps = tuple(np.flatnonzero(deltas > 1.5 * median).tolist())
    if (timestamps.shape != (spec["shape"][0],) or not np.all(np.isfinite(timestamps))
            or np.any(deltas <= 0) or abs(1 / median - FS) > 0.02 or gaps != spec["gaps"]):
        raise RuntimeError(f"{STOP}: {subject} timestamp profile")
    ordinary = np.delete(deltas, spec["gaps"])
    if float(np.max(np.abs(ordinary / median - 1))) > spec["max_jitter"]:
        raise RuntimeError(f"{STOP}: {subject} timestamp jitter")
    region = np.asarray(nwb["/acquisition/ElectricalSeriesEEG/electrodes"][...], dtype=np.int64)
    valid = np.asarray(nwb["/general/extracellular_ephys/electrodes/is_data_valid"][...], dtype=bool)
    valid_columns = tuple(np.flatnonzero(valid[region]).tolist())
    if not np.array_equal(region, np.arange(30)) or valid_columns != spec["valid_columns"]:
        raise RuntimeError(f"{STOP}: {subject} electrode profile")
    if not set(CHANNELS).issubset(valid_columns):
        raise RuntimeError(f"{STOP}: {subject} common channels")
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
    permitted_states = ALL_STATES if subject == "521887" else STATES
    eligible = valid_trials & np.isin(states, permitted_states) & (currents == CURRENT)
    eligible &= (targets == "MOs") & (descriptions == "biphasic")
    for index in np.flatnonzero(eligible):
        lo, hi = spec["segments"][states[index]]
        eligible[index] = origins[index] - 2_500 >= lo and origins[index] + 1_250 < hi
    counts: dict[str, int] = {}
    for state in permitted_states:
        for name, parity in (("development", 0), ("confirmation", 1)):
            counts[f"{state}/{name}"] = int(np.sum(eligible & (states == state) & ((ids % 2) == parity)))
    if counts != spec["counts"]:
        raise RuntimeError(f"{STOP}: {subject} split counts")
    return {
        "confirmation_values_opened": endpoint_opened,
        "conversion": conversion,
        "eeg_shape": list(data.shape),
        "eligible": eligible,
        "fs_hz": 1 / median,
        "origins": origins,
        "segments": spec["segments"],
        "split_counts": counts,
        "trial_ids": ids,
        "trial_starts": starts,
        "trial_states": states,
        "valid_channels": list(CHANNELS),
    }


def public_schema(schema: dict[str, Any]) -> dict[str, Any]:
    hidden = {"eligible", "origins", "trial_ids", "trial_starts", "trial_states"}
    return {key: value for key, value in schema.items() if key not in hidden}


def replace_artifacts(signal: np.ndarray, origins: np.ndarray) -> None:
    for origin in origins:
        signal[origin:origin + 5] = signal[origin - 5:origin]


def extract_waveforms(nwb: h5py.File, schema: dict[str, Any]) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    rows = np.flatnonzero(schema["eligible"])
    origins = schema["origins"][rows]
    states = schema["trial_states"][rows]
    raw = np.empty((len(rows), 249, len(CHANNELS)), dtype=np.float64)
    baseline = np.empty((len(rows), len(CHANNELS)), dtype=np.float64)
    data = nwb["/acquisition/ElectricalSeriesEEG/data"]
    sos = butter(3, (0.1, 100.0), btype="bandpass", fs=FS, output="sos")
    unique_segments = sorted(set(tuple(value) for value in schema["segments"].values()))
    for out_channel, source_channel in enumerate(CHANNELS):
        for lo, hi in unique_segments:
            trial_indices = np.flatnonzero([
                tuple(schema["segments"][state]) == (lo, hi) for state in states
            ])
            if not len(trial_indices):
                continue
            relative = origins[trial_indices] - lo
            continuous = np.asarray(data[lo:hi, source_channel], dtype=np.float64)
            replace_artifacts(continuous, relative)
            continuous *= schema["conversion"] * 1e6
            continuous = sosfiltfilt(sos, continuous)
            for trial_index, origin in zip(trial_indices, relative, strict=True):
                baseline[trial_index, out_channel] = float(np.mean(continuous[origin - 1_250:origin - 25]))
                raw[trial_index, :, out_channel] = continuous[origin + 5:origin + 1_250:5]
    raw -= raw.mean(axis=2, keepdims=True)
    baseline -= baseline.mean(axis=1, keepdims=True)
    raw -= baseline[:, None, :]
    flat = raw.reshape(len(raw), -1)
    norms = np.linalg.norm(flat, axis=1)
    if flat.shape[1] != 3_486 or not np.all(np.isfinite(flat)) or np.any(norms <= 0):
        raise RuntimeError(f"{STOP}: waveform shape/finite/norm")
    return flat, flat / norms[:, None], rows


def groups(values: np.ndarray, rows: np.ndarray, schema: dict[str, Any],
           states: tuple[str, ...], parity: int | None) -> dict[str, np.ndarray]:
    ids = schema["trial_ids"][rows]
    observed = schema["trial_states"][rows]
    output: dict[str, np.ndarray] = {}
    for state in states:
        select = observed == state
        if parity is not None:
            select &= (ids % 2) == parity
        output[state] = values[select]
        if len(output[state]) < 20:
            raise RuntimeError(f"{STOP}: group {state}/{parity}")
    return output


def contrast(grouped: dict[str, np.ndarray]) -> np.ndarray:
    return grouped["isoflurane"].mean(0) - grouped["awake"].mean(0)


def rank_one_axis(first: np.ndarray, second: np.ndarray) -> np.ndarray:
    matrix = np.stack((first, second))
    _, singular, vh = np.linalg.svd(matrix, full_matrices=False)
    if singular[0] <= 0 or not np.all(np.isfinite(singular)):
        raise RuntimeError(f"{STOP}: rank-one axis")
    axis = vh[0]
    if float(axis @ (first + second)) < 0:
        axis = -axis
    return axis


def axis_statistics(axis: np.ndarray, development: np.ndarray, confirmation: np.ndarray) -> dict[str, float]:
    amplitude = float(development @ axis)
    prediction = amplitude * axis
    zero_error = float(confirmation @ confirmation)
    axis_error = float(np.sum((confirmation - prediction) ** 2))
    norm = float(np.sqrt(zero_error))
    if zero_error <= 0 or norm <= 0:
        raise RuntimeError(f"{STOP}: axis statistic norm")
    return {
        "axis_amplitude_from_development": amplitude,
        "axis_error": axis_error,
        "improvement_over_zero": (zero_error - axis_error) / zero_error,
        "signed_cosine": float((confirmation @ axis) / norm),
        "zero_error": zero_error,
    }


def _means(rng: np.random.Generator, values: np.ndarray, batch: int) -> np.ndarray:
    n = len(values)
    return (rng.multinomial(n, np.full(n, 1 / n), size=batch) / n) @ values


def bootstrap(source1: dict[str, np.ndarray], source2: dict[str, np.ndarray],
              target_dev: dict[str, np.ndarray], target_confirm: dict[str, np.ndarray],
              target_recovery: np.ndarray, *, repetitions: int = BOOTSTRAPS,
              seed: int = BOOTSTRAP_SEED, batch_size: int = 64) -> dict[str, np.ndarray]:
    rng = np.random.Generator(np.random.PCG64(seed))
    improvements: list[np.ndarray] = []
    cosines: list[np.ndarray] = []
    q_values: list[np.ndarray] = []
    completed = 0
    while completed < repetitions:
        batch = min(batch_size, repetitions - completed)
        d1 = _means(rng, source1["isoflurane"], batch) - _means(rng, source1["awake"], batch)
        d2 = _means(rng, source2["isoflurane"], batch) - _means(rng, source2["awake"], batch)
        stacked = np.stack((d1, d2), axis=1)
        gram = stacked @ np.swapaxes(stacked, 1, 2)
        _, eigenvectors = np.linalg.eigh(gram)
        coeff = eigenvectors[:, :, 1]
        axis = coeff[:, 0, None] * d1 + coeff[:, 1, None] * d2
        axis /= np.linalg.norm(axis, axis=1)[:, None]
        orientation = np.sign(np.sum(axis * (d1 + d2), axis=1))
        orientation[orientation == 0] = 1
        axis *= orientation[:, None]
        dev = _means(rng, target_dev["isoflurane"], batch) - _means(rng, target_dev["awake"], batch)
        awake = _means(rng, target_confirm["awake"], batch)
        iso = _means(rng, target_confirm["isoflurane"], batch)
        conf = iso - awake
        recovery = _means(rng, target_recovery, batch)
        amplitude = np.sum(dev * axis, axis=1)
        prediction = amplitude[:, None] * axis
        zero = np.sum(conf * conf, axis=1)
        improvements.append((zero - np.sum((conf - prediction) ** 2, axis=1)) / zero)
        cosines.append(np.sum(conf * axis, axis=1) / np.sqrt(zero))
        q_values.append(np.linalg.norm(recovery - awake, axis=1) / np.linalg.norm(iso - awake, axis=1))
        completed += batch
    return {"improvement": np.concatenate(improvements), "cosine": np.concatenate(cosines),
            "Q": np.concatenate(q_values)}


def permutation_p(awake: np.ndarray, iso: np.ndarray) -> tuple[float, int, float]:
    observed = float(np.linalg.norm(iso.mean(0) - awake.mean(0)))
    pooled = np.concatenate((awake, iso))
    rng = np.random.Generator(np.random.PCG64(PERMUTATION_SEED))
    exceedances = 0
    for _ in range(PERMUTATIONS):
        order = rng.permutation(len(pooled))
        distance = float(np.linalg.norm(
            pooled[order[len(awake):]].mean(0) - pooled[order[:len(awake)]].mean(0)
        ))
        exceedances += int(distance >= observed)
    return (1 + exceedances) / (PERMUTATIONS + 1), exceedances, observed


def gain_residual(awake: np.ndarray, iso: np.ndarray) -> dict[str, float]:
    a, i = awake.mean(0), iso.mean(0)
    aa, ii = float(a @ a), float(i @ i)
    if aa <= 0 or ii <= 0:
        raise RuntimeError(f"{STOP}: gain norm")
    alpha = max(0.0, float((i @ a) / aa))
    return {"alpha": alpha, "R": float(np.linalg.norm(i - alpha * a) / np.sqrt(ii))}


def time_halves(values: np.ndarray, rows: np.ndarray, schema: dict[str, Any]) -> tuple[dict[str, np.ndarray], dict[str, np.ndarray]]:
    ids, states = schema["trial_ids"][rows], schema["trial_states"][rows]
    starts = schema["trial_starts"][rows]
    early: dict[str, np.ndarray] = {}
    late: dict[str, np.ndarray] = {}
    for state in STATES:
        indices = np.flatnonzero((states == state) & ((ids % 2) == 1))
        indices = indices[np.argsort(starts[indices], kind="stable")]
        middle = len(indices) // 2
        if middle < 20 or len(indices) - middle < 20:
            raise RuntimeError(f"{STOP}: time halves")
        early[state], late[state] = values[indices[:middle]], values[indices[middle:]]
    return early, late


def decide(axis: dict[str, float], boot: dict[str, float], permutation: float,
           gain: dict[str, float], q: float, q_upper: float,
           half_stats: dict[str, dict[str, float]]) -> str:
    state_supported = (
        axis["improvement_over_zero"] >= 0.10 and boot["improvement_lower_95"] > 0
        and axis["signed_cosine"] >= 0.30 and boot["cosine_lower_95"] > 0
        and permutation <= 0.01 and gain["R"] >= 0.10
        and all(row["improvement_over_zero"] > 0 and row["signed_cosine"] > 0
                for row in half_stats.values())
    )
    if state_supported and q <= 0.75 and q_upper < 1:
        return "STATE_AXIS_AND_RECOVERY_SUPPORTED"
    if state_supported:
        return "STATE_AXIS_SUPPORTED_RECOVERY_NOT_ESTABLISHED"
    return "STATE_AXIS_NOT_ESTABLISHED"


def preregistered_files() -> tuple[Path, ...]:
    return (Path(__file__).resolve(), TEST_FILE, CONTRACT)


def schema_receipt(paths: dict[str, Path], artifact_dir: Path) -> dict[str, Any]:
    raw = {subject: raw_identity(path, subject) for subject, path in paths.items()}
    schemas = {}
    for subject, path in paths.items():
        with h5py.File(path, "r") as nwb:
            schemas[subject] = public_schema(read_schema(nwb, subject, endpoint_opened=False))
    receipt = {"confirmation_values_opened": False, "raw": raw, "schemas": schemas}
    receipt["receipt_sha256"] = write_json_once(artifact_dir / SCHEMA_RECEIPT, receipt)
    return receipt


def seal(paths: dict[str, Path], artifact_dir: Path) -> dict[str, Any]:
    receipt_path = artifact_dir / SCHEMA_RECEIPT
    if not receipt_path.is_file():
        raise RuntimeError(f"{STOP}: schema receipt missing")
    raw = {subject: raw_identity(path, subject) for subject, path in paths.items()}
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    if receipt.get("raw") != raw or receipt.get("confirmation_values_opened") is not False:
        raise RuntimeError(f"{STOP}: receipt identity")
    files = {str(path.relative_to(ROOT)).replace("\\", "/"): sha256_file(path)
             for path in preregistered_files()}
    manifest = {"confirmation_values_opened": False, "files": files, "raw": raw,
                "schema_receipt_sha256": sha256_file(receipt_path)}
    manifest["manifest_sha256"] = write_json_once(artifact_dir / MANIFEST, manifest)
    return manifest


def verify_manifest(paths: dict[str, Path], artifact_dir: Path) -> str:
    path = artifact_dir / MANIFEST
    if not path.is_file():
        raise RuntimeError(f"{STOP}: manifest missing")
    manifest = json.loads(path.read_text(encoding="utf-8"))
    raw = {subject: raw_identity(raw_path, subject) for subject, raw_path in paths.items()}
    files = {str(file.relative_to(ROOT)).replace("\\", "/"): sha256_file(file)
             for file in preregistered_files()}
    if (manifest.get("confirmation_values_opened") is not False or manifest.get("raw") != raw
            or manifest.get("files") != files
            or manifest.get("schema_receipt_sha256") != sha256_file(artifact_dir / SCHEMA_RECEIPT)):
        raise RuntimeError(f"{STOP}: manifest mutation")
    return sha256_file(path)


def compute_result(paths: dict[str, Path], artifact_dir: Path) -> dict[str, Any]:
    manifest_sha = verify_manifest(paths, artifact_dir)
    extracted: dict[str, tuple[np.ndarray, np.ndarray, np.ndarray, dict[str, Any]]] = {}
    for subject, path in paths.items():
        with h5py.File(path, "r") as nwb:
            schema = read_schema(nwb, subject, endpoint_opened=True)
            raw, unit, rows = extract_waveforms(nwb, schema)
            extracted[subject] = (raw, unit, rows, schema)
    source_groups = []
    for subject in ("521885", "521886"):
        _, unit, rows, schema = extracted[subject]
        source_groups.append(groups(unit, rows, schema, STATES, None))
    raw_target, unit_target, target_rows, target_schema = extracted["521887"]
    target_dev = groups(unit_target, target_rows, target_schema, STATES, 0)
    target_conf = groups(unit_target, target_rows, target_schema, STATES, 1)
    target_all_conf = groups(unit_target, target_rows, target_schema, ALL_STATES, 1)
    raw_conf = groups(raw_target, target_rows, target_schema, STATES, 1)
    d1, d2 = contrast(source_groups[0]), contrast(source_groups[1])
    axis = rank_one_axis(d1, d2)
    axis_result = axis_statistics(axis, contrast(target_dev), contrast(target_conf))
    boot_values = bootstrap(source_groups[0], source_groups[1], target_dev, target_conf,
                            target_all_conf["recovery"])
    boot = {
        "cosine_lower_95": float(np.quantile(boot_values["cosine"], 0.025)),
        "cosine_median": float(np.median(boot_values["cosine"])),
        "improvement_lower_95": float(np.quantile(boot_values["improvement"], 0.025)),
        "improvement_median": float(np.median(boot_values["improvement"])),
        "Q_upper_97_5": float(np.quantile(boot_values["Q"], 0.975)),
        "repetitions": BOOTSTRAPS,
        "seed": BOOTSTRAP_SEED,
    }
    permutation, exceedances, distance = permutation_p(target_conf["awake"], target_conf["isoflurane"])
    gain = gain_residual(raw_conf["awake"], raw_conf["isoflurane"])
    awake, iso, recovery = (target_all_conf[state].mean(0) for state in ALL_STATES)
    d_ai, d_ar = float(np.linalg.norm(iso - awake)), float(np.linalg.norm(recovery - awake))
    q = d_ar / d_ai
    early, late = time_halves(unit_target, target_rows, target_schema)
    halves = {
        "early": axis_statistics(axis, contrast(target_dev), contrast(early)),
        "late": axis_statistics(axis, contrast(target_dev), contrast(late)),
    }
    decision = decide(axis_result, boot, permutation, gain, q, boot["Q_upper_97_5"], halves)
    result = {
        "axis": axis_result,
        "bootstrap": boot,
        "claim_ceiling": "three-mouse 20-uA MOs-evoked EEG measurement-space state-axis result",
        "decision": decision,
        "gain_control": gain,
        "manifest_sha256": manifest_sha,
        "permutation": {"distance": distance, "exceedances": exceedances,
                        "p": permutation, "permutations": PERMUTATIONS, "seed": PERMUTATION_SEED},
        "recovery": {"D_AI": d_ai, "D_AR": d_ar, "Q": q,
                     "Q_upper_97_5": boot["Q_upper_97_5"]},
        "response_dimension": 3_486,
        "response_shape": [249, 14],
        "stage3_authorized": decision == "STATE_AXIS_AND_RECOVERY_SUPPORTED",
        "time_halves": halves,
    }
    validate_result(result)
    return result


def validate_result(result: dict[str, Any]) -> None:
    expected = decide(result["axis"], result["bootstrap"], result["permutation"]["p"],
                      result["gain_control"], result["recovery"]["Q"],
                      result["recovery"]["Q_upper_97_5"], result["time_halves"])
    if result.get("decision") != expected or result.get("stage3_authorized") != (
            expected == "STATE_AXIS_AND_RECOVERY_SUPPORTED"):
        raise RuntimeError(f"{STOP}: result decision")
    if result.get("response_dimension") != 3_486 or result["bootstrap"]["repetitions"] != BOOTSTRAPS:
        raise RuntimeError(f"{STOP}: result schema")


def execute(paths: dict[str, Path], artifact_dir: Path) -> dict[str, Any]:
    if (artifact_dir / RESULT).exists():
        raise RuntimeError(f"{STOP}: refusing to overwrite {RESULT}")
    result = compute_result(paths, artifact_dir)
    result_sha = write_json_once(artifact_dir / RESULT, result)
    return {"result_sha256": result_sha, **result}


def verify_result(paths: dict[str, Path], artifact_dir: Path) -> dict[str, Any]:
    result_path = artifact_dir / RESULT
    if not result_path.is_file():
        raise RuntimeError(f"{STOP}: result missing")
    stored = json.loads(result_path.read_text(encoding="utf-8"))
    validate_result(stored)
    recomputed = compute_result(paths, artifact_dir)
    if canonical_json_bytes(stored) != canonical_json_bytes(recomputed):
        raise RuntimeError(f"{STOP}: raw recomputation mismatch")
    receipt = {"decision": stored["decision"], "manifest_sha256": stored["manifest_sha256"],
               "raw_recomputed": True, "result_sha256": sha256_file(result_path), "status": "PASS"}
    receipt["validation_receipt_sha256"] = write_json_once(artifact_dir / VALIDATION, receipt)
    return receipt


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-a", type=Path, required=True)
    parser.add_argument("--source-b", type=Path, required=True)
    parser.add_argument("--target", type=Path, required=True)
    parser.add_argument("--artifact-dir", type=Path,
                        default=ROOT / "artifacts" / "brain" / "ce_brain_phase2c_state_axis")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--schema-only", action="store_true")
    mode.add_argument("--seal", action="store_true")
    mode.add_argument("--execute", action="store_true")
    mode.add_argument("--verify-result", action="store_true")
    args = parser.parse_args()
    paths = {"521885": args.source_a, "521886": args.source_b, "521887": args.target}
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
