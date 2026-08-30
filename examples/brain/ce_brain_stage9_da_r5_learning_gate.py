"""Sealed observational dopamine-to-next-day learning gate for CE-BRAIN Stage 9."""
from __future__ import annotations

import argparse
import hashlib
import json
import platform
import re
import sys
from pathlib import Path
from typing import Any

import h5py
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data" / "external" / "ce_brain_stage9_da" / "development"
DOWNLOAD = ROOT / "artifacts" / "brain" / "ce_brain_stage9_da_development_download" / "receipt.json"
CONTRACT = ROOT / "paper" / "검증_원장" / "CE_BRAIN_STAGE9_DA_R5_학습게이트_계약.md"
TEST_FILE = ROOT / "tests" / "test_ce_brain_stage9_da_r5_learning_gate.py"
ARTIFACT = ROOT / "artifacts" / "brain" / "ce_brain_stage9_da_r5_learning_gate"
SEED, BOOTSTRAPS = 20260909, 1999
MANIFEST, RESULT, VALIDATION = "manifest.json", "result.json", "validation-receipt.json"


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as source:
        while block := source.read(1024 * 1024): value.update(block)
    return value.hexdigest()


def canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def write_once(path: Path, value: Any) -> str:
    payload = canonical(value) + b"\n"
    if path.exists(): raise RuntimeError(f"STAGE9_DA_STOP: refusing overwrite {path}")
    path.parent.mkdir(parents=True, exist_ok=True); temporary = path.with_suffix(path.suffix + ".tmp"); temporary.write_bytes(payload); temporary.replace(path)
    return hashlib.sha256(payload).hexdigest()


def session_values(path: Path) -> dict[str, Any]:
    with h5py.File(path, "r") as handle:
        codes = handle["acquisition/eventLog/event_code"][:]
        flags = handle["acquisition/eventLog/event_flag"][:]
        event_time = handle["acquisition/eventLog/timestamp"][:]
        photo = handle["processing/photometry/photometry_dff/data"][:].astype(float)
        photo_time = handle["processing/photometry/photometry_dff/timestamps"][:].astype(float)
        start = handle["session_start_time"][()].decode() if isinstance(handle["session_start_time"][()], bytes) else str(handle["session_start_time"][()])
    if len(photo) != len(photo_time) or not np.all(np.diff(photo_time) > 0): raise RuntimeError(f"STAGE9_DA_COVERAGE_STOP: photometry {path.name}")
    cues = event_time[(codes == 15) & (flags == 0)]; rewards = event_time[(codes == 10) & (flags == 0)]; licks = event_time[np.isin(codes, (1, 3, 5))]
    behavior, dopamine = [], []
    for cue in cues:
        index = np.searchsorted(rewards, cue, side="right")
        if index >= len(rewards): continue
        reward = rewards[index]; delay = reward - cue
        if not 0.5 <= delay <= 3.0: continue
        pre = photo[(photo_time >= cue - 1.0) & (photo_time < cue)]; post = photo[(photo_time >= cue) & (photo_time < cue + 1.0)]
        if len(pre) < 10 or len(post) < 10 or not np.all(np.isfinite(pre)) or not np.all(np.isfinite(post)): continue
        behavior.append(float(np.sum((licks >= cue) & (licks < reward)) / delay)); dopamine.append(float(np.mean(post) - np.median(pre)))
    return {"start": start, "behavior": behavior, "dopamine": dopamine, "trials": len(behavior)}


def parse(path: Path) -> tuple[str, int]:
    match = re.match(r"(sub-(?:60sD|600sD)-[FM]\d+)_ses-day(\d+)[ab]?\.nwb", path.name)
    if not match: raise RuntimeError(f"STAGE9_DA_COVERAGE_STOP: filename {path.name}")
    return match.group(1), int(match.group(2))


def daily_table() -> list[dict[str, Any]]:
    grouped: dict[tuple[str, int], list[dict[str, Any]]] = {}
    for path in sorted(DATA.glob("*.nwb")):
        grouped.setdefault(parse(path), []).append(session_values(path))
    daily = []
    for (subject, day), pieces in sorted(grouped.items()):
        pieces.sort(key=lambda item: item["start"]); behavior = sum((item["behavior"] for item in pieces), []); dopamine = sum((item["dopamine"] for item in pieces), [])
        if len(behavior) < 4: raise RuntimeError(f"STAGE9_DA_COVERAGE_STOP: {subject} day {day} trials {len(behavior)}")
        daily.append({"subject": subject, "day": day, "iti": 600.0 if subject.startswith("sub-600sD") else 60.0, "behavior": float(np.median(behavior)), "dopamine": float(np.median(dopamine)), "trials": len(behavior)})
    return daily


def transition_rows(daily: list[dict[str, Any]]) -> list[dict[str, Any]]:
    lookup = {(row["subject"], row["day"]): row for row in daily}; output = []
    by_subject = sorted({row["subject"] for row in daily})
    shifted = {}
    for subject in by_subject:
        values = [lookup[(subject, day)]["dopamine"] for day in range(1, 9)]
        shifted[subject] = np.roll(values, 3)
    for subject in by_subject:
        for day in range(1, 8):
            current, future = lookup[(subject, day)], lookup[(subject, day + 1)]
            output.append({"subject": subject, "day": day, "log_iti": float(np.log10(current["iti"])), "behavior": current["behavior"], "dopamine": current["dopamine"], "shifted_dopamine": float(shifted[subject][day - 1]), "target": future["behavior"]})
    return output


def ridge_predict(train: list[dict[str, Any]], test: list[dict[str, Any]], names: tuple[str, ...]) -> tuple[np.ndarray, np.ndarray]:
    x_train = np.asarray([[row[name] for name in names] for row in train], float); x_test = np.asarray([[row[name] for name in names] for row in test], float); y = np.asarray([row["target"] for row in train])
    mean, scale = x_train.mean(axis=0), x_train.std(axis=0); scale[scale == 0] = 1
    a = np.column_stack((np.ones(len(train)), (x_train - mean) / scale)); b = np.column_stack((np.ones(len(test)), (x_test - mean) / scale)); penalty = np.eye(a.shape[1]); penalty[0, 0] = 0
    coefficient = np.linalg.solve(a.T @ a + penalty, a.T @ y)
    return b @ coefficient, coefficient


def predictions(rows: list[dict[str, Any]]) -> tuple[dict[str, np.ndarray], list[str], list[float]]:
    subjects = sorted({row["subject"] for row in rows}); output = {name: np.empty(len(rows)) for name in ("P", "B", "C", "S")}; coefficients = []
    for subject in subjects:
        train = [row for row in rows if row["subject"] != subject]; indices = [i for i, row in enumerate(rows) if row["subject"] == subject]; test = [rows[i] for i in indices]
        output["P"][indices] = [row["behavior"] for row in test]
        output["B"][indices], _ = ridge_predict(train, test, ("log_iti", "day", "behavior"))
        output["C"][indices], coef = ridge_predict(train, test, ("log_iti", "day", "behavior", "dopamine")); coefficients.append(float(coef[-1]))
        output["S"][indices], _ = ridge_predict(train, test, ("log_iti", "day", "behavior", "shifted_dopamine"))
    return output, subjects, coefficients


def comparison(primary: np.ndarray, baseline: np.ndarray, target: np.ndarray, row_subjects: list[str], subjects: list[str], offset: int) -> dict[str, float]:
    def improvement(indices: np.ndarray) -> float:
        p = float(np.sqrt(np.mean((target[indices] - primary[indices]) ** 2))); b = float(np.sqrt(np.mean((target[indices] - baseline[indices]) ** 2))); return (b - p) / b
    actual = improvement(np.arange(len(target))); rng = np.random.Generator(np.random.PCG64(SEED + offset)); values = []
    locations = {subject: np.flatnonzero(np.asarray(row_subjects) == subject) for subject in subjects}
    for _ in range(BOOTSTRAPS):
        sampled = rng.choice(subjects, len(subjects), replace=True); indices = np.concatenate([locations[item] for item in sampled]); values.append(improvement(indices))
    return {"improvement": actual, "lower_95": float(np.quantile(values, 0.025)), "upper_95": float(np.quantile(values, 0.975))}


def analyze() -> dict[str, Any]:
    daily = daily_table(); rows = transition_rows(daily); pred, subjects, coefficients = predictions(rows); target = np.asarray([row["target"] for row in rows]); row_subjects = [row["subject"] for row in rows]
    comparisons = {"C_vs_B": comparison(pred["C"], pred["B"], target, row_subjects, subjects, 1), "C_vs_P": comparison(pred["C"], pred["P"], target, row_subjects, subjects, 2), "C_vs_S": comparison(pred["C"], pred["S"], target, row_subjects, subjects, 3)}
    coverage = len(subjects) == 7 and all(sum(row["subject"] == subject for row in rows) >= 5 for subject in subjects)
    passed = coverage and comparisons["C_vs_B"]["improvement"] >= 0.05 and comparisons["C_vs_B"]["lower_95"] > 0 and comparisons["C_vs_P"]["improvement"] >= 0.05 and comparisons["C_vs_P"]["lower_95"] > 0 and comparisons["C_vs_S"]["improvement"] >= 0.03 and comparisons["C_vs_S"]["lower_95"] > 0 and sum(value > 0 for value in coefficients) >= 6
    decision = "STAGE9_DA_COVERAGE_STOP" if not coverage else "DEVELOPMENT_DOPAMINE_UPDATE_SIGNAL_SUPPORTED" if passed else "DOPAMINE_UPDATE_SIGNAL_NOT_ESTABLISHED"
    return {"decision": decision, "claim_ceiling": "observational next-day prediction in seven development animals", "coverage": {"animals": len(subjects), "daily_rows": len(daily), "transition_rows": len(rows), "trials_by_day": [row["trials"] for row in daily]}, "rmse": {name: float(np.sqrt(np.mean((target - value) ** 2))) for name, value in pred.items()}, "comparisons": comparisons, "cue_dopamine_coefficients": coefficients, "positive_coefficient_folds": sum(value > 0 for value in coefficients), "bootstrap": {"repetitions": BOOTSTRAPS, "seed": SEED}}


def input_files() -> tuple[Path, ...]: return tuple(sorted(DATA.glob("*.nwb")))
def runtime() -> dict[str, str]: return {"executable": sys.executable, "python": platform.python_version(), "numpy": np.__version__, "h5py": h5py.__version__}


def seal(artifact: Path) -> dict[str, Any]:
    receipt = json.loads(DOWNLOAD.read_text(encoding="utf-8"))
    if receipt.get("decision") != "STAGE9_DA_DEVELOPMENT_LOCKED" or receipt.get("confirmation_opened") is not False or len(input_files()) != 57: raise RuntimeError("STAGE9_DA_STOP: input lock")
    manifest = {"files": {str(path.relative_to(ROOT)).replace("\\", "/"): digest(path) for path in (*input_files(), Path(__file__).resolve(), TEST_FILE, CONTRACT, DOWNLOAD)}, "runtime": runtime(), "scores_opened": False}; manifest["manifest_sha256"] = write_once(artifact / MANIFEST, manifest); return manifest


def verify_manifest(artifact: Path) -> str:
    path = artifact / MANIFEST; stored = json.loads(path.read_text(encoding="utf-8")); expected = {str(item.relative_to(ROOT)).replace("\\", "/"): digest(item) for item in (*input_files(), Path(__file__).resolve(), TEST_FILE, CONTRACT, DOWNLOAD)}
    if stored.get("files") != expected or stored.get("runtime") != runtime() or stored.get("scores_opened") is not False: raise RuntimeError("STAGE9_DA_STOP: manifest mutation")
    return digest(path)


def execute(artifact: Path) -> dict[str, Any]:
    result = analyze(); result["manifest_sha256"] = verify_manifest(artifact); result_hash = write_once(artifact / RESULT, result); return {"result_sha256": result_hash, **result}


def verify_result(artifact: Path) -> dict[str, Any]:
    stored_path = artifact / RESULT; stored = json.loads(stored_path.read_text(encoding="utf-8")); fresh = analyze(); fresh["manifest_sha256"] = verify_manifest(artifact)
    if canonical(stored) != canonical(fresh): raise RuntimeError("STAGE9_DA_STOP: raw recomputation mismatch")
    receipt = {"status": "PASS", "raw_recomputed": True, "decision": stored["decision"], "result_sha256": digest(stored_path)}; receipt["validation_receipt_sha256"] = write_once(artifact / VALIDATION, receipt); return receipt


def main() -> None:
    parser = argparse.ArgumentParser(); group = parser.add_mutually_exclusive_group(required=True); group.add_argument("--seal", action="store_true"); group.add_argument("--execute", action="store_true"); group.add_argument("--verify-result", action="store_true"); parser.add_argument("--artifact-dir", type=Path, default=ARTIFACT); args = parser.parse_args(); value = seal(args.artifact_dir) if args.seal else execute(args.artifact_dir) if args.execute else verify_result(args.artifact_dir); print(json.dumps(value, sort_keys=True))


if __name__ == "__main__": main()
