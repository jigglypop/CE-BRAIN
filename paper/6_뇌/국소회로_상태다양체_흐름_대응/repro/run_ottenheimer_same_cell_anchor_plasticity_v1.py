from __future__ import annotations

import argparse
import csv
import hashlib
import itertools
import json
import math
import platform
import sys
import zipfile
import zlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

import numpy as np
import scipy
from scipy.io import loadmat, whosmat
from scipy.signal import lfilter


CONTRACT_ID = "ALT_BIO_D7_OTTENHEIMER_SAME_CELL_ANCHOR_PLASTICITY_v1+A1+A2"
EXPECTED_ARCHIVE_BYTES = 3_723_747_863
EXPECTED_ARCHIVE_MD5 = "6085f775f1ea3a85505c55aafaf242bb"
EXPECTED_ARCHIVE_SHA256 = (
    "47ffe1933713f53be720d85023f75c6f487faa8ee39a46ad0af63e3801bc4bd9"
)
EXPECTED_ZIP_ENTRIES = 225
EXPECTED_PYTHON_EXECUTABLE = Path(
    r"C:\Users\dongh\AppData\Local\Programs\Python\Python311\python.exe"
)
EXPECTED_PYTHON_VERSION = "3.11.9"
EXPECTED_NUMPY_VERSION = "2.4.6"
EXPECTED_SCIPY_VERSION = "1.17.1"
REPO_ROOT = Path(__file__).resolve().parents[4]
RUNNER_PATH = Path(__file__).resolve()
CONTRACT_BASE_PATH = REPO_ROOT / (
    "paper/검증_원장/"
    "CE_NPF_ALT_BIO_D7_OTTENHEIMER2023_동일세포앵커_학습표현_분석계약_v1.md"
)
CONTRACT_A1_PATH = REPO_ROOT / (
    "paper/검증_원장/"
    "CE_NPF_ALT_BIO_D7_OTTENHEIMER2023_분석계약_v1_사전스키마보정_A1.md"
)
CONTRACT_A2_PATH = REPO_ROOT / (
    "paper/검증_원장/"
    "CE_NPF_ALT_BIO_D7_OTTENHEIMER2023_분석계약_v1_등록보정_A2.md"
)
TEST_PATH = RUNNER_PATH.with_name(
    "test_ottenheimer_same_cell_anchor_plasticity_v1.py"
)
EXTERNAL_ROOT = REPO_ROOT / "data/external/ottenheimer_2023_figshare_21365598"
EXPECTED_ARCHIVE_PATH = EXTERNAL_ROOT / "Imaging.zip"
EXPECTED_AUTHOR_CODE_PATH = EXTERNAL_ROOT / "ottenheimer-et-al-2022-v2.0.zip"
EXPECTED_AUTHOR_CODE_BYTES = 78_852
EXPECTED_AUTHOR_CODE_SHA256 = (
    "594ec93c6d1665dc6e00653e4e6afd74188fd5c96d31efda0dd5148711e35221"
)
EXPECTED_PREFLIGHT_RECEIPT_PATH = RUNNER_PATH.with_name(
    "ottenheimer_same_cell_anchor_plasticity_v1A2_preflight_final.json"
)
EXPECTED_SOURCE_LOCK_PATH = RUNNER_PATH.with_name(
    "ottenheimer_same_cell_anchor_plasticity_v1_execution_source_lock.tsv"
)

MICE = ("PL01", "PL02", "PL03", "PL08", "PL10", "PL11", "PL15", "PL16")
SESSIONS = ("o1d1", "o1d2", "o1d3")
SESSION_LABELS = {"o1d1": "A1", "o1d2": "A2", "o1d3": "A3"}
TRACKED_COUNTS = {
    "PL01": 55,
    "PL02": 55,
    "PL03": 33,
    "PL08": 20,
    "PL10": 40,
    "PL11": 64,
    "PL15": 39,
    "PL16": 65,
}
EXPECTED_TRACKED_TOTAL = 371
EXPECTED_PRIMARY_RETAINED = {
    "PL01": 54,
    "PL02": 52,
    "PL03": 33,
    "PL08": 17,
    "PL10": 35,
    "PL11": 62,
    "PL15": 38,
    "PL16": 63,
}
EXPECTED_PRIMARY_RETAINED_TOTAL = 354
EXPECTED_NO_DISTANCE_RETAINED = {
    "PL01": 55,
    "PL02": 53,
    "PL03": 33,
    "PL08": 19,
    "PL10": 38,
    "PL11": 64,
    "PL15": 39,
    "PL16": 65,
}
EXPECTED_AUTHOR_GREEDY_TOTAL = 370
KNOWN_OOB_TRIPLET = ("PL08", 9)

FRAME_RATE = 15.0
FRAME_RATE_RELATIVE_TOLERANCE = 0.05
SMOOTH_HISTORY = 15
SMOOTH_SIGMA_SECONDS = 0.3
PRIMARY_BINS = 15
SENSITIVITY_BINS = 25
BIN_SECONDS = 0.1
PRIMARY_PHASE_TRIALS = 60
PRIMARY_MIN_FOLD_TRIALS = 6
THIRDS_MIN_FOLD_TRIALS = 5
MAX_REGISTRATION_DISTANCE = 5.0
MIN_REGISTRATION_MARGIN = 2.0
MIN_REGISTRATION_FRACTION = 0.8
MIN_REGISTERED_CELLS = 15
ALPHA = 0.05

LOCK_ROLES = {
    "analysis_contract_base",
    "analysis_contract_amendment_a1",
    "analysis_contract_amendment_a2",
    "analysis_runner",
    "regression_tests",
    "provider_archive",
    "author_code_archive",
    "preflight_receipt",
    "python_runtime",
    "numpy_runtime",
    "scipy_runtime",
}


class GateError(RuntimeError):
    status = "D7_BLOCKED"


class SourceError(GateError):
    status = "D7_SOURCE_BLOCKED"


class SchemaError(GateError):
    status = "D7_SCHEMA_BLOCKED"


class RegistrationError(GateError):
    status = "D7_REGISTRATION_SCHEMA_BLOCKED"


class NumericalError(GateError):
    status = "D7_NUMERICAL_BLOCKED"


class ExecutionLockError(GateError):
    status = "D7_EXECUTION_LOCK_BLOCKED"


class SensitivityUnavailableError(RuntimeError):
    pass


@dataclass(frozen=True)
class SessionPaths:
    mouse: str
    session: str
    fall: Path
    events: Path
    mask: Path
    fall_member: str
    events_member: str
    mask_member: str


@dataclass(frozen=True)
class EventData:
    frame_times: np.ndarray
    segment_ids: np.ndarray
    cue: np.ndarray
    cue_labels: np.ndarray
    lick: np.ndarray


@dataclass(frozen=True)
class SessionRegistration:
    mapped_raw: np.ndarray
    mapped_xy: np.ndarray
    valid: np.ndarray
    summary: dict[str, Any]


@dataclass(frozen=True)
class RegistrationVariant:
    retained_k: np.ndarray
    raw_by_session: dict[str, np.ndarray]
    xy_by_session: dict[str, np.ndarray]
    summary: dict[str, Any]


@dataclass(frozen=True)
class MouseRegistration:
    corrected: RegistrationVariant
    author_typo: RegistrationVariant
    strict_5px_2px: RegistrationVariant
    no_distance_margin: RegistrationVariant
    author_greedy: RegistrationVariant


def hash_file(path: Path, algorithms: Iterable[str] = ("sha256",)) -> dict[str, str]:
    digests = {name: hashlib.new(name) for name in algorithms}
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            for digest in digests.values():
                digest.update(block)
    return {name: digest.hexdigest() for name, digest in digests.items()}


def normalized_path(path: Path) -> str:
    return str(path.resolve()).replace("\\", "/").casefold()


def resolve_lock_artifact(path_text: str) -> Path:
    candidate = Path(path_text)
    if not candidate.is_absolute():
        candidate = REPO_ROOT / candidate
    return candidate.resolve()


def canonical_lock_paths() -> dict[str, Path]:
    return {
        "analysis_contract_base": CONTRACT_BASE_PATH,
        "analysis_contract_amendment_a1": CONTRACT_A1_PATH,
        "analysis_contract_amendment_a2": CONTRACT_A2_PATH,
        "analysis_runner": RUNNER_PATH,
        "regression_tests": TEST_PATH,
        "provider_archive": EXPECTED_ARCHIVE_PATH,
        "author_code_archive": EXPECTED_AUTHOR_CODE_PATH,
        "preflight_receipt": EXPECTED_PREFLIGHT_RECEIPT_PATH,
        "python_runtime": Path(sys.executable).resolve(),
        "numpy_runtime": Path(np.__file__).resolve(),
        "scipy_runtime": Path(scipy.__file__).resolve(),
    }


def validate_lock_role_paths(
    by_role: dict[str, dict[str, str]],
) -> dict[str, Path]:
    if set(by_role) != LOCK_ROLES:
        raise ExecutionLockError(
            f"source-lock roles differ: missing={sorted(LOCK_ROLES-set(by_role))}, "
            f"extra={sorted(set(by_role)-LOCK_ROLES)}"
        )
    expected = canonical_lock_paths()
    resolved: dict[str, Path] = {}
    for role, expected_path in expected.items():
        artifact = resolve_lock_artifact(by_role[role]["path"])
        if normalized_path(artifact) != normalized_path(expected_path):
            raise ExecutionLockError(
                f"{role}: path {artifact} != canonical {expected_path.resolve()}"
            )
        resolved[role] = artifact
    return resolved


def to_builtin(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): to_builtin(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [to_builtin(item) for item in value]
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, Path):
        return str(value.resolve())
    return value


def write_json_exclusive(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8", newline="\n") as handle:
        json.dump(to_builtin(payload), handle, ensure_ascii=False, indent=2, sort_keys=True)
        handle.write("\n")


def verify_runtime() -> dict[str, Any]:
    executable = Path(sys.executable).resolve()
    expected = EXPECTED_PYTHON_EXECUTABLE.resolve()
    observed_version = platform.python_version()
    errors = []
    if normalized_path(executable) != normalized_path(expected):
        errors.append(f"python executable {executable} != {expected}")
    if observed_version != EXPECTED_PYTHON_VERSION:
        errors.append(f"Python {observed_version} != {EXPECTED_PYTHON_VERSION}")
    if np.__version__ != EXPECTED_NUMPY_VERSION:
        errors.append(f"NumPy {np.__version__} != {EXPECTED_NUMPY_VERSION}")
    if scipy.__version__ != EXPECTED_SCIPY_VERSION:
        errors.append(f"SciPy {scipy.__version__} != {EXPECTED_SCIPY_VERSION}")
    if errors:
        raise ExecutionLockError("; ".join(errors))
    return {
        "python_executable": str(executable),
        "python_version": observed_version,
        "numpy_version": np.__version__,
        "scipy_version": scipy.__version__,
    }


def load_execution_lock(path: Path) -> dict[str, dict[str, str]]:
    if not path.is_file():
        raise ExecutionLockError(f"source lock not found: {path}")
    with path.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle, delimiter="\t"))
    required_columns = {"artifact_role", "path", "bytes", "sha256", "version"}
    if not rows or not required_columns <= set(rows[0]):
        raise ExecutionLockError("source lock columns are missing")
    by_role: dict[str, dict[str, str]] = {}
    for row in rows:
        role = row["artifact_role"]
        if role in by_role:
            raise ExecutionLockError(f"duplicate source-lock role: {role}")
        by_role[role] = row
    resolved = validate_lock_role_paths(by_role)
    for role, row in by_role.items():
        artifact = resolved[role]
        if not artifact.is_file():
            raise ExecutionLockError(f"{role}: artifact missing: {artifact}")
        try:
            expected_bytes = int(row["bytes"])
        except ValueError as exc:
            raise ExecutionLockError(f"{role}: invalid byte count") from exc
        if artifact.stat().st_size != expected_bytes:
            raise ExecutionLockError(
                f"{role}: bytes {artifact.stat().st_size} != {expected_bytes}"
            )
        digest = hash_file(artifact)["sha256"]
        if digest != row["sha256"].casefold():
            raise ExecutionLockError(f"{role}: SHA-256 mismatch")
    provider_row = by_role["provider_archive"]
    if (
        int(provider_row["bytes"]) != EXPECTED_ARCHIVE_BYTES
        or provider_row["sha256"].casefold() != EXPECTED_ARCHIVE_SHA256
    ):
        raise ExecutionLockError("provider_archive metadata differs from official lock")
    author_row = by_role["author_code_archive"]
    if (
        int(author_row["bytes"]) != EXPECTED_AUTHOR_CODE_BYTES
        or author_row["sha256"].casefold() != EXPECTED_AUTHOR_CODE_SHA256
    ):
        raise ExecutionLockError("author_code_archive metadata differs from official lock")
    try:
        with resolved["preflight_receipt"].open("r", encoding="utf-8") as handle:
            preflight_receipt = json.load(handle)
    except (OSError, json.JSONDecodeError) as exc:
        raise ExecutionLockError(f"cannot read preflight receipt: {exc}") from exc
    if (
        preflight_receipt.get("contract_id") != CONTRACT_ID
        or preflight_receipt.get("mode") != "preflight"
        or preflight_receipt.get("status")
        != "D7_PREFLIGHT_PASS / ENDPOINT_NOT_RUN"
    ):
        raise ExecutionLockError("preflight receipt identity/status gate failed")
    return by_role


def session_paths(extracted_root: Path, mouse: str, session: str) -> SessionPaths:
    relative = Path(mouse) / session
    events_name = f"{mouse.lower()}{session}events.mat"
    mask_name = f"{mouse}{session}ROImasks.npy"
    return SessionPaths(
        mouse=mouse,
        session=session,
        fall=extracted_root / relative / "Fall.mat",
        events=extracted_root / relative / events_name,
        mask=extracted_root / "ROIs" / "Masks" / mask_name,
        fall_member=f"Imaging/{mouse}/{session}/Fall.mat",
        events_member=f"Imaging/{mouse}/{session}/{events_name}",
        mask_member=f"Imaging/ROIs/Masks/{mask_name}",
    )


def file_crc32(path: Path) -> int:
    crc = 0
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            crc = zlib.crc32(block, crc)
    return crc & 0xFFFFFFFF


def verify_source(archive_path: Path, extracted_root: Path) -> dict[str, Any]:
    if not archive_path.is_file():
        raise SourceError(f"archive not found: {archive_path}")
    size = archive_path.stat().st_size
    if size != EXPECTED_ARCHIVE_BYTES:
        raise SourceError(f"archive bytes {size} != {EXPECTED_ARCHIVE_BYTES}")
    hashes = hash_file(archive_path, ("md5", "sha256"))
    if hashes["md5"] != EXPECTED_ARCHIVE_MD5:
        raise SourceError(f"archive MD5 {hashes['md5']} != {EXPECTED_ARCHIVE_MD5}")
    if hashes["sha256"] != EXPECTED_ARCHIVE_SHA256:
        raise SourceError(
            f"archive SHA-256 {hashes['sha256']} != {EXPECTED_ARCHIVE_SHA256}"
        )

    try:
        archive = zipfile.ZipFile(archive_path)
    except zipfile.BadZipFile as exc:
        raise SourceError(f"invalid ZIP: {exc}") from exc
    with archive:
        infos = archive.infolist()
        names = [info.filename for info in infos]
        if len(infos) != EXPECTED_ZIP_ENTRIES:
            raise SourceError(f"ZIP entries {len(infos)} != {EXPECTED_ZIP_ENTRIES}")
        if len(names) != len(set(names)):
            raise SourceError("ZIP has duplicate member names")
        if {name.split("/")[0] for name in names if name} != {"Imaging"}:
            raise SourceError("ZIP top-level path differs from Imaging/")
        bad = archive.testzip()
        if bad is not None:
            raise SourceError(f"ZIP CRC failed at {bad}")
        by_name = {info.filename: info for info in infos}
        required: list[tuple[str, Path]] = []
        for mouse in MICE:
            for session in SESSIONS:
                paths = session_paths(extracted_root, mouse, session)
                required.extend(
                    [
                        (paths.fall_member, paths.fall),
                        (paths.events_member, paths.events),
                        (paths.mask_member, paths.mask),
                    ]
                )
        if len({member for member, _ in required}) != 72:
            raise SourceError("required member manifest is not exactly 72 unique files")
        for member, local_path in required:
            if member not in by_name:
                raise SourceError(f"required ZIP member missing: {member}")
            if not local_path.is_file():
                raise SourceError(f"extracted file missing: {local_path}")
            info = by_name[member]
            if local_path.stat().st_size != info.file_size:
                raise SourceError(f"extracted size differs: {local_path}")
            if file_crc32(local_path) != info.CRC:
                raise SourceError(f"extracted CRC differs: {local_path}")

        return {
            "archive_path": str(archive_path.resolve()),
            "archive_bytes": size,
            "archive_md5": hashes["md5"],
            "archive_sha256": hashes["sha256"],
            "zip_entries": len(infos),
            "zip_crc_bad_member": bad,
            "verified_extracted_members": len(required),
            "verified_extracted_bytes": int(
                sum(by_name[member].file_size for member, _ in required)
            ),
        }


def numeric_vector(value: Any, label: str, *, allow_empty: bool = False) -> np.ndarray:
    array = np.asarray(value)
    if array.ndim == 0:
        array = array.reshape(1)
    elif array.ndim == 2 and 1 in array.shape:
        array = array.reshape(-1)
    if array.ndim != 1 or (array.size == 0 and not allow_empty):
        raise SchemaError(f"{label} must be a vector, got {array.shape}")
    if not np.issubdtype(array.dtype, np.number):
        raise SchemaError(f"{label} must be numeric")
    output = np.asarray(array, dtype=np.float64)
    if not np.all(np.isfinite(output)):
        raise SchemaError(f"{label} contains non-finite values")
    return output


def mat_header(path: Path) -> dict[str, tuple[tuple[int, ...], str]]:
    try:
        return {name: (tuple(shape), kind) for name, shape, kind in whosmat(path)}
    except Exception as exc:
        raise SchemaError(f"cannot read MAT header {path}: {exc}") from exc


def validate_event_data(
    paths: SessionPaths, neural_shape: tuple[int, int]
) -> tuple[EventData, dict[str, Any]]:
    label = f"{paths.mouse}/{paths.session}"
    try:
        raw = loadmat(
            paths.events,
            variable_names=["frameTimes", "cue", "cue1", "cue2", "cue3", "lick"],
            squeeze_me=True,
        )
    except Exception as exc:
        raise SchemaError(f"{label}: cannot load events: {exc}") from exc
    required = {"frameTimes", "cue", "cue1", "cue2", "cue3", "lick"}
    missing = sorted(required - set(raw))
    if missing:
        raise SchemaError(f"{label}: missing event variables {missing}")
    frame_times = numeric_vector(raw["frameTimes"], f"{label}/frameTimes")
    cue = numeric_vector(raw["cue"], f"{label}/cue")
    cue_sets = [numeric_vector(raw[f"cue{i}"], f"{label}/cue{i}") for i in (1, 2, 3)]
    lick = numeric_vector(raw["lick"], f"{label}/lick", allow_empty=True)
    if not np.all(np.diff(frame_times) > 0):
        raise SchemaError(f"{label}: frameTimes is not strictly increasing")
    if not np.all(np.diff(cue) > 0):
        raise SchemaError(f"{label}: cue is not strictly increasing")
    if any(not np.all(np.diff(values) > 0) for values in cue_sets):
        raise SchemaError(f"{label}: a cue subtype is not strictly increasing")
    if lick.size > 1 and not np.all(np.diff(lick) > 0):
        raise SchemaError(f"{label}: lick is not strictly increasing")

    n_roi, neural_t = neural_shape
    extra = neural_t - frame_times.size
    if extra not in (1, 2):
        raise SchemaError(
            f"{label}: neural T - frameTimes = {extra}, expected 1 or 2"
        )
    median_dt = float(np.median(np.diff(frame_times)))
    if abs(median_dt - 1.0 / FRAME_RATE) > FRAME_RATE_RELATIVE_TOLERANCE / FRAME_RATE:
        raise SchemaError(f"{label}: median frame interval {median_dt} is outside 15 Hz gate")
    frame_differences = np.diff(frame_times)
    break_indices = np.flatnonzero(
        (frame_differences < 0.5 * median_dt)
        | (frame_differences > 1.5 * median_dt)
    )
    segment_ids = np.zeros(frame_times.size, dtype=np.int64)
    for break_index in break_indices:
        segment_ids[break_index + 1 :] += 1

    concatenated = np.sort(np.concatenate(cue_sets))
    if concatenated.size != cue.size or not np.array_equal(concatenated, cue):
        raise SchemaError(f"{label}: cue1/cue2/cue3 are not the exact cue partition")
    cue_labels = np.zeros(cue.size, dtype=np.int8)
    for cue_label, values in enumerate(cue_sets, start=1):
        indices = np.searchsorted(cue, values)
        if np.any(indices >= cue.size) or not np.array_equal(cue[indices], values):
            raise SchemaError(f"{label}: exact cue subtype join failed")
        if np.any(cue_labels[indices] != 0):
            raise SchemaError(f"{label}: cue subtype overlap")
        cue_labels[indices] = cue_label
    if np.any(cue_labels == 0):
        raise SchemaError(f"{label}: unlabeled cue trials")
    if cue.size < 2 * PRIMARY_PHASE_TRIALS:
        raise SchemaError(f"{label}: fewer than 120 trials")

    primary_phase_indices = (
        np.arange(PRIMARY_PHASE_TRIALS),
        np.arange(cue.size - PRIMARY_PHASE_TRIALS, cue.size),
    )
    primary_counts: dict[str, list[int]] = {}
    for phase_name, phase_indices in zip(("early", "late"), primary_phase_indices):
        counts = []
        for cue_label in (1, 2, 3):
            selected = phase_indices[cue_labels[phase_indices] == cue_label]
            fold_counts = [int(selected[fold::2].size) for fold in (0, 1)]
            if min(fold_counts) < PRIMARY_MIN_FOLD_TRIALS:
                raise SchemaError(
                    f"{label}/{phase_name}/cue{cue_label}: fold counts {fold_counts}"
                )
            counts.append(int(selected.size))
        primary_counts[phase_name] = counts

    if cue[0] < frame_times[0] or cue[-1] + SENSITIVITY_BINS * BIN_SECONDS > frame_times[-1]:
        raise SchemaError(f"{label}: cue response window falls outside frameTimes")
    if cue[0] - 2.5 < frame_times[0] or cue[-1] + 2.5 > frame_times[-1]:
        raise SchemaError(f"{label}: full behavior window falls outside frameTimes")
    if lick.size and (lick[0] < frame_times[0] or lick[-1] > frame_times[-1]):
        raise SchemaError(f"{label}: lick timestamp outside frameTimes")
    for onset in cue:
        baseline_start = int(np.searchsorted(frame_times, onset - 1.0, side="left"))
        baseline_stop = int(np.searchsorted(frame_times, onset, side="left"))
        if baseline_stop <= baseline_start:
            raise SchemaError(f"{label}: empty cue baseline bin")
        for bin_index in range(SENSITIVITY_BINS):
            start = int(
                np.searchsorted(
                    frame_times, onset + bin_index * BIN_SECONDS, side="left"
                )
            )
            stop = int(
                np.searchsorted(
                    frame_times, onset + (bin_index + 1) * BIN_SECONDS, side="left"
                )
            )
            if stop <= start:
                raise SchemaError(f"{label}: empty response bin {bin_index}")

        response_stop = int(
            np.searchsorted(
                frame_times,
                onset + SENSITIVITY_BINS * BIN_SECONDS,
                side="left",
            )
        )
        history_start = max(0, baseline_start - SMOOTH_HISTORY)
        if response_stop <= history_start:
            raise SchemaError(f"{label}: invalid extended endpoint window")
        if segment_ids[history_start] != segment_ids[response_stop - 1]:
            raise SchemaError(f"{label}: endpoint smoothing window crosses a time gap")

    return EventData(frame_times, segment_ids, cue, cue_labels, lick), {
        "n_roi": int(n_roi),
        "neural_frames": int(neural_t),
        "event_frames": int(frame_times.size),
        "trailing_neural_frames": int(extra),
        "median_frame_interval_seconds": median_dt,
        "segment_break_indices_zero_based": [int(value) for value in break_indices],
        "segment_break_seconds": [
            float(frame_differences[value]) for value in break_indices
        ],
        "trial_count": int(cue.size),
        "cue_counts": [int(np.sum(cue_labels == label_)) for label_ in (1, 2, 3)],
        "primary_phase_cue_counts": primary_counts,
        "lick_count": int(lick.size),
    }


def roi_field(stat_item: Any, field: str, label: str) -> np.ndarray:
    if not hasattr(stat_item, field):
        raise SchemaError(f"{label}: stat is missing {field}")
    return np.asarray(getattr(stat_item, field)).reshape(-1)


def process_roi_candidates(
    iscell: np.ndarray,
    stat: np.ndarray,
    fluorescence: np.ndarray,
    *,
    corrected_edge: bool,
    label: str,
) -> tuple[np.ndarray, dict[str, Any]]:
    if iscell.ndim != 2 or iscell.shape[1] < 1:
        raise SchemaError(f"{label}: iscell shape {iscell.shape}")
    if fluorescence.ndim != 2 or fluorescence.shape[0] != iscell.shape[0]:
        raise SchemaError(f"{label}: F/iscell row mismatch")
    if stat.size != iscell.shape[0]:
        raise SchemaError(f"{label}: stat/iscell row mismatch")
    initial = np.flatnonzero(iscell[:, 0] != 0)
    if initial.size < 2:
        raise RegistrationError(f"{label}: fewer than two initial iscell ROIs")

    pixels: list[np.ndarray] = []
    x_pixels: list[np.ndarray] = []
    y_pixels: list[np.ndarray] = []
    global_counts = np.zeros(512 * 512, dtype=np.int32)
    for raw_index in initial:
        item_label = f"{label}/stat[{raw_index}]"
        x = roi_field(stat[raw_index], "xpix", item_label).astype(np.int64)
        y = roi_field(stat[raw_index], "ypix", item_label).astype(np.int64)
        if x.size == 0 or x.size != y.size:
            raise SchemaError(f"{item_label}: xpix/ypix shape mismatch")
        if np.any((x < 0) | (x > 511) | (y < 0) | (y > 511)):
            raise SchemaError(f"{item_label}: pixel outside 512x512 FOV")
        encoded = y + 512 * x
        if np.unique(encoded).size != encoded.size:
            raise SchemaError(f"{item_label}: duplicate pixels within ROI")
        pixels.append(encoded)
        x_pixels.append(x)
        y_pixels.append(y)
        global_counts[encoded] += 1

    overlap = np.array(
        [float(np.mean(global_counts[encoded] > 1)) for encoded in pixels],
        dtype=np.float64,
    )
    full_overlap = overlap == 1.0
    count_full = int(np.sum(full_overlap))
    counting = np.arange(1, initial.size + 1)
    duplicate_remove = full_overlap & (
        counting <= initial.size - count_full / 3.0
    )

    edge_flags = np.zeros(initial.size, dtype=bool)
    zero_flags = np.zeros(initial.size, dtype=bool)
    for position, raw_index in enumerate(initial):
        x = x_pixels[position]
        y = y_pixels[position]
        if corrected_edge:
            edge_flags[position] = bool(
                np.any((x == 0) | (x == 511) | (y == 0) | (y == 511))
            )
        else:
            edge_flags[position] = bool(
                np.any((y == 0) | (y == 511))
                or np.any((x == 0) | (y == 511))
            )
        zero_flags[position] = bool(np.any(fluorescence[raw_index, :] == 0))
    remove = duplicate_remove | edge_flags | zero_flags
    retained = initial[~remove]
    if retained.size < 2:
        raise RegistrationError(f"{label}: processROIs retained fewer than two ROIs")
    return retained, {
        "initial_iscell": int(initial.size),
        "full_overlap_entries": count_full,
        "duplicate_removed": int(np.sum(duplicate_remove)),
        "edge_removed": int(np.sum(edge_flags)),
        "zero_trace_removed": int(np.sum(zero_flags)),
        "retained_candidates": int(retained.size),
    }


def match_manual_coordinates(
    track_xy: np.ndarray,
    track_eligible: np.ndarray,
    candidate_raw: np.ndarray,
    stat: np.ndarray,
    *,
    label: str,
    max_distance: float | None,
    min_margin: float | None,
) -> SessionRegistration:
    candidate_xy = np.empty((candidate_raw.size, 2), dtype=np.float64)
    for position, raw_index in enumerate(candidate_raw):
        med = roi_field(stat[raw_index], "med", f"{label}/stat[{raw_index}]")
        if med.size != 2 or not np.all(np.isfinite(med)):
            raise SchemaError(f"{label}/stat[{raw_index}]: invalid med")
        candidate_xy[position] = (float(med[1]), float(med[0]))
    active = np.flatnonzero(track_eligible)
    if active.size == 0:
        raise RegistrationError(f"{label}: no structurally eligible track coordinates")
    distances = np.linalg.norm(
        track_xy[active, None, :] - candidate_xy[None, :, :], axis=2
    )
    if distances.shape[1] < 2:
        raise RegistrationError(f"{label}: fewer than two registration candidates")
    order = np.argsort(distances, axis=1, kind="stable")
    nearest_position = order[:, 0]
    d1 = distances[np.arange(active.size), order[:, 0]]
    d2 = distances[np.arange(active.size), order[:, 1]]
    distance_ok = (
        np.ones(active.size, dtype=bool)
        if max_distance is None
        else d1 <= max_distance
    )
    margin_ok = (
        np.ones(active.size, dtype=bool)
        if min_margin is None
        else (d2 - d1) >= min_margin
    )
    collision = np.zeros(active.size, dtype=bool)
    for candidate in np.unique(nearest_position):
        rows = np.flatnonzero(nearest_position == candidate)
        if rows.size > 1:
            collision[rows] = True
    valid = distance_ok & margin_ok & ~collision

    mapped_raw = np.full(track_xy.shape[0], -1, dtype=np.int64)
    mapped_xy = np.full((track_xy.shape[0], 2), np.nan, dtype=np.float64)
    valid_rows = active[valid]
    mapped_raw[valid_rows] = candidate_raw[nearest_position[valid]]
    mapped_xy[valid_rows] = candidate_xy[nearest_position[valid]]
    return SessionRegistration(
        mapped_raw=mapped_raw,
        mapped_xy=mapped_xy,
        valid=mapped_raw >= 0,
        summary={
            "tracked_columns": int(track_xy.shape[0]),
            "structurally_excluded": int(track_xy.shape[0] - active.size),
            "max_distance_px": max_distance,
            "min_margin_px": min_margin,
            "distance_failures": int(np.sum(~distance_ok)),
            "margin_failures": int(np.sum(distance_ok & ~margin_ok)),
            "collision_failures": int(np.sum(collision)),
            "valid_session_matches": int(np.sum(valid)),
            "d1_median_px": float(np.median(d1)),
            "d1_max_px": float(np.max(d1)),
            "margin_median_px": float(np.median(d2 - d1)),
        },
    )


def match_author_greedy(
    track_xy: np.ndarray,
    track_eligible: np.ndarray,
    candidate_raw: np.ndarray,
    stat: np.ndarray,
    *,
    label: str,
) -> SessionRegistration:
    candidate_xy = np.empty((candidate_raw.size, 2), dtype=np.float64)
    for position, raw_index in enumerate(candidate_raw):
        med = roi_field(stat[raw_index], "med", f"{label}/stat[{raw_index}]")
        if med.size != 2 or not np.all(np.isfinite(med)):
            raise SchemaError(f"{label}/stat[{raw_index}]: invalid med")
        candidate_xy[position] = (float(med[1]), float(med[0]))
    active = np.flatnonzero(track_eligible)
    distances = np.linalg.norm(
        track_xy[active, None, :] - candidate_xy[None, :, :], axis=2
    )
    orders = [list(np.argsort(row, kind="stable")) for row in distances]
    distance_lists = [list(row[order]) for row, order in zip(distances, orders)]
    closest = np.array([order[0] for order in orders], dtype=np.int64)
    initial_closest = closest.copy()
    current_distance = np.array(
        [values[0] for values in distance_lists], dtype=np.float64
    )
    iterations = 0
    rerouted_rows: set[int] = set()
    while True:
        counts = np.bincount(closest, minlength=candidate_raw.size)
        doubles = np.flatnonzero(counts > 1)
        if doubles.size == 0:
            break
        iterations += 1
        if iterations > candidate_raw.size * max(1, active.size):
            raise RegistrationError(f"{label}: author greedy did not converge")
        frozen_doubles = doubles.copy()
        for candidate in frozen_doubles:
            bad = np.flatnonzero(closest == candidate)
            if bad.size < 2:
                continue
            farther = np.flatnonzero(
                current_distance[bad] > np.min(current_distance[bad])
            )
            if farther.size == 0:
                if any(len(distance_lists[row]) < 2 for row in bad):
                    raise RegistrationError(f"{label}: author greedy exhausted candidates")
                second = np.array(
                    [distance_lists[row][1] for row in bad], dtype=np.float64
                )
                farther = np.array([int(np.argmin(second))], dtype=np.int64)
            for relative in farther:
                row = int(bad[int(relative)])
                if not orders[row]:
                    raise RegistrationError(f"{label}: author greedy empty order")
                closest[row] = int(orders[row][0])
                current_distance[row] = float(distance_lists[row][0])
                del orders[row][0]
                del distance_lists[row][0]
                rerouted_rows.add(row)

    mapped_raw = np.full(track_xy.shape[0], -1, dtype=np.int64)
    mapped_xy = np.full((track_xy.shape[0], 2), np.nan, dtype=np.float64)
    mapped_raw[active] = candidate_raw[closest]
    mapped_xy[active] = candidate_xy[closest]
    return SessionRegistration(
        mapped_raw=mapped_raw,
        mapped_xy=mapped_xy,
        valid=mapped_raw >= 0,
        summary={
            "tracked_columns": int(track_xy.shape[0]),
            "structurally_excluded": int(track_xy.shape[0] - active.size),
            "valid_session_matches": int(active.size),
            "collision_loop_iterations": int(iterations),
            "collision_touched_rows": int(len(rerouted_rows)),
            "final_rerouted_rows": int(np.sum(closest != initial_closest)),
            "assigned_distance_median_px": float(np.median(current_distance)),
            "assigned_distance_max_px": float(np.max(current_distance)),
        },
    )


def registration_variant(
    session_matches: dict[str, SessionRegistration],
    *,
    original_count: int,
    variant_name: str,
) -> RegistrationVariant:
    keep = np.logical_and.reduce([session_matches[s].valid for s in SESSIONS])
    retained_k = np.flatnonzero(keep)
    raw_by_session = {
        session: session_matches[session].mapped_raw[retained_k] for session in SESSIONS
    }
    xy_by_session = {
        session: session_matches[session].mapped_xy[retained_k] for session in SESSIONS
    }
    threshold = max(
        MIN_REGISTERED_CELLS, math.ceil(MIN_REGISTRATION_FRACTION * original_count)
    )
    return RegistrationVariant(
        retained_k=retained_k,
        raw_by_session=raw_by_session,
        xy_by_session=xy_by_session,
        summary={
            "variant": variant_name,
            "original_tracked_columns": int(original_count),
            "retained_triplets": int(retained_k.size),
            "required_triplets": int(threshold),
            "fraction_retained": float(retained_k.size / original_count),
            "gate_pass": bool(retained_k.size >= threshold),
            "sessions": {
                session: session_matches[session].summary for session in SESSIONS
            },
        },
    )


def load_registration_session(
    paths: SessionPaths,
    track_xy: np.ndarray,
    track_eligible: np.ndarray,
    expected_neural_shape: tuple[int, int],
) -> tuple[
    SessionRegistration,
    SessionRegistration,
    SessionRegistration,
    SessionRegistration,
    SessionRegistration,
    dict[str, Any],
]:
    label = f"{paths.mouse}/{paths.session}"
    try:
        raw = loadmat(
            paths.fall,
            variable_names=["F", "Fneu", "iscell", "stat", "ops"],
            squeeze_me=True,
            struct_as_record=False,
        )
    except Exception as exc:
        raise SchemaError(f"{label}: cannot load registration variables: {exc}") from exc
    required = {"F", "Fneu", "iscell", "stat", "ops"}
    missing = sorted(required - set(raw))
    if missing:
        raise SchemaError(f"{label}: missing registration variables {missing}")
    fluorescence = np.asarray(raw["F"])
    fneu = np.asarray(raw["Fneu"])
    iscell = np.asarray(raw["iscell"])
    stat = np.asarray(raw["stat"], dtype=object).reshape(-1)
    ops = raw["ops"]
    if fluorescence.shape != expected_neural_shape or fneu.shape != expected_neural_shape:
        raise SchemaError(f"{label}: fluorescence shape differs from header")
    if not np.all(np.isfinite(fluorescence)) or not np.all(np.isfinite(fneu)):
        raise SchemaError(f"{label}: non-finite fluorescence values")
    if iscell.shape[0] != expected_neural_shape[0] or stat.size != expected_neural_shape[0]:
        raise SchemaError(f"{label}: ROI metadata row mismatch")
    if not hasattr(ops, "diameter"):
        raise SchemaError(f"{label}: ops.diameter missing")
    diameter_array = np.asarray(getattr(ops, "diameter"), dtype=np.float64).reshape(-1)
    if diameter_array.size != 1 or not np.isfinite(diameter_array[0]):
        raise SchemaError(f"{label}: invalid ops.diameter")
    diameter = float(diameter_array[0])
    if diameter != 12.0:
        raise SchemaError(f"{label}: ops.diameter {diameter} != 12")
    diameter_distance = diameter / math.sqrt(2.0)

    corrected_candidates, corrected_qc = process_roi_candidates(
        iscell,
        stat,
        fluorescence,
        corrected_edge=True,
        label=f"{label}/corrected",
    )
    author_candidates, author_qc = process_roi_candidates(
        iscell,
        stat,
        fluorescence,
        corrected_edge=False,
        label=f"{label}/author_typo",
    )
    if not np.array_equal(corrected_candidates, author_candidates):
        raise RegistrationError(
            f"{label}: corrected and author-typo candidate arrays differ"
        )
    corrected = match_manual_coordinates(
        track_xy,
        track_eligible,
        corrected_candidates,
        stat,
        label=f"{label}/corrected",
        max_distance=diameter_distance,
        min_margin=MIN_REGISTRATION_MARGIN,
    )
    author = match_manual_coordinates(
        track_xy,
        track_eligible,
        author_candidates,
        stat,
        label=f"{label}/author_typo",
        max_distance=diameter_distance,
        min_margin=MIN_REGISTRATION_MARGIN,
    )
    strict = match_manual_coordinates(
        track_xy,
        track_eligible,
        corrected_candidates,
        stat,
        label=f"{label}/strict_5px_2px",
        max_distance=MAX_REGISTRATION_DISTANCE,
        min_margin=MIN_REGISTRATION_MARGIN,
    )
    no_distance = match_manual_coordinates(
        track_xy,
        track_eligible,
        corrected_candidates,
        stat,
        label=f"{label}/no_distance_margin",
        max_distance=None,
        min_margin=None,
    )
    greedy = match_author_greedy(
        track_xy,
        track_eligible,
        corrected_candidates,
        stat,
        label=f"{label}/author_greedy",
    )
    corrected.summary["process_rois"] = corrected_qc
    author.summary["process_rois"] = author_qc
    strict.summary["process_rois"] = corrected_qc
    no_distance.summary["process_rois"] = corrected_qc
    greedy.summary["process_rois"] = corrected_qc
    return corrected, author, strict, no_distance, greedy, {
        "F_shape": [int(value) for value in fluorescence.shape],
        "iscell_shape": [int(value) for value in iscell.shape],
        "stat_count": int(stat.size),
        "ops_diameter_px": diameter,
        "primary_max_distance_px": diameter_distance,
    }


def validate_headers(paths: SessionPaths) -> tuple[tuple[int, int], dict[str, Any]]:
    label = f"{paths.mouse}/{paths.session}"
    fall = mat_header(paths.fall)
    required_fall = {"spks", "F", "Fneu", "stat", "iscell", "ops"}
    missing = sorted(required_fall - set(fall))
    if missing:
        raise SchemaError(f"{label}: missing Fall variables {missing}")
    shapes = [fall[name][0] for name in ("spks", "F", "Fneu")]
    if len(set(shapes)) != 1 or len(shapes[0]) != 2:
        raise SchemaError(f"{label}: neural array shapes differ {shapes}")
    n_roi, neural_t = shapes[0]
    if fall["iscell"][0][0] != n_roi or int(np.prod(fall["stat"][0])) != n_roi:
        raise SchemaError(f"{label}: Fall ROI metadata header mismatch")
    events = mat_header(paths.events)
    required_events = {"frameTimes", "cue", "cue1", "cue2", "cue3", "lick"}
    event_missing = sorted(required_events - set(events))
    if event_missing:
        raise SchemaError(f"{label}: missing event headers {event_missing}")
    return (int(n_roi), int(neural_t)), {
        "neural_shape": [int(n_roi), int(neural_t)],
        "fall_variables": sorted(fall),
        "event_variables": sorted(events),
    }


def preflight(
    archive_path: Path, extracted_root: Path
) -> tuple[
    dict[str, Any],
    dict[tuple[str, str], EventData],
    dict[str, MouseRegistration],
    dict[tuple[str, str], tuple[int, int]],
]:
    source_summary = verify_source(archive_path, extracted_root)
    events: dict[tuple[str, str], EventData] = {}
    neural_shapes: dict[tuple[str, str], tuple[int, int]] = {}
    session_summaries: dict[str, Any] = {}
    paths_by_key: dict[tuple[str, str], SessionPaths] = {}

    for mouse in MICE:
        for session in SESSIONS:
            paths = session_paths(extracted_root, mouse, session)
            paths_by_key[(mouse, session)] = paths
            shape, header_summary = validate_headers(paths)
            event, event_summary = validate_event_data(paths, shape)
            events[(mouse, session)] = event
            neural_shapes[(mouse, session)] = shape
            session_summaries[f"{mouse}/{session}"] = {
                "header": header_summary,
                "events": event_summary,
            }

    observed_breaks = {
        key: summary["events"]["segment_break_indices_zero_based"]
        for key, summary in session_summaries.items()
        if summary["events"]["segment_break_indices_zero_based"]
    }
    expected_breaks = {"PL01/o1d2": [10149]}
    if observed_breaks != expected_breaks:
        raise SchemaError(
            f"frame-time break manifest {observed_breaks} != {expected_breaks}"
        )

    registrations: dict[str, MouseRegistration] = {}
    registration_summaries: dict[str, Any] = {}
    observed_total = 0
    observed_primary_total = 0
    observed_greedy_total = 0
    for mouse in MICE:
        expected_count = TRACKED_COUNTS[mouse]
        observed_total += expected_count
        masks: dict[str, np.ndarray] = {}
        out_of_fov_by_session: dict[str, list[int]] = {}
        out_of_fov_union: set[int] = set()
        for session in SESSIONS:
            paths = paths_by_key[(mouse, session)]
            try:
                mask = np.load(paths.mask, allow_pickle=False)
            except Exception as exc:
                raise SchemaError(f"{mouse}/{session}: cannot load mask: {exc}") from exc
            mask = np.asarray(mask, dtype=np.float64)
            if mask.shape != (2, expected_count) or not np.all(np.isfinite(mask)):
                raise SchemaError(
                    f"{mouse}/{session}: mask shape/value gate failed: {mask.shape}"
                )
            if not np.array_equal(mask, np.rint(mask)):
                raise SchemaError(f"{mouse}/{session}: mask coordinates are not integers")
            invalid = np.flatnonzero(
                np.any((mask < 0) | (mask > 511), axis=0)
            )
            out_of_fov_by_session[session] = [int(value) for value in invalid]
            out_of_fov_union.update(int(value) for value in invalid)
            masks[session] = mask
        expected_oob = {KNOWN_OOB_TRIPLET[1]} if mouse == KNOWN_OOB_TRIPLET[0] else set()
        if out_of_fov_union != expected_oob:
            raise SchemaError(
                f"{mouse}: out-of-FOV columns {sorted(out_of_fov_union)} != "
                f"{sorted(expected_oob)}"
            )
        track_eligible = np.ones(expected_count, dtype=bool)
        if expected_oob:
            track_eligible[list(expected_oob)] = False

        corrected_matches: dict[str, SessionRegistration] = {}
        author_matches: dict[str, SessionRegistration] = {}
        strict_matches: dict[str, SessionRegistration] = {}
        no_distance_matches: dict[str, SessionRegistration] = {}
        greedy_matches: dict[str, SessionRegistration] = {}
        for session in SESSIONS:
            paths = paths_by_key[(mouse, session)]
            track_xy = masks[session].T.copy()
            corrected, author, strict, no_distance, greedy, registration_shape = (
                load_registration_session(
                    paths,
                    track_xy,
                    track_eligible,
                    neural_shapes[(mouse, session)],
                )
            )
            corrected_matches[session] = corrected
            author_matches[session] = author
            strict_matches[session] = strict
            no_distance_matches[session] = no_distance
            greedy_matches[session] = greedy
            session_summaries[f"{mouse}/{session}"]["registration_shape"] = (
                registration_shape
            )
            session_summaries[f"{mouse}/{session}"]["mask_oob_columns_zero_based"] = (
                out_of_fov_by_session[session]
            )
            if not np.array_equal(corrected.mapped_raw, author.mapped_raw):
                raise RegistrationError(
                    f"{mouse}/{session}: corrected and author-typo maps differ"
                )
        corrected_variant = registration_variant(
            corrected_matches,
            original_count=expected_count,
            variant_name="diameter_margin_corrected_edge_primary",
        )
        author_variant = registration_variant(
            author_matches,
            original_count=expected_count,
            variant_name="author_edge_typo_sensitivity",
        )
        strict_variant = registration_variant(
            strict_matches,
            original_count=expected_count,
            variant_name="strict_5px_2px_sensitivity",
        )
        no_distance_variant = registration_variant(
            no_distance_matches,
            original_count=expected_count,
            variant_name="no_distance_margin_sensitivity",
        )
        greedy_variant = registration_variant(
            greedy_matches,
            original_count=expected_count,
            variant_name="author_greedy_sensitivity",
        )
        if not corrected_variant.summary["gate_pass"]:
            raise RegistrationError(
                f"{mouse}: corrected registration retained "
                f"{corrected_variant.retained_k.size}/{expected_count}, required "
                f"{corrected_variant.summary['required_triplets']}"
            )
        if corrected_variant.retained_k.size != EXPECTED_PRIMARY_RETAINED[mouse]:
            raise RegistrationError(
                f"{mouse}: primary retained {corrected_variant.retained_k.size} != "
                f"{EXPECTED_PRIMARY_RETAINED[mouse]}"
            )
        if author_variant.retained_k.size != corrected_variant.retained_k.size:
            raise RegistrationError(f"{mouse}: author-typo retained count differs")
        if no_distance_variant.retained_k.size != EXPECTED_NO_DISTANCE_RETAINED[mouse]:
            raise RegistrationError(
                f"{mouse}: no-distance retained {no_distance_variant.retained_k.size} != "
                f"{EXPECTED_NO_DISTANCE_RETAINED[mouse]}"
            )
        expected_greedy = expected_count - (1 if mouse == KNOWN_OOB_TRIPLET[0] else 0)
        if greedy_variant.retained_k.size != expected_greedy:
            raise RegistrationError(
                f"{mouse}: author-greedy retained {greedy_variant.retained_k.size} != "
                f"{expected_greedy}"
            )
        strict_variant.summary["sensitivity_available"] = bool(
            strict_variant.retained_k.size >= 6
        )
        observed_primary_total += int(corrected_variant.retained_k.size)
        observed_greedy_total += int(greedy_variant.retained_k.size)
        registrations[mouse] = MouseRegistration(
            corrected_variant,
            author_variant,
            strict_variant,
            no_distance_variant,
            greedy_variant,
        )
        registration_summaries[mouse] = {
            "corrected": corrected_variant.summary,
            "author_typo": author_variant.summary,
            "strict_5px_2px": strict_variant.summary,
            "no_distance_margin": no_distance_variant.summary,
            "author_greedy": greedy_variant.summary,
        }
    if observed_total != EXPECTED_TRACKED_TOTAL:
        raise SchemaError(
            f"tracked total {observed_total} != {EXPECTED_TRACKED_TOTAL}"
        )
    if observed_primary_total != EXPECTED_PRIMARY_RETAINED_TOTAL:
        raise RegistrationError(
            f"primary retained total {observed_primary_total} != "
            f"{EXPECTED_PRIMARY_RETAINED_TOTAL}"
        )
    if observed_greedy_total != EXPECTED_AUTHOR_GREEDY_TOTAL:
        raise RegistrationError(
            f"author-greedy total {observed_greedy_total} != "
            f"{EXPECTED_AUTHOR_GREEDY_TOTAL}"
        )

    summary = {
        "source": source_summary,
        "session_schema": session_summaries,
        "registration": registration_summaries,
        "cohort": {
            "mice": list(MICE),
            "sessions": list(SESSIONS),
            "tracked_counts": TRACKED_COUNTS,
            "tracked_total": observed_total,
            "primary_retained_counts": EXPECTED_PRIMARY_RETAINED,
            "primary_retained_total": observed_primary_total,
            "author_greedy_retained_total": observed_greedy_total,
            "independent_unit": "mouse",
            "n_mice": len(MICE),
        },
    }
    return summary, events, registrations, neural_shapes


def author_smoothing_weights() -> np.ndarray:
    ephys_samples = np.arange(51, dtype=np.float64)
    ephys_times = ephys_samples * 0.02
    ephys_weights = np.exp(-0.5 * (ephys_samples / 15.0) ** 2)
    imaging_times = np.arange(SMOOTH_HISTORY + 1, dtype=np.float64) / FRAME_RATE
    return np.interp(imaging_times, ephys_times, ephys_weights)


def causal_halfnormal(activity: np.ndarray, segment_ids: np.ndarray) -> np.ndarray:
    if activity.ndim != 2:
        raise NumericalError(f"activity must be 2D, got {activity.shape}")
    if segment_ids.shape != (activity.shape[1],):
        raise NumericalError("segment_ids length differs from activity")
    weights = author_smoothing_weights()
    output = np.empty_like(activity, dtype=np.float64)
    starts = np.concatenate(([0], np.flatnonzero(np.diff(segment_ids) != 0) + 1))
    stops = np.concatenate((starts[1:], [activity.shape[1]]))
    for start, stop in zip(starts, stops):
        segment = activity[:, start:stop]
        numerator = lfilter(weights, [1.0], segment, axis=1)
        denominator = lfilter(weights, [1.0], np.ones(stop - start, dtype=float))
        output[:, start:stop] = numerator / denominator[None, :]
    if not np.all(np.isfinite(output)):
        raise NumericalError("non-finite causal smoothing output")
    return output


def bin_trial_activity(
    activity: np.ndarray, event: EventData, *, n_bins: int = SENSITIVITY_BINS
) -> np.ndarray:
    n_cells = activity.shape[0]
    output = np.empty((n_cells, event.cue.size, n_bins), dtype=np.float64)
    for trial, onset in enumerate(event.cue):
        baseline_start = int(np.searchsorted(event.frame_times, onset - 1.0, side="left"))
        baseline_stop = int(np.searchsorted(event.frame_times, onset, side="left"))
        if baseline_stop <= baseline_start:
            raise SchemaError(f"empty baseline at trial {trial}")
        baseline = np.mean(activity[:, baseline_start:baseline_stop], axis=1)
        for bin_index in range(n_bins):
            start = int(
                np.searchsorted(
                    event.frame_times,
                    onset + bin_index * BIN_SECONDS,
                    side="left",
                )
            )
            stop = int(
                np.searchsorted(
                    event.frame_times,
                    onset + (bin_index + 1) * BIN_SECONDS,
                    side="left",
                )
            )
            if stop <= start:
                raise SchemaError(f"empty response bin at trial {trial}, bin {bin_index}")
            output[:, trial, bin_index] = (
                np.mean(activity[:, start:stop], axis=1) - baseline
            )
    if not np.all(np.isfinite(output)):
        raise NumericalError("non-finite trial response")
    return output


def cue_centered_signature(
    responses: np.ndarray,
    labels: np.ndarray,
    trial_indices: np.ndarray,
    *,
    n_bins: int,
) -> np.ndarray:
    means = []
    for cue_label in (1, 2, 3):
        selected = trial_indices[labels[trial_indices] == cue_label]
        if selected.size == 0:
            raise SchemaError(f"empty cue {cue_label} signature")
        means.append(np.mean(responses[:, selected, :n_bins], axis=1))
    stacked = np.stack(means, axis=1)
    centered = stacked - np.mean(stacked, axis=1, keepdims=True)
    flattened = centered.reshape(centered.shape[0], -1)
    if not np.all(np.isfinite(flattened)):
        raise NumericalError("non-finite cue-centered signature")
    return flattened


def all_trial_signature(
    responses: np.ndarray, labels: np.ndarray, *, n_bins: int
) -> np.ndarray:
    return cue_centered_signature(
        responses, labels, np.arange(labels.size), n_bins=n_bins
    )


def normalized_midrank(values: np.ndarray, true_index: int) -> float:
    true_value = float(values[true_index])
    less = int(np.sum(values < true_value))
    equal = int(np.sum(values == true_value))
    if equal < 1 or values.size < 2:
        raise NumericalError("invalid midrank inputs")
    midrank = less + (equal + 1) / 2.0
    return float((midrank - 1.0) / (values.size - 1.0))


def cosine_matrix(
    source: np.ndarray, target: np.ndarray
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    source_norm = np.linalg.norm(source, axis=1)
    target_norm = np.linalg.norm(target, axis=1)
    source_valid = source_norm > 0
    target_valid = target_norm > 0
    normalized_source = np.zeros_like(source, dtype=np.float64)
    normalized_target = np.zeros_like(target, dtype=np.float64)
    normalized_source[source_valid] = source[source_valid] / source_norm[source_valid, None]
    normalized_target[target_valid] = target[target_valid] / target_norm[target_valid, None]
    matrix = normalized_source @ normalized_target.T
    if not np.all(np.isfinite(matrix)):
        raise NumericalError("non-finite cosine matrix")
    return matrix, source_valid, target_valid


def directional_rank_advantage(matrix: np.ndarray) -> np.ndarray:
    n_cells = matrix.shape[0]
    if matrix.shape != (n_cells, n_cells):
        raise NumericalError("cosine matrix is not square")
    return np.array(
        [normalized_midrank(matrix[row], row) - 0.5 for row in range(n_cells)],
        dtype=np.float64,
    )


def local_directional_rank_advantage(
    matrix: np.ndarray, target_xy: np.ndarray
) -> np.ndarray:
    n_cells = matrix.shape[0]
    if n_cells < 6 or target_xy.shape != (n_cells, 2):
        raise NumericalError("local-spatial null requires at least six aligned cells")
    coordinate_distances = np.linalg.norm(
        target_xy[:, None, :] - target_xy[None, :, :], axis=2
    )
    result = np.empty(n_cells, dtype=np.float64)
    for row in range(n_cells):
        neighbors = np.argsort(coordinate_distances[row], kind="stable")
        neighbors = neighbors[neighbors != row][:5]
        comparison_indices = np.concatenate(([row], neighbors))
        values = matrix[row, comparison_indices]
        result[row] = normalized_midrank(values, 0) - 0.5
    return result


def compute_mouse_anchor(
    responses_by_session: dict[str, np.ndarray],
    events_by_session: dict[str, EventData],
    xy_by_session: dict[str, np.ndarray],
    *,
    n_bins: int = PRIMARY_BINS,
    population_center: bool = True,
    pairs: tuple[tuple[str, str], ...] = (
        ("o1d1", "o1d2"),
        ("o1d2", "o1d3"),
        ("o1d1", "o1d3"),
    ),
    local: bool = False,
) -> dict[str, Any]:
    signatures: dict[str, np.ndarray] = {}
    for session in SESSIONS:
        signature = all_trial_signature(
            responses_by_session[session],
            events_by_session[session].cue_labels,
            n_bins=n_bins,
        )
        if population_center:
            signature = signature - np.mean(signature, axis=0, keepdims=True)
        signatures[session] = signature

    pair_advantages = []
    same_cosines = []
    pair_summaries: dict[str, Any] = {}
    for source, target in pairs:
        matrix, source_valid, target_valid = cosine_matrix(
            signatures[source], signatures[target]
        )
        if local:
            forward = local_directional_rank_advantage(matrix, xy_by_session[target])
            reverse = local_directional_rank_advantage(
                matrix.T, xy_by_session[source]
            )
        else:
            forward = directional_rank_advantage(matrix)
            reverse = directional_rank_advantage(matrix.T)
        symmetric = (forward + reverse) / 2.0
        symmetric[~(source_valid & target_valid)] = 0.0
        pair_advantages.append(symmetric)
        diagonal = np.diag(matrix)
        same_cosines.extend(float(value) for value in diagonal)
        pair_summaries[f"{SESSION_LABELS[source]}_{SESSION_LABELS[target]}"] = {
            "median_advantage": float(np.median(symmetric)),
            "mean_advantage": float(np.mean(symmetric)),
            "median_same_cell_cosine": float(np.median(diagonal)),
        }
    cell_average = np.mean(np.stack(pair_advantages, axis=1), axis=1)
    return {
        "mouse_anchor": float(np.median(cell_average)),
        "n_cells": int(cell_average.size),
        "same_cell_cosines": same_cosines,
        "pair_summaries": pair_summaries,
    }


def phase_indices(n_trials: int, mode: str) -> tuple[np.ndarray, np.ndarray, int]:
    if mode == "sixty":
        k = PRIMARY_PHASE_TRIALS
        minimum = PRIMARY_MIN_FOLD_TRIALS
    elif mode == "thirds":
        k = n_trials // 3
        minimum = THIRDS_MIN_FOLD_TRIALS
    else:
        raise ValueError(f"unknown phase mode: {mode}")
    if 2 * k > n_trials:
        raise SchemaError(f"phase windows overlap for n={n_trials}, k={k}")
    return np.arange(k), np.arange(n_trials - k, n_trials), minimum


def compute_mouse_plasticity(
    responses_by_session: dict[str, np.ndarray],
    events_by_session: dict[str, EventData],
    *,
    n_bins: int = PRIMARY_BINS,
    phase_mode: str = "sixty",
    insufficient_is_unavailable: bool = False,
) -> dict[str, Any]:
    c_by_session: dict[str, float] = {}
    for session in SESSIONS:
        responses = responses_by_session[session]
        labels = events_by_session[session].cue_labels
        early, late, minimum = phase_indices(labels.size, phase_mode)
        phase_signatures: dict[tuple[str, int], np.ndarray] = {}
        for phase_name, indices in (("early", early), ("late", late)):
            for fold in (0, 1):
                folded_parts = []
                for cue_label in (1, 2, 3):
                    cue_indices = indices[labels[indices] == cue_label]
                    selected = cue_indices[fold::2]
                    if selected.size < minimum:
                        message = (
                            f"{session}/{phase_mode}/{phase_name}/cue{cue_label}/"
                            f"fold{fold}: {selected.size} < {minimum}"
                        )
                        if insufficient_is_unavailable:
                            raise SensitivityUnavailableError(message)
                        raise SchemaError(message)
                    folded_parts.append(
                        np.mean(responses[:, selected, :n_bins], axis=1)
                    )
                stacked = np.stack(folded_parts, axis=1)
                centered = stacked - np.mean(stacked, axis=1, keepdims=True)
                phase_signatures[(phase_name, fold)] = centered.reshape(
                    centered.shape[0], -1
                )
        deltas = [
            phase_signatures[("late", fold)]
            - phase_signatures[("early", fold)]
            for fold in (0, 1)
        ]
        norm0 = np.linalg.norm(deltas[0], axis=1)
        norm1 = np.linalg.norm(deltas[1], axis=1)
        cosine = np.zeros(norm0.size, dtype=np.float64)
        nonzero = (norm0 > 0) & (norm1 > 0)
        cosine[nonzero] = np.sum(
            deltas[0][nonzero] * deltas[1][nonzero], axis=1
        ) / (norm0[nonzero] * norm1[nonzero])
        if not np.all(np.isfinite(cosine)):
            raise NumericalError(f"{session}: non-finite plasticity cosine")
        c_by_session[session] = float(np.mean(cosine))
    p_zero = c_by_session["o1d1"]
    p_specific = c_by_session["o1d1"] - (
        c_by_session["o1d2"] + c_by_session["o1d3"]
    ) / 2.0
    return {
        "C_by_session": {
            SESSION_LABELS[key]: value for key, value in c_by_session.items()
        },
        "P_zero": float(p_zero),
        "P_specific": float(p_specific),
    }


def compute_mouse_behavior(event: EventData) -> dict[str, float]:
    lick_contrast = np.empty(event.cue.size, dtype=np.float64)
    for trial, onset in enumerate(event.cue):
        relative = event.lick - onset
        post = int(np.sum((relative > 0) & (relative < 2.5)))
        pre = int(np.sum((relative > -2.5) & (relative < 0)))
        lick_contrast[trial] = post - pre
    early = np.arange(PRIMARY_PHASE_TRIALS)
    late = np.arange(event.cue.size - PRIMARY_PHASE_TRIALS, event.cue.size)

    def difference(indices: np.ndarray) -> float:
        cs_plus = lick_contrast[indices[event.cue_labels[indices] == 1]]
        cs_minus = lick_contrast[indices[event.cue_labels[indices] == 3]]
        if cs_plus.size == 0 or cs_minus.size == 0:
            raise SchemaError("behavior phase has no CS+ or CS- trials")
        return float(np.mean(cs_plus) - np.mean(cs_minus))

    early_difference = difference(early)
    late_difference = difference(late)
    return {
        "early_CSplus_minus_CSminus": early_difference,
        "late_CSplus_minus_CSminus": late_difference,
        "B": late_difference - early_difference,
    }


def exact_one_sided_signflip(values: Iterable[float]) -> dict[str, Any]:
    vector = np.asarray(list(values), dtype=np.float64)
    if vector.shape != (len(MICE),) or not np.all(np.isfinite(vector)):
        raise NumericalError(f"sign-flip vector shape/value gate failed: {vector.shape}")
    observed = float(np.mean(vector))
    tail = 0
    total = 0
    for signs in itertools.product((-1.0, 1.0), repeat=vector.size):
        statistic = float(np.mean(vector * np.asarray(signs)))
        tail += int(statistic >= observed)
        total += 1
    return {
        "n_mice": int(vector.size),
        "observed_mean": observed,
        "positive_mice": int(np.sum(vector > 0)),
        "zero_mice": int(np.sum(vector == 0)),
        "tail_assignments": tail,
        "total_assignments": total,
        "p_exact_one_sided": float(tail / total),
    }


def aggregate_component(values_by_mouse: dict[str, float]) -> dict[str, Any]:
    values = [values_by_mouse[mouse] for mouse in MICE]
    return {
        "mouse_values": values_by_mouse,
        "mean": float(np.mean(values)),
        "median": float(np.median(values)),
        "signflip": exact_one_sided_signflip(values),
    }


def component_pass(component: dict[str, Any], *, require_six_positive: bool) -> bool:
    signflip = component["signflip"]
    return bool(
        component["mean"] > 0
        and signflip["p_exact_one_sided"] <= ALPHA
        and (not require_six_positive or signflip["positive_mice"] >= 6)
    )


def load_spks(path: Path, expected_shape: tuple[int, int], label: str) -> np.ndarray:
    try:
        raw = loadmat(path, variable_names=["spks"], squeeze_me=True)
    except Exception as exc:
        raise SchemaError(f"{label}: cannot load spks: {exc}") from exc
    if "spks" not in raw:
        raise SchemaError(f"{label}: spks missing")
    spks = np.asarray(raw["spks"])
    if spks.shape != expected_shape:
        raise SchemaError(f"{label}: spks shape {spks.shape} != {expected_shape}")
    if not np.all(np.isfinite(spks)):
        raise SchemaError(f"{label}: non-finite spks")
    return spks


def variant_features(
    responses: np.ndarray,
    union_raw: np.ndarray,
    variant_raw: np.ndarray,
) -> np.ndarray:
    positions = np.searchsorted(union_raw, variant_raw)
    if np.any(positions >= union_raw.size) or not np.array_equal(
        union_raw[positions], variant_raw
    ):
        raise NumericalError("variant raw ROI lookup failed")
    return responses[positions]


def execute_endpoints(
    events: dict[tuple[str, str], EventData],
    registrations: dict[str, MouseRegistration],
    neural_shapes: dict[tuple[str, str], tuple[int, int]],
    extracted_root: Path,
) -> dict[str, Any]:
    primary_anchor: dict[str, float] = {}
    primary_same_cosines: list[float] = []
    primary_p0: dict[str, float] = {}
    primary_pspecific: dict[str, float] = {}
    behavior_b: dict[str, float] = {}
    behavior_late: dict[str, float] = {}
    mouse_details: dict[str, Any] = {}

    sensitivity_values: dict[str, dict[str, dict[str, float]]] = {
        name: {"A": {}, "P_zero": {}, "P_specific": {}}
        for name in (
            "author_edge_typo",
            "strict_5px_2px",
            "no_distance_margin",
            "author_greedy",
            "local_spatial_null",
            "raw_unsmoothed_spks",
            "cue_window_0_2p5",
            "first_last_one_third",
            "no_population_residualization",
            "adjacent_pairs_only",
        )
    }
    sensitivity_available: dict[str, bool] = {
        name: True for name in sensitivity_values
    }

    for mouse in MICE:
        corrected = registrations[mouse].corrected
        author = registrations[mouse].author_typo
        registration_variants = {
            "primary": corrected,
            "author_edge_typo": author,
            "strict_5px_2px": registrations[mouse].strict_5px_2px,
            "no_distance_margin": registrations[mouse].no_distance_margin,
            "author_greedy": registrations[mouse].author_greedy,
        }
        smoothed_by_variant: dict[str, dict[str, np.ndarray]] = {
            name: {} for name in registration_variants
        }
        corrected_raw: dict[str, np.ndarray] = {}
        mouse_events = {session: events[(mouse, session)] for session in SESSIONS}

        for session in SESSIONS:
            paths = session_paths(extracted_root, mouse, session)
            spks = load_spks(
                paths.fall, neural_shapes[(mouse, session)], f"{mouse}/{session}"
            )
            event = mouse_events[session]
            spks = spks[:, : event.frame_times.size]
            raw_groups = [
                variant.raw_by_session[session]
                for variant in registration_variants.values()
                if variant.retained_k.size
            ]
            union_raw = np.unique(np.concatenate(raw_groups)).astype(np.int64)
            selected = np.asarray(spks[union_raw], dtype=np.float64)
            smoothed = causal_halfnormal(selected, event.segment_ids)
            smoothed_trials = bin_trial_activity(smoothed, event)
            raw_trials = bin_trial_activity(selected, event)
            for name, variant in registration_variants.items():
                smoothed_by_variant[name][session] = variant_features(
                    smoothed_trials, union_raw, variant.raw_by_session[session]
                )
            corrected_raw[session] = variant_features(
                raw_trials, union_raw, corrected.raw_by_session[session]
            )
            del spks, selected, smoothed, smoothed_trials, raw_trials

        corrected_smoothed = smoothed_by_variant["primary"]

        anchor = compute_mouse_anchor(
            corrected_smoothed,
            mouse_events,
            corrected.xy_by_session,
        )
        plasticity = compute_mouse_plasticity(corrected_smoothed, mouse_events)
        behavior = compute_mouse_behavior(mouse_events["o1d1"])
        primary_anchor[mouse] = anchor["mouse_anchor"]
        primary_same_cosines.extend(anchor["same_cell_cosines"])
        primary_p0[mouse] = plasticity["P_zero"]
        primary_pspecific[mouse] = plasticity["P_specific"]
        behavior_b[mouse] = behavior["B"]
        behavior_late[mouse] = behavior["late_CSplus_minus_CSminus"]

        local_anchor = compute_mouse_anchor(
            corrected_smoothed,
            mouse_events,
            corrected.xy_by_session,
            local=True,
        )
        sensitivity_values["local_spatial_null"]["A"][mouse] = local_anchor[
            "mouse_anchor"
        ]

        for sensitivity_name in (
            "author_edge_typo",
            "strict_5px_2px",
            "no_distance_margin",
            "author_greedy",
        ):
            variant = registration_variants[sensitivity_name]
            if variant.retained_k.size >= 6:
                variant_anchor = compute_mouse_anchor(
                    smoothed_by_variant[sensitivity_name],
                    mouse_events,
                    variant.xy_by_session,
                )
                sensitivity_values[sensitivity_name]["A"][mouse] = variant_anchor[
                    "mouse_anchor"
                ]
            else:
                sensitivity_available[sensitivity_name] = False

        raw_anchor = compute_mouse_anchor(
            corrected_raw, mouse_events, corrected.xy_by_session
        )
        raw_plastic = compute_mouse_plasticity(corrected_raw, mouse_events)
        sensitivity_values["raw_unsmoothed_spks"]["A"][mouse] = raw_anchor[
            "mouse_anchor"
        ]
        sensitivity_values["raw_unsmoothed_spks"]["P_zero"][mouse] = raw_plastic[
            "P_zero"
        ]
        sensitivity_values["raw_unsmoothed_spks"]["P_specific"][mouse] = (
            raw_plastic["P_specific"]
        )

        wide_anchor = compute_mouse_anchor(
            corrected_smoothed,
            mouse_events,
            corrected.xy_by_session,
            n_bins=SENSITIVITY_BINS,
        )
        wide_plastic = compute_mouse_plasticity(
            corrected_smoothed, mouse_events, n_bins=SENSITIVITY_BINS
        )
        sensitivity_values["cue_window_0_2p5"]["A"][mouse] = wide_anchor[
            "mouse_anchor"
        ]
        sensitivity_values["cue_window_0_2p5"]["P_zero"][mouse] = wide_plastic[
            "P_zero"
        ]
        sensitivity_values["cue_window_0_2p5"]["P_specific"][mouse] = (
            wide_plastic["P_specific"]
        )

        try:
            thirds = compute_mouse_plasticity(
                corrected_smoothed,
                mouse_events,
                phase_mode="thirds",
                insufficient_is_unavailable=True,
            )
        except SensitivityUnavailableError:
            sensitivity_available["first_last_one_third"] = False
        else:
            sensitivity_values["first_last_one_third"]["P_zero"][mouse] = thirds[
                "P_zero"
            ]
            sensitivity_values["first_last_one_third"]["P_specific"][mouse] = (
                thirds["P_specific"]
            )

        uncentered = compute_mouse_anchor(
            corrected_smoothed,
            mouse_events,
            corrected.xy_by_session,
            population_center=False,
        )
        sensitivity_values["no_population_residualization"]["A"][mouse] = (
            uncentered["mouse_anchor"]
        )

        adjacent = compute_mouse_anchor(
            corrected_smoothed,
            mouse_events,
            corrected.xy_by_session,
            pairs=(("o1d1", "o1d2"), ("o1d2", "o1d3")),
        )
        sensitivity_values["adjacent_pairs_only"]["A"][mouse] = adjacent[
            "mouse_anchor"
        ]

        mouse_details[mouse] = {
            "n_primary_cells": anchor["n_cells"],
            "primary_anchor": anchor["mouse_anchor"],
            "primary_anchor_pairs": anchor["pair_summaries"],
            "primary_plasticity": plasticity,
            "behavior": behavior,
        }

    anchor_component = aggregate_component(primary_anchor)
    anchor_component["pooled_same_cell_cosine_median"] = float(
        np.median(primary_same_cosines)
    )
    anchor_conditions = {
        "grand_mean_positive": anchor_component["mean"] > 0,
        "pooled_same_cell_cosine_median_positive": anchor_component[
            "pooled_same_cell_cosine_median"
        ]
        > 0,
        "at_least_six_positive_mice": anchor_component["signflip"][
            "positive_mice"
        ]
        >= 6,
        "p_at_most_alpha": anchor_component["signflip"]["p_exact_one_sided"]
        <= ALPHA,
    }
    anchor_pass = bool(all(anchor_conditions.values()))

    p0_component = aggregate_component(primary_p0)
    pspecific_component = aggregate_component(primary_pspecific)
    p0_pass = component_pass(p0_component, require_six_positive=True)
    pspecific_pass = component_pass(pspecific_component, require_six_positive=True)
    behavior_component = aggregate_component(behavior_b)
    late_behavior_component = aggregate_component(behavior_late)
    behavior_change_pass = component_pass(
        behavior_component, require_six_positive=False
    )
    behavior_late_pass = component_pass(
        late_behavior_component, require_six_positive=False
    )
    behavior_pass = behavior_change_pass and behavior_late_pass

    sensitivity_results: dict[str, Any] = {}
    for name, metrics in sensitivity_values.items():
        item: dict[str, Any] = {"available": sensitivity_available[name]}
        if sensitivity_available[name]:
            for metric, values in metrics.items():
                if len(values) == len(MICE):
                    item[metric] = aggregate_component(values)
                elif values:
                    raise NumericalError(
                        f"partial sensitivity metric {name}/{metric}: {len(values)} mice"
                    )
        sensitivity_results[name] = item

    direction_names = (
        "local_spatial_null",
        "author_edge_typo",
        "strict_5px_2px",
        "no_distance_margin",
        "author_greedy",
    )
    direction_gates = {
        name: bool(
            sensitivity_results[name]["available"]
            and sensitivity_results[name]["A"]["mean"] > 0
        )
        for name in direction_names
    }
    registration_local_direction_ok = all(direction_gates.values())
    primary_conjunction = anchor_pass and p0_pass and pspecific_pass
    if not primary_conjunction:
        status = "D7_COMPONENT_CONJUNCTION_NOT_SUPPORTED"
    elif not registration_local_direction_ok:
        status = "D7_REGISTRATION_OR_LOCAL_TUNING_SENSITIVE"
    elif behavior_pass:
        status = "D7_STABLE_ANCHOR_AND_LEARNING_PLASTIC_EXPRESSION_SUPPORTED"
    else:
        status = "D7_STABLE_ANCHOR_AND_WITHIN_SESSION_CHANGE_SUPPORTED"

    return {
        "status": status,
        "statistical_assumptions": {
            "signflip_null": (
                "Exact one-sided enumeration assumes sign symmetry of each "
                "mouse-level statistic under its null."
            ),
            "independent_unit": "mouse",
            "n_mice": len(MICE),
            "small_sample_warning": (
                "Type-I interpretation is assumption-dependent at n=8; no "
                "asymptotic approximation or independent holdout cohort is used."
            ),
        },
        "primary": {
            "anchor": anchor_component,
            "anchor_conditions": anchor_conditions,
            "anchor_pass": anchor_pass,
            "P_zero": p0_component,
            "P_zero_pass": p0_pass,
            "P_specific": pspecific_component,
            "P_specific_pass": pspecific_pass,
            "behavior_B": behavior_component,
            "behavior_B_pass": behavior_change_pass,
            "behavior_late_discrimination": late_behavior_component,
            "behavior_late_discrimination_pass": behavior_late_pass,
            "behavior_gate_pass": behavior_pass,
            "component_conjunction_pass": primary_conjunction,
        },
        "sensitivity": sensitivity_results,
        "sensitivity_direction_gates": direction_gates,
        "mouse_details": mouse_details,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=("preflight", "execute"), required=True)
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--extracted-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--source-lock", type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.output.exists():
        print(f"refusing to overwrite existing output: {args.output}", file=sys.stderr)
        return 3
    payload: dict[str, Any] = {
        "contract_id": CONTRACT_ID,
        "mode": args.mode,
    }
    try:
        payload["runtime"] = verify_runtime()
        if args.mode == "execute":
            if args.source_lock is None:
                raise ExecutionLockError("--source-lock is required for execute mode")
            source_lock_path = args.source_lock.resolve()
            if normalized_path(source_lock_path) != normalized_path(
                EXPECTED_SOURCE_LOCK_PATH
            ):
                raise ExecutionLockError(
                    f"source lock {source_lock_path} != canonical "
                    f"{EXPECTED_SOURCE_LOCK_PATH.resolve()}"
                )
            lock = load_execution_lock(source_lock_path)
            provider_path = resolve_lock_artifact(lock["provider_archive"]["path"])
            if normalized_path(provider_path) != normalized_path(args.archive):
                raise ExecutionLockError("--archive differs from provider_archive lock")
            lock_digest = hash_file(source_lock_path)["sha256"]
            payload["source_lock"] = {
                "path": str(source_lock_path),
                "bytes": int(source_lock_path.stat().st_size),
                "sha256": lock_digest,
                "roles": sorted(lock),
            }
        preflight_summary, events, registrations, neural_shapes = preflight(
            args.archive, args.extracted_root
        )
        payload["preflight"] = preflight_summary
        if args.mode == "preflight":
            payload["status"] = "D7_PREFLIGHT_PASS / ENDPOINT_NOT_RUN"
        else:
            endpoint = execute_endpoints(
                events, registrations, neural_shapes, args.extracted_root
            )
            payload.update(endpoint)
    except GateError as exc:
        payload["status"] = exc.status
        payload["error"] = str(exc)
        write_json_exclusive(args.output, payload)
        print(json.dumps(to_builtin(payload), ensure_ascii=False, indent=2))
        return 2
    except Exception as exc:
        payload["status"] = "D7_UNEXPECTED_EXECUTION_BLOCKED"
        payload["error"] = f"{type(exc).__name__}: {exc}"
        write_json_exclusive(args.output, payload)
        print(json.dumps(to_builtin(payload), ensure_ascii=False, indent=2))
        return 2
    write_json_exclusive(args.output, payload)
    print(json.dumps(to_builtin(payload), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
