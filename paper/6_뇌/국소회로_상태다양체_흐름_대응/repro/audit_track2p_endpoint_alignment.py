from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np


SUBJECTS = ("jm031", "jm032", "jm038", "jm039", "jm040", "jm046")
ROUNDING_TOLERANCE_FRAMES = 0.20
MAX_INTERVAL_MULTIPLIER = 2
MAX_MISSING_FRACTION = 0.05


def inspect_endpoint(session_root: Path) -> tuple[dict[str, object], list[str]]:
    errors: list[str] = []
    spks_path = session_root / "suite2p" / "plane0" / "spks.npy"
    motion_path = session_root / "move_deve" / "motion_energy_glob.npy"
    timestamps_path = session_root / "move_deve" / "tstamps.npy"
    interframe_path = session_root / "move_deve" / "interframe_int.npy"

    spks = np.load(spks_path, mmap_mode="r")
    motion = np.load(motion_path, mmap_mode="r")
    timestamps = np.asarray(np.load(timestamps_path), dtype=np.float64)
    interframe = np.asarray(np.load(interframe_path), dtype=np.float64)
    neural_frames = int(spks.shape[1])
    behavior_frames = int(motion.shape[0])

    if timestamps.shape != (behavior_frames,):
        errors.append(
            f"timestamps shape {timestamps.shape} != ({behavior_frames},)"
        )
    if interframe.shape != (max(behavior_frames - 1, 0),):
        errors.append(
            f"interframe shape {interframe.shape} != ({behavior_frames - 1},)"
        )
    if behavior_frames < 2:
        errors.append("fewer than two behavior frames")

    missing_positions: list[int] = []
    residual = float("nan")
    median_interval = float("nan")
    max_multiplier = 0
    inferred_missing = -1
    restored_last_position = -1
    if not errors:
        differences = np.diff(timestamps)
        if not np.all(np.isfinite(timestamps)):
            errors.append("timestamps contain non-finite values")
        if not np.all(np.isfinite(interframe)):
            errors.append("interframe intervals contain non-finite values")
        if not np.all(differences > 0):
            errors.append("timestamps are not strictly increasing")
        if not np.array_equal(differences, interframe):
            errors.append("interframe_int is not exactly diff(tstamps)")

        median_interval = float(np.median(interframe))
        if not np.isfinite(median_interval) or median_interval <= 0:
            errors.append(f"invalid median interval {median_interval}")
        else:
            ratios = interframe / median_interval
            multipliers = np.rint(ratios).astype(np.int64)
            residual = float(np.max(np.abs(ratios - multipliers)))
            max_multiplier = int(np.max(multipliers))
            inferred_missing = int(np.sum(multipliers - 1))
            positions = np.concatenate(
                (np.array([0], dtype=np.int64), np.cumsum(multipliers))
            )
            restored_last_position = int(positions[-1])
            for index, multiplier in enumerate(multipliers):
                if multiplier > 1:
                    missing_positions.extend(
                        range(int(positions[index] + 1), int(positions[index + 1]))
                    )

            if np.any(multipliers < 1):
                errors.append("an interval rounded below one frame")
            if max_multiplier > MAX_INTERVAL_MULTIPLIER:
                errors.append(
                    f"interval multiplier {max_multiplier} exceeds "
                    f"{MAX_INTERVAL_MULTIPLIER}"
                )
            if residual > ROUNDING_TOLERANCE_FRAMES:
                errors.append(
                    f"rounding residual {residual} exceeds "
                    f"{ROUNDING_TOLERANCE_FRAMES} frame"
                )
            if inferred_missing != neural_frames - behavior_frames:
                errors.append(
                    f"inferred missing {inferred_missing} != neural-behavior "
                    f"difference {neural_frames - behavior_frames}"
                )
            if restored_last_position != neural_frames - 1:
                errors.append(
                    f"restored last position {restored_last_position} != "
                    f"{neural_frames - 1}"
                )

    missing_fraction = (neural_frames - behavior_frames) / neural_frames
    if missing_fraction < 0 or missing_fraction > MAX_MISSING_FRACTION:
        errors.append(
            f"missing fraction {missing_fraction} outside "
            f"[0, {MAX_MISSING_FRACTION}]"
        )

    return (
        {
            "session": str(session_root),
            "neural_frames": neural_frames,
            "behavior_frames": behavior_frames,
            "inferred_missing": inferred_missing,
            "missing_positions": missing_positions,
            "missing_fraction": missing_fraction,
            "median_timestamp_interval": median_interval,
            "max_interval_multiplier": max_multiplier,
            "max_rounding_residual_frames": residual,
            "restored_last_position": restored_last_position,
        },
        errors,
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--selected-root", type=Path, required=True)
    args = parser.parse_args()
    root = args.selected_root.resolve()
    if root.name != "selected":
        raise ValueError(f"selected root must end with selected: {root}")

    endpoints: list[dict[str, object]] = []
    errors: list[str] = []
    for subject in SUBJECTS:
        sessions = sorted(path for path in (root / subject).glob("20*") if path.is_dir())
        if len(sessions) < 2:
            errors.append(f"{subject}: fewer than two sessions")
            continue
        for endpoint_name, session_root in (
            ("first", sessions[0]),
            ("last", sessions[-1]),
        ):
            result, endpoint_errors = inspect_endpoint(session_root)
            result["subject"] = subject
            result["endpoint"] = endpoint_name
            result["session"] = session_root.name
            endpoints.append(result)
            errors.extend(
                f"{subject}/{session_root.name}: {message}"
                for message in endpoint_errors
            )

    receipt = {
        "decision": (
            "TRACK2P_ENDPOINT_ALIGNMENT_PASS"
            if not errors and len(endpoints) == 2 * len(SUBJECTS)
            else "D1_ALIGNMENT_BLOCKED"
        ),
        "scope": "first_last_alignment_only_no_biological_endpoint",
        "rules": {
            "rounding_tolerance_frames": ROUNDING_TOLERANCE_FRAMES,
            "max_interval_multiplier": MAX_INTERVAL_MULTIPLIER,
            "max_missing_fraction": MAX_MISSING_FRACTION,
            "fill": "NaN_no_interpolation",
        },
        "endpoints": endpoints,
        "errors": errors,
    }
    print(json.dumps(receipt, ensure_ascii=False, indent=2))
    return 0 if receipt["decision"] == "TRACK2P_ENDPOINT_ALIGNMENT_PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
