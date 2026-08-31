from __future__ import annotations

import argparse
import hashlib
import json
from collections import defaultdict
from pathlib import Path

import numpy as np


EXCLUDED = {"wt": {11}, "unc31": {0, 3, 4}}
MIN_RECORDINGS = {"wt": 80, "unc31": 10}
PERMUTATIONS = 20_000
BOOTSTRAPS = 10_000
SEED = 20_260_901


def load_lines(path: Path) -> list[str]:
    return path.read_text(encoding="utf-8").splitlines()


def holdout(ds_name: str) -> bool:
    prefix = hashlib.sha256(ds_name.encode("utf-8")).digest()[:4]
    return int.from_bytes(prefix, "big") % 5 == 0


def event_metrics(
    data: np.ndarray,
    labels: list[str],
    source: int,
    stimulus_volume: int,
) -> tuple[float, float, float] | None:
    if stimulus_volume < 20 or stimulus_volume + 12 > data.shape[0]:
        return None
    baseline = data[stimulus_volume - 20 : stimulus_volume]
    post = data[stimulus_volume + 2 : stimulus_volume + 12]
    baseline_finite = np.mean(np.isfinite(baseline), axis=0) >= 0.8
    post_finite = np.mean(np.isfinite(post), axis=0) >= 0.8
    valid = baseline_finite & post_finite

    center = np.nanmedian(baseline, axis=0)
    mad = 1.4826 * np.nanmedian(np.abs(baseline - center), axis=0)
    epsilon = 1e-6 * np.maximum(1.0, np.abs(center))
    z = (np.nanmean(post, axis=0) - center) / (mad + epsilon)
    valid &= np.isfinite(z) & (mad + epsilon > 0)

    if not valid[source] or z[source] < 2.0:
        return None
    identified = np.array(
        [index < len(labels) and bool(labels[index].strip()) for index in range(data.shape[1])]
    )
    downstream = valid & identified
    downstream[source] = False
    if int(np.sum(downstream)) < 20:
        return None

    zd = np.clip(z[downstream], -20.0, 20.0)
    source_z = min(float(z[source]), 20.0)
    length = float(np.sqrt(np.mean(zd**2)) / source_z)
    breadth = float(np.mean(np.abs(zd) >= 2.0))
    energy2 = float(np.sum(zd**2))
    energy4 = float(np.sum(zd**4))
    participation = (
        float(energy2**2 / (len(zd) * energy4)) if energy4 > 0 else 0.0
    )
    return length, breadth, participation


def load_group(name: str, root: Path) -> list[dict[str, object]]:
    records: list[dict[str, object]] = []
    ids = sorted(int(path.name.split("_")[0]) for path in root.glob("*_ds_name.txt"))
    for record_id in ids:
        if record_id in EXCLUDED[name]:
            continue
        labels = load_lines(root / f"{record_id}_labels.txt")
        sources = [int(value) for value in load_lines(root / f"{record_id}_stim_neurons.txt")]
        volumes = [int(value) for value in load_lines(root / f"{record_id}_stim_volume_i.txt")]
        ds_name = load_lines(root / f"{record_id}_ds_name.txt")[0].strip()
        data = np.loadtxt(root / f"{record_id}_gcamp.txt")
        labels = labels[: data.shape[1]]

        valid_events: list[dict[str, object]] = []
        for source, volume in zip(sources, volumes):
            if source < 0 or source >= data.shape[1] or not labels[source].strip():
                continue
            metrics = event_metrics(data, labels, source, volume)
            if metrics is None:
                continue
            length, breadth, participation = metrics
            valid_events.append(
                {
                    "source": labels[source].strip(),
                    "length": length,
                    "breadth": breadth,
                    "participation": participation,
                }
            )
        if len(valid_events) < 3:
            continue
        records.append(
            {
                "group": name,
                "recording_id": record_id,
                "ds_name": ds_name,
                "holdout": holdout(ds_name),
                "valid_events": len(valid_events),
                "length": float(np.median([event["length"] for event in valid_events])),
                "breadth": float(np.median([event["breadth"] for event in valid_events])),
                "participation": float(
                    np.median([event["participation"] for event in valid_events])
                ),
                "events": valid_events,
            }
        )
    return records


def median_difference(wt: np.ndarray, unc31: np.ndarray) -> float:
    return float(np.median(wt) - np.median(unc31))


def permutation_p(wt: np.ndarray, unc31: np.ndarray, rng: np.random.Generator) -> float:
    observed = median_difference(wt, unc31)
    combined = np.concatenate([wt, unc31])
    exceed = 0
    for _ in range(PERMUTATIONS):
        order = rng.permutation(len(combined))
        difference = median_difference(
            combined[order[: len(wt)]], combined[order[len(wt) :]]
        )
        exceed += difference >= observed
    return float((exceed + 1) / (PERMUTATIONS + 1))


def bootstrap_ci(wt: np.ndarray, unc31: np.ndarray, rng: np.random.Generator) -> list[float]:
    values = np.empty(BOOTSTRAPS, dtype=float)
    for index in range(BOOTSTRAPS):
        values[index] = median_difference(
            rng.choice(wt, size=len(wt), replace=True),
            rng.choice(unc31, size=len(unc31), replace=True),
        )
    return [float(value) for value in np.quantile(values, [0.025, 0.975])]


def source_matched(records: list[dict[str, object]], rng: np.random.Generator) -> dict[str, object]:
    values: dict[str, dict[str, dict[int, list[float]]]] = {
        "wt": defaultdict(lambda: defaultdict(list)),
        "unc31": defaultdict(lambda: defaultdict(list)),
    }
    for record in records:
        group = str(record["group"])
        record_id = int(record["recording_id"])
        for event in record["events"]:
            values[group][str(event["source"])][record_id].append(float(event["length"]))

    shared = []
    deltas = []
    for source in sorted(set(values["wt"]) & set(values["unc31"])):
        if len(values["wt"][source]) < 3 or len(values["unc31"][source]) < 3:
            continue
        wt_value = np.median(
            [np.median(record_values) for record_values in values["wt"][source].values()]
        )
        unc_value = np.median(
            [np.median(record_values) for record_values in values["unc31"][source].values()]
        )
        shared.append(source)
        deltas.append(float(wt_value - unc_value))
    if not deltas:
        return {"sources": 0, "median_difference": None, "sign_flip_p": None}
    delta_array = np.asarray(deltas)
    observed = float(np.median(delta_array))
    exceed = 0
    for _ in range(PERMUTATIONS):
        signs = rng.choice(np.array([-1.0, 1.0]), size=len(delta_array))
        exceed += float(np.median(delta_array * signs)) >= observed
    return {
        "sources": len(shared),
        "source_labels": shared,
        "median_difference": observed,
        "sign_flip_p": float((exceed + 1) / (PERMUTATIONS + 1)),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--wt-root", type=Path, required=True)
    parser.add_argument("--unc31-root", type=Path, required=True)
    args = parser.parse_args()
    rng = np.random.default_rng(SEED)
    records = load_group("wt", args.wt_root.resolve()) + load_group(
        "unc31", args.unc31_root.resolve()
    )

    by_group = {
        group: [record for record in records if record["group"] == group]
        for group in ("wt", "unc31")
    }
    wt = np.asarray([record["length"] for record in by_group["wt"]], dtype=float)
    unc31 = np.asarray([record["length"] for record in by_group["unc31"]], dtype=float)
    wt_hold = np.asarray(
        [record["length"] for record in by_group["wt"] if record["holdout"]], dtype=float
    )
    unc_hold = np.asarray(
        [record["length"] for record in by_group["unc31"] if record["holdout"]], dtype=float
    )
    wt_dev = np.asarray(
        [record["length"] for record in by_group["wt"] if not record["holdout"]], dtype=float
    )
    unc_dev = np.asarray(
        [record["length"] for record in by_group["unc31"] if not record["holdout"]], dtype=float
    )

    quality = {
        "wt_recordings": len(wt),
        "unc31_recordings": len(unc31),
        "wt_holdout": len(wt_hold),
        "unc31_holdout": len(unc_hold),
        "wt_valid_events": sum(int(record["valid_events"]) for record in by_group["wt"]),
        "unc31_valid_events": sum(
            int(record["valid_events"]) for record in by_group["unc31"]
        ),
    }
    quality_pass = (
        len(wt) >= MIN_RECORDINGS["wt"]
        and len(unc31) >= MIN_RECORDINGS["unc31"]
        and len(wt_hold) >= 15
        and len(unc_hold) >= 2
    )

    primary: dict[str, object] = {}
    if quality_pass:
        difference = median_difference(wt, unc31)
        p_value = permutation_p(wt, unc31, rng)
        ci = bootstrap_ci(wt, unc31, rng)
        dev_difference = median_difference(wt_dev, unc_dev)
        holdout_difference = median_difference(wt_hold, unc_hold)
        supported = (
            difference > 0
            and p_value < 0.05
            and ci[0] > 0
            and dev_difference > 0
            and holdout_difference > 0
        )
        decision = (
            "R1_EFFECTIVE_PROPAGATION_SUPPORTED"
            if supported
            else "R1_EFFECTIVE_PROPAGATION_NOT_SUPPORTED"
        )
        primary = {
            "wt_median": float(np.median(wt)),
            "unc31_median": float(np.median(unc31)),
            "median_difference": difference,
            "permutation_p_one_sided": p_value,
            "bootstrap_95_ci": ci,
            "development_difference": dev_difference,
            "holdout_difference": holdout_difference,
        }
    else:
        decision = "R1_BLOCKED_QUALITY"

    def secondary(field: str) -> dict[str, float]:
        wt_values = np.asarray([record[field] for record in by_group["wt"]])
        unc_values = np.asarray([record[field] for record in by_group["unc31"]])
        return {
            "wt_median": float(np.median(wt_values)),
            "unc31_median": float(np.median(unc_values)),
            "median_difference": median_difference(wt_values, unc_values),
        }

    receipt = {
        "decision": decision,
        "claim_ceiling": "L2_intervention_association_not_plasticity_or_behavior_mediation",
        "contract": "ALT_BIO_R1_UNC31_v1",
        "seed": SEED,
        "permutations": PERMUTATIONS,
        "bootstraps": BOOTSTRAPS,
        "quality": quality,
        "quality_pass": quality_pass,
        "primary_effective_length": primary,
        "secondary_breadth": secondary("breadth") if by_group["unc31"] else None,
        "secondary_participation": (
            secondary("participation") if by_group["unc31"] else None
        ),
        "source_matched_sensitivity": source_matched(records, rng),
    }
    print(json.dumps(receipt, ensure_ascii=False, indent=2))
    return 0 if decision != "R1_BLOCKED_QUALITY" else 2


if __name__ == "__main__":
    raise SystemExit(main())
