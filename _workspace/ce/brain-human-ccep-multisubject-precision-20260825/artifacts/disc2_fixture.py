"""Endpoint-blind analytic and geometry-null fixtures for BA-OBS-DISC2."""

from __future__ import annotations

import argparse
from concurrent.futures import ProcessPoolExecutor
import hashlib
import json
import os
from pathlib import Path
import sys
from typing import Any, Sequence

for _thread_variable in (
    "OMP_NUM_THREADS",
    "OPENBLAS_NUM_THREADS",
    "MKL_NUM_THREADS",
    "VECLIB_MAXIMUM_THREADS",
    "NUMEXPR_NUM_THREADS",
):
    os.environ.setdefault(_thread_variable, "1")

import numpy as np

from disc2_ccep_core import (
    FitError,
    SourceData,
    candidate_mean,
    fit_candidate,
)
from disc2_ccep_run import (
    ARTIFACTS,
    CONTRACT,
    atomic_write_json,
    d0_cross_validated_selection,
    file_sha256,
    utc_now,
)


FIXTURE_RECEIPT = ARTIFACTS / "pre-d0-fixture-receipt-v2.json"
FIXTURE_SEED = "BA-OBS-DISC2::pre-D0-fixture::v2-unseen-after-v1"


def seed_u64(label: str) -> int:
    return int.from_bytes(hashlib.sha256(label.encode("utf-8")).digest()[:8], "big")


def synthetic_sources(
    *,
    replicate: int,
    generating_candidate: str,
    parameters: np.ndarray,
    noise_scale: float,
) -> tuple[list[SourceData], dict[str, int]]:
    sources = []
    folds: dict[str, int] = {}
    for participant_index in range(24):
        subject = f"fixture-sub-{participant_index:02d}"
        fold = participant_index % 6
        folds[subject] = fold
        age_tilde = (-0.75, -0.25, 0.25, 0.75)[participant_index // 6]
        generator = np.random.Generator(
            np.random.PCG64(
                seed_u64(
                    f"{FIXTURE_SEED}::{replicate}::{generating_candidate}::{participant_index}"
                )
            )
        )
        anchor_delta = generator.normal(0.0, 1.0, size=(4, 3))
        query_delta = generator.normal(0.0, 1.0, size=(12, 3))
        # Avoid a degenerate concentration at the chart origin.
        anchor_delta[:, 0] += np.asarray((-1.4, -0.5, 0.5, 1.4))
        query_delta[:, 0] += np.linspace(-1.5, 1.5, 12)
        source_offset = generator.normal(0.0, 0.8)
        anchor_z = candidate_mean(
            generating_candidate, parameters, age_tilde, anchor_delta
        ) + source_offset
        query_z = candidate_mean(
            generating_candidate, parameters, age_tilde, query_delta
        ) + source_offset
        if noise_scale > 0.0:
            anchor_z = anchor_z + generator.normal(0.0, noise_scale, size=(4, 5))
            query_z = query_z + generator.normal(0.0, noise_scale, size=(12, 5))
        sources.append(
            SourceData(
                subject=subject,
                source_id=f"fixture-source-{participant_index:02d}",
                age_tilde=age_tilde,
                anchor_delta=anchor_delta,
                query_delta=query_delta,
                anchor_z=anchor_z,
                query_z=query_z,
            ).validated()
        )
    return sources, folds


def analytic_family_fixture(candidate: str, parameters: np.ndarray) -> dict[str, Any]:
    sources, _ = synthetic_sources(
        replicate=-1,
        generating_candidate=candidate,
        parameters=parameters,
        noise_scale=0.015,
    )
    baseline = fit_candidate(sources, "S0")
    generating = fit_candidate(sources, candidate)
    improvement = 1.0 - generating.objective / baseline.objective
    return {
        "generating_candidate": candidate,
        "generating_parameters": parameters.tolist(),
        "baseline_objective": baseline.objective,
        "generating_objective": generating.objective,
        "relative_improvement": improvement,
        "baseline_fit": baseline.as_dict(),
        "generating_fit": generating.as_dict(),
        "status": "PASS" if improvement > 0.0 else "FAIL",
    }


def run_null_replicate(replicate: int) -> dict[str, Any]:
    parameters = np.asarray([0.25, -0.12, 0.08, 0.06], dtype=np.float64)
    sources, folds = synthetic_sources(
        replicate=replicate,
        generating_candidate="S0",
        parameters=parameters,
        noise_scale=0.25,
    )
    try:
        result = d0_cross_validated_selection(sources, folds)
    except FitError as error:
        return {
            "replicate": replicate,
            "status": "FIXTURE_NUMERICAL_STOP",
            "error": str(error),
            "winner": None,
        }
    return {
        "replicate": replicate,
        "status": result["status"],
        "winner": result["winner"],
        "survivors": result["survivors"],
        "candidate_summary": {
            name: {
                "admissible": value["admissible"],
                "cv_relative_improvement": value.get("cv_relative_improvement"),
                "fold_wins": value.get("fold_wins"),
                "survives": value.get("survives"),
            }
            for name, value in result["candidates"].items()
            if name != "S0"
        },
    }


def run_fixtures(replicates: int, workers: int, *, final: bool) -> dict[str, Any]:
    if replicates <= 0:
        raise ValueError("replicates must be positive")
    if final and replicates != 64:
        raise ValueError("the final frozen fixture requires exactly 64 null replicates")
    cable = analytic_family_fixture(
        "SC", np.asarray([0.30, -0.12, 0.09, 0.04, 1.20], dtype=np.float64)
    )
    heat = analytic_family_fixture(
        "SH0", np.asarray([0.30, -0.12, 0.09, 0.04, 0.70], dtype=np.float64)
    )
    if workers == 1:
        null_results = [run_null_replicate(index) for index in range(replicates)]
    else:
        with ProcessPoolExecutor(max_workers=workers) as executor:
            null_results = list(executor.map(run_null_replicate, range(replicates)))
    false_selections = sum(result.get("winner") is not None for result in null_results)
    numerical_stops = sum(
        result.get("status") == "FIXTURE_NUMERICAL_STOP" for result in null_results
    )
    fixture_pass = (
        cable["status"] == "PASS"
        and heat["status"] == "PASS"
        and numerical_stops == 0
        and (false_selections <= 2 if final else True)
    )
    receipt = {
        "schema": "BA-OBS-DISC2-pre-D0-fixture-v2",
        "created_at_utc": utc_now(),
        "contract_sha256": file_sha256(CONTRACT),
        "core_code_sha256": file_sha256(ARTIFACTS / "disc2_ccep_core.py"),
        "runner_code_sha256": file_sha256(ARTIFACTS / "disc2_ccep_run.py"),
        "fixture_code_sha256": file_sha256(Path(__file__)),
        "analytic_cable": cable,
        "analytic_heat": heat,
        "null_replicates": replicates,
        "null_false_selections": false_selections,
        "null_numerical_stops": numerical_stops,
        "null_results": null_results,
        "final_fixture": final,
        "status": "PASS" if fixture_pass else "FIXTURE_STOP",
    }
    if final:
        atomic_write_json(FIXTURE_RECEIPT, receipt)
    return receipt


def make_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--replicates", type=int, default=1)
    parser.add_argument("--workers", type=int, default=max(1, min(4, os.cpu_count() or 1)))
    parser.add_argument("--final", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = make_parser().parse_args(argv)
    try:
        receipt = run_fixtures(args.replicates, args.workers, final=args.final)
    except BaseException as error:
        print(
            json.dumps(
                {"status": "STOP", "error_type": type(error).__name__, "error": str(error)}
            ),
            file=sys.stderr,
            flush=True,
        )
        return 2
    summary = {
        key: receipt[key]
        for key in (
            "status",
            "null_replicates",
            "null_false_selections",
            "null_numerical_stops",
        )
    }
    summary["analytic_cable_improvement"] = receipt["analytic_cable"][
        "relative_improvement"
    ]
    summary["analytic_heat_improvement"] = receipt["analytic_heat"][
        "relative_improvement"
    ]
    print(json.dumps(summary, sort_keys=True), flush=True)
    return 0 if receipt["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
