from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
V1_PATH = HERE / "audit_randi_2023_source_schema.py"
SPEC = importlib.util.spec_from_file_location("randi_source_audit_v1", V1_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"cannot load v1 audit helpers: {V1_PATH}")
V1 = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(V1)

EXPECTED_USABLE = {"wt": 112, "unc31": 15}
ALLOWED_SENTINELS = {-3, -2, -1}


def audit_group(name: str, root: Path, archive: Path) -> dict[str, object]:
    expected = V1.EXPECTED[name]
    errors: list[str] = []
    archive_size = archive.stat().st_size
    archive_digest = V1.sha256(archive)
    if archive_size != expected["archive_bytes"]:
        errors.append(
            f"archive bytes: expected={expected['archive_bytes']}, actual={archive_size}"
        )
    if archive_digest != expected["archive_sha256"]:
        errors.append(
            f"archive sha256: expected={expected['archive_sha256']}, actual={archive_digest}"
        )

    expected_ids = list(range(int(expected["recordings"])))
    observed_ids = sorted(
        int(path.name[: -len("_ds_name.txt")])
        for path in root.glob("*_ds_name.txt")
    )
    if observed_ids != expected_ids:
        errors.append(
            f"recording ids: expected=0..{expected_ids[-1]}, actual={observed_ids}"
        )
    expected_file_count = int(expected["recordings"]) * len(V1.SUFFIXES)
    observed_file_count = sum(path.is_file() for path in root.iterdir())
    if observed_file_count != expected_file_count:
        errors.append(
            f"file count: expected={expected_file_count}, actual={observed_file_count}"
        )

    summaries: list[dict[str, object]] = []
    ds_names: list[str] = []
    for record_id in observed_ids:
        paths = {
            suffix: root / f"{record_id}_{suffix}.txt" for suffix in V1.SUFFIXES
        }
        missing = [str(path) for path in paths.values() if not path.is_file()]
        if missing:
            errors.append(f"recording {record_id} missing files: {missing}")
            continue

        ds_name_lines = V1.lines(paths["ds_name"])
        labels = V1.lines(paths["labels"])
        timestamps = V1.lines(paths["t"])
        stim_neurons_text = V1.lines(paths["stim_neurons"])
        stim_volume_text = V1.lines(paths["stim_volume_i"])
        if len(ds_name_lines) != 1 or not ds_name_lines[0].strip():
            errors.append(f"recording {record_id} invalid ds_name")
        else:
            ds_names.append(ds_name_lines[0].strip())

        try:
            gcamp_rows, gcamp_columns = V1.scan_gcamp(paths["gcamp"])
        except ValueError as exc:
            errors.append(str(exc))
            continue
        if len(timestamps) != gcamp_rows:
            errors.append(
                f"recording {record_id} time rows={len(timestamps)} "
                f"but GCaMP rows={gcamp_rows}"
            )
        if len(labels) < gcamp_columns:
            errors.append(
                f"recording {record_id} labels={len(labels)} "
                f"but GCaMP columns={gcamp_columns}"
            )
        elif any(label.strip() for label in labels[gcamp_columns:]):
            errors.append(f"recording {record_id} nonblank label padding")
        aligned_labels = labels[:gcamp_columns]

        if len(stim_neurons_text) != len(stim_volume_text):
            errors.append(
                f"recording {record_id} stim neurons={len(stim_neurons_text)} "
                f"but stim volumes={len(stim_volume_text)}"
            )
        try:
            stim_neurons = [int(value) for value in stim_neurons_text]
            stim_volumes = [int(value) for value in stim_volume_text]
        except ValueError as exc:
            errors.append(f"recording {record_id} non-integer stimulus index: {exc}")
            continue
        if any(
            value not in ALLOWED_SENTINELS and not 0 <= value < gcamp_columns
            for value in stim_neurons
        ):
            errors.append(f"recording {record_id} out-of-range stimulated neuron")
        if any(value < 0 or value >= gcamp_rows for value in stim_volumes):
            errors.append(f"recording {record_id} out-of-range stimulus volume")

        summaries.append(
            {
                "recording_id": record_id,
                "timepoints": gcamp_rows,
                "neurons": gcamp_columns,
                "identified_labels": sum(bool(label.strip()) for label in aligned_labels),
                "stimuli": len(stim_volumes),
                "identity_usable": any(label.strip() for label in aligned_labels),
            }
        )

    if len(ds_names) != len(set(ds_names)):
        errors.append("duplicate ds_name values")
    usable_ids = [
        int(summary["recording_id"])
        for summary in summaries
        if summary["identity_usable"]
    ]
    if len(usable_ids) != EXPECTED_USABLE[name]:
        errors.append(
            f"identity usable recordings: expected={EXPECTED_USABLE[name]}, "
            f"actual={len(usable_ids)}"
        )

    def extent(field: str) -> dict[str, int] | None:
        values = [int(summary[field]) for summary in summaries]
        if not values:
            return None
        return {"min": min(values), "max": max(values)}

    return {
        "name": name,
        "archive": str(archive),
        "archive_bytes": archive_size,
        "archive_sha256": archive_digest,
        "recordings": len(summaries),
        "identity_usable_recordings": len(usable_ids),
        "identity_usable_ids": usable_ids,
        "identity_excluded_ids": sorted(set(observed_ids) - set(usable_ids)),
        "timepoints": extent("timepoints"),
        "neurons": extent("neurons"),
        "identified_labels": extent("identified_labels"),
        "stimuli": extent("stimuli"),
        "errors": errors,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--wt-root", type=Path, required=True)
    parser.add_argument("--wt-archive", type=Path, required=True)
    parser.add_argument("--unc31-root", type=Path, required=True)
    parser.add_argument("--unc31-archive", type=Path, required=True)
    args = parser.parse_args()
    groups = [
        audit_group("wt", args.wt_root.resolve(), args.wt_archive.resolve()),
        audit_group(
            "unc31", args.unc31_root.resolve(), args.unc31_archive.resolve()
        ),
    ]
    errors = [error for group in groups for error in group["errors"]]
    receipt = {
        "decision": (
            "RANDI_2023_SOURCE_SCHEMA_V2_PASS"
            if not errors
            else "RANDI_2023_SOURCE_SCHEMA_V2_FAIL"
        ),
        "scope": "source_and_schema_only_no_biological_endpoint",
        "provider_export_code": {
            "repository": "https://github.com/leiferlab/pumpprobe",
            "commit": "1dbc5e0a2b609d54bc9b1c90c73d4e3bf183d3c7",
        },
        "groups": groups,
        "error_count": len(errors),
    }
    print(json.dumps(receipt, ensure_ascii=False, indent=2))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
