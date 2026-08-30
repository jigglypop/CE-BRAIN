"""Stage 3A R4 exploratory model competition after preregistered coverage stop."""

from __future__ import annotations

import argparse
import importlib.util
import sys
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[2]
R3_PATH = ROOT / "examples" / "brain" / "ce_brain_stage3a_worm_metric_r3.py"
SPEC = importlib.util.spec_from_file_location("ce_brain_stage3a_worm_metric_r3_sealed", R3_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("STAGE3A_R4_APPARATUS_STOP: sealed R3 module unavailable")
r3 = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = r3
SPEC.loader.exec_module(r3)
base = r3.base

STOP = "STAGE3A_R4_APPARATUS_STOP"
CONTRACT = ROOT / "paper" / "검증_원장" / "CE_BRAIN_STAGE3A_R4_탐색모형경쟁_계약.md"
TEST_FILE = ROOT / "tests" / "test_ce_brain_stage3a_worm_metric_r4.py"
ARTIFACT_DIR = ROOT / "artifacts" / "brain" / "ce_brain_stage3a_worm_metric_r4"
DECIDE = base.decide


def preregistered_files() -> tuple[Path, ...]:
    return (*r3.preregistered_files(), Path(__file__).resolve(), TEST_FILE, CONTRACT)


def seal_r4(data_dir: Path, artifact_dir: Path) -> dict[str, object]:
    receipt_path = artifact_dir / base.SCHEMA_RECEIPT
    if not receipt_path.is_file():
        raise RuntimeError(f"{STOP}: schema receipt missing")
    current = base.schema_inventory(data_dir, hash_raw=True)
    stored = base.json.loads(receipt_path.read_text(encoding="utf-8")); stored.pop("receipt_sha256", None)
    if base.canonical_json_bytes(current) != base.canonical_json_bytes(stored):
        raise RuntimeError(f"{STOP}: schema receipt mutation")
    files = {str(path.relative_to(ROOT)).replace("\\", "/"): base.sha256_file(path)
             for path in preregistered_files()}
    manifest: dict[str, object] = {
        "confirmation_values_opened": True,
        "confirmation_scientific_endpoints_opened": True,
        "confirmation_model_scores_opened": False,
        "diagnostic_access_scope": "R3_coverage_counts_and_positive_counts_before_R4",
        "files": files, "inventory_sha256": base.EXPECTED_INVENTORY_SHA,
        "runtime": base.verify_runtime(), "schema_receipt_sha256": base.sha256_file(receipt_path)}
    manifest["manifest_sha256"] = base.write_json_once(artifact_dir / base.MANIFEST, manifest)
    return manifest


def verify_manifest_r4(data_dir: Path, artifact_dir: Path) -> str:
    path = artifact_dir / base.MANIFEST
    manifest = base.json.loads(path.read_text(encoding="utf-8"))
    files = {str(file.relative_to(ROOT)).replace("\\", "/"): base.sha256_file(file)
             for file in preregistered_files()}
    base.load_inventory(data_dir, hash_raw=True)
    if (manifest.get("confirmation_scientific_endpoints_opened") is not True
            or manifest.get("confirmation_model_scores_opened") is not False
            or manifest.get("files") != files or manifest.get("runtime") != base.verify_runtime()
            or manifest.get("inventory_sha256") != base.EXPECTED_INVENTORY_SHA
            or manifest.get("schema_receipt_sha256") != base.sha256_file(artifact_dir / base.SCHEMA_RECEIPT)):
        raise RuntimeError(f"{STOP}: manifest mutation")
    return base.sha256_file(path)


def build_result(data_dir: Path, artifact_dir: Path) -> dict[str, object]:
    manifest_sha = verify_manifest_r4(data_dir, artifact_dir)
    _, paths = base.load_inventory(data_dir, hash_raw=False)
    template = base.build_template(base.collect_coordinates(paths))
    rows = [row for path in paths for row in r3.extract_subject(path, template)]
    development = [row for row in rows if base.subject_development(row["subject"])
                   and not base.source_holdout(row["source"])]
    confirmation = [row for row in rows if not base.subject_development(row["subject"])]
    development_pairs = {(row["source"], row["receiver"]) for row in development}
    common_rows = [row for row in confirmation if not base.source_holdout(row["source"])
                   and (row["source"], row["receiver"]) in development_pairs]
    unseen_rows = [row for row in confirmation if base.source_holdout(row["source"])]
    if (len(development) < 10_000 or len(confirmation) < 4_000
            or len(common_rows) < 1_500 or len(unseen_rows) < 1_000):
        raise RuntimeError(f"{STOP}: exploratory coverage")
    dev_arrays = base.feature_arrays(development, template)
    common_arrays = base.feature_arrays(common_rows, template)
    unseen_arrays = base.feature_arrays(unseen_rows, template)
    models = base.fit_models(dev_arrays, template)
    common_losses = base.subject_losses(common_arrays, base.predict_models(models, common_arrays, include_graph=True))
    unseen_losses = base.subject_losses(unseen_arrays, base.predict_models(models, unseen_arrays, include_graph=False))
    common_score = base.score_set(common_losses, 100)
    unseen_score = base.score_set(unseen_losses, 200)
    rng = np.random.Generator(np.random.PCG64(base.SEED + 250))
    f_vs_r = base.bootstrap_improvement(common_losses, "F", "R", rng)
    directional = {"improvement": (common_score["losses"]["R"] - common_score["losses"]["F"])
                   / common_score["losses"]["R"], "lower_95": float(np.quantile(f_vs_r, .025)),
                   "median": float(np.median(f_vs_r))}
    rates = base.pair_rates(confirmation)
    symmetry = base.symmetry_diagnostic(rates)
    triangle = base.triangle_diagnostic(rates)
    candidate = DECIDE(common_score, unseen_score, symmetry, triangle, directional)
    result: dict[str, object] = {
        "axioms": {"directionality_F_vs_R": directional, "symmetry": symmetry, "triangle": triangle},
        "bootstrap": {"repetitions": base.BOOTSTRAPS, "seed": base.SEED},
        "candidate_decision": candidate, "decision": f"EXPLORATORY_{candidate}",
        "claim_ceiling": "post-coverage-stop exploratory C. elegans representation result",
        "coverage": {"development_rows": len(development), "confirmation_rows": len(confirmation),
                     "common_pair_rows": len(common_rows), "unseen_source_rows": len(unseen_rows),
                     "development_subjects": len({row['subject'] for row in development}),
                     "confirmation_subjects": len({row['subject'] for row in confirmation}),
                     "eligible_stimulus_events": len({(row['subject'], row['event']) for row in rows}),
                     "template_nodes": len(template),
                     "development_detected_edges": int(sum(row['y'] for row in development)),
                     "confirmation_detected_edges": int(sum(row['y'] for row in confirmation))},
        "heldout_animal_common_pair": common_score, "heldout_source": unseen_score,
        "manifest_sha256": manifest_sha, "model_ridges": models["ridges"],
        "stage4_authorized": False}
    validate_result(result)
    return result


def validate_result(result: dict[str, object]) -> None:
    candidate = DECIDE(result["heldout_animal_common_pair"], result["heldout_source"],
                       result["axioms"]["symmetry"], result["axioms"]["triangle"],
                       result["axioms"]["directionality_F_vs_R"])
    if (result.get("candidate_decision") != candidate
            or result.get("decision") != f"EXPLORATORY_{candidate}"
            or result.get("stage4_authorized") is not False):
        raise RuntimeError(f"{STOP}: result decision")


base.STOP = STOP
base.CONTRACT = CONTRACT
base.TEST_FILE = TEST_FILE
base.preregistered_files = preregistered_files
base.verify_manifest = verify_manifest_r4
base.build_result = build_result
base.validate_result = validate_result


def main() -> None:
    parser = argparse.ArgumentParser(); parser.add_argument("--data-dir", type=Path, required=True)
    parser.add_argument("--artifact-dir", type=Path, default=ARTIFACT_DIR)
    actions = parser.add_mutually_exclusive_group(required=True)
    for name in ("schema-only", "seal", "execute", "verify-result"):
        actions.add_argument(f"--{name}", action="store_true")
    args = parser.parse_args()
    if args.schema_only: output = base.schema_receipt(args.data_dir, args.artifact_dir)
    elif args.seal: output = seal_r4(args.data_dir, args.artifact_dir)
    elif args.execute: output = base.execute(args.data_dir, args.artifact_dir)
    else: output = base.verify_result(args.data_dir, args.artifact_dir)
    print(base.json.dumps(output, sort_keys=True, allow_nan=False))


if __name__ == "__main__": main()
