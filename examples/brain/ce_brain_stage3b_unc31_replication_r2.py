"""Stage 3B R2: sampling-rate correction for finite-frame eligibility."""
from __future__ import annotations
import argparse, importlib.util, json, sys
from collections import defaultdict
from pathlib import Path
from typing import Any
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
BASE_PATH = ROOT / "examples" / "brain" / "ce_brain_stage3b_unc31_replication.py"
SPEC = importlib.util.spec_from_file_location("stage3b_r1_failed", BASE_PATH)
if SPEC is None or SPEC.loader is None: raise RuntimeError("STAGE3B_R2_APPARATUS_STOP: R1 unavailable")
base = importlib.util.module_from_spec(SPEC); sys.modules[SPEC.name] = base; SPEC.loader.exec_module(base)
STOP = "STAGE3B_R2_APPARATUS_STOP"
CONTRACT = ROOT / "paper" / "검증_원장" / "CE_BRAIN_STAGE3B_R2_표본율수정_계약.md"
TEST_FILE = ROOT / "tests" / "test_ce_brain_stage3b_unc31_replication_r2.py"
R1_CONTRACT = ROOT / "paper" / "검증_원장" / "CE_BRAIN_STAGE3B_UNC31_교란외삽_계약.md"
R1_TEST = ROOT / "tests" / "test_ce_brain_stage3b_unc31_replication.py"
ARTIFACT = ROOT / "artifacts" / "brain" / "ce_brain_stage3b_unc31_replication_r2"


def extract_subject(folder: Path, subject: int, template: dict[str, np.ndarray]) -> list[dict[str, Any]]:
    labels = base.load_labels(folder / f"{subject}_labels.txt")
    signal = np.loadtxt(folder / f"{subject}_gcamp.txt", dtype=float, ndmin=2)
    time = np.loadtxt(folder / f"{subject}_t.txt", dtype=float, ndmin=1)
    stimuli = np.loadtxt(folder / f"{subject}_stim_neurons.txt", dtype=int, ndmin=1)
    volumes = np.loadtxt(folder / f"{subject}_stim_volume_i.txt", dtype=int, ndmin=1)
    if signal.shape != (len(time), len(labels)): return []
    output = []
    for event, (source_index, volume) in enumerate(zip(stimuli, volumes, strict=True)):
        if not (0 <= source_index < len(labels)) or labels[source_index] not in template: continue
        source = labels[source_index]
        baseline_i = np.flatnonzero((time >= time[volume] - 10) & (time <= time[volume] - 2))
        next_limit = volumes[event + 1] - 10 if event + 1 < len(volumes) else volume + 21
        response_i = np.arange(volume + 3, min(volume + 21, next_limit, len(time)))
        if len(baseline_i) < 12 or len(response_i) < 12: continue
        baseline, response = signal[baseline_i], signal[response_i]
        finite_baseline = np.sum(np.isfinite(baseline), axis=0) >= 12
        finite_response = np.sum(np.isfinite(response), axis=0) >= 12
        center = np.nanmedian(baseline, axis=0)
        mad = 1.4826 * np.nanmedian(np.abs(baseline - center[None, :]), axis=0)
        positive = mad[np.isfinite(mad) & (mad > 0)]
        if len(positive) < 10: continue
        mad = np.maximum(mad, float(np.quantile(positive, .10)))
        denom_positive = np.abs(center[np.isfinite(center) & (np.abs(center) > 0)])
        if len(denom_positive) < 10: continue
        denominator = np.maximum(np.abs(center), float(np.quantile(denom_positive, .10)))
        z = (response - center[None, :]) / mad[None, :]
        dff = np.abs(response - center[None, :]) / denominator[None, :]
        detected = base.run_length_at_least(np.abs(z) >= 3., 4) & (np.nanmax(dff, axis=0) >= .10)
        eligible = finite_baseline & finite_response & np.isfinite(center) & np.isfinite(mad)
        by_label: dict[str, list[int]] = defaultdict(list)
        for column, label in enumerate(labels):
            if label in template and label != source and eligible[column]: by_label[label].append(column)
        for receiver, columns in by_label.items():
            output.append({"event": event, "receiver": receiver, "source": source,
                           "subject": subject, "y": int(np.any(detected[columns]))})
    return output


def preregistered_files():
    return (Path(__file__).resolve(), BASE_PATH, TEST_FILE, R1_TEST, CONTRACT, R1_CONTRACT, base.STAGE3A_PATH)


base.STOP = STOP; base.CONTRACT = CONTRACT; base.TEST_FILE = TEST_FILE
base.extract_subject = extract_subject; base.preregistered_files = preregistered_files
base.s3a.SEED = base.SEED


def main():
    p=argparse.ArgumentParser();p.add_argument("--data-dir",type=Path,default=base.DEFAULT_DATA)
    p.add_argument("--artifact-dir",type=Path,default=ARTIFACT);g=p.add_mutually_exclusive_group(required=True)
    for a in ("inventory","schema-only","development-only","seal","execute","verify-result"):g.add_argument(f"--{a}",action="store_true")
    a=p.parse_args()
    if a.inventory:o=base.create_inventory(a.data_dir,a.artifact_dir)
    elif a.schema_only:o=base.schema_receipt(a.data_dir,a.artifact_dir)
    elif a.development_only:o=base.development_receipt(a.data_dir,a.artifact_dir)
    elif a.seal:o=base.seal(a.data_dir,a.artifact_dir)
    elif a.execute:o=base.execute(a.data_dir,a.artifact_dir)
    else:o=base.verify_result(a.data_dir,a.artifact_dir)
    print(json.dumps(o,sort_keys=True,allow_nan=False))
if __name__=="__main__":main()
