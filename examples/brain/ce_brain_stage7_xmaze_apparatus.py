"""Score-blind X-maze visit/transition apparatus for DANDI 001701.

This module deliberately does not read unit spike times.  It establishes only
whether behavior can support a later, separately contracted neural analysis.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import h5py
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data" / "external" / "ce_brain_stage7_dandi001701"
FILES = {
    "BaggySweatpants": (
        DATA / "sub-BaggySweatpants_ses-BaggySweatpants-DY15-g1.nwb",
        "5a2246041e421cd5b321adf9ccc40ba6f11379b40b08794c1b214590c50921f3",
    ),
    "Franklin": (
        DATA / "sub-Franklin_ses-Franklin-DY16-g0.nwb",
        "60446690e71448c6228106b09ba669c047ad8cacdf0c1dea6b6cfab73ee0d8b2",
    ),
}
ENDPOINT_RADIUS = 0.18
MINIMUM_DWELL_SECONDS = 0.20
MERGE_GAP_SECONDS = 1.0


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as source:
        while block := source.read(8 * 1024 * 1024):
            value.update(block)
    return value.hexdigest()


def normalize_position(position: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    valid = np.isfinite(position).all(axis=1)
    if valid.mean() < 0.90:
        raise RuntimeError("STAGE7_XMAZE_APPARATUS_STOP: position coverage")
    low = np.nanpercentile(position[valid], 1, axis=0)
    high = np.nanpercentile(position[valid], 99, axis=0)
    if np.any(high <= low):
        raise RuntimeError("STAGE7_XMAZE_APPARATUS_STOP: degenerate position range")
    return (position - low) / (high - low), low, high


def endpoint_visits(position: np.ndarray, rate: float) -> list[dict[str, int | float]]:
    normalized, _, _ = normalize_position(position)
    valid = np.isfinite(normalized).all(axis=1)
    # Labels: west-south, west-north, east-south, east-north.
    corners = np.asarray(((0, 0), (0, 1), (1, 0), (1, 1)), dtype=float)
    distance = np.linalg.norm(normalized[:, None, :] - corners[None, :, :], axis=2)
    nearest = distance.argmin(axis=1)
    labels = np.where(valid & (distance.min(axis=1) <= ENDPOINT_RADIUS), nearest, -1)

    visits: list[dict[str, int | float]] = []
    start = 0
    while start < len(labels):
        if labels[start] < 0:
            start += 1
            continue
        stop = start + 1
        while stop < len(labels) and labels[stop] == labels[start]:
            stop += 1
        if (stop - start) / rate >= MINIMUM_DWELL_SECONDS:
            visit = {"start": start, "stop": stop, "endpoint": int(labels[start])}
            if (
                visits
                and visit["endpoint"] == visits[-1]["endpoint"]
                and (start - int(visits[-1]["stop"])) / rate <= MERGE_GAP_SECONDS
            ):
                visits[-1]["stop"] = stop
            else:
                visits.append(visit)
        start = stop
    return visits


def cross_maze_transitions(visits: list[dict[str, int | float]], rate: float) -> list[dict[str, int | float | str]]:
    transitions: list[dict[str, int | float | str]] = []
    for origin, destination in zip(visits, visits[1:]):
        origin_endpoint = int(origin["endpoint"])
        destination_endpoint = int(destination["endpoint"])
        origin_side = origin_endpoint // 2
        destination_side = destination_endpoint // 2
        if origin_side == destination_side:
            continue
        transitions.append(
            {
                "origin_endpoint": origin_endpoint,
                "destination_endpoint": destination_endpoint,
                "direction": "east_to_west" if origin_side == 1 else "west_to_east",
                "destination_arm": "north" if destination_endpoint % 2 else "south",
                "origin_exit_seconds": float(origin["stop"]) / rate,
                "destination_entry_seconds": float(destination["start"]) / rate,
            }
        )
    return transitions


def audit_file(path: Path, expected_hash: str) -> dict[str, object]:
    actual_hash = digest(path)
    if actual_hash != expected_hash:
        raise RuntimeError("STAGE7_XMAZE_APPARATUS_STOP: SHA-256")
    with h5py.File(path, "r") as nwb:
        if nwb["session_description"][()].decode() != "X Maze":
            raise RuntimeError("STAGE7_XMAZE_APPARATUS_STOP: session type")
        if "intervals" in nwb and len(nwb["intervals"]):
            raise RuntimeError("STAGE7_XMAZE_APPARATUS_STOP: unexpected intervals")
        position_series = nwb["processing/behavior/Position/position"]
        position = np.asarray(position_series["data"])
        rate = float(position_series["starting_time"].attrs["rate"])
        reference_frame = position_series["reference_frame"][()].decode()
        units = len(nwb["units/id"])
    normalized, low, high = normalize_position(position)
    visits = endpoint_visits(position, rate)
    transitions = cross_maze_transitions(visits, rate)
    endpoint_counts = np.bincount([int(v["endpoint"]) for v in visits], minlength=4)
    direction_counts = {
        direction: sum(t["direction"] == direction for t in transitions)
        for direction in ("east_to_west", "west_to_east")
    }
    eligible = (
        reference_frame == "(0,0) is bottom left corner"
        and np.isfinite(normalized).all(axis=1).mean() >= 0.90
        and min(endpoint_counts) >= 20
        and min(direction_counts.values()) >= 40
    )
    return {
        "decision": "STAGE7_XMAZE_BEHAVIOR_APPARATUS_ELIGIBLE" if eligible else "STAGE7_XMAZE_APPARATUS_STOP",
        "file": path.name,
        "sha256": actual_hash,
        "sampling_rate_hz": rate,
        "position_rows": len(position),
        "position_valid_fraction": float(np.isfinite(position).all(axis=1).mean()),
        "normalization_percentile_1": low.tolist(),
        "normalization_percentile_99": high.tolist(),
        "endpoint_radius": ENDPOINT_RADIUS,
        "minimum_dwell_seconds": MINIMUM_DWELL_SECONDS,
        "merge_gap_seconds": MERGE_GAP_SECONDS,
        "endpoint_visit_counts_west_south_west_north_east_south_east_north": endpoint_counts.tolist(),
        "cross_maze_transition_counts": direction_counts,
        "units_present_but_spike_times_unread": units,
        "trial_semantics": "absent",
    }


def audit() -> dict[str, object]:
    sessions = {name: audit_file(path, expected_hash) for name, (path, expected_hash) in FILES.items()}
    passed = all(session["decision"] == "STAGE7_XMAZE_BEHAVIOR_APPARATUS_ELIGIBLE" for session in sessions.values())
    return {
        "decision": "STAGE7_XMAZE_BEHAVIOR_APPARATUS_ELIGIBLE" if passed else "STAGE7_XMAZE_APPARATUS_STOP",
        "sessions": sessions,
        "primary_later_direction": "east_to_west (official task: east sample, west choice)",
        "claim_ceiling": "behavior apparatus only; no correct/reward/retrieval/correction claim; unit spike times unopened",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = audit()
    payload = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        if args.output.exists():
            raise RuntimeError(f"refusing overwrite: {args.output}")
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload, encoding="utf-8")
    print(payload, end="")


if __name__ == "__main__":
    main()
