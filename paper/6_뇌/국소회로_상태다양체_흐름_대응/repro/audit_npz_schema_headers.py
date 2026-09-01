#!/usr/bin/env python3
"""Inventory NPZ array headers without interpreting array values."""

from __future__ import annotations

import argparse
import hashlib
import json
import zipfile
from collections import Counter
from pathlib import Path

import numpy as np


class NpzSchemaError(RuntimeError):
    pass


def _array_header(archive: zipfile.ZipFile, info: zipfile.ZipInfo) -> dict[str, object]:
    if not info.filename.endswith(".npy"):
        raise NpzSchemaError(f"non-NPY member in NPZ: {info.filename!r}")
    with archive.open(info, "r") as stream:
        version = np.lib.format.read_magic(stream)
        if version == (1, 0):
            shape, fortran_order, dtype = np.lib.format.read_array_header_1_0(stream)
        elif version == (2, 0):
            shape, fortran_order, dtype = np.lib.format.read_array_header_2_0(stream)
        elif version == (3, 0):
            from numpy.lib import _format_impl

            shape, fortran_order, dtype = _format_impl._read_array_header(stream, version)
        else:
            raise NpzSchemaError(f"unsupported NPY version {version}: {info.filename!r}")
    return {
        "key": info.filename[:-4],
        "shape": list(shape),
        "dtype": dtype.str,
        "fortran_order": bool(fortran_order),
        "member_uncompressed_bytes": info.file_size,
        "member_compressed_bytes": info.compress_size,
        "member_crc32": f"{info.CRC:08x}",
    }


def audit_tree(root: Path) -> dict[str, object]:
    resolved_root = root.resolve()
    paths = sorted(resolved_root.rglob("*.npz"), key=lambda path: path.as_posix())
    if not paths:
        raise NpzSchemaError(f"no NPZ files below {root}")
    files: list[dict[str, object]] = []
    schema_counts: Counter[str] = Counter()
    for path in paths:
        relative = path.relative_to(resolved_root).as_posix()
        payload_hash = hashlib.sha256(path.read_bytes()).hexdigest()
        with zipfile.ZipFile(path, "r") as archive:
            bad = archive.testzip()
            if bad is not None:
                raise NpzSchemaError(f"inner ZIP CRC failed for {relative}: {bad}")
            arrays = [_array_header(archive, info) for info in archive.infolist() if not info.is_dir()]
        arrays.sort(key=lambda item: str(item["key"]))
        schema_key = json.dumps(
            [(item["key"], item["shape"], item["dtype"], item["fortran_order"]) for item in arrays],
            separators=(",", ":"),
            sort_keys=False,
        )
        schema_hash = hashlib.sha256(schema_key.encode("utf-8")).hexdigest()
        schema_counts[schema_hash] += 1
        files.append(
            {
                "path": relative,
                "bytes": path.stat().st_size,
                "sha256": payload_hash,
                "schema_sha256": schema_hash,
                "arrays": arrays,
            }
        )
    canonical = "".join(
        f"{item['path']}|{item['bytes']}|{item['sha256']}|{item['schema_sha256']}\n" for item in files
    ).encode("utf-8")
    return {
        "status": "NPZ_SCHEMA_HEADER_AUDIT_PASS",
        "scope": "NPY names, shapes, dtypes and archive integrity; biological values not interpreted",
        "root": str(root),
        "file_count": len(files),
        "distinct_schema_count": len(schema_counts),
        "schema_counts": dict(sorted(schema_counts.items())),
        "canonical_files_sha256": hashlib.sha256(canonical).hexdigest(),
        "files": files,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    try:
        result = audit_tree(args.root)
    except (OSError, ValueError, zipfile.BadZipFile, NpzSchemaError) as exc:
        print(json.dumps({"status": "NPZ_SCHEMA_HEADER_AUDIT_FAIL", "error": str(exc)}, indent=2))
        return 1
    rendered = json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(rendered, encoding="utf-8", newline="\n")
    print(json.dumps({key: result[key] for key in ("status", "file_count", "distinct_schema_count", "canonical_files_sha256")}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
