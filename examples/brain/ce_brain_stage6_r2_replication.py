"""Frozen R1 analysis applied to a second eligible Stage 6 development subject."""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
import sys
from pathlib import Path
from typing import Any

import h5py
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
R1_PATH = ROOT / "examples" / "brain" / "ce_brain_stage6_r1_recurrent_prediction.py"
SPEC = importlib.util.spec_from_file_location("ce_brain_stage6_r1_frozen", R1_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("STAGE6_R2_APPARATUS_STOP: R1 unavailable")
r1 = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = r1
SPEC.loader.exec_module(r1)

CONTRACT = ROOT / "paper" / "검증_원장" / "CE_BRAIN_STAGE6_R2_개발개체복제_계약.md"
TEST_FILE = ROOT / "tests" / "test_ce_brain_stage6_r2_replication.py"
R1_CONTRACT = ROOT / "paper" / "검증_원장" / "CE_BRAIN_STAGE6_R1_순환예측_계약.md"
R1_RESULT = ROOT / "artifacts" / "brain" / "ce_brain_stage6_r1_recurrent_prediction" / r1.RESULT
R1_VALIDATION = ROOT / "artifacts" / "brain" / "ce_brain_stage6_r1_recurrent_prediction" / r1.VALIDATION
DEFAULT_NWB = ROOT / "data" / "external" / "ce_brain_stage6_allen_dev" / "sub-740268983_ses-759883607.nwb"
ARTIFACT = ROOT / "artifacts" / "brain" / "ce_brain_stage6_r2_replication"
EXPECTED_SHA256 = "689b5fdc793343c9b874a1080252ec8c7d08f790274500c1344b925a692cfea2"
EXPECTED_SESSION = "759883607"
MANIFEST = "manifest.json"
RESULT = "result.json"
VALIDATION = "validation-receipt.json"
STOP = "STAGE6_R2_APPARATUS_STOP"


def validate_schema(path: Path) -> dict[str, Any]:
    with h5py.File(path, "r") as nwb:
        identifier = nwb["/identifier"][()]
        identifier = identifier.decode() if hasattr(identifier, "decode") else str(identifier)
        base = "/intervals/natural_movie_one_presentations"
        frames = np.asarray(nwb[f"{base}/frame"])
        starts = np.asarray(nwb[f"{base}/start_time"])
        stops = np.asarray(nwb[f"{base}/stop_time"])
        blocks = np.asarray(nwb[f"{base}/stimulus_block"])
        slices, repeat_blocks = r1.repeat_slices(frames, blocks)
        if identifier != EXPECTED_SESSION or len(slices) != 20 or sorted(np.unique(repeat_blocks).tolist()) != [4, 12]:
            raise RuntimeError(f"{STOP}: session/movie schema")
        if not np.all(np.diff(starts) > 0) or not np.all(stops > starts) or "/processing/running/running_speed" not in nwb:
            raise RuntimeError(f"{STOP}: strict-past schema")
        return {"session_id": identifier, "movie_repeats": len(slices), "strict_time": True, "stimulus_blocks": [4, 12]}


def files() -> tuple[Path, ...]:
    return (Path(__file__).resolve(), TEST_FILE, CONTRACT, R1_PATH, R1_CONTRACT, R1_RESULT, R1_VALIDATION)


def seal(nwb: Path, artifact: Path) -> dict[str, Any]:
    if r1.sha256(nwb) != EXPECTED_SHA256:
        raise RuntimeError(f"{STOP}: NWB hash")
    schema = validate_schema(nwb)
    manifest = {
        "files": {str(path.relative_to(ROOT)).replace("\\", "/"): r1.sha256(path) for path in files()},
        "nwb_sha256": EXPECTED_SHA256,
        "runtime": r1.runtime(),
        "schema": schema,
        "r2_scores_opened": False,
        "confirmation_endpoint_opened": False,
        "dandi_001695_opened": False,
    }
    manifest["manifest_sha256"] = r1.write_once(artifact / MANIFEST, manifest)
    return manifest


def verify_manifest(nwb: Path, artifact: Path) -> str:
    path = artifact / MANIFEST
    manifest = json.loads(path.read_text(encoding="utf-8"))
    expected_files = {str(item.relative_to(ROOT)).replace("\\", "/"): r1.sha256(item) for item in files()}
    if manifest.get("files") != expected_files or manifest.get("nwb_sha256") != r1.sha256(nwb) or manifest.get("runtime") != r1.runtime() or manifest.get("schema") != validate_schema(nwb) or manifest.get("r2_scores_opened") is not False:
        raise RuntimeError(f"{STOP}: manifest mutation")
    return r1.sha256(path)


def execute(nwb: Path, artifact: Path) -> dict[str, Any]:
    manifest_hash = verify_manifest(nwb, artifact)
    result = r1.analyze(nwb)
    result["manifest_sha256"] = manifest_hash
    result["replication_of"] = "STAGE6_R1_FROZEN"
    result_hash = r1.write_once(artifact / RESULT, result)
    return {"result_sha256": result_hash, **result}


def verify_result(nwb: Path, artifact: Path) -> dict[str, Any]:
    stored_path = artifact / RESULT
    stored = json.loads(stored_path.read_text(encoding="utf-8"))
    fresh = r1.analyze(nwb)
    fresh["manifest_sha256"] = verify_manifest(nwb, artifact)
    fresh["replication_of"] = "STAGE6_R1_FROZEN"
    if r1.canonical_bytes(stored) != r1.canonical_bytes(fresh):
        raise RuntimeError(f"{STOP}: raw recomputation mismatch")
    receipt = {"status": "PASS", "raw_recomputed": True, "decision": stored["decision"], "result_sha256": r1.sha256(stored_path)}
    receipt["validation_receipt_sha256"] = r1.write_once(artifact / VALIDATION, receipt)
    return receipt


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--nwb", type=Path, default=DEFAULT_NWB)
    parser.add_argument("--artifact-dir", type=Path, default=ARTIFACT)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--seal", action="store_true")
    group.add_argument("--execute", action="store_true")
    group.add_argument("--verify-result", action="store_true")
    args = parser.parse_args()
    output = seal(args.nwb, args.artifact_dir) if args.seal else execute(args.nwb, args.artifact_dir) if args.execute else verify_result(args.nwb, args.artifact_dir)
    print(json.dumps(output, sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()

