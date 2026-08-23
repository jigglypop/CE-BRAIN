"""Read-only BA-SRM6 source, MAT-schema, clock, and split audit.

This script never fits or scores a neural/behavior model.  It emits an immutable
input receipt to stdout after checking the source-locked archives and selectively
extracted ``heatDataMS.mat`` files.
"""

from __future__ import annotations

import hashlib
import json
import math
import argparse
from pathlib import Path
from typing import Any

import numpy as np
from scipy.io import loadmat


WINDOW = 60
HORIZON = 6
LEADING_GUARD = 12
EMBARGO = 12
GAP_FACTOR = 3.0

EXPECTED_ARCHIVES = {
    "AML310_moving.tar.gz": (
        348_444_164,
        "144126ee9a49d311c3393deea434e1a0963d55de35318e25d98d48f9c175250a",
    ),
    "AML32_moving.tar.gz": (
        1_218_075_251,
        "6b71a6ba1a5d2f1ef3bf9661e845e1e52634bae217fc0c2630a83fca07daed63",
    ),
    "AML18_moving.tar.gz": (
        1_409_801_111,
        "588d7666f4e8afebad1ab9b8483244a6de0303251d862425522c2b8dd78bbd82",
    ),
}

ROOT_SPECS = {
    "AKS297.51_moving": ("gcamp", "AKS297.51_moving_datasets.txt"),
    "AML32_moving": ("gcamp", "AML32_moving_datasets.txt"),
    "AML18_moving": ("gfp", "AML18_moving_datasets.txt"),
}

GCAMP_ROLES = {
    "BrainScanner20200130_105254": "train",
    "BrainScanner20200130_110803": "train",
    "BrainScanner20170424_105620": "train",
    "BrainScanner20170610_105634": "train",
    "BrainScanner20170613_134800": "train",
    "BrainScanner20180709_100433": "train",
    "BrainScanner20200309_151024": "train",
    "BrainScanner20200310_141211": "validation",
    "BrainScanner20200309_153839": "validation",
    "BrainScanner20200310_142022": "held_out",
    "BrainScanner20200309_162140": "held_out",
}

GFP_IDS = (
    "BrainScanner20200116_145254",
    "BrainScanner20200116_152636",
    "BrainScanner20200204_102136",
    "BrainScanner20200310_153952",
    "BrainScanner20200311_100140",
    "BrainScanner20200929_140030",
    "BrainScanner20200929_143439",
    "BrainScanner20210503_122703",
    "BrainScanner20210503_135244",
    "BrainScanner20210503_151831",
    "BrainScanner20210503_154404",
)
GFP_ROLES = {
    recording_id: (
        "train" if index < 7 else "validation" if index < 9 else "held_out"
    )
    for index, recording_id in enumerate(GFP_IDS)
}

EXCLUDED_INTERVALS = {
    "BrainScanner20200130_105254": ((65.0, 75.0),),
    "BrainScanner20200310_141211": ((200.0, 210.0), (240.0, 250.0)),
    "BrainScanner20200309_151024": ((30.0, 40.0), (125.0, 135.0)),
    "BrainScanner20200309_153839": ((35.0, 45.0), (160.0, 170.0)),
    "BrainScanner20200309_162140": ((0.0, 10.0), (300.0, 310.0)),
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def parse_log(path: Path) -> list[tuple[str, int | None]]:
    rows: list[tuple[str, int | None]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        fields = stripped.split()
        rows.append((fields[0], int(fields[1]) if len(fields) > 1 else None))
    return rows


def split_anchor_counts(time: np.ndarray, recording_id: str) -> dict[str, int]:
    total = int(time.size)
    train_end = int(math.floor(0.6 * total))
    validation_end = int(math.floor(0.8 * total))
    positive = np.diff(time)
    positive = positive[np.isfinite(positive) & (positive > 0.0)]
    if not positive.size:
        return {"train": 0, "validation": 0, "test": 0}
    max_gap = float(GAP_FACTOR * np.median(positive))
    excluded = EXCLUDED_INTERVALS.get(recording_id, ())
    counts = {"train": 0, "validation": 0, "test": 0}
    for anchor in range(WINDOW - 1, total - HORIZON):
        start = anchor - WINDOW + 1
        stop = anchor + HORIZON
        if start < LEADING_GUARD:
            continue
        local_steps = np.diff(time[start : stop + 1])
        if not np.all(
            np.isfinite(local_steps)
            & (local_steps > 0.0)
            & (local_steps <= max_gap)
        ):
            continue
        local_time = time[start : stop + 1]
        if any(np.any((local_time >= left) & (local_time <= right)) for left, right in excluded):
            continue
        if stop < train_end - EMBARGO:
            counts["train"] += 1
        elif start >= train_end + EMBARGO and stop < validation_end - EMBARGO:
            counts["validation"] += 1
        elif start >= validation_end + EMBARGO:
            counts["test"] += 1
    return counts


def audit_recording(
    mat_path: Path,
    recording_id: str,
    cut_volume: int | None,
    signal_class: str,
    role: str,
) -> dict[str, Any]:
    data = loadmat(
        mat_path,
        variable_names=("Ratio2", "R2", "hasPointsTime", "behavior"),
        simplify_cells=True,
    )
    required = ("Ratio2", "R2", "hasPointsTime", "behavior")
    missing = [field for field in required if field not in data]
    if missing:
        return {
            "recording_id": recording_id,
            "signal_class": signal_class,
            "outer_role": role,
            "schema_passed": False,
            "missing": missing,
        }
    ratio = np.asarray(data["Ratio2"], dtype=float)
    red = np.asarray(data["R2"], dtype=float)
    time = np.asarray(data["hasPointsTime"], dtype=float).reshape(-1)
    behavior = data["behavior"]
    behavior_fields = ("v", "pc1_2")
    missing_behavior = [field for field in behavior_fields if field not in behavior]
    if missing_behavior:
        return {
            "recording_id": recording_id,
            "signal_class": signal_class,
            "outer_role": role,
            "schema_passed": False,
            "missing_behavior": missing_behavior,
        }
    velocity = np.asarray(behavior["v"], dtype=float).reshape(-1)
    posture = np.asarray(behavior["pc1_2"], dtype=float)
    full_t = int(time.size)
    stop = full_t if cut_volume is None else min(full_t, int(cut_volume) + 1)
    ratio = ratio[:, :stop]
    red = red[:, :stop]
    time = time[:stop]
    velocity = velocity[:stop]
    posture = posture[:stop]
    shape_passed = bool(
        ratio.ndim == 2
        and red.shape == ratio.shape
        and ratio.shape[1] == stop
        and velocity.shape == (stop,)
        and posture.shape == (stop, 2)
    )
    positive_steps = np.diff(time)
    positive_only = positive_steps[
        np.isfinite(positive_steps) & (positive_steps > 0.0)
    ]
    train_end = int(math.floor(0.6 * stop))
    ratio_train = ratio[:, :train_end]
    red_train = red[:, :train_end]
    ratio_kept = np.mean(np.isfinite(ratio_train), axis=1) >= 0.75
    red_kept = np.mean(np.isfinite(red_train), axis=1) >= 0.75
    ratio_variance = np.nanstd(ratio_train, axis=1) > 1e-12
    red_variance = np.nanstd(red_train, axis=1) > 1e-12
    counts = split_anchor_counts(time, recording_id)
    return {
        "recording_id": recording_id,
        "signal_class": signal_class,
        "outer_role": role,
        "cut_volume": cut_volume,
        "full_timepoints": full_t,
        "usable_timepoints": stop,
        "ratio2_shape": list(ratio.shape),
        "r2_shape": list(red.shape),
        "clock_shape": list(time.shape),
        "velocity_shape": list(velocity.shape),
        "posture_shape": list(posture.shape),
        "schema_passed": shape_passed,
        "median_positive_dt": (
            float(np.median(positive_only)) if positive_only.size else None
        ),
        "nonpositive_clock_steps": int(np.sum(~np.isfinite(positive_steps) | (positive_steps <= 0.0))),
        "long_clock_gaps": (
            int(np.sum(positive_steps > GAP_FACTOR * np.median(positive_only)))
            if positive_only.size
            else None
        ),
        "finite_velocity_fraction": float(np.mean(np.isfinite(velocity))),
        "finite_posture_fraction": float(np.mean(np.isfinite(posture))),
        "ratio2_prefix_finite_fraction_median": float(
            np.median(np.mean(np.isfinite(ratio_train), axis=1))
        ),
        "ratio2_prefix_finite_fraction_max": float(
            np.max(np.mean(np.isfinite(ratio_train), axis=1))
        ),
        "r2_prefix_finite_fraction_median": float(
            np.median(np.mean(np.isfinite(red_train), axis=1))
        ),
        "r2_prefix_finite_fraction_max": float(
            np.max(np.mean(np.isfinite(red_train), axis=1))
        ),
        "ratio2_units_passing_prefix_rule": int(np.sum(ratio_kept & ratio_variance)),
        "r2_units_passing_prefix_rule": int(np.sum(red_kept & red_variance)),
        "clock_only_anchor_counts": counts,
        "excluded_intervals": [list(interval) for interval in EXCLUDED_INTERVALS.get(recording_id, ())],
        "mat_sha256": sha256_file(mat_path),
        "mat_bytes": mat_path.stat().st_size,
    }


def build_receipt(repository: Path) -> dict[str, Any]:
    data_root = repository / "data" / "external" / "ba_srm6"
    extracted = data_root / "extracted"
    archive_rows: list[dict[str, Any]] = []
    archive_passed = True
    for name, (expected_bytes, expected_hash) in EXPECTED_ARCHIVES.items():
        path = data_root / name
        observed_hash = sha256_file(path)
        passed = bool(path.stat().st_size == expected_bytes and observed_hash == expected_hash)
        archive_passed &= passed
        archive_rows.append(
            {
                "name": name,
                "bytes": path.stat().st_size,
                "expected_bytes": expected_bytes,
                "sha256": observed_hash,
                "expected_sha256": expected_hash,
                "passed": passed,
            }
        )

    recordings: list[dict[str, Any]] = []
    for root_name, (signal_class, log_name) in ROOT_SPECS.items():
        root = extracted / root_name
        for recording_id, cut_volume in parse_log(root / log_name):
            roles = GCAMP_ROLES if signal_class == "gcamp" else GFP_ROLES
            recordings.append(
                audit_recording(
                    root / f"{recording_id}_MS" / "heatDataMS.mat",
                    recording_id,
                    cut_volume,
                    signal_class,
                    roles[recording_id],
                )
            )
    ids = [row["recording_id"] for row in recordings]
    roles_complete = bool(
        len(ids) == 22
        and len(set(ids)) == 22
        and set(GCAMP_ROLES).issubset(ids)
        and set(GFP_ROLES).issubset(ids)
    )
    schema_passed = all(bool(row.get("schema_passed")) for row in recordings)
    horizon_passed = all(
        min(row["clock_only_anchor_counts"].values()) >= 100
        for row in recordings
        if row.get("schema_passed")
    )
    unit_viability_passed = all(
        row.get("ratio2_units_passing_prefix_rule", 0) >= 48
        and row.get("r2_units_passing_prefix_rule", 0) >= 48
        for row in recordings
        if row.get("schema_passed")
    )
    return {
        "schema": "ce.ba_srm6.input_audit.v1",
        "contract": "_workspace/ce/brain-adaptive-effective-dimension-validation-20260823/00-contract.md",
        "endpoint_opened": False,
        "model_fit": False,
        "scores_computed": False,
        "constants": {
            "window_volumes": WINDOW,
            "horizon_volumes": HORIZON,
            "leading_guard_volumes": LEADING_GUARD,
            "split_embargo_volumes": EMBARGO,
            "gap_factor": GAP_FACTOR,
            "chronological_split": [0.6, 0.2, 0.2],
            "unit_prefix_finite_fraction": 0.75,
            "unit_prefix_scale_floor": 1e-12,
        },
        "archives": archive_rows,
        "recordings": sorted(recordings, key=lambda row: row["recording_id"]),
        "summary": {
            "archive_passed": archive_passed,
            "schema_passed": schema_passed,
            "split_membership_passed": roles_complete,
            "horizon_availability_passed": horizon_passed,
            "unit_viability_passed": unit_viability_passed,
            "gcamp_recordings": sum(row.get("signal_class") == "gcamp" for row in recordings),
            "gfp_recordings": sum(row.get("signal_class") == "gfp" for row in recordings),
            "input_passed": bool(
                archive_passed
                and schema_passed
                and roles_complete
                and horizon_passed
                and unit_viability_passed
            ),
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output")
    args = parser.parse_args()
    repository = Path(__file__).resolve().parents[4]
    payload = json.dumps(build_receipt(repository), indent=2, sort_keys=True) + "\n"
    if args.output:
        Path(args.output).write_text(payload, encoding="utf-8")
    else:
        print(payload, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
