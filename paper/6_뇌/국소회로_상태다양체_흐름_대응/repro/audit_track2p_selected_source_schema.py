from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path

import numpy as np


EXPECTED_SESSIONS = {
    "jm031": 7,
    "jm032": 7,
    "jm038": 7,
    "jm039": 7,
    "jm040": 6,
    "jm046": 7,
}


def npy_header(path: Path) -> tuple[tuple[int, ...], bool, np.dtype[object]]:
    with path.open("rb") as handle:
        version = np.lib.format.read_magic(handle)
        if version == (1, 0):
            shape, fortran_order, dtype = np.lib.format.read_array_header_1_0(handle)
        else:
            shape, fortran_order, dtype = np.lib.format.read_array_header_2_0(handle)
    return tuple(int(value) for value in shape), bool(fortran_order), dtype


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--selected-root", type=Path, required=True)
    args = parser.parse_args()
    root = args.selected_root.resolve()
    if root.name != "selected":
        raise ValueError(f"selected root must end with selected: {root}")

    errors: list[str] = []
    sessions: dict[str, list[dict[str, object]]] = defaultdict(list)
    for spks_path in sorted(root.glob("*/*/suite2p/plane0/spks.npy")):
        subject = spks_path.parts[-5]
        session = spks_path.parts[-4]
        session_root = spks_path.parents[2]
        paths = {
            "spks": spks_path,
            "stat": session_root / "suite2p" / "plane0" / "stat.npy",
            "iscell": session_root / "suite2p" / "plane0" / "iscell.npy",
            "motion": session_root / "move_deve" / "motion_energy_glob.npy",
            "timestamps": session_root / "move_deve" / "tstamps.npy",
            "interframe": session_root / "move_deve" / "interframe_int.npy",
        }
        missing = [str(path) for path in paths.values() if not path.is_file()]
        if missing:
            errors.append(f"{subject}/{session} missing: {missing}")
            continue
        shapes = {name: npy_header(path)[0] for name, path in paths.items()}
        if len(shapes["spks"]) != 2:
            errors.append(f"{subject}/{session} spks shape={shapes['spks']}")
            continue
        cells, neural_frames = shapes["spks"]
        if shapes["stat"] != (cells,):
            errors.append(
                f"{subject}/{session} stat={shapes['stat']} but cells={cells}"
            )
        if shapes["iscell"] != (cells, 2):
            errors.append(
                f"{subject}/{session} iscell={shapes['iscell']} but cells={cells}"
            )
        if len(shapes["motion"]) != 1 or shapes["timestamps"] != shapes["motion"]:
            errors.append(
                f"{subject}/{session} motion={shapes['motion']} "
                f"timestamps={shapes['timestamps']}"
            )
        if len(shapes["motion"]) == 1 and shapes["interframe"] != (
            shapes["motion"][0] - 1,
        ):
            errors.append(
                f"{subject}/{session} interframe={shapes['interframe']} "
                f"motion={shapes['motion']}"
            )
        sessions[subject].append(
            {
                "session": session,
                "cells": cells,
                "neural_frames": neural_frames,
                "behavior_frames": shapes["motion"][0],
                "frame_delta": shapes["motion"][0] - neural_frames,
            }
        )

    if set(sessions) != set(EXPECTED_SESSIONS):
        errors.append(
            f"subjects: expected={sorted(EXPECTED_SESSIONS)}, actual={sorted(sessions)}"
        )
    subject_summary: dict[str, dict[str, object]] = {}
    for subject, expected_count in EXPECTED_SESSIONS.items():
        subject_sessions = sorted(sessions.get(subject, []), key=lambda item: item["session"])
        if len(subject_sessions) != expected_count:
            errors.append(
                f"{subject} sessions: expected={expected_count}, actual={len(subject_sessions)}"
            )
        cell_counts = {int(item["cells"]) for item in subject_sessions}
        if len(cell_counts) != 1:
            errors.append(f"{subject} cross-day cell rows differ: {sorted(cell_counts)}")
        subject_summary[subject] = {
            "sessions": len(subject_sessions),
            "session_ids": [item["session"] for item in subject_sessions],
            "tracked_cells": next(iter(cell_counts)) if len(cell_counts) == 1 else None,
            "neural_frames": {
                "min": min((int(item["neural_frames"]) for item in subject_sessions), default=0),
                "max": max((int(item["neural_frames"]) for item in subject_sessions), default=0),
            },
            "frame_deltas": sorted({int(item["frame_delta"]) for item in subject_sessions}),
        }

    ground_truth = sorted(
        str(path.relative_to(root)).replace("\\", "/")
        for path in root.glob("*/ground_truth.csv")
    )
    if len(ground_truth) != 3:
        errors.append(f"ground truth files: expected=3, actual={len(ground_truth)}")

    receipt = {
        "decision": (
            "TRACK2P_SELECTED_SOURCE_SCHEMA_PASS"
            if not errors
            else "TRACK2P_SELECTED_SOURCE_SCHEMA_FAIL"
        ),
        "scope": "source_and_shape_only_no_biological_endpoint",
        "subjects": subject_summary,
        "session_count": sum(len(value) for value in sessions.values()),
        "ground_truth_files": ground_truth,
        "errors": errors,
    }
    print(json.dumps(receipt, ensure_ascii=False, indent=2))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
