#!/usr/bin/env python3
"""One-shot Stx3 reward-relative population-geometry analysis.

Implements the frozen v1 contract plus its pre-outcome v1.1--v1.3
clarifications using only h5py, NumPy, and SciPy.  The independent unit is the
mouse; no cell/trial pseudoreplication enters the group tests.
"""

from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import math
import os
import platform
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

import h5py
import numpy as np
import scipy
from scipy.stats import rankdata

import audit_stx3_roi_aligner_maps as roi_audit_module
from audit_stx3_roi_aligner_maps import (
    DENSE_DAY0_DAY5_RAVEL,
    audit_dense_maps,
    load_day_pair,
)


CONTRACT_ID = "CE_NPF_ALT_BIO_STX3_REWARD_ALIGNMENT_XN_v1_3"
BASE_CONTRACT_SHA256 = "13bf98597f63fbb397cf86b0aa29404999eeb509a3f3a09e17fb7603d6eb576a"
PRIOR_ADDENDUM_SHA256 = "f7bf144585e19207a1289c85128c6b428a97433d3e355b7e389af0958911aa95"
STATISTICAL_ADDENDUM_SHA256 = (
    "6a096227441ce8bb2a562953870524d35973be260b38b3adb5a9f95055cffa09"
)
ADDENDUM_SHA256 = "c56d3c2aa0932ba4116ac96927c7bf3ecb0967bce158d79ebd85c18f0d37f829"
BLOCKED_PREFLIGHT_RECEIPT_SHA256 = (
    "d7913685d98457d91783bfa88a0891a7ab4dabcb4214e6dbf8117308f9e3036c"
)
FULL_BLOCK_OFFSET_MAP_SHA256 = (
    "399b783760b50e33d93206066a841ab0ce53773fe13b955593f83b727ff2c92c"
)
CODE_COMMIT = "f2ab24db8709a321d38576a1fa674f95035a2fec"
MOUSE_METADATA_SHA256 = "2a52a5561de9ea61c379b4e6997aa51429403dd75be58ed3fd99d7c56f58d68a"
OFFICIAL_SESSION_SHA256 = "82938af1cb7689fb9c919b29606fde9a121ac538e2e7db8c4532935cd07488a1"
OFFICIAL_BEHAVIOR_SHA256 = "e168df23550cae4e5dc1ee92dab7e3346db128fac43e7ae3646cb22c0a45188c"
OFFICIAL_UTILITIES_SHA256 = "cda27c7efe916eaf2ca478ecc574c34da10ea4426c4553367a434d0d68951d76"
OFFICIAL_REWARD_OVERREP_SHA256 = "81bfd032d0d10c083a6bbd61dc4e1148306ea3d157b963f4028d82466fabe3e7"
TWOPUTILS_SPATIAL_ANALYSES_SHA256 = (
    "da82bcec7813fcae838c3f4a892d282d87543120dc93533a76d504ee8a04199b"
)
TWOPUTILS_SESS_SHA256 = "888693b5652ad155384dd0654a4d5c98740e9fa9dc3b15bc1062ecab4514f919"
SELECTION_RECEIPT_SHA256 = "a2c139cff4312b7c3869465b355aa738552373d119f96c8aab3a5e4dc4982dfa"
SELECTION_CANONICAL_SHA256 = "3b2ceb2c5e3715d2f03a030070c06679a1b5d3fadbc63f2ae460f747e6f85663"
ROI_PAIR_CANONICAL_SHA256 = "c5ce0aca6ab6bcf4ac4294bb3b0cae97606d67b53a08333225f4191350149fe5"
ROI_AUDIT_SHA256 = "985dc4b2cc87cd4dadb5af65efa015579fa90fd0c68c68bea233fa06d2d94ae4"
PREFLIGHT_STATUS = "STX3_V1_3_FULL_PREFLIGHT_PASS"
TEST_STATUS = "STX3_V1_3_FOCUSED_TESTS_PASS"
EXPECTED_FOCUSED_TEST_COUNT = 35

SUBJECTS = tuple(
    [f"Ctrl_{index}" for index in range(1, 10)]
    + [f"Cre_{index}" for index in range(1, 8)]
)
GROUP_BY_SUBJECT = {
    subject: ("Ctrl" if subject.startswith("Ctrl_") else "Cre")
    for subject in SUBJECTS
}
LOCKED_FULL_BLOCK_OFFSETS = {
    (subject, day): (
        1
        if (subject, day) == ("Cre_1", 0)
        else 2
        if (subject, day) == ("Ctrl_4", 0)
        else 0
    )
    for subject in SUBJECTS
    for day in (0, 5)
}
NOVEL_ARM_BY_SUBJECT = {
    "Ctrl_1": -1,
    "Ctrl_2": 1,
    "Ctrl_3": -1,
    "Ctrl_4": 1,
    "Ctrl_5": -1,
    "Ctrl_6": 1,
    "Ctrl_7": -1,
    "Ctrl_8": 1,
    "Ctrl_9": -1,
    "Cre_1": -1,
    "Cre_2": 1,
    "Cre_3": -1,
    "Cre_4": 1,
    "Cre_5": -1,
    "Cre_6": -1,
    "Cre_7": 1,
}

BIN_EDGES = np.arange(13.0, 44.0, 1.0)
BIN_CENTERS = BIN_EDGES[:-1] + 0.5
N_BINS = 30
INTERIOR_FULL_INDICES = np.arange(1, 29, dtype=np.int64)
LEFT_TFRONT = 32.67690445738824
RIGHT_TFRONT = 39.83365218636522
LEFT_REWARD_FULL = np.arange(14, 19, dtype=np.int64)
RIGHT_REWARD_FULL = np.arange(21, 26, dtype=np.int64)
WRONG_SHIFTS = tuple(range(5, 24))
NONWRAP_SHIFTS = tuple(range(8, 24))
RIGHT_REQUIRED_FULL_INDICES = np.asarray(
    sorted(
        {
            int(((index - 1 + shift) % 28) + 1)
            for index in RIGHT_REWARD_FULL
            for shift in (0, *WRONG_SHIFTS)
        }
    ),
    dtype=np.int64,
)
FLOOR_MULTIPLIER = 1e-3
MIN_COMMON_ROIS = 20
MIN_TRIALS_PER_FOLD = 4
ASSOCIATION_PERMUTATIONS = 99_999
ASSOCIATION_SEED = 20_260_901

ALIGNED_PREFIX = "processing/behavior/2P-aligned behavior"
FULL_PREFIX = "processing/behavior/Full temporal resolution behavior"
F_DFF_PATH = "processing/ophys/dF/dF/data"
FLUORESCENCE_PATH = "processing/ophys/fluorescence/fluorescence/data"
NEUROPIL_PATH = "processing/ophys/neuropil/neuropil fluorescence/data"
SUBJECT_PATH = "general/subject/subject_id"
ANNOTATION_PATH = "acquisition/trial_cell_data/data"

PATH_RE = re.compile(
    r"^sub-(?P<subject>(?:Ctrl|Cre)-\d+)_ses-ymaze-day(?P<day>[05])-.*\.nwb$"
)


class ContractBlocked(RuntimeError):
    def __init__(self, status: str, message: str):
        super().__init__(message)
        self.status = status


@dataclass(frozen=True)
class Trial:
    ordinal: int
    block: int
    lr: int
    aligned_start: int
    aligned_end: int
    full_start: int
    full_end: int


@dataclass
class SessionData:
    subject: str
    day: int
    path: Path
    roi_indices: np.ndarray
    trials: list[Trial]
    neural_bins: np.ndarray
    speed_bins: np.ndarray
    lick_bins: np.ndarray
    behavior: list[dict[str, Any]]
    fold_ordinals: dict[int, dict[str, list[int]]]
    full_block_offset: int = 0
    boundary_timing_ms: dict[str, float] | None = None


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _full_block_offset_map_sha256() -> str:
    canonical = "\n".join(
        f"{subject}\t{day}\t{offset}"
        for (subject, day), offset in sorted(LOCKED_FULL_BLOCK_OFFSETS.items())
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _checked_file_sha256(path: Path, *, status: str, label: str) -> str:
    try:
        return file_sha256(path)
    except Exception as exc:
        raise ContractBlocked(status, f"cannot hash {label} {path}: {exc}") from exc


def _read_json(path: Path, *, status: str, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise ContractBlocked(status, f"cannot parse {label} JSON {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ContractBlocked(status, f"{label} JSON root is not an object: {path}")
    return value


def _decode_scalar(dataset: h5py.Dataset) -> str:
    value = dataset[()]
    if isinstance(value, bytes):
        return value.decode("utf-8")
    return str(value)


def _canonical_selection_hash(assets: list[dict[str, Any]]) -> str:
    lines = [
        f"{asset['path']}\t{asset['size']}\t{asset['sha256']}"
        for asset in sorted(assets, key=lambda item: item["path"])
    ]
    return hashlib.sha256("\n".join(lines).encode("utf-8")).hexdigest()


def _validate_asset_rows(value: Any, *, label: str) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        raise ContractBlocked("STX3_SOURCE_BLOCKED", f"{label} assets are not a list")
    rows: list[dict[str, Any]] = []
    seen_paths: set[str] = set()
    for index, item in enumerate(value):
        if not isinstance(item, dict):
            raise ContractBlocked("STX3_SOURCE_BLOCKED", f"{label} asset {index} is not an object")
        path = item.get("path")
        size = item.get("size")
        sha256 = item.get("sha256")
        if not isinstance(path, str) or not path or "\\" in path:
            raise ContractBlocked("STX3_SOURCE_BLOCKED", f"invalid {label} asset path at {index}")
        if path in seen_paths:
            raise ContractBlocked("STX3_SOURCE_BLOCKED", f"duplicate {label} asset path: {path}")
        if not isinstance(size, int) or isinstance(size, bool) or size <= 0:
            raise ContractBlocked("STX3_SOURCE_BLOCKED", f"invalid {label} asset size: {path}")
        if not isinstance(sha256, str) or re.fullmatch(r"[0-9a-f]{64}", sha256) is None:
            raise ContractBlocked("STX3_SOURCE_BLOCKED", f"invalid {label} asset SHA-256: {path}")
        seen_paths.add(path)
        rows.append(item)
    return rows


def validate_source_receipts(
    selection_path: Path,
    download_receipt_path: Path,
    data_root: Path,
) -> tuple[dict[tuple[str, int], dict[str, Any]], list[dict[str, Any]]]:
    selection = _read_json(selection_path, status="STX3_SOURCE_BLOCKED", label="selection")
    assets = _validate_asset_rows(selection.get("selected_assets", []), label="selection")
    if selection.get("status") != "DANDI_ASSET_SELECTION_AUDIT_PASS" or len(assets) != 32:
        raise ContractBlocked("STX3_SOURCE_BLOCKED", "selection receipt is not the locked 32-asset set")
    if _canonical_selection_hash(assets) != SELECTION_CANONICAL_SHA256:
        raise ContractBlocked("STX3_SOURCE_BLOCKED", "selection canonical hash mismatch")

    receipt = _read_json(
        download_receipt_path, status="STX3_SOURCE_BLOCKED", label="download receipt"
    )
    if receipt.get("status") != "DANDI_SELECTED_DOWNLOAD_PASS":
        raise ContractBlocked("STX3_SOURCE_BLOCKED", "download receipt is not PASS")
    if receipt.get("verified_asset_count") != 32:
        raise ContractBlocked("STX3_SOURCE_BLOCKED", "download receipt does not verify 32 assets")
    if receipt.get("verified_bytes") != 20_006_552_508:
        raise ContractBlocked("STX3_SOURCE_BLOCKED", "download byte total mismatch")

    receipt_assets = _validate_asset_rows(receipt.get("assets", []), label="download receipt")
    receipt_by_path = {item["path"]: item for item in receipt_assets}
    paths: dict[tuple[str, int], dict[str, Any]] = {}
    integrity_records: list[dict[str, Any]] = []
    for asset in sorted(assets, key=lambda item: item["path"]):
        relative = Path(*asset["path"].split("/"))
        local_path = data_root / relative
        match = PATH_RE.match(relative.name)
        if match is None:
            raise ContractBlocked("STX3_SOURCE_BLOCKED", f"unexpected selected path: {asset['path']}")
        subject = match.group("subject").replace("-", "_")
        day = int(match.group("day"))
        key = (subject, day)
        if key in paths:
            raise ContractBlocked("STX3_SOURCE_BLOCKED", f"duplicate subject/day asset: {key}")
        if not local_path.is_file() or local_path.stat().st_size != asset["size"]:
            raise ContractBlocked("STX3_SOURCE_BLOCKED", f"missing/size mismatch: {local_path}")
        receipt_asset = receipt_by_path.get(asset["path"])
        if receipt_asset is None or receipt_asset.get("sha256") != asset["sha256"]:
            raise ContractBlocked("STX3_SOURCE_BLOCKED", f"receipt identity mismatch: {asset['path']}")
        observed_sha256 = file_sha256(local_path)
        if observed_sha256 != asset["sha256"]:
            raise ContractBlocked("STX3_SOURCE_BLOCKED", f"current SHA-256 mismatch: {asset['path']}")
        paths[key] = {**asset, "local_path": local_path}
        integrity_records.append(
            {
                "subject": subject,
                "day": day,
                "path": local_path.as_posix(),
                "size": asset["size"],
                "sha256": observed_sha256,
            }
        )

    expected_keys = {(subject, day) for subject in SUBJECTS for day in (0, 5)}
    if set(paths) != expected_keys:
        missing = sorted(expected_keys.difference(paths))
        extra = sorted(set(paths).difference(expected_keys))
        raise ContractBlocked(
            "STX3_SOURCE_BLOCKED", f"subject/day key mismatch; missing={missing}, extra={extra}"
        )
    return paths, integrity_records


def _read_roi_columns(dataset: h5py.Dataset, indices: np.ndarray) -> np.ndarray:
    try:
        indices = np.asarray(indices, dtype=np.int64)
    except Exception as exc:
        raise ContractBlocked("STX3_REGISTRATION_BLOCKED", "ROI indices are not integers") from exc
    if indices.ndim != 1 or indices.size == 0 or np.unique(indices).size != indices.size:
        raise ContractBlocked("STX3_REGISTRATION_BLOCKED", "ROI indices must be nonempty and unique")
    if dataset.ndim != 2:
        raise ContractBlocked(
            "STX3_SCHEMA_BLOCKED", f"neural dataset must be 2-D, observed shape {dataset.shape}"
        )
    if indices.min() < 0 or indices.max() >= dataset.shape[1]:
        raise ContractBlocked(
            "STX3_REGISTRATION_BLOCKED",
            f"ROI index outside NWB columns: min={indices.min()}, max={indices.max()}, n={dataset.shape[1]}",
        )
    order = np.argsort(indices)
    sorted_data = np.asarray(dataset[:, indices[order]], dtype=np.float64)
    return sorted_data[:, np.argsort(order)]


def _event_indices(values: np.ndarray, label: str) -> np.ndarray:
    try:
        values = np.asarray(values, dtype=np.float64)
    except Exception as exc:
        raise ContractBlocked(
            "STX3_TRIAL_JOIN_BLOCKED", f"{label} event vector is not numeric"
        ) from exc
    if (
        values.ndim != 1
        or not np.all(np.isfinite(values))
        or not np.all(np.isin(values, (0.0, 1.0)))
    ):
        raise ContractBlocked(
            "STX3_TRIAL_JOIN_BLOCKED",
            f"{label} event vector must be finite, 1-D, and exactly binary",
        )
    return np.flatnonzero(values == 1).astype(np.int64)


def _integer_array(value: Any, label: str) -> np.ndarray:
    try:
        array = np.asarray(value, dtype=np.float64)
    except Exception as exc:
        raise ContractBlocked("STX3_SCHEMA_BLOCKED", f"{label} is not numeric") from exc
    if (
        array.ndim != 1
        or not np.all(np.isfinite(array))
        or not np.all(array == np.floor(array))
    ):
        raise ContractBlocked("STX3_SCHEMA_BLOCKED", f"{label} is not a finite integer vector")
    return array.astype(np.int64)


def _finite_unique(segment: np.ndarray, label: str) -> int:
    try:
        segment = np.asarray(segment, dtype=np.float64)
    except Exception as exc:
        raise ContractBlocked(
            "STX3_TRIAL_JOIN_BLOCKED", f"{label} contains nonnumeric samples"
        ) from exc
    if segment.ndim != 1 or segment.size == 0 or not np.all(np.isfinite(segment)):
        raise ContractBlocked(
            "STX3_TRIAL_JOIN_BLOCKED", f"{label} contains missing/nonfinite samples"
        )
    unique = np.unique(segment)
    if unique.size != 1 or not float(unique[0]).is_integer():
        raise ContractBlocked(
            "STX3_TRIAL_JOIN_BLOCKED", f"{label} is not one finite integer: {unique.tolist()}"
        )
    return int(unique[0])


def _numeric_leaves(value: Any, *, label: str) -> list[float]:
    if isinstance(value, dict):
        leaves: list[float] = []
        for key, child in value.items():
            leaves.extend(_numeric_leaves(child, label=f"{label}.{key}"))
        return leaves
    if isinstance(value, (list, tuple)):
        leaves = []
        for index, child in enumerate(value):
            leaves.extend(_numeric_leaves(child, label=f"{label}[{index}]"))
        return leaves
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ContractBlocked("STX3_SCHEMA_BLOCKED", f"{label} is not numeric")
    number = float(value)
    if not math.isfinite(number):
        raise ContractBlocked("STX3_SCHEMA_BLOCKED", f"{label} is nonfinite")
    return [number]


def _validate_optional_reward_fronts(metadata: dict[str, Any], path: Path) -> None:
    """Validate any provider annotation that independently repeats reward fronts."""

    accepted_keys = {
        "tfront",
        "tfronts",
        "rewardfront",
        "rewardfronts",
        "rewardzonefront",
        "rewardzonefronts",
    }
    observed: list[tuple[str, Any]] = []

    def visit(value: Any, prefix: str) -> None:
        if not isinstance(value, dict):
            return
        for key, child in value.items():
            label = f"{prefix}.{key}" if prefix else str(key)
            normalized = re.sub(r"[\s_\-]", "", str(key)).lower()
            if normalized in accepted_keys:
                observed.append((label, child))
            elif isinstance(child, dict):
                visit(child, label)

    visit(metadata, "")
    for label, value in observed:
        leaves = _numeric_leaves(value, label=label)
        if not leaves:
            raise ContractBlocked("STX3_SCHEMA_BLOCKED", f"empty reward-front annotation in {path}")
        for number in leaves:
            if not (
                math.isclose(number, LEFT_TFRONT, rel_tol=0.0, abs_tol=1e-9)
                or math.isclose(number, RIGHT_TFRONT, rel_tol=0.0, abs_tol=1e-9)
            ):
                raise ContractBlocked(
                    "STX3_SCHEMA_BLOCKED",
                    f"reward-front annotation {label}={number} disagrees with frozen fronts in {path}",
                )


def _validate_ordered_boundaries(starts: np.ndarray, ends: np.ndarray, label: str) -> None:
    if starts.size != ends.size or starts.size == 0:
        raise ContractBlocked(
            "STX3_TRIAL_JOIN_BLOCKED",
            f"{label} start/end count mismatch: {starts.size}/{ends.size}",
        )
    if np.any(starts >= ends):
        raise ContractBlocked("STX3_TRIAL_JOIN_BLOCKED", f"{label} has start >= end")
    if starts.size > 1 and np.any(ends[:-1] > starts[1:]):
        raise ContractBlocked("STX3_TRIAL_JOIN_BLOCKED", f"{label} trials overlap")


def _trial_bin_means(
    values: np.ndarray,
    positions: np.ndarray,
    trials: list[Trial],
    *,
    aligned: bool,
) -> np.ndarray:
    values = np.asarray(values, dtype=np.float64)
    positions = np.asarray(positions, dtype=np.float64)
    if values.shape[0] != positions.shape[0]:
        raise ContractBlocked("STX3_SCHEMA_BLOCKED", "value/position length mismatch")
    tail_shape = values.shape[1:]
    result = np.full((len(trials), N_BINS, *tail_shape), np.nan, dtype=np.float64)
    for trial_index, trial in enumerate(trials):
        start = trial.aligned_start if aligned else trial.full_start
        end = trial.aligned_end if aligned else trial.full_end
        pos = positions[start:end]
        trial_values = values[start:end]
        # Pinned TwoPUtils convention: trial [start, stop), bins (left, right].
        bin_indices = np.searchsorted(BIN_EDGES, pos, side="left") - 1
        for bin_index in range(N_BINS):
            mask = (bin_indices == bin_index) & np.isfinite(pos)
            if not np.any(mask):
                continue
            selected = trial_values[mask]
            finite = np.isfinite(selected)
            counts = np.sum(finite, axis=0)
            totals = np.sum(np.where(finite, selected, 0.0), axis=0)
            np.divide(
                totals,
                counts,
                out=result[trial_index, bin_index],
                where=counts > 0,
            )
    return result


def _build_fold_ordinals(trials: list[Trial]) -> dict[int, dict[str, list[int]]]:
    output: dict[int, dict[str, list[int]]] = {}
    cycle = ("A", "B", "H")
    for lr in (-1, 1):
        selected = [trial.ordinal for trial in trials if trial.block == 5 and trial.lr == lr]
        folds = {"A": [], "B": [], "H": []}
        for local_index, ordinal in enumerate(selected):
            folds[cycle[local_index % 3]].append(ordinal)
        if any(len(folds[name]) < MIN_TRIALS_PER_FOLD for name in cycle):
            raise ContractBlocked(
                "STX3_TRIAL_JOIN_BLOCKED",
                f"block5 LR={lr} fold counts below {MIN_TRIALS_PER_FOLD}: "
                f"{ {name: len(values) for name, values in folds.items()} }",
            )
        output[lr] = folds
    return output


def _metadata_array(container: dict[str, Any], key: str, label: str) -> np.ndarray:
    if key not in container:
        raise ContractBlocked("STX3_SCHEMA_BLOCKED", f"missing metadata {label}.{key}")
    try:
        array = np.asarray(container[key], dtype=np.float64)
    except Exception as exc:
        raise ContractBlocked("STX3_SCHEMA_BLOCKED", f"invalid metadata {label}.{key}") from exc
    if array.ndim != 1 or not np.all(np.isfinite(array)):
        raise ContractBlocked("STX3_SCHEMA_BLOCKED", f"invalid metadata {label}.{key}")
    return array


def _metadata_integer_array(container: dict[str, Any], key: str, label: str) -> np.ndarray:
    if key not in container:
        raise ContractBlocked("STX3_SCHEMA_BLOCKED", f"missing metadata {label}.{key}")
    return _integer_array(container[key], f"metadata {label}.{key}")


def _validate_signal_family(
    nwb: h5py.File, prefix: str, signals: tuple[str, ...]
) -> int:
    canonical_timestamps: np.ndarray | None = None
    expected_length: int | None = None
    for signal in signals:
        data_path = f"{prefix}/{signal}/data"
        timestamp_path = f"{prefix}/{signal}/timestamps"
        if data_path not in nwb or timestamp_path not in nwb:
            raise ContractBlocked(
                "STX3_SCHEMA_BLOCKED", f"missing {signal} data/timestamps under {prefix}"
            )
        dataset = nwb[data_path]
        timestamps = np.asarray(nwb[timestamp_path][:], dtype=np.float64)
        if dataset.ndim != 1 or timestamps.ndim != 1 or dataset.shape[0] != timestamps.size:
            raise ContractBlocked(
                "STX3_SCHEMA_BLOCKED", f"invalid {signal} data/timestamp shape under {prefix}"
            )
        if not np.all(np.isfinite(timestamps)) or np.any(np.diff(timestamps) <= 0):
            raise ContractBlocked(
                "STX3_SCHEMA_BLOCKED", f"nonfinite/nonmonotone {signal} timestamps under {prefix}"
            )
        if canonical_timestamps is None:
            canonical_timestamps = timestamps
            expected_length = timestamps.size
        elif not np.array_equal(timestamps, canonical_timestamps):
            raise ContractBlocked(
                "STX3_SCHEMA_BLOCKED", f"timestamp mismatch for {signal} under {prefix}"
            )
    if expected_length is None:
        raise ContractBlocked("STX3_SCHEMA_BLOCKED", f"empty signal family: {prefix}")
    return expected_length


def load_session(
    path: Path,
    *,
    expected_subject: str,
    expected_day: int,
    expected_ravel: int,
    expected_novel_arm: int,
    roi_indices: np.ndarray,
) -> SessionData:
    try:
        nwb = h5py.File(path, "r")
    except Exception as exc:
        raise ContractBlocked("STX3_SCHEMA_BLOCKED", f"cannot open {path}: {exc}") from exc

    with nwb:
        required = [
            SUBJECT_PATH,
            ANNOTATION_PATH,
            F_DFF_PATH,
            FLUORESCENCE_PATH,
            NEUROPIL_PATH,
        ]
        missing = [dataset_path for dataset_path in required if dataset_path not in nwb]
        if missing:
            raise ContractBlocked("STX3_SCHEMA_BLOCKED", f"missing datasets in {path}: {missing}")

        aligned_signals = (
            "position",
            "speed",
            "licks",
            "reward",
            "block",
            "left or right",
            "trial start",
            "trial end",
            "trial number",
        )
        full_signals = (
            "position",
            "speed",
            "non-consummatory licks",
            "reward",
            "manual rewards",
            "block",
            "left or right",
            "trial start",
            "trial end",
            "trial number",
        )
        aligned_length = _validate_signal_family(nwb, ALIGNED_PREFIX, aligned_signals)
        full_length = _validate_signal_family(nwb, FULL_PREFIX, full_signals)

        neural_shapes = {
            tuple(nwb[dataset_path].shape)
            for dataset_path in (F_DFF_PATH, FLUORESCENCE_PATH, NEUROPIL_PATH)
        }
        if len(neural_shapes) != 1:
            raise ContractBlocked("STX3_SCHEMA_BLOCKED", f"neural array shape mismatch in {path}")
        neural_shape = next(iter(neural_shapes))
        if len(neural_shape) != 2 or neural_shape[0] != aligned_length:
            raise ContractBlocked(
                "STX3_SCHEMA_BLOCKED",
                f"neural arrays are not aligned (frames, ROI) in {path}: {neural_shape}",
            )

        subject_id = _decode_scalar(nwb[SUBJECT_PATH]).replace("-", "_")
        if subject_id != expected_subject:
            raise ContractBlocked(
                "STX3_SCHEMA_BLOCKED", f"subject mismatch in {path}: {subject_id} != {expected_subject}"
            )

        raw_annotation = nwb[ANNOTATION_PATH][0]
        if isinstance(raw_annotation, bytes):
            raw_annotation = raw_annotation.decode("utf-8")
        try:
            metadata = json.loads(str(raw_annotation))
        except Exception as exc:
            raise ContractBlocked(
                "STX3_SCHEMA_BLOCKED", f"cannot parse trial annotation JSON in {path}: {exc}"
            ) from exc
        if not isinstance(metadata, dict):
            raise ContractBlocked("STX3_SCHEMA_BLOCKED", f"trial annotation root is not an object: {path}")
        _validate_optional_reward_fronts(metadata, path)
        metadata_day = metadata.get("day", None)
        if not isinstance(metadata_day, (int, float)) or not math.isfinite(float(metadata_day)):
            raise ContractBlocked("STX3_SCHEMA_BLOCKED", f"invalid metadata day in {path}")
        if float(metadata_day) != int(float(metadata_day)) or int(metadata_day) != expected_day:
            raise ContractBlocked("STX3_SCHEMA_BLOCKED", f"metadata day mismatch in {path}")
        if str(metadata.get("mouse", "")).replace("-", "_") != expected_subject:
            raise ContractBlocked("STX3_SCHEMA_BLOCKED", f"metadata mouse mismatch in {path}")
        if bool(metadata.get("mux", True)):
            raise ContractBlocked("STX3_SCHEMA_BLOCKED", f"dense session unexpectedly marked mux: {path}")
        novel_arm = metadata.get("novel_arm", None)
        if (
            not isinstance(novel_arm, (int, float))
            or not math.isfinite(float(novel_arm))
            or float(novel_arm) != int(float(novel_arm))
            or int(novel_arm) != expected_novel_arm
        ):
            raise ContractBlocked("STX3_SCHEMA_BLOCKED", f"novel-arm metadata mismatch in {path}")

        # ravel_ind is not stored in every annotation; when present it must agree.
        if "ravel_ind" in metadata:
            ravel = metadata["ravel_ind"]
            if (
                not isinstance(ravel, (int, float))
                or not math.isfinite(float(ravel))
                or float(ravel) != int(float(ravel))
                or int(ravel) != expected_ravel
            ):
                raise ContractBlocked("STX3_REGISTRATION_BLOCKED", f"ravel index mismatch in {path}")

        trial_info = metadata.get("trial_info")
        if not isinstance(trial_info, dict):
            raise ContractBlocked("STX3_SCHEMA_BLOCKED", f"missing trial metadata in {path}")
        block = _metadata_integer_array(trial_info, "block_number", "trial_info")
        lr = _metadata_integer_array(trial_info, "LR", "trial_info")
        if not np.all(np.isin(block, np.arange(6))) or not np.all(np.isin(lr, (-1, 1))):
            raise ContractBlocked("STX3_TRIAL_JOIN_BLOCKED", f"invalid block/LR metadata: {path}")
        vr_trial_info = metadata.get("vr_trial_info")
        if not isinstance(vr_trial_info, dict):
            raise ContractBlocked(
                "STX3_SCHEMA_BLOCKED", f"missing full-resolution trial metadata in {path}"
            )
        vr_block = _metadata_integer_array(
            vr_trial_info, "block_number", "vr_trial_info"
        )
        vr_lr = _metadata_integer_array(vr_trial_info, "LR", "vr_trial_info")
        if not np.all(np.isin(vr_block, np.arange(6))) or not np.all(
            np.isin(vr_lr, (-1, 1))
        ):
            raise ContractBlocked(
                "STX3_TRIAL_JOIN_BLOCKED", f"invalid full-resolution block/LR metadata: {path}"
            )

        aligned_starts = _event_indices(nwb[f"{ALIGNED_PREFIX}/trial start/data"][:], "aligned start")
        aligned_ends = _event_indices(nwb[f"{ALIGNED_PREFIX}/trial end/data"][:], "aligned end")
        full_starts = _event_indices(nwb[f"{FULL_PREFIX}/trial start/data"][:], "full start")
        full_ends = _event_indices(nwb[f"{FULL_PREFIX}/trial end/data"][:], "full end")
        _validate_ordered_boundaries(aligned_starts, aligned_ends, "aligned")
        _validate_ordered_boundaries(full_starts, full_ends, "full")
        if (
            aligned_ends[-1] >= aligned_length
            or full_ends[-1] >= full_length
            or aligned_starts[0] < 0
            or full_starts[0] < 0
        ):
            raise ContractBlocked("STX3_TRIAL_JOIN_BLOCKED", f"trial boundary outside data in {path}")

        metadata_starts = _integer_array(
            metadata.get("trial_start_inds", []), "metadata trial_start_inds"
        )
        metadata_ends = _integer_array(
            metadata.get("teleport_inds", []), "metadata teleport_inds"
        )
        if not np.array_equal(aligned_starts, metadata_starts):
            raise ContractBlocked("STX3_TRIAL_JOIN_BLOCKED", f"aligned start indices mismatch: {path}")
        if not np.array_equal(aligned_ends, metadata_ends):
            raise ContractBlocked("STX3_TRIAL_JOIN_BLOCKED", f"aligned end indices mismatch: {path}")

        n_trials = block.size
        if not (
            lr.size == n_trials
            and vr_block.size == n_trials
            and vr_lr.size == n_trials
            and aligned_starts.size == n_trials
            and aligned_ends.size == n_trials
            and full_starts.size == n_trials
            and full_ends.size == n_trials
        ):
            raise ContractBlocked("STX3_TRIAL_JOIN_BLOCKED", f"trial count mismatch in {path}")
        if not np.array_equal(lr, vr_lr):
            raise ContractBlocked(
                "STX3_TRIAL_JOIN_BLOCKED",
                f"neural/full metadata LR mismatch in {path}",
            )

        aligned_block = np.asarray(nwb[f"{ALIGNED_PREFIX}/block/data"][:], dtype=np.float64)
        aligned_lr = np.asarray(nwb[f"{ALIGNED_PREFIX}/left or right/data"][:], dtype=np.float64)
        aligned_trial_number = np.asarray(
            nwb[f"{ALIGNED_PREFIX}/trial number/data"][:], dtype=np.float64
        )
        full_block = np.asarray(nwb[f"{FULL_PREFIX}/block/data"][:], dtype=np.float64)
        full_lr = np.asarray(nwb[f"{FULL_PREFIX}/left or right/data"][:], dtype=np.float64)
        full_trial_number = np.asarray(
            nwb[f"{FULL_PREFIX}/trial number/data"][:], dtype=np.float64
        )
        trials: list[Trial] = []
        observed_trial_numbers: list[int] = []
        observed_block_offsets: list[int] = []
        for index in range(n_trials):
            expected_block = int(block[index])
            expected_lr_value = int(lr[index])
            expected_full_block = int(vr_block[index])
            expected_full_lr = int(vr_lr[index])
            a_start, a_end = int(aligned_starts[index]), int(aligned_ends[index])
            f_start, f_end = int(full_starts[index]), int(full_ends[index])
            observed = (
                _finite_unique(aligned_block[a_start:a_end], "aligned block"),
                _finite_unique(aligned_lr[a_start:a_end], "aligned LR"),
                _finite_unique(full_block[f_start:f_end], "full block"),
                _finite_unique(full_lr[f_start:f_end], "full LR"),
            )
            expected = (
                expected_block,
                expected_lr_value,
                expected_full_block,
                expected_full_lr,
            )
            if observed != expected:
                raise ContractBlocked(
                    "STX3_TRIAL_JOIN_BLOCKED",
                    f"trial ordinal {index} block/LR mismatch in {path}: "
                    f"observed={observed}, metadata={expected}",
                )
            aligned_number = _finite_unique(
                aligned_trial_number[a_start:a_end], "aligned trial number"
            )
            full_number = _finite_unique(
                full_trial_number[f_start:f_end], "full trial number"
            )
            if aligned_number != full_number:
                raise ContractBlocked(
                    "STX3_TRIAL_JOIN_BLOCKED",
                    f"trial ordinal {index} aligned/full number mismatch in {path}: "
                    f"{aligned_number}/{full_number}",
                )
            observed_trial_numbers.append(aligned_number)
            observed_block_offsets.append(expected_block - expected_full_block)
            trials.append(
                Trial(
                    ordinal=index,
                    block=expected_block,
                    lr=expected_lr_value,
                    aligned_start=a_start,
                    aligned_end=a_end,
                    full_start=f_start,
                    full_end=f_end,
                )
            )

        locked_offset = LOCKED_FULL_BLOCK_OFFSETS.get((expected_subject, expected_day))
        if locked_offset is None:
            raise ContractBlocked(
                "STX3_TRIAL_JOIN_BLOCKED",
                f"session is absent from the locked full-block offset map: "
                f"{expected_subject}/day{expected_day}",
            )
        unique_offsets = sorted(set(observed_block_offsets))
        if unique_offsets != [locked_offset]:
            raise ContractBlocked(
                "STX3_TRIAL_JOIN_BLOCKED",
                f"global-minus-local block offset mismatch in {path}: "
                f"observed={unique_offsets}, locked={locked_offset}",
            )

        expected_trial_numbers = np.arange(
            observed_trial_numbers[0],
            observed_trial_numbers[0] + n_trials,
            dtype=np.int64,
        )
        if not np.array_equal(np.asarray(observed_trial_numbers), expected_trial_numbers):
            raise ContractBlocked(
                "STX3_TRIAL_JOIN_BLOCKED",
                f"aligned/full trial-number series is not consecutive in {path}",
            )

        aligned_timestamps = np.asarray(
            nwb[f"{ALIGNED_PREFIX}/position/timestamps"][:], dtype=np.float64
        )
        full_timestamps = np.asarray(
            nwb[f"{FULL_PREFIX}/position/timestamps"][:], dtype=np.float64
        )
        start_delta_ms = 1000.0 * (
            aligned_timestamps[aligned_starts] - full_timestamps[full_starts]
        )
        end_delta_ms = 1000.0 * (
            aligned_timestamps[aligned_ends] - full_timestamps[full_ends]
        )
        boundary_timing_ms = {
            "start_min": float(np.min(start_delta_ms)),
            "start_max": float(np.max(start_delta_ms)),
            "start_max_abs": float(np.max(np.abs(start_delta_ms))),
            "end_min": float(np.min(end_delta_ms)),
            "end_max": float(np.max(end_delta_ms)),
            "end_max_abs": float(np.max(np.abs(end_delta_ms))),
        }

        fold_ordinals = _build_fold_ordinals(trials)
        f_dff_dataset = nwb[F_DFF_PATH]
        f_dff = _read_roi_columns(f_dff_dataset, roi_indices)
        aligned_position = np.asarray(nwb[f"{ALIGNED_PREFIX}/position/data"][:], dtype=np.float64)
        aligned_speed = np.asarray(nwb[f"{ALIGNED_PREFIX}/speed/data"][:], dtype=np.float64)
        aligned_lick = np.asarray(nwb[f"{ALIGNED_PREFIX}/licks/data"][:], dtype=np.float64)
        if not (
            f_dff.shape[0]
            == aligned_position.size
            == aligned_speed.size
            == aligned_lick.size
        ):
            raise ContractBlocked("STX3_SCHEMA_BLOCKED", f"aligned length mismatch: {path}")

        neural_bins = _trial_bin_means(f_dff, aligned_position, trials, aligned=True)
        speed_bins = _trial_bin_means(aligned_speed[:, None], aligned_position, trials, aligned=True)[..., 0]
        lick_bins = _trial_bin_means(aligned_lick[:, None], aligned_position, trials, aligned=True)[..., 0]

        full_position = np.asarray(nwb[f"{FULL_PREFIX}/position/data"][:], dtype=np.float64)
        full_speed = np.asarray(nwb[f"{FULL_PREFIX}/speed/data"][:], dtype=np.float64)
        full_lick = np.asarray(
            nwb[f"{FULL_PREFIX}/non-consummatory licks/data"][:], dtype=np.float64
        )
        full_reward = np.asarray(nwb[f"{FULL_PREFIX}/reward/data"][:], dtype=np.float64)
        full_manual_reward = np.asarray(
            nwb[f"{FULL_PREFIX}/manual rewards/data"][:], dtype=np.float64
        )
        if not (
            full_position.size
            == full_speed.size
            == full_lick.size
            == full_reward.size
            == full_manual_reward.size
            == full_length
        ):
            raise ContractBlocked("STX3_SCHEMA_BLOCKED", f"full-resolution length mismatch: {path}")
        if not np.all(np.isfinite(full_reward)) or not np.all(
            np.isfinite(full_manual_reward)
        ):
            raise ContractBlocked(
                "STX3_SCHEMA_BLOCKED", f"nonfinite reward/manual-reward event in {path}"
            )
        if np.any(full_reward < 0) or np.any(full_manual_reward < 0):
            raise ContractBlocked("STX3_SCHEMA_BLOCKED", f"negative reward event in {path}")

        behavior: list[dict[str, Any]] = []
        for trial in trials:
            sl = slice(trial.full_start, trial.full_end)
            pos = full_position[sl]
            lick_values = full_lick[sl]
            speed_values = full_speed[sl]
            reward_values = full_reward[sl]
            manual_reward_values = full_manual_reward[sl]
            if np.any(lick_values[np.isfinite(lick_values)] < 0):
                raise ContractBlocked("STX3_SCHEMA_BLOCKED", f"negative lick event in {path}")

            delivery = np.flatnonzero(
                (reward_values > 0) | (manual_reward_values > 0)
            )
            cutoff = int(delivery[0]) if delivery.size else pos.size
            pos = pos[:cutoff]
            lick_values = lick_values[:cutoff]
            speed_values = speed_values[:cutoff]
            front = LEFT_TFRONT if trial.lr == -1 else RIGHT_TFRONT
            whole_mask = np.isfinite(pos) & (pos >= 13.0) & (pos < 43.0)
            pre_mask = whole_mask & (pos >= front - 3.0) & (pos < front)
            finite_lick = np.isfinite(lick_values)
            finite_speed = np.isfinite(speed_values)
            whole_licks = float(np.sum(lick_values[whole_mask & finite_lick]))
            pre_licks = float(np.sum(lick_values[pre_mask & finite_lick]))
            eligible_speed = speed_values[whole_mask & finite_speed]
            trial_speed = float(np.mean(eligible_speed)) if eligible_speed.size else math.nan
            omitted = bool(delivery.size == 0)
            behavior.append(
                {
                    "ordinal": trial.ordinal,
                    "block": trial.block,
                    "lr": trial.lr,
                    "whole_licks": whole_licks,
                    "pre_licks": pre_licks,
                    "whole_speed": trial_speed,
                    "omitted": omitted,
                }
            )

    return SessionData(
        subject=expected_subject,
        day=expected_day,
        path=path,
        roi_indices=np.asarray(roi_indices, dtype=np.int64),
        trials=trials,
        neural_bins=neural_bins,
        speed_bins=speed_bins,
        lick_bins=lick_bins,
        behavior=behavior,
        fold_ordinals=fold_ordinals,
        full_block_offset=locked_offset,
        boundary_timing_ms=boundary_timing_ms,
    )


def _training_references(
    sessions: dict[int, SessionData],
) -> tuple[list[tuple[int, int, int]], np.ndarray, np.ndarray, np.ndarray]:
    references: list[tuple[int, int, int]] = []
    categories: list[tuple[int, int, int]] = []
    speeds: list[float] = []
    licks: list[float] = []
    for day in (0, 5):
        session = sessions[day]
        for trial in session.trials:
            if trial.block >= 5:
                continue
            for bin_index in range(N_BINS):
                speed = float(session.speed_bins[trial.ordinal, bin_index])
                lick = float(session.lick_bins[trial.ordinal, bin_index])
                if not (math.isfinite(speed) and math.isfinite(lick)):
                    continue
                references.append((day, trial.ordinal, bin_index))
                categories.append((day, trial.lr, bin_index))
                speeds.append(speed)
                licks.append(lick)
    if not references:
        raise ContractBlocked("STX3_NUMERICAL_BLOCKED", "no blocks0-4 training observations")
    category_lookup = {
        category: index for index, category in enumerate(sorted(set(categories)))
    }
    codes = np.asarray([category_lookup[category] for category in categories], dtype=np.int64)
    return references, codes, np.asarray(speeds), np.asarray(licks)


def _matrix_from_references(
    arrays: dict[int, np.ndarray], references: list[tuple[int, int, int]]
) -> np.ndarray:
    return np.vstack([arrays[day][trial, bin_index] for day, trial, bin_index in references])


def _equal_trial_nanmean(selected: np.ndarray) -> np.ndarray:
    selected = np.asarray(selected, dtype=np.float64)
    finite = np.isfinite(selected)
    counts = np.sum(finite, axis=0)
    totals = np.sum(np.where(finite, selected, 0.0), axis=0)
    output = np.full(selected.shape[1:], np.nan, dtype=np.float64)
    np.divide(totals, counts, out=output, where=counts > 0)
    return output


def _raw_endpoint_cell_mask(sessions: dict[int, SessionData]) -> np.ndarray:
    cell_count = sessions[0].neural_bins.shape[-1]
    mask = np.ones(cell_count, dtype=bool)
    for day in (0, 5):
        session = sessions[day]
        for fold in ("A", "B"):
            for lr, required_bins in (
                (-1, LEFT_REWARD_FULL),
                (1, RIGHT_REQUIRED_FULL_INDICES),
            ):
                ordinals = session.fold_ordinals[lr][fold]
                ratemap = _equal_trial_nanmean(
                    session.neural_bins[np.asarray(ordinals, dtype=np.int64)]
                )
                mask &= np.all(np.isfinite(ratemap[required_bins]), axis=0)
    return mask


def _require_complete_endpoint_population(
    sessions: dict[int, SessionData], *, subject: str
) -> np.ndarray:
    """Freeze the aligner population; never select cells using endpoint values."""

    mask = _raw_endpoint_cell_mask(sessions)
    missing = np.flatnonzero(~mask)
    if missing.size:
        raise ContractBlocked(
            "STX3_REGISTRATION_BLOCKED",
            f"{subject} has {missing.size}/{mask.size} mapped ROIs with an incomplete "
            "raw endpoint; endpoint-based cell deletion is forbidden",
        )
    return np.ones(mask.size, dtype=bool)


def _apply_cell_mask(sessions: dict[int, SessionData], mask: np.ndarray) -> None:
    for session in sessions.values():
        session.roi_indices = session.roi_indices[mask]
        session.neural_bins = session.neural_bins[..., mask]


def _group_demean(matrix: np.ndarray, codes: np.ndarray) -> np.ndarray:
    matrix = np.asarray(matrix, dtype=np.float64)
    output = matrix.copy()
    for code in np.unique(codes):
        mask = codes == code
        output[mask] -= np.mean(output[mask], axis=0, keepdims=True)
    return output


def _cell_axis_demean(array: np.ndarray) -> np.ndarray:
    array = np.asarray(array, dtype=np.float64)
    output = np.full_like(array, np.nan)
    valid = np.all(np.isfinite(array), axis=-1)
    if np.any(valid):
        selected = array[valid]
        output[valid] = selected - np.mean(selected, axis=-1, keepdims=True)
    return output


def _fit_motor_coefficients(
    raw_training: np.ndarray,
    category_codes: np.ndarray,
    speeds: np.ndarray,
    licks: np.ndarray,
) -> dict[str, Any]:
    speed_mean = float(np.mean(speeds))
    speed_sd = float(np.std(speeds, ddof=0))
    lick_mean = float(np.mean(licks))
    lick_sd = float(np.std(licks, ddof=0))
    if not math.isfinite(speed_sd) or speed_sd <= 0:
        raise ContractBlocked("STX3_NUMERICAL_BLOCKED", "blocks0-4 speed SD is zero/nonfinite")
    if not math.isfinite(lick_sd) or lick_sd <= 0:
        raise ContractBlocked("STX3_NUMERICAL_BLOCKED", "blocks0-4 lick SD is zero/nonfinite")
    z_speed = (speeds - speed_mean) / speed_sd
    z_lick = (licks - lick_mean) / lick_sd
    design = np.column_stack([z_speed, z_lick])

    design_residual = _group_demean(design, category_codes)
    response_residual = _group_demean(raw_training, category_codes)
    expected_rank = design.shape[1]
    observed_rank = int(np.linalg.matrix_rank(design_residual))
    if observed_rank != expected_rank:
        raise ContractBlocked(
            "STX3_NUMERICAL_BLOCKED",
            f"motor nuisance design rank {observed_rank} != {expected_rank}",
        )
    coefficients = np.linalg.lstsq(design_residual, response_residual, rcond=None)[0]
    beta = coefficients[0]
    gamma = coefficients[1]
    if not np.all(np.isfinite(beta)) or not np.all(np.isfinite(gamma)):
        raise ContractBlocked("STX3_NUMERICAL_BLOCKED", "nonfinite motor coefficients")
    return {
        "speed_mean": speed_mean,
        "speed_sd": speed_sd,
        "lick_mean": lick_mean,
        "lick_sd": lick_sd,
        "beta": beta,
        "gamma": gamma,
        "training_rows": int(raw_training.shape[0]),
        "category_count": int(np.unique(category_codes).size),
        "design_rank": observed_rank,
    }


def _motor_transform(
    session: SessionData, coefficients: dict[str, Any]
) -> np.ndarray:
    z_speed = (session.speed_bins - coefficients["speed_mean"]) / coefficients["speed_sd"]
    z_lick = (session.lick_bins - coefficients["lick_mean"]) / coefficients["lick_sd"]
    transformed = (
        session.neural_bins
        - z_speed[..., None] * coefficients["beta"]
        - z_lick[..., None] * coefficients["gamma"]
    )
    return _cell_axis_demean(transformed)


def _estimate_precision(training: np.ndarray, category_codes: np.ndarray) -> dict[str, Any]:
    if training.ndim != 2 or training.shape[0] != category_codes.size:
        raise ContractBlocked("STX3_NUMERICAL_BLOCKED", "invalid precision training matrix")
    if not np.all(np.isfinite(training)):
        raise ContractBlocked("STX3_NUMERICAL_BLOCKED", "nonfinite precision training values")
    residual = _group_demean(training, category_codes)
    variance = np.var(residual, axis=0, ddof=1)
    if not np.all(np.isfinite(variance)):
        raise ContractBlocked("STX3_NUMERICAL_BLOCKED", "nonfinite residual variance")
    positive = variance[np.isfinite(variance) & (variance > 0)]
    if positive.size == 0:
        raise ContractBlocked("STX3_NUMERICAL_BLOCKED", "no positive residual variance")
    floor = float(np.median(positive) * FLOOR_MULTIPLIER)
    if not math.isfinite(floor) or floor <= 0:
        raise ContractBlocked("STX3_NUMERICAL_BLOCKED", "invalid variance floor")
    precision = 1.0 / np.maximum(variance, floor)
    if not np.all(np.isfinite(precision)):
        raise ContractBlocked("STX3_NUMERICAL_BLOCKED", "nonfinite diagonal precision")
    return {
        "precision": precision,
        "variance_floor": floor,
        "variance_min": float(np.min(variance)),
        "variance_median": float(np.median(variance)),
        "variance_max": float(np.max(variance)),
        "residual_rows": int(residual.shape[0]),
    }


def _fold_ratemap(
    array: np.ndarray, session: SessionData, lr: int, fold: str
) -> np.ndarray:
    ordinals = np.asarray(session.fold_ordinals[lr][fold], dtype=np.int64)
    selected = array[ordinals]
    return _equal_trial_nanmean(selected)


def _validate_endpoint_trial_vectors(
    array: np.ndarray, session: SessionData, *, variant: str
) -> None:
    """Sensitivity transforms may not recover endpoint vectors by dropping trials."""

    for lr, required_bins in (
        (-1, LEFT_REWARD_FULL),
        (1, RIGHT_REQUIRED_FULL_INDICES),
    ):
        for fold in ("A", "B"):
            ordinals = np.asarray(session.fold_ordinals[lr][fold], dtype=np.int64)
            selected = array[np.ix_(ordinals, required_bins, np.arange(array.shape[-1]))]
            if not np.all(np.isfinite(selected)):
                raise ContractBlocked(
                    "STX3_NUMERICAL_BLOCKED",
                    f"{variant} has nonfinite required trial vector: "
                    f"{session.subject} day{session.day} LR={lr} fold={fold}",
                )


def reward_alignment_bilinear_proxy(
    sessions: dict[int, SessionData],
    arrays: dict[int, np.ndarray],
    precision: np.ndarray,
    *,
    wrong_shifts: Iterable[int] = WRONG_SHIFTS,
    strict_trial_vectors: bool = False,
    variant: str = "primary",
) -> dict[str, Any]:
    p = int(precision.size)
    if p < MIN_COMMON_ROIS:
        raise ContractBlocked("STX3_REGISTRATION_BLOCKED", f"only {p} finite common ROIs")
    day_results: dict[str, Any] = {}
    for day in (0, 5):
        session = sessions[day]
        if strict_trial_vectors:
            _validate_endpoint_trial_vectors(arrays[day], session, variant=variant)
        maps = {
            (lr, fold): _fold_ratemap(arrays[day], session, lr, fold)
            for lr in (-1, 1)
            for fold in ("A", "B")
        }
        bilinear_scores: dict[int, float] = {}
        shifts = (0, *tuple(wrong_shifts))
        for shift in shifts:
            right_interior = RIGHT_REWARD_FULL - 1
            shifted_right = ((right_interior + shift) % 28) + 1
            values: list[float] = []
            for left_index, right_index in zip(
                LEFT_REWARD_FULL, shifted_right, strict=True
            ):
                delta_a = maps[(-1, "A")][left_index] - maps[(1, "A")][right_index]
                delta_b = maps[(-1, "B")][left_index] - maps[(1, "B")][right_index]
                if not np.all(np.isfinite(delta_a)) or not np.all(np.isfinite(delta_b)):
                    raise ContractBlocked(
                        "STX3_NUMERICAL_BLOCKED",
                        f"nonfinite frozen-ROI fold mean: {session.subject} day{day} "
                        f"shift{shift} bins{left_index}/{right_index}",
                    )
                value = float(np.sum(delta_a * precision * delta_b) / p)
                values.append(value)
            bilinear_scores[int(shift)] = float(np.mean(values))
        wrong_values = [bilinear_scores[int(shift)] for shift in wrong_shifts]
        geometry = float(np.median(wrong_values) - bilinear_scores[0])
        day_results[str(day)] = {
            "G": geometry,
            "G_role": "reward_alignment_contrast_of_crossvalidated_bilinear_scores",
            "true_bilinear_score": bilinear_scores[0],
            "wrong_shift_bilinear_median": float(np.median(wrong_values)),
            "bilinear_scores_by_shift": {
                str(key): value for key, value in sorted(bilinear_scores.items())
            },
        }
    return {
        "day": day_results,
        "delta_G": float(day_results["5"]["G"] - day_results["0"]["G"]),
    }


def heldout_behavior(session: SessionData, *, omission_only: bool = False) -> dict[str, Any]:
    by_ordinal = {int(item["ordinal"]): item for item in session.behavior}
    arm_values: dict[str, Any] = {}
    for lr in (-1, 1):
        records = [by_ordinal[ordinal] for ordinal in session.fold_ordinals[lr]["H"]]
        if omission_only:
            records = [record for record in records if record["omitted"]]
        if omission_only and len(records) < 2:
            arm_values[str(lr)] = {"available": False, "trial_count": len(records)}
            continue
        total_licks = float(sum(record["whole_licks"] for record in records))
        pre_licks = float(sum(record["pre_licks"] for record in records))
        concentration = 0.0 if total_licks == 0 else pre_licks / total_licks
        speeds = np.asarray([record["whole_speed"] for record in records], dtype=np.float64)
        if speeds.size == 0 or not np.all(np.isfinite(speeds)):
            raise ContractBlocked(
                "STX3_NUMERICAL_BLOCKED",
                f"nonfinite/empty H speed: {session.subject} day{session.day} LR{lr}",
            )
        arm_values[str(lr)] = {
            "available": True,
            "trial_count": len(records),
            "whole_licks": total_licks,
            "pre_reward_licks": pre_licks,
            "concentration": float(concentration),
            "mean_speed": float(np.mean(speeds)),
        }
    available = all(arm_values[str(lr)].get("available", False) for lr in (-1, 1))
    if not available:
        return {"available": False, "arms": arm_values}
    return {
        "available": True,
        "B": float(np.mean([arm_values["-1"]["concentration"], arm_values["1"]["concentration"]])),
        "speed": float(np.mean([arm_values["-1"]["mean_speed"], arm_values["1"]["mean_speed"]])),
        "arms": arm_values,
    }


def exact_group_label_test(
    values: np.ndarray, groups: np.ndarray, *, ctrl_size: int = 9
) -> dict[str, Any]:
    values = np.asarray(values, dtype=np.float64)
    groups = np.asarray(groups)
    if values.size != groups.size or not np.all(np.isfinite(values)):
        raise ContractBlocked("STX3_NUMERICAL_BLOCKED", "exact group test has invalid inputs")
    if np.sum(groups == "Ctrl") != ctrl_size or np.sum(groups == "Cre") != values.size - ctrl_size:
        raise ContractBlocked("STX3_NUMERICAL_BLOCKED", "exact group sizes do not match")
    observed = float(np.mean(values[groups == "Ctrl"]) - np.mean(values[groups == "Cre"]))
    extreme = 0
    total = 0
    indices = np.arange(values.size)
    for control_tuple in itertools.combinations(indices.tolist(), ctrl_size):
        control = np.zeros(values.size, dtype=bool)
        control[list(control_tuple)] = True
        statistic = float(np.mean(values[control]) - np.mean(values[~control]))
        extreme += int(statistic >= observed)
        total += 1
    expected_total = math.comb(values.size, ctrl_size)
    if total != expected_total:
        raise AssertionError(f"unexpected permutation total {total} != {expected_total}")
    return {
        "statistic_mean_ctrl_minus_cre": observed,
        "p_one_sided_exact": extreme / total,
        "extreme_count": extreme,
        "permutation_count": total,
        "p_value_role": "conditional_label_exchangeability_reference",
        "design_based_randomization_p": False,
        "direction_positive": bool(observed > 0),
    }


def _descriptive_group_summary(values: np.ndarray, groups: np.ndarray) -> dict[str, Any]:
    values = np.asarray(values, dtype=np.float64)
    groups = np.asarray(groups)
    if values.ndim != 1 or groups.shape != values.shape or not np.all(np.isfinite(values)):
        raise ContractBlocked("STX3_NUMERICAL_BLOCKED", "invalid descriptive group inputs")
    output: dict[str, Any] = {"n": int(values.size), "p_value": None}
    means: dict[str, float | None] = {}
    counts: dict[str, int] = {}
    for group in ("Ctrl", "Cre"):
        selected = values[groups == group]
        counts[group] = int(selected.size)
        means[group] = float(np.mean(selected)) if selected.size else None
    difference = (
        float(means["Ctrl"] - means["Cre"])
        if means["Ctrl"] is not None and means["Cre"] is not None
        else None
    )
    output.update(
        {
            "group_counts": counts,
            "group_means": means,
            "mean_ctrl_minus_cre": difference,
            "status": "DESCRIPTIVE_ONLY",
        }
    )
    return output


def _residualizer(controls: np.ndarray) -> np.ndarray:
    controls = np.asarray(controls, dtype=np.float64)
    return np.eye(controls.shape[0]) - controls @ np.linalg.pinv(controls)


def _within_group_permutation_indices(
    groups: np.ndarray,
    *,
    permutations: int = ASSOCIATION_PERMUTATIONS,
    seed: int = ASSOCIATION_SEED,
) -> np.ndarray:
    groups = np.asarray(groups)
    rng = np.random.Generator(np.random.PCG64(seed))
    group_indices = [np.flatnonzero(groups == group) for group in ("Ctrl", "Cre")]
    output = np.tile(np.arange(groups.size, dtype=np.int64), (permutations, 1))
    for row in range(permutations):
        for indices in group_indices:
            output[row, indices] = rng.permutation(indices)
    return output


def treatment_adjusted_rank_association(
    geometry: np.ndarray,
    behavior: np.ndarray,
    groups: np.ndarray,
    *,
    speed: np.ndarray | None = None,
    permutations: int = ASSOCIATION_PERMUTATIONS,
    seed: int = ASSOCIATION_SEED,
    permutation_indices: np.ndarray | None = None,
) -> dict[str, Any]:
    geometry = np.asarray(geometry, dtype=np.float64)
    behavior = np.asarray(behavior, dtype=np.float64)
    groups = np.asarray(groups)
    if geometry.size != 16 or behavior.size != 16:
        raise ContractBlocked("STX3_NUMERICAL_BLOCKED", "association requires 16 mice")
    if not np.all(np.isfinite(geometry)) or not np.all(np.isfinite(behavior)):
        raise ContractBlocked("STX3_NUMERICAL_BLOCKED", "association has nonfinite values")

    geometry_rank = rankdata(geometry, method="average")
    behavior_rank = rankdata(behavior, method="average")
    group_indicator = (groups == "Cre").astype(np.float64)
    controls = [np.ones(geometry.size), group_indicator]
    if speed is not None:
        speed = np.asarray(speed, dtype=np.float64)
        if speed.size != 16 or not np.all(np.isfinite(speed)):
            raise ContractBlocked("STX3_NUMERICAL_BLOCKED", "speed-adjusted association is invalid")
        controls.append(rankdata(speed, method="average"))
    projection = _residualizer(np.column_stack(controls))
    geometry_residual = projection @ geometry_rank
    behavior_residual = projection @ behavior_rank
    behavior_fitted = behavior_rank - behavior_residual
    denominator = float(np.linalg.norm(geometry_residual) * np.linalg.norm(behavior_residual))
    if denominator == 0 or not math.isfinite(denominator):
        raise ContractBlocked("STX3_NUMERICAL_BLOCKED", "rank association has zero residual norm")
    observed = float(np.dot(geometry_residual, behavior_residual) / denominator)

    if permutation_indices is None:
        permutation_indices = _within_group_permutation_indices(
            groups, permutations=permutations, seed=seed
        )
    permutation_indices = np.asarray(permutation_indices, dtype=np.int64)
    if permutation_indices.shape != (permutations, geometry.size):
        raise ContractBlocked(
            "STX3_NUMERICAL_BLOCKED", "association permutation-index shape mismatch"
        )
    for group in ("Ctrl", "Cre"):
        indices = np.flatnonzero(groups == group)
        if not np.all(np.sort(permutation_indices[:, indices], axis=1) == indices):
            raise ContractBlocked(
                "STX3_NUMERICAL_BLOCKED", "association permutation crosses groups"
            )
    extreme = 0
    for order in permutation_indices:
        pseudo_behavior = behavior_fitted + behavior_residual[order]
        residual = projection @ pseudo_behavior
        perm_denominator = float(np.linalg.norm(geometry_residual) * np.linalg.norm(residual))
        if not math.isfinite(perm_denominator) or perm_denominator <= 0:
            raise ContractBlocked(
                "STX3_NUMERICAL_BLOCKED",
                "Freedman-Lane pseudo-response has zero/nonfinite residual norm",
            )
        statistic = float(np.dot(geometry_residual, residual) / perm_denominator)
        if not math.isfinite(statistic):
            raise ContractBlocked(
                "STX3_NUMERICAL_BLOCKED", "Freedman-Lane statistic is nonfinite"
            )
        extreme += int(statistic >= observed)
    return {
        "statistic_partial_spearman": observed,
        "p_one_sided_monte_carlo": (1 + extreme) / (1 + permutations),
        "extreme_count": extreme,
        "permutation_count": permutations,
        "seed": seed,
        "speed_adjusted": speed is not None,
        "permutation_scheme": "freedman_lane_rank_residual_within_observed_group",
        "causal_randomization_p": False,
        "direction_positive": bool(observed > 0),
    }


def _variant_group_result(
    delta_geometry: np.ndarray,
    delta_behavior: np.ndarray,
    groups: np.ndarray,
    *,
    delta_speed: np.ndarray | None = None,
    permutation_indices: np.ndarray | None = None,
) -> dict[str, Any]:
    geometry_test = exact_group_label_test(delta_geometry, groups)
    behavior_test = exact_group_label_test(delta_behavior, groups)
    association = treatment_adjusted_rank_association(
        delta_geometry,
        delta_behavior,
        groups,
        speed=delta_speed,
        permutation_indices=permutation_indices,
    )
    p_joint = max(
        geometry_test["p_one_sided_exact"],
        behavior_test["p_one_sided_exact"],
        association["p_one_sided_monte_carlo"],
    )
    directions = (
        geometry_test["direction_positive"],
        behavior_test["direction_positive"],
        association["direction_positive"],
    )
    return {
        "geometry": geometry_test,
        "behavior": behavior_test,
        "association": association,
        "p_joint_max": float(p_joint),
        "all_directions_positive": bool(all(directions)),
        "conjunction_pass": bool(all(directions) and p_joint <= 0.05),
    }


def _trial_count_summary(session: SessionData) -> dict[str, Any]:
    by_block_arm: dict[str, int] = {}
    for block in range(6):
        for lr in (-1, 1):
            by_block_arm[f"block{block}_lr{lr}"] = sum(
                trial.block == block and trial.lr == lr for trial in session.trials
            )
    return {
        "total": len(session.trials),
        "by_block_arm": by_block_arm,
        "block5_folds": {
            str(lr): {fold: len(values) for fold, values in session.fold_ordinals[lr].items()}
            for lr in (-1, 1)
        },
    }


def validate_runtime_roi_inputs(roi_root: Path, roi_audit_path: Path) -> dict[str, Any]:
    """Re-audit the actual runtime pickles and compare every locked identity field."""

    if _checked_file_sha256(
        roi_audit_path, status="STX3_REGISTRATION_BLOCKED", label="ROI audit"
    ) != ROI_AUDIT_SHA256:
        raise ContractBlocked("STX3_REGISTRATION_BLOCKED", "ROI audit file hash mismatch")
    frozen = _read_json(
        roi_audit_path, status="STX3_REGISTRATION_BLOCKED", label="frozen ROI audit"
    )
    try:
        observed = audit_dense_maps(roi_root, minimum_common_rois=MIN_COMMON_ROIS)
    except Exception as exc:
        raise ContractBlocked(
            "STX3_REGISTRATION_BLOCKED", f"runtime ROI audit failed: {exc}"
        ) from exc
    for label, value in (("frozen", frozen), ("runtime", observed)):
        if value.get("status") != "STX3_ROI_ALIGNER_AUDIT_PASS":
            raise ContractBlocked("STX3_REGISTRATION_BLOCKED", f"{label} ROI audit is not PASS")
        if value.get("canonical_day0_day5_pairs_sha256") != ROI_PAIR_CANONICAL_SHA256:
            raise ContractBlocked(
                "STX3_REGISTRATION_BLOCKED", f"{label} ROI canonical pair hash mismatch"
            )

    comparison_fields = (
        "subject",
        "group",
        "pickle_sha256",
        "day0_ravel_ind",
        "day5_ravel_ind",
        "common_roi_count",
        "day0_roi_min",
        "day0_roi_max",
        "day5_roi_min",
        "day5_roi_max",
        "ordered_pairs_sha256",
    )
    frozen_by_subject = {
        item.get("subject"): {key: item.get(key) for key in comparison_fields}
        for item in frozen.get("subjects", [])
        if isinstance(item, dict)
    }
    observed_by_subject = {
        item.get("subject"): {key: item.get(key) for key in comparison_fields}
        for item in observed.get("subjects", [])
        if isinstance(item, dict)
    }
    if set(frozen_by_subject) != set(SUBJECTS) or observed_by_subject != frozen_by_subject:
        raise ContractBlocked(
            "STX3_REGISTRATION_BLOCKED",
            "runtime ROI pickle hashes, ravel maps, or ordered pairs differ from the frozen audit",
        )
    module_path = Path(roi_audit_module.__file__).resolve()
    return {
        "roi_root": roi_root.resolve().as_posix(),
        "frozen_roi_audit_sha256": _checked_file_sha256(
            roi_audit_path, status="STX3_REGISTRATION_BLOCKED", label="ROI audit"
        ),
        "roi_audit_module": module_path.as_posix(),
        "roi_audit_module_sha256": _checked_file_sha256(
            module_path, status="STX3_REGISTRATION_BLOCKED", label="ROI audit module"
        ),
        "canonical_day0_day5_pairs_sha256": observed[
            "canonical_day0_day5_pairs_sha256"
        ],
        "subject_count": observed["subject_count"],
        "subjects": observed["subjects"],
    }


def _load_locked_day_pair(
    roi_root: Path, subject: str
) -> tuple[np.ndarray, np.ndarray, int, int]:
    aligner_path = roi_root / subject / "roi_aligner_results.pkl"
    day0_ravel, day5_ravel = DENSE_DAY0_DAY5_RAVEL[subject]
    try:
        day0_indices, day5_indices = load_day_pair(
            aligner_path, day0_ravel, day5_ravel
        )
    except Exception as exc:
        raise ContractBlocked(
            "STX3_REGISTRATION_BLOCKED", f"cannot load locked ROI pair for {subject}: {exc}"
        ) from exc
    order = np.argsort(day0_indices)
    return day0_indices[order], day5_indices[order], day0_ravel, day5_ravel


def preflight_all_sessions(
    assets: dict[tuple[str, int], dict[str, Any]], roi_root: Path
) -> list[dict[str, Any]]:
    """Validate all 32 sessions structurally without computing a biological endpoint."""

    summaries: list[dict[str, Any]] = []
    for subject in SUBJECTS:
        day0_indices, day5_indices, day0_ravel, day5_ravel = _load_locked_day_pair(
            roi_root, subject
        )
        for day, roi_indices, ravel in (
            (0, day0_indices, day0_ravel),
            (5, day5_indices, day5_ravel),
        ):
            print(
                f"PREFLIGHT {len(summaries) + 1}/{len(SUBJECTS) * 2} {subject} day{day}",
                flush=True,
            )
            session = load_session(
                assets[(subject, day)]["local_path"],
                expected_subject=subject,
                expected_day=day,
                expected_ravel=ravel,
                expected_novel_arm=NOVEL_ARM_BY_SUBJECT[subject],
                roi_indices=roi_indices,
            )
            summaries.append(
                {
                    "subject": subject,
                    "day": day,
                    "group": GROUP_BY_SUBJECT[subject],
                    "source_sha256": assets[(subject, day)]["sha256"],
                    "mapped_common_roi_count": int(roi_indices.size),
                    "trial_counts": _trial_count_summary(session),
                    "binned_neural_shape": list(session.neural_bins.shape),
                    "full_block_offset": session.full_block_offset,
                    "cross_family_boundary_timing_ms": session.boundary_timing_ms,
                    "structural_validation": "PASS",
                }
            )
    expected_pairs = {(subject, day) for subject in SUBJECTS for day in (0, 5)}
    if len(summaries) != len(expected_pairs) or {
        (item["subject"], item["day"]) for item in summaries
    } != expected_pairs:
        raise ContractBlocked(
            "STX3_PREFLIGHT_BLOCKED",
            f"preflight did not cover exactly {len(expected_pairs)} sessions",
        )
    return summaries


def analyze_mouse(
    subject: str,
    assets: dict[tuple[str, int], dict[str, Any]],
    roi_root: Path,
) -> dict[str, Any]:
    day0_indices, day5_indices, day0_ravel, day5_ravel = _load_locked_day_pair(
        roi_root, subject
    )
    if day0_indices.size < MIN_COMMON_ROIS:
        raise ContractBlocked(
            "STX3_REGISTRATION_BLOCKED",
            f"{subject} has only {day0_indices.size} mapped day0/day5 ROIs",
        )

    sessions = {
        0: load_session(
            assets[(subject, 0)]["local_path"],
            expected_subject=subject,
            expected_day=0,
            expected_ravel=day0_ravel,
            expected_novel_arm=NOVEL_ARM_BY_SUBJECT[subject],
            roi_indices=day0_indices,
        ),
        5: load_session(
            assets[(subject, 5)]["local_path"],
            expected_subject=subject,
            expected_day=5,
            expected_ravel=day5_ravel,
            expected_novel_arm=NOVEL_ARM_BY_SUBJECT[subject],
            roi_indices=day5_indices,
        ),
    }

    references, category_codes, training_speed, training_lick = _training_references(sessions)
    raw_arrays = {day: sessions[day].neural_bins for day in (0, 5)}
    raw_training_all = _matrix_from_references(raw_arrays, references)
    analysis_cells = _require_complete_endpoint_population(sessions, subject=subject)
    common_training_rows = np.all(np.isfinite(raw_training_all), axis=1)
    if int(np.sum(common_training_rows)) < 3:
        raise ContractBlocked(
            "STX3_NUMERICAL_BLOCKED", f"{subject} has fewer than 3 common training rows"
        )
    references = [
        reference
        for reference, keep in zip(references, common_training_rows, strict=True)
        if keep
    ]
    category_codes = category_codes[common_training_rows]
    training_speed = training_speed[common_training_rows]
    training_lick = training_lick[common_training_rows]
    mapped_roi_count = int(day0_indices.size)

    raw_arrays = {day: sessions[day].neural_bins for day in (0, 5)}
    raw_training = _matrix_from_references(raw_arrays, references)
    motor_coefficients = _fit_motor_coefficients(
        raw_training, category_codes, training_speed, training_lick
    )
    variant_arrays = {
        "primary": raw_arrays,
        "S_rate": {day: _cell_axis_demean(raw_arrays[day]) for day in (0, 5)},
        "S_motor": {
            day: _motor_transform(sessions[day], motor_coefficients) for day in (0, 5)
        },
    }

    geometries: dict[str, Any] = {}
    precision_summaries: dict[str, Any] = {}
    for variant, arrays in variant_arrays.items():
        variant_training = _matrix_from_references(arrays, references)
        precision_result = _estimate_precision(variant_training, category_codes)
        precision = precision_result.pop("precision")
        precision_summaries[variant] = precision_result
        geometries[variant] = reward_alignment_bilinear_proxy(
            sessions,
            arrays,
            precision,
            strict_trial_vectors=variant != "primary",
            variant=variant,
        )

    primary_precision_result = _estimate_precision(
        _matrix_from_references(variant_arrays["primary"], references), category_codes
    )
    nonwrap_geometry = reward_alignment_bilinear_proxy(
        sessions,
        variant_arrays["primary"],
        primary_precision_result["precision"],
        wrong_shifts=NONWRAP_SHIFTS,
    )

    behavior = {str(day): heldout_behavior(sessions[day]) for day in (0, 5)}
    if not all(behavior[str(day)]["available"] for day in (0, 5)):
        raise ContractBlocked("STX3_NUMERICAL_BLOCKED", f"missing H behavior for {subject}")
    delta_behavior = float(behavior["5"]["B"] - behavior["0"]["B"])
    delta_speed = float(behavior["5"]["speed"] - behavior["0"]["speed"])
    omission = {str(day): heldout_behavior(sessions[day], omission_only=True) for day in (0, 5)}
    omission_delta = (
        float(omission["5"]["B"] - omission["0"]["B"])
        if omission["0"]["available"] and omission["5"]["available"]
        else None
    )

    return {
        "subject": subject,
        "group": GROUP_BY_SUBJECT[subject],
        "novel_arm": NOVEL_ARM_BY_SUBJECT[subject],
        "ravel_indices": {"day0": day0_ravel, "day5": day5_ravel},
        "mapped_common_roi_count": mapped_roi_count,
        "endpoint_complete_roi_count": int(np.sum(analysis_cells)),
        "analysis_common_roi_count": int(np.sum(analysis_cells)),
        "roi_population_rule": "all_aligner_mapped_rois_or_fail_closed",
        "analysis_common_day0_indices_sha256": hashlib.sha256(
            np.asarray(day0_indices[analysis_cells], dtype="<i8").tobytes()
        ).hexdigest(),
        "analysis_common_day5_indices_sha256": hashlib.sha256(
            np.asarray(day5_indices[analysis_cells], dtype="<i8").tobytes()
        ).hexdigest(),
        "trial_counts": {str(day): _trial_count_summary(sessions[day]) for day in (0, 5)},
        "training": {
            "row_count": len(references),
            "fixed_row_sha256": hashlib.sha256(
                json.dumps(references, separators=(",", ":")).encode("ascii")
            ).hexdigest(),
            "category_count": int(np.unique(category_codes).size),
            "speed_mean": motor_coefficients["speed_mean"],
            "speed_sd": motor_coefficients["speed_sd"],
            "lick_mean": motor_coefficients["lick_mean"],
            "lick_sd": motor_coefficients["lick_sd"],
            "motor_design_rank": motor_coefficients["design_rank"],
        },
        "precision": precision_summaries,
        "geometry": geometries,
        "nonwrap_primary_geometry": nonwrap_geometry,
        "behavior": behavior,
        "delta_B": delta_behavior,
        "delta_speed": delta_speed,
        "omission_sensitivity": {"day": omission, "delta_B": omission_delta},
    }


def _primary_status(primary: dict[str, Any]) -> str:
    if primary["conjunction_pass"]:
        return "STX3_PRIMARY_CONJUNCTION_SUPPORTED"
    if (
        primary["geometry"]["direction_positive"]
        and primary["geometry"]["p_one_sided_exact"] <= 0.05
    ):
        return "STX3_PRIMARY_GEOMETRY_COMPONENT_ONLY"
    return "STX3_PRIMARY_COMPONENT_CONJUNCTION_NOT_SUPPORTED"


def _sensitivity_direction_reversed(result: dict[str, Any]) -> bool:
    geometry = result["geometry"]
    return bool(
        geometry["statistic_mean_ctrl_minus_cre"] <= 0
        or not geometry["direction_positive"]
    )


def _final_status(results: dict[str, dict[str, Any]]) -> str:
    primary = results["primary"]
    rate = results["S_rate"]
    motor = results["S_motor"]
    if not primary["conjunction_pass"]:
        return _primary_status(primary).replace("STX3_PRIMARY_", "STX3_")
    if _sensitivity_direction_reversed(rate) or _sensitivity_direction_reversed(motor):
        return "STX3_GLOBAL_RATE_OR_MOTOR_CONFOUND_COMPATIBLE_FAIL"
    if rate["conjunction_pass"] and motor["conjunction_pass"]:
        return "STX3_REWARD_ALIGNMENT_BEHAVIOR_CONJUNCTION_CONFOUND_ROBUST_SUPPORTED"
    return "STX3_PRIMARY_ONLY_CONFOUND_SENSITIVE_NO_EVIDENCE_ELEVATION"


def analyze_all(
    assets: dict[tuple[str, int], dict[str, Any]], roi_root: Path
) -> dict[str, Any]:
    mouse_results: list[dict[str, Any]] = []
    for index, subject in enumerate(SUBJECTS, start=1):
        print(f"ANALYZE {index}/{len(SUBJECTS)} {subject}", flush=True)
        mouse_results.append(analyze_mouse(subject, assets, roi_root))

    groups = np.asarray([item["group"] for item in mouse_results])
    delta_behavior = np.asarray([item["delta_B"] for item in mouse_results], dtype=np.float64)
    delta_speed = np.asarray([item["delta_speed"] for item in mouse_results], dtype=np.float64)
    association_orders = _within_group_permutation_indices(groups)
    group_results: dict[str, dict[str, Any]] = {}
    for variant in ("primary", "S_rate", "S_motor"):
        delta_geometry = np.asarray(
            [item["geometry"][variant]["delta_G"] for item in mouse_results],
            dtype=np.float64,
        )
        group_results[variant] = _variant_group_result(
            delta_geometry,
            delta_behavior,
            groups,
            delta_speed=delta_speed if variant == "S_motor" else None,
            permutation_indices=association_orders,
        )

    nonwrap_delta = np.asarray(
        [item["nonwrap_primary_geometry"]["delta_G"] for item in mouse_results],
        dtype=np.float64,
    )
    nonwrap_summary = _descriptive_group_summary(nonwrap_delta, groups)

    subset_indices = np.asarray(
        [index for index, item in enumerate(mouse_results) if item["subject"] not in {"Ctrl_6", "Ctrl_7", "Ctrl_8", "Ctrl_9"}],
        dtype=np.int64,
    )
    subset_groups = groups[subset_indices]
    subset_geometry = np.asarray(
        [item["geometry"]["primary"]["delta_G"] for item in mouse_results],
        dtype=np.float64,
    )[subset_indices]
    wavelength_980_summary = _descriptive_group_summary(subset_geometry, subset_groups)

    omission_values = [item["omission_sensitivity"]["delta_B"] for item in mouse_results]
    omission_available_indices = np.asarray(
        [index for index, value in enumerate(omission_values) if value is not None],
        dtype=np.int64,
    )
    omission_summary = (
        _descriptive_group_summary(
            np.asarray([omission_values[index] for index in omission_available_indices]),
            groups[omission_available_indices],
        )
        if omission_available_indices.size
        else {
            "n": 0,
            "group_counts": {"Ctrl": 0, "Cre": 0},
            "group_means": {"Ctrl": None, "Cre": None},
            "mean_ctrl_minus_cre": None,
            "p_value": None,
            "status": "DESCRIPTIVE_ONLY",
        }
    )

    status = _final_status(group_results)
    return {
        "status": status,
        "primary_status": _primary_status(group_results["primary"]),
        "mouse_order": list(SUBJECTS),
        "mice": mouse_results,
        "association_permutation_indices_sha256": hashlib.sha256(
            np.asarray(association_orders, dtype="<i8").tobytes()
        ).hexdigest(),
        "group_tests": group_results,
        "fixed_sensitivities": {
            "status": "DESCRIPTIVE_ONLY_NO_CONFIRMATORY_P_VALUES",
            "nonwrapping_wrong_shift_primary_geometry": {
                "mouse_delta_G": nonwrap_delta.tolist(),
                "summary": nonwrap_summary,
            },
            "wavelength_980_only_primary_geometry": {
                "subjects": [mouse_results[index]["subject"] for index in subset_indices],
                "mouse_delta_G": subset_geometry.tolist(),
                "summary": wavelength_980_summary,
            },
            "omission_only_behavior": {
                "available_subjects": [
                    mouse_results[index]["subject"] for index in omission_available_indices
                ],
                "mouse_delta_B": [omission_values[index] for index in omission_available_indices],
                "summary": omission_summary,
            },
        },
        "claim_ceiling": (
            "BIO_EVIDENCE_L2_SAME_ANIMAL_TRIAD_WITH_"
            "NONRANDOMIZED_MECHANISM_ASSOCIATION_COMPONENT"
        ),
        "L3_confirmed": False,
        "integrated_chain_grade": "BIO_EVIDENCE_L0",
        "biological_mediation": "UNTESTED_NO_MEDIATOR_SPECIFIC_INTERVENTION_OR_RESCUE",
        "direct_W_STP_CONNECTIVITY_SPEED_DELAY_measurement": False,
    }


def validate_frozen_inputs(
    contract_path: Path,
    prior_addendum_path: Path,
    statistical_addendum_path: Path,
    addendum_path: Path,
    blocked_preflight_receipt_path: Path,
    roi_audit_path: Path,
    official_code_root: Path,
    twoputils_root: Path,
    mouse_metadata_path: Path,
    selection_path: Path,
) -> dict[str, Any]:
    contract_hash = _checked_file_sha256(
        contract_path, status="STX3_SOURCE_BLOCKED", label="base contract"
    )
    if contract_hash != BASE_CONTRACT_SHA256:
        raise ContractBlocked(
            "STX3_SOURCE_BLOCKED",
            f"base contract hash mismatch: {contract_hash} != {BASE_CONTRACT_SHA256}",
        )
    prior_addendum_hash = _checked_file_sha256(
        prior_addendum_path,
        status="STX3_SOURCE_BLOCKED",
        label="prior contract addendum",
    )
    if prior_addendum_hash != PRIOR_ADDENDUM_SHA256:
        raise ContractBlocked(
            "STX3_SOURCE_BLOCKED",
            f"prior addendum hash mismatch: "
            f"{prior_addendum_hash} != {PRIOR_ADDENDUM_SHA256}",
        )
    statistical_addendum_hash = _checked_file_sha256(
        statistical_addendum_path,
        status="STX3_SOURCE_BLOCKED",
        label="statistical contract addendum",
    )
    if statistical_addendum_hash != STATISTICAL_ADDENDUM_SHA256:
        raise ContractBlocked(
            "STX3_SOURCE_BLOCKED",
            f"statistical addendum hash mismatch: "
            f"{statistical_addendum_hash} != {STATISTICAL_ADDENDUM_SHA256}",
        )
    addendum_hash = _checked_file_sha256(
        addendum_path, status="STX3_SOURCE_BLOCKED", label="contract addendum"
    )
    if addendum_hash != ADDENDUM_SHA256:
        raise ContractBlocked(
            "STX3_SOURCE_BLOCKED",
            f"addendum hash mismatch: {addendum_hash} != {ADDENDUM_SHA256}",
        )
    blocked_preflight_hash = _checked_file_sha256(
        blocked_preflight_receipt_path,
        status="STX3_SOURCE_BLOCKED",
        label="blocked v1.2 preflight receipt",
    )
    if blocked_preflight_hash != BLOCKED_PREFLIGHT_RECEIPT_SHA256:
        raise ContractBlocked(
            "STX3_SOURCE_BLOCKED",
            f"blocked preflight receipt hash mismatch: "
            f"{blocked_preflight_hash} != {BLOCKED_PREFLIGHT_RECEIPT_SHA256}",
        )
    blocked_preflight = _read_json(
        blocked_preflight_receipt_path,
        status="STX3_SOURCE_BLOCKED",
        label="blocked v1.2 preflight receipt",
    )
    if (
        blocked_preflight.get("status") != "STX3_TRIAL_JOIN_BLOCKED"
        or blocked_preflight.get("biological_endpoint_evaluated") is not False
    ):
        raise ContractBlocked(
            "STX3_SOURCE_BLOCKED",
            "v1.2 blocked-preflight receipt does not prove a value-blind trial-join stop",
        )
    offset_map_hash = _full_block_offset_map_sha256()
    if offset_map_hash != FULL_BLOCK_OFFSET_MAP_SHA256:
        raise ContractBlocked(
            "STX3_SOURCE_BLOCKED",
            f"locked full-block offset map hash mismatch: "
            f"{offset_map_hash} != {FULL_BLOCK_OFFSET_MAP_SHA256}",
        )
    official_code_root = official_code_root.resolve()
    twoputils_root = twoputils_root.resolve()
    expected_mouse_metadata_path = official_code_root / "mouse_metadata.py"
    if mouse_metadata_path.resolve() != expected_mouse_metadata_path:
        raise ContractBlocked(
            "STX3_SOURCE_BLOCKED",
            f"mouse_metadata.py is not under the locked official-code root: "
            f"{mouse_metadata_path.resolve()} != {expected_mouse_metadata_path}",
        )
    code_sources = {
        "mouse_metadata": (
            expected_mouse_metadata_path,
            MOUSE_METADATA_SHA256,
        ),
        "official_session": (
            official_code_root / "session.py",
            OFFICIAL_SESSION_SHA256,
        ),
        "official_behavior": (
            official_code_root / "behavior.py",
            OFFICIAL_BEHAVIOR_SHA256,
        ),
        "official_utilities": (
            official_code_root / "utilities.py",
            OFFICIAL_UTILITIES_SHA256,
        ),
        "official_reward_overrep": (
            official_code_root / "reward_overrep.py",
            OFFICIAL_REWARD_OVERREP_SHA256,
        ),
        "twoputils_spatial_analyses": (
            twoputils_root / "spatial_analyses.py",
            TWOPUTILS_SPATIAL_ANALYSES_SHA256,
        ),
        "twoputils_sess": (
            twoputils_root / "sess.py",
            TWOPUTILS_SESS_SHA256,
        ),
    }
    code_source_hashes: dict[str, str] = {}
    for label, (source_path, expected_hash) in code_sources.items():
        observed_hash = _checked_file_sha256(
            source_path,
            status="STX3_SOURCE_BLOCKED",
            label=f"pinned code source {label}",
        )
        if observed_hash != expected_hash:
            raise ContractBlocked(
                "STX3_SOURCE_BLOCKED",
                f"{label} hash mismatch: {observed_hash} != {expected_hash}",
            )
        code_source_hashes[f"{label}_sha256"] = observed_hash
    selection_hash = _checked_file_sha256(
        selection_path, status="STX3_SOURCE_BLOCKED", label="selection receipt"
    )
    roi_audit_hash = _checked_file_sha256(
        roi_audit_path, status="STX3_REGISTRATION_BLOCKED", label="ROI audit"
    )
    roi_audit = _read_json(
        roi_audit_path, status="STX3_REGISTRATION_BLOCKED", label="ROI audit"
    )
    if roi_audit.get("status") != "STX3_ROI_ALIGNER_AUDIT_PASS":
        raise ContractBlocked("STX3_REGISTRATION_BLOCKED", "ROI audit is not PASS")
    if roi_audit.get("canonical_day0_day5_pairs_sha256") != ROI_PAIR_CANONICAL_SHA256:
        raise ContractBlocked("STX3_REGISTRATION_BLOCKED", "ROI pair canonical hash mismatch")
    if roi_audit_hash != ROI_AUDIT_SHA256:
        raise ContractBlocked("STX3_REGISTRATION_BLOCKED", "ROI audit file hash mismatch")
    audited_ravels = {
        item.get("subject"): (item.get("day0_ravel_ind"), item.get("day5_ravel_ind"))
        for item in roi_audit.get("subjects", [])
    }
    if audited_ravels != DENSE_DAY0_DAY5_RAVEL:
        raise ContractBlocked("STX3_REGISTRATION_BLOCKED", "ROI audit ravel mapping mismatch")
    if selection_hash != SELECTION_RECEIPT_SHA256:
        raise ContractBlocked("STX3_SOURCE_BLOCKED", "selection receipt file hash mismatch")
    return {
        "base_contract_sha256": contract_hash,
        "prior_addendum_sha256": prior_addendum_hash,
        "statistical_addendum_sha256": statistical_addendum_hash,
        "addendum_sha256": addendum_hash,
        "blocked_preflight_receipt_sha256": blocked_preflight_hash,
        "full_block_offset_map_sha256": offset_map_hash,
        **code_source_hashes,
        "resolved_official_code_root": official_code_root.as_posix(),
        "resolved_twoputils_root": twoputils_root.as_posix(),
        "selection_receipt_sha256": selection_hash,
        "roi_audit_sha256": roi_audit_hash,
    }


def _parse_execution_lock(path: Path) -> dict[str, str]:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except Exception as exc:
        raise ContractBlocked("STX3_SOURCE_BLOCKED", f"cannot read execution lock: {exc}") from exc
    rows: dict[str, str] = {}
    for line_number, line in enumerate(lines, start=1):
        if not line or line.startswith("#"):
            continue
        if line.count("\t") != 1:
            raise ContractBlocked(
                "STX3_SOURCE_BLOCKED", f"malformed execution lock line {line_number}"
            )
        key, value = line.split("\t", 1)
        if not key or key in rows:
            raise ContractBlocked(
                "STX3_SOURCE_BLOCKED", f"empty/duplicate execution lock key: {key!r}"
            )
        rows[key] = value
    return rows


def _validate_preflight_receipt(
    path: Path,
    *,
    preflight_script_path: Path,
    runner_hash: str,
    audit_module_hash: str,
    selection_hash: str,
    download_receipt_hash: str,
    data_root: Path,
    roi_root: Path,
    official_code_root: Path,
    twoputils_root: Path,
) -> dict[str, Any]:
    expected_script = Path(__file__).resolve().with_name(
        "preflight_stx3_reward_alignment_v1_1.py"
    )
    if preflight_script_path.resolve() != expected_script:
        raise ContractBlocked(
            "STX3_PREFLIGHT_BLOCKED",
            f"unexpected preflight script: {preflight_script_path.resolve()} != {expected_script}",
        )
    receipt = _read_json(path, status="STX3_PREFLIGHT_BLOCKED", label="preflight receipt")
    expected_pairs = {(subject, day) for subject in SUBJECTS for day in (0, 5)}
    summaries = receipt.get("session_summaries", [])
    if not isinstance(summaries, list):
        raise ContractBlocked("STX3_PREFLIGHT_BLOCKED", "preflight summaries are not a list")
    try:
        observed_pairs = {(str(item["subject"]), int(item["day"])) for item in summaries}
    except Exception as exc:
        raise ContractBlocked("STX3_PREFLIGHT_BLOCKED", "malformed preflight session summary") from exc
    required = {
        "status": PREFLIGHT_STATUS,
        "contract_id": CONTRACT_ID,
        "biological_endpoint_evaluated": False,
        "preflight_script": preflight_script_path.resolve().as_posix(),
        "preflight_script_sha256": _checked_file_sha256(
            preflight_script_path,
            status="STX3_PREFLIGHT_BLOCKED",
            label="preflight script",
        ),
        "runner_sha256": runner_hash,
        "roi_audit_module_sha256": audit_module_hash,
        "selection_receipt_sha256": selection_hash,
        "download_receipt_sha256": download_receipt_hash,
        "resolved_data_root": data_root.resolve().as_posix(),
        "resolved_roi_root": roi_root.resolve().as_posix(),
        "resolved_official_code_root": official_code_root.resolve().as_posix(),
        "resolved_twoputils_root": twoputils_root.resolve().as_posix(),
        "subject_count": 16,
        "session_count": 32,
    }
    for key, expected in required.items():
        if receipt.get(key) != expected:
            raise ContractBlocked(
                "STX3_PREFLIGHT_BLOCKED",
                f"preflight {key} mismatch: {receipt.get(key)!r} != {expected!r}",
            )
    frozen_inputs = receipt.get("frozen_inputs")
    required_frozen_inputs = {
        "base_contract_sha256": BASE_CONTRACT_SHA256,
        "prior_addendum_sha256": PRIOR_ADDENDUM_SHA256,
        "statistical_addendum_sha256": STATISTICAL_ADDENDUM_SHA256,
        "addendum_sha256": ADDENDUM_SHA256,
        "blocked_preflight_receipt_sha256": BLOCKED_PREFLIGHT_RECEIPT_SHA256,
        "full_block_offset_map_sha256": FULL_BLOCK_OFFSET_MAP_SHA256,
        "mouse_metadata_sha256": MOUSE_METADATA_SHA256,
        "official_session_sha256": OFFICIAL_SESSION_SHA256,
        "official_behavior_sha256": OFFICIAL_BEHAVIOR_SHA256,
        "official_utilities_sha256": OFFICIAL_UTILITIES_SHA256,
        "official_reward_overrep_sha256": OFFICIAL_REWARD_OVERREP_SHA256,
        "twoputils_spatial_analyses_sha256": TWOPUTILS_SPATIAL_ANALYSES_SHA256,
        "twoputils_sess_sha256": TWOPUTILS_SESS_SHA256,
        "selection_receipt_sha256": SELECTION_RECEIPT_SHA256,
        "roi_audit_sha256": ROI_AUDIT_SHA256,
    }
    if not isinstance(frozen_inputs, dict) or any(
        frozen_inputs.get(key) != value
        for key, value in required_frozen_inputs.items()
    ):
        raise ContractBlocked(
            "STX3_PREFLIGHT_BLOCKED", "preflight frozen-input hash chain mismatch"
        )
    if observed_pairs != expected_pairs or len(summaries) != 32:
        raise ContractBlocked("STX3_PREFLIGHT_BLOCKED", "preflight did not PASS all 32 sessions")
    if any(
        not isinstance(item, dict)
        or item.get("structural_validation") != "PASS"
        or not isinstance(item.get("mapped_common_roi_count"), int)
        or item["mapped_common_roi_count"] < MIN_COMMON_ROIS
        or item.get("full_block_offset")
        != LOCKED_FULL_BLOCK_OFFSETS.get((item.get("subject"), item.get("day")))
        or not isinstance(item.get("cross_family_boundary_timing_ms"), dict)
        or set(item["cross_family_boundary_timing_ms"])
        != {
            "start_min",
            "start_max",
            "start_max_abs",
            "end_min",
            "end_max",
            "end_max_abs",
        }
        or not all(
            isinstance(value, (int, float)) and math.isfinite(float(value))
            for value in item["cross_family_boundary_timing_ms"].values()
        )
        for item in summaries
    ):
        raise ContractBlocked(
            "STX3_PREFLIGHT_BLOCKED", "one or more preflight session summaries are not structural PASS"
        )
    source_integrity = receipt.get("source_integrity")
    if (
        not isinstance(source_integrity, dict)
        or source_integrity.get("asset_count") != 32
        or source_integrity.get("total_bytes") != 20_006_552_508
    ):
        raise ContractBlocked("STX3_PREFLIGHT_BLOCKED", "preflight source-integrity summary mismatch")
    environment = receipt.get("environment")
    expected_environment = {
        "python_executable": Path(sys.executable).resolve().as_posix(),
        "python_version": platform.python_version(),
        "numpy_version": np.__version__,
        "scipy_version": scipy.__version__,
        "h5py_version": h5py.__version__,
    }
    if not isinstance(environment, dict) or any(
        environment.get(key) != value for key, value in expected_environment.items()
    ):
        raise ContractBlocked("STX3_PREFLIGHT_BLOCKED", "preflight environment mismatch")
    runtime_roi = receipt.get("runtime_roi")
    if (
        not isinstance(runtime_roi, dict)
        or runtime_roi.get("canonical_day0_day5_pairs_sha256") != ROI_PAIR_CANONICAL_SHA256
        or runtime_roi.get("subject_count") != 16
    ):
        raise ContractBlocked("STX3_PREFLIGHT_BLOCKED", "preflight runtime ROI audit mismatch")
    return receipt


def _validate_test_receipt(path: Path, *, runner_hash: str) -> dict[str, Any]:
    receipt = _read_json(path, status="STX3_TEST_BLOCKED", label="focused-test receipt")
    test_path = Path(__file__).resolve().with_name(
        "test_stx3_reward_alignment_crossnobis_v1_1.py"
    )
    required = {
        "status": TEST_STATUS,
        "contract_id": CONTRACT_ID,
        "exit_code": 0,
        "collected": EXPECTED_FOCUSED_TEST_COUNT,
        "passed": EXPECTED_FOCUSED_TEST_COUNT,
        "failed": 0,
        "errors": 0,
        "skipped": 0,
        "deselected": 0,
        "runner_sha256": runner_hash,
        "test_file_sha256": _checked_file_sha256(
            test_path, status="STX3_TEST_BLOCKED", label="focused-test source"
        ),
    }
    for key, expected in required.items():
        if receipt.get(key) != expected:
            raise ContractBlocked(
                "STX3_TEST_BLOCKED",
                f"focused-test {key} mismatch: {receipt.get(key)!r} != {expected!r}",
            )
    return receipt


def _validate_execution_locks(
    contract_path: Path,
    prior_addendum_path: Path,
    statistical_addendum_path: Path,
    addendum_path: Path,
    blocked_preflight_receipt_path: Path,
    execution_lock_path: Path,
    roi_audit_path: Path,
    official_code_root: Path,
    twoputils_root: Path,
    mouse_metadata_path: Path,
    selection_path: Path,
    download_receipt_path: Path,
    data_root: Path,
    roi_root: Path,
    preflight_receipt_path: Path,
    preflight_script_path: Path,
    test_receipt_path: Path,
    output_path: Path,
    attempt_marker_path: Path,
    attempt_id: str,
) -> dict[str, Any]:
    frozen = validate_frozen_inputs(
        contract_path,
        prior_addendum_path,
        statistical_addendum_path,
        addendum_path,
        blocked_preflight_receipt_path,
        roi_audit_path,
        official_code_root,
        twoputils_root,
        mouse_metadata_path,
        selection_path,
    )
    runner_path = Path(__file__).resolve()
    audit_module_path = Path(roi_audit_module.__file__).resolve()
    runner_hash = _checked_file_sha256(
        runner_path, status="STX3_SOURCE_BLOCKED", label="endpoint runner"
    )
    audit_module_hash = _checked_file_sha256(
        audit_module_path, status="STX3_REGISTRATION_BLOCKED", label="ROI audit module"
    )
    download_receipt_hash = _checked_file_sha256(
        download_receipt_path, status="STX3_SOURCE_BLOCKED", label="download receipt"
    )
    preflight_hash = _checked_file_sha256(
        preflight_receipt_path, status="STX3_PREFLIGHT_BLOCKED", label="preflight receipt"
    )
    test_hash = _checked_file_sha256(
        test_receipt_path, status="STX3_TEST_BLOCKED", label="focused-test receipt"
    )
    required_lock = {
        "contract_id": CONTRACT_ID,
        "base_contract_sha256": BASE_CONTRACT_SHA256,
        "prior_addendum_sha256": PRIOR_ADDENDUM_SHA256,
        "statistical_addendum_sha256": STATISTICAL_ADDENDUM_SHA256,
        "addendum_sha256": ADDENDUM_SHA256,
        "blocked_preflight_receipt_sha256": BLOCKED_PREFLIGHT_RECEIPT_SHA256,
        "full_block_offset_map_sha256": FULL_BLOCK_OFFSET_MAP_SHA256,
        "authorization": "true",
        "execution_ready": "true",
        "attempt_id": attempt_id,
        "python_executable": Path(sys.executable).resolve().as_posix(),
        "python_version": platform.python_version(),
        "numpy_version": np.__version__,
        "scipy_version": scipy.__version__,
        "h5py_version": h5py.__version__,
        "runner_sha256": runner_hash,
        "roi_audit_module_sha256": audit_module_hash,
        "official_code_commit": CODE_COMMIT,
        "mouse_metadata_sha256": frozen["mouse_metadata_sha256"],
        "official_session_sha256": frozen["official_session_sha256"],
        "official_behavior_sha256": frozen["official_behavior_sha256"],
        "official_utilities_sha256": frozen["official_utilities_sha256"],
        "official_reward_overrep_sha256": frozen[
            "official_reward_overrep_sha256"
        ],
        "twoputils_spatial_analyses_sha256": frozen[
            "twoputils_spatial_analyses_sha256"
        ],
        "twoputils_sess_sha256": frozen["twoputils_sess_sha256"],
        "selection_receipt_sha256": frozen["selection_receipt_sha256"],
        "download_receipt_sha256": download_receipt_hash,
        "roi_audit_sha256": frozen["roi_audit_sha256"],
        "preflight_receipt_sha256": preflight_hash,
        "preflight_script_sha256": _checked_file_sha256(
            preflight_script_path,
            status="STX3_PREFLIGHT_BLOCKED",
            label="preflight script",
        ),
        "test_receipt_sha256": test_hash,
        "resolved_contract_path": contract_path.resolve().as_posix(),
        "resolved_prior_addendum_path": prior_addendum_path.resolve().as_posix(),
        "resolved_statistical_addendum_path": statistical_addendum_path.resolve().as_posix(),
        "resolved_addendum_path": addendum_path.resolve().as_posix(),
        "resolved_blocked_preflight_receipt_path": (
            blocked_preflight_receipt_path.resolve().as_posix()
        ),
        "resolved_selection_path": selection_path.resolve().as_posix(),
        "resolved_download_receipt_path": download_receipt_path.resolve().as_posix(),
        "resolved_data_root": data_root.resolve().as_posix(),
        "resolved_roi_root": roi_root.resolve().as_posix(),
        "resolved_roi_audit_path": roi_audit_path.resolve().as_posix(),
        "resolved_official_code_root": official_code_root.resolve().as_posix(),
        "resolved_twoputils_root": twoputils_root.resolve().as_posix(),
        "resolved_mouse_metadata_path": mouse_metadata_path.resolve().as_posix(),
        "resolved_preflight_receipt_path": preflight_receipt_path.resolve().as_posix(),
        "resolved_preflight_script_path": preflight_script_path.resolve().as_posix(),
        "resolved_test_receipt_path": test_receipt_path.resolve().as_posix(),
        "resolved_output_path": output_path.resolve().as_posix(),
        "resolved_attempt_marker_path": attempt_marker_path.resolve().as_posix(),
    }
    lock_rows = _parse_execution_lock(execution_lock_path)
    if set(lock_rows) != set(required_lock):
        raise ContractBlocked(
            "STX3_SOURCE_BLOCKED",
            f"execution lock key set mismatch; missing={sorted(set(required_lock)-set(lock_rows))}, "
            f"extra={sorted(set(lock_rows)-set(required_lock))}",
        )
    for key, expected in required_lock.items():
        if lock_rows[key] != str(expected):
            raise ContractBlocked(
                "STX3_SOURCE_BLOCKED",
                f"execution lock {key} mismatch: {lock_rows[key]!r} != {expected!r}",
            )
    _validate_preflight_receipt(
        preflight_receipt_path,
        preflight_script_path=preflight_script_path,
        runner_hash=runner_hash,
        audit_module_hash=audit_module_hash,
        selection_hash=frozen["selection_receipt_sha256"],
        download_receipt_hash=download_receipt_hash,
        data_root=data_root,
        roi_root=roi_root,
        official_code_root=official_code_root,
        twoputils_root=twoputils_root,
    )
    _validate_test_receipt(test_receipt_path, runner_hash=runner_hash)
    return {
        **frozen,
        "execution_lock_sha256": file_sha256(execution_lock_path),
        "download_receipt_sha256": download_receipt_hash,
        "preflight_receipt_sha256": preflight_hash,
        "test_receipt_sha256": test_hash,
        "runner_sha256": runner_hash,
        "roi_audit_module_sha256": audit_module_hash,
        "locked_environment": required_lock,
    }


def _create_attempt_marker(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    if hasattr(os, "O_BINARY"):
        flags |= os.O_BINARY
    try:
        descriptor = os.open(path, flags)
    except FileExistsError as exc:
        raise ContractBlocked(
            "STX3_ONE_SHOT_ALREADY_CONSUMED", f"attempt marker already exists: {path}"
        ) from exc
    with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())


def _open_output_exclusive(path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    if hasattr(os, "O_BINARY"):
        flags |= os.O_BINARY
    try:
        descriptor = os.open(path, flags)
    except FileExistsError as exc:
        raise ContractBlocked(
            "STX3_ONE_SHOT_ALREADY_CONSUMED", f"one-shot output already exists: {path}"
        ) from exc
    return os.fdopen(descriptor, "w", encoding="utf-8", newline="\n")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--contract", required=True, type=Path)
    parser.add_argument("--prior-contract-addendum", required=True, type=Path)
    parser.add_argument("--statistical-contract-addendum", required=True, type=Path)
    parser.add_argument("--contract-addendum", required=True, type=Path)
    parser.add_argument("--blocked-preflight-receipt", required=True, type=Path)
    parser.add_argument("--execution-lock", required=True, type=Path)
    parser.add_argument("--preflight-receipt", required=True, type=Path)
    parser.add_argument("--preflight-script", required=True, type=Path)
    parser.add_argument("--test-receipt", required=True, type=Path)
    parser.add_argument("--selection", required=True, type=Path)
    parser.add_argument("--download-receipt", required=True, type=Path)
    parser.add_argument("--data-root", required=True, type=Path)
    parser.add_argument("--roi-root", required=True, type=Path)
    parser.add_argument("--roi-audit", required=True, type=Path)
    parser.add_argument("--official-code-root", required=True, type=Path)
    parser.add_argument("--twoputils-root", required=True, type=Path)
    parser.add_argument("--mouse-metadata", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--attempt-marker", required=True, type=Path)
    parser.add_argument("--attempt-id", required=True)
    args = parser.parse_args()

    if args.output.exists() or args.attempt_marker.exists():
        print(
            f"REFUSE: one-shot output/marker already exists: "
            f"{args.output} / {args.attempt_marker}",
            file=sys.stderr,
        )
        return 2

    base_receipt: dict[str, Any] = {
        "contract_id": CONTRACT_ID,
        "runner": Path(__file__).resolve().as_posix(),
        "runner_sha256": file_sha256(Path(__file__)),
        "command_arguments": {key: str(value) for key, value in vars(args).items()},
        "attempt_id": args.attempt_id,
        "biological_endpoint_started": False,
        "biological_endpoint_evaluated": False,
        "environment": {
            "python_executable": sys.executable,
            "python_version": platform.python_version(),
            "numpy_version": np.__version__,
            "scipy_version": scipy.__version__,
            "h5py_version": h5py.__version__,
            "platform": platform.platform(),
        },
        "metric_definition": {
            "geometry_estimator_name": "A/B crossvalidated bilinear reward-alignment proxy",
            "unbiased_crossnobis_claim": False,
            "fisher_metric_claim": False,
            "physical_spacetime_metric_claim": False,
            "bin_edges": BIN_EDGES.tolist(),
            "trial_slice": "[start, stop)",
            "position_bin_interval": "(left_edge, right_edge]",
            "observation_unit": "completed_trial_x_position_bin_population_vector",
            "left_tfront": LEFT_TFRONT,
            "right_tfront": RIGHT_TFRONT,
            "left_reward_full_indices": LEFT_REWARD_FULL.tolist(),
            "right_reward_full_indices": RIGHT_REWARD_FULL.tolist(),
            "wrong_shifts": list(WRONG_SHIFTS),
            "floor_multiplier": FLOOR_MULTIPLIER,
            "trial_cycle": ["A", "B", "H"],
            "minimum_trials_per_fold": MIN_TRIALS_PER_FOLD,
            "behavior_reward_censor": "before_first_reward_or_manual_reward_positive_sample",
            "behavior_arm_estimand": "pooled_event_ratio_then_equal_arm_weight",
            "required_variant_status": {
                "S_rate": "CONFIRMATORY_REQUIRED",
                "S_motor": "CONFIRMATORY_REQUIRED",
            },
            "reporting_sensitivities_status": {
                "nonwrapping_shift": "DESCRIPTIVE_ONLY",
                "omission_only_behavior": "DESCRIPTIVE_ONLY",
                "wavelength_980nm_subset": "DESCRIPTIVE_ONLY",
            },
            "association_permutations": ASSOCIATION_PERMUTATIONS,
            "association_seed": ASSOCIATION_SEED,
        },
    }
    exit_code = 1
    output_handle = None
    try:
        base_receipt["locks"] = _validate_execution_locks(
            args.contract,
            args.prior_contract_addendum,
            args.statistical_contract_addendum,
            args.contract_addendum,
            args.blocked_preflight_receipt,
            args.execution_lock,
            args.roi_audit,
            args.official_code_root,
            args.twoputils_root,
            args.mouse_metadata,
            args.selection,
            args.download_receipt,
            args.data_root,
            args.roi_root,
            args.preflight_receipt,
            args.preflight_script,
            args.test_receipt,
            args.output,
            args.attempt_marker,
            args.attempt_id,
        )
        assets, integrity = validate_source_receipts(
            args.selection, args.download_receipt, args.data_root
        )
        base_receipt["runtime_roi"] = validate_runtime_roi_inputs(
            args.roi_root, args.roi_audit
        )
        base_receipt["source_integrity"] = {
            "selection_sha256": file_sha256(args.selection),
            "download_receipt_sha256": file_sha256(args.download_receipt),
            "asset_count": len(integrity),
            "total_bytes": sum(item["size"] for item in integrity),
            "assets": integrity,
        }
        _create_attempt_marker(
            args.attempt_marker,
            {
                "status": "STX3_ONE_SHOT_ATTEMPT_RESERVED",
                "contract_id": CONTRACT_ID,
                "attempt_id": args.attempt_id,
                "runner_sha256": base_receipt["runner_sha256"],
                "execution_lock_sha256": base_receipt["locks"]["execution_lock_sha256"],
                "resolved_output_path": args.output.resolve().as_posix(),
                "marker_created_before_biological_endpoint": True,
                "biological_endpoint_started": False,
            },
        )
        output_handle = _open_output_exclusive(args.output)
        base_receipt["biological_endpoint_started"] = True
        base_receipt["result"] = analyze_all(assets, args.roi_root)
        base_receipt["status"] = base_receipt["result"]["status"]
        base_receipt["biological_endpoint_evaluated"] = True
        exit_code = 0
    except ContractBlocked as exc:
        base_receipt["status"] = exc.status
        base_receipt["error"] = str(exc)
    except Exception as exc:
        base_receipt["status"] = "STX3_IMPLEMENTATION_ERROR_BLOCKED"
        base_receipt["error"] = f"{type(exc).__name__}: {exc}"
    if output_handle is not None:
        with output_handle:
            json.dump(base_receipt, output_handle, ensure_ascii=False, indent=2)
            output_handle.write("\n")
            output_handle.flush()
            os.fsync(output_handle.fileno())
    print(json.dumps(
        {
            "status": base_receipt["status"],
            "biological_endpoint_evaluated": base_receipt["biological_endpoint_evaluated"],
            "output": args.output.as_posix() if output_handle is not None else None,
            "error": base_receipt.get("error"),
        },
        ensure_ascii=False,
        indent=2,
    ))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
