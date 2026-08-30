"""Stage 3A R3: finite-observation amendment for ragged calcium traces."""

from __future__ import annotations

import argparse
import importlib.util
import sys
from pathlib import Path

import h5py
import numpy as np


ROOT = Path(__file__).resolve().parents[2]
R2_PATH = ROOT / "examples" / "brain" / "ce_brain_stage3a_worm_metric_r2.py"
SPEC = importlib.util.spec_from_file_location("ce_brain_stage3a_worm_metric_r2_sealed", R2_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("STAGE3A_R3_APPARATUS_STOP: sealed R2 module unavailable")
r2 = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = r2
SPEC.loader.exec_module(r2)
base = r2.base

STOP = "STAGE3A_R3_APPARATUS_STOP"
CONTRACT = ROOT / "paper" / "검증_원장" / "CE_BRAIN_STAGE3A_R3_결측관측_계약.md"
TEST_FILE = ROOT / "tests" / "test_ce_brain_stage3a_worm_metric_r3.py"
ARTIFACT_DIR = ROOT / "artifacts" / "brain" / "ce_brain_stage3a_worm_metric_r3"


def residual_z_finite(green: np.ndarray, red: np.ndarray, timestamps: np.ndarray,
                      starts: np.ndarray, stops: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    nonstim = np.ones(len(timestamps), dtype=bool)
    for start, stop in zip(starts, stops, strict=True):
        nonstim &= ~((timestamps >= start - 10) & (timestamps <= stop + 20))
    if np.sum(nonstim) < 20:
        nonstim = np.zeros(len(timestamps), dtype=bool)
        for start in starts:
            nonstim |= (timestamps >= start - 10) & (timestamps <= start - 2)
    if np.sum(nonstim) < 16:
        raise RuntimeError(f"{STOP}: nonstim frames")

    finite = np.isfinite(green) & np.isfinite(red)
    residual = np.full_like(green, np.nan, dtype=np.float64)
    centers = np.full(green.shape[1], np.nan)
    scales = np.full(green.shape[1], np.nan)
    for column in range(green.shape[1]):
        fit = nonstim & finite[:, column]
        if np.sum(fit) < 16:
            continue
        x, y = red[fit, column], green[fit, column]
        xm, ym = float(np.mean(x)), float(np.mean(y))
        variance = float(np.mean((x - xm) ** 2))
        slope = float(np.mean((x - xm) * (y - ym)) / variance) if variance > 0 else 0.0
        observed = finite[:, column]
        values = green[observed, column] - (ym - slope * xm) - red[observed, column] * slope
        residual[observed, column] = values
        center = float(np.median(residual[fit, column]))
        scale = float(1.4826 * np.median(np.abs(residual[fit, column] - center)))
        centers[column], scales[column] = center, scale
    positive = scales[np.isfinite(scales) & (scales > 0)]
    if len(positive) < max(10, green.shape[1] // 4):
        raise RuntimeError(f"{STOP}: residual scale")
    floor = float(np.quantile(positive, 0.10))
    valid_columns = np.isfinite(scales)
    scales[valid_columns] = np.maximum(scales[valid_columns], floor)
    z = (residual - centers[None, :]) / scales[None, :]
    return z, finite & np.isfinite(z)


def extract_subject(path: Path, template: dict[str, np.ndarray]) -> list[dict[str, object]]:
    subject = base.subject_id(path)
    with h5py.File(path, "r") as nwb:
        names, _ = base.canonical_map(nwb)
        table = nwb["intervals/OptogeneticStimulusTable"]
        starts = np.asarray(table["start_time"][...], dtype=np.float64)
        stops = np.asarray(table["stop_time"][...], dtype=np.float64)
        target_ids = np.asarray(table["target_pumpprobe_id"][...], dtype=np.float64)
        green_group = nwb["processing/ophys/GreenSignals/BaseGreenSignal"]
        red_group = nwb["processing/ophys/RedSignals/BaseRedSignal"]
        green = np.asarray(green_group["data"][...], dtype=np.float64)
        red = np.asarray(red_group["data"][...], dtype=np.float64)
        timestamps = np.asarray(green_group["timestamps"][...], dtype=np.float64)
        red_timestamps = np.asarray(red_group["timestamps"][...], dtype=np.float64)
        pump = nwb["processing/ophys/PumpProbeGreenSegmentations/PumpProbeGreenPlaneSegmentation"]
        receiver_ids = np.asarray(pump["id"][...], dtype=np.int64)
        if (green.shape != red.shape or green.shape[1] != len(receiver_ids)
                or not np.allclose(timestamps, red_timestamps, rtol=0, atol=1e-9)):
            raise RuntimeError(f"{STOP}: signal alignment")
        row_by_id = {int(receiver): index for index, receiver in enumerate(receiver_ids)}
        z, finite = residual_z_finite(green, red, timestamps, starts, stops)
        output: list[dict[str, object]] = []
        for event, (start, stop, target_value) in enumerate(zip(starts, stops, target_ids, strict=True)):
            if not np.isfinite(target_value):
                continue
            target_id = int(target_value)
            source = names.get(target_id)
            source_row = row_by_id.get(target_id)
            if source is None or source_row is None or source not in template:
                continue
            baseline = (timestamps >= start - 10) & (timestamps <= start - 2)
            response = (timestamps >= stop + 1) & (timestamps <= stop + 10)
            eligible = (np.sum(finite[baseline], axis=0) >= 8) & (np.sum(finite[response], axis=0) >= 8)
            if not eligible[source_row]:
                continue
            baseline_center = np.nanmedian(z[baseline], axis=0)
            event_z = z[response] - baseline_center[None, :]
            if not bool(base.consecutive(event_z[:, [source_row]], 4.0, positive=True)[0]):
                continue
            detected = base.consecutive(event_z, 3.0, positive=False)
            safe_abs = np.where(np.isfinite(event_z), np.abs(event_z), -np.inf)
            peak_index = np.argmax(safe_abs, axis=0)
            peak = event_z[peak_index, np.arange(event_z.shape[1])]
            response_times = timestamps[response] - stop
            latency = response_times[peak_index]
            for receiver_id, receiver_row in row_by_id.items():
                receiver = names.get(receiver_id)
                if (not eligible[receiver_row] or receiver is None or receiver == source
                        or receiver not in template):
                    continue
                output.append({"event": event, "latency": float(latency[receiver_row]),
                               "peak": float(peak[receiver_row]), "receiver": receiver,
                               "source": source, "subject": subject,
                               "y": int(detected[receiver_row])})
        return output


def preregistered_files() -> tuple[Path, ...]:
    return (*r2.preregistered_files(), Path(__file__).resolve(), TEST_FILE, CONTRACT)


def seal_r3(data_dir: Path, artifact_dir: Path) -> dict[str, object]:
    receipt_path = artifact_dir / base.SCHEMA_RECEIPT
    if not receipt_path.is_file():
        raise RuntimeError(f"{STOP}: schema receipt missing")
    current = base.schema_inventory(data_dir, hash_raw=True)
    stored = base.json.loads(receipt_path.read_text(encoding="utf-8"))
    stored.pop("receipt_sha256", None)
    if base.canonical_json_bytes(current) != base.canonical_json_bytes(stored):
        raise RuntimeError(f"{STOP}: schema receipt mutation")
    files = {str(path.relative_to(ROOT)).replace("\\", "/"): base.sha256_file(path)
             for path in preregistered_files()}
    manifest: dict[str, object] = {
        "confirmation_values_opened": True,
        "confirmation_scientific_endpoints_opened": False,
        "diagnostic_access_scope": "finite_fraction_and_missingness_only_after_R2_stop",
        "files": files,
        "inventory_sha256": base.EXPECTED_INVENTORY_SHA,
        "runtime": base.verify_runtime(),
        "schema_receipt_sha256": base.sha256_file(receipt_path),
    }
    manifest["manifest_sha256"] = base.write_json_once(artifact_dir / base.MANIFEST, manifest)
    return manifest


def verify_manifest_r3(data_dir: Path, artifact_dir: Path) -> str:
    path = artifact_dir / base.MANIFEST
    if not path.is_file():
        raise RuntimeError(f"{STOP}: manifest missing")
    manifest = base.json.loads(path.read_text(encoding="utf-8"))
    files = {str(file.relative_to(ROOT)).replace("\\", "/"): base.sha256_file(file)
             for file in preregistered_files()}
    base.load_inventory(data_dir, hash_raw=True)
    runtime = base.verify_runtime()
    if (manifest.get("confirmation_values_opened") is not True
            or manifest.get("confirmation_scientific_endpoints_opened") is not False
            or manifest.get("diagnostic_access_scope") != "finite_fraction_and_missingness_only_after_R2_stop"
            or manifest.get("files") != files
            or manifest.get("inventory_sha256") != base.EXPECTED_INVENTORY_SHA
            or manifest.get("runtime") != runtime
            or manifest.get("schema_receipt_sha256") != base.sha256_file(artifact_dir / base.SCHEMA_RECEIPT)):
        raise RuntimeError(f"{STOP}: manifest mutation")
    return base.sha256_file(path)


base.STOP = STOP
base.CONTRACT = CONTRACT
base.TEST_FILE = TEST_FILE
base.extract_subject = extract_subject
base.preregistered_files = preregistered_files
base.verify_manifest = verify_manifest_r3


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
        output = seal_r3(args.data_dir, args.artifact_dir)
    elif args.execute:
        output = base.execute(args.data_dir, args.artifact_dir)
    else:
        output = base.verify_result(args.data_dir, args.artifact_dir)
    print(base.json.dumps(output, sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()
