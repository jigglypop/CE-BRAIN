#!/usr/bin/env python3
"""Safely audit the day-0/day-5 dense-cohort ROI registration maps.

The provider's files are dill/pickle streams.  This module never calls ``dill.load``
or unrestricted ``pickle.load``: only a tiny NumPy reconstruction allowlist is
accepted, followed by strict plain-container validation.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib
import io
import json
import pickle
from pathlib import Path
from typing import Any

import numpy as np


# Pinned from mouse_metadata.py at code commit
# f2ab24db8709a321d38576a1fa674f95035a2fec.
DENSE_DAY0_DAY5_RAVEL = {
    "Ctrl_1": (0, 5),
    "Ctrl_2": (0, 6),
    "Ctrl_3": (0, 5),
    "Ctrl_4": (1, 7),
    "Ctrl_5": (0, 5),
    "Ctrl_6": (0, 5),
    "Ctrl_7": (0, 5),
    "Ctrl_8": (0, 5),
    "Ctrl_9": (0, 5),
    "Cre_1": (1, 6),
    "Cre_2": (0, 5),
    "Cre_3": (0, 5),
    "Cre_4": (0, 5),
    "Cre_5": (0, 5),
    "Cre_6": (0, 5),
    "Cre_7": (0, 5),
}

_SAFE_MODULES = {
    "numpy",
    "numpy._core.multiarray",
    "numpy.core.multiarray",
    "numpy.core._multiarray_umath",
}


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _safe_import_module(name: str):
    if name not in _SAFE_MODULES:
        raise pickle.UnpicklingError(f"blocked dill module import: {name!r}")
    return importlib.import_module(name)


def _safe_get_attr(obj: Any, name: str):
    module_name = getattr(obj, "__name__", None)
    if module_name not in _SAFE_MODULES or name not in {"dtype", "scalar"}:
        raise pickle.UnpicklingError(
            f"blocked dill attribute lookup: {module_name!r}.{name}"
        )
    return getattr(obj, name)


class RestrictedAlignerUnpickler(pickle.Unpickler):
    """Permit only the globals needed for lists of NumPy scalar indices."""

    def find_class(self, module: str, name: str):
        if (module, name) == ("dill._dill", "_import_module"):
            return _safe_import_module
        if (module, name) == ("dill._dill", "_get_attr"):
            return _safe_get_attr
        if (module, name) == ("numpy", "dtype"):
            return np.dtype
        if module in {"numpy._core.multiarray", "numpy.core.multiarray"} and name == "scalar":
            return np._core.multiarray.scalar
        raise pickle.UnpicklingError(f"blocked pickle global: {module}.{name}")


def restricted_loads(payload: bytes) -> Any:
    return RestrictedAlignerUnpickler(io.BytesIO(payload)).load()


def _integer_vector(value: Any, *, label: str) -> np.ndarray:
    if not isinstance(value, (list, tuple, np.ndarray)):
        raise ValueError(f"{label} is not a list/tuple/array")
    array = np.asarray(value)
    if array.ndim != 1:
        raise ValueError(f"{label} must be 1-D, observed {array.shape}")
    if not np.issubdtype(array.dtype, np.integer):
        raise ValueError(f"{label} must be integer, observed {array.dtype}")
    array = array.astype(np.int64, copy=False)
    if array.size == 0 or np.any(array < 0):
        raise ValueError(f"{label} must contain nonnegative indices")
    if np.unique(array).size != array.size:
        raise ValueError(f"{label} contains duplicate indices")
    return array


def load_day_pair(path: Path, day0_ravel: int, day5_ravel: int) -> tuple[np.ndarray, np.ndarray]:
    matches = restricted_loads(path.read_bytes())
    if not isinstance(matches, dict):
        raise ValueError("aligner root must be a dict")
    if day0_ravel not in matches or not isinstance(matches[day0_ravel], dict):
        raise ValueError(f"missing day-0 reference ravel index {day0_ravel}")
    reference = matches[day0_ravel]
    if day5_ravel not in reference or not isinstance(reference[day5_ravel], dict):
        raise ValueError(f"missing day-5 target ravel index {day5_ravel}")
    pair = reference[day5_ravel]
    if not {"ref_inds", "targ_inds"}.issubset(pair):
        raise ValueError("aligner pair lacks ref_inds/targ_inds")
    ref_inds = _integer_vector(pair["ref_inds"], label="ref_inds")
    targ_inds = _integer_vector(pair["targ_inds"], label="targ_inds")
    if ref_inds.shape != targ_inds.shape:
        raise ValueError(
            f"ref/target mapping length mismatch: {ref_inds.shape} vs {targ_inds.shape}"
        )
    return ref_inds, targ_inds


def audit_dense_maps(root: Path, *, minimum_common_rois: int = 20) -> dict[str, Any]:
    errors: list[str] = []
    records: list[dict[str, Any]] = []
    canonical_pairs: list[dict[str, Any]] = []

    for subject, (day0_ravel, day5_ravel) in sorted(DENSE_DAY0_DAY5_RAVEL.items()):
        path = root / subject / "roi_aligner_results.pkl"
        try:
            if not path.is_file():
                raise ValueError(f"missing aligner: {path}")
            ref_inds, targ_inds = load_day_pair(path, day0_ravel, day5_ravel)
            pair_payload = [
                [int(ref_index), int(targ_index)]
                for ref_index, targ_index in zip(ref_inds, targ_inds, strict=True)
            ]
            pair_bytes = json.dumps(pair_payload, separators=(",", ":")).encode("ascii")
            if ref_inds.size < minimum_common_rois:
                errors.append(
                    f"{subject}: common ROI count {ref_inds.size} < {minimum_common_rois}"
                )
            record = {
                "subject": subject,
                "group": "Ctrl" if subject.startswith("Ctrl_") else "Cre",
                "path": path.as_posix(),
                "pickle_sha256": file_sha256(path),
                "day0_ravel_ind": day0_ravel,
                "day5_ravel_ind": day5_ravel,
                "common_roi_count": int(ref_inds.size),
                "day0_roi_min": int(ref_inds.min()),
                "day0_roi_max": int(ref_inds.max()),
                "day5_roi_min": int(targ_inds.min()),
                "day5_roi_max": int(targ_inds.max()),
                "ordered_pairs_sha256": hashlib.sha256(pair_bytes).hexdigest(),
            }
            records.append(record)
            canonical_pairs.append({"subject": subject, "pairs": pair_payload})
        except Exception as exc:
            errors.append(f"{subject}: {exc}")

    canonical = json.dumps(
        canonical_pairs, sort_keys=True, separators=(",", ":")
    ).encode("ascii")
    passed = len(records) == len(DENSE_DAY0_DAY5_RAVEL) and not errors
    return {
        "status": "STX3_ROI_ALIGNER_AUDIT_PASS" if passed else "STX3_ROI_ALIGNER_AUDIT_FAIL",
        "scope": "registration identities and integer ROI maps only; no neural/behavioural outcomes",
        "root": root.as_posix(),
        "source_code_commit": "f2ab24db8709a321d38576a1fa674f95035a2fec",
        "minimum_common_rois": minimum_common_rois,
        "subject_count": len(records),
        "canonical_day0_day5_pairs_sha256": hashlib.sha256(canonical).hexdigest(),
        "subjects": records,
        "errors": errors,
        "biological_endpoint_evaluated": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", required=True, type=Path)
    parser.add_argument("--minimum-common-rois", type=int, default=20)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    result = audit_dense_maps(args.root, minimum_common_rois=args.minimum_common_rois)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"].endswith("PASS") else 1


if __name__ == "__main__":
    raise SystemExit(main())
