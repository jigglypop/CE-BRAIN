from __future__ import annotations

import argparse
import hashlib
import json
import math
import platform
import warnings
import zlib
from pathlib import Path

import numpy as np
import scipy
from scipy.stats import rankdata


EXPECTED_MANIFEST_SHA256 = (
    "3cfb18334b413a0ceaa307cdf328750f3fe3f7b5e2b88b6d4b5e1b178375fc25"
)
EXPECTED_FILE_COUNT = 249
EXPECTED_BYTES = 4_294_515_444
EXPECTED_SESSIONS = {
    "jm031": (
        "2023-10-18_a",
        "2023-10-19_a",
        "2023-10-20_a",
        "2023-10-21_a",
        "2023-10-22_a",
        "2023-10-23_a",
        "2023-10-24_a",
    ),
    "jm032": (
        "2023-10-18_a",
        "2023-10-19_a",
        "2023-10-20_a",
        "2023-10-21_a",
        "2023-10-22_a",
        "2023-10-23_a",
        "2023-10-24_a",
    ),
    "jm038": (
        "2023-04-30_a",
        "2023-05-01_a",
        "2023-05-02_a",
        "2023-05-03_a",
        "2023-05-04_a",
        "2023-05-05_a",
        "2023-05-06_a",
    ),
    "jm039": (
        "2024-04-30_a",
        "2024-05-01_a",
        "2024-05-02_a",
        "2024-05-03_a",
        "2024-05-04_a",
        "2024-05-05_a",
        "2024-05-06_a",
    ),
    "jm040": (
        "2024-05-01_a",
        "2024-05-02_a",
        "2024-05-03_a",
        "2024-05-04_a",
        "2024-05-05_a",
        "2024-05-06_a",
    ),
    "jm046": (
        "2024-09-03_a",
        "2024-09-04_a",
        "2024-09-05_a",
        "2024-09-06_a",
        "2024-09-07_a",
        "2024-09-08_a",
        "2024-09-09_a",
    ),
}
SELECTED_SUFFIXES = (
    "/move_deve/interframe_int.npy",
    "/move_deve/tstamps.npy",
    "/move_deve/motion_energy_glob.npy",
    "/suite2p/plane0/spks.npy",
    "/suite2p/plane0/stat.npy",
    "/suite2p/plane0/iscell.npy",
    "/ground_truth.csv",
)
BIN_FRAMES = 10
MIN_VALID_MOTION_FRACTION = 0.95
MIN_CELLS = 20
ROUNDING_TOLERANCE_FRAMES = 0.20
MAX_INTERVAL_MULTIPLIER = 2
MAX_MISSING_FRACTION = 0.05


class SourceError(RuntimeError):
    pass


class AlignmentError(RuntimeError):
    pass


class QualityError(RuntimeError):
    pass


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def crc32_and_size(path: Path) -> tuple[int, int]:
    checksum = 0
    size = 0
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            checksum = zlib.crc32(block, checksum)
            size += len(block)
    return checksum & 0xFFFFFFFF, size


def selected_manifest_entries(manifest: Path) -> dict[str, tuple[int, int]]:
    digest = sha256(manifest)
    if digest != EXPECTED_MANIFEST_SHA256:
        raise SourceError(
            f"manifest SHA-256 {digest} != {EXPECTED_MANIFEST_SHA256}"
        )
    payload = json.loads(manifest.read_text(encoding="utf-8"))
    entries = {
        str(entry["key"]): (int(entry["size"]), int(entry["crc"]))
        for entry in payload["entries"]
        if entry.get("size") is not None
        and any(str(entry["key"]).endswith(suffix) for suffix in SELECTED_SUFFIXES)
    }
    total_bytes = sum(size for size, _ in entries.values())
    if len(entries) != EXPECTED_FILE_COUNT or total_bytes != EXPECTED_BYTES:
        raise SourceError(
            f"manifest selection count/bytes {len(entries)}/{total_bytes} != "
            f"{EXPECTED_FILE_COUNT}/{EXPECTED_BYTES}"
        )
    return entries


def verify_source_layout(manifest: Path, root: Path) -> dict[str, object]:
    entries = selected_manifest_entries(manifest)
    actual = {
        str(path.relative_to(root)).replace("\\", "/"): path
        for path in root.rglob("*")
        if path.is_file()
    }
    expected_keys = set(entries)
    actual_keys = set(actual)
    if actual_keys != expected_keys:
        missing = sorted(expected_keys - actual_keys)
        extra = sorted(actual_keys - expected_keys)
        raise SourceError(f"selected file set differs: missing={missing}, extra={extra}")
    integrity_errors: list[str] = []
    for key in sorted(entries):
        expected_size, expected_crc32 = entries[key]
        actual_crc32, actual_size = crc32_and_size(actual[key])
        if actual_size != expected_size or actual_crc32 != expected_crc32:
            integrity_errors.append(
                f"{key}: size/crc32 {actual_size}/{actual_crc32} != "
                f"{expected_size}/{expected_crc32}"
            )
    if integrity_errors:
        raise SourceError(f"selected file integrity differs: {integrity_errors}")
    return {
        "manifest_sha256": EXPECTED_MANIFEST_SHA256,
        "files": len(entries),
        "bytes": sum(size for size, _ in entries.values()),
        "verification": "exact_member_set_size_and_provider_crc32",
    }


def restore_motion(
    session_root: Path, neural_frames: int
) -> tuple[np.ndarray, dict[str, object]]:
    move_root = session_root / "move_deve"
    motion = np.asarray(np.load(move_root / "motion_energy_glob.npy"), dtype=np.float64)
    timestamps = np.asarray(np.load(move_root / "tstamps.npy"), dtype=np.float64)
    interframe = np.asarray(np.load(move_root / "interframe_int.npy"), dtype=np.float64)
    if timestamps.shape != motion.shape:
        raise AlignmentError(f"timestamps {timestamps.shape} != motion {motion.shape}")
    if interframe.shape != (motion.size - 1,):
        raise AlignmentError(
            f"interframe {interframe.shape} != ({motion.size - 1},)"
        )
    differences = np.diff(timestamps)
    if not np.array_equal(interframe, differences):
        raise AlignmentError("interframe_int is not exactly diff(tstamps)")
    if not np.all(np.isfinite(timestamps)) or not np.all(interframe > 0):
        raise AlignmentError("timestamps are non-finite or not strictly increasing")

    median_interval = float(np.median(interframe))
    ratios = interframe / median_interval
    multipliers = np.rint(ratios).astype(np.int64)
    residual = float(np.max(np.abs(ratios - multipliers)))
    if np.any(multipliers < 1):
        raise AlignmentError("an interval rounded below one frame")
    if int(np.max(multipliers)) > MAX_INTERVAL_MULTIPLIER:
        raise AlignmentError("an interval multiplier exceeded two frames")
    if residual > ROUNDING_TOLERANCE_FRAMES:
        raise AlignmentError(f"rounding residual {residual} exceeded tolerance")

    positions = np.concatenate(
        (np.array([0], dtype=np.int64), np.cumsum(multipliers))
    )
    inferred_missing = int(np.sum(multipliers - 1))
    if inferred_missing != neural_frames - motion.size:
        raise AlignmentError(
            f"inferred missing {inferred_missing} != frame difference "
            f"{neural_frames - motion.size}"
        )
    if int(positions[-1]) != neural_frames - 1:
        raise AlignmentError(
            f"restored last position {positions[-1]} != {neural_frames - 1}"
        )
    missing_fraction = inferred_missing / neural_frames
    if missing_fraction > MAX_MISSING_FRACTION:
        raise AlignmentError(f"missing fraction {missing_fraction} exceeded gate")

    restored = np.full(neural_frames, np.nan, dtype=np.float64)
    restored[positions] = motion
    present = np.zeros(neural_frames, dtype=bool)
    present[positions] = True
    return restored, {
        "behavior_frames": int(motion.size),
        "inferred_missing": inferred_missing,
        "missing_positions": np.flatnonzero(~present).tolist(),
        "missing_fraction": missing_fraction,
        "max_rounding_residual_frames": residual,
    }


def endpoint_thirds(bin_count: int) -> tuple[slice, slice, slice]:
    if bin_count % 3:
        raise QualityError(f"bin count {bin_count} is not divisible by three")
    third = bin_count // 3
    return slice(0, third), slice(third, 2 * third), slice(2 * third, 3 * third)


def load_all_day_cell_rows(
    root: Path, subject: str
) -> tuple[np.ndarray, int, list[Path]]:
    expected = EXPECTED_SESSIONS[subject]
    actual = tuple(
        sorted(path.name for path in (root / subject).glob("20*") if path.is_dir())
    )
    if actual != expected:
        raise QualityError(f"sessions {actual} != expected {expected}")
    sessions = [root / subject / name for name in expected]
    masks: list[np.ndarray] = []
    cell_count: int | None = None
    for session in sessions:
        iscell = np.asarray(
            np.load(session / "suite2p" / "plane0" / "iscell.npy")
        )
        if iscell.ndim != 2 or iscell.shape[1] != 2:
            raise QualityError(f"{session.name}: invalid iscell shape {iscell.shape}")
        if cell_count is None:
            cell_count = int(iscell.shape[0])
        elif int(iscell.shape[0]) != cell_count:
            raise QualityError(f"{session.name}: cell row count changed")
        masks.append(iscell[:, 0] == 1)
    assert cell_count is not None
    rows = np.flatnonzero(np.logical_and.reduce(masks))
    if rows.size < MIN_CELLS:
        raise QualityError(f"all-day iscell intersection {rows.size} < {MIN_CELLS}")
    return rows, cell_count, sessions


def prepare_endpoint(
    session_root: Path, cell_rows: np.ndarray
) -> tuple[tuple[np.ndarray, np.ndarray], tuple[np.ndarray, np.ndarray], dict[str, object]]:
    spks = np.load(
        session_root / "suite2p" / "plane0" / "spks.npy", mmap_mode="r"
    )
    if spks.ndim != 2 or int(np.max(cell_rows)) >= spks.shape[0]:
        raise QualityError(f"invalid spks shape {spks.shape} for selected rows")
    neural_frames = int(spks.shape[1])
    if neural_frames % (BIN_FRAMES * 3):
        raise QualityError(
            f"neural frames {neural_frames} not divisible by {BIN_FRAMES * 3}"
        )
    motion, alignment = restore_motion(session_root, neural_frames)

    bin_count = neural_frames // BIN_FRAMES
    motion_windows = motion.reshape(bin_count, BIN_FRAMES)
    motion_counts = np.sum(np.isfinite(motion_windows), axis=1)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", category=RuntimeWarning)
        motion_binned = np.nanmedian(motion_windows, axis=1)
    motion_binned[motion_counts < 8] = np.nan

    activity_binned = np.empty((cell_rows.size, bin_count), dtype=np.float64)
    chunk_size = 64
    for start in range(0, cell_rows.size, chunk_size):
        stop = min(start + chunk_size, cell_rows.size)
        chunk = np.asarray(spks[cell_rows[start:stop]], dtype=np.float64)
        activity_binned[start:stop] = chunk.reshape(
            stop - start, bin_count, BIN_FRAMES
        ).mean(axis=2)

    first, guard, last = endpoint_thirds(bin_count)
    del guard
    activity_halves: list[np.ndarray] = []
    motion_halves: list[np.ndarray] = []
    valid_fractions: list[float] = []
    for selection in (first, last):
        selected_motion = motion_binned[selection]
        valid = np.isfinite(selected_motion)
        valid_fraction = float(np.mean(valid))
        if valid_fraction < MIN_VALID_MOTION_FRACTION:
            raise QualityError(
                f"valid motion fraction {valid_fraction} < "
                f"{MIN_VALID_MOTION_FRACTION}"
            )
        selected_motion = selected_motion[valid]
        if np.ptp(selected_motion) == 0:
            raise QualityError("motion is constant in an endpoint third")
        activity_halves.append(activity_binned[:, selection][:, valid])
        motion_halves.append(selected_motion)
        valid_fractions.append(valid_fraction)

    receipt = {
        "session": session_root.name,
        "neural_frames": neural_frames,
        "bin_count": bin_count,
        "analysis_bins_per_half_before_motion_QC": bin_count // 3,
        "guard_bins": bin_count // 3,
        "valid_motion_fraction_A": valid_fractions[0],
        "valid_motion_fraction_B": valid_fractions[1],
        "alignment": alignment,
    }
    return (
        (activity_halves[0], activity_halves[1]),
        (motion_halves[0], motion_halves[1]),
        receipt,
    )


def prepare_subject(
    root: Path, subject: str
) -> tuple[
    np.ndarray,
    list[tuple[tuple[np.ndarray, np.ndarray], tuple[np.ndarray, np.ndarray]]],
    dict[str, object],
]:
    cell_rows, tracked_rows, sessions = load_all_day_cell_rows(root, subject)
    endpoint_roots = (sessions[0], sessions[-1])
    prepared: list[
        tuple[tuple[np.ndarray, np.ndarray], tuple[np.ndarray, np.ndarray]]
    ] = []
    endpoint_receipts: list[dict[str, object]] = []
    valid_cells = np.ones(cell_rows.size, dtype=bool)
    frame_counts: list[int] = []
    for session in endpoint_roots:
        activities, motions, receipt = prepare_endpoint(session, cell_rows)
        prepared.append((activities, motions))
        endpoint_receipts.append(receipt)
        frame_counts.append(int(receipt["neural_frames"]))
        for activity in activities:
            valid_cells &= np.all(np.isfinite(activity), axis=1)
            valid_cells &= np.ptp(activity, axis=1) > 0
    if frame_counts[0] != frame_counts[1]:
        raise QualityError(f"first/last frame counts differ: {frame_counts}")
    if int(np.sum(valid_cells)) < MIN_CELLS:
        raise QualityError(
            f"valid four-half cells {int(np.sum(valid_cells))} < {MIN_CELLS}"
        )

    selected_rows = cell_rows[valid_cells]
    filtered = [
        (
            (activities[0][valid_cells], activities[1][valid_cells]),
            motions,
        )
        for activities, motions in prepared
    ]
    receipt = {
        "subject": subject,
        "sessions": list(EXPECTED_SESSIONS[subject]),
        "first_session": endpoint_roots[0].name,
        "last_session": endpoint_roots[1].name,
        "tracked_rows": tracked_rows,
        "iscell_all_days": int(cell_rows.size),
        "valid_four_half_cells": int(selected_rows.size),
        "endpoints": endpoint_receipts,
    }
    return selected_rows, filtered, receipt


def spearman_per_cell(activity: np.ndarray, motion: np.ndarray) -> np.ndarray:
    if activity.shape[1] != motion.size:
        raise ValueError("activity and motion lengths differ")
    motion_ranks = rankdata(motion, method="average")
    motion_centered = motion_ranks - np.mean(motion_ranks)
    motion_norm = float(np.sqrt(np.dot(motion_centered, motion_centered)))
    result = np.empty(activity.shape[0], dtype=np.float64)
    for index, values in enumerate(activity):
        activity_ranks = rankdata(values, method="average")
        activity_centered = activity_ranks - np.mean(activity_ranks)
        denominator = float(
            np.sqrt(np.dot(activity_centered, activity_centered)) * motion_norm
        )
        if denominator <= 0:
            raise QualityError("constant series reached Spearman endpoint")
        result[index] = float(
            np.dot(activity_centered, motion_centered) / denominator
        )
    return result


def coupling_metrics(betas: np.ndarray) -> dict[str, float]:
    if betas.ndim != 2 or betas.shape[1] != 4 or not np.all(np.isfinite(betas)):
        raise ValueError("betas must be a finite cells-by-four matrix")
    q_first = float(np.mean(betas[:, 0] * betas[:, 1]))
    q_last = float(np.mean(betas[:, 2] * betas[:, 3]))
    reorganization = float(
        np.mean((betas[:, 2] - betas[:, 0]) * (betas[:, 3] - betas[:, 1]))
    )
    return {
        "Q_first": q_first,
        "Q_last": q_last,
        "G_last_minus_first": q_last - q_first,
        "R_crossvalidated_reorganization_descriptive": reorganization,
    }


def exact_one_sided_sign_p(positive: int, total: int) -> float:
    return float(
        sum(math.comb(total, count) for count in range(positive, total + 1))
        / (2**total)
    )


def compute_subject(
    root: Path, subject: str
) -> dict[str, object]:
    selected_rows, prepared, receipt = prepare_subject(root, subject)
    columns: list[np.ndarray] = []
    for activities, motions in prepared:
        columns.append(spearman_per_cell(activities[0], motions[0]))
        columns.append(spearman_per_cell(activities[1], motions[1]))
    betas = np.column_stack(columns)
    return {
        **receipt,
        "provider_row_min": int(np.min(selected_rows)),
        "provider_row_max": int(np.max(selected_rows)),
        "metrics": coupling_metrics(betas),
    }


def runtime_receipt() -> dict[str, str]:
    return {
        "python_executable": str(Path(__import__("sys").executable).resolve()),
        "python": platform.python_version(),
        "numpy": np.__version__,
        "scipy": scipy.__version__,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--selected-root", type=Path, required=True)
    parser.add_argument("--mode", choices=("preflight", "endpoint"), required=True)
    args = parser.parse_args()
    manifest = args.manifest.resolve()
    root = args.selected_root.resolve()
    if root.name != "selected":
        raise ValueError(f"selected root must end with selected: {root}")

    try:
        source = verify_source_layout(manifest, root)
    except Exception as exc:
        receipt = {
            "decision": "D1_SOURCE_BLOCKED",
            "scope": "source_preflight_no_biological_endpoint",
            "error": f"{type(exc).__name__}: {exc}",
        }
        print(json.dumps(receipt, ensure_ascii=False, indent=2))
        return 1

    preflight: list[dict[str, object]] = []
    alignment_errors: list[str] = []
    quality_errors: list[str] = []
    for subject in EXPECTED_SESSIONS:
        try:
            _, _, subject_receipt = prepare_subject(root, subject)
            preflight.append(subject_receipt)
        except AlignmentError as exc:
            alignment_errors.append(f"{subject}: {exc}")
        except Exception as exc:
            quality_errors.append(f"{subject}: {type(exc).__name__}: {exc}")

    if alignment_errors or quality_errors:
        decision = (
            "D1_ALIGNMENT_BLOCKED" if alignment_errors else "D1_BLOCKED_QUALITY"
        )
        receipt = {
            "decision": decision,
            "scope": "all_mouse_preflight_no_correlation_endpoint",
            "source": source,
            "subjects_passed": preflight,
            "alignment_errors": alignment_errors,
            "quality_errors": quality_errors,
        }
        print(json.dumps(receipt, ensure_ascii=False, indent=2))
        return 1

    if args.mode == "preflight":
        receipt = {
            "decision": "D1_PREFLIGHT_PASS",
            "scope": "all_mouse_source_alignment_split_cell_QC_no_correlations",
            "source": source,
            "runtime": runtime_receipt(),
            "subjects": preflight,
        }
        print(json.dumps(receipt, ensure_ascii=False, indent=2))
        return 0

    subjects = [compute_subject(root, subject) for subject in EXPECTED_SESSIONS]
    effects = [
        float(subject["metrics"]["G_last_minus_first"])  # type: ignore[index]
        for subject in subjects
    ]
    positive = sum(effect > 0 for effect in effects)
    p_value = exact_one_sided_sign_p(positive, len(effects))
    decision = (
        "D1_STABLE_MOTION_COUPLING_INCREASE_SUPPORTED"
        if positive == len(EXPECTED_SESSIONS)
        else "D1_STABLE_MOTION_COUPLING_INCREASE_NOT_SUPPORTED"
    )
    receipt = {
        "decision": decision,
        "scope": (
            "observed_cross_third_activity_motion_coupling_score_not_meaning_"
            "synapses_speed_or_geometry"
        ),
        "source": source,
        "runtime": runtime_receipt(),
        "fixed_parameters": {
            "bin_frames": BIN_FRAMES,
            "split": "first_third_A_middle_third_guard_last_third_B",
            "minimum_valid_motion_fraction": MIN_VALID_MOTION_FRACTION,
            "minimum_cells": MIN_CELLS,
        },
        "subjects": subjects,
        "inference": {
            "unit": "mouse",
            "null": "population_median_G_less_than_or_equal_to_zero",
            "positive_G": positive,
            "total_mice": len(effects),
            "one_sided_exact_binomial_sign_p": p_value,
            "ties": "counted_nonpositive_without_reducing_n",
            "median_G": float(np.median(effects)),
            "min_G": float(np.min(effects)),
            "max_G": float(np.max(effects)),
        },
    }
    print(json.dumps(receipt, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
