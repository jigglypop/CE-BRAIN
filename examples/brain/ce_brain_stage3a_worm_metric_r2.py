"""Stage 3A R2: sealed apparatus amendment for empty canonical-coordinate sets."""

from __future__ import annotations

import argparse
import importlib.util
import sys
from pathlib import Path
from typing import Iterable

import h5py
import numpy as np


ROOT = Path(__file__).resolve().parents[2]
BASE_PATH = ROOT / "examples" / "brain" / "ce_brain_stage3a_worm_metric.py"
SPEC = importlib.util.spec_from_file_location("ce_brain_stage3a_worm_metric_r1_sealed", BASE_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("STAGE3A_R2_APPARATUS_STOP: sealed R1 module unavailable")
base = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = base
SPEC.loader.exec_module(base)

STOP = "STAGE3A_R2_APPARATUS_STOP"
CONTRACT = ROOT / "paper" / "검증_원장" / "CE_BRAIN_STAGE3A_R2_장치수정_계약.md"
R1_CONTRACT = ROOT / "paper" / "검증_원장" / "CE_BRAIN_STAGE3A_선충_간선표현_계약.md"
TEST_FILE = ROOT / "tests" / "test_ce_brain_stage3a_worm_metric_r2.py"
R1_TEST_FILE = ROOT / "tests" / "test_ce_brain_stage3a_worm_metric.py"
ARTIFACT_DIR = ROOT / "artifacts" / "brain" / "ce_brain_stage3a_worm_metric_r2"


def collect_coordinates(paths: Iterable[Path]) -> dict[int, dict[str, np.ndarray]]:
    """Exclude subjects with fewer than ten canonical nodes before normalization."""
    output: dict[int, dict[str, np.ndarray]] = {}
    for path in paths:
        subject = base.subject_id(path)
        if not base.subject_development(subject):
            continue
        with h5py.File(path, "r") as nwb:
            names, coords = base.canonical_map(nwb)
            if len(names) < 10:
                continue
            output[subject] = base.normalized_coordinates(names, coords)
    return output


def preregistered_files() -> tuple[Path, ...]:
    return (Path(__file__).resolve(), BASE_PATH, TEST_FILE, R1_TEST_FILE, CONTRACT, R1_CONTRACT)


base.STOP = STOP
base.CONTRACT = CONTRACT
base.TEST_FILE = TEST_FILE
base.collect_coordinates = collect_coordinates
base.preregistered_files = preregistered_files


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", type=Path, required=True)
    parser.add_argument("--artifact-dir", type=Path, default=ARTIFACT_DIR)
    actions = parser.add_mutually_exclusive_group(required=True)
    for name in ("schema-only", "seal", "execute", "verify-result"):
        actions.add_argument(f"--{name}", action="store_true")
    args = parser.parse_args()
    if args.schema_only:
        output = base.schema_receipt(args.data_dir, args.artifact_dir)
    elif args.seal:
        output = base.seal(args.data_dir, args.artifact_dir)
    elif args.execute:
        output = base.execute(args.data_dir, args.artifact_dir)
    else:
        output = base.verify_result(args.data_dir, args.artifact_dir)
    print(base.json.dumps(output, sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()
