"""Schema-only eligibility audit for one Stage 6 Allen development NWB."""
from __future__ import annotations

import argparse
import collections
import hashlib
import json
from pathlib import Path

import h5py
import numpy as np

EXPECTED_SHA256 = "4e284295a1be5c6cca49df84fab52ad38b4749d2361b2edebeb676051cf09921"
EXPECTED_SESSION = "721123822"
VISUAL_PREFIXES = ("VIS",)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        while block := source.read(8 * 1024 * 1024):
            digest.update(block)
    return digest.hexdigest()


def text(value) -> str:
    return value.decode() if hasattr(value, "decode") else str(value)


def audit(path: Path, verify_hash: bool = True) -> dict:
    actual_hash = sha256(path) if verify_hash else "NOT_CHECKED_IN_UNIT_TEST"
    if verify_hash and actual_hash != EXPECTED_SHA256:
        raise RuntimeError(f"STAGE6_SCHEMA_STOP: SHA-256 mismatch {actual_hash}")
    with h5py.File(path, "r") as nwb:
        identifier = text(nwb["/identifier"][()])
        if identifier != EXPECTED_SESSION:
            raise RuntimeError(f"STAGE6_SCHEMA_STOP: session {identifier}")
        required = (
            "/units/id", "/units/spike_times", "/units/spike_times_index", "/units/peak_channel_id",
            "/general/extracellular_ephys/electrodes/id", "/general/extracellular_ephys/electrodes/location",
            "/intervals/natural_movie_one_presentations/frame",
            "/intervals/natural_movie_one_presentations/start_time",
            "/intervals/natural_movie_one_presentations/stop_time",
            "/intervals/natural_movie_one_presentations/stimulus_block",
            "/processing/running/running_speed",
        )
        missing = [name for name in required if name not in nwb]
        if missing:
            raise RuntimeError(f"STAGE6_SCHEMA_STOP: missing {missing}")
        base = "/intervals/natural_movie_one_presentations"
        frames = np.asarray(nwb[f"{base}/frame"])
        starts = np.asarray(nwb[f"{base}/start_time"])
        stops = np.asarray(nwb[f"{base}/stop_time"])
        blocks = np.asarray(nwb[f"{base}/stimulus_block"])
        resets = np.flatnonzero(np.r_[True, frames[1:] <= frames[:-1]])
        ends = np.r_[resets[1:], len(frames)]
        repeat_lengths = ends - resets
        electrode_ids = np.asarray(nwb["/general/extracellular_ephys/electrodes/id"])
        locations = [text(x) for x in nwb["/general/extracellular_ephys/electrodes/location"][()]]
        location_for = dict(zip(electrode_ids.tolist(), locations))
        peak_channels = np.asarray(nwb["/units/peak_channel_id"])
        unit_locations = collections.Counter(location_for.get(int(channel), "MISSING") for channel in peak_channels)
        visual_units = sum(count for location, count in unit_locations.items() if location.startswith(VISUAL_PREFIXES))
        valid = bool(
            len(frames) >= 9_000
            and len(resets) >= 10
            and np.all(repeat_lengths == 900)
            and np.array_equal(np.unique(frames), np.arange(900))
            and np.all(np.isfinite(starts))
            and np.all(np.isfinite(stops))
            and np.all(starts[1:] > starts[:-1])
            and np.all(stops > starts)
            and visual_units >= 200
            and len(np.unique(blocks)) >= 2
        )
        return {
            "decision": "STAGE6_DEVELOPMENT_SCHEMA_ELIGIBLE" if valid else "STAGE6_SCHEMA_STOP",
            "session_id": identifier,
            "nwb_sha256": actual_hash,
            "unit_count": int(len(peak_channels)),
            "visual_unit_count": int(visual_units),
            "unit_locations": dict(sorted(unit_locations.items())),
            "natural_movie_one": {
                "rows": int(len(frames)),
                "unique_frames": int(len(np.unique(frames))),
                "repeat_count": int(len(resets)),
                "repeat_lengths": dict(sorted(collections.Counter(map(int, repeat_lengths)).items())),
                "stimulus_blocks": sorted(map(int, np.unique(blocks))),
                "strict_time_order": bool(np.all(starts[1:] > starts[:-1])),
                "start_min": float(starts.min()),
                "stop_max": float(stops.max()),
            },
            "running_speed_present": True,
            "confirmation_endpoint_opened": False,
            "dandi_001695_opened": False,
            "claim_ceiling": "development schema eligibility only; no predictive score",
        }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("nwb", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = audit(args.nwb)
    payload = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        if args.output.exists():
            raise RuntimeError(f"STAGE6_SCHEMA_STOP: refusing overwrite {args.output}")
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload, encoding="utf-8")
    print(payload, end="")


if __name__ == "__main__":
    main()

