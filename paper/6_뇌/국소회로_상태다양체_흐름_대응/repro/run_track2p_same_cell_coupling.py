from __future__ import annotations

import argparse
import json
import math
import platform
from pathlib import Path

import numpy as np
import scipy
from scipy.stats import kendalltau, rankdata


SUBJECTS = ("jm031", "jm032", "jm038", "jm039", "jm040", "jm046")
BIN_FRAMES = 10
BLOCK_BINS = 60
MIN_BLOCKS_PER_HALF = 20
MIN_VALID_MOTION_FRACTION = 0.95
MIN_CELLS = 20
ROUNDING_TOLERANCE_FRAMES = 0.20
MAX_INTERVAL_MULTIPLIER = 2
MAX_MISSING_FRACTION = 0.05


def restore_motion(session_root: Path, neural_frames: int) -> tuple[np.ndarray, dict[str, object]]:
    move_root = session_root / "move_deve"
    motion = np.asarray(np.load(move_root / "motion_energy_glob.npy"), dtype=np.float64)
    timestamps = np.asarray(np.load(move_root / "tstamps.npy"), dtype=np.float64)
    interframe = np.asarray(np.load(move_root / "interframe_int.npy"), dtype=np.float64)
    if timestamps.shape != motion.shape:
        raise ValueError(f"timestamps {timestamps.shape} != motion {motion.shape}")
    if interframe.shape != (motion.size - 1,):
        raise ValueError(
            f"interframe {interframe.shape} != ({motion.size - 1},)"
        )
    differences = np.diff(timestamps)
    if not np.array_equal(interframe, differences):
        raise ValueError("interframe_int is not exactly diff(tstamps)")
    if not np.all(np.isfinite(timestamps)) or not np.all(interframe > 0):
        raise ValueError("timestamps are non-finite or not strictly increasing")

    median_interval = float(np.median(interframe))
    ratios = interframe / median_interval
    multipliers = np.rint(ratios).astype(np.int64)
    residual = float(np.max(np.abs(ratios - multipliers)))
    if np.any(multipliers < 1):
        raise ValueError("an interval rounded below one frame")
    if int(np.max(multipliers)) > MAX_INTERVAL_MULTIPLIER:
        raise ValueError("an interval multiplier exceeded two frames")
    if residual > ROUNDING_TOLERANCE_FRAMES:
        raise ValueError(f"rounding residual {residual} exceeded tolerance")

    positions = np.concatenate(
        (np.array([0], dtype=np.int64), np.cumsum(multipliers))
    )
    inferred_missing = int(np.sum(multipliers - 1))
    if inferred_missing != neural_frames - motion.size:
        raise ValueError(
            f"inferred missing {inferred_missing} != frame difference "
            f"{neural_frames - motion.size}"
        )
    if int(positions[-1]) != neural_frames - 1:
        raise ValueError(
            f"restored last position {positions[-1]} != {neural_frames - 1}"
        )
    missing_fraction = inferred_missing / neural_frames
    if missing_fraction > MAX_MISSING_FRACTION:
        raise ValueError(f"missing fraction {missing_fraction} exceeded gate")

    restored = np.full(neural_frames, np.nan, dtype=np.float64)
    restored[positions] = motion
    missing_positions = np.flatnonzero(~np.isfinite(restored)).tolist()
    return restored, {
        "behavior_frames": int(motion.size),
        "inferred_missing": inferred_missing,
        "missing_positions": missing_positions,
        "missing_fraction": missing_fraction,
        "max_rounding_residual_frames": residual,
    }


def binned_endpoint(
    session_root: Path, cell_rows: np.ndarray
) -> tuple[np.ndarray, np.ndarray, dict[str, object]]:
    spks = np.load(
        session_root / "suite2p" / "plane0" / "spks.npy", mmap_mode="r"
    )
    neural_frames = int(spks.shape[1])
    motion, alignment = restore_motion(session_root, neural_frames)

    bin_count = neural_frames // BIN_FRAMES
    trim_frames = bin_count * BIN_FRAMES
    motion_windows = motion[:trim_frames].reshape(bin_count, BIN_FRAMES)
    motion_counts = np.sum(np.isfinite(motion_windows), axis=1)
    with np.errstate(all="ignore"):
        motion_binned = np.nanmedian(motion_windows, axis=1)
    motion_binned[motion_counts < 8] = np.nan

    activity_binned = np.empty((cell_rows.size, bin_count), dtype=np.float64)
    chunk_size = 64
    for start in range(0, cell_rows.size, chunk_size):
        stop = min(start + chunk_size, cell_rows.size)
        chunk = np.asarray(
            spks[cell_rows[start:stop], :trim_frames], dtype=np.float64
        )
        activity_binned[start:stop] = chunk.reshape(
            stop - start, bin_count, BIN_FRAMES
        ).mean(axis=2)

    block_count = bin_count // BLOCK_BINS
    if block_count % 2:
        block_count -= 1
    kept_bins = block_count * BLOCK_BINS
    if block_count // 2 < MIN_BLOCKS_PER_HALF:
        raise ValueError(
            f"only {block_count // 2} blocks per half; need "
            f"{MIN_BLOCKS_PER_HALF}"
        )
    activity_binned = activity_binned[:, :kept_bins]
    motion_binned = motion_binned[:kept_bins]
    block_ids = np.arange(kept_bins) // BLOCK_BINS
    half_masks = np.vstack((block_ids % 2 == 0, block_ids % 2 == 1))

    valid_rates: list[float] = []
    masks: list[np.ndarray] = []
    for half_mask in half_masks:
        assigned = int(np.sum(half_mask))
        mask = half_mask & np.isfinite(motion_binned)
        valid_rate = float(np.sum(mask) / assigned)
        if valid_rate < MIN_VALID_MOTION_FRACTION:
            raise ValueError(
                f"valid motion rate {valid_rate} below "
                f"{MIN_VALID_MOTION_FRACTION}"
            )
        if np.ptp(motion_binned[mask]) == 0:
            raise ValueError("motion is constant in a half")
        valid_rates.append(valid_rate)
        masks.append(mask)

    return activity_binned, motion_binned, {
        "neural_frames": neural_frames,
        "bin_count": bin_count,
        "complete_even_blocks": block_count,
        "blocks_per_half": block_count // 2,
        "valid_motion_fraction_A": valid_rates[0],
        "valid_motion_fraction_B": valid_rates[1],
        "mask_A": masks[0],
        "mask_B": masks[1],
        "alignment": alignment,
    }


def spearman_per_cell(activity: np.ndarray, motion: np.ndarray) -> np.ndarray:
    if activity.shape[1] != motion.size:
        raise ValueError("activity and motion lengths differ")
    result = np.full(activity.shape[0], np.nan, dtype=np.float64)
    motion_ranks = rankdata(motion, method="average")
    motion_centered = motion_ranks - np.mean(motion_ranks)
    motion_norm = float(np.sqrt(np.dot(motion_centered, motion_centered)))
    for index, values in enumerate(activity):
        if not np.all(np.isfinite(values)) or np.ptp(values) == 0:
            continue
        activity_ranks = rankdata(values, method="average")
        activity_centered = activity_ranks - np.mean(activity_ranks)
        denominator = float(
            np.sqrt(np.dot(activity_centered, activity_centered)) * motion_norm
        )
        if denominator > 0:
            result[index] = float(
                np.dot(activity_centered, motion_centered) / denominator
            )
    return result


def kendall_per_cell(activity: np.ndarray, motion: np.ndarray) -> np.ndarray:
    result = np.full(activity.shape[0], np.nan, dtype=np.float64)
    for index, values in enumerate(activity):
        if not np.all(np.isfinite(values)) or np.ptp(values) == 0:
            continue
        statistic = kendalltau(values, motion, variant="b").statistic
        if np.isfinite(statistic):
            result[index] = float(statistic)
    return result


def effect_from_betas(betas: np.ndarray, selector: np.ndarray | None = None) -> dict[str, float]:
    chosen = betas if selector is None else betas[selector]
    if chosen.shape[0] == 0 or not np.all(np.isfinite(chosen)):
        raise ValueError("effect received empty or non-finite beta matrix")
    cross = [
        float(np.median(np.abs(chosen[:, first] - chosen[:, last])))
        for first in (0, 1)
        for last in (2, 3)
    ]
    day_change = float(np.mean(cross))
    split_noise = float(
        0.5
        * (
            np.median(np.abs(chosen[:, 0] - chosen[:, 1]))
            + np.median(np.abs(chosen[:, 2] - chosen[:, 3]))
        )
    )
    return {
        "D_day_change": day_change,
        "N_split_half_noise": split_noise,
        "E_change_minus_noise": day_change - split_noise,
    }


def exact_one_sided_sign_p(positive: int, total: int) -> float:
    return float(
        sum(math.comb(total, count) for count in range(positive, total + 1))
        / (2**total)
    )


def analyze_subject(root: Path, subject: str) -> tuple[dict[str, object], list[str]]:
    errors: list[str] = []
    sessions = sorted(path for path in (root / subject).glob("20*") if path.is_dir())
    first = sessions[0]
    last = sessions[-1]

    iscell_masks: list[np.ndarray] = []
    cell_count: int | None = None
    for session in sessions:
        iscell = np.asarray(
            np.load(session / "suite2p" / "plane0" / "iscell.npy")
        )
        if iscell.ndim != 2 or iscell.shape[1] != 2:
            errors.append(f"{session.name}: invalid iscell shape {iscell.shape}")
            continue
        if cell_count is None:
            cell_count = int(iscell.shape[0])
        elif int(iscell.shape[0]) != cell_count:
            errors.append(f"{session.name}: cell row count changed")
        iscell_masks.append(iscell[:, 0] == 1)
    if errors or cell_count is None or len(iscell_masks) != len(sessions):
        return {"subject": subject}, errors or ["iscell preflight failed"]

    intersection = np.logical_and.reduce(iscell_masks)
    cell_rows = np.flatnonzero(intersection)
    if cell_rows.size < MIN_CELLS:
        return {
            "subject": subject,
            "tracked_rows": cell_count,
            "iscell_all_days": int(cell_rows.size),
        }, [f"all-day iscell intersection {cell_rows.size} < {MIN_CELLS}"]

    endpoint_data: list[tuple[np.ndarray, np.ndarray, dict[str, object]]] = []
    for session in (first, last):
        try:
            endpoint_data.append(binned_endpoint(session, cell_rows))
        except Exception as exc:  # result is an explicit quality block
            errors.append(f"{session.name}: {type(exc).__name__}: {exc}")
    if errors:
        return {
            "subject": subject,
            "first_session": first.name,
            "last_session": last.name,
            "tracked_rows": cell_count,
            "iscell_all_days": int(cell_rows.size),
        }, errors

    beta_columns: list[np.ndarray] = []
    kendall_columns: list[np.ndarray] = []
    endpoint_receipts: list[dict[str, object]] = []
    for session, (activity, motion, receipt) in zip((first, last), endpoint_data):
        masks = (receipt.pop("mask_A"), receipt.pop("mask_B"))
        for mask in masks:
            beta_columns.append(spearman_per_cell(activity[:, mask], motion[mask]))
            kendall_columns.append(kendall_per_cell(activity[:, mask], motion[mask]))
        endpoint_receipts.append({"session": session.name, **receipt})

    betas_all = np.column_stack(beta_columns)
    valid = np.all(np.isfinite(betas_all), axis=1)
    betas = betas_all[valid]
    valid_rows = cell_rows[valid]
    if betas.shape[0] < MIN_CELLS:
        errors.append(f"valid endpoint cells {betas.shape[0]} < {MIN_CELLS}")
        return {
            "subject": subject,
            "first_session": first.name,
            "last_session": last.name,
            "tracked_rows": cell_count,
            "iscell_all_days": int(cell_rows.size),
            "valid_endpoint_cells": int(betas.shape[0]),
            "endpoints": endpoint_receipts,
        }, errors

    kendall_all = np.column_stack(kendall_columns)
    if not np.all(np.isfinite(kendall_all[valid])):
        errors.append("Kendall robustness missing for a primary-valid cell")
        return {"subject": subject}, errors

    primary = effect_from_betas(betas)
    kendall_effect = effect_from_betas(kendall_all[valid])
    parity: dict[str, dict[str, float] | None] = {}
    for name, remainder in (("even_provider_rows", 0), ("odd_provider_rows", 1)):
        selector = valid_rows % 2 == remainder
        parity[name] = (
            effect_from_betas(betas, selector) if int(np.sum(selector)) >= 10 else None
        )

    return {
        "subject": subject,
        "first_session": first.name,
        "last_session": last.name,
        "tracked_rows": cell_count,
        "iscell_all_days": int(cell_rows.size),
        "valid_endpoint_cells": int(betas.shape[0]),
        "endpoints": endpoint_receipts,
        "median_beta_F_A": float(np.median(betas[:, 0])),
        "median_beta_F_B": float(np.median(betas[:, 1])),
        "median_beta_L_A": float(np.median(betas[:, 2])),
        "median_beta_L_B": float(np.median(betas[:, 3])),
        "primary": primary,
        "robustness": {
            "kendall_tau_b": kendall_effect,
            "provider_row_parity": parity,
        },
    }, errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--selected-root", type=Path, required=True)
    args = parser.parse_args()
    root = args.selected_root.resolve()
    if root.name != "selected":
        raise ValueError(f"selected root must end with selected: {root}")

    subjects: list[dict[str, object]] = []
    errors: list[str] = []
    for subject in SUBJECTS:
        result, subject_errors = analyze_subject(root, subject)
        subjects.append(result)
        errors.extend(f"{subject}: {message}" for message in subject_errors)

    quality_pass = not errors and len(subjects) == len(SUBJECTS)
    positive = 0
    p_value: float | None = None
    leave_one_out_positive: list[int] = []
    if quality_pass:
        effects = [
            float(subject["primary"]["E_change_minus_noise"])  # type: ignore[index]
            for subject in subjects
        ]
        positive = sum(effect > 0 for effect in effects)
        p_value = exact_one_sided_sign_p(positive, len(effects))
        leave_one_out_positive = [
            sum(value > 0 for index, value in enumerate(effects) if index != omitted)
            for omitted in range(len(effects))
        ]
        decision = (
            "D1_SAME_CELL_COUPLING_CHANGE_SUPPORTED"
            if positive == len(SUBJECTS)
            else "D1_SAME_CELL_COUPLING_CHANGE_NOT_SUPPORTED"
        )
    else:
        decision = "D1_BLOCKED_QUALITY"

    receipt = {
        "decision": decision,
        "scope": "same_tracked_rows_activity_motion_coupling_not_meaning_or_synapses",
        "source_manifest_sha256": (
            "3cfb18334b413a0ceaa307cdf328750f3fe3f7b5e2b88b6d4b5e1b178375fc25"
        ),
        "runtime": {
            "python": platform.python_version(),
            "numpy": np.__version__,
            "scipy": scipy.__version__,
        },
        "fixed_parameters": {
            "bin_frames": BIN_FRAMES,
            "block_bins": BLOCK_BINS,
            "minimum_blocks_per_half": MIN_BLOCKS_PER_HALF,
            "minimum_valid_motion_fraction": MIN_VALID_MOTION_FRACTION,
            "minimum_cells": MIN_CELLS,
        },
        "subjects": subjects,
        "inference": {
            "unit": "mouse",
            "positive_E": positive if quality_pass else None,
            "total_mice": len(SUBJECTS),
            "one_sided_exact_binomial_sign_p": p_value,
            "leave_one_mouse_out_positive_of_five": leave_one_out_positive,
        },
        "errors": errors,
    }
    print(json.dumps(receipt, ensure_ascii=False, indent=2))
    return 0 if quality_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
