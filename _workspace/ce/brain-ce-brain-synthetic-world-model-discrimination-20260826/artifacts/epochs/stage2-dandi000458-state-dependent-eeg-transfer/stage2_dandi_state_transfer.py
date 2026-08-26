"""Sealed Stage 2 DANDI EEG state-associated transfer experiment."""

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


STOP = "STAGE2_APPARATUS_STOP"
FS = 2_500.0
VALID_CHANNELS = (0, 1, 2, 3, 4, 5, 9, 19, 20, 22, 23, 24, 25, 26, 27, 28, 29)
CURRENTS = (20, 50, 100)
STATES = ("awake", "isoflurane")
RAW_BYTES = 312_139_546
RAW_SHA256 = "b80cd3a375ead36c05c451f562e92947573cd0679a30ffd573a04e44339b0171"
SCHEMA_RECEIPT = "stage2-schema-receipt.json"
MANIFEST = "stage2-manifest.json"
RESULT = "stage2-result.json"
VALIDATION_RECEIPT = "stage2-validation-receipt.json"
EXPECTED_SPLIT_COUNTS = {
    "awake/20/development": 30, "awake/20/confirmation": 30,
    "awake/50/development": 33, "awake/50/confirmation": 27,
    "awake/100/development": 27, "awake/100/confirmation": 33,
    "isoflurane/20/development": 30, "isoflurane/20/confirmation": 30,
    "isoflurane/50/development": 32, "isoflurane/50/confirmation": 27,
    "isoflurane/100/development": 24, "isoflurane/100/confirmation": 31,
}
PREREGISTERED_FILES = (
    "00-contract.md", "10-data-lock.md", "10-sources.md", "20-hypotheses.md",
    "20-audit.md", "21-preexecution-validation.md", "30-models.md", "40-metrics.md",
    "50-gates.md", "60-negative-controls.md", "probe_remote_schema.py",
    "schema-receipt.json", "stage2_dandi_state_transfer.py",
    "test_stage2_dandi_state_transfer.py", "timestamp-gap-apparatus-amendment.md",
    SCHEMA_RECEIPT,
)


def pivot_dir() -> Path:
    return Path(__file__).resolve().parent


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
    payload = canonical_json_bytes(value)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    temporary.write_bytes(payload)
    temporary.replace(path)
    return hashlib.sha256(payload).hexdigest()


def raw_identity(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise RuntimeError(f"{STOP}: raw file missing")
    size, digest = path.stat().st_size, sha256_file(path)
    if size != RAW_BYTES or digest != RAW_SHA256:
        raise RuntimeError(f"{STOP}: raw identity mismatch")
    return {"bytes": size, "filename": path.name, "sha256": digest}


def decode_text(values: np.ndarray) -> np.ndarray:
    return np.asarray([item.decode() if isinstance(item, bytes) else str(item) for item in values])


def nearest_origins(timestamps: np.ndarray, start_times: np.ndarray) -> np.ndarray:
    right = np.clip(np.searchsorted(timestamps, start_times, side="left"), 1, len(timestamps) - 1)
    left = right - 1
    right_distance = np.abs(timestamps[right] - start_times)
    left_distance = np.abs(timestamps[left] - start_times)
    if np.any(np.isclose(right_distance, left_distance, rtol=0.0, atol=1e-12)):
        raise RuntimeError(f"{STOP}: non-unique nearest trial timestamp")
    choose_right = right_distance < left_distance
    origins = np.where(choose_right, right, left)
    if np.any(np.abs(timestamps[origins] - start_times) > 0.5 / FS):
        raise RuntimeError(f"{STOP}: trial timing alignment")
    return origins.astype(np.int64)


def valid_series_columns(
    series_rows: np.ndarray,
    electrode_valid: np.ndarray,
    table_name: str,
) -> tuple[int, ...]:
    if table_name != "/general/extracellular_ephys/electrodes":
        raise RuntimeError(f"{STOP}: ElectricalSeries electrode table reference")
    if series_rows.shape != (30,) or len(np.unique(series_rows)) != 30:
        raise RuntimeError(f"{STOP}: ElectricalSeries electrode row mapping")
    if np.any(series_rows < 0) or np.any(series_rows >= len(electrode_valid)):
        raise RuntimeError(f"{STOP}: ElectricalSeries electrode row range")
    columns = tuple(np.flatnonzero(electrode_valid[series_rows]).tolist())
    if columns != VALID_CHANNELS:
        raise RuntimeError(f"{STOP}: valid ElectricalSeries channel columns")
    return columns


def validate_timestamp_profile(timestamps: np.ndarray) -> tuple[float, int]:
    if not np.all(np.isfinite(timestamps)):
        raise RuntimeError(f"{STOP}: timestamps")
    deltas = np.diff(timestamps)
    median_delta = float(np.median(deltas))
    gap_indices = np.flatnonzero(deltas > 1.5 * median_delta)
    if (np.any(deltas <= 0) or abs(1 / median_delta - FS) > 0.01
            or gap_indices.tolist() != [125_307]
            or not 1.9999 <= deltas[125_307] / median_delta <= 2.0001):
        raise RuntimeError(f"{STOP}: timestamp rate or uniformity")
    ordinary = np.delete(deltas, 125_307)
    if float(np.max(np.abs(ordinary / median_delta - 1))) > 2e-5:
        raise RuntimeError(f"{STOP}: ordinary timestamp jitter")
    return median_delta, 125_308


def split_counts(ids: np.ndarray, states: np.ndarray, currents: np.ndarray, eligible: np.ndarray) -> dict[str, int]:
    result = {}
    for state in STATES:
        for current in CURRENTS:
            for split, parity in (("development", 0), ("confirmation", 1)):
                result[f"{state}/{current}/{split}"] = int(np.sum(
                    eligible & (states == state) & (currents == current) & ((ids % 2) == parity)
                ))
    return result


def read_schema(nwb: h5py.File, *, confirmation_values_opened: bool) -> dict[str, Any]:
    required = (
        "/acquisition/ElectricalSeriesEEG/data", "/acquisition/ElectricalSeriesEEG/timestamps",
        "/general/extracellular_ephys/electrodes/id",
        "/general/extracellular_ephys/electrodes/is_data_valid", "/intervals/trials/id",
        "/acquisition/ElectricalSeriesEEG/electrodes",
        "/intervals/trials/start_time", "/intervals/trials/behavioral_epoch",
        "/intervals/trials/estim_current", "/intervals/trials/estim_target_region",
        "/intervals/trials/stimulus_description", "/intervals/trials/is_valid",
    )
    if any(path not in nwb for path in required):
        raise RuntimeError(f"{STOP}: required NWB path missing")
    data = nwb[required[0]]
    timestamps = np.asarray(nwb[required[1]][...], dtype=np.float64)
    conversion = float(data.attrs.get("conversion", np.nan))
    if data.shape != (6_217_728, 30) or data.dtype != np.dtype("int16"):
        raise RuntimeError(f"{STOP}: EEG shape or dtype")
    if conversion != 1.9499999284744263e-07:
        raise RuntimeError(f"{STOP}: EEG conversion")
    if timestamps.shape != (6_217_728,):
        raise RuntimeError(f"{STOP}: timestamps")
    median_delta, continuous_segment_start = validate_timestamp_profile(timestamps)
    electrode_ids = np.asarray(nwb[required[2]][...], dtype=np.int64)
    electrode_valid = np.asarray(nwb[required[3]][...], dtype=bool)
    if electrode_ids.shape != (30,) or not np.array_equal(electrode_ids, np.arange(30)):
        raise RuntimeError(f"{STOP}: electrode table IDs")
    series_region = nwb["/acquisition/ElectricalSeriesEEG/electrodes"]
    table_reference = series_region.attrs.get("table")
    if table_reference is None:
        raise RuntimeError(f"{STOP}: ElectricalSeries electrode table reference")
    series_columns = valid_series_columns(
        np.asarray(series_region[...], dtype=np.int64),
        electrode_valid,
        nwb[table_reference].name,
    )
    trials = nwb["/intervals/trials"]
    ids = np.asarray(trials["id"][...], dtype=np.int64)
    start_times = np.asarray(trials["start_time"][...], dtype=np.float64)
    states = decode_text(trials["behavioral_epoch"][...])
    current_text = decode_text(trials["estim_current"][...])
    targets = decode_text(trials["estim_target_region"][...])
    descriptions = decode_text(trials["stimulus_description"][...])
    valid_trials = np.asarray(trials["is_valid"][...], dtype=bool)
    if not all(len(value) == 360 for value in (ids, start_times, states, current_text, targets, descriptions, valid_trials)):
        raise RuntimeError(f"{STOP}: trial table length")
    try:
        currents = current_text.astype(np.int64)
    except ValueError as error:
        raise RuntimeError(f"{STOP}: current encoding") from error
    origins = nearest_origins(timestamps, start_times)
    eligible = (valid_trials & np.isin(states, STATES) & np.isin(currents, CURRENTS)
                & (targets == "MOs") & (descriptions == "biphasic"))
    counts = split_counts(ids, states, currents, eligible)
    if counts != EXPECTED_SPLIT_COUNTS:
        raise RuntimeError(f"{STOP}: registered split counts")
    eligible_origins = origins[eligible]
    if (timestamps[eligible_origins].min() - timestamps[continuous_segment_start] < 120.0
            or np.any(eligible_origins - 2_500 < continuous_segment_start)
            or np.any(eligible_origins + 1_250 > len(timestamps))):
        raise RuntimeError(f"{STOP}: extraction boundary")
    return {
        "confirmation_values_opened": confirmation_values_opened,
        "continuous_segment_start": continuous_segment_start,
        "conversion_volts_per_count": conversion, "eeg_dtype": "int16",
        "eeg_shape": list(data.shape), "eligible_mask": eligible, "fs_hz": 1 / median_delta,
        "origins": origins, "split_counts": counts, "timestamp_count": len(timestamps),
        "trial_currents": currents, "trial_ids": ids, "trial_states": states,
        "valid_channels": list(series_columns),
    }


def public_schema_receipt(schema: dict[str, Any]) -> dict[str, Any]:
    private = {"eligible_mask", "origins", "trial_currents", "trial_ids", "trial_states"}
    return {key: value for key, value in schema.items() if key not in private}


def create_schema_receipt(raw_path: Path, *, pivot: Path | None = None) -> dict[str, Any]:
    target, identity = pivot_dir() if pivot is None else pivot, raw_identity(raw_path)
    with h5py.File(raw_path, "r") as nwb:
        schema = read_schema(nwb, confirmation_values_opened=False)
    receipt = {"raw": identity, "schema": public_schema_receipt(schema)}
    return {"receipt_sha256": write_json_once(target / SCHEMA_RECEIPT, receipt), **receipt}


def verify_file_map(pivot: Path, files: dict[str, str]) -> None:
    if set(files) != set(PREREGISTERED_FILES):
        raise RuntimeError(f"{STOP}: manifest file set")
    for relative, expected in files.items():
        path = pivot / relative
        if not path.is_file() or sha256_file(path) != expected:
            raise RuntimeError(f"{STOP}: preregistration mutation")


def seal_manifest(raw_path: Path, *, pivot: Path | None = None) -> dict[str, Any]:
    target = pivot_dir() if pivot is None else pivot
    schema_path = target / SCHEMA_RECEIPT
    if not schema_path.is_file():
        raise RuntimeError(f"{STOP}: schema receipt missing")
    identity = raw_identity(raw_path)
    if json.loads(schema_path.read_text())["raw"] != identity:
        raise RuntimeError(f"{STOP}: schema/raw identity")
    files = {}
    for relative in PREREGISTERED_FILES:
        path = target / relative
        if not path.is_file():
            raise RuntimeError(f"{STOP}: preregistered file missing: {relative}")
        files[relative] = sha256_file(path)
    manifest = {"confirmation_values_opened": False, "files": files, "raw": identity,
                "schema_receipt_sha256": sha256_file(schema_path)}
    return {"manifest_sha256": write_json_once(target / MANIFEST, manifest), **manifest}


def verify_manifest(raw_path: Path, *, pivot: Path | None = None) -> tuple[dict[str, Any], str]:
    target = pivot_dir() if pivot is None else pivot
    manifest_path = target / MANIFEST
    if not manifest_path.is_file():
        raise RuntimeError(f"{STOP}: manifest missing")
    manifest = json.loads(manifest_path.read_text())
    if manifest.get("confirmation_values_opened") is not False or manifest.get("raw") != raw_identity(raw_path):
        raise RuntimeError(f"{STOP}: manifest identity/state")
    if manifest.get("schema_receipt_sha256") != sha256_file(target / SCHEMA_RECEIPT):
        raise RuntimeError(f"{STOP}: schema receipt mutation")
    verify_file_map(target, manifest.get("files", {}))
    return manifest, sha256_file(manifest_path)


def replace_artifacts(signal: np.ndarray, origins: np.ndarray) -> None:
    for origin in origins:
        signal[origin:origin + 5] = signal[origin - 5:origin]


def finish_waveforms(response: np.ndarray, baseline_mean: np.ndarray) -> np.ndarray:
    response = response - response.mean(axis=2, keepdims=True)
    baseline_car = baseline_mean - baseline_mean.mean(axis=1, keepdims=True)
    response = response - baseline_car[:, np.newaxis, :]
    if response.shape[1:] != (249, 17):
        raise RuntimeError(f"{STOP}: waveform shape")
    norms = np.linalg.norm(response.reshape(len(response), -1), axis=1)
    if not np.all(np.isfinite(response)) or not np.all(np.isfinite(norms)) or np.any(norms <= 0):
        raise RuntimeError(f"{STOP}: waveform finite/norm")
    return response


def extract_waveforms(nwb: h5py.File, schema: dict[str, Any]) -> tuple[np.ndarray, np.ndarray]:
    eligible = schema["eligible_mask"]
    origins = schema["origins"][eligible]
    segment_start = schema["continuous_segment_start"]
    relative_origins = origins - segment_start
    data = nwb["/acquisition/ElectricalSeriesEEG/data"]
    response = np.empty((len(origins), 249, 17), dtype=np.float64)
    baseline_mean = np.empty((len(origins), 17), dtype=np.float64)
    filter_sos = butter(3, (0.1, 100.0), btype="bandpass", fs=FS, output="sos")
    for output_channel, source_channel in enumerate(schema["valid_channels"]):
        continuous = np.asarray(data[segment_start:, source_channel], dtype=np.float64)
        replace_artifacts(continuous, relative_origins)
        continuous *= schema["conversion_volts_per_count"] * 1e6
        continuous = sosfiltfilt(filter_sos, continuous)
        for trial_index, origin in enumerate(relative_origins):
            baseline_mean[trial_index, output_channel] = float(np.mean(continuous[origin - 1_250:origin - 25]))
            response[trial_index, :, output_channel] = continuous[origin + 5:origin + 1_250:5]
    return finish_waveforms(response, baseline_mean), np.flatnonzero(eligible)


def confirmation_groups(waveforms: np.ndarray, eligible_rows: np.ndarray, schema: dict[str, Any]) -> dict[int, dict[str, np.ndarray]]:
    ids, states, currents = (schema["trial_ids"][eligible_rows], schema["trial_states"][eligible_rows],
                              schema["trial_currents"][eligible_rows])
    return {current: {state: waveforms[(ids % 2 == 1) & (states == state) & (currents == current)]
                      for state in STATES} for current in CURRENTS}


def current_statistics(awake: np.ndarray, isoflurane: np.ndarray, current: int) -> dict[str, Any]:
    if len(awake) < 20 or len(isoflurane) < 20:
        raise RuntimeError(f"{STOP}: confirmation trial count")
    awake_flat, iso_flat = awake.reshape(len(awake), -1), isoflurane.reshape(len(isoflurane), -1)
    awake_norms, iso_norms = np.linalg.norm(awake_flat, axis=1), np.linalg.norm(iso_flat, axis=1)
    if (not np.all(np.isfinite(awake_norms)) or not np.all(np.isfinite(iso_norms))
            or np.any(awake_norms <= 0) or np.any(iso_norms <= 0)):
        raise RuntimeError(f"{STOP}: trial waveform norm")
    awake_mean, iso_mean = awake_flat.mean(axis=0), iso_flat.mean(axis=0)
    awake_mean_sq, iso_mean_sq = float(awake_mean @ awake_mean), float(iso_mean @ iso_mean)
    if not np.isfinite(awake_mean_sq + iso_mean_sq) or awake_mean_sq <= 0 or iso_mean_sq <= 0:
        raise RuntimeError(f"{STOP}: state mean waveform norm")
    alpha = max(0.0, float((iso_mean @ awake_mean) / awake_mean_sq))
    residual = float(np.linalg.norm(iso_mean - alpha * awake_mean) / np.sqrt(iso_mean_sq))
    awake_unit, iso_unit = awake_flat / awake_norms[:, None], iso_flat / iso_norms[:, None]
    distance = float(np.linalg.norm(iso_unit.mean(0) - awake_unit.mean(0)))
    pooled = np.concatenate((awake_unit, iso_unit))
    rng, exceedances = np.random.Generator(np.random.PCG64(20_260_827 + current)), 0
    for _ in range(999):
        order = rng.permutation(len(pooled))
        permuted_distance = float(np.linalg.norm(
            pooled[order[len(awake_unit):]].mean(0) - pooled[order[:len(awake_unit)]].mean(0)))
        exceedances += int(permuted_distance >= distance)
    return {"D_trial_normalized_waveform": distance, "R_mean_waveform_gain_residual": residual,
            "alpha_nonnegative_global_gain": alpha, "awake_confirmation_trials": len(awake),
            "isoflurane_confirmation_trials": len(isoflurane),
            "permutation_exceedances": exceedances, "permutation_p": (1 + exceedances) / 1000,
            "permutations": 999}


def decide(metrics: dict[int, dict[str, Any]]) -> str:
    p = [metrics[current]["permutation_p"] for current in CURRENTS]
    r = [metrics[current]["R_mean_waveform_gain_residual"] for current in CURRENTS]
    if all(value <= .05 for value in p) and sum(p[i] <= .01 and r[i] >= .10 for i in range(3)) >= 2:
        return "STAGE2_STATE_ASSOCIATED_TRANSFER_DIFFERENCE"
    if all(value > .05 for value in p) and all(value < .10 for value in r):
        return "STAGE2_GLOBAL_GAIN_COMPATIBLE_AT_REGISTERED_RESOLUTION"
    return "STAGE2_TRANSFER_TENSION"


def descriptive_channels(waveforms: np.ndarray) -> list[dict[str, Any]]:
    mean_waveform, output = waveforms.mean(0), []
    for index, channel in enumerate(VALID_CHANNELS):
        trace = mean_waveform[:, index]
        peak = int(np.argmax(np.abs(trace)))
        output.append({"channel_id": channel,
                       "integrated_absolute_uv_seconds": float(np.sum(np.abs(trace)) / 500),
                       "signed_peak_uv": float(trace[peak]), "peak_latency_ms": float(2 + 2 * peak)})
    return output


def validate_result(result: dict[str, Any]) -> None:
    metrics = {int(key): value for key, value in result["confirmation_metrics"].items()}
    if set(metrics) != set(CURRENTS) or result["decision"] != decide(metrics):
        raise RuntimeError(f"{STOP}: result decision")
    for row in metrics.values():
        numeric = (row["D_trial_normalized_waveform"], row["R_mean_waveform_gain_residual"],
                   row["alpha_nonnegative_global_gain"], row["permutation_p"])
        if not all(np.isfinite(value) for value in numeric) or not 0 < row["permutation_p"] <= 1:
            raise RuntimeError(f"{STOP}: result metric")


def compute_result(raw_path: Path, *, pivot: Path | None = None) -> dict[str, Any]:
    target = pivot_dir() if pivot is None else pivot
    _, manifest_sha = verify_manifest(raw_path, pivot=target)
    with h5py.File(raw_path, "r") as nwb:
        schema = read_schema(nwb, confirmation_values_opened=True)
        waveforms, eligible_rows = extract_waveforms(nwb, schema)
    groups = confirmation_groups(waveforms, eligible_rows, schema)
    metrics = {current: current_statistics(groups[current]["awake"], groups[current]["isoflurane"], current)
               for current in CURRENTS}
    return {
        "claim_ceiling": "one-session one-animal EEG-only L3 state-associated perturbational result",
        "confirmation_metrics": {str(current): metrics[current] for current in CURRENTS},
        "decision": decide(metrics),
        "descriptive_channels": {str(current): {state: descriptive_channels(groups[current][state])
                                                  for state in STATES} for current in CURRENTS},
        "manifest_sha256": manifest_sha, "raw": raw_identity(raw_path), "response_dimension": 4_233,
        "response_shape": [249, 17], "schema": public_schema_receipt(schema), "stage3_authorized": False,
    }


def execute(raw_path: Path, *, pivot: Path | None = None) -> dict[str, Any]:
    target = pivot_dir() if pivot is None else pivot
    if (target / RESULT).exists():
        raise RuntimeError(f"{STOP}: refusing to overwrite {RESULT}")
    result = compute_result(raw_path, pivot=target)
    validate_result(result)
    result_sha = write_json_once(target / RESULT, result)
    stored = json.loads((target / RESULT).read_text())
    validate_result(stored)
    if sha256_file(target / RESULT) != result_sha:
        raise RuntimeError(f"{STOP}: result write verification")
    return {"result_sha256": result_sha, **result}


def verify_result_from_raw(raw_path: Path, *, pivot: Path | None = None) -> dict[str, Any]:
    target = pivot_dir() if pivot is None else pivot
    result_path = target / RESULT
    if not result_path.is_file():
        raise RuntimeError(f"{STOP}: result missing")
    stored = json.loads(result_path.read_text())
    validate_result(stored)
    recomputed = compute_result(raw_path, pivot=target)
    validate_result(recomputed)
    if canonical_json_bytes(stored) != canonical_json_bytes(recomputed):
        raise RuntimeError(f"{STOP}: raw result recomputation mismatch")
    receipt = {
        "decision": stored["decision"],
        "manifest_sha256": stored["manifest_sha256"],
        "raw_sha256": stored["raw"]["sha256"],
        "recomputed_from_raw": True,
        "result_sha256": sha256_file(result_path),
        "status": "PASS",
    }
    receipt_sha = write_json_once(target / VALIDATION_RECEIPT, receipt)
    return {"validation_receipt_sha256": receipt_sha, **receipt}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--nwb", type=Path, required=True)
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--schema-only", action="store_true")
    modes.add_argument("--seal", action="store_true")
    modes.add_argument("--execute", action="store_true")
    modes.add_argument("--verify-result", action="store_true")
    arguments = parser.parse_args()
    if arguments.schema_only:
        output = create_schema_receipt(arguments.nwb)
    elif arguments.seal:
        output = seal_manifest(arguments.nwb)
    elif arguments.execute:
        output = execute(arguments.nwb)
    else:
        output = verify_result_from_raw(arguments.nwb)
    print(json.dumps(output, sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()
