#!/usr/bin/env python3
"""Fetch selected members from a range-addressable remote ZIP.

The input must be a manifest produced by
``audit_remote_zip_central_directory.py``.  Adjacent selected local records are
coalesced into a small number of HTTP range requests.  Each decoded member is
checked against its central-directory size and CRC before it is written.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import struct
import sys
import zlib
from pathlib import Path, PurePosixPath

from audit_remote_zip_central_directory import ZipAuditError, _range_request


LOCAL_ENTRY_SIGNATURE = b"PK\x03\x04"


def _safe_destination(root: Path, member_name: str) -> Path:
    pure = PurePosixPath(member_name)
    if pure.is_absolute() or not pure.parts or any(part in ("", ".", "..") for part in pure.parts):
        raise ZipAuditError(f"unsafe member path: {member_name!r}")
    destination = root.joinpath(*pure.parts)
    resolved_root = root.resolve()
    resolved_destination = destination.resolve()
    try:
        resolved_destination.relative_to(resolved_root)
    except ValueError as exc:
        raise ZipAuditError(f"member path escapes output root: {member_name!r}") from exc
    return destination


def _decode_member(span: bytes, span_start: int, entry: dict[str, object]) -> bytes:
    local_offset = int(entry["local_header_offset"])
    cursor = local_offset - span_start
    if cursor < 0 or cursor + 30 > len(span):
        raise ZipAuditError(f"local header outside fetched span: {entry['name']!r}")
    fields = struct.unpack_from("<4s5H3L2H", span, cursor)
    if fields[0] != LOCAL_ENTRY_SIGNATURE:
        raise ZipAuditError(f"local header signature mismatch: {entry['name']!r}")
    _, _, flags, method, _, _, _, _, _, name_length, extra_length = fields
    if flags & 0x0001:
        raise ZipAuditError(f"encrypted member is unsupported: {entry['name']!r}")
    if method != int(entry["compression_method"]):
        raise ZipAuditError(f"local/central compression mismatch: {entry['name']!r}")
    name_start = cursor + 30
    name_end = name_start + name_length
    data_start = name_end + extra_length
    compressed_size = int(entry["compressed_size"])
    data_end = data_start + compressed_size
    if data_end > len(span):
        raise ZipAuditError(f"compressed payload outside fetched span: {entry['name']!r}")
    encoding = "utf-8" if flags & 0x0800 else "cp437"
    local_name = span[name_start:name_end].decode(encoding)
    if local_name != entry["name"]:
        raise ZipAuditError(f"local/central member name mismatch: {entry['name']!r}")
    compressed = span[data_start:data_end]
    if method == 0:
        decoded = compressed
    elif method == 8:
        decoded = zlib.decompress(compressed, -zlib.MAX_WBITS)
    else:
        raise ZipAuditError(f"unsupported ZIP compression method {method}: {entry['name']!r}")
    if len(decoded) != int(entry["uncompressed_size"]):
        raise ZipAuditError(f"uncompressed size mismatch: {entry['name']!r}")
    expected_crc = int(str(entry["crc32"]), 16)
    if zlib.crc32(decoded) & 0xFFFFFFFF != expected_crc:
        raise ZipAuditError(f"CRC mismatch: {entry['name']!r}")
    return decoded


def _record_boundaries(entries: list[dict[str, object]], central_offset: int) -> dict[str, int]:
    files = sorted(
        (entry for entry in entries if not bool(entry["is_directory"])),
        key=lambda entry: int(entry["local_header_offset"]),
    )
    boundaries: dict[str, int] = {}
    for index, entry in enumerate(files):
        next_offset = central_offset if index + 1 == len(files) else int(files[index + 1]["local_header_offset"])
        if next_offset <= int(entry["local_header_offset"]):
            raise ZipAuditError("local-header offsets are not strictly increasing")
        boundaries[str(entry["name"])] = next_offset
    return boundaries


def _coalesced_groups(
    selected: list[dict[str, object]], boundaries: dict[str, int], max_span_bytes: int
) -> list[list[dict[str, object]]]:
    ordered = sorted(selected, key=lambda entry: int(entry["local_header_offset"]))
    groups: list[list[dict[str, object]]] = []
    for entry in ordered:
        if not groups:
            groups.append([entry])
            continue
        group = groups[-1]
        current_end = boundaries[str(group[-1]["name"])]
        entry_start = int(entry["local_header_offset"])
        proposed_end = boundaries[str(entry["name"])]
        group_start = int(group[0]["local_header_offset"])
        if entry_start == current_end and proposed_end - group_start <= max_span_bytes:
            group.append(entry)
        else:
            groups.append([entry])
    return groups


def extract_selected(
    source_manifest: Path,
    output_root: Path,
    prefixes: tuple[str, ...],
    max_member_bytes: int,
    max_total_bytes: int,
    max_span_bytes: int,
) -> dict[str, object]:
    source_bytes = source_manifest.read_bytes()
    manifest = json.loads(source_bytes)
    if manifest.get("status") != "REMOTE_ZIP_CENTRAL_DIRECTORY_AUDIT_PASS":
        raise ZipAuditError("source manifest did not pass the central-directory audit")
    entries = list(manifest["entries"])
    selected = [
        entry
        for entry in entries
        if not bool(entry["is_directory"])
        and any(str(entry["name"]).startswith(prefix) for prefix in prefixes)
    ]
    if not selected:
        raise ZipAuditError("no members matched the requested prefix")
    too_large = [entry["name"] for entry in selected if int(entry["uncompressed_size"]) > max_member_bytes]
    if too_large:
        raise ZipAuditError(f"selected member exceeds max-member-bytes: {too_large[0]!r}")
    total_uncompressed = sum(int(entry["uncompressed_size"]) for entry in selected)
    if total_uncompressed > max_total_bytes:
        raise ZipAuditError(
            f"selected uncompressed total {total_uncompressed} exceeds limit {max_total_bytes}"
        )

    output_root.mkdir(parents=True, exist_ok=True)
    boundaries = _record_boundaries(entries, int(manifest["central_directory_offset"]))
    groups = _coalesced_groups(selected, boundaries, max_span_bytes)
    receipts: list[dict[str, object]] = []
    for group in groups:
        start = int(group[0]["local_header_offset"])
        end_exclusive = boundaries[str(group[-1]["name"])]
        span, _ = _range_request(str(manifest["url"]), start, end_exclusive - 1)
        for entry in group:
            decoded = _decode_member(span, start, entry)
            destination = _safe_destination(output_root, str(entry["name"]))
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(decoded)
            receipts.append(
                {
                    "name": entry["name"],
                    "bytes": len(decoded),
                    "crc32": entry["crc32"],
                    "sha256": hashlib.sha256(decoded).hexdigest(),
                }
            )
    canonical = "".join(
        f"{item['name']}|{item['bytes']}|{item['crc32']}|{item['sha256']}\n" for item in receipts
    ).encode("utf-8")
    return {
        "status": "REMOTE_ZIP_SELECTED_MEMBERS_PASS",
        "scope": "selected member bytes only; no biological endpoint evaluated",
        "source_manifest": str(source_manifest),
        "source_manifest_sha256": hashlib.sha256(source_bytes).hexdigest(),
        "source_url": manifest["url"],
        "prefixes": list(prefixes),
        "range_request_count": len(groups),
        "member_count": len(receipts),
        "total_uncompressed_bytes": total_uncompressed,
        "canonical_members_sha256": hashlib.sha256(canonical).hexdigest(),
        "members": receipts,
    }


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-manifest", required=True, type=Path)
    parser.add_argument("--output-root", required=True, type=Path)
    parser.add_argument("--prefix", required=True, action="append")
    parser.add_argument("--receipt", required=True, type=Path)
    parser.add_argument("--max-member-bytes", type=int, default=64 * 1024 * 1024)
    parser.add_argument("--max-total-bytes", type=int, default=1024 * 1024 * 1024)
    parser.add_argument("--max-span-bytes", type=int, default=128 * 1024 * 1024)
    return parser


def main() -> int:
    args = _build_parser().parse_args()
    try:
        result = extract_selected(
            args.source_manifest,
            args.output_root,
            tuple(args.prefix),
            args.max_member_bytes,
            args.max_total_bytes,
            args.max_span_bytes,
        )
    except (OSError, ValueError, KeyError, ZipAuditError, json.JSONDecodeError) as exc:
        print(json.dumps({"status": "REMOTE_ZIP_SELECTED_MEMBERS_FAIL", "error": str(exc)}, indent=2))
        return 1
    rendered = json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    args.receipt.parent.mkdir(parents=True, exist_ok=True)
    args.receipt.write_text(rendered, encoding="utf-8", newline="\n")
    print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
