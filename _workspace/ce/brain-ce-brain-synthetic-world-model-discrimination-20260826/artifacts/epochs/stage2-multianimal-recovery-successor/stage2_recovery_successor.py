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


FS = 2500.0
STATES = ("awake", "isoflurane", "recovery")
COMMON_CHANNELS = (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 16, 21, 22, 23, 24, 25, 26, 27, 28, 29)
STOP = "STAGE2_SUCCESSOR_APPARATUS_STOP"
MANIFEST = "successor-manifest.json"
RESULT = "successor-result.json"
VALIDATION = "successor-validation-receipt.json"

SPECS: dict[str, dict[str, Any]] = {
    "543393": {
        "asset_id": "73689194-02e4-40c5-9936-5c6ed7cfb99d",
        "path": "sub-543393/sub-543393_ses-20200820_behavior+ecephys.nwb",
        "size": 527_509_576,
        "sha256": "78e4809d903aea2261c302799b3ee03b899f01183ccbf434af8671afc6fba332",
        "current": 70,
        "shape": (10_727_680, 30),
        "valid_rows": (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 16, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29),
        "split_counts": {
            "awake/development": 150, "awake/confirmation": 150,
            "isoflurane/development": 150, "isoflurane/confirmation": 150,
            "recovery/development": 150, "recovery/confirmation": 150,
        },
    },
    "543394": {
        "asset_id": "f00ff515-1833-4f4f-bd9e-9c7dbf353397",
        "path": "sub-543394/sub-543394_ses-20200827_behavior+ecephys.nwb",
        "size": 589_190_292,
        "sha256": "3d9b703e2c96428cad82af4ff13f8f4d1f4c7302c758fad4243220854dbb4c1c",
        "current": 50,
        "shape": (11_697_152, 30),
        "valid_rows": (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 16, 21, 22, 23, 24, 25, 26, 27, 28, 29),
        "split_counts": {
            "awake/development": 150, "awake/confirmation": 150,
            "isoflurane/development": 150, "isoflurane/confirmation": 150,
            "recovery/development": 149, "recovery/confirmation": 149,
        },
    },
}

PREREGISTERED_FILES = (
    "00-contract.md", "10-data-lock.md", "10-sources.md", "20-hypotheses.md",
    "20-audit.md", "21-preexecution-validation.md", "30-models.md", "40-metrics.md",
    "50-gates.md", "60-negative-controls.md",
    "probe_successor_schema.py", "schema-543393.json", "schema-543394.json",
    "stage2_recovery_successor.py", "test_stage2_recovery_successor.py",
)


def epoch_dir() -> Path:
    return Path(__file__).resolve().parent


def canonical_json_bytes(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_json_once(path: Path, value: Any) -> str:
    payload = canonical_json_bytes(value)
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_BINARY", 0)
    descriptor = os.open(path, flags)
    try:
        os.write(descriptor, payload)
    finally:
        os.close(descriptor)
    return hashlib.sha256(payload).hexdigest()


def raw_identity(subject: str, path: Path) -> dict[str, Any]:
    spec = SPECS[subject]
    identity = {
        "subject": subject,
        "asset_id": spec["asset_id"],
        "dandi_path": spec["path"],
        "local_path": str(path.resolve()),
        "size": path.stat().st_size,
        "sha256": sha256_file(path),
    }
    if identity["size"] != spec["size"] or identity["sha256"] != spec["sha256"]:
        raise RuntimeError(f"{STOP}: raw identity for {subject}")
    return identity


def decode_text(values: np.ndarray) -> np.ndarray:
    return np.asarray([value.decode() if isinstance(value, bytes) else str(value) for value in values])


def nearest_origins(timestamps: np.ndarray, start_times: np.ndarray) -> np.ndarray:
    right = np.clip(np.searchsorted(timestamps, start_times, side="left"), 1, len(timestamps) - 1)
    left = right - 1
    right_distance = np.abs(timestamps[right] - start_times)
    left_distance = np.abs(timestamps[left] - start_times)
    if np.any(np.isclose(right_distance, left_distance, rtol=0.0, atol=1e-12)):
        raise RuntimeError(f"{STOP}: non-unique nearest timestamp")
    origins = np.where(right_distance < left_distance, right, left)
    if np.any(np.abs(timestamps[origins] - start_times) > 0.5 / FS):
        raise RuntimeError(f"{STOP}: trial timing alignment")
    return origins.astype(np.int64)


def split_counts(ids: np.ndarray, states: np.ndarray, eligible: np.ndarray) -> dict[str, int]:
    return {
        f"{state}/{split}": int(np.sum(eligible & (states == state) & ((ids % 2) == parity)))
        for state in STATES
        for split, parity in (("development", 0), ("confirmation", 1))
    }


def read_schema(nwb: h5py.File, subject: str) -> dict[str, Any]:
    spec = SPECS[subject]
    required = (
        "/acquisition/ElectricalSeriesEEG/data",
        "/acquisition/ElectricalSeriesEEG/timestamps",
        "/acquisition/ElectricalSeriesEEG/electrodes",
        "/general/extracellular_ephys/electrodes/id",
        "/general/extracellular_ephys/electrodes/is_data_valid",
        "/intervals/trials/id", "/intervals/trials/start_time",
        "/intervals/trials/behavioral_epoch", "/intervals/trials/estim_current",
        "/intervals/trials/estim_target_region", "/intervals/trials/stimulus_description",
        "/intervals/trials/is_valid",
    )
    if any(path not in nwb for path in required):
        raise RuntimeError(f"{STOP}: required NWB path")
    data = nwb[required[0]]
    if data.shape != spec["shape"] or data.dtype != np.dtype("int16"):
        raise RuntimeError(f"{STOP}: EEG shape/dtype for {subject}")
    conversion = float(data.attrs.get("conversion", np.nan))
    if conversion != 1.9499999284744263e-07:
        raise RuntimeError(f"{STOP}: EEG conversion")
    timestamps = np.asarray(nwb[required[1]][...], dtype=np.float64)
    deltas = np.diff(timestamps)
    median_delta = float(np.median(deltas))
    if (
        timestamps.shape != (spec["shape"][0],)
        or not np.all(np.isfinite(timestamps))
        or np.any(deltas <= 0)
        or abs(1.0 / median_delta - FS) > 0.01
        or np.any(deltas > 1.5 * median_delta)
        or float(np.max(np.abs(deltas / median_delta - 1.0))) > 2.1e-5
    ):
        raise RuntimeError(f"{STOP}: timestamp profile for {subject}")
    electrode_ids = np.asarray(nwb[required[3]][...], dtype=np.int64)
    valid = np.asarray(nwb[required[4]][...], dtype=bool)
    if not np.array_equal(electrode_ids, np.arange(30)):
        raise RuntimeError(f"{STOP}: electrode IDs")
    if tuple(np.flatnonzero(valid).tolist()) != spec["valid_rows"]:
        raise RuntimeError(f"{STOP}: valid electrode rows")
    region = nwb[required[2]]
    table_ref = region.attrs.get("table")
    if table_ref is None or nwb[table_ref].name != "/general/extracellular_ephys/electrodes":
        raise RuntimeError(f"{STOP}: electrode table reference")
    series_rows = np.asarray(region[...], dtype=np.int64)
    if not np.array_equal(series_rows, np.arange(30)):
        raise RuntimeError(f"{STOP}: series electrode mapping")
    if not all(valid[index] for index in COMMON_CHANNELS):
        raise RuntimeError(f"{STOP}: common channel validity")

    trials = nwb["/intervals/trials"]
    ids = np.asarray(trials["id"][...], dtype=np.int64)
    start_times = np.asarray(trials["start_time"][...], dtype=np.float64)
    states = decode_text(trials["behavioral_epoch"][...])
    current_text = decode_text(trials["estim_current"][...])
    targets = decode_text(trials["estim_target_region"][...])
    descriptions = decode_text(trials["stimulus_description"][...])
    valid_trials = np.asarray(trials["is_valid"][...], dtype=bool)
    if not all(len(value) == 900 for value in (ids, start_times, states, current_text, targets, descriptions, valid_trials)):
        raise RuntimeError(f"{STOP}: trial table length")
    try:
        currents = current_text.astype(np.int64)
    except ValueError as error:
        raise RuntimeError(f"{STOP}: current encoding") from error
    eligible = (
        valid_trials & np.isin(states, STATES) & (currents == spec["current"])
        & (targets == "MOs") & (descriptions == "biphasic")
    )
    counts = split_counts(ids, states, eligible)
    if counts != spec["split_counts"]:
        raise RuntimeError(f"{STOP}: split counts for {subject}")
    origins = nearest_origins(timestamps, start_times)
    eligible_origins = origins[eligible]
    if np.any(eligible_origins - 2_500 < 0) or np.any(eligible_origins + 1_250 > len(timestamps)):
        raise RuntimeError(f"{STOP}: extraction boundary")
    return {
        "conversion": conversion,
        "eligible": eligible,
        "fs_hz": 1.0 / median_delta,
        "ids": ids,
        "origins": origins,
        "split_counts": counts,
        "states": states,
    }


def replace_artifacts(signal: np.ndarray, origins: np.ndarray) -> None:
    for origin in origins:
        signal[origin:origin + 5] = signal[origin - 5:origin]


def finish_waveforms(response: np.ndarray, baseline_mean: np.ndarray) -> np.ndarray:
    response = response - response.mean(axis=2, keepdims=True)
    baseline_car = baseline_mean - baseline_mean.mean(axis=1, keepdims=True)
    response = response - baseline_car[:, np.newaxis, :]
    if response.shape[1:] != (249, len(COMMON_CHANNELS)):
        raise RuntimeError(f"{STOP}: waveform shape")
    flat = response.reshape(len(response), -1)
    norms = np.linalg.norm(flat, axis=1)
    if not np.all(np.isfinite(flat)) or not np.all(np.isfinite(norms)) or np.any(norms <= 0):
        raise RuntimeError(f"{STOP}: waveform finite/norm")
    return flat


def extract_waveforms(nwb: h5py.File, schema: dict[str, Any]) -> tuple[np.ndarray, np.ndarray]:
    eligible_rows = np.flatnonzero(schema["eligible"])
    origins = schema["origins"][eligible_rows]
    data = nwb["/acquisition/ElectricalSeriesEEG/data"]
    response = np.empty((len(origins), 249, len(COMMON_CHANNELS)), dtype=np.float64)
    baseline = np.empty((len(origins), len(COMMON_CHANNELS)), dtype=np.float64)
    filter_sos = butter(3, (0.1, 100.0), btype="bandpass", fs=FS, output="sos")
    for output_channel, source_channel in enumerate(COMMON_CHANNELS):
        continuous = np.asarray(data[:, source_channel], dtype=np.float64)
        replace_artifacts(continuous, origins)
        continuous *= schema["conversion"] * 1e6
        continuous = sosfiltfilt(filter_sos, continuous)
        for trial_index, origin in enumerate(origins):
            baseline[trial_index, output_channel] = float(np.mean(continuous[origin - 1_250:origin - 25]))
            response[trial_index, :, output_channel] = continuous[origin + 5:origin + 1_250:5]
    return finish_waveforms(response, baseline), eligible_rows


def normalized_distance(first: np.ndarray, second: np.ndarray) -> float:
    return float(np.linalg.norm(first.mean(axis=0) - second.mean(axis=0)))


def gain_residual(awake: np.ndarray, isoflurane: np.ndarray) -> tuple[float, float]:
    awake_mean = awake.mean(axis=0)
    iso_mean = isoflurane.mean(axis=0)
    denominator = float(awake_mean @ awake_mean)
    iso_norm = float(np.linalg.norm(iso_mean))
    if denominator <= 0 or iso_norm <= 0:
        raise RuntimeError(f"{STOP}: mean waveform norm")
    gain = max(0.0, float((iso_mean @ awake_mean) / denominator))
    residual = float(np.linalg.norm(iso_mean - gain * awake_mean) / iso_norm)
    return gain, residual


def permutation_p(awake: np.ndarray, isoflurane: np.ndarray, seed: int) -> tuple[float, int]:
    observed = normalized_distance(awake, isoflurane)
    pooled = np.concatenate((awake, isoflurane), axis=0)
    rng = np.random.Generator(np.random.PCG64(seed))
    exceedances = 0
    for _ in range(999):
        order = rng.permutation(len(pooled))
        permuted = normalized_distance(pooled[order[:len(awake)]], pooled[order[len(awake):]])
        exceedances += permuted >= observed
    return (1 + exceedances) / 1000.0, exceedances


def bootstrap_q(awake: np.ndarray, isoflurane: np.ndarray, recovery: np.ndarray, seed: int) -> tuple[float, float]:
    d_ai = normalized_distance(awake, isoflurane)
    d_ar = normalized_distance(awake, recovery)
    if d_ai <= 0:
        raise RuntimeError(f"{STOP}: zero awake/isoflurane distance")
    observed = d_ar / d_ai
    rng = np.random.Generator(np.random.PCG64(seed))
    samples = np.empty(1_999, dtype=np.float64)
    for index in range(len(samples)):
        a = awake[rng.integers(0, len(awake), len(awake))]
        i = isoflurane[rng.integers(0, len(isoflurane), len(isoflurane))]
        r = recovery[rng.integers(0, len(recovery), len(recovery))]
        denominator = normalized_distance(a, i)
        samples[index] = normalized_distance(a, r) / denominator if denominator > 0 else np.nan
    if not np.all(np.isfinite(samples)):
        raise RuntimeError(f"{STOP}: bootstrap ratio")
    return float(observed), float(np.percentile(samples, 97.5))


def registered_pass_flags(p_value: float, residual: float, q: float, q_upper: float) -> tuple[bool, bool]:
    state_pass = p_value <= 0.01 and residual >= 0.10
    recovery_pass = q <= 0.75 and q_upper < 1.0
    return state_pass, recovery_pass


def subject_metrics(subject: str, raw_waveforms: dict[str, np.ndarray]) -> dict[str, Any]:
    unit = {state: values / np.linalg.norm(values, axis=1, keepdims=True) for state, values in raw_waveforms.items()}
    d_ai = normalized_distance(unit["awake"], unit["isoflurane"])
    d_ar = normalized_distance(unit["awake"], unit["recovery"])
    gain, residual = gain_residual(raw_waveforms["awake"], raw_waveforms["isoflurane"])
    p_value, exceedances = permutation_p(unit["awake"], unit["isoflurane"], 20_260_828 + int(subject))
    q, q_upper = bootstrap_q(unit["awake"], unit["isoflurane"], unit["recovery"], 20_261_828 + int(subject))
    state_pass, recovery_pass = registered_pass_flags(p_value, residual, q, q_upper)
    return {
        "subject": subject,
        "current_microampere": SPECS[subject]["current"],
        "confirmation_counts": {state: len(raw_waveforms[state]) for state in STATES},
        "D_AI": d_ai, "D_AR": d_ar, "Q": q, "Q_upper_97_5": q_upper,
        "gain_AI": gain, "R_AI": residual, "p_AI": p_value,
        "permutation_exceedances": exceedances,
        "state_pass": state_pass, "recovery_pass": recovery_pass,
    }


def decide(metrics: list[dict[str, Any]]) -> str:
    if len(metrics) != 2:
        raise RuntimeError(f"{STOP}: subject count")
    if all(item["state_pass"] and item["recovery_pass"] for item in metrics):
        return "STAGE2_RECOVERY_REPLICATION_SUPPORTED"
    if all(item["state_pass"] for item in metrics) and any(item["Q"] < 1.0 for item in metrics):
        return "STAGE2_RECOVERY_REPLICATION_TENSION"
    return "STAGE2_RECOVERY_NOT_ESTABLISHED"


def verify_file_map(files: dict[str, str]) -> None:
    if set(files) != set(PREREGISTERED_FILES):
        raise RuntimeError(f"{STOP}: manifest file set")
    for relative, expected in files.items():
        path = epoch_dir() / relative
        if not path.is_file() or sha256_file(path) != expected:
            raise RuntimeError(f"{STOP}: preregistration mutation: {relative}")


def seal_manifest(raw_paths: dict[str, Path]) -> dict[str, Any]:
    files = {relative: sha256_file(epoch_dir() / relative) for relative in PREREGISTERED_FILES}
    raw = {subject: raw_identity(subject, raw_paths[subject]) for subject in sorted(SPECS)}
    manifest = {"confirmation_eeg_opened": False, "files": files, "raw": raw}
    digest = write_json_once(epoch_dir() / MANIFEST, manifest)
    return {"manifest_sha256": digest, **manifest}


def verify_manifest(raw_paths: dict[str, Path]) -> tuple[dict[str, Any], str]:
    path = epoch_dir() / MANIFEST
    if not path.is_file():
        raise RuntimeError(f"{STOP}: manifest missing")
    manifest = json.loads(path.read_text(encoding="utf-8"))
    if manifest.get("confirmation_eeg_opened") is not False:
        raise RuntimeError(f"{STOP}: manifest open state")
    verify_file_map(manifest.get("files", {}))
    actual = {subject: raw_identity(subject, raw_paths[subject]) for subject in sorted(SPECS)}
    if manifest.get("raw") != actual:
        raise RuntimeError(f"{STOP}: manifest raw identity")
    return manifest, sha256_file(path)


def compute_result(raw_paths: dict[str, Path]) -> dict[str, Any]:
    _, manifest_sha = verify_manifest(raw_paths)
    metrics = []
    schemas = {}
    for subject in sorted(SPECS):
        with h5py.File(raw_paths[subject], "r") as nwb:
            schema = read_schema(nwb, subject)
            waveforms, eligible_rows = extract_waveforms(nwb, schema)
        confirmation = schema["ids"][eligible_rows] % 2 == 1
        groups = {
            state: waveforms[confirmation & (schema["states"][eligible_rows] == state)]
            for state in STATES
        }
        metrics.append(subject_metrics(subject, groups))
        schemas[subject] = {
            "fs_hz": schema["fs_hz"],
            "split_counts": schema["split_counts"],
            "waveform_shape": [249, len(COMMON_CHANNELS)],
        }
    return {
        "schema": "ce.stage2.multianimal-recovery-result.v1",
        "manifest_sha256": manifest_sha,
        "decision": decide(metrics),
        "subjects": metrics,
        "schemas": schemas,
        "claim_ceiling": "two-animal within-subject EEG recovery association; no geometry or anatomy claim",
    }


def execute(raw_paths: dict[str, Path]) -> dict[str, Any]:
    result = compute_result(raw_paths)
    digest = write_json_once(epoch_dir() / RESULT, result)
    return {"result_sha256": digest, **result}


def verify_result(raw_paths: dict[str, Path]) -> dict[str, Any]:
    result_path = epoch_dir() / RESULT
    if not result_path.is_file():
        raise RuntimeError(f"{STOP}: result missing")
    expected = result_path.read_bytes()
    recomputed = canonical_json_bytes(compute_result(raw_paths))
    if expected != recomputed:
        raise RuntimeError(f"{STOP}: result recomputation mismatch")
    receipt = {
        "schema": "ce.stage2.multianimal-recovery-validation.v1",
        "manifest_sha256": sha256_file(epoch_dir() / MANIFEST),
        "result_sha256": hashlib.sha256(expected).hexdigest(),
        "raw_recomputed": True,
    }
    digest = write_json_once(epoch_dir() / VALIDATION, receipt)
    return {"validation_sha256": digest, **receipt}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw-543393", type=Path, required=True)
    parser.add_argument("--raw-543394", type=Path, required=True)
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--seal", action="store_true")
    action.add_argument("--execute", action="store_true")
    action.add_argument("--verify-result", action="store_true")
    args = parser.parse_args()
    raw_paths = {"543393": args.raw_543393, "543394": args.raw_543394}
    if args.seal:
        output = seal_manifest(raw_paths)
    elif args.execute:
        output = execute(raw_paths)
    else:
        output = verify_result(raw_paths)
    print(json.dumps(output, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
