"""Preregistered DANDI 000559 dopamine-intervention persistence analysis."""

from __future__ import annotations

import argparse
import csv
import itertools
import json
import math
from collections import defaultdict
from pathlib import Path
from typing import Iterable, Mapping


SHARED_COHORTS = (0, 3, 5)
POST_SESSIONS = (3, 4)


def eligible(row: Mapping[str, object]) -> bool:
    """Return whether a processed-summary row belongs to the locked apparatus."""
    try:
        cohort = int(row["cohort"])
        target = int(row["target_syllable"])
        syllable = int(row["syllable"])
        stim_duration = float(row["stim_duration"])
        bin_start = float(row["bin_start"])
        bin_end = float(row["bin_end"])
    except (KeyError, TypeError, ValueError):
        return False
    rle = str(row.get("rle", "")).strip().lower() in {"true", "1"}
    treatment = row.get("area") == "snc (axon)" and row.get("opsin") == "chr2"
    control = row.get("area") == "ctrl" and row.get("opsin") == "ctrl"
    return (
        row.get("experiment_type") == "reinforcement"
        and not rle
        and cohort in SHARED_COHORTS
        and (treatment or control)
        and math.isclose(stim_duration, 0.25)
        and syllable == target
        and math.isclose(bin_start, 1770.0)
        and math.isclose(bin_end, 1800.0)
    )


def animal_endpoints(rows: Iterable[Mapping[str, object]]) -> list[dict[str, object]]:
    """Collapse repeated target sessions to one endpoint per animal and phase."""
    grouped: dict[tuple[str, int, int, str], list[float]] = defaultdict(list)
    for row in rows:
        if not eligible(row):
            continue
        session = int(row["session_number"])
        if session not in POST_SESSIONS:
            continue
        value = float(row["change_usage"])
        if not math.isfinite(value):
            raise ValueError("non-finite change_usage in eligible row")
        group = "chr2" if row["opsin"] == "chr2" else "ctrl"
        key = (str(row["mouse_id"]), int(row["cohort"]), session, group)
        grouped[key].append(value)

    by_mouse: dict[tuple[str, int, str], dict[int, float]] = defaultdict(dict)
    for (mouse, cohort, session, group), values in grouped.items():
        by_mouse[(mouse, cohort, group)][session] = sum(values) / len(values)

    endpoints: list[dict[str, object]] = []
    for (mouse, cohort, group), sessions in sorted(by_mouse.items()):
        if set(sessions) != set(POST_SESSIONS):
            raise ValueError(f"missing post session for {mouse}: {sorted(sessions)}")
        endpoints.append(
            {
                "mouse_id": mouse,
                "cohort": cohort,
                "group": group,
                "post_mean": sum(sessions.values()) / len(POST_SESSIONS),
                "session4": sessions[4],
            }
        )
    return endpoints


def cohort_adjusted_beta(
    endpoints: list[Mapping[str, object]], outcome: str, labels: list[int] | None = None
) -> float:
    if labels is None:
        labels = [1 if row["group"] == "chr2" else 0 for row in endpoints]
    if len(labels) != len(endpoints):
        raise ValueError("label count mismatch")
    x_res: list[float] = []
    y_res: list[float] = []
    cohorts = sorted({int(row["cohort"]) for row in endpoints})
    for cohort in cohorts:
        idx = [i for i, row in enumerate(endpoints) if int(row["cohort"]) == cohort]
        xs = [float(labels[i]) for i in idx]
        ys = [float(endpoints[i][outcome]) for i in idx]
        # A leave-one-animal-out sample can make a small cohort uninformative.
        # Such a cohort contributes no within-cohort treatment contrast; the
        # locked full apparatus is checked separately before inference.
        if min(xs) == max(xs):
            continue
        mean_x = sum(xs) / len(xs)
        mean_y = sum(ys) / len(ys)
        x_res.extend(x - mean_x for x in xs)
        y_res.extend(y - mean_y for y in ys)
    denominator = sum(x * x for x in x_res)
    if denominator == 0:
        raise ValueError("zero treatment variance after cohort adjustment")
    return sum(x * y for x, y in zip(x_res, y_res)) / denominator


def exact_p_value(endpoints: list[Mapping[str, object]], outcome: str) -> tuple[float, int]:
    observed = cohort_adjusted_beta(endpoints, outcome)
    cohort_indices = {
        cohort: [i for i, row in enumerate(endpoints) if int(row["cohort"]) == cohort]
        for cohort in SHARED_COHORTS
    }
    choices = []
    for cohort, idx in cohort_indices.items():
        treated = sum(endpoints[i]["group"] == "chr2" for i in idx)
        if treated == 0 or treated == len(idx):
            raise ValueError(f"cohort {cohort} lacks both treatment groups")
        choices.append(list(itertools.combinations(idx, treated)))
    exceed = 0
    total = 0
    for assignment in itertools.product(*choices):
        treated_idx = set().union(*(set(part) for part in assignment))
        labels = [int(i in treated_idx) for i in range(len(endpoints))]
        beta = cohort_adjusted_beta(endpoints, outcome, labels)
        exceed += beta >= observed - 1e-15
        total += 1
    return exceed / total, total


def analyze(rows: Iterable[Mapping[str, object]]) -> dict[str, object]:
    endpoints = animal_endpoints(rows)
    counts = defaultdict(int)
    for row in endpoints:
        counts[(int(row["cohort"]), str(row["group"]))] += 1
    expected = {
        (0, "chr2"): 4,
        (0, "ctrl"): 2,
        (3, "chr2"): 1,
        (3, "ctrl"): 2,
        (5, "chr2"): 3,
        (5, "ctrl"): 2,
    }
    if dict(counts) != expected:
        raise ValueError(f"locked apparatus mismatch: {dict(counts)!r}")

    primary_beta = cohort_adjusted_beta(endpoints, "post_mean")
    primary_p, permutations = exact_p_value(endpoints, "post_mean")
    session4_beta = cohort_adjusted_beta(endpoints, "session4")
    session4_p, session4_permutations = exact_p_value(endpoints, "session4")
    jackknife = [
        cohort_adjusted_beta(endpoints[:i] + endpoints[i + 1 :], "post_mean")
        for i in range(len(endpoints))
    ]
    passed = (
        primary_beta > 0
        and primary_p <= 0.01
        and min(jackknife) > 0
        and session4_beta > 0
        and session4_p <= 0.05
    )
    return {
        "status": (
            "DA_CAUSAL_PERSISTENCE_ESTABLISHED_DEVELOPMENT"
            if passed
            else "DA_CAUSAL_PERSISTENCE_NOT_ESTABLISHED"
        ),
        "animal_count": len(endpoints),
        "chr2_count": sum(row["group"] == "chr2" for row in endpoints),
        "ctrl_count": sum(row["group"] == "ctrl" for row in endpoints),
        "primary_beta": primary_beta,
        "primary_exact_p": primary_p,
        "primary_jackknife_min": min(jackknife),
        "session4_beta": session4_beta,
        "session4_exact_p": session4_p,
        "permutations": permutations,
        "session4_permutations": session4_permutations,
        "claim_ceiling": "causal dopamine-system intervention -> persistent behavior update",
    }


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("summary_csv", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = analyze(read_csv(args.summary_csv))
    payload = json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True)
    if args.output:
        args.output.write_text(payload + "\n", encoding="utf-8")
    print(payload)


if __name__ == "__main__":
    main()
