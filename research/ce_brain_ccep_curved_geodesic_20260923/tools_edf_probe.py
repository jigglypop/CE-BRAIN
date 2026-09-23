"""Probe an OpenNeuro EDF header through an HTTP range request (header bytes only).

Reports record geometry and whether an EDF+ annotation signal exists. With
--annotations it streams only the annotation-signal bytes of the first N data
records (stimulation markers are metadata, not the scientific endpoint).
"""
from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.parse

import requests

S3 = "https://s3.amazonaws.com/openneuro.org"
UA = {"User-Agent": "CE-ccep-curved-geodesic-probe/1"}


def get_range(url: str, start: int, end: int) -> bytes:
    resp = requests.get(url, headers={**UA, "Range": f"bytes={start}-{end}"}, timeout=120)
    if resp.status_code != 206:
        raise RuntimeError(f"HTTP {resp.status_code} for range {start}-{end}")
    return resp.content


def parse_header(url: str) -> dict:
    fixed = get_range(url, 0, 255)
    ns = int(fixed[252:256].decode("ascii").strip())
    header_bytes = int(fixed[184:192].decode("ascii").strip())
    full = get_range(url, 0, header_bytes - 1)
    body = full[256:]

    def field(offset: int, width: int) -> list[str]:
        base = offset * ns
        return [body[base + i * width: base + (i + 1) * width].decode("latin-1").strip() for i in range(ns)]

    labels = field(0, 16)
    cursor = 16
    transducer = field(cursor, 80); cursor += 80
    dimension = field(cursor, 8); cursor += 8
    phys_min = field(cursor, 8); cursor += 8
    phys_max = field(cursor, 8); cursor += 8
    dig_min = field(cursor, 8); cursor += 8
    dig_max = field(cursor, 8); cursor += 8
    prefilter = field(cursor, 80); cursor += 80
    samples = [int(v) for v in field(cursor, 8)]
    head = requests.head(url, headers=UA, timeout=60)
    return {
        "version": fixed[0:8].decode("latin-1"),
        "patient": fixed[8:88].decode("latin-1").strip(),
        "recording": fixed[88:168].decode("latin-1").strip(),
        "start": fixed[168:184].decode("latin-1"),
        "header_bytes": header_bytes,
        "reserved": fixed[192:236].decode("latin-1").strip(),
        "n_records": int(fixed[236:244].decode("ascii").strip()),
        "record_duration_s": float(fixed[244:252].decode("ascii").strip()),
        "ns": ns,
        "labels": labels,
        "dimension": dimension,
        "phys_min": phys_min, "phys_max": phys_max, "dig_min": dig_min, "dig_max": dig_max,
        "prefilter": prefilter[:3],
        "samples_per_record": samples,
        "content_length": int(head.headers.get("content-length", -1)),
        "etag": head.headers.get("etag"),
        "version_id": head.headers.get("x-amz-version-id"),
    }


def annotation_texts(url: str, hdr: dict, n_records: int) -> list[str]:
    labels = hdr["labels"]
    if "EDF Annotations" not in labels:
        return []
    idx = labels.index("EDF Annotations")
    spr = hdr["samples_per_record"]
    record_bytes = 2 * sum(spr)
    offset_in_record = 2 * sum(spr[:idx])
    width = 2 * spr[idx]
    out = []
    for rec in range(n_records):
        start = hdr["header_bytes"] + rec * record_bytes + offset_in_record
        chunk = get_range(url, start, start + width - 1)
        for tal in chunk.split(b"\x00"):
            text = tal.decode("latin-1").strip("\x14 ")
            if text:
                out.append(text.replace("\x14", " | ").replace("\x15", " dur="))
    return out


def block_annotations(url: str, hdr: dict, first_record: int, n_records: int) -> list[str]:
    """One contiguous range over n_records; returns annotation TAL texts only."""
    labels = hdr["labels"]
    idx = labels.index("EDF Annotations")
    spr = hdr["samples_per_record"]
    record_bytes = 2 * sum(spr)
    offset_in_record = 2 * sum(spr[:idx])
    width = 2 * spr[idx]
    start = hdr["header_bytes"] + first_record * record_bytes
    t0 = time.time()
    payload = get_range(url, start, start + n_records * record_bytes - 1)
    elapsed = time.time() - t0
    print(f"# block {len(payload) / 1e6:.1f} MB in {elapsed:.1f}s = {len(payload) / 1e6 / elapsed:.1f} MB/s")
    out = []
    for rec in range(n_records):
        chunk = payload[rec * record_bytes + offset_in_record: rec * record_bytes + offset_in_record + width]
        for tal in chunk.split(b"\x00"):
            parts = tal.decode("latin-1").split("\x14")
            if len(parts) >= 2 and any(p.strip() for p in parts[1:]):
                out.append(" | ".join(p.replace("\x15", " dur=") for p in parts if p))
    return out


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("dataset")
    parser.add_argument("path")
    parser.add_argument("--annotations", type=int, default=0)
    parser.add_argument("--block", type=int, nargs=2, default=None, metavar=("FIRST", "N"))
    args = parser.parse_args()
    url = f"{S3}/{args.dataset}/{urllib.parse.quote(args.path)}"
    hdr = parse_header(url)
    brief = {k: v for k, v in hdr.items() if k not in ("labels", "dimension", "phys_min", "phys_max",
                                                        "dig_min", "dig_max", "samples_per_record")}
    brief["labels_head"] = hdr["labels"][:12]
    brief["labels_tail"] = hdr["labels"][-6:]
    brief["unique_spr"] = sorted(set(hdr["samples_per_record"]))
    brief["dimension_set"] = sorted(set(hdr["dimension"]))
    brief["has_annotations"] = "EDF Annotations" in hdr["labels"]
    sys.stdout.reconfigure(encoding="utf-8")
    print(json.dumps(brief, indent=1, ensure_ascii=False))
    if args.annotations:
        for text in annotation_texts(url, hdr, args.annotations):
            print(text)
    if args.block:
        texts = block_annotations(url, hdr, args.block[0], args.block[1])
        print(f"# non-timekeeping annotations: {len(texts)}")
        for text in texts[:200]:
            print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
