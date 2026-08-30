"""Sealed CE-BRAIN Phase 2 state-by-input EEG experiment.

The confirmation EEG values in subject 521886 must remain unopened until the
schema receipt and manifest have been written by this module.
"""

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


STOP = "PHASE2_APPARATUS_STOP"
FS = 2_500.0
CURRENTS = (20, 50, 100)
COMMON_CHANNELS = (0, 1, 2, 3, 4, 5, 9, 20, 22, 23, 24, 25, 26, 27, 28, 29)
STATES = ("awake", "isoflurane")
TARGET_STATES = ("awake", "isoflurane", "recovery")
BOOTSTRAPS = 1_999
BOOTSTRAP_SEED = 20_260_901
SCHEMA_RECEIPT = "phase2-schema-receipt.json"
MANIFEST = "phase2-manifest.json"
RESULT = "phase2-result.json"
VALIDATION = "phase2-validation-receipt.json"

ROOT = Path(__file__).resolve().parents[2]
CONTRACT = ROOT / "paper" / "검증_원장" / "CE_BRAIN_PHASE2_상태입력_계약.md"
TEST_FILE = ROOT / "tests" / "test_ce_brain_phase2_state_input.py"

SPECS: dict[str, dict[str, Any]] = {
    "521885": {
        "bytes": 312_139_546,
        "sha256": "b80cd3a375ead36c05c451f562e92947573cd0679a30ffd573a04e44339b0171",
        "shape": (6_217_728, 30),
        "trial_count": 360,
        "states": STATES,
        "valid_columns": (0, 1, 2, 3, 4, 5, 9, 19, 20, 22, 23, 24, 25, 26, 27, 28, 29),
        "gap_left": 125_307,
        "max_jitter": 2e-5,
        "counts": {
            "awake/20/development": 30, "awake/20/confirmation": 30,
            "awake/50/development": 33, "awake/50/confirmation": 27,
            "awake/100/development": 27, "awake/100/confirmation": 33,
            "isoflurane/20/development": 30, "isoflurane/20/confirmation": 30,
            "isoflurane/50/development": 32, "isoflurane/50/confirmation": 27,
            "isoflurane/100/development": 24, "isoflurane/100/confirmation": 31,
        },
    },
    "521886": {
        "bytes": 504_307_581,
        "sha256": "a799afdf771a5f629e19312d37714b0990418cef0d2b7425b46e17574678fcb6",
        "shape": (10_564_096, 30),
        "trial_count": 900,
        "states": TARGET_STATES,
        "valid_columns": (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29),
        "gap_left": 151_674,
        "max_jitter": 3e-5,
        "counts": {
            "awake/20/development": 53, "awake/20/confirmation": 46,
            "awake/50/development": 48, "awake/50/confirmation": 51,
            "awake/100/development": 48, "awake/100/confirmation": 52,
            "isoflurane/20/development": 54, "isoflurane/20/confirmation": 46,
            "isoflurane/50/development": 48, "isoflurane/50/confirmation": 52,
            "isoflurane/100/development": 48, "isoflurane/100/confirmation": 52,
            "recovery/20/development": 53, "recovery/20/confirmation": 45,
            "recovery/50/development": 47, "recovery/50/confirmation": 51,
            "recovery/100/development": 47, "recovery/100/confirmation": 52,
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
    if not path.is_file():
        raise RuntimeError(f"{STOP}: {subject} raw file missing")
    size = path.stat().st_size
    digest = sha256_file(path)
    if size != spec["bytes"] or digest != spec["sha256"]:
        raise RuntimeError(f"{STOP}: {subject} raw identity mismatch")
    return {"bytes": size, "filename": path.name, "sha256": digest, "subject": subject}


def decode_text(values: np.ndarray) -> np.ndarray:
    return np.asarray([item.decode() if isinstance(item, bytes) else str(item) for item in values])


def nearest_origins(timestamps: np.ndarray, start_times: np.ndarray) -> np.ndarray:
    right = np.clip(np.searchsorted(timestamps, start_times, side="left"), 1, len(timestamps) - 1)
    left = right - 1
    dr = np.abs(timestamps[right] - start_times)
    dl = np.abs(timestamps[left] - start_times)
    if np.any(np.isclose(dr, dl, rtol=0.0, atol=1e-12)):
        raise RuntimeError(f"{STOP}: non-unique nearest timestamp")
    origins = np.where(dr < dl, right, left)
    if np.any(np.abs(timestamps[origins] - start_times) > 0.5 / FS):
        raise RuntimeError(f"{STOP}: trial timing alignment")
    return origins.astype(np.int64)


def split_counts(ids: np.ndarray, states: np.ndarray, currents: np.ndarray,
                 eligible: np.ndarray, expected_states: tuple[str, ...]) -> dict[str, int]:
    result: dict[str, int] = {}
    for state in expected_states:
        for current in CURRENTS:
            for name, parity in (("development", 0), ("confirmation", 1)):
                result[f"{state}/{current}/{name}"] = int(np.sum(
                    eligible & (states == state) & (currents == current) & ((ids % 2) == parity)
                ))
    return result


def read_schema(nwb: h5py.File, subject: str, *, endpoint_opened: bool) -> dict[str, Any]:
    spec = SPECS[subject]
    required = (
        "/acquisition/ElectricalSeriesEEG/data", "/acquisition/ElectricalSeriesEEG/timestamps",
        "/acquisition/ElectricalSeriesEEG/electrodes",
        "/general/extracellular_ephys/electrodes/id",
        "/general/extracellular_ephys/electrodes/is_data_valid",
        "/intervals/trials/id", "/intervals/trials/start_time",
        "/intervals/trials/behavioral_epoch", "/intervals/trials/estim_current",
        "/intervals/trials/estim_target_region", "/intervals/trials/stimulus_description",
        "/intervals/trials/is_valid",
    )
    if any(path not in nwb for path in required):
        raise RuntimeError(f"{STOP}: {subject} required NWB path")
    data = nwb[required[0]]
    if data.shape != spec["shape"] or data.dtype != np.dtype("int16"):
        raise RuntimeError(f"{STOP}: {subject} EEG shape/dtype")
    conversion = float(data.attrs.get("conversion", np.nan))
    if conversion != 1.9499999284744263e-07:
        raise RuntimeError(f"{STOP}: {subject} conversion")
    timestamps = np.asarray(nwb[required[1]][...], dtype=np.float64)
    if timestamps.shape != (spec["shape"][0],) or not np.all(np.isfinite(timestamps)):
        raise RuntimeError(f"{STOP}: {subject} timestamps")
    deltas = np.diff(timestamps)
    median_delta = float(np.median(deltas))
    gaps = np.flatnonzero(deltas > 1.5 * median_delta)
    if (np.any(deltas <= 0) or abs(1 / median_delta - FS) > 0.01
            or gaps.tolist() != [spec["gap_left"]]
            or not 1.999 <= deltas[spec["gap_left"]] / median_delta <= 2.001):
        raise RuntimeError(f"{STOP}: {subject} timestamp gap/rate")
    ordinary = np.delete(deltas, spec["gap_left"])
    if float(np.max(np.abs(ordinary / median_delta - 1))) > spec["max_jitter"]:
        raise RuntimeError(f"{STOP}: {subject} timestamp jitter")
    electrode_ids = np.asarray(nwb[required[3]][...], dtype=np.int64)
    electrode_valid = np.asarray(nwb[required[4]][...], dtype=bool)
    region = nwb[required[2]]
    series_rows = np.asarray(region[...], dtype=np.int64)
    if (electrode_ids.shape != (30,) or not np.array_equal(electrode_ids, np.arange(30))
            or not np.array_equal(series_rows, np.arange(30))):
        raise RuntimeError(f"{STOP}: {subject} electrode mapping")
    valid_columns = tuple(np.flatnonzero(electrode_valid[series_rows]).tolist())
    if valid_columns != spec["valid_columns"] or not set(COMMON_CHANNELS).issubset(valid_columns):
        raise RuntimeError(f"{STOP}: {subject} valid channel profile")
    trials = nwb["/intervals/trials"]
    ids = np.asarray(trials["id"][...], dtype=np.int64)
    starts = np.asarray(trials["start_time"][...], dtype=np.float64)
    states = decode_text(trials["behavioral_epoch"][...])
    current_text = decode_text(trials["estim_current"][...])
    targets = decode_text(trials["estim_target_region"][...])
    descriptions = decode_text(trials["stimulus_description"][...])
    valid_trials = np.asarray(trials["is_valid"][...], dtype=bool)
    if not all(len(value) == spec["trial_count"] for value in
               (ids, starts, states, current_text, targets, descriptions, valid_trials)):
        raise RuntimeError(f"{STOP}: {subject} trial table length")
    try:
        currents = current_text.astype(np.int64)
    except ValueError as error:
        raise RuntimeError(f"{STOP}: {subject} current encoding") from error
    origins = nearest_origins(timestamps, starts)
    eligible = (valid_trials & np.isin(states, spec["states"]) & np.isin(currents, CURRENTS)
                & (targets == "MOs") & (descriptions == "biphasic"))
    counts = split_counts(ids, states, currents, eligible, spec["states"])
    if counts != spec["counts"]:
        raise RuntimeError(f"{STOP}: {subject} registered split counts")
    segment_start = spec["gap_left"] + 1
    selected = origins[eligible]
    if (np.any(selected - 2_500 < segment_start)
            or np.any(selected + 1_250 >= len(timestamps))):
        raise RuntimeError(f"{STOP}: {subject} extraction boundary")
    return {
        "confirmation_values_opened": endpoint_opened,
        "continuous_segment_start": segment_start,
        "conversion_volts_per_count": conversion,
        "eeg_shape": list(data.shape),
        "eligible_mask": eligible,
        "fs_hz": 1 / median_delta,
        "origins": origins,
        "split_counts": counts,
        "timestamp_count": len(timestamps),
        "trial_currents": currents,
        "trial_ids": ids,
        "trial_starts": starts,
        "trial_states": states,
        "valid_channels": list(COMMON_CHANNELS),
    }


def public_schema(schema: dict[str, Any]) -> dict[str, Any]:
    hidden = {"eligible_mask", "origins", "trial_currents", "trial_ids", "trial_starts", "trial_states"}
    return {key: value for key, value in schema.items() if key not in hidden}


def replace_artifacts(signal: np.ndarray, origins: np.ndarray) -> None:
    for origin in origins:
        signal[origin:origin + 5] = signal[origin - 5:origin]


def extract_unit_waveforms(nwb: h5py.File, schema: dict[str, Any]) -> tuple[np.ndarray, np.ndarray]:
    eligible = schema["eligible_mask"]
    rows = np.flatnonzero(eligible)
    origins = schema["origins"][eligible]
    segment_start = schema["continuous_segment_start"]
    relative_origins = origins - segment_start
    data = nwb["/acquisition/ElectricalSeriesEEG/data"]
    response = np.empty((len(origins), 249, len(COMMON_CHANNELS)), dtype=np.float64)
    baseline = np.empty((len(origins), len(COMMON_CHANNELS)), dtype=np.float64)
    sos = butter(3, (0.1, 100.0), btype="bandpass", fs=FS, output="sos")
    for out_channel, source_channel in enumerate(COMMON_CHANNELS):
        continuous = np.asarray(data[segment_start:, source_channel], dtype=np.float64)
        replace_artifacts(continuous, relative_origins)
        continuous *= schema["conversion_volts_per_count"] * 1e6
        continuous = sosfiltfilt(sos, continuous)
        for trial_index, origin in enumerate(relative_origins):
            baseline[trial_index, out_channel] = float(np.mean(continuous[origin - 1_250:origin - 25]))
            response[trial_index, :, out_channel] = continuous[origin + 5:origin + 1_250:5]
    response -= response.mean(axis=2, keepdims=True)
    baseline -= baseline.mean(axis=1, keepdims=True)
    response -= baseline[:, None, :]
    flat = response.reshape(len(response), -1)
    norms = np.linalg.norm(flat, axis=1)
    if (flat.shape[1] != 3_984 or not np.all(np.isfinite(flat))
            or not np.all(np.isfinite(norms)) or np.any(norms <= 0)):
        raise RuntimeError(f"{STOP}: waveform shape/finite/norm")
    return flat / norms[:, None], rows


def make_groups(units: np.ndarray, eligible_rows: np.ndarray, schema: dict[str, Any],
                states: tuple[str, ...], parity: int | None) -> dict[tuple[str, int], np.ndarray]:
    ids = schema["trial_ids"][eligible_rows]
    observed_states = schema["trial_states"][eligible_rows]
    currents = schema["trial_currents"][eligible_rows]
    groups: dict[tuple[str, int], np.ndarray] = {}
    for state in states:
        for current in CURRENTS:
            select = (observed_states == state) & (currents == current)
            if parity is not None:
                select &= (ids % 2) == parity
            group = units[select]
            if len(group) < 20:
                raise RuntimeError(f"{STOP}: insufficient group {state}/{current}/{parity}")
            groups[(state, current)] = group
    return groups


def make_time_half_groups(units: np.ndarray, eligible_rows: np.ndarray,
                          schema: dict[str, Any]) -> tuple[dict[tuple[str, int], np.ndarray],
                                                            dict[tuple[str, int], np.ndarray]]:
    ids = schema["trial_ids"][eligible_rows]
    starts = schema["trial_starts"][eligible_rows]
    observed_states = schema["trial_states"][eligible_rows]
    currents = schema["trial_currents"][eligible_rows]
    early: dict[tuple[str, int], np.ndarray] = {}
    late: dict[tuple[str, int], np.ndarray] = {}
    for state in STATES:
        for current in CURRENTS:
            indices = np.flatnonzero(
                (observed_states == state) & (currents == current) & ((ids % 2) == 1)
            )
            indices = indices[np.argsort(starts[indices], kind="stable")]
            midpoint = len(indices) // 2
            if midpoint < 20 or len(indices) - midpoint < 20:
                raise RuntimeError(f"{STOP}: time-half group {state}/{current}")
            early[(state, current)] = units[indices[:midpoint]]
            late[(state, current)] = units[indices[midpoint:]]
    return early, late


def contrasts(groups: dict[tuple[str, int], np.ndarray], *, normalize: bool = False) -> dict[int, np.ndarray]:
    output = {
        current: groups[("isoflurane", current)].mean(0) - groups[("awake", current)].mean(0)
        for current in CURRENTS
    }
    if normalize:
        for current, value in output.items():
            norm = float(np.linalg.norm(value))
            if not np.isfinite(norm) or norm <= 0:
                raise RuntimeError(f"{STOP}: contrast norm")
            output[current] = value / norm
    return output


def separable_prediction(first: np.ndarray, second: np.ndarray, weight: float) -> np.ndarray:
    """Best rank-one direction for two contrasts with interpolated magnitude."""
    squeeze = first.ndim == 1
    x = first[None, :] if squeeze else first
    y = second[None, :] if squeeze else second
    if x.shape != y.shape or x.ndim != 2:
        raise RuntimeError(f"{STOP}: separable prediction shape")
    gram = np.empty((len(x), 2, 2), dtype=np.float64)
    gram[:, 0, 0] = np.sum(x * x, axis=1)
    gram[:, 0, 1] = gram[:, 1, 0] = np.sum(x * y, axis=1)
    gram[:, 1, 1] = np.sum(y * y, axis=1)
    eigenvalues, eigenvectors = np.linalg.eigh(gram)
    coefficients = eigenvectors[:, :, 1]
    direction = coefficients[:, 0, None] * x + coefficients[:, 1, None] * y
    norms = np.linalg.norm(direction, axis=1)
    if (np.any(eigenvalues[:, 1] <= 0) or np.any(norms <= 0)
            or not np.all(np.isfinite(eigenvalues))):
        raise RuntimeError(f"{STOP}: separable rank-one fit")
    direction /= norms[:, None]
    b1 = np.sum(x * direction, axis=1)
    b2 = np.sum(y * direction, axis=1)
    prediction = ((1 - weight) * b1 + weight * b2)[:, None] * direction
    return prediction[0] if squeeze else prediction


def score_contrasts(source: dict[int, np.ndarray], target: dict[int, np.ndarray]) -> dict[str, Any]:
    errors_m1: dict[int, float] = {}
    errors_m2: dict[int, float] = {}
    for held in CURRENTS:
        train = [current for current in CURRENTS if current != held]
        u1, u2 = train
        weight = (held - u1) / (u2 - u1)
        m1 = separable_prediction(source[u1], source[u2], weight)
        m2 = source[u1] + weight * (source[u2] - source[u1])
        errors_m1[held] = float(np.sum((target[held] - m1) ** 2))
        errors_m2[held] = float(np.sum((target[held] - m2) ** 2))
    mean_m1 = float(np.mean(list(errors_m1.values())))
    mean_m2 = float(np.mean(list(errors_m2.values())))
    if not np.isfinite(mean_m1 + mean_m2) or mean_m1 <= 0:
        raise RuntimeError(f"{STOP}: model score")
    return {
        "errors_m1": {str(key): value for key, value in errors_m1.items()},
        "errors_m2": {str(key): value for key, value in errors_m2.items()},
        "m2_better_currents": int(sum(errors_m2[c] < errors_m1[c] for c in CURRENTS)),
        "mean_error_m1": mean_m1,
        "mean_error_m2": mean_m2,
        "relative_m2_improvement": (mean_m1 - mean_m2) / mean_m1,
    }


def _bootstrap_means(rng: np.random.Generator, values: np.ndarray, batch: int) -> np.ndarray:
    count = len(values)
    weights = rng.multinomial(count, np.full(count, 1 / count), size=batch) / count
    return weights @ values


def bootstrap_improvements(source_groups: dict[tuple[str, int], np.ndarray],
                           target_groups: dict[tuple[str, int], np.ndarray],
                           *, repetitions: int = BOOTSTRAPS, seed: int = BOOTSTRAP_SEED,
                           batch_size: int = 64) -> np.ndarray:
    rng = np.random.Generator(np.random.PCG64(seed))
    improvements: list[np.ndarray] = []
    completed = 0
    while completed < repetitions:
        batch = min(batch_size, repetitions - completed)
        source = {
            (state, current): _bootstrap_means(rng, source_groups[(state, current)], batch)
            for state in STATES for current in CURRENTS
        }
        target = {
            (state, current): _bootstrap_means(rng, target_groups[(state, current)], batch)
            for state in STATES for current in CURRENTS
        }
        ds = {current: source[("isoflurane", current)] - source[("awake", current)] for current in CURRENTS}
        dt = {current: target[("isoflurane", current)] - target[("awake", current)] for current in CURRENTS}
        e1 = np.zeros(batch)
        e2 = np.zeros(batch)
        for held in CURRENTS:
            u1, u2 = [current for current in CURRENTS if current != held]
            weight = (held - u1) / (u2 - u1)
            p1 = separable_prediction(ds[u1], ds[u2], weight)
            p2 = ds[u1] + weight * (ds[u2] - ds[u1])
            e1 += np.sum((dt[held] - p1) ** 2, axis=1) / len(CURRENTS)
            e2 += np.sum((dt[held] - p2) ** 2, axis=1) / len(CURRENTS)
        if np.any(e1 <= 0) or not np.all(np.isfinite(e1 + e2)):
            raise RuntimeError(f"{STOP}: bootstrap model score")
        improvements.append((e1 - e2) / e1)
        completed += batch
    return np.concatenate(improvements)


def decide(score: dict[str, Any], lower: float, upper: float) -> str:
    improvement = score["relative_m2_improvement"]
    better = score["m2_better_currents"]
    if improvement >= 0.05 and lower > 0 and better >= 2:
        return "STATE_INPUT_INTERACTION_SUPPORTED"
    if improvement <= -0.05 and upper < 0 and better <= 1:
        return "STATE_INPUT_SEPARABLE_RETAINED"
    return "STATE_INPUT_NOT_ESTABLISHED"


def recovery_metrics(groups: dict[tuple[str, int], np.ndarray]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for current in CURRENTS:
        awake = groups[("awake", current)].mean(0)
        iso = groups[("isoflurane", current)].mean(0)
        recovery = groups[("recovery", current)].mean(0)
        d_ai = float(np.linalg.norm(iso - awake))
        d_ar = float(np.linalg.norm(recovery - awake))
        if d_ai <= 0 or not np.isfinite(d_ai + d_ar):
            raise RuntimeError(f"{STOP}: recovery distance")
        result[str(current)] = {"D_AI": d_ai, "D_AR": d_ar, "Q": d_ar / d_ai}
    return result


def preregistered_files() -> tuple[Path, ...]:
    return (Path(__file__).resolve(), TEST_FILE, CONTRACT)


def schema_receipt(source_path: Path, target_path: Path, artifact_dir: Path) -> dict[str, Any]:
    identities = {
        "521885": raw_identity(source_path, "521885"),
        "521886": raw_identity(target_path, "521886"),
    }
    schemas: dict[str, Any] = {}
    for subject, path in (("521885", source_path), ("521886", target_path)):
        with h5py.File(path, "r") as nwb:
            schemas[subject] = public_schema(read_schema(nwb, subject, endpoint_opened=False))
    receipt = {"confirmation_values_opened": False, "raw": identities, "schemas": schemas}
    receipt["receipt_sha256"] = write_json_once(artifact_dir / SCHEMA_RECEIPT, receipt)
    return receipt


def seal(source_path: Path, target_path: Path, artifact_dir: Path) -> dict[str, Any]:
    receipt_path = artifact_dir / SCHEMA_RECEIPT
    if not receipt_path.is_file():
        raise RuntimeError(f"{STOP}: schema receipt missing")
    raw = {"521885": raw_identity(source_path, "521885"), "521886": raw_identity(target_path, "521886")}
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    if receipt.get("raw") != raw or receipt.get("confirmation_values_opened") is not False:
        raise RuntimeError(f"{STOP}: schema receipt identity")
    files = {str(path.relative_to(ROOT)).replace("\\", "/"): sha256_file(path) for path in preregistered_files()}
    manifest = {
        "confirmation_values_opened": False,
        "files": files,
        "raw": raw,
        "schema_receipt_sha256": sha256_file(receipt_path),
    }
    manifest["manifest_sha256"] = write_json_once(artifact_dir / MANIFEST, manifest)
    return manifest


def verify_manifest(source_path: Path, target_path: Path, artifact_dir: Path) -> tuple[dict[str, Any], str]:
    path = artifact_dir / MANIFEST
    if not path.is_file():
        raise RuntimeError(f"{STOP}: manifest missing")
    manifest = json.loads(path.read_text(encoding="utf-8"))
    raw = {"521885": raw_identity(source_path, "521885"), "521886": raw_identity(target_path, "521886")}
    if manifest.get("confirmation_values_opened") is not False or manifest.get("raw") != raw:
        raise RuntimeError(f"{STOP}: manifest state/identity")
    if manifest.get("schema_receipt_sha256") != sha256_file(artifact_dir / SCHEMA_RECEIPT):
        raise RuntimeError(f"{STOP}: schema receipt mutation")
    current = {str(path.relative_to(ROOT)).replace("\\", "/"): sha256_file(path) for path in preregistered_files()}
    if manifest.get("files") != current:
        raise RuntimeError(f"{STOP}: preregistration mutation")
    return manifest, sha256_file(path)


def compute_result(source_path: Path, target_path: Path, artifact_dir: Path) -> dict[str, Any]:
    _, manifest_sha = verify_manifest(source_path, target_path, artifact_dir)
    extracted: dict[str, tuple[np.ndarray, np.ndarray, dict[str, Any]]] = {}
    for subject, path in (("521885", source_path), ("521886", target_path)):
        with h5py.File(path, "r") as nwb:
            schema = read_schema(nwb, subject, endpoint_opened=True)
            units, rows = extract_unit_waveforms(nwb, schema)
            extracted[subject] = (units, rows, schema)
    source_units, source_rows, source_schema = extracted["521885"]
    target_units, target_rows, target_schema = extracted["521886"]
    source_all = make_groups(source_units, source_rows, source_schema, STATES, None)
    target_confirm = make_groups(target_units, target_rows, target_schema, STATES, 1)
    target_development = make_groups(target_units, target_rows, target_schema, STATES, 0)
    target_recovery = make_groups(target_units, target_rows, target_schema, TARGET_STATES, 1)
    target_early, target_late = make_time_half_groups(target_units, target_rows, target_schema)
    score = score_contrasts(contrasts(source_all), contrasts(target_confirm))
    bootstrap = bootstrap_improvements(source_all, target_confirm)
    lower, upper = (float(np.quantile(bootstrap, q)) for q in (0.025, 0.975))
    shape_score = score_contrasts(contrasts(source_all, normalize=True),
                                  contrasts(target_confirm, normalize=True))
    within_target = score_contrasts(contrasts(target_development), contrasts(target_confirm))
    result = {
        "bootstrap": {
            "lower_95": lower,
            "median": float(np.median(bootstrap)),
            "repetitions": BOOTSTRAPS,
            "seed": BOOTSTRAP_SEED,
            "upper_95": upper,
        },
        "claim_ceiling": "two-mouse MOs-evoked EEG measurement-space state-by-current result",
        "decision": decide(score, lower, upper),
        "manifest_sha256": manifest_sha,
        "primary_cross_animal_cross_current": score,
        "recovery_descriptive": recovery_metrics(target_recovery),
        "response_dimension": 3_984,
        "response_shape": [249, 16],
        "shape_only_cross_animal_cross_current": shape_score,
        "source_subject": "521885_OUTCOME_KNOWN_DEVELOPMENT",
        "target_subject": "521886_CONFIRMATION",
        "target_time_half_cross_animal": {
            "early": score_contrasts(contrasts(source_all), contrasts(target_early)),
            "late": score_contrasts(contrasts(source_all), contrasts(target_late)),
        },
        "within_target_development_to_confirmation": within_target,
    }
    validate_result(result)
    return result


def validate_result(result: dict[str, Any]) -> None:
    score = result["primary_cross_animal_cross_current"]
    bootstrap = result["bootstrap"]
    expected = decide(score, bootstrap["lower_95"], bootstrap["upper_95"])
    if result.get("decision") != expected or result.get("response_dimension") != 3_984:
        raise RuntimeError(f"{STOP}: result decision/schema")
    numeric = [
        score["mean_error_m1"], score["mean_error_m2"], score["relative_m2_improvement"],
        bootstrap["lower_95"], bootstrap["median"], bootstrap["upper_95"],
    ]
    if not np.all(np.isfinite(numeric)) or bootstrap["repetitions"] != BOOTSTRAPS:
        raise RuntimeError(f"{STOP}: result finite/bootstrap")


def execute(source_path: Path, target_path: Path, artifact_dir: Path) -> dict[str, Any]:
    if (artifact_dir / RESULT).exists():
        raise RuntimeError(f"{STOP}: refusing to overwrite {RESULT}")
    result = compute_result(source_path, target_path, artifact_dir)
    result_sha = write_json_once(artifact_dir / RESULT, result)
    stored = json.loads((artifact_dir / RESULT).read_text(encoding="utf-8"))
    validate_result(stored)
    return {"result_sha256": result_sha, **stored}


def verify_result(source_path: Path, target_path: Path, artifact_dir: Path) -> dict[str, Any]:
    result_path = artifact_dir / RESULT
    if not result_path.is_file():
        raise RuntimeError(f"{STOP}: result missing")
    stored = json.loads(result_path.read_text(encoding="utf-8"))
    validate_result(stored)
    recomputed = compute_result(source_path, target_path, artifact_dir)
    if canonical_json_bytes(stored) != canonical_json_bytes(recomputed):
        raise RuntimeError(f"{STOP}: raw recomputation mismatch")
    receipt = {
        "decision": stored["decision"],
        "manifest_sha256": stored["manifest_sha256"],
        "raw_recomputed": True,
        "result_sha256": sha256_file(result_path),
        "status": "PASS",
    }
    receipt["validation_receipt_sha256"] = write_json_once(artifact_dir / VALIDATION, receipt)
    return receipt


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--target", type=Path, required=True)
    parser.add_argument("--artifact-dir", type=Path, default=ROOT / "artifacts" / "brain" / "ce_brain_phase2_state_input")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--schema-only", action="store_true")
    mode.add_argument("--seal", action="store_true")
    mode.add_argument("--execute", action="store_true")
    mode.add_argument("--verify-result", action="store_true")
    args = parser.parse_args()
    if args.schema_only:
        output = schema_receipt(args.source, args.target, args.artifact_dir)
    elif args.seal:
        output = seal(args.source, args.target, args.artifact_dir)
    elif args.execute:
        output = execute(args.source, args.target, args.artifact_dir)
    else:
        output = verify_result(args.source, args.target, args.artifact_dir)
    print(json.dumps(output, sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()
