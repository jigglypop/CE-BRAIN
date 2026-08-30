"""Stage 3A R5 exploratory report with triangle axiom marked unidentifiable."""
from __future__ import annotations
import argparse, importlib.util, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
R4_PATH = ROOT / "examples" / "brain" / "ce_brain_stage3a_worm_metric_r4.py"
SPEC = importlib.util.spec_from_file_location("ce_brain_stage3a_worm_metric_r4_sealed", R4_PATH)
if SPEC is None or SPEC.loader is None: raise RuntimeError("STAGE3A_R5_APPARATUS_STOP: R4 unavailable")
r4 = importlib.util.module_from_spec(SPEC); sys.modules[SPEC.name] = r4; SPEC.loader.exec_module(r4)
base = r4.base
STOP = "STAGE3A_R5_APPARATUS_STOP"
CONTRACT = ROOT / "paper" / "검증_원장" / "CE_BRAIN_STAGE3A_R5_삼각진단불가_계약.md"
TEST_FILE = ROOT / "tests" / "test_ce_brain_stage3a_worm_metric_r5.py"
ARTIFACT_DIR = ROOT / "artifacts" / "brain" / "ce_brain_stage3a_worm_metric_r5"


def triangle_unidentifiable(rates):
    eligible = {pair for pair, row in rates.items() if row["subjects"] >= 3}
    nodes = sorted({node for pair in eligible for node in pair})
    triads = sum((a, b) in eligible and (b, c) in eligible and (a, c) in eligible
                 for a in nodes for b in nodes for c in nodes if len({a, b, c}) == 3)
    return {"status": "NOT_IDENTIFIABLE", "eligible_ordered_triads": int(triads),
            "required_ordered_triads": 1000, "violation_upper_95": 1.0}


def preregistered_files():
    return (*r4.preregistered_files(), Path(__file__).resolve(), TEST_FILE, CONTRACT)


def seal_r5(data_dir, artifact_dir):
    receipt = artifact_dir / base.SCHEMA_RECEIPT
    current = base.schema_inventory(data_dir, hash_raw=True)
    stored = base.json.loads(receipt.read_text(encoding="utf-8")); stored.pop("receipt_sha256", None)
    if base.canonical_json_bytes(current) != base.canonical_json_bytes(stored): raise RuntimeError(f"{STOP}: schema")
    files = {str(p.relative_to(ROOT)).replace("\\", "/"): base.sha256_file(p) for p in preregistered_files()}
    manifest = {"confirmation_values_opened": True, "confirmation_scientific_endpoints_opened": True,
                "confirmation_model_scores_computed": True, "confirmation_model_scores_observed": False,
                "diagnostic_access_scope": "R4_stopped_after_model_fit_before_result_write",
                "files": files, "inventory_sha256": base.EXPECTED_INVENTORY_SHA,
                "runtime": base.verify_runtime(), "schema_receipt_sha256": base.sha256_file(receipt)}
    manifest["manifest_sha256"] = base.write_json_once(artifact_dir / base.MANIFEST, manifest)
    return manifest


def verify_manifest_r5(data_dir, artifact_dir):
    path = artifact_dir / base.MANIFEST; manifest = base.json.loads(path.read_text(encoding="utf-8"))
    files = {str(p.relative_to(ROOT)).replace("\\", "/"): base.sha256_file(p) for p in preregistered_files()}
    base.load_inventory(data_dir, hash_raw=True)
    if (manifest.get("confirmation_model_scores_computed") is not True
            or manifest.get("confirmation_model_scores_observed") is not False
            or manifest.get("files") != files or manifest.get("runtime") != base.verify_runtime()
            or manifest.get("inventory_sha256") != base.EXPECTED_INVENTORY_SHA
            or manifest.get("schema_receipt_sha256") != base.sha256_file(artifact_dir / base.SCHEMA_RECEIPT)):
        raise RuntimeError(f"{STOP}: manifest")
    return base.sha256_file(path)


base.STOP = STOP; base.CONTRACT = CONTRACT; base.TEST_FILE = TEST_FILE
base.triangle_diagnostic = triangle_unidentifiable; base.preregistered_files = preregistered_files
r4.verify_manifest_r4 = verify_manifest_r5


def main():
    parser=argparse.ArgumentParser(); parser.add_argument("--data-dir",type=Path,required=True)
    parser.add_argument("--artifact-dir",type=Path,default=ARTIFACT_DIR)
    group=parser.add_mutually_exclusive_group(required=True)
    for name in ("schema-only","seal","execute","verify-result"): group.add_argument(f"--{name}",action="store_true")
    a=parser.parse_args()
    if a.schema_only: out=base.schema_receipt(a.data_dir,a.artifact_dir)
    elif a.seal: out=seal_r5(a.data_dir,a.artifact_dir)
    elif a.execute: out=base.execute(a.data_dir,a.artifact_dir)
    else: out=base.verify_result(a.data_dir,a.artifact_dir)
    print(base.json.dumps(out,sort_keys=True,allow_nan=False))
if __name__ == "__main__": main()
