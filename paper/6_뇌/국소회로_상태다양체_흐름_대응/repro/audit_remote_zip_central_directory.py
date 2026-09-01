#!/usr/bin/env python3
"""Inspect a remote ZIP central directory without downloading member payloads.

This is a source/schema preflight utility.  It deliberately reads only the ZIP
end records and central directory using HTTP byte ranges; it never opens an
archive member.  The emitted manifest is therefore not a biological endpoint
receipt.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import struct
import sys
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


EOCD_SIGNATURE = b"PK\x05\x06"
ZIP64_EOCD_SIGNATURE = b"PK\x06\x06"
ZIP64_LOCATOR_SIGNATURE = b"PK\x06\x07"
CENTRAL_ENTRY_SIGNATURE = b"PK\x01\x02"


class ZipAuditError(RuntimeError):
    """Raised when a remote object is not an auditable single-disk ZIP."""


@dataclass(frozen=True)
class DirectoryLocation:
    entry_count: int
    offset: int
    size: int
    zip64: bool


def _range_request(url: str, start: int, end: int) -> tuple[bytes, dict[str, str]]:
    if start < 0 or end < start:
        raise ValueError(f"invalid byte range {start}-{end}")
    request = urllib.request.Request(
        url,
        headers={
            "Range": f"bytes={start}-{end}",
            "User-Agent": "CE-NPF-remote-zip-schema-audit/1.0",
            "Accept-Encoding": "identity",
        },
    )
    with urllib.request.urlopen(request, timeout=120) as response:
        body = response.read()
        status = getattr(response, "status", None)
        headers = {key.lower(): value for key, value in response.headers.items()}
    expected = end - start + 1
    if status != 206:
        raise ZipAuditError(f"range request returned HTTP {status}, expected 206")
    if len(body) != expected:
        raise ZipAuditError(
            f"range {start}-{end} returned {len(body)} bytes, expected {expected}"
        )
    return body, headers


def _parse_total_size(content_range: str) -> int:
    try:
        unit_and_range, total = content_range.split("/", 1)
        unit, _ = unit_and_range.split(" ", 1)
        if unit.lower() != "bytes" or total == "*":
            raise ValueError
        return int(total)
    except (AttributeError, TypeError, ValueError) as exc:
        raise ZipAuditError(f"invalid Content-Range header: {content_range!r}") from exc


def _find_eocd(tail: bytes, tail_start: int) -> tuple[int, tuple[int, ...]]:
    index = tail.rfind(EOCD_SIGNATURE)
    if index < 0 or index + 22 > len(tail):
        raise ZipAuditError("ZIP end-of-central-directory record not found")
    fields = struct.unpack_from("<4s4H2LH", tail, index)
    comment_length = fields[-1]
    if index + 22 + comment_length != len(tail):
        raise ZipAuditError("EOCD comment length does not terminate at object end")
    return tail_start + index, fields[1:]


def _directory_location(
    url: str,
    total_size: int,
    tail: bytes,
    tail_start: int,
) -> DirectoryLocation:
    eocd_offset, fields = _find_eocd(tail, tail_start)
    disk_number, cd_disk, entries_disk, entries_total, cd_size, cd_offset, _ = fields
    if disk_number != 0 or cd_disk != 0 or entries_disk != entries_total:
        raise ZipAuditError("multi-disk ZIP archives are not supported")

    zip64 = (
        entries_total == 0xFFFF
        or cd_size == 0xFFFFFFFF
        or cd_offset == 0xFFFFFFFF
    )
    if not zip64:
        return DirectoryLocation(entries_total, cd_offset, cd_size, False)

    locator_offset = eocd_offset - 20
    if locator_offset < 0:
        raise ZipAuditError("invalid ZIP64 locator offset")
    local_index = locator_offset - tail_start
    if 0 <= local_index and local_index + 20 <= len(tail):
        locator = tail[local_index : local_index + 20]
    else:
        locator, _ = _range_request(url, locator_offset, locator_offset + 19)
    signature, zip64_disk, zip64_offset, disk_count = struct.unpack("<4sIQI", locator)
    if signature != ZIP64_LOCATOR_SIGNATURE:
        raise ZipAuditError("ZIP64 locator signature not found")
    # Some single-object repository ZIP writers emit zero in the locator's
    # "total number of disks" field.  The ZIP64 EOCD below still has to prove
    # that both the record and central directory reside on disk zero.  Accept
    # only that known single-disk encoding and the specification's value 1.
    if zip64_disk != 0 or disk_count not in (0, 1):
        raise ZipAuditError("multi-disk ZIP64 archives are not supported")

    record, _ = _range_request(url, zip64_offset, zip64_offset + 55)
    unpacked = struct.unpack("<4sQ2H2L4Q", record)
    if unpacked[0] != ZIP64_EOCD_SIGNATURE:
        raise ZipAuditError("ZIP64 EOCD signature not found")
    _, record_size, _, _, disk_number, cd_disk, entries_disk, entries_total, cd_size, cd_offset = unpacked
    if record_size < 44:
        raise ZipAuditError("invalid ZIP64 EOCD record size")
    if disk_number != 0 or cd_disk != 0 or entries_disk != entries_total:
        raise ZipAuditError("multi-disk ZIP64 central directory is not supported")
    if cd_offset + cd_size > total_size:
        raise ZipAuditError("central directory lies outside the remote object")
    return DirectoryLocation(entries_total, cd_offset, cd_size, True)


def _zip64_values(extra: bytes) -> list[int]:
    cursor = 0
    while cursor + 4 <= len(extra):
        header_id, data_size = struct.unpack_from("<HH", extra, cursor)
        cursor += 4
        end = cursor + data_size
        if end > len(extra):
            raise ZipAuditError("truncated ZIP extra field")
        if header_id == 0x0001:
            payload = extra[cursor:end]
            if len(payload) % 8 != 0:
                raise ZipAuditError("invalid ZIP64 extended-information length")
            return list(struct.unpack(f"<{len(payload) // 8}Q", payload))
        cursor = end
    return []


def parse_central_directory(data: bytes, expected_entries: int) -> list[dict[str, object]]:
    entries: list[dict[str, object]] = []
    cursor = 0
    while cursor < len(data):
        if cursor + 46 > len(data):
            raise ZipAuditError("truncated central-directory entry")
        fields = struct.unpack_from("<4s6H3L5H2L", data, cursor)
        if fields[0] != CENTRAL_ENTRY_SIGNATURE:
            raise ZipAuditError(f"unexpected central-directory signature at byte {cursor}")
        (
            _,
            _,
            _,
            flags,
            method,
            _,
            _,
            crc32,
            compressed_size,
            uncompressed_size,
            name_length,
            extra_length,
            comment_length,
            disk_start,
            _,
            _,
            local_header_offset,
        ) = fields
        record_end = cursor + 46 + name_length + extra_length + comment_length
        if record_end > len(data):
            raise ZipAuditError("central-directory variable fields are truncated")
        name_bytes = data[cursor + 46 : cursor + 46 + name_length]
        extra_start = cursor + 46 + name_length
        extra = data[extra_start : extra_start + extra_length]
        encoding = "utf-8" if flags & 0x0800 else "cp437"
        try:
            name = name_bytes.decode(encoding)
        except UnicodeDecodeError as exc:
            raise ZipAuditError(f"cannot decode member name at byte {cursor}") from exc

        zip64 = iter(_zip64_values(extra))
        if uncompressed_size == 0xFFFFFFFF:
            uncompressed_size = next(zip64, None)
        if compressed_size == 0xFFFFFFFF:
            compressed_size = next(zip64, None)
        if local_header_offset == 0xFFFFFFFF:
            local_header_offset = next(zip64, None)
        if disk_start == 0xFFFF:
            disk_start = next(zip64, None)
        if None in (uncompressed_size, compressed_size, local_header_offset, disk_start):
            raise ZipAuditError(f"missing ZIP64 value for {name!r}")
        if disk_start != 0:
            raise ZipAuditError("member resides on a nonzero ZIP disk")

        entries.append(
            {
                "name": name,
                "compressed_size": compressed_size,
                "uncompressed_size": uncompressed_size,
                "compression_method": method,
                "crc32": f"{crc32:08x}",
                "local_header_offset": local_header_offset,
                "is_directory": name.endswith("/"),
            }
        )
        cursor = record_end
    if len(entries) != expected_entries:
        raise ZipAuditError(
            f"parsed {len(entries)} central entries, expected {expected_entries}"
        )
    return entries


def _canonical_entry_lines(entries: Iterable[dict[str, object]]) -> bytes:
    return "".join(
        f"{entry['name']}|{entry['compressed_size']}|{entry['uncompressed_size']}|"
        f"{entry['compression_method']}|{entry['crc32']}|{entry['local_header_offset']}\n"
        for entry in entries
    ).encode("utf-8")


def audit_remote_zip(url: str, expected_size: int | None, max_directory_bytes: int) -> dict[str, object]:
    probe, probe_headers = _range_request(url, 0, 0)
    total_size = _parse_total_size(probe_headers.get("content-range", ""))
    if probe != b"P":
        raise ZipAuditError("remote object does not begin with ZIP signature byte 'P'")
    if expected_size is not None and total_size != expected_size:
        raise ZipAuditError(f"remote size {total_size} != expected {expected_size}")

    tail_length = min(total_size, 1 << 20)
    tail_start = total_size - tail_length
    tail, tail_headers = _range_request(url, tail_start, total_size - 1)
    location = _directory_location(url, total_size, tail, tail_start)
    if location.size > max_directory_bytes:
        raise ZipAuditError(
            f"central directory is {location.size} bytes, above limit {max_directory_bytes}"
        )
    directory, directory_headers = _range_request(
        url, location.offset, location.offset + location.size - 1
    )
    entries = parse_central_directory(directory, location.entry_count)
    canonical = _canonical_entry_lines(entries)
    return {
        "status": "REMOTE_ZIP_CENTRAL_DIRECTORY_AUDIT_PASS",
        "scope": "ZIP metadata only; no member payload was requested",
        "url": url,
        "remote_size": total_size,
        "etag": directory_headers.get("etag") or tail_headers.get("etag") or probe_headers.get("etag"),
        "last_modified": directory_headers.get("last-modified") or tail_headers.get("last-modified") or probe_headers.get("last-modified"),
        "zip64": location.zip64,
        "central_directory_offset": location.offset,
        "central_directory_size": location.size,
        "entry_count": len(entries),
        "canonical_entries_sha256": hashlib.sha256(canonical).hexdigest(),
        "entries": entries,
    }


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", required=True)
    parser.add_argument("--expected-size", type=int)
    parser.add_argument("--max-central-directory-bytes", type=int, default=512 * 1024 * 1024)
    parser.add_argument("--output", type=Path)
    return parser


def main() -> int:
    args = _build_parser().parse_args()
    try:
        result = audit_remote_zip(args.url, args.expected_size, args.max_central_directory_bytes)
    except (OSError, ZipAuditError, ValueError) as exc:
        print(json.dumps({"status": "REMOTE_ZIP_CENTRAL_DIRECTORY_AUDIT_FAIL", "error": str(exc)}, ensure_ascii=False, indent=2))
        return 1
    rendered = json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.output is not None:
        args.output.write_text(rendered, encoding="utf-8", newline="\n")
    else:
        sys.stdout.write(rendered)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
