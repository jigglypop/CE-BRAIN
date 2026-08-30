"""Preregistered Stage 3 source-held-out analysis for Borealis VSD data."""

from __future__ import annotations

import argparse
import hashlib
import io
import itertools
import json
import math
import zipfile
from pathlib import Path

import numpy as np


STIM_LABELS = (
    "M2L", "BCR", "RSL", "MFR", "BCL", "HLR", "MBL", "V2R", "FLL", "PTR",
    "HLL", "M2R", "PTL", "FLR", "V2L", "MBR", "V1L", "V1R", "MFL", "RSR",
)
DEVELOPMENT_LABELS = (
    "V2L", "HLR", "M2R", "MFR", "RSL", "MBR", "MFL", "V1R", "PTR", "RSR",
    "PTL", "M2L",
)
ZIP_PREFIX = "Neurophotonics tutorial/"


def locked_split() -> tuple[list[str], list[str], list[str]]:
    ranked = sorted(
        STIM_LABELS,
        key=lambda label: hashlib.sha256(
            f"CE-BRAIN-stage3-vsd-r1|{label}".encode()
        ).hexdigest(),
    )
    return ranked[:12], ranked[12:16], ranked[16:]


def _read_tiff(payload: bytes) -> np.ndarray:
    from PIL import Image

    with Image.open(io.BytesIO(payload)) as image:
        if image.size != (128, 128) or image.n_frames != 108:
            raise ValueError(
                f"unexpected TIFF apparatus: size={image.size}, frames={image.n_frames}"
            )
        frames = []
        for index in range(image.n_frames):
            image.seek(index)
            frames.append(np.asarray(image, dtype=np.float64))
    return np.stack(frames, axis=0)


def _gaussian_kernel() -> np.ndarray:
    axis = np.arange(-2, 3, dtype=np.float64)
    xx, yy = np.meshgrid(axis, axis)
    kernel = np.exp(-(xx * xx + yy * yy) / (2.0 * 2.5**2))
    return kernel / kernel.sum()


def response_vector(stim: np.ndarray, no_stim: np.ndarray, positions: np.ndarray) -> np.ndarray:
    """Reproduce the fixed MATLAB response definition for one repeat."""
    from scipy.ndimage import convolve

    if stim.shape != (108, 128, 128) or no_stim.shape != stim.shape:
        raise ValueError("expected paired 108x128x128 TIFF stacks")
    if np.any(no_stim == 0):
        raise ValueError("zero no-stim denominator")
    normalized = stim / no_stim
    baseline = normalized[2:28].mean(axis=0)
    if np.any(baseline == 0) or not np.isfinite(baseline).all():
        raise ValueError("invalid normalization baseline")
    dff = (normalized - baseline) / baseline * 100.0
    filtered = convolve(
        dff, _gaussian_kernel()[None, :, :], mode="constant", cval=0.0
    )
    filtered = np.delete(filtered, 31, axis=0)
    filtered = np.concatenate((filtered, filtered[-1:]), axis=0)

    values = np.zeros(len(positions), dtype=np.float64)
    for index, (x_one_based, y_one_based) in enumerate(positions):
        x = int(x_one_based) - 1
        y = int(y_one_based) - 1
        roi = filtered[:, y : y + 5, x : x + 5].mean(axis=(1, 2))
        base = roi[19:28]
        base_mean = float(base.mean())
        base_sd = float(base.std(ddof=1))
        peak = float(roi[31:42].max())
        if peak > 2.5 * base_sd:
            values[index] = max(0.0, float(roi[32:35].sum() - 3.0 * base_mean))
    if not np.isfinite(values).all():
        raise ValueError("non-finite response")
    return values


def load_development_matrices(zip_path: Path) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    from scipy.io import loadmat

    development, calibration, confirmation = locked_split()
    if tuple(development) != DEVELOPMENT_LABELS:
        raise AssertionError("locked source split changed")
    del calibration, confirmation
    matrices = [np.zeros((len(development), len(STIM_LABELS))) for _ in range(2)]
    with zipfile.ZipFile(zip_path) as archive:
        positions = loadmat(
            io.BytesIO(archive.read(ZIP_PREFIX + "Matlab codes/pos.mat"))
        )["pos"].astype(np.float64)
        if positions.shape != (20, 2):
            raise ValueError(f"unexpected pos.mat shape: {positions.shape}")
        for row_index, label in enumerate(development):
            source_index = STIM_LABELS.index(label)
            no_letter = chr(ord("A") + source_index // 2)
            for repeat in (1, 2):
                stim = _read_tiff(
                    archive.read(f"{ZIP_PREFIX}Data/{label}{repeat}.tif")
                )
                no_stim = _read_tiff(
                    archive.read(f"{ZIP_PREFIX}Data/NO{no_letter}{repeat}.tif")
                )
                vector = response_vector(stim, no_stim, positions)
                vector[source_index] = 0.0
                matrices[repeat - 1][row_index] = vector
    return matrices[0], matrices[1], positions


def _design(
    source_indices: list[int], receiver_indices: np.ndarray, positions: np.ndarray, model: str
) -> np.ndarray:
    rows = []
    receiver_count = len(positions)
    for source in source_indices:
        delta = positions[receiver_indices] - positions[source]
        intercept = np.eye(receiver_count)[receiver_indices]
        if model == "euclidean":
            distance = np.sqrt(np.square(delta).sum(axis=1))
            geometry = np.column_stack((distance, distance**2))
        elif model == "directed":
            dx, dy = delta[:, 0], delta[:, 1]
            geometry = np.column_stack((dx, dy, dx**2, dx * dy, dy**2))
        else:
            raise ValueError(model)
        rows.append(np.column_stack((intercept, geometry)))
    return np.vstack(rows)


def predict_model(
    train: np.ndarray,
    train_source_indices: list[int],
    target_source_index: int,
    positions: np.ndarray,
    model: str,
) -> np.ndarray:
    receiver_indices = np.arange(len(positions))
    if model == "baseline":
        return train.mean(axis=0)
    if model in {"euclidean", "directed"}:
        design = _design(train_source_indices, receiver_indices, positions, model)
        target = _design([target_source_index], receiver_indices, positions, model)
        coefficients, *_ = np.linalg.lstsq(design, train.reshape(-1), rcond=None)
        return np.maximum(0.0, target @ coefficients)
    if model == "kernel":
        coords = positions[train_source_indices]
        pairwise = np.sqrt(np.square(coords[:, None, :] - coords[None, :, :]).sum(axis=2))
        positive = pairwise[pairwise > 0]
        if not len(positive):
            raise ValueError("kernel model needs distinct training sources")
        bandwidth = float(np.median(positive))
        distance = np.sqrt(np.square(coords - positions[target_source_index]).sum(axis=1))
        weights = np.exp(-np.square(distance) / (2.0 * bandwidth**2))
        weights /= weights.sum()
        return weights @ train
    raise ValueError(model)


def source_improvements(
    repeat1: np.ndarray, repeat2: np.ndarray, positions: np.ndarray
) -> dict[str, np.ndarray]:
    if repeat1.shape != repeat2.shape or repeat1.shape != (12, 20):
        raise ValueError("expected two 12x20 development matrices")
    source_indices = [STIM_LABELS.index(label) for label in DEVELOPMENT_LABELS]
    losses = {name: [] for name in ("baseline", "euclidean", "directed", "kernel")}
    for held_row, held_source in enumerate(source_indices):
        train_rows = [i for i in range(len(source_indices)) if i != held_row]
        train_sources = [source_indices[i] for i in train_rows]
        receiver_mask = np.arange(20) != held_source
        directional_losses = {name: [] for name in losses}
        for train_matrix, test_matrix in ((repeat1, repeat2), (repeat2, repeat1)):
            observed = test_matrix[held_row]
            for model in losses:
                predicted = predict_model(
                    train_matrix[train_rows], train_sources, held_source, positions, model
                )
                directional_losses[model].append(
                    float(np.mean(np.square(predicted[receiver_mask] - observed[receiver_mask])))
                )
        for model in losses:
            losses[model].append(float(np.mean(directional_losses[model])))
    baseline = np.asarray(losses["baseline"])
    if np.any(baseline <= 0):
        raise ValueError("non-positive baseline MSE")
    return {
        model: (baseline - np.asarray(losses[model])) / baseline
        for model in ("euclidean", "directed", "kernel")
    }


def exact_signflip_p(values: np.ndarray) -> float:
    values = np.asarray(values, dtype=np.float64)
    observed = float(values.mean())
    exceed = 0
    for signs in itertools.product((-1.0, 1.0), repeat=len(values)):
        exceed += float(np.mean(values * np.asarray(signs))) >= observed - 1e-15
    return exceed / (2 ** len(values))


def bootstrap_interval(values: np.ndarray, seed: int = 5593) -> tuple[float, float]:
    values = np.asarray(values, dtype=np.float64)
    rng = np.random.default_rng(seed)
    samples = rng.choice(values, size=(10_000, len(values)), replace=True).mean(axis=1)
    low, high = np.quantile(samples, (0.025, 0.975))
    return float(low), float(high)


def metric_diagnostics(mean_response: np.ndarray) -> dict[str, float]:
    source_indices = [STIM_LABELS.index(label) for label in DEVELOPMENT_LABELS]
    square = mean_response[:, source_indices]
    positive = square[square > 0]
    if not len(positive):
        return {"symmetry_median_abs": math.nan, "triangle_violation_fraction": math.nan}
    epsilon = float(np.median(positive)) * 1e-6
    probability = (square + epsilon) / (square + epsilon).sum(axis=1, keepdims=True)
    distance = -np.log(probability)
    symmetry = np.abs(distance - distance.T)
    mask = ~np.eye(len(distance), dtype=bool)
    violations = []
    for i, j, k in itertools.permutations(range(len(distance)), 3):
        violations.append(distance[i, k] > distance[i, j] + distance[j, k])
    return {
        "symmetry_median_abs": float(np.median(symmetry[mask])),
        "triangle_violation_fraction": float(np.mean(violations)),
    }


def analyze_matrices(
    repeat1: np.ndarray, repeat2: np.ndarray, positions: np.ndarray
) -> dict[str, object]:
    improvements = source_improvements(repeat1, repeat2, positions)
    stats = {}
    passes = {}
    for model, values in improvements.items():
        interval = bootstrap_interval(values)
        p_value = exact_signflip_p(values)
        stats[model] = {
            "mean_improvement": float(values.mean()),
            "exact_p": p_value,
            "bootstrap_95": list(interval),
            "source_improvements": values.tolist(),
        }
        passes[model] = values.mean() > 0 and p_value <= 0.01 and interval[0] > 0

    best_geometry = max(("euclidean", "directed"), key=lambda key: improvements[key].mean())
    kernel_advantage = improvements["kernel"] - improvements[best_geometry]
    kernel_advantage_p = exact_signflip_p(kernel_advantage)
    kernel_advantage_ci = bootstrap_interval(kernel_advantage, seed=5594)
    kernel_preferred = (
        passes["kernel"]
        and kernel_advantage.mean() > 0
        and kernel_advantage_p <= 0.01
        and kernel_advantage_ci[0] > 0
    )
    geometry_survives = passes["euclidean"] or passes["directed"]
    if kernel_preferred:
        status = "GENERAL_KERNEL_PREFERRED_DEVELOPMENT"
    elif geometry_survives:
        status = "SPATIAL_GEOMETRY_SURVIVES_DEVELOPMENT"
    elif passes["kernel"]:
        status = "GENERAL_KERNEL_SURVIVES_DEVELOPMENT"
    else:
        status = "VSD_SOURCE_GENERALIZATION_NOT_ESTABLISHED"

    off_diagonal = []
    for row, label in enumerate(DEVELOPMENT_LABELS):
        source = STIM_LABELS.index(label)
        for receiver in range(20):
            if receiver != source:
                off_diagonal.append((repeat1[row, receiver], repeat2[row, receiver]))
    repeat_correlation = float(np.corrcoef(np.asarray(off_diagonal).T)[0, 1])
    result = {
        "status": status,
        "development_sources": list(DEVELOPMENT_LABELS),
        "models": stats,
        "best_geometry": best_geometry,
        "kernel_advantage_mean": float(kernel_advantage.mean()),
        "kernel_advantage_exact_p": kernel_advantage_p,
        "kernel_advantage_bootstrap_95": list(kernel_advantage_ci),
        "repeat_correlation": repeat_correlation,
        "claim_ceiling": "single-animal mesoscale source-held-out development",
    }
    result.update(metric_diagnostics((repeat1 + repeat2) / 2.0))
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("zip_path", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    repeat1, repeat2, positions = load_development_matrices(args.zip_path)
    result = analyze_matrices(repeat1, repeat2, positions)
    payload = json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True)
    if args.output:
        args.output.write_text(payload + "\n", encoding="utf-8")
    print(payload)


if __name__ == "__main__":
    main()
