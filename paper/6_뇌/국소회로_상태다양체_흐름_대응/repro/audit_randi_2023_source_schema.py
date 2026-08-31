from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


EXPECTED = {
    "wt": {
        "recordings": 113,
        "archive_bytes": 523_093_816,
        "archive_sha256": "d6e7b3d93175b40b7ae17bde2182835e9c2144388142c522ee9be3832f6ce836",
    },
    "unc31": {
        "recordings": 18,
        "archive_bytes": 84_924_311,
        "archive_sha256": "8b99f6610dbb2d6ab0b8dd6ad15646fe1c120da25dd9bb725f36f530b2af321a",
    },
}

SUFFIXES = (
    "ds_name",
    "gcamp",
    "labels",
    "stim_neurons",
    "stim_volume_i",
    "t",
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def lines(path: Path) -> list[str]:
    with path.open("r", encoding="utf-8") as handle:
        return handle.read().splitlines()


def scan_gcamp(path: Path) -> tuple[int, int]:
    row_count = 0
    column_count: int | None = None
    with path.open("rb") as handle:
        for raw_line in handle:
            columns = raw_line.split()
            if not columns:
                raise ValueError(f"blank GCaMP row: {path}:{row_count + 1}")
            if column_count is None:
                column_count = len(columns)
            elif len(columns) != column_count:
                raise ValueError(
                    f"ragged GCaMP matrix: {path}:{row_count + 1}; "
                    f"expected={column_count}, actual={len(columns)}"
                )
            row_count += 1
    if row_count == 0 or column_count is None:
        raise ValueError(f"empty GCaMP matrix: {path}")
    return row_count, column_count


def audit_group(name: str, root: Path, archive: Path) -> dict[str, object]:
    expected = EXPECTED[name]
    errors: list[str] = []
    archive_size = archive.stat().st_size
    archive_digest = sha256(archive)
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

    observed_files = [path for path in root.iterdir() if path.is_file()]
    expected_file_count = int(expected["recordings"]) * len(SUFFIXES)
    if len(observed_files) != expected_file_count:
        errors.append(
            f"file count: expected={expected_file_count}, actual={len(observed_files)}"
        )

    summaries: list[dict[str, object]] = []
    ds_names: list[str] = []
    for record_id in observed_ids:
        paths = {
            suffix: root / f"{record_id}_{suffix}.txt" for suffix in SUFFIXES
        }
        missing = [str(path) for path in paths.values() if not path.is_file()]
        if missing:
            errors.append(f"recording {record_id} missing files: {missing}")
            continue

        ds_name_lines = lines(paths["ds_name"])
        labels = lines(paths["labels"])
        timestamps = lines(paths["t"])
        stim_neurons_text = lines(paths["stim_neurons"])
        stim_volume_text = lines(paths["stim_volume_i"])
        if len(ds_name_lines) != 1 or not ds_name_lines[0].strip():
            errors.append(f"recording {record_id} invalid ds_name")
        else:
            ds_names.append(ds_name_lines[0].strip())

        try:
            gcamp_rows, gcamp_columns = scan_gcamp(paths["gcamp"])
        except ValueError as exc:
            errors.append(str(exc))
            continue

        if len(timestamps) != gcamp_rows:
            errors.append(
                f"recording {record_id} time rows={len(timestamps)} "
                f"but GCaMP rows={gcamp_rows}"
            )
        if len(labels) != gcamp_columns:
            errors.append(
                f"recording {record_id} labels={len(labels)} "
                f"but GCaMP columns={gcamp_columns}"
            )
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
        if any(value < -1 or value >= gcamp_columns for value in stim_neurons):
            errors.append(f"recording {record_id} out-of-range stimulated neuron")
        if any(value < 0 or value >= gcamp_rows for value in stim_volumes):
            errors.append(f"recording {record_id} out-of-range stimulus volume")

        summaries.append(
            {
                "recording_id": record_id,
                "timepoints": gcamp_rows,
                "neurons": gcamp_columns,
                "identified_labels": sum(bool(label.strip()) for label in labels),
                "stimuli": len(stim_volumes),
            }
        )

    if len(ds_names) != len(set(ds_names)):
        errors.append("duplicate ds_name values")

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
            "RANDI_2023_SOURCE_SCHEMA_PASS"
            if not errors
            else "RANDI_2023_SOURCE_SCHEMA_FAIL"
        ),
        "scope": "source_and_schema_only_no_biological_endpoint",
        "groups": groups,
        "error_count": len(errors),
    }
    print(json.dumps(receipt, ensure_ascii=False, indent=2))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
