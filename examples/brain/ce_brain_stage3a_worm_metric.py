"""Preregistered CE-BRAIN Stage 3A representation competition on DANDI 001075."""

from __future__ import annotations

import argparse
import hashlib
import heapq
import json
import math
import os
import platform
import re
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable

import h5py
import numpy as np
import scipy
from scipy.optimize import minimize
from scipy.special import expit


STOP = "STAGE3A_APPARATUS_STOP"
ROOT = Path(__file__).resolve().parents[2]
CONTRACT = ROOT / "paper" / "검증_원장" / "CE_BRAIN_STAGE3A_선충_간선표현_계약.md"
TEST_FILE = ROOT / "tests" / "test_ce_brain_stage3a_worm_metric.py"
INVENTORY_NAME = "download-inventory.json"
SCHEMA_RECEIPT = "stage3a-schema-receipt.json"
MANIFEST = "stage3a-manifest.json"
RESULT = "stage3a-result.json"
VALIDATION = "stage3a-validation-receipt.json"
EXPECTED_INVENTORY_SHA = "31c9501592dc10b9a176f12124a77e7bbdfc06d2bf43fab97874526af5d7fcfc"
EXPECTED_FILES = 110
EXPECTED_BYTES = 1_700_529_616
BOOTSTRAPS = 1_999
SEED = 20_260_905
RIDGES = (1e-4, 1e-3, 1e-2, 1e-1, 1.0)
RFF_DIM = 64
EXPECTED_RUNTIME = {
    "implementation": "CPython",
    "python": "3.11.9",
    "numpy": "2.4.6",
    "scipy": "1.17.1",
    "h5py": "3.16.0",
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


def runtime_identity() -> dict[str, str]:
    return {
        "implementation": platform.python_implementation(),
        "python": platform.python_version(),
        "numpy": np.__version__,
        "scipy": scipy.__version__,
        "h5py": h5py.__version__,
        "executable": str(Path(sys.executable).resolve()),
    }


def verify_runtime() -> dict[str, str]:
    identity = runtime_identity()
    if any(identity.get(key) != value for key, value in EXPECTED_RUNTIME.items()):
        raise RuntimeError(f"{STOP}: runtime identity")
    return identity


def text(value: Any) -> str:
    return value.decode(errors="replace").strip() if isinstance(value, bytes) else str(value).strip()


def subject_id(path: Path) -> int:
    match = re.search(r"sub-(\d+)_", path.name)
    if not match:
        raise RuntimeError(f"{STOP}: subject filename {path.name}")
    return int(match.group(1))


def subject_development(subject: int) -> bool:
    token = f"CE-BRAIN-STAGE3A-20260905|{subject}".encode()
    return int(hashlib.sha256(token).hexdigest()[:8], 16) % 10 < 7


def source_holdout(label: str) -> bool:
    token = f"CE-BRAIN-STAGE3A-SOURCE-20260905|{label}".encode()
    return int(hashlib.sha256(token).hexdigest()[:8], 16) % 5 == 0


def load_inventory(data_dir: Path, *, hash_raw: bool) -> tuple[dict[str, Any], list[Path]]:
    inventory_path = data_dir / INVENTORY_NAME
    if not inventory_path.is_file() or sha256_file(inventory_path) != EXPECTED_INVENTORY_SHA:
        raise RuntimeError(f"{STOP}: inventory identity")
    inventory = json.loads(inventory_path.read_text(encoding="utf-8"))
    assets = inventory.get("assets", [])
    if (inventory.get("dandiset") != "001075" or inventory.get("version") != "0.240930.1859"
            or len(assets) != EXPECTED_FILES or inventory.get("total_bytes") != EXPECTED_BYTES):
        raise RuntimeError(f"{STOP}: inventory schema")
    paths: list[Path] = []
    for row in assets:
        path = data_dir / row["filename"]
        if not path.is_file() or path.stat().st_size != row["bytes"]:
            raise RuntimeError(f"{STOP}: asset size {path.name}")
        if hash_raw and sha256_file(path) != row["sha256"]:
            raise RuntimeError(f"{STOP}: asset hash {path.name}")
        paths.append(path)
    return inventory, sorted(paths, key=subject_id)


def canonical_map(nwb: h5py.File) -> tuple[dict[int, str], dict[int, np.ndarray]]:
    pump = nwb["processing/ophys/PumpProbeGreenSegmentations/PumpProbeGreenPlaneSegmentation"]
    neuropal = nwb["processing/ophys/NeuroPALSegmentations/NeuroPALPlaneSegmentation"]
    labels = np.asarray(neuropal["labels"][...])
    receiver_ids = np.asarray(pump["id"][...], dtype=np.int64)
    references = np.asarray(pump["neuropal_ids"][...])
    centroids = np.asarray(pump["centroids"][...], dtype=np.float64)
    if centroids.shape != (len(receiver_ids), 3):
        raise RuntimeError(f"{STOP}: centroid shape")
    names: dict[int, str] = {}
    coords: dict[int, np.ndarray] = {}
    for receiver, reference, coordinate in zip(receiver_ids, references, centroids, strict=True):
        raw = text(reference)
        if not re.fullmatch(r"\d+", raw):
            continue
        index = int(raw)
        if index >= len(labels):
            # A few source files contain legacy/merged reference tokens that do
            # not point to a row in the converted NeuroPAL table. They fail the
            # preregistered single valid integer-reference gate and are excluded.
            continue
        label = text(labels[index])
        if not label or not re.search(r"[A-Za-z]", label):
            continue
        names[int(receiver)] = label
        coords[int(receiver)] = coordinate
    return names, coords


def inspect_schema(path: Path) -> dict[str, Any]:
    with h5py.File(path, "r") as nwb:
        if text(nwb["general/subject/genotype"][()]) != "WT":
            raise RuntimeError(f"{STOP}: genotype")
        table = nwb["intervals/OptogeneticStimulusTable"]
        required = ("id", "power", "start_time", "stop_time", "target_pumpprobe_id")
        lengths = {name: len(table[name]) for name in required}
        if len(set(lengths.values())) != 1 or lengths["id"] < 3:
            raise RuntimeError(f"{STOP}: stimulus table")
        powers = np.asarray(table["power"][...], dtype=np.float64)
        starts = np.asarray(table["start_time"][...], dtype=np.float64)
        stops = np.asarray(table["stop_time"][...], dtype=np.float64)
        target_ids = np.asarray(table["target_pumpprobe_id"][...], dtype=np.float64)
        if (not np.all(powers == 0.0012) or np.any(stops <= starts) or np.any(np.diff(starts) <= 0)
                or not np.allclose(stops - starts, 0.5, rtol=0, atol=1e-9)):
            raise RuntimeError(f"{STOP}: stimulus profile")
        names, _ = canonical_map(nwb)
        green = nwb["processing/ophys/GreenSignals/BaseGreenSignal"]
        red = nwb["processing/ophys/RedSignals/BaseRedSignal"]
        if green["data"].shape != red["data"].shape or green["data"].shape[1] < 80:
            raise RuntimeError(f"{STOP}: signal shape")
        if green["timestamps"].shape != (green["data"].shape[0],):
            raise RuntimeError(f"{STOP}: timestamp shape")
        explicit = [int(value) for value in target_ids[np.isfinite(target_ids)]]
        canonical_sources = [names[value] for value in explicit if value in names]
        return {
            "canonical_receivers": len(names),
            "canonical_source_events": len(canonical_sources),
            "development": subject_development(subject_id(path)),
            "explicit_target_events": len(explicit),
            "frames": int(green["data"].shape[0]),
            "receivers": int(green["data"].shape[1]),
            "stimuli": int(lengths["id"]),
            "subject": subject_id(path),
            "unique_canonical_sources": len(set(canonical_sources)),
        }


def schema_inventory(data_dir: Path, *, hash_raw: bool = True) -> dict[str, Any]:
    inventory, paths = load_inventory(data_dir, hash_raw=hash_raw)
    schemas = [inspect_schema(path) for path in paths]
    development = [row for row in schemas if row["development"]]
    confirmation = [row for row in schemas if not row["development"]]
    if len(development) != 77 or len(confirmation) != 33:
        raise RuntimeError(f"{STOP}: subject split")
    summary = {
        "canonical_receiver_instances": sum(row["canonical_receivers"] for row in schemas),
        "canonical_source_events": sum(row["canonical_source_events"] for row in schemas),
        "confirmation_subjects": len(confirmation),
        "development_subjects": len(development),
        "explicit_target_events": sum(row["explicit_target_events"] for row in schemas),
        "files": len(schemas),
        "receiver_instances": sum(row["receivers"] for row in schemas),
        "stimuli": sum(row["stimuli"] for row in schemas),
    }
    return {"confirmation_values_opened": False, "inventory_sha256": EXPECTED_INVENTORY_SHA,
            "raw_total_bytes": inventory["total_bytes"], "schemas": schemas, "summary": summary}


def schema_receipt(data_dir: Path, artifact_dir: Path) -> dict[str, Any]:
    receipt = schema_inventory(data_dir, hash_raw=True)
    receipt["receipt_sha256"] = write_json_once(artifact_dir / SCHEMA_RECEIPT, receipt)
    return receipt


def preregistered_files() -> tuple[Path, ...]:
    return (Path(__file__).resolve(), TEST_FILE, CONTRACT)


def seal(data_dir: Path, artifact_dir: Path) -> dict[str, Any]:
    receipt_path = artifact_dir / SCHEMA_RECEIPT
    if not receipt_path.is_file():
        raise RuntimeError(f"{STOP}: schema receipt missing")
    current = schema_inventory(data_dir, hash_raw=True)
    stored = json.loads(receipt_path.read_text(encoding="utf-8"))
    stored.pop("receipt_sha256", None)
    if canonical_json_bytes(current) != canonical_json_bytes(stored):
        raise RuntimeError(f"{STOP}: schema receipt mutation")
    files = {str(path.relative_to(ROOT)).replace("\\", "/"): sha256_file(path)
             for path in preregistered_files()}
    manifest = {"confirmation_values_opened": False, "files": files,
                "inventory_sha256": EXPECTED_INVENTORY_SHA,
                "runtime": verify_runtime(),
                "schema_receipt_sha256": sha256_file(receipt_path)}
    manifest["manifest_sha256"] = write_json_once(artifact_dir / MANIFEST, manifest)
    return manifest


def verify_manifest(data_dir: Path, artifact_dir: Path) -> str:
    path = artifact_dir / MANIFEST
    if not path.is_file():
        raise RuntimeError(f"{STOP}: manifest missing")
    manifest = json.loads(path.read_text(encoding="utf-8"))
    files = {str(file.relative_to(ROOT)).replace("\\", "/"): sha256_file(file)
             for file in preregistered_files()}
    load_inventory(data_dir, hash_raw=True)
    runtime = verify_runtime()
    if (manifest.get("confirmation_values_opened") is not False or manifest.get("files") != files
            or manifest.get("inventory_sha256") != EXPECTED_INVENTORY_SHA
            or manifest.get("runtime") != runtime
            or manifest.get("schema_receipt_sha256") != sha256_file(artifact_dir / SCHEMA_RECEIPT)):
        raise RuntimeError(f"{STOP}: manifest mutation")
    return sha256_file(path)


def normalized_coordinates(names: dict[int, str], coords: dict[int, np.ndarray]) -> dict[str, np.ndarray]:
    by_label: dict[str, list[np.ndarray]] = defaultdict(list)
    for receiver, label in names.items():
        by_label[label].append(coords[receiver])
    labels = sorted(by_label)
    matrix = np.stack([np.median(by_label[label], axis=0) for label in labels])
    median = np.median(matrix, axis=0)
    q75, q25 = np.quantile(matrix, (0.75, 0.25), axis=0)
    scale = q75 - q25
    if np.any(scale <= 0):
        raise RuntimeError(f"{STOP}: coordinate scale")
    matrix = (matrix - median) / scale
    return {label: row for label, row in zip(labels, matrix, strict=True)}


def similarity_align(source: np.ndarray, target: np.ndarray) -> tuple[np.ndarray, float, np.ndarray, np.ndarray]:
    source_mean, target_mean = source.mean(0), target.mean(0)
    a, b = source - source_mean, target - target_mean
    u, singular, vt = np.linalg.svd(a.T @ b)
    rotation = u @ vt
    scale = float(np.sum(singular) / np.sum(a * a))
    return rotation, scale, source_mean, target_mean


def build_template(subject_coords: dict[int, dict[str, np.ndarray]], iterations: int = 5) -> dict[str, np.ndarray]:
    if not subject_coords:
        raise RuntimeError(f"{STOP}: no development coordinates")
    reference_subject = max(subject_coords, key=lambda key: len(subject_coords[key]))
    template = {label: value.copy() for label, value in subject_coords[reference_subject].items()}
    aligned: dict[int, dict[str, np.ndarray]] = {}
    for _ in range(iterations):
        aligned = {}
        for subject, coordinates in subject_coords.items():
            overlap = sorted(set(coordinates) & set(template))
            if len(overlap) < 10:
                continue
            source = np.stack([coordinates[label] for label in overlap])
            target = np.stack([template[label] for label in overlap])
            rotation, scale, source_mean, target_mean = similarity_align(source, target)
            aligned[subject] = {label: (value - source_mean) @ rotation * scale + target_mean
                                for label, value in coordinates.items()}
        values: dict[str, list[np.ndarray]] = defaultdict(list)
        for coordinates in aligned.values():
            for label, value in coordinates.items():
                values[label].append(value)
        template = {label: np.median(rows, axis=0) for label, rows in values.items()}
    if len(template) < 200:
        raise RuntimeError(f"{STOP}: template coverage")
    return template


def consecutive(values: np.ndarray, threshold: float, *, positive: bool) -> np.ndarray:
    mask = values >= threshold if positive else np.abs(values) >= threshold
    return np.any(mask[:-1] & mask[1:], axis=0) if len(mask) >= 2 else np.zeros(mask.shape[1], dtype=bool)


def residual_z(green: np.ndarray, red: np.ndarray, timestamps: np.ndarray,
               starts: np.ndarray, stops: np.ndarray) -> np.ndarray:
    nonstim = np.ones(len(timestamps), dtype=bool)
    for start, stop in zip(starts, stops, strict=True):
        nonstim &= ~((timestamps >= start - 10) & (timestamps <= stop + 20))
    if np.sum(nonstim) < 20:
        # Long dense sessions can cover the entire record. The inter-event pre-stimulus
        # intervals are the preregistered fallback noise sample.
        nonstim = np.zeros(len(timestamps), dtype=bool)
        for start in starts:
            nonstim |= (timestamps >= start - 10) & (timestamps <= start - 2)
    if np.sum(nonstim) < 16:
        raise RuntimeError(f"{STOP}: nonstim frames")
    x, y = red[nonstim], green[nonstim]
    xm, ym = x.mean(0), y.mean(0)
    variance = np.mean((x - xm) ** 2, axis=0)
    slope = np.divide(np.mean((x - xm) * (y - ym), axis=0), variance,
                      out=np.zeros_like(variance), where=variance > 0)
    residual = green - (ym - slope * xm)[None, :] - red * slope[None, :]
    center = np.median(residual[nonstim], axis=0)
    mad = 1.4826 * np.median(np.abs(residual[nonstim] - center), axis=0)
    positive = mad[np.isfinite(mad) & (mad > 0)]
    if len(positive) < max(10, green.shape[1] // 4):
        raise RuntimeError(f"{STOP}: residual scale")
    floor = float(np.quantile(positive, 0.10))
    mad = np.maximum(mad, floor)
    z = (residual - center) / mad
    if not np.all(np.isfinite(z)):
        raise RuntimeError(f"{STOP}: residual finite")
    return z


def extract_subject(path: Path, template: dict[str, np.ndarray]) -> list[dict[str, Any]]:
    subject = subject_id(path)
    with h5py.File(path, "r") as nwb:
        names, _ = canonical_map(nwb)
        table = nwb["intervals/OptogeneticStimulusTable"]
        starts = np.asarray(table["start_time"][...], dtype=np.float64)
        stops = np.asarray(table["stop_time"][...], dtype=np.float64)
        target_ids = np.asarray(table["target_pumpprobe_id"][...], dtype=np.float64)
        green_group = nwb["processing/ophys/GreenSignals/BaseGreenSignal"]
        red_group = nwb["processing/ophys/RedSignals/BaseRedSignal"]
        green = np.asarray(green_group["data"][...], dtype=np.float64)
        red = np.asarray(red_group["data"][...], dtype=np.float64)
        timestamps = np.asarray(green_group["timestamps"][...], dtype=np.float64)
        red_timestamps = np.asarray(red_group["timestamps"][...], dtype=np.float64)
        pump = nwb["processing/ophys/PumpProbeGreenSegmentations/PumpProbeGreenPlaneSegmentation"]
        receiver_ids = np.asarray(pump["id"][...], dtype=np.int64)
        if (green.shape != red.shape or green.shape[1] != len(receiver_ids)
                or not np.allclose(timestamps, red_timestamps, rtol=0, atol=1e-9)):
            raise RuntimeError(f"{STOP}: signal alignment")
        row_by_id = {int(receiver): index for index, receiver in enumerate(receiver_ids)}
        z = residual_z(green, red, timestamps, starts, stops)
        output: list[dict[str, Any]] = []
        for event, (start, stop, target_value) in enumerate(zip(starts, stops, target_ids, strict=True)):
            if not np.isfinite(target_value):
                continue
            target_id = int(target_value)
            source = names.get(target_id)
            source_row = row_by_id.get(target_id)
            if source is None or source_row is None or source not in template:
                continue
            baseline = (timestamps >= start - 10) & (timestamps <= start - 2)
            response = (timestamps >= stop + 1) & (timestamps <= stop + 10)
            if np.sum(baseline) < 8 or np.sum(response) < 8:
                continue
            event_z = z[response] - np.median(z[baseline], axis=0)[None, :]
            if not bool(consecutive(event_z[:, [source_row]], 4.0, positive=True)[0]):
                continue
            detected = consecutive(event_z, 3.0, positive=False)
            peak_index = np.argmax(np.abs(event_z), axis=0)
            peak = event_z[peak_index, np.arange(event_z.shape[1])]
            response_times = timestamps[response] - stop
            latency = response_times[peak_index]
            for receiver_id, receiver_row in row_by_id.items():
                receiver = names.get(receiver_id)
                if receiver is None or receiver == source or receiver not in template:
                    continue
                output.append({
                    "event": event,
                    "latency": float(latency[receiver_row]),
                    "peak": float(peak[receiver_row]),
                    "receiver": receiver,
                    "source": source,
                    "subject": subject,
                    "y": int(detected[receiver_row]),
                })
        return output


def collect_coordinates(paths: Iterable[Path]) -> dict[int, dict[str, np.ndarray]]:
    output = {}
    for path in paths:
        if not subject_development(subject_id(path)):
            continue
        with h5py.File(path, "r") as nwb:
            names, coords = canonical_map(nwb)
            normalized = normalized_coordinates(names, coords)
            if len(normalized) >= 10:
                output[subject_id(path)] = normalized
    return output


def feature_arrays(rows: list[dict[str, Any]], template: dict[str, np.ndarray]) -> dict[str, Any]:
    source = np.stack([template[row["source"]] for row in rows])
    receiver = np.stack([template[row["receiver"]] for row in rows])
    return {
        "delta": receiver - source,
        "pair": np.asarray([(row["source"], row["receiver"]) for row in rows], dtype=object),
        "receiver_coord": receiver,
        "source_coord": source,
        "subjects": np.asarray([row["subject"] for row in rows], dtype=np.int64),
        "y": np.asarray([row["y"] for row in rows], dtype=np.float64),
    }


def log_loss(y: np.ndarray, probability: np.ndarray) -> float:
    probability = np.clip(probability, 1e-8, 1 - 1e-8)
    return float(np.mean(-(y * np.log(probability) + (1 - y) * np.log(1 - probability))))


def lower_matrix(values: np.ndarray) -> np.ndarray:
    return np.asarray([[values[0], 0, 0], [values[1], values[2], 0],
                       [values[3], values[4], values[5]]], dtype=np.float64)


def lower_gradient(matrix: np.ndarray) -> np.ndarray:
    return np.asarray([matrix[0, 0], matrix[1, 0], matrix[1, 1],
                       matrix[2, 0], matrix[2, 1], matrix[2, 2]])


def fit_metric(delta: np.ndarray, y: np.ndarray, ridge: float, *, directional: bool,
               maxiter: int = 120) -> dict[str, Any]:
    dimension = 10 if directional else 7
    initial = np.zeros(dimension)
    initial[0] = math.log((float(y.mean()) + 1e-4) / (1 - float(y.mean()) + 1e-4))
    initial[[1, 3, 6]] = 0.1

    def objective(parameters: np.ndarray) -> tuple[float, np.ndarray]:
        intercept = parameters[0]
        lower = lower_matrix(parameters[1:7])
        projected = delta @ lower
        eta = intercept - np.sum(projected * projected, axis=1)
        if directional:
            eta += delta @ parameters[7:10]
        probability = expit(eta)
        residual = probability - y
        loss = float(np.mean(np.logaddexp(0, eta) - y * eta)
                     + ridge * np.sum(parameters[1:] ** 2))
        full = -2 * delta.T @ (residual[:, None] * projected) / len(y)
        gradient = np.zeros_like(parameters)
        gradient[0] = residual.mean()
        gradient[1:7] = lower_gradient(full) + 2 * ridge * parameters[1:7]
        if directional:
            gradient[7:10] = delta.T @ residual / len(y) + 2 * ridge * parameters[7:10]
        return loss, gradient

    result = minimize(objective, initial, jac=True, method="L-BFGS-B",
                      options={"maxiter": maxiter, "ftol": 1e-10})
    if not result.success and result.nit == 0:
        raise RuntimeError(f"{STOP}: metric fit {result.message}")
    return {"directional": directional, "parameters": result.x, "ridge": ridge}


def predict_metric(model: dict[str, Any], delta: np.ndarray) -> np.ndarray:
    parameters = model["parameters"]
    lower = lower_matrix(parameters[1:7])
    eta = parameters[0] - np.sum((delta @ lower) ** 2, axis=1)
    if model["directional"]:
        eta += delta @ parameters[7:10]
    return expit(eta)


def quadrants(template: dict[str, np.ndarray]) -> tuple[np.ndarray, np.ndarray]:
    matrix = np.stack(list(template.values()))
    center = matrix.mean(0)
    _, _, vh = np.linalg.svd(matrix - center, full_matrices=False)
    return center, vh[:2]


def quadrant_index(source: np.ndarray, center: np.ndarray, axes: np.ndarray) -> np.ndarray:
    projected = (source - center) @ axes.T
    return (projected[:, 0] >= 0).astype(np.int64) + 2 * (projected[:, 1] >= 0).astype(np.int64)


def fit_switching(delta: np.ndarray, source: np.ndarray, y: np.ndarray, ridge: float,
                  center: np.ndarray, axes: np.ndarray, maxiter: int = 120) -> dict[str, Any]:
    region = quadrant_index(source, center, axes)
    initial = np.zeros(31)
    initial[0] = math.log((float(y.mean()) + 1e-4) / (1 - float(y.mean()) + 1e-4))
    initial[[1, 3, 6]] = 0.1

    def objective(parameters: np.ndarray) -> tuple[float, np.ndarray]:
        common = lower_matrix(parameters[1:7])
        deviations = [lower_matrix(parameters[7 + 6*q:13 + 6*q]) for q in range(4)]
        eta = np.full(len(y), parameters[0])
        projected: list[tuple[np.ndarray, np.ndarray, np.ndarray]] = []
        for q in range(4):
            select = np.flatnonzero(region == q)
            lower = common + deviations[q]
            values = delta[select] @ lower
            eta[select] -= np.sum(values * values, axis=1)
            projected.append((select, lower, values))
        probability = expit(eta)
        residual = probability - y
        gradient = np.zeros_like(parameters)
        gradient[0] = residual.mean()
        common_full = np.zeros((3, 3))
        for q, (select, _, values) in enumerate(projected):
            full = -2 * delta[select].T @ (residual[select, None] * values) / len(y)
            common_full += full
            start = 7 + 6*q
            gradient[start:start+6] = lower_gradient(full) + 8 * ridge * parameters[start:start+6]
        gradient[1:7] = lower_gradient(common_full) + 2 * ridge * parameters[1:7]
        penalty = ridge * (np.sum(parameters[1:7] ** 2)
                           + 4 * np.sum(parameters[7:] ** 2))
        loss = float(np.mean(np.logaddexp(0, eta) - y * eta) + penalty)
        return loss, gradient

    result = minimize(objective, initial, jac=True, method="L-BFGS-B",
                      options={"maxiter": maxiter, "ftol": 1e-10})
    if not result.success and result.nit == 0:
        raise RuntimeError(f"{STOP}: switching fit")
    return {"axes": axes, "center": center, "parameters": result.x, "ridge": ridge}


def predict_switching(model: dict[str, Any], delta: np.ndarray, source: np.ndarray) -> np.ndarray:
    parameters = model["parameters"]
    region = quadrant_index(source, model["center"], model["axes"])
    eta = np.full(len(delta), parameters[0])
    common = lower_matrix(parameters[1:7])
    for q in range(4):
        select = region == q
        lower = common + lower_matrix(parameters[7 + 6*q:13 + 6*q])
        eta[select] -= np.sum((delta[select] @ lower) ** 2, axis=1)
    return expit(eta)


def rff_basis() -> tuple[np.ndarray, np.ndarray]:
    rng = np.random.Generator(np.random.PCG64(SEED))
    return rng.normal(size=(6, RFF_DIM)), rng.uniform(0, 2*np.pi, size=RFF_DIM)


def rff_features(source: np.ndarray, receiver: np.ndarray) -> np.ndarray:
    weights, phase = rff_basis()
    values = np.concatenate((source, receiver), axis=1)
    return np.sqrt(2 / RFF_DIM) * np.cos(values @ weights + phase)


def fit_logistic(features: np.ndarray, y: np.ndarray, ridge: float,
                 maxiter: int = 120) -> dict[str, Any]:
    initial = np.zeros(features.shape[1] + 1)
    initial[0] = math.log((float(y.mean()) + 1e-4) / (1 - float(y.mean()) + 1e-4))

    def objective(parameters: np.ndarray) -> tuple[float, np.ndarray]:
        eta = parameters[0] + features @ parameters[1:]
        probability = expit(eta)
        residual = probability - y
        loss = float(np.mean(np.logaddexp(0, eta) - y * eta)
                     + ridge * np.sum(parameters[1:] ** 2))
        gradient = np.concatenate(([residual.mean()], features.T @ residual / len(y)
                                   + 2 * ridge * parameters[1:]))
        return loss, gradient

    result = minimize(objective, initial, jac=True, method="L-BFGS-B",
                      options={"maxiter": maxiter, "ftol": 1e-10})
    if not result.success and result.nit == 0:
        raise RuntimeError(f"{STOP}: operator fit")
    return {"parameters": result.x, "ridge": ridge}


def predict_logistic(model: dict[str, Any], features: np.ndarray) -> np.ndarray:
    return expit(model["parameters"][0] + features @ model["parameters"][1:])


def graph_fit(pairs: np.ndarray, y: np.ndarray) -> dict[str, Any]:
    pair_values: dict[tuple[str, str], list[float]] = defaultdict(list)
    source_values: dict[str, list[float]] = defaultdict(list)
    receiver_values: dict[str, list[float]] = defaultdict(list)
    for pair, value in zip(pairs, y, strict=True):
        source, receiver = str(pair[0]), str(pair[1])
        pair_values[(source, receiver)].append(float(value))
        source_values[source].append(float(value))
        receiver_values[receiver].append(float(value))
    smooth = lambda values: (sum(values) + 0.5) / (len(values) + 1)
    return {
        "global": smooth(y.tolist()),
        "pair": {pair: smooth(values) for pair, values in pair_values.items()},
        "receiver": {key: smooth(values) for key, values in receiver_values.items()},
        "source": {key: smooth(values) for key, values in source_values.items()},
    }


def graph_predict(model: dict[str, Any], pairs: np.ndarray) -> np.ndarray:
    output = np.empty(len(pairs))
    for index, pair in enumerate(pairs):
        source, receiver = str(pair[0]), str(pair[1])
        if (source, receiver) in model["pair"]:
            output[index] = model["pair"][(source, receiver)]
            continue
        source_p = model["source"].get(source, model["global"])
        receiver_p = model["receiver"].get(receiver, model["global"])
        logits = [math.log(p / (1-p)) for p in (source_p, receiver_p)]
        output[index] = expit(np.mean(logits))
    return output


def fold_index(subjects: np.ndarray) -> np.ndarray:
    return np.asarray([int(hashlib.sha256(f"CE-BRAIN-STAGE3A-CV|{int(s)}".encode()).hexdigest()[:8], 16) % 5
                       for s in subjects], dtype=np.int64)


def select_ridge(name: str, arrays: dict[str, Any], center: np.ndarray,
                 axes: np.ndarray) -> float:
    folds = fold_index(arrays["subjects"])
    scores = []
    # Deterministic per-subject cap keeps CV computationally bounded without
    # changing the final all-row fit or any confirmation score.
    rng = np.random.Generator(np.random.PCG64(SEED + len(name)))
    cap = np.arange(len(folds))
    if len(cap) > 180_000:
        cap = np.sort(rng.choice(cap, 180_000, replace=False))
    for ridge in RIDGES:
        fold_losses = []
        for fold in range(5):
            train = cap[folds[cap] != fold]
            valid = cap[folds[cap] == fold]
            if name == "R":
                model = fit_metric(arrays["delta"][train], arrays["y"][train], ridge,
                                   directional=False, maxiter=80)
                probability = predict_metric(model, arrays["delta"][valid])
            elif name == "F":
                model = fit_metric(arrays["delta"][train], arrays["y"][train], ridge,
                                   directional=True, maxiter=80)
                probability = predict_metric(model, arrays["delta"][valid])
            elif name == "S":
                model = fit_switching(arrays["delta"][train], arrays["source_coord"][train],
                                      arrays["y"][train], ridge, center, axes, maxiter=80)
                probability = predict_switching(model, arrays["delta"][valid],
                                                arrays["source_coord"][valid])
            elif name == "O":
                features = rff_features(arrays["source_coord"][cap], arrays["receiver_coord"][cap])
                train_local = np.flatnonzero(folds[cap] != fold)
                valid_local = np.flatnonzero(folds[cap] == fold)
                model = fit_logistic(features[train_local], arrays["y"][cap][train_local], ridge,
                                     maxiter=80)
                probability = predict_logistic(model, features[valid_local])
            else:
                raise ValueError(name)
            fold_losses.append(log_loss(arrays["y"][valid], probability))
        scores.append((float(np.mean(fold_losses)), ridge))
    return min(scores)[1]


def fit_models(arrays: dict[str, Any], template: dict[str, np.ndarray]) -> dict[str, Any]:
    center, axes = quadrants(template)
    ridges = {name: select_ridge(name, arrays, center, axes) for name in ("R", "F", "S", "O")}
    return {
        "N": float((arrays["y"].sum() + 0.5) / (len(arrays["y"]) + 1)),
        "R": fit_metric(arrays["delta"], arrays["y"], ridges["R"], directional=False),
        "F": fit_metric(arrays["delta"], arrays["y"], ridges["F"], directional=True),
        "S": fit_switching(arrays["delta"], arrays["source_coord"], arrays["y"], ridges["S"], center, axes),
        "G": graph_fit(arrays["pair"], arrays["y"]),
        "O": fit_logistic(rff_features(arrays["source_coord"], arrays["receiver_coord"]),
                          arrays["y"], ridges["O"]),
        "ridges": ridges,
    }


def predict_models(models: dict[str, Any], arrays: dict[str, Any], *, include_graph: bool) -> dict[str, np.ndarray]:
    output = {
        "N": np.full(len(arrays["y"]), models["N"]),
        "R": predict_metric(models["R"], arrays["delta"]),
        "F": predict_metric(models["F"], arrays["delta"]),
        "S": predict_switching(models["S"], arrays["delta"], arrays["source_coord"]),
        "O": predict_logistic(models["O"], rff_features(arrays["source_coord"], arrays["receiver_coord"])),
    }
    if include_graph:
        output["G"] = graph_predict(models["G"], arrays["pair"])
    return output


def subject_losses(arrays: dict[str, Any], predictions: dict[str, np.ndarray]) -> dict[str, dict[int, float]]:
    output: dict[str, dict[int, float]] = {name: {} for name in predictions}
    for subject in np.unique(arrays["subjects"]):
        select = arrays["subjects"] == subject
        for name, probability in predictions.items():
            output[name][int(subject)] = log_loss(arrays["y"][select], probability[select])
    return output


def mean_losses(losses: dict[str, dict[int, float]]) -> dict[str, float]:
    return {name: float(np.mean(list(values.values()))) for name, values in losses.items()}


def bootstrap_improvement(losses: dict[str, dict[int, float]], better: str, baseline: str,
                          rng: np.random.Generator) -> np.ndarray:
    subjects = sorted(set(losses[better]) & set(losses[baseline]))
    a = np.asarray([losses[better][subject] for subject in subjects])
    b = np.asarray([losses[baseline][subject] for subject in subjects])
    weights = rng.multinomial(len(subjects), np.full(len(subjects), 1/len(subjects)), size=BOOTSTRAPS)
    ma, mb = weights @ a / len(subjects), weights @ b / len(subjects)
    return (mb - ma) / mb


def score_set(losses: dict[str, dict[int, float]], seed_offset: int) -> dict[str, Any]:
    means = mean_losses(losses)
    rng = np.random.Generator(np.random.PCG64(SEED + seed_offset))
    comparisons = {}
    for name in sorted(set(losses) - {"N"}):
        values = bootstrap_improvement(losses, name, "N", rng)
        comparisons[f"{name}_vs_N"] = {
            "improvement": (means["N"] - means[name]) / means["N"],
            "lower_95": float(np.quantile(values, 0.025)),
            "median": float(np.median(values)),
        }
    ranking = sorted(means, key=means.get)
    if len(ranking) >= 2:
        first, second = ranking[:2]
        values = bootstrap_improvement(losses, first, second, rng)
        comparisons["winner_vs_runner"] = {
            "better": first, "baseline": second,
            "improvement": (means[second] - means[first]) / means[second],
            "lower_95": float(np.quantile(values, 0.025)),
            "median": float(np.median(values)),
        }
    return {"comparisons": comparisons, "losses": means, "ranking": ranking}


def pair_rates(rows: list[dict[str, Any]]) -> dict[tuple[str, str], dict[str, Any]]:
    values: dict[tuple[str, str], list[int]] = defaultdict(list)
    subjects: dict[tuple[str, str], set[int]] = defaultdict(set)
    for row in rows:
        pair = (row["source"], row["receiver"])
        values[pair].append(row["y"])
        subjects[pair].add(row["subject"])
    return {pair: {"p": (sum(outcomes) + 0.5) / (len(outcomes) + 1),
                   "subjects": len(subjects[pair]), "trials": len(outcomes)}
            for pair, outcomes in values.items()}


def symmetry_diagnostic(rates: dict[tuple[str, str], dict[str, Any]]) -> dict[str, Any]:
    differences = []
    for (source, receiver), row in rates.items():
        reverse = rates.get((receiver, source))
        if source < receiver and reverse and row["subjects"] >= 3 and reverse["subjects"] >= 3:
            differences.append(abs(row["p"] - reverse["p"]))
    if not differences:
        raise RuntimeError(f"{STOP}: symmetry coverage")
    values = np.asarray(differences)
    rng = np.random.Generator(np.random.PCG64(SEED + 301))
    boot = np.median(values[rng.integers(0, len(values), size=(BOOTSTRAPS, len(values)))], axis=1)
    return {"bidirectional_pairs": len(values), "mean_abs_difference": float(values.mean()),
            "median_abs_difference": float(np.median(values)),
            "median_upper_97_5": float(np.quantile(boot, 0.975))}


def triangle_diagnostic(rates: dict[tuple[str, str], dict[str, Any]]) -> dict[str, Any]:
    eligible = {pair: row for pair, row in rates.items() if row["subjects"] >= 3}
    outgoing: dict[str, set[str]] = defaultdict(set)
    for source, receiver in eligible:
        outgoing[source].add(receiver)
    heap: list[tuple[int, tuple[str, str, str]]] = []
    limit = 50_000
    for source in sorted(outgoing):
        for middle in sorted(outgoing[source]):
            for receiver in sorted(outgoing.get(middle, ())):
                if receiver == source or (source, receiver) not in eligible:
                    continue
                triad = (source, middle, receiver)
                key = int(hashlib.sha256(("|".join(triad)).encode()).hexdigest()[:16], 16)
                item = (-key, triad)
                if len(heap) < limit:
                    heapq.heappush(heap, item)
                elif item > heap[0]:
                    heapq.heapreplace(heap, item)
    triads = [item[1] for item in heap]
    if len(triads) < 1_000:
        raise RuntimeError(f"{STOP}: triangle coverage")
    violation = np.asarray([
        -math.log(eligible[(a, c)]["p"]) > 1.1 * (
            -math.log(eligible[(a, b)]["p"]) - math.log(eligible[(b, c)]["p"]))
        for a, b, c in triads
    ], dtype=np.float64)
    rng = np.random.Generator(np.random.PCG64(SEED + 302))
    weights = rng.binomial(len(violation), float(violation.mean()), size=BOOTSTRAPS) / len(violation)
    return {"sampled_ordered_triads": len(triads), "violation_rate": float(violation.mean()),
            "violation_lower_95": float(np.quantile(weights, 0.025)),
            "violation_upper_95": float(np.quantile(weights, 0.975))}


def supported(score: dict[str, Any], name: str) -> bool:
    row = score["comparisons"].get(f"{name}_vs_N", {})
    return row.get("improvement", -np.inf) >= 0.05 and row.get("lower_95", -np.inf) > 0


def decisive_winner(score: dict[str, Any]) -> str | None:
    row = score["comparisons"].get("winner_vs_runner", {})
    winner = row.get("better")
    if (winner and winner != "N" and supported(score, winner)
            and row.get("improvement", -np.inf) >= 0.03 and row.get("lower_95", -np.inf) > 0):
        return str(winner)
    return None


def decide(common: dict[str, Any], unseen: dict[str, Any], symmetry: dict[str, Any],
           triangle: dict[str, Any], directional: dict[str, float]) -> str:
    common_winner, unseen_winner = decisive_winner(common), decisive_winner(unseen)
    direction_supported = directional["improvement"] >= 0.03 and directional["lower_95"] > 0
    if common_winner == "G":
        return "DIRECTED_GRAPH_SEEN_SOURCE_ONLY"
    if common_winner is None or unseen_winner is None or common_winner != unseen_winner:
        if direction_supported and supported(common, "F") and supported(unseen, "F"):
            return "DIRECTIONAL_FINSLER_RETAINED"
        return "REPRESENTATION_TENSION"
    if common_winner == "R":
        local_ok = triangle["violation_upper_95"] <= 0.10 and not direction_supported
        return "RIEMANNIAN_LIKE_LOCAL_RETAINED" if local_ok else "REPRESENTATION_TENSION"
    if common_winner == "F":
        return "DIRECTIONAL_FINSLER_RETAINED"
    if common_winner == "S":
        return "SWITCHING_STRATIFIED_RETAINED"
    if common_winner == "O":
        return "GENERAL_TRANSITION_OPERATOR_RETAINED"
    return "REPRESENTATION_TENSION"


def build_result(data_dir: Path, artifact_dir: Path) -> dict[str, Any]:
    manifest_sha = verify_manifest(data_dir, artifact_dir)
    _, paths = load_inventory(data_dir, hash_raw=False)
    coordinate_sets = collect_coordinates(paths)
    template = build_template(coordinate_sets)
    rows: list[dict[str, Any]] = []
    for path in paths:
        rows.extend(extract_subject(path, template))
    development = [row for row in rows if subject_development(row["subject"])
                   and not source_holdout(row["source"])]
    confirmation = [row for row in rows if not subject_development(row["subject"])]
    if len(development) < 20_000 or len(confirmation) < 10_000:
        raise RuntimeError(f"{STOP}: endpoint coverage")
    development_pairs = {(row["source"], row["receiver"]) for row in development}
    common_rows = [row for row in confirmation
                   if not source_holdout(row["source"])
                   and (row["source"], row["receiver"]) in development_pairs]
    unseen_rows = [row for row in confirmation if source_holdout(row["source"])]
    if len(common_rows) < 5_000 or len(unseen_rows) < 1_000:
        raise RuntimeError(f"{STOP}: holdout coverage")
    dev_arrays = feature_arrays(development, template)
    common_arrays = feature_arrays(common_rows, template)
    unseen_arrays = feature_arrays(unseen_rows, template)
    models = fit_models(dev_arrays, template)
    common_losses = subject_losses(common_arrays, predict_models(models, common_arrays, include_graph=True))
    unseen_losses = subject_losses(unseen_arrays, predict_models(models, unseen_arrays, include_graph=False))
    common_score = score_set(common_losses, 100)
    unseen_score = score_set(unseen_losses, 200)
    rng = np.random.Generator(np.random.PCG64(SEED + 250))
    f_vs_r = bootstrap_improvement(common_losses, "F", "R", rng)
    directional = {
        "improvement": (common_score["losses"]["R"] - common_score["losses"]["F"])
                       / common_score["losses"]["R"],
        "lower_95": float(np.quantile(f_vs_r, 0.025)),
        "median": float(np.median(f_vs_r)),
    }
    rates = pair_rates(confirmation)
    symmetry = symmetry_diagnostic(rates)
    triangle = triangle_diagnostic(rates)
    decision = decide(common_score, unseen_score, symmetry, triangle, directional)
    result = {
        "axioms": {"directionality_F_vs_R": directional, "symmetry": symmetry,
                   "triangle": triangle},
        "bootstrap": {"repetitions": BOOTSTRAPS, "seed": SEED},
        "claim_ceiling": "C. elegans direct-optogenetic propagation edge-representation result",
        "coverage": {
            "confirmation_detected_edges": int(sum(row["y"] for row in confirmation)),
            "confirmation_rows": len(confirmation),
            "confirmation_subjects": len({row["subject"] for row in confirmation}),
            "development_detected_edges": int(sum(row["y"] for row in development)),
            "development_rows": len(development),
            "development_subjects": len({row["subject"] for row in development}),
            "eligible_stimulus_events": len({(row["subject"], row["event"]) for row in rows}),
            "template_nodes": len(template),
            "common_pair_rows": len(common_rows),
            "unseen_source_rows": len(unseen_rows),
        },
        "decision": decision,
        "heldout_animal_common_pair": common_score,
        "heldout_source": unseen_score,
        "manifest_sha256": manifest_sha,
        "model_ridges": models["ridges"],
        "stage4_authorized": False,
    }
    validate_result(result)
    return result


def validate_result(result: dict[str, Any]) -> None:
    expected = decide(result["heldout_animal_common_pair"], result["heldout_source"],
                      result["axioms"]["symmetry"], result["axioms"]["triangle"],
                      result["axioms"]["directionality_F_vs_R"])
    if result.get("decision") != expected or result.get("stage4_authorized") is not False:
        raise RuntimeError(f"{STOP}: result decision")
    if result.get("bootstrap", {}).get("repetitions") != BOOTSTRAPS:
        raise RuntimeError(f"{STOP}: result bootstrap")


def execute(data_dir: Path, artifact_dir: Path) -> dict[str, Any]:
    if (artifact_dir / RESULT).exists():
        raise RuntimeError(f"{STOP}: refusing to overwrite {RESULT}")
    result = build_result(data_dir, artifact_dir)
    result_sha = write_json_once(artifact_dir / RESULT, result)
    return {"result_sha256": result_sha, **result}


def verify_result(data_dir: Path, artifact_dir: Path) -> dict[str, Any]:
    result_path = artifact_dir / RESULT
    if not result_path.is_file():
        raise RuntimeError(f"{STOP}: result missing")
    stored = json.loads(result_path.read_text(encoding="utf-8"))
    validate_result(stored)
    recomputed = build_result(data_dir, artifact_dir)
    if canonical_json_bytes(stored) != canonical_json_bytes(recomputed):
        raise RuntimeError(f"{STOP}: raw recomputation mismatch")
    receipt = {"decision": stored["decision"], "manifest_sha256": stored["manifest_sha256"],
               "raw_recomputed": True, "result_sha256": sha256_file(result_path), "status": "PASS"}
    receipt["validation_receipt_sha256"] = write_json_once(artifact_dir / VALIDATION, receipt)
    return receipt


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", type=Path, required=True)
    parser.add_argument("--artifact-dir", type=Path,
                        default=ROOT / "artifacts" / "brain" / "ce_brain_stage3a_worm_metric")
    mode = parser.add_mutually_exclusive_group(required=True)
    for name in ("schema-only", "seal", "execute", "verify-result"):
        mode.add_argument(f"--{name}", action="store_true")
    args = parser.parse_args()
    if args.schema_only:
        output = schema_receipt(args.data_dir, args.artifact_dir)
    elif args.seal:
        output = seal(args.data_dir, args.artifact_dir)
    elif args.execute:
        output = execute(args.data_dir, args.artifact_dir)
    else:
        output = verify_result(args.data_dir, args.artifact_dir)
    print(json.dumps(output, sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()
