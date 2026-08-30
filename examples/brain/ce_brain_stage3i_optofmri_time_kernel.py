"""Preregistered Stage 3I minimal spatiotemporal opto-fMRI kernel."""

from __future__ import annotations

import argparse
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
from examples.brain.ce_brain_stage3g_optofmri_physical_distance import _load_epi_atlas


BASELINE = slice(0, 40)
RESPONSE = slice(40, 100)


def percent_trajectory(data: np.ndarray, mask: np.ndarray) -> np.ndarray:
    if data.ndim != 4 or data.shape[-1] < RESPONSE.stop:
        raise ValueError("time series must contain at least 100 samples")
    baseline = data[..., BASELINE].mean(axis=3)
    if np.any(baseline[mask] <= 0):
        raise ValueError("masked baseline must be positive")
    return np.asarray(
        -100.0
        * (data[..., RESPONSE][mask] - baseline[mask, np.newaxis])
        / baseline[mask, np.newaxis],
        dtype=np.float32,
    )


def subject_result(subject: str, input_root: Path, registration_root: Path) -> dict[str, object]:
    paths_by_site: dict[str, list[Path]] = {}
    baselines = []
    for site in SITES:
        paths = sorted(
            (input_root / subject / f"func_{site}").glob("*.nii.gz"),
            key=lambda path: int(path.name.removesuffix(".nii.gz")),
        )[:5]
        if len(paths) != 5:
            raise ValueError(f"expected five trials: {subject} {site}")
        paths_by_site[site] = paths
        for path in paths:
            data = load_nifti(path)
            if data.shape != (96, 48, 18, 120):
                raise ValueError(f"unexpected shape {data.shape}: {path}")
            baselines.append(data[..., BASELINE].mean(axis=3))

    subject_baseline = np.mean(baselines, axis=0)
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

    odd = []
    even = []
    for site in SITES:
        trials = [percent_trajectory(load_nifti(path), mask) for path in paths_by_site[site]]
        odd.append(np.mean([trials[0], trials[2], trials[4]], axis=0).reshape(-1))
        even.append(np.mean([trials[1], trials[3]], axis=0).reshape(-1))
    odd_rdm, even_rdm, cross_rdm = response_rdms(np.stack(odd), np.stack(even))
    return {
        "subject": subject,
        "genotype": subject.split("-", 1)[0],
        "mask_voxels": int(mask.sum()),
        "time_samples": RESPONSE.stop - RESPONSE.start,
        "repeat_reliability": float(spearmanr(odd_rdm, even_rdm).statistic),
        "odd_rdm": odd_rdm.tolist(),
        "even_rdm": even_rdm.tolist(),
        "cross_half_rdm": cross_rdm.tolist(),
    }


def analyze(rows: list[dict[str, object]]) -> dict[str, object]:
    gates = {}
    for genotype in ("Thy1", "VGAT"):
        values = np.asarray(
            [row["repeat_reliability"] for row in rows if row["genotype"] == genotype],
            dtype=float,
        )
        p_value = exact_signflip_p(values)
        gates[genotype] = {
            "values": values.tolist(),
            "median": float(np.median(values)),
            "signflip_p": p_value,
            "passed": bool(np.median(values) >= 0.30 and p_value <= 0.05),
        }
    return {
        "status": (
            "SPATIOTEMPORAL_KERNEL_REPEATABLE"
            if all(gate["passed"] for gate in gates.values())
            else "SPATIOTEMPORAL_KERNEL_REPEATABILITY_NOT_ESTABLISHED"
        ),
        "gates": gates,
        "subjects": rows,
        "calibration_confirmation_opened": False,
        "claim_ceiling": "minimal registered-raw six-source K(j,t|i) response representation",
        "apparatus_limitation": "slice timing, motion correction, and paper GLM not yet reproduced",
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
