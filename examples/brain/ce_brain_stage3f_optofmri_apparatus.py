"""Outcome-blind remote apparatus audit for the CNIR opto-fMRI EGG archive.

Only archive headers and filenames are read.  Image payloads are skipped by
HTTP byte range, so this gate cannot inspect any fMRI outcome values.
"""

from __future__ import annotations

import argparse
from collections import Counter
import json
import re
import struct
import time
from dataclasses import dataclass
from pathlib import Path
from typing import BinaryIO

import requests


EGG_MAGIC = 0x41474745
END_MAGIC = 0x08E28222
FILE_HEADER_MAGIC = 0x0A8590E3
FILENAME_HEADER_MAGIC = 0x0A8591AC
BLOCK_HEADER_MAGIC = 0x02B50C13
WIN_FILE_INFO_MAGIC = 0x2C86950B
POSIX_FILE_INFO_MAGIC = 0x1EE922E5
ENCRYPT_HEADER_MAGIC = 0x08D1470F
COMMENT_HEADER_MAGIC = 0x04C63672
DUMMY_HEADER_MAGIC = 0x07463307
SPLIT_HEADER_MAGIC = 0x24F5A262
SOLID_HEADER_MAGIC = 0x24E5A060

EXPECTED_GENOTYPES = ("Thy1", "VGAT")
EXPECTED_SUBJECTS_PER_GENOTYPE = 12
EXPECTED_SITES = ("MOp", "MOs", "SSp-bfd", "VISp", "RSP", "VISarl")


class HttpRangeReader:
    """Small seekable reader backed by cached HTTP range requests."""

    def __init__(self, url: str, size: int, page_size: int = 1 << 16):
        self.url = url
        self.size = size
        self.page_size = page_size
        self.pos = 0
        self._page_start = -1
        self._page = b""
        self._session = requests.Session()

    def tell(self) -> int:
        return self.pos

    def seek(self, offset: int, whence: int = 0) -> int:
        if whence == 0:
            new_pos = offset
        elif whence == 1:
            new_pos = self.pos + offset
        elif whence == 2:
            new_pos = self.size + offset
        else:
            raise ValueError(f"unsupported whence: {whence}")
        if not 0 <= new_pos <= self.size:
            raise ValueError(f"seek outside archive: {new_pos}")
        self.pos = new_pos
        return self.pos

    def read(self, count: int = -1) -> bytes:
        if count < 0:
            count = self.size - self.pos
        chunks: list[bytes] = []
        remaining = min(count, self.size - self.pos)
        while remaining:
            page_start = (self.pos // self.page_size) * self.page_size
            if page_start != self._page_start:
                page_end = min(self.size - 1, page_start + self.page_size - 1)
                page = bytearray()
                attempts = 0
                while len(page) < page_end - page_start + 1:
                    request_start = page_start + len(page)
                    try:
                        response = self._session.get(
                            self.url,
                            headers={"Range": f"bytes={request_start}-{page_end}"},
                            timeout=(10, 30),
                        )
                        response.raise_for_status()
                        if response.status_code != 206:
                            raise RuntimeError(
                                f"range request returned HTTP {response.status_code}"
                            )
                        page += response.content
                        attempts = 0
                    except requests.RequestException as error:
                        attempts += 1
                        if attempts >= 5:
                            raise
                        retry_after = 0.0
                        if error.response is not None:
                            try:
                                retry_after = float(error.response.headers.get("Retry-After", 0))
                            except ValueError:
                                retry_after = 0.0
                        time.sleep(max(retry_after, float(attempts)))
                self._page = bytes(page)
                self._page_start = page_start
            local = self.pos - page_start
            take = min(remaining, len(self._page) - local)
            if take <= 0:
                raise EOFError("range server returned an incomplete page")
            chunks.append(self._page[local : local + take])
            self.pos += take
            remaining -= take
        return b"".join(chunks)


@dataclass(frozen=True)
class EggEntry:
    filename: str
    file_length: int
    method: int
    compressed_size: int
    data_offset: int
    encrypted: bool


def _read_exact(stream: BinaryIO | HttpRangeReader, count: int) -> bytes:
    data = stream.read(count)
    if len(data) != count:
        raise EOFError(f"wanted {count} bytes, received {len(data)}")
    return data


def _u32(stream: BinaryIO | HttpRangeReader) -> int:
    return struct.unpack("<I", _read_exact(stream, 4))[0]


def _extra_size(stream: BinaryIO | HttpRangeReader) -> tuple[int, int]:
    flags = _read_exact(stream, 1)[0]
    width = 4 if flags & 1 else 2
    size = int.from_bytes(_read_exact(stream, width), "little")
    return flags, size


def scan_egg(stream: BinaryIO | HttpRangeReader, archive_size: int) -> list[EggEntry]:
    """Read only EGG metadata and skip every compressed data block."""
    if _u32(stream) != EGG_MAGIC:
        raise ValueError("not an EGG archive")
    _read_exact(stream, 10)
    while True:
        magic = _u32(stream)
        if magic == END_MAGIC:
            break
        if magic not in {SPLIT_HEADER_MAGIC, SOLID_HEADER_MAGIC}:
            raise ValueError(f"unexpected prefix 0x{magic:08x}")
        _, size = _extra_size(stream)
        stream.seek(size, 1)

    entries: list[EggEntry] = []
    while stream.tell() < archive_size:
        magic = _u32(stream)
        if magic == END_MAGIC:
            break
        if magic != FILE_HEADER_MAGIC:
            raise ValueError(f"unexpected entry 0x{magic:08x} at {stream.tell()-4}")
        _read_exact(stream, 4)  # file id
        file_length = struct.unpack("<q", _read_exact(stream, 8))[0]
        filename = ""
        encrypted = False
        while True:
            sub = _u32(stream)
            if sub == END_MAGIC:
                break
            if sub == FILENAME_HEADER_MAGIC:
                flags, size = _extra_size(stream)
                locale = 65001
                if flags & 0x08:
                    locale = int.from_bytes(_read_exact(stream, 2), "little")
                raw = _read_exact(stream, size)
                encoding = {949: "euc-kr", 1200: "utf-16-le"}.get(locale, "utf-8")
                filename = raw.decode(encoding, errors="replace").replace("\\", "/")
            elif sub in {
                WIN_FILE_INFO_MAGIC,
                POSIX_FILE_INFO_MAGIC,
                ENCRYPT_HEADER_MAGIC,
                COMMENT_HEADER_MAGIC,
                DUMMY_HEADER_MAGIC,
            }:
                _, size = _extra_size(stream)
                encrypted |= sub == ENCRYPT_HEADER_MAGIC
                stream.seek(size, 1)
            else:
                raise ValueError(f"unexpected sub-header 0x{sub:08x}")

        method = compressed_size = data_offset = 0
        if file_length > 0:
            if _u32(stream) != BLOCK_HEADER_MAGIC:
                raise ValueError(f"missing block for {filename}")
            block = _read_exact(stream, 14)
            method = struct.unpack_from("<H", block, 0)[0] & 0xFF
            uncompressed_size = struct.unpack_from("<I", block, 2)[0]
            compressed_size = struct.unpack_from("<I", block, 6)[0]
            if _u32(stream) != END_MAGIC:
                raise ValueError(f"missing block terminator for {filename}")
            data_offset = stream.tell()
            if uncompressed_size != file_length:
                raise ValueError(f"size mismatch for {filename}")
            stream.seek(compressed_size, 1)
        entries.append(
            EggEntry(filename, file_length, method, compressed_size, data_offset, encrypted)
        )
    return entries


def audit_entries(entries: list[EggEntry]) -> dict[str, object]:
    subject_re = re.compile(r"^(Thy1|VGAT)-sub(\d{2})/")
    subjects: dict[str, set[str]] = {name: set() for name in EXPECTED_GENOTYPES}
    subject_files: dict[str, list[str]] = {}
    for entry in entries:
        match = subject_re.match(entry.filename)
        if not match:
            continue
        genotype, number = match.groups()
        subject = f"{genotype}-sub{number}"
        subjects[genotype].add(subject)
        subject_files.setdefault(subject, []).append(entry.filename)

    per_subject = {}
    for subject, filenames in sorted(subject_files.items()):
        funcs = sorted(name for name in filenames if "/func_" in name and name.endswith(".nii.gz"))
        site_counts = Counter(name.split("/")[1].removeprefix("func_") for name in funcs)
        per_subject[subject] = {
            "anatomical_nifti": sum("/anat/" in name and name.endswith(".nii.gz") for name in filenames),
            "functional_nifti": len(funcs),
            "stimulation_site_counts": dict(sorted(site_counts.items())),
        }

    complete_counts = all(
        len(subjects[name]) == EXPECTED_SUBJECTS_PER_GENOTYPE for name in EXPECTED_GENOTYPES
    )
    all_sites_each = bool(per_subject) and all(
        set(row["stimulation_site_counts"]) == set(EXPECTED_SITES)
        and min(row["stimulation_site_counts"].values()) >= 1
        for row in per_subject.values()
    )
    no_encryption = not any(entry.encrypted for entry in entries)
    supported_methods = sorted({entry.method for entry in entries if entry.file_length > 0})
    eligible = complete_counts and all_sites_each and no_encryption
    return {
        "status": (
            "STAGE3_OPTOFMRI_APPARATUS_ELIGIBLE"
            if eligible
            else "STAGE3_OPTOFMRI_APPARATUS_INCOMPLETE"
        ),
        "entry_count": len(entries),
        "genotype_subject_counts": {name: len(subjects[name]) for name in EXPECTED_GENOTYPES},
        "expected_stimulation_sites": list(EXPECTED_SITES),
        "all_six_stimulation_sites_each": all_sites_each,
        "encrypted_entries": sum(entry.encrypted for entry in entries),
        "compression_methods": supported_methods,
        "per_subject": per_subject,
        "claim_ceiling": "outcome-blind archive apparatus only",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--archive", type=Path)
    source.add_argument("--url")
    parser.add_argument("--size", type=int)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--manifest-output", type=Path)
    args = parser.parse_args()
    if args.archive:
        with args.archive.open("rb") as stream:
            entries = scan_egg(stream, args.archive.stat().st_size)
    else:
        if args.size is None:
            parser.error("--url requires --size")
        entries = scan_egg(HttpRangeReader(args.url, args.size), args.size)
    result = audit_entries(entries)
    if args.manifest_output:
        args.manifest_output.parent.mkdir(parents=True, exist_ok=True)
        manifest = [
            {
                "filename": entry.filename,
                "file_length": entry.file_length,
                "method": entry.method,
                "compressed_size": entry.compressed_size,
                "data_offset": entry.data_offset,
                "encrypted": entry.encrypted,
            }
            for entry in entries
        ]
        args.manifest_output.write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    payload = json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload + "\n", encoding="utf-8")
    print(payload)


if __name__ == "__main__":
    main()
