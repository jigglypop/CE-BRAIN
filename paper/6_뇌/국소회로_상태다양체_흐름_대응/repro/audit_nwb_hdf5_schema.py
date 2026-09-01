#!/usr/bin/env python3
"""Audit the structural contract of a Stx3 NWB file without reading outcomes.

Only dataset paths, shapes, dtypes, file identity, and the scalar subject identifier
are inspected.  Neural and behavioural arrays are never sliced or materialised.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any

import h5py


OPHYS_PATHS = {
    "dff": "processing/ophys/dF/dF/data",
    "fluorescence": "processing/ophys/fluorescence/fluorescence/data",
    "neuropil": "processing/ophys/neuropil/neuropil fluorescence/data",
    "roi_ids": "processing/ophys/ImageSegmentation/PlaneSegmentation/id",
}

ALIGNED_SIGNALS = (
    "block",
    "left or right",
    "licks",
    "position",
    "reward",
    "speed",
    "trial end",
    "trial number",
    "trial start",
    "x position",
    "y position",
)

FULL_RES_SIGNALS = (
    "block",
    "consummatory licks",
    "left or right",
    "manual rewards",
    "non-consummatory licks",
    "position",
    "reward",
    "rotary encoder reading",
    "speed",
    "trial end",
    "trial number",
    "trial start",
    "x position",
    "y position",
)

SUBJECT_FROM_PATH_RE = re.compile(r"(?:^|[\\/])sub-(?P<subject>[^\\/_]+)(?:[\\/]|_)")
DAY_FROM_PATH_RE = re.compile(r"_ses-ymaze-day(?P<day>\d+)-")


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _dataset_record(dataset: h5py.Dataset) -> dict[str, Any]:
    return {
        "shape": list(dataset.shape),
        "dtype": str(dataset.dtype),
        "ndim": int(dataset.ndim),
    }


def _decode_scalar_identity(dataset: h5py.Dataset) -> str:
    """Read only the non-outcome scalar identity field."""
    value = dataset[()]
    if isinstance(value, bytes):
        return value.decode("utf-8")
    return str(value)


def _normalise_subject(subject: str) -> str:
    return subject.replace("_", "-")


def audit_nwb_schema(path: Path, *, expected_sha256: str | None = None) -> dict[str, Any]:
    errors: list[str] = []
    datasets: dict[str, dict[str, Any]] = {}
    identity: dict[str, Any] = {}

    actual_sha256 = file_sha256(path)
    if expected_sha256 is not None and actual_sha256.lower() != expected_sha256.lower():
        errors.append(
            f"sha256 mismatch: expected {expected_sha256.lower()}, observed {actual_sha256.lower()}"
        )

    with h5py.File(path, "r") as nwb:
        subject_path = "general/subject/subject_id"
        if subject_path not in nwb or not isinstance(nwb[subject_path], h5py.Dataset):
            errors.append(f"missing dataset: {subject_path}")
            subject = None
        else:
            subject_dataset = nwb[subject_path]
            datasets[subject_path] = _dataset_record(subject_dataset)
            subject = _decode_scalar_identity(subject_dataset)
            identity["subject_id"] = subject

        path_subject_match = SUBJECT_FROM_PATH_RE.search(path.as_posix())
        path_subject = path_subject_match.group("subject") if path_subject_match else None
        identity["path_subject"] = path_subject
        if subject is not None and path_subject is not None:
            if _normalise_subject(subject) != _normalise_subject(path_subject):
                errors.append(
                    f"subject mismatch: NWB={subject!r}, path={path_subject!r}"
                )

        day_match = DAY_FROM_PATH_RE.search(path.name)
        identity["path_day"] = int(day_match.group("day")) if day_match else None

        for label, dataset_path in OPHYS_PATHS.items():
            if dataset_path not in nwb or not isinstance(nwb[dataset_path], h5py.Dataset):
                errors.append(f"missing {label} dataset: {dataset_path}")
                continue
            datasets[dataset_path] = _dataset_record(nwb[dataset_path])

        neural_paths = [OPHYS_PATHS[key] for key in ("dff", "fluorescence", "neuropil")]
        if all(dataset_path in nwb for dataset_path in neural_paths):
            neural_shapes = [tuple(nwb[dataset_path].shape) for dataset_path in neural_paths]
            if any(len(shape) != 2 for shape in neural_shapes):
                errors.append(f"neural arrays must be 2-D: {neural_shapes}")
            elif len(set(neural_shapes)) != 1:
                errors.append(f"neural array shape mismatch: {neural_shapes}")
            neural_shape = neural_shapes[0]
        else:
            neural_shape = None

        roi_path = OPHYS_PATHS["roi_ids"]
        if neural_shape is not None and roi_path in nwb:
            roi_shape = tuple(nwb[roi_path].shape)
            if roi_shape != (neural_shape[1],):
                errors.append(
                    f"ROI count mismatch: neural columns={neural_shape[1]}, roi_ids={roi_shape}"
                )

        aligned_prefix = "processing/behavior/2P-aligned behavior"
        aligned_lengths: set[int] = set()
        for signal in ALIGNED_SIGNALS:
            for leaf in ("data", "timestamps"):
                dataset_path = f"{aligned_prefix}/{signal}/{leaf}"
                if dataset_path not in nwb or not isinstance(nwb[dataset_path], h5py.Dataset):
                    errors.append(f"missing aligned behaviour dataset: {dataset_path}")
                    continue
                dataset = nwb[dataset_path]
                datasets[dataset_path] = _dataset_record(dataset)
                if dataset.ndim != 1:
                    errors.append(f"aligned behaviour dataset must be 1-D: {dataset_path}")
                elif dataset.shape:
                    aligned_lengths.add(int(dataset.shape[0]))

        if len(aligned_lengths) != 1:
            errors.append(f"aligned behaviour lengths disagree: {sorted(aligned_lengths)}")
        elif neural_shape is not None and next(iter(aligned_lengths)) != neural_shape[0]:
            errors.append(
                "aligned behaviour length does not equal neural frame count: "
                f"{next(iter(aligned_lengths))} != {neural_shape[0]}"
            )

        full_prefix = "processing/behavior/Full temporal resolution behavior"
        full_lengths: set[int] = set()
        for signal in FULL_RES_SIGNALS:
            for leaf in ("data", "timestamps"):
                dataset_path = f"{full_prefix}/{signal}/{leaf}"
                if dataset_path not in nwb or not isinstance(nwb[dataset_path], h5py.Dataset):
                    errors.append(f"missing full-resolution behaviour dataset: {dataset_path}")
                    continue
                dataset = nwb[dataset_path]
                datasets[dataset_path] = _dataset_record(dataset)
                if dataset.ndim != 1:
                    errors.append(f"full-resolution dataset must be 1-D: {dataset_path}")
                elif dataset.shape:
                    full_lengths.add(int(dataset.shape[0]))

        if len(full_lengths) != 1:
            errors.append(f"full-resolution behaviour lengths disagree: {sorted(full_lengths)}")

    return {
        "status": "NWB_SCHEMA_AUDIT_PASS" if not errors else "NWB_SCHEMA_AUDIT_FAIL",
        "scope": (
            "file identity plus HDF5 paths/shapes/dtypes and scalar subject identity only; "
            "no neural or behavioural outcome values evaluated"
        ),
        "file": path.as_posix(),
        "size": path.stat().st_size,
        "sha256": actual_sha256,
        "identity": identity,
        "datasets": dict(sorted(datasets.items())),
        "errors": errors,
        "biological_endpoint_evaluated": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--expected-sha256")
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    result = audit_nwb_schema(args.input, expected_sha256=args.expected_sha256)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"].endswith("PASS") else 1


if __name__ == "__main__":
    raise SystemExit(main())
