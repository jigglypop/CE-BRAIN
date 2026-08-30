"""Reproduce the author-defined mono/bi/trisynaptic structural profiles."""

from __future__ import annotations

import argparse
import hashlib
import itertools
import json
from pathlib import Path

import numpy as np
from scipy.io import loadmat

from examples.brain.ce_brain_stage3f_optofmri_state_rdm import SITES, load_nifti
from examples.brain.ce_brain_stage3g_optofmri_physical_distance import left_source_labels


CONNECTOME_ZIP_SHA256 = "8b481aebca120d41532c7fd5ab1845c6eb9c043c939b6e3eddd2c937b611a09f"
CONNECTOME_MAT_SHA256 = "87bd852da4c72499dbc788bd911154789cfe4bd374a79b956cbc2995bb0d86bf"
TESSELLATION_SHA256 = "8f2760fff6d0fe4654e377f7956392a470d50446cbc182bfab56495971c52eca"
POLYSYNAPTIC_ZIP_SHA256 = "183e458904d00a265450f9b2ec1956b774cc8c314699f58cbe7b4b757cfa672e"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(8 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def parcel_weights(
    atlas: np.ndarray,
    tessellation: np.ndarray,
    label_groups: list[tuple[int, ...]],
    parcel_count: int,
) -> np.ndarray:
    if atlas.shape != tessellation.shape:
        raise ValueError("atlas and tessellation shapes differ")
    weights = np.zeros((len(label_groups), parcel_count), dtype=np.float64)
    parcel_ids = np.asarray(tessellation, dtype=np.int64)
    for row, labels in enumerate(label_groups):
        selected = parcel_ids[np.isin(atlas, labels)]
        selected = selected[selected > 0]
        if not len(selected) or int(selected.max()) > parcel_count:
            raise ValueError(f"invalid or empty parcel selection at row {row}")
        counts = np.bincount(selected, minlength=parcel_count + 1)[1:]
        weights[row] = counts / counts.sum()
    return weights


def incremental_residuals(beta: np.ndarray) -> np.ndarray:
    """Match MATLAB regress residualization across target ROIs."""
    beta = np.asarray(beta, dtype=np.float64)
    result = np.zeros_like(beta)
    result[:, :, 0] = beta[:, :, 0]
    for order in range(1, beta.shape[2]):
        for source in range(beta.shape[0]):
            predictors = np.column_stack(
                [beta[source, :, :order], np.ones(beta.shape[1], dtype=float)]
            )
            coefficients, *_ = np.linalg.lstsq(predictors, beta[source, :, order], rcond=None)
            result[source, :, order] = beta[source, :, order] - predictors @ coefficients
    return result


def normalize_targets(profiles: np.ndarray) -> np.ndarray:
    mean = profiles.mean(axis=1, keepdims=True)
    scale = profiles.std(axis=1, ddof=1, keepdims=True)
    if np.any(scale == 0):
        raise ValueError("constant structural profile")
    return (profiles - mean) / scale


def profile_rdm(profiles: np.ndarray) -> np.ndarray:
    pairs = itertools.combinations(range(len(profiles)), 2)
    return np.asarray(
        [1.0 - np.corrcoef(profiles[left], profiles[right])[0, 1] for left, right in pairs],
        dtype=float,
    )


def _atlas_roi_groups(allen_idx_proc: np.ndarray) -> list[tuple[int, ...]]:
    groups = []
    for row in allen_idx_proc:
        groups.append(tuple(int(value) for value in np.asarray(row[2]).ravel()))
    return groups


def build_operator(
    connectome_mat: Path,
    tessellation_path: Path,
    atlas_mat: Path,
    max_order: int = 3,
) -> dict[str, object]:
    if sha256_file(connectome_mat) != CONNECTOME_MAT_SHA256:
        raise ValueError("connectome SHA-256 mismatch")
    if sha256_file(tessellation_path) != TESSELLATION_SHA256:
        raise ValueError("tessellation SHA-256 mismatch")

    atlas_data = loadmat(atlas_mat)
    atlas = np.asarray(atlas_data["atlas_orig"])
    allen = np.asarray(atlas_data["Allen_idx_proc"], dtype=object)
    tessellation = load_nifti(tessellation_path)
    roi_groups = _atlas_roi_groups(allen)
    source_groups = [left_source_labels()[site] for site in SITES]
    source_weights = parcel_weights(atlas, tessellation, source_groups, 15314)
    roi_weights = parcel_weights(atlas, tessellation, roi_groups, 15314)
    source_parcels = source_weights > 0

    print("loading 15314x15314 connectome", flush=True)
    connectome = np.asarray(
        loadmat(connectome_mat, variable_names=("full_connectome_no_thr",))[
            "full_connectome_no_thr"
        ],
        dtype=np.float64,
    )
    if connectome.shape != (15314, 15314) or not np.isfinite(connectome).all():
        raise ValueError("invalid connectome matrix")
    forward = source_weights @ connectome
    beta = np.empty((len(SITES), len(roi_groups), max_order), dtype=np.float64)
    for order in range(max_order):
        if order:
            print(f"computing structural order {order + 1}", flush=True)
            forward = forward @ connectome
        forward[source_parcels] = 0.0
        beta[:, :, order] = forward @ roi_weights.T

    residual = incremental_residuals(beta)
    normalized = normalize_targets(residual)
    rdms = {
        f"incremental_order_{order + 1}": profile_rdm(normalized[:, :, order]).tolist()
        for order in range(max_order)
    }
    return {
        "status": "STRUCTURAL_OPERATOR_BUILT",
        "source_order": list(SITES),
        "target_roi_count": len(roi_groups),
        "parcel_count": 15314,
        "source_parcel_counts": {
            site: int(source_parcels[index].sum()) for index, site in enumerate(SITES)
        },
        "orders": max_order,
        "structural_rdms": rdms,
        "beta_profiles": beta.tolist(),
        "incremental_normalized_profiles": normalized.tolist(),
        "input_sha256": {
            "full_connectome_no_thr.mat": CONNECTOME_MAT_SHA256,
            "final_tesselation.nii.gz": TESSELLATION_SHA256,
            "Allen_idx_proc.mat": sha256_file(atlas_mat),
        },
        "response_data_used": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--connectome", type=Path, required=True)
    parser.add_argument("--tessellation", type=Path, required=True)
    parser.add_argument("--atlas", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--max-order", type=int, default=3)
    args = parser.parse_args()
    result = build_operator(args.connectome, args.tessellation, args.atlas, args.max_order)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: value for key, value in result.items() if key not in {
        "beta_profiles", "incremental_normalized_profiles"
    }}, indent=2))


if __name__ == "__main__":
    main()
