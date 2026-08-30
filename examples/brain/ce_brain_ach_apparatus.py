"""Endpoint-blind direct-write-gate audit for DANDI 001176."""
from __future__ import annotations

import hashlib
from pathlib import Path

import h5py

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data" / "external" / "ce_brain_ach_dandi001176"
FILES = {
    "ach_only": (
        DATA / "sub-22713_ses-22713-2-2-Ach-V1_behavior+ophys.nwb",
        "ff1eca2449c8c8ac56c92b1a00e0ecd5d8a1e121a0d6e0b1ae6fe11d77119075",
    ),
    "simultaneous_axon_ach": (
        DATA / "sub-26536_ses-26536-2-2_behavior+ophys.nwb",
        "4074ccfc0529e10743723ad62297916bff7fa41089836949fe7ff7956bc7fb3f",
    ),
}


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as source:
        while block := source.read(8 * 1024 * 1024):
            value.update(block)
    return value.hexdigest()


def audit_file(path: Path, expected_hash: str) -> dict[str, object]:
    if digest(path) != expected_hash:
        raise RuntimeError("ACH_APPARATUS_STOP: SHA-256")
    with h5py.File(path, "r") as nwb:
        acquisition = set(nwb.get("acquisition", {}).keys())
        processing = set(nwb.get("processing", {}).keys())
        intervals = set(nwb.get("intervals", {}).keys())
        indicators = []
        locations = []
        fluorescence_shapes = []
        if "processing/ophys/ImageSegmentation" in nwb:
            for plane in nwb["processing/ophys/ImageSegmentation"].values():
                if isinstance(plane, h5py.Group) and "imaging_plane" in plane:
                    imaging_plane = plane["imaging_plane"]
                    indicators.append(imaging_plane["indicator"][()].decode())
                    locations.append(imaging_plane["location"][()].decode())
        if "processing/ophys/Fluorescence" in nwb:
            for series in nwb["processing/ophys/Fluorescence"].values():
                fluorescence_shapes.append(list(series["data"].shape))
    return {
        "file": path.name,
        "sha256": expected_hash,
        "acquisition": sorted(acquisition),
        "processing": sorted(processing),
        "intervals": sorted(intervals),
        "indicators": indicators,
        "locations": locations,
        "fluorescence_shapes": fluorescence_shapes,
        "has_behavior_state": {"PupilTracking", "treadmill_velocity"}.issubset(acquisition),
        "has_ach": "Ach sensor" in indicators,
        "has_cholinergic_axon_gcamp": "GCaMP" in indicators,
        "has_ephys": "ecephys" in processing or any("Electrical" in name for name in acquisition),
        "has_intervention_or_trials": bool(intervals),
        "has_persistent_update_endpoint": False,
    }


def audit() -> dict[str, object]:
    files = {name: audit_file(path, expected_hash) for name, (path, expected_hash) in FILES.items()}
    combined = files["simultaneous_axon_ach"]
    fast_dynamics = bool(
        combined["has_behavior_state"]
        and combined["has_ach"]
        and combined["has_cholinergic_axon_gcamp"]
    )
    direct_gate = bool(
        fast_dynamics and combined["has_ephys"]
        and combined["has_intervention_or_trials"]
        and combined["has_persistent_update_endpoint"]
    )
    return {
        "decision": (
            "ACH_DIRECT_WRITE_GATE_IDENTIFIABLE" if direct_gate
            else "ACH_FAST_DYNAMICS_PRESENT_WRITE_GATE_NOT_IDENTIFIABLE" if fast_dynamics
            else "ACH_APPARATUS_STOP"
        ),
        "dandiset": "001176@0.260610.2204",
        "inventory_assets": 132,
        "inventory_subjects": 29,
        "inventory_bytes": 924_191_446,
        "files": files,
        "missing_for_direct_gate": [
            "local electrical population trajectory",
            "controlled or naturally repeated matched trajectory with different ACh",
            "subsequent persistent synaptic/representational/behavioral update endpoint",
        ],
        "claim_ceiling": "fast ACh/axon/behavior coupling apparatus only; no chemical write-permission claim",
    }
