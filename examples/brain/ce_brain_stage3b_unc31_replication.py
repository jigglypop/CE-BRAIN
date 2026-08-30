"""CE-BRAIN Stage 3B: WT-to-unc-31 cross-genotype representation replication."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
import os
import platform
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

import numpy as np


ROOT = Path(__file__).resolve().parents[2]
STAGE3A_PATH = ROOT / "examples" / "brain" / "ce_brain_stage3a_worm_metric.py"
SPEC = importlib.util.spec_from_file_location("ce_brain_stage3a_model_library", STAGE3A_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("STAGE3B_APPARATUS_STOP: Stage 3A model library unavailable")
s3a = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = s3a
SPEC.loader.exec_module(s3a)

STOP = "STAGE3B_APPARATUS_STOP"
CONTRACT = ROOT / "paper" / "검증_원장" / "CE_BRAIN_STAGE3B_UNC31_교란외삽_계약.md"
TEST_FILE = ROOT / "tests" / "test_ce_brain_stage3b_unc31_replication.py"
DEFAULT_DATA = ROOT / "data" / "external" / "ce_brain_stage3_osf"
DEFAULT_ARTIFACT = ROOT / "artifacts" / "brain" / "ce_brain_stage3b_unc31_replication"
INVENTORY = "stage3b-asset-inventory.json"
SCHEMA = "stage3b-schema-receipt.json"
DEVELOPMENT = "stage3b-development-receipt.json"
MANIFEST = "stage3b-manifest.json"
RESULT = "stage3b-result.json"
VALIDATION = "stage3b-validation-receipt.json"
WT_ARCHIVE_SHA = "d6e7b3d93175b40b7ae17bde2182835e9c2144388142c522ee9be3832f6ce836"
UNC31_ARCHIVE_SHA = "8b99f6610dbb2d6ab0b8dd6ad15646fe1c120da25dd9bb725f36f530b2af321a"
POSITIONS_SHA = "b854b039929185f22dcb2eadce24b08408bfdec80f1a88581fe33edb382ede40"
SEED = 20_260_906
BOOTSTRAPS = 1_999
SUFFIXES = ("ds_name", "labels", "stim_neurons", "stim_volume_i", "t", "gcamp")
EXPECTED_RUNTIME = {"implementation": "CPython", "python": "3.11.9", "numpy": "2.4.6",
                    "scipy": "1.17.1", "h5py": "3.16.0"}


def canonical_json_bytes(value: Any) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n").encode()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while chunk := stream.read(8 * 1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def write_once(path: Path, value: Any) -> str:
    if path.exists():
        raise RuntimeError(f"{STOP}: refusing to overwrite {path.name}")
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = canonical_json_bytes(value)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    temporary.write_bytes(payload)
    temporary.replace(path)
    return hashlib.sha256(payload).hexdigest()


def runtime_identity() -> dict[str, str]:
    import h5py, scipy
    return {"implementation": platform.python_implementation(), "python": platform.python_version(),
            "numpy": np.__version__, "scipy": scipy.__version__, "h5py": h5py.__version__,
            "executable": str(Path(sys.executable).resolve())}


def verify_runtime() -> dict[str, str]:
    row = runtime_identity()
    if any(row[key] != value for key, value in EXPECTED_RUNTIME.items()):
        raise RuntimeError(f"{STOP}: runtime identity")
    return row


def cohort_dir(data_dir: Path, cohort: str) -> Path:
    return data_dir / ("exported_data" if cohort == "WT" else "exported_data_unc31")


def subject_ids(folder: Path) -> list[int]:
    return sorted(int(path.name.split("_", 1)[0]) for path in folder.glob("*_ds_name.txt"))


def create_inventory(data_dir: Path, artifact_dir: Path) -> dict[str, Any]:
    archives = {"WT": data_dir / "exported_data.tar.gz",
                "UNC31": data_dir / "exported_data_unc31.tar.gz",
                "positions": data_dir / "anatlas_neuron_positions.txt"}
    expected = {"WT": WT_ARCHIVE_SHA, "UNC31": UNC31_ARCHIVE_SHA, "positions": POSITIONS_SHA}
    archive_rows = {}
    for name, path in archives.items():
        digest = sha256_file(path)
        if digest != expected[name]:
            raise RuntimeError(f"{STOP}: {name} archive identity")
        archive_rows[name] = {"bytes": path.stat().st_size, "path": path.name, "sha256": digest}
    files = []
    for cohort in ("WT", "UNC31"):
        folder = cohort_dir(data_dir, cohort)
        for subject in subject_ids(folder):
            for suffix in SUFFIXES:
                path = folder / f"{subject}_{suffix}.txt"
                if not path.is_file():
                    raise RuntimeError(f"{STOP}: missing {path.name}")
                files.append({"bytes": path.stat().st_size, "cohort": cohort,
                              "name": path.name, "sha256": sha256_file(path)})
    inventory = {"archives": archive_rows, "files": files, "source": "OSF E2SYT",
                 "subjects": {"WT": len(subject_ids(cohort_dir(data_dir, "WT"))),
                              "UNC31": len(subject_ids(cohort_dir(data_dir, "UNC31")))}}
    inventory["inventory_sha256"] = write_once(artifact_dir / INVENTORY, inventory)
    return inventory


def verify_inventory(data_dir: Path, artifact_dir: Path, *, hash_files: bool) -> str:
    path = artifact_dir / INVENTORY
    if not path.is_file():
        raise RuntimeError(f"{STOP}: inventory missing")
    inventory = json.loads(path.read_text(encoding="utf-8"))
    if inventory.get("subjects") != {"WT": 113, "UNC31": 18}:
        raise RuntimeError(f"{STOP}: inventory subjects")
    for name, expected in (("WT", WT_ARCHIVE_SHA), ("UNC31", UNC31_ARCHIVE_SHA),
                           ("positions", POSITIONS_SHA)):
        if inventory["archives"][name]["sha256"] != expected:
            raise RuntimeError(f"{STOP}: inventory archive")
    for row in inventory["files"]:
        file = cohort_dir(data_dir, row["cohort"]) / row["name"]
        if not file.is_file() or file.stat().st_size != row["bytes"]:
            raise RuntimeError(f"{STOP}: extracted asset")
        if hash_files and sha256_file(file) != row["sha256"]:
            raise RuntimeError(f"{STOP}: extracted asset hash")
    return sha256_file(path)


def load_positions(path: Path) -> dict[str, np.ndarray]:
    lines = path.read_text(encoding="utf-8").splitlines()
    labels = lines[0].lstrip("#").split()
    values = np.loadtxt(path, comments="#", dtype=np.float64)
    if values.shape != (len(labels), 3):
        raise RuntimeError(f"{STOP}: anatomical coordinate schema")
    median = np.median(values, axis=0)
    scale = np.quantile(values, .75, axis=0) - np.quantile(values, .25, axis=0)
    values = (values - median) / scale
    grouped: dict[str, list[np.ndarray]] = defaultdict(list)
    for label, value in zip(labels, values, strict=True):
        grouped[label].append(value)
    return {label: np.median(rows, axis=0) for label, rows in grouped.items()}


def load_labels(path: Path) -> list[str]:
    labels = path.read_text(encoding="utf-8").split("\n")
    if labels and labels[-1] == "":
        labels.pop()
    return [label.strip() for label in labels]


def signal_columns(path: Path) -> int:
    with path.open("r", encoding="utf-8") as stream:
        return len(stream.readline().split())


def schema_summary(data_dir: Path) -> dict[str, Any]:
    template = load_positions(data_dir / "anatlas_neuron_positions.txt")
    output: dict[str, Any] = {"confirmation_values_opened": False, "cohorts": {}}
    for cohort in ("WT", "UNC31"):
        folder = cohort_dir(data_dir, cohort)
        subjects = []; pairs: dict[tuple[str, str], set[int]] = defaultdict(set)
        source_events = 0; potential_rows = 0; mismatched = []
        for subject in subject_ids(folder):
            labels = load_labels(folder / f"{subject}_labels.txt")
            columns = signal_columns(folder / f"{subject}_gcamp.txt")
            stimuli = np.loadtxt(folder / f"{subject}_stim_neurons.txt", dtype=np.int64, ndmin=1)
            volumes = np.loadtxt(folder / f"{subject}_stim_volume_i.txt", dtype=np.int64, ndmin=1)
            if len(stimuli) != len(volumes):
                raise RuntimeError(f"{STOP}: stimulus schema")
            if len(labels) != columns:
                mismatched.append(subject); continue
            receivers = {label for label in labels if label in template}
            valid_sources = []
            for index in stimuli:
                if 0 <= index < columns and labels[index] in template:
                    source = labels[index]; valid_sources.append(source); source_events += 1
                    potential_rows += len(receivers - {source})
                    for receiver in receivers - {source}:
                        pairs[(source, receiver)].add(subject)
            subjects.append({"canonical_receivers": len(receivers), "canonical_source_events": len(valid_sources),
                             "signal_columns": columns, "stimuli": len(stimuli), "subject": subject})
        eligible = {pair for pair, owners in pairs.items() if len(owners) >= 3}
        nodes = sorted({node for pair in eligible for node in pair})
        triads = sum((a, b) in eligible and (b, c) in eligible and (a, c) in eligible
                     for a in nodes for b in nodes for c in nodes if len({a, b, c}) == 3)
        bidirectional = {tuple(sorted((a, b))) for a, b in pairs if (b, a) in pairs}
        output["cohorts"][cohort] = {
            "bidirectional_pairs": len(bidirectional), "canonical_source_events": source_events,
            "directed_pairs": len(pairs), "directed_pairs_subjects_ge_3": len(eligible),
            "mismatched_subjects_excluded": mismatched, "potential_rows": potential_rows,
            "subjects": subjects, "subjects_retained": len(subjects), "triads_subjects_ge_3": triads}
    return output


def schema_receipt(data_dir: Path, artifact_dir: Path) -> dict[str, Any]:
    verify_inventory(data_dir, artifact_dir, hash_files=True)
    row = schema_summary(data_dir)
    row["schema_receipt_sha256"] = write_once(artifact_dir / SCHEMA, row)
    return row


def run_length_at_least(mask: np.ndarray, length: int) -> np.ndarray:
    if mask.shape[0] < length:
        return np.zeros(mask.shape[1], dtype=bool)
    acc = mask.astype(np.int16)
    total = np.cumsum(acc, axis=0)
    windows = total[length - 1:].copy()
    if length < len(mask):
        windows[1:] -= total[:-length]
    return np.any(windows >= length, axis=0)


def extract_subject(folder: Path, subject: int, template: dict[str, np.ndarray]) -> list[dict[str, Any]]:
    labels = load_labels(folder / f"{subject}_labels.txt")
    signal = np.loadtxt(folder / f"{subject}_gcamp.txt", dtype=np.float64, ndmin=2)
    time = np.loadtxt(folder / f"{subject}_t.txt", dtype=np.float64, ndmin=1)
    stimuli = np.loadtxt(folder / f"{subject}_stim_neurons.txt", dtype=np.int64, ndmin=1)
    volumes = np.loadtxt(folder / f"{subject}_stim_volume_i.txt", dtype=np.int64, ndmin=1)
    if signal.shape != (len(time), len(labels)):
        return []
    output = []
    for event, (source_index, volume) in enumerate(zip(stimuli, volumes, strict=True)):
        if not (0 <= source_index < len(labels)) or labels[source_index] not in template:
            continue
        source = labels[source_index]
        baseline_i = np.flatnonzero((time >= time[volume] - 10) & (time <= time[volume] - 2))
        next_limit = volumes[event + 1] - 20 if event + 1 < len(volumes) else volume + 41
        response_i = np.arange(volume + 6, min(volume + 41, next_limit, len(time)))
        if len(baseline_i) < 24 or len(response_i) < 16:
            continue
        baseline = signal[baseline_i]
        response = signal[response_i]
        finite_baseline = np.sum(np.isfinite(baseline), axis=0) >= 24
        finite_response = np.sum(np.isfinite(response), axis=0) >= 16
        center = np.nanmedian(baseline, axis=0)
        mad = 1.4826 * np.nanmedian(np.abs(baseline - center[None, :]), axis=0)
        positive = mad[np.isfinite(mad) & (mad > 0)]
        if len(positive) < 10:
            continue
        mad = np.maximum(mad, float(np.quantile(positive, .10)))
        denom_positive = np.abs(center[np.isfinite(center) & (np.abs(center) > 0)])
        if len(denom_positive) < 10:
            continue
        denominator = np.maximum(np.abs(center), float(np.quantile(denom_positive, .10)))
        z = (response - center[None, :]) / mad[None, :]
        dff = np.abs(response - center[None, :]) / denominator[None, :]
        detected = run_length_at_least(np.abs(z) >= 3.0, 4) & (np.nanmax(dff, axis=0) >= .10)
        eligible = finite_baseline & finite_response & np.isfinite(center) & np.isfinite(mad)
        by_label: dict[str, list[int]] = defaultdict(list)
        for column, label in enumerate(labels):
            if label in template and label != source and eligible[column]:
                by_label[label].append(column)
        for receiver, columns in by_label.items():
            output.append({"event": event, "receiver": receiver, "source": source, "subject": subject,
                           "y": int(np.any(detected[columns]))})
    return output


def cohort_rows(data_dir: Path, cohort: str, template: dict[str, np.ndarray]) -> list[dict[str, Any]]:
    folder = cohort_dir(data_dir, cohort)
    return [row for subject in subject_ids(folder) for row in extract_subject(folder, subject, template)]


def development_receipt(data_dir: Path, artifact_dir: Path) -> dict[str, Any]:
    verify_inventory(data_dir, artifact_dir, hash_files=True)
    template = load_positions(data_dir / "anatlas_neuron_positions.txt")
    rows = cohort_rows(data_dir, "WT", template)
    training = [row for row in rows if not s3a.source_holdout(row["source"])]
    row = {"confirmation_values_opened": False, "eligible_events": len({(x["subject"], x["event"]) for x in rows}),
           "positive_edges": int(sum(x["y"] for x in training)), "rows": len(training),
           "source_holdout_rows": len(rows) - len(training), "subjects": len({x["subject"] for x in training}),
           "template_nodes": len(template)}
    row["development_receipt_sha256"] = write_once(artifact_dir / DEVELOPMENT, row)
    return row


def preregistered_files() -> tuple[Path, ...]:
    return (Path(__file__).resolve(), TEST_FILE, CONTRACT, STAGE3A_PATH)


def seal(data_dir: Path, artifact_dir: Path) -> dict[str, Any]:
    verify_inventory(data_dir, artifact_dir, hash_files=True)
    schema_path, dev_path = artifact_dir / SCHEMA, artifact_dir / DEVELOPMENT
    if not schema_path.is_file() or not dev_path.is_file():
        raise RuntimeError(f"{STOP}: preregistration receipts missing")
    if canonical_json_bytes(schema_summary(data_dir)) != canonical_json_bytes(json.loads(schema_path.read_text())):
        raise RuntimeError(f"{STOP}: schema receipt mutation")
    files = {str(path.relative_to(ROOT)).replace("\\", "/"): sha256_file(path)
             for path in preregistered_files()}
    manifest = {"confirmation_values_opened": False, "development_receipt_sha256": sha256_file(dev_path),
                "files": files, "inventory_sha256": sha256_file(artifact_dir / INVENTORY),
                "runtime": verify_runtime(), "schema_receipt_sha256": sha256_file(schema_path)}
    manifest["manifest_sha256"] = write_once(artifact_dir / MANIFEST, manifest)
    return manifest


def verify_manifest(data_dir: Path, artifact_dir: Path) -> str:
    path = artifact_dir / MANIFEST
    manifest = json.loads(path.read_text(encoding="utf-8"))
    files = {str(file.relative_to(ROOT)).replace("\\", "/"): sha256_file(file)
             for file in preregistered_files()}
    verify_inventory(data_dir, artifact_dir, hash_files=True)
    if (manifest.get("confirmation_values_opened") is not False or manifest.get("files") != files
            or manifest.get("runtime") != verify_runtime()
            or manifest.get("inventory_sha256") != sha256_file(artifact_dir / INVENTORY)
            or manifest.get("schema_receipt_sha256") != sha256_file(artifact_dir / SCHEMA)
            or manifest.get("development_receipt_sha256") != sha256_file(artifact_dir / DEVELOPMENT)):
        raise RuntimeError(f"{STOP}: manifest mutation")
    return sha256_file(path)


def axiom_diagnostics(rates: dict[tuple[str, str], dict[str, Any]]) -> tuple[dict[str, Any], dict[str, Any]]:
    diffs = [abs(row["p"] - rates[(b, a)]["p"]) for (a, b), row in rates.items()
             if a < b and (b, a) in rates and row["subjects"] >= 3 and rates[(b, a)]["subjects"] >= 3]
    symmetry = {"bidirectional_pairs": len(diffs), "median_abs_difference": float(np.median(diffs)) if diffs else None}
    eligible = {pair: row for pair, row in rates.items() if row["subjects"] >= 3}
    nodes = sorted({node for pair in eligible for node in pair}); triads = []
    for a in nodes:
        for b in nodes:
            if a == b or (a, b) not in eligible: continue
            for c in nodes:
                if c in (a, b) or (b, c) not in eligible or (a, c) not in eligible: continue
                triads.append((a, b, c))
    if len(triads) < 1_000:
        triangle = {"status": "NOT_IDENTIFIABLE", "eligible_ordered_triads": len(triads),
                    "violation_upper_95": 1.0}
    else:
        rng = np.random.Generator(np.random.PCG64(SEED + 302))
        if len(triads) > 50_000:
            triads = [triads[index] for index in np.sort(rng.choice(len(triads), 50_000, replace=False))]
        violation = np.asarray([-math.log(eligible[(a, c)]["p"]) > 1.1 *
                                (-math.log(eligible[(a, b)]["p"]) - math.log(eligible[(b, c)]["p"]))
                                for a, b, c in triads], dtype=float)
        boot = rng.binomial(len(violation), float(violation.mean()), size=BOOTSTRAPS) / len(violation)
        triangle = {"status": "IDENTIFIED", "eligible_ordered_triads": len(triads),
                    "violation_rate": float(violation.mean()),
                    "violation_upper_95": float(np.quantile(boot, .975))}
    return symmetry, triangle


def cross_decision(common: dict[str, Any], unseen: dict[str, Any], triangle: dict[str, Any],
                   directional: dict[str, float]) -> str:
    common_winner = s3a.decisive_winner(common); unseen_winner = s3a.decisive_winner(unseen)
    if common_winner is None or unseen_winner is None or common_winner != unseen_winner:
        return "CROSS_GENOTYPE_REPRESENTATION_TENSION"
    winner = common_winner
    if winner == "R" and (triangle["status"] != "IDENTIFIED" or triangle["violation_upper_95"] > .10
                           or directional["lower_95"] > 0):
        return "CROSS_GENOTYPE_REPRESENTATION_TENSION"
    return f"CROSS_GENOTYPE_{winner}_RETAINED"


def build_result(data_dir: Path, artifact_dir: Path) -> dict[str, Any]:
    manifest_sha = verify_manifest(data_dir, artifact_dir)
    template = load_positions(data_dir / "anatlas_neuron_positions.txt")
    wt = cohort_rows(data_dir, "WT", template)
    development = [row for row in wt if not s3a.source_holdout(row["source"])]
    unc = cohort_rows(data_dir, "UNC31", template)
    development_pairs = {(row["source"], row["receiver"]) for row in development}
    common_rows = [row for row in unc if not s3a.source_holdout(row["source"])
                   and (row["source"], row["receiver"]) in development_pairs]
    unseen_rows = [row for row in unc if s3a.source_holdout(row["source"])]
    if (len(development) < 50_000 or len(unc) < 15_000 or len(common_rows) < 5_000
            or len(unseen_rows) < 2_000 or len({row["subject"] for row in unc}) < 12):
        raise RuntimeError(f"{STOP}: endpoint coverage")
    dev_arrays = s3a.feature_arrays(development, template)
    common_arrays = s3a.feature_arrays(common_rows, template)
    unseen_arrays = s3a.feature_arrays(unseen_rows, template)
    models = s3a.fit_models(dev_arrays, template)
    common_losses = s3a.subject_losses(common_arrays, s3a.predict_models(models, common_arrays, include_graph=True))
    unseen_losses = s3a.subject_losses(unseen_arrays, s3a.predict_models(models, unseen_arrays, include_graph=False))
    common_score = s3a.score_set(common_losses, 410); unseen_score = s3a.score_set(unseen_losses, 510)
    rng = np.random.Generator(np.random.PCG64(SEED + 250))
    f_vs_r = s3a.bootstrap_improvement(common_losses, "F", "R", rng)
    directional = {"improvement": (common_score["losses"]["R"] - common_score["losses"]["F"])
                   / common_score["losses"]["R"], "lower_95": float(np.quantile(f_vs_r, .025)),
                   "median": float(np.median(f_vs_r))}
    rates = s3a.pair_rates(unc); symmetry, triangle = axiom_diagnostics(rates)
    decision = cross_decision(common_score, unseen_score, triangle, directional)
    result = {"axioms": {"directionality_F_vs_R": directional, "symmetry": symmetry, "triangle": triangle},
              "bootstrap": {"repetitions": BOOTSTRAPS, "seed": SEED},
              "claim_ceiling": "WT-to-unc-31 C. elegans cross-genotype representation replication",
              "coverage": {"common_pair_rows": len(common_rows), "confirmation_rows": len(unc),
                           "confirmation_subjects": len({row['subject'] for row in unc}),
                           "development_rows": len(development), "development_subjects": len({row['subject'] for row in development}),
                           "unseen_source_rows": len(unseen_rows)},
              "decision": decision, "heldout_unc31_common_pair": common_score,
              "heldout_unc31_unseen_source": unseen_score, "manifest_sha256": manifest_sha,
              "model_ridges": models["ridges"], "stage4_authorized": False}
    validate_result(result)
    return result


def validate_result(result: dict[str, Any]) -> None:
    expected = cross_decision(result["heldout_unc31_common_pair"], result["heldout_unc31_unseen_source"],
                              result["axioms"]["triangle"], result["axioms"]["directionality_F_vs_R"])
    if result.get("decision") != expected or result.get("stage4_authorized") is not False:
        raise RuntimeError(f"{STOP}: decision integrity")


def execute(data_dir: Path, artifact_dir: Path) -> dict[str, Any]:
    result = build_result(data_dir, artifact_dir)
    digest = write_once(artifact_dir / RESULT, result)
    return {"result_sha256": digest, **result}


def verify_result(data_dir: Path, artifact_dir: Path) -> dict[str, Any]:
    path = artifact_dir / RESULT
    stored = json.loads(path.read_text(encoding="utf-8")); validate_result(stored)
    recomputed = build_result(data_dir, artifact_dir)
    if canonical_json_bytes(stored) != canonical_json_bytes(recomputed):
        raise RuntimeError(f"{STOP}: raw recomputation mismatch")
    receipt = {"decision": stored["decision"], "raw_recomputed": True,
               "result_sha256": sha256_file(path), "status": "PASS"}
    receipt["validation_receipt_sha256"] = write_once(artifact_dir / VALIDATION, receipt)
    return receipt


def main() -> None:
    parser = argparse.ArgumentParser(); parser.add_argument("--data-dir", type=Path, default=DEFAULT_DATA)
    parser.add_argument("--artifact-dir", type=Path, default=DEFAULT_ARTIFACT)
    group = parser.add_mutually_exclusive_group(required=True)
    for action in ("inventory", "schema-only", "development-only", "seal", "execute", "verify-result"):
        group.add_argument(f"--{action}", action="store_true")
    args = parser.parse_args()
    if args.inventory: output = create_inventory(args.data_dir, args.artifact_dir)
    elif args.schema_only: output = schema_receipt(args.data_dir, args.artifact_dir)
    elif args.development_only: output = development_receipt(args.data_dir, args.artifact_dir)
    elif args.seal: output = seal(args.data_dir, args.artifact_dir)
    elif args.execute: output = execute(args.data_dir, args.artifact_dir)
    else: output = verify_result(args.data_dir, args.artifact_dir)
    print(json.dumps(output, sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()
