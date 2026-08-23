"""Draft-only D1 trajectory screen.  Default mode never performs network I/O."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location("brainvision_range", HERE / "brainvision_range.py")
br = importlib.util.module_from_spec(_spec)
assert _spec.loader is not None
_spec.loader.exec_module(br)

A2_SHA256 = "8f37e315b2a2fb808c24c60ab10f5bd3c177ad31c3e00498634c6894bc1ac8d5"
WORDS = ("child", "daughter", "father", "four", "six", "ten", "three", "wife")
DIMENSIONS, HISTORIES, RIDGES = (2, 3, 4), (25, 50, 100), (1e-4, 1e-2, 1.0, 1e2)
ANCHOR, TARGET = 100, 125


class D1Invalid(RuntimeError):
    pass


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def vech(matrix: np.ndarray) -> np.ndarray:
    return matrix[np.tril_indices(matrix.shape[0])]


def area(increments: np.ndarray) -> np.ndarray:
    d = increments.shape[1]
    value = np.zeros(d * (d - 1) // 2)
    index = 0
    for a in range(d):
        for b in range(a + 1, d):
            value[index] = 0.5 * sum(
                increments[p, a] * increments[q, b] - increments[p, b] * increments[q, a]
                for p in range(len(increments)) for q in range(p + 1, len(increments))
            )
            index += 1
    return value


def shuffled_area(increments: np.ndarray, trial_hash: str, number: int) -> np.ndarray:
    seed = int.from_bytes(hashlib.sha256(f"{trial_hash}:{number}".encode()).digest()[:8], "little")
    return area(increments[np.random.default_rng(seed).permutation(len(increments))])


def feature_count(d: int, model: str) -> int:
    baseline = 1 + 3 * d + 2 + d + d * (d + 1) // 2 + 4 * d + 7 + 1
    return baseline + (d * (d - 1) // 2 if model == "M1" else 0)


def fixed_coding(word: str, condition: str) -> np.ndarray:
    if word not in WORDS or condition not in {"task", "rest"}:
        raise D1Invalid("unknown fixed categorical level")
    return np.array([float(word == item) for item in WORDS[1:]] + [float(condition == "task")])


def path_features(z: np.ndarray, h: int, word: str, condition: str) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    if z.shape[0] != 126 or ANCHOR - h < 0 or TARGET >= z.shape[0]:
        raise D1Invalid("window/history geometry mismatch")
    increments = np.diff(z, axis=0)[ANCHOR - h:ANCHOR]
    center = increments.mean(axis=0)
    deviation = increments - center
    pieces = [
        np.array([1.0]), z[ANCHOR], 250.0 * (z[ANCHOR] - z[ANCHOR - 1]), z[ANCHOR - h],
        np.array([np.linalg.norm(increments, axis=1).sum(), np.square(increments).sum() / h]),
        center, vech(deviation.T @ deviation / h),
        (deviation ** 3).mean(axis=0), (deviation ** 4).mean(axis=0), increments.min(axis=0), increments.max(axis=0),
        fixed_coding(word, condition),
    ]
    return np.concatenate(pieces), area(increments), z[TARGET] - z[ANCHOR]


def fit_transform(train_windows: list[np.ndarray], d: int) -> dict:
    values = np.concatenate(train_windows, axis=0)
    median = np.median(values, axis=0)
    scale = 1.4826 * np.median(np.abs(values - median), axis=0)
    if not np.isfinite(scale).all() or np.any(scale == 0.0):
        raise D1Invalid("APPARATUS_INVALID_TRAINING_SCALE")
    scaled = (values - median) / scale
    covariance = scaled.T @ scaled / len(scaled)
    eigenvalue, eigenvector = np.linalg.eigh(covariance)
    order = np.argsort(eigenvalue)[::-1]
    eigenvalue, eigenvector = eigenvalue[order], eigenvector[:, order]
    if eigenvalue[0] <= 0 or eigenvalue[d - 1] / eigenvalue[0] < 1e-6 or eigenvalue[0] / eigenvalue[d - 1] > 1e6:
        raise D1Invalid("APPARATUS_INVALID_NUMERICAL_RANK")
    return {"median": median, "scale": scale, "basis": eigenvector[:, :d], "eigenvalue": eigenvalue[:d]}


def apply_transform(window: np.ndarray, transform: dict) -> np.ndarray:
    return ((window - transform["median"]) / transform["scale"]) @ transform["basis"] / np.sqrt(transform["eigenvalue"])


def standardize_train(train: np.ndarray, holdout: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    mean, scale = train[:, 1:].mean(axis=0), train[:, 1:].std(axis=0)
    if not np.isfinite(scale).all() or np.any(scale == 0.0):
        raise D1Invalid("APPARATUS_INVALID_DESIGN")
    return np.column_stack((train[:, :1], (train[:, 1:] - mean) / scale)), np.column_stack((holdout[:, :1], (holdout[:, 1:] - mean) / scale))


def ridge_fit(x: np.ndarray, y: np.ndarray, ridge: float) -> np.ndarray:
    penalty = np.diag([0.0] + [np.sqrt(ridge)] * (x.shape[1] - 1))
    augmented_x = np.vstack((x, penalty))
    augmented_y = np.vstack((y, np.zeros((x.shape[1], y.shape[1]))))
    return np.linalg.lstsq(augmented_x, augmented_y, rcond=None)[0]


def paired_folds(count: int):
    for held in range(count):
        yield [index for index in range(count) if index != held], held


def evaluate(records: list[dict], d: int, h: int, ridge: float) -> dict:
    if len(records) != 32 or feature_count(d, "M1") >= 2 * (len(records) - 1):
        raise D1Invalid("candidate pre-fit row-count gate failed")
    losses = {key: [] for key in ("m0_task", "m1_task", "reverse_task", "m0_rest", "m1_rest")}
    shuffle_losses = [[] for _ in range(20)]
    for train_indices, held in paired_folds(len(records)):
        train = [records[index] for index in train_indices]
        transform = fit_transform([window for record in train for window in (record["task"], record["rest"])], d)
        def make(record: dict, condition: str, replacement_area=None):
            base, ordered, target = path_features(apply_transform(record[condition], transform), h, record["word"], condition)
            return base, ordered if replacement_area is None else replacement_area, target
        train_rows = [make(record, condition) for record in train for condition in ("task", "rest")]
        hold_rows = {condition: make(records[held], condition) for condition in ("task", "rest")}
        raw0 = np.stack([row[0] for row in train_rows]); xa = np.stack([row[1] for row in train_rows]); y = np.stack([row[2] for row in train_rows])
        hold0 = np.stack([hold_rows[c][0] for c in ("task", "rest")])
        raw1 = np.column_stack((raw0, xa))
        hold1 = np.column_stack((hold0, np.stack([hold_rows[c][1] for c in ("task", "rest")])))
        x0, h0 = standardize_train(raw0, hold0)
        x1, h1 = standardize_train(raw1, hold1)
        b0, b1 = ridge_fit(x0, y, ridge), ridge_fit(x1, y, ridge)
        for index, condition in enumerate(("task", "rest")):
            target = hold_rows[condition][2]
            losses[f"m0_{condition}"].append(float(np.mean((target - h0[index] @ b0) ** 2)))
            losses[f"m1_{condition}"].append(float(np.mean((target - h1[index] @ b1) ** 2)))
            if condition == "task":
                # Reverse/shuffles must use the frozen M1 scaler, not a refit.
                raw_train = np.column_stack((np.stack([row[0] for row in train_rows]), xa))
                mean, scale = raw_train[:, 1:].mean(axis=0), raw_train[:, 1:].std(axis=0)
                frozen = lambda raw: np.r_[raw[0], (raw[1:] - mean) / scale]
                losses["reverse_task"].append(float(np.mean((target - frozen(np.r_[hold_rows[condition][0], -hold_rows[condition][1]]) @ b1) ** 2)))
                z = apply_transform(records[held][condition], transform)
                inc = np.diff(z, axis=0)[ANCHOR - h:ANCHOR]
                for number in range(20):
                    raw = np.r_[hold_rows[condition][0], shuffled_area(inc, records[held]["trial_hash"], number)]
                    shuffle_losses[number].append(float(np.mean((target - frozen(raw) @ b1) ** 2)))
    mean = {key: float(np.mean(value)) for key, value in losses.items()}
    return {"loss": mean, "shuffle_task": [float(np.mean(value)) for value in shuffle_losses],
            "survives": mean["m1_task"] < mean["m0_task"] and mean["m1_task"] < mean["reverse_task"] and all(mean["m1_task"] < value for value in [float(np.mean(x)) for x in shuffle_losses])}


def qc_accept(qc: dict, cutoffs: dict) -> bool:
    return qc["nonfinite_count"] == 0 and qc["zero_mad_channel_count"] == 0 and all(
        qc[name] <= values["cutoff"] for name, values in cutoffs.items()
    )


def load_d1(manifest: Path, a0: Path, a2: Path) -> tuple[list[dict], list[dict]]:
    draft = preflight(manifest, a2)
    a0_data = json.loads(a0.read_bytes())
    rows = [row for row in json.loads(manifest.read_bytes())["trials"] if row["split"] == "D1"]
    cutoffs = draft["frozen_qc_cutoffs"]
    records, pair_qc = [], []
    for row in rows:
        record = br.recording_for(a0_data, row["subject"], row["session"])
        values, accepted, requests = {}, True, []
        for condition, key in (("task", "task_anchor_s"), ("rest", "rest_anchor_s")):
            anchor = br.anchor_to_sample(float(row[key])); _, _, start, end = br.byte_geometry(anchor)
            raw, request = br.fetch_exact_range(record["eeg_url"], start, end, record["content_length"], record["etag"])
            window = br.causal_filter_and_decimate(br.parse_multiplexed_float32(raw)); qc = br.window_qc(window)
            values[condition], accepted = window, accepted and qc_accept(qc, cutoffs)
            requests.append({"condition": condition, "request": request, "qc": qc})
        pair_qc.append({
            "trial_hash": row["trial_hash"], "subject": row["subject"], "session": row["session"],
            "onset": row["onset"], "word": row["word"], "accepted": accepted, "windows": requests,
        })
        if accepted:
            records.append({"trial_hash": row["trial_hash"], "word": row["word"], "task": values["task"], "rest": values["rest"], "requests": requests})
    return records, pair_qc


def d4_diagnostics(records: list[dict]) -> dict:
    outcomes = []
    for train_indices, _ in paired_folds(len(records)):
        train = [records[index] for index in train_indices]
        transform = fit_transform([window for record in train for window in (record["task"], record["rest"])], 4)
        for record in train:
            for condition in ("task", "rest"):
                base, ordered, target = path_features(apply_transform(record[condition], transform), 25, record["word"], condition)
                if not (np.isfinite(base).all() and np.isfinite(ordered).all() and np.isfinite(target).all()):
                    raise D1Invalid("d4 finite-feature diagnostic failed")
        outcomes.append({"ratio": float(transform["eigenvalue"][-1] / transform["eigenvalue"][0]), "kappa": float(transform["eigenvalue"][0] / transform["eigenvalue"][-1])})
    return {"status": "DEFERRED_TO_D2_NO_OUTCOME_KILL", "p0": feature_count(4, "M0"), "p1": feature_count(4, "M1"), "folds": outcomes}


def execute(manifest: Path, a0: Path, a2: Path) -> dict:
    records, pair_qc = load_d1(manifest, a0, a2)
    if len(records) < 2:
        return {
            "schema": "BA-SELF1-D1-receipt-v2", "status": "D1_FAIL_CLOSED",
            "scientific_endpoint_opened": False, "model_outcome_computed": False,
            "error": "no QC-accepted D1 pairs", "allowed_splits": ["D1"],
            "unopened_splits": ["D2", "C1", "C2", "C3"],
            "accepted_pairs": len(records), "rejected_pairs": len(pair_qc) - len(records),
            "pair_qc": pair_qc,
        }
    results = {}
    for d in (2, 3):
        for h in HISTORIES:
            values = {}
            for ridge in RIDGES:
                try:
                    values[str(ridge)] = evaluate(records, d, h, ridge)
                except D1Invalid as error:
                    values[str(ridge)] = {"status": "KILLED_PREFIT", "reason": str(error), "survives": False}
            results[f"d{d}_H{h}"] = {"lambdas": values, "survives": any(value.get("survives", False) for value in values.values())}
    return {"schema": "BA-SELF1-D1-receipt-v2", "status": "D1_FUTILITY_SCREEN_COMPLETE_NO_SELECTION", "scientific_endpoint_opened": True,
            "allowed_splits": ["D1"], "unopened_splits": ["D2", "C1", "C2", "C3"], "accepted_pairs": len(records),
            "pair_qc": pair_qc, "outcome_screen_dimensions": [2, 3], "results": results,
            "d4": d4_diagnostics(records), "selection": "none; D1 only kills or permits D2"}


def preflight(manifest: Path, a2: Path) -> dict:
    if sha256(manifest) != br.MANIFEST_SHA256 or sha256(a2) != A2_SHA256:
        raise D1Invalid("sealed input hash mismatch")
    rows = json.loads(manifest.read_bytes())["trials"]
    d1 = [row for row in rows if row["split"] == "D1"]
    if len(d1) != 32 or any(row["subject"] != "sub-02" for row in d1):
        raise D1Invalid("D1 manifest selection mismatch")
    a2_receipt = json.loads(a2.read_bytes())
    if a2_receipt["status"] != "A2_APPARATUS_PASS" or "frozen_qc_cutoffs" not in a2_receipt:
        raise D1Invalid("frozen A2 QC unavailable")
    return {"schema": "BA-SELF1-D1-draft-v1", "status": "D1_DRAFT_NOT_EXECUTED", "network_accessed": False,
            "scientific_endpoint_opened": False, "manifest_sha256": br.MANIFEST_SHA256, "a2_receipt_sha256": A2_SHA256,
            "selected_trials": len(d1), "allowed_splits": ["D1"], "unopened_splits": ["D2", "C1", "C2", "C3"],
            "frozen_qc_cutoffs": a2_receipt["frozen_qc_cutoffs"], "menu": {"d": DIMENSIONS, "H": HISTORIES, "lambda": RIDGES},
            "cv": "leave-one-trial-pair-out; task/rest paired; fold-local transforms and standardization"}


def main() -> int:
    parser = argparse.ArgumentParser(); parser.add_argument("--manifest", type=Path, required=True); parser.add_argument("--a0-receipt", type=Path, required=True); parser.add_argument("--a2-receipt", type=Path, required=True); parser.add_argument("--output", type=Path, required=True); parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    try:
        receipt = execute(args.manifest, args.a0_receipt, args.a2_receipt) if args.execute else preflight(args.manifest, args.a2_receipt)
    except (D1Invalid, br.ApparatusInvalid) as error:
        receipt = {"schema": "BA-SELF1-D1-receipt-v2", "status": "D1_FAIL_CLOSED", "scientific_endpoint_opened": False,
                   "model_outcome_computed": False, "error": str(error), "unopened_splits": ["D2", "C1", "C2", "C3"]}
        br.dump_atomic(args.output, receipt); print(receipt["status"]); return 2
    br.dump_atomic(args.output, receipt); print(receipt["status"])
    return 2 if receipt["status"] == "D1_FAIL_CLOSED" else 0


if __name__ == "__main__":
    raise SystemExit(main())
