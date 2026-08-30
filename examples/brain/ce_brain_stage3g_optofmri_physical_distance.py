"""Preregistered Stage 3G R2 physical source-distance analysis."""

from __future__ import annotations

import argparse
import itertools
import json
from pathlib import Path

import numpy as np
from scipy.stats import spearmanr

from examples.brain.ce_brain_stage3f_optofmri_state_rdm import (
    DEVELOPMENT,
    SITES,
    exact_signflip_p,
    load_nifti,
    response_rdms,
)
from examples.brain.ce_brain_stage3g_optofmri_registration import SOURCE_BASES


PAIR_INDICES = tuple(itertools.combinations(range(len(SITES)), 2))


def left_source_labels() -> dict[str, tuple[int, ...]]:
    result = {}
    for name, bases in SOURCE_BASES.items():
        result[name] = tuple(
            base + 2000 + layer
            for base, layer_count in bases
            for layer in range(layer_count + 1)
        )
    return result


def source_centroids(
    labels_xyz: np.ndarray,
    spacing: tuple[float, float, float],
    origin: tuple[float, float, float],
    direction: tuple[float, ...],
) -> np.ndarray:
    direction_matrix = np.asarray(direction, dtype=float).reshape(3, 3)
    spacing_array = np.asarray(spacing, dtype=float)
    origin_array = np.asarray(origin, dtype=float)
    centroids = []
    for name in SITES:
        indices = np.argwhere(np.isin(labels_xyz, left_source_labels()[name]))
        if not len(indices):
            raise ValueError(f"registered T2 atlas has no voxels for {name}")
        mean_index = indices.mean(axis=0)
        physical = origin_array + direction_matrix @ (mean_index * spacing_array)
        centroids.append(physical)
    return np.asarray(centroids, dtype=float)


def distance_vector(centroids: np.ndarray) -> np.ndarray:
    return np.asarray(
        [np.linalg.norm(centroids[left] - centroids[right]) for left, right in PAIR_INDICES],
        dtype=float,
    )


def _load_registered_centroids(path: Path) -> np.ndarray:
    try:
        import SimpleITK as sitk
    except ImportError as error:  # pragma: no cover - environment-dependent
        raise RuntimeError("SimpleITK is required for registered NIfTI inputs") from error

    image = sitk.ReadImage(str(path))
    labels_xyz = np.transpose(sitk.GetArrayViewFromImage(image), (2, 1, 0))
    return source_centroids(
        labels_xyz,
        tuple(image.GetSpacing()),
        tuple(image.GetOrigin()),
        tuple(image.GetDirection()),
    )


def _load_epi_atlas(path: Path) -> np.ndarray:
    try:
        import SimpleITK as sitk
    except ImportError as error:  # pragma: no cover - environment-dependent
        raise RuntimeError("SimpleITK is required for registered NIfTI inputs") from error

    return np.transpose(sitk.GetArrayFromImage(sitk.ReadImage(str(path))), (2, 1, 0))


def subject_result(subject: str, input_root: Path, registration_root: Path) -> dict[str, object]:
    baseline_maps = []
    raw_by_site: dict[str, list[tuple[np.ndarray, np.ndarray]]] = {}
    for site in SITES:
        files = sorted(
            (input_root / subject / f"func_{site}").glob("*.nii.gz"),
            key=lambda path: int(path.name.removesuffix(".nii.gz")),
        )[:5]
        if len(files) != 5:
            raise ValueError(f"expected five trials: {subject} {site}")
        rows = []
        for path in files:
            data = load_nifti(path)
            baseline = data[..., :40].mean(axis=3)
            response = data[..., 40:80].mean(axis=3)
            baseline_maps.append(baseline)
            rows.append((baseline, response))
        raw_by_site[site] = rows

    subject_baseline = np.mean(baseline_maps, axis=0)
    positive = subject_baseline[subject_baseline > 0]
    if not len(positive):
        raise ValueError(f"no positive baseline voxels: {subject}")
    threshold = 0.20 * float(np.percentile(positive, 95))
    atlas_epi = _load_epi_atlas(registration_root / subject / "atlas_in_EPI.nii.gz")
    if atlas_epi.shape != subject_baseline.shape:
        raise ValueError(f"atlas/EPI shape mismatch: {subject}")
    mask = (atlas_epi > 0) & (subject_baseline > threshold)
    if int(mask.sum()) < 1000:
        raise ValueError(f"registered brain mask too small: {subject}")

    odd_maps = []
    even_maps = []
    for site in SITES:
        maps = []
        for baseline, response in raw_by_site[site]:
            percent = -100.0 * (response[mask] - baseline[mask]) / baseline[mask]
            maps.append(np.asarray(percent, dtype=np.float32))
        odd_maps.append(np.mean([maps[0], maps[2], maps[4]], axis=0))
        even_maps.append(np.mean([maps[1], maps[3]], axis=0))
    odd_rdm, even_rdm, cross_rdm = response_rdms(np.stack(odd_maps), np.stack(even_maps))
    centroids = _load_registered_centroids(
        registration_root / subject / "atlas_in_T2.nii.gz"
    )
    physical = distance_vector(centroids)
    return {
        "subject": subject,
        "genotype": subject.split("-", 1)[0],
        "mask_voxels": int(mask.sum()),
        "source_centroids": {name: centroids[index].tolist() for index, name in enumerate(SITES)},
        "physical_distance_rdm": physical.tolist(),
        "odd_rdm": odd_rdm.tolist(),
        "even_rdm": even_rdm.tolist(),
        "cross_half_rdm": cross_rdm.tolist(),
        "repeat_reliability": float(spearmanr(odd_rdm, even_rdm).statistic),
        "physical_distance_rho": float(spearmanr(physical, cross_rdm).statistic),
    }


def exact_source_permutation_p(
    distances: np.ndarray,
    responses: np.ndarray,
) -> float:
    observed = float(
        np.mean([spearmanr(distance, response).statistic for distance, response in zip(distances, responses)])
    )
    exceed = 0
    total = 0
    for permutation in itertools.permutations(range(len(SITES))):
        permuted_pairs = tuple((permutation[left], permutation[right]) for left, right in PAIR_INDICES)
        scores = []
        for distance, response in zip(distances, responses):
            matrix = np.zeros((len(SITES), len(SITES)), dtype=float)
            for value, (left, right) in zip(distance, PAIR_INDICES):
                matrix[left, right] = matrix[right, left] = value
            candidate = np.asarray([matrix[left, right] for left, right in permuted_pairs])
            scores.append(spearmanr(candidate, response).statistic)
        exceed += float(np.mean(scores)) >= observed - 1e-12
        total += 1
    return exceed / total


def _genotype_difference_p(scores: np.ndarray, labels: np.ndarray) -> float:
    first = scores[labels == "Thy1"]
    second = scores[labels == "VGAT"]
    observed = abs(float(first.mean() - second.mean()))
    exceed = 0
    total = 0
    for indices in itertools.combinations(range(len(scores)), len(first)):
        mask = np.zeros(len(scores), dtype=bool)
        mask[list(indices)] = True
        difference = abs(float(scores[mask].mean() - scores[~mask].mean()))
        exceed += difference >= observed - 1e-12
        total += 1
    return exceed / total


def analyze(rows: list[dict[str, object]]) -> dict[str, object]:
    labels = np.asarray([row["genotype"] for row in rows])
    reliabilities = np.asarray([row["repeat_reliability"] for row in rows], dtype=float)
    scores = np.asarray([row["physical_distance_rho"] for row in rows], dtype=float)
    distances = np.asarray([row["physical_distance_rdm"] for row in rows], dtype=float)
    responses = np.asarray([row["cross_half_rdm"] for row in rows], dtype=float)
    gates = {}
    for genotype in ("Thy1", "VGAT"):
        selected = labels == genotype
        rel = reliabilities[selected]
        association = scores[selected]
        reliability_p = exact_signflip_p(rel)
        association_p = exact_signflip_p(association)
        source_p = exact_source_permutation_p(distances[selected], responses[selected])
        reliability_pass = bool(np.median(rel) >= 0.30 and reliability_p <= 0.05)
        association_pass = bool(
            np.median(association) >= 0.30 and association_p <= 0.05 and source_p <= 0.05
        )
        gates[genotype] = {
            "repeat_reliability": {
                "values": rel.tolist(),
                "median": float(np.median(rel)),
                "signflip_p": reliability_p,
                "passed": reliability_pass,
            },
            "physical_distance": {
                "values": association.tolist(),
                "median": float(np.median(association)),
                "signflip_p": association_p,
                "source_permutation_p": source_p,
                "passed": association_pass,
            },
            "passed": reliability_pass and association_pass,
        }

    passed_count = sum(bool(gates[name]["passed"]) for name in gates)
    if passed_count == 2:
        status = "COMMON_PHYSICAL_DISTANCE_CANDIDATE"
    elif passed_count == 1:
        status = "CONDITION_LIMITED_PHYSICAL_DISTANCE_CANDIDATE"
    else:
        status = "PHYSICAL_DISTANCE_GEOMETRY_NOT_ESTABLISHED"
    difference = float(scores[labels == "Thy1"].mean() - scores[labels == "VGAT"].mean())
    difference_p = _genotype_difference_p(scores, labels)
    interpretable_difference = bool(
        all(gates[name]["repeat_reliability"]["passed"] for name in gates)
        and abs(difference) >= 0.20
        and difference_p <= 0.05
    )
    return {
        "status": status,
        "gates": gates,
        "genotype_mean_rho_difference_thy1_minus_vgat": difference,
        "genotype_permutation_p_two_sided": difference_p,
        "genotype_difference_interpretable": interpretable_difference,
        "calibration_confirmation_opened": False,
        "claim_ceiling": "six-source scale physical-distance/response-pattern association",
        "subjects": rows,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-root", type=Path, required=True)
    parser.add_argument("--registration-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    rows = []
    for genotype in ("Thy1", "VGAT"):
        for subject in DEVELOPMENT[genotype]:
            print(f"analyzing {subject}", flush=True)
            rows.append(subject_result(subject, args.input_root, args.registration_root))
    result = analyze(rows)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
