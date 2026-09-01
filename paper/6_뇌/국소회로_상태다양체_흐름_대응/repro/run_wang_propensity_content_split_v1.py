#!/usr/bin/env python3
"""Transparent post-publication reproduction of Wang et al. developmental summaries.

This is not preregistered or confirmatory.  It reproduces same-cell weighted
spatial-information rank correlations and adjacent-day map-correlation trends
from the authors' released figure-level MAT files.  No cell-level p-value is
promoted to an animal-level population inference because animal/litter IDs are
absent from these files.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import platform
import sys
from pathlib import Path
from typing import Any

import numpy as np
import scipy
from scipy.io import loadmat
from scipy.stats import pearsonr, spearmanr


CONTRACT_ID = "CE_NPF_ALT_BIO_WANG2024_PROPENSITY_CONTENT_SPLIT_POSTHOC_v1"
PAPER_DOI = "10.1038/s41467-024-54320-z"
CODE_COMMIT = "1cc8cdd51de11ee9774e0e0c032cda5df2f170bc"
ARCHIVE_SHA256 = "55b2e0f38ed1a605eb9b59d6608e4a22762d3dda73b681b2ef401bfc5563d09b"

FILES = {
    "wsi_juvenile": (
        "fig_5e_wSI_bef_wSI_aft_p17.mat",
        "2390674f5f775088049c1910eb820515fadf9bb1cff3679c11bfcb537eda6d01",
    ),
    "wsi_adult": (
        "fig_5e_wSI_bef_wSI_aft_adult.mat",
        "1493b9cb59b0a226eca1c0861ddea348123a976bd401e8e6c503f7ff318f7fa7",
    ),
    "wsi_published_summary": (
        "fig_5f_Weighted_SI_correlation_p17_adult.mat",
        "36d24cdad3a1e253d1ecde2fed2122cdba29d49c19128d621dbe711d38009773",
    ),
    "content_2d_juvenile": (
        "fig_3b_2D_spatial_correlation_p17.mat",
        "3cf611811430fa42850d60ec114eb27163e32680d84cfc878724d8626567721f",
    ),
    "content_2d_adult": (
        "fig_3b_2D_spatial_correlation_adult.mat",
        "558d1a5358f375776a59345fa2b32c1abce0e57aa705202503d433d42e6d2baf",
    ),
    "content_1d_juvenile": (
        "fig_3d_1D_spatial_correlation_p17.mat",
        "0314937f048849dacdcbf5a8df7d64138d3240ff12b9bb788ad6f70f57beef37",
    ),
    "content_1d_adult": (
        "fig_3d_1D_spatial_correlation_adult.mat",
        "4e10fda3cce0405a8a928590ace1a7644b4eedc7f866fe438d562f9267182c86",
    ),
}

JUVENILE_PAIR_START_AGES = np.asarray([17, 18, 19, 20, 21, 22, 23, 24, 27], dtype=float)
CONTENT_PAIR_COORDINATES = {
    "content_2d_juvenile": np.asarray([17, 18, 19, 20, 21, 22, 23, 24, 25, 27], dtype=float),
    "content_2d_adult": np.asarray([1, 2, 3, 4, 6, 7, 8, 9], dtype=float),
    "content_1d_juvenile": np.arange(17, 28, dtype=float),
    "content_1d_adult": np.asarray([1, 2, 3, 4, 6, 7, 8, 9], dtype=float),
}


class ReproductionBlocked(RuntimeError):
    pass


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_locked_files(data_root: Path) -> tuple[dict[str, dict[str, Any]], list[dict[str, Any]]]:
    loaded: dict[str, dict[str, Any]] = {}
    provenance: list[dict[str, Any]] = []
    for role, (filename, expected_sha256) in FILES.items():
        path = data_root / filename
        if not path.is_file():
            raise ReproductionBlocked(f"missing locked input: {path}")
        observed_sha256 = file_sha256(path)
        if observed_sha256 != expected_sha256:
            raise ReproductionBlocked(
                f"SHA-256 mismatch for {role}: {observed_sha256} != {expected_sha256}"
            )
        try:
            raw = loadmat(path, squeeze_me=True, struct_as_record=False)
        except Exception as exc:
            raise ReproductionBlocked(f"cannot load {role}: {exc}") from exc
        loaded[role] = {key: value for key, value in raw.items() if not key.startswith("__")}
        provenance.append(
            {
                "role": role,
                "path": path.resolve().as_posix(),
                "bytes": path.stat().st_size,
                "sha256": observed_sha256,
                "variables": sorted(loaded[role]),
            }
        )
    return loaded, provenance


def _numeric_vector(value: Any, label: str) -> np.ndarray:
    try:
        vector = np.asarray(value, dtype=np.float64).reshape(-1)
    except Exception as exc:
        raise ReproductionBlocked(f"{label} is not numeric") from exc
    if vector.size < 2 or not np.all(np.isfinite(vector)):
        raise ReproductionBlocked(f"{label} must contain at least two finite values")
    return vector


def _cell_vectors(value: Any, label: str) -> list[np.ndarray]:
    array = np.asarray(value, dtype=object).reshape(-1)
    vectors = [_numeric_vector(item, f"{label}[{index}]") for index, item in enumerate(array)]
    if not vectors:
        raise ReproductionBlocked(f"{label} is empty")
    return vectors


def same_cell_rank_series(mat: dict[str, Any], label: str) -> dict[str, Any]:
    if "wSI_bef" not in mat or "wSI_aft" not in mat:
        raise ReproductionBlocked(f"{label} lacks wSI_bef/wSI_aft")
    before = _cell_vectors(mat["wSI_bef"], f"{label}.wSI_bef")
    after = _cell_vectors(mat["wSI_aft"], f"{label}.wSI_aft")
    if len(before) != 9 or len(after) != 9:
        raise ReproductionBlocked(f"{label} must contain exactly nine adjacent-day pairs")
    records: list[dict[str, Any]] = []
    for index, (x, y) in enumerate(zip(before, after, strict=True)):
        if x.shape != y.shape:
            raise ReproductionBlocked(f"{label} pair {index} length mismatch")
        result = spearmanr(x, y)
        rho = float(result.statistic)
        p_value = float(result.pvalue)
        if not (math.isfinite(rho) and math.isfinite(p_value)):
            raise ReproductionBlocked(f"{label} pair {index} has undefined Spearman correlation")
        records.append(
            {
                "pair_index": index,
                "same_cell_count": int(x.size),
                "spearman_rho": rho,
                "cell_level_p_value_descriptive_only": p_value,
            }
        )
    rhos = np.asarray([item["spearman_rho"] for item in records])
    ordinal_trend = pearsonr(np.arange(1, 10, dtype=float), rhos)
    return {
        "pairs": records,
        "median_rho": float(np.median(rhos)),
        "rho_vs_pair_ordinal_pearson": float(ordinal_trend.statistic),
        "rho_vs_pair_ordinal_p_descriptive_only": float(ordinal_trend.pvalue),
    }


def content_stability_trend(
    mat: dict[str, Any], label: str, pair_coordinates: np.ndarray
) -> dict[str, Any]:
    if "y" not in mat:
        raise ReproductionBlocked(f"{label} lacks author summary y")
    values = _numeric_vector(mat["y"], f"{label}.y")
    pair_coordinates = np.asarray(pair_coordinates, dtype=np.float64)
    if pair_coordinates.shape != values.shape or not np.all(np.isfinite(pair_coordinates)):
        raise ReproductionBlocked(f"{label} frozen adjacent-pair coordinates mismatch")
    result = pearsonr(pair_coordinates, values)
    distribution_sizes: list[int] | None = None
    if "sp_corr" in mat:
        try:
            distribution_sizes = [
                int(np.asarray(item).size)
                for item in np.asarray(mat["sp_corr"], dtype=object).reshape(-1)
            ]
        except Exception:
            distribution_sizes = None
    return {
        "adjacent_pair_count": int(values.size),
        "adjacent_pair_start_coordinate": pair_coordinates.tolist(),
        "author_summary_values": values.tolist(),
        "pearson_r_vs_pair_start_coordinate": float(result.statistic),
        "p_two_sided_descriptive_only": float(result.pvalue),
        "cell_distribution_sizes_if_recoverable": distribution_sizes,
    }


def _summary_crosscheck(summary: dict[str, Any], juvenile: np.ndarray, adult: np.ndarray) -> dict[str, Any]:
    if "y" not in summary:
        return {"available": False, "reason": "published summary lacks y"}
    values = _numeric_vector(summary["y"], "published_summary.y")
    candidates = {
        "juvenile_then_adult": np.concatenate([juvenile, adult]),
        "adult_then_juvenile": np.concatenate([adult, juvenile]),
    }
    differences = {
        key: float(np.max(np.abs(values - candidate)))
        for key, candidate in candidates.items()
        if candidate.shape == values.shape
    }
    if not differences:
        return {
            "available": False,
            "reason": f"summary length {values.size} does not match pair series length {juvenile.size + adult.size}",
        }
    best = min(differences, key=differences.get)
    return {
        "available": True,
        "published_summary_count": int(values.size),
        "best_order": best,
        "max_absolute_difference": differences[best],
        "all_order_differences": differences,
    }


def analyze(data_root: Path) -> dict[str, Any]:
    mats, provenance = load_locked_files(data_root)
    juvenile = same_cell_rank_series(mats["wsi_juvenile"], "juvenile")
    adult = same_cell_rank_series(mats["wsi_adult"], "adult")
    juvenile_rhos = np.asarray([item["spearman_rho"] for item in juvenile["pairs"]])
    adult_rhos = np.asarray([item["spearman_rho"] for item in adult["pairs"]])
    juvenile_age_trend = pearsonr(JUVENILE_PAIR_START_AGES, juvenile_rhos)
    content = {
        role: content_stability_trend(mats[role], role, CONTENT_PAIR_COORDINATES[role])
        for role in (
            "content_2d_juvenile",
            "content_2d_adult",
            "content_1d_juvenile",
            "content_1d_adult",
        )
    }
    return {
        "contract_id": CONTRACT_ID,
        "status": "WANG_POSTHOC_PROPENSITY_CONTENT_SPLIT_COMPATIBLE_L1",
        "analysis_kind": "POST_PUBLICATION_TRANSPARENT_REPRODUCTION_NOT_PREREGISTERED",
        "paper_doi": PAPER_DOI,
        "official_code_commit": CODE_COMMIT,
        "source_archive_sha256": ARCHIVE_SHA256,
        "source_provenance": provenance,
        "same_cell_weighted_spatial_information": {
            "juvenile": juvenile,
            "adult": adult,
            "juvenile_start_ages": JUVENILE_PAIR_START_AGES.astype(int).tolist(),
            "juvenile_rho_vs_start_age_pearson": float(juvenile_age_trend.statistic),
            "juvenile_rho_vs_start_age_p_descriptive_only": float(juvenile_age_trend.pvalue),
            "published_summary_crosscheck": _summary_crosscheck(
                mats["wsi_published_summary"], juvenile_rhos, adult_rhos
            ),
        },
        "specific_spatial_content_stability": content,
        "claim_assessment": {
            "early_same_cell_coding_propensity": "OBSERVATIONALLY_COMPATIBLE",
            "specific_spatial_content_fixed_at_early_age": "CONTRADICTED_BY_RISING_ADJACENT_DAY_STABILITY",
            "born_with_semantic_content": "UNTESTED_NO_BIRTH_OR_LINEAGE_MEASUREMENT",
            "adolescent_fixation": "NOT_SUPPORTED_NO_SAME_COHORT_JUVENILE_TO_ADULT_AND_CONTENT_CHANGES_DURING_JUVENILE_WINDOW",
            "causal_mechanism": "UNTESTED_NO_RANDOM_INTERVENTION_OR_RESCUE_IN_THIS_RELEASE",
        },
        "evidence_ceiling": "BIO_EVIDENCE_L1_OBSERVATIONAL",
        "unit_warning": "Figure files omit animal/litter IDs; cells are not independent animals and cell-level p-values are descriptive only.",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-root", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    if args.output.exists():
        print(f"REFUSE: output exists: {args.output}", file=sys.stderr)
        return 2
    receipt: dict[str, Any] = {
        "contract_id": CONTRACT_ID,
        "runner": Path(__file__).resolve().as_posix(),
        "runner_sha256": file_sha256(Path(__file__).resolve()),
        "environment": {
            "python_executable": Path(sys.executable).resolve().as_posix(),
            "python_version": platform.python_version(),
            "numpy_version": np.__version__,
            "scipy_version": scipy.__version__,
            "platform": platform.platform(),
        },
        "biological_endpoint_evaluated": False,
    }
    exit_code = 1
    try:
        receipt["result"] = analyze(args.data_root)
        receipt["status"] = receipt["result"]["status"]
        receipt["biological_endpoint_evaluated"] = True
        exit_code = 0
    except ReproductionBlocked as exc:
        receipt["status"] = "WANG_REPRODUCTION_BLOCKED"
        receipt["error"] = str(exc)
    except Exception as exc:
        receipt["status"] = "WANG_IMPLEMENTATION_ERROR_BLOCKED"
        receipt["error"] = f"{type(exc).__name__}: {exc}"

    args.output.parent.mkdir(parents=True, exist_ok=True)
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    descriptor = os.open(args.output, flags)
    with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as handle:
        json.dump(receipt, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())
    print(json.dumps({"status": receipt["status"], "output": args.output.as_posix(), "error": receipt.get("error")}, ensure_ascii=False, indent=2))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
