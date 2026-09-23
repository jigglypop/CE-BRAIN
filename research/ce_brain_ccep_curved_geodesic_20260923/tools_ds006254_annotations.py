"""Endpoint-blind annotation harvest for OpenNeuro ds006254 (EDF+ stimulation markers).

For each EDF recording it reads only the leading data records (NATUS writes the
annotation TALs ahead of time), grows the block until two consecutive blocks add
no new annotation, and records every non-timekeeping annotation plus the S3
identity (ETag, VersionId, Content-Length).  No neural sample is decoded.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import requests

UA = {"User-Agent": "CE-ccep-curved-geodesic-annotations/1"}
HERE = Path(__file__).resolve().parent
TREE_SHA = "6170b5c333fb5dab60b01ce81f3e451d80f3a150"
BLOCK_RECORDS = 400
PARALLEL = 8


def get_range(url: str, start: int, end: int, etag: str | None = None) -> bytes:
    headers = {**UA, "Range": f"bytes={start}-{end}"}
    if etag:
        headers["If-Match"] = etag
    for attempt in range(5):
        try:
            resp = requests.get(url, headers=headers, timeout=300)
            if resp.status_code == 206:
                return resp.content
            if resp.status_code < 500:
                raise RuntimeError(f"HTTP {resp.status_code}")
        except requests.RequestException:
            pass
        time.sleep(2.0 * (attempt + 1))
    raise RuntimeError(f"range failed {start}-{end}")


def parallel_range(url: str, start: int, end: int, etag: str, parts: int = PARALLEL) -> bytes:
    size = end - start + 1
    step = -(-size // parts)
    bounds = [(start + i * step, min(end, start + (i + 1) * step - 1)) for i in range(parts) if start + i * step <= end]
    with ThreadPoolExecutor(max_workers=len(bounds)) as pool:
        chunks = list(pool.map(lambda b: get_range(url, b[0], b[1], etag), bounds))
    return b"".join(chunks)


def header(url: str) -> dict:
    head = requests.head(url, headers=UA, timeout=60)
    head.raise_for_status()
    fixed = get_range(url, 0, 255)
    ns = int(fixed[252:256].decode("ascii").strip())
    hbytes = int(fixed[184:192].decode("ascii").strip())
    body = get_range(url, 0, hbytes - 1)[256:]

    def field(offset: int, width: int) -> list[str]:
        return [body[offset * ns + i * width: offset * ns + (i + 1) * width].decode("latin-1").strip()
                for i in range(ns)]

    labels = field(0, 16)
    spr_offset = 16 + 80 + 8 * 5 + 80
    return {
        "content_length": int(head.headers["content-length"]),
        "etag": head.headers.get("etag"),
        "version_id": head.headers.get("x-amz-version-id"),
        "reserved": fixed[192:236].decode("latin-1").strip(),
        "start": fixed[168:184].decode("latin-1"),
        "header_bytes": hbytes,
        "n_records": int(fixed[236:244].decode("ascii").strip()),
        "record_duration_s": float(fixed[244:252].decode("ascii").strip()),
        "ns": ns,
        "labels": labels,
        "dimension": field(16 + 80, 8),
        "phys_min": field(16 + 80 + 8, 8),
        "phys_max": field(16 + 80 + 16, 8),
        "dig_min": field(16 + 80 + 24, 8),
        "dig_max": field(16 + 80 + 32, 8),
        "samples_per_record": [int(v) for v in field(spr_offset, 8)],
    }


def tals(payload: bytes, hdr: dict, n_records: int) -> list[dict]:
    spr = hdr["samples_per_record"]
    idx = hdr["labels"].index("EDF Annotations")
    rec_bytes = 2 * sum(spr)
    off = 2 * sum(spr[:idx])
    width = 2 * spr[idx]
    out = []
    for rec in range(n_records):
        chunk = payload[rec * rec_bytes + off: rec * rec_bytes + off + width]
        for tal in chunk.split(b"\x00"):
            parts = tal.decode("latin-1").split("\x14")
            texts = [p for p in parts[1:] if p.strip()]
            if texts:
                onset = parts[0].split("\x15")[0]
                for text in texts:
                    out.append({"onset_s": float(onset), "text": text.strip(), "record": rec})
    return out


def harvest(path: str, url: str) -> dict:
    hdr = header(url)
    rec_bytes = 2 * sum(hdr["samples_per_record"])
    found: list[dict] = []
    seen = set()
    first = 0
    quiet = 0
    t0 = time.time()
    while first < hdr["n_records"] and quiet < 2:
        n = min(BLOCK_RECORDS, hdr["n_records"] - first)
        start = hdr["header_bytes"] + first * rec_bytes
        payload = parallel_range(url, start, start + n * rec_bytes - 1, hdr["etag"])
        new = 0
        for row in tals(payload, hdr, n):
            key = (row["onset_s"], row["text"])
            if key not in seen:
                seen.add(key)
                row["record"] += first
                found.append(row)
                new += 1
        quiet = quiet + 1 if new == 0 else 0
        first += n
    return {
        "path": path,
        "url": url,
        "s3": {k: hdr[k] for k in ("content_length", "etag", "version_id")},
        "edf": {k: hdr[k] for k in ("reserved", "start", "header_bytes", "n_records", "record_duration_s", "ns")},
        "labels": hdr["labels"],
        "dimension": hdr["dimension"],
        "phys_min": hdr["phys_min"], "phys_max": hdr["phys_max"],
        "dig_min": hdr["dig_min"], "dig_max": hdr["dig_max"],
        "samples_per_record": hdr["samples_per_record"],
        "records_scanned": first,
        "annotations": found,
        "scan_seconds": round(time.time() - t0, 1),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--only", default=None)
    parser.add_argument("--out", default=str(HERE / "ds006254_annotation_harvest.json"))
    args = parser.parse_args()
    probe = json.loads((HERE / "probe_ds006254_1.0.0.json").read_text(encoding="utf-8"))
    if probe["tree_sha"] != TREE_SHA:
        raise RuntimeError("tree SHA mismatch")
    listing = json.loads((HERE / "files_ds006254_1.0.0.json").read_text(encoding="utf-8"))
    locked = {r["path"]: r["urls"][0] for r in listing if r["path"].endswith("_ieeg.edf")}
    edfs = sorted(p for p in probe["paths"] if p.endswith("_ieeg.edf"))
    if set(edfs) != set(locked):
        raise RuntimeError("GitHub tree and snapshot listing disagree on EDF paths")
    if args.only:
        edfs = [p for p in edfs if args.only in p]
    out_path = Path(args.out)
    done = json.loads(out_path.read_text(encoding="utf-8")) if out_path.exists() else {}
    for path in edfs:
        if path in done:
            continue
        try:
            row = harvest(path, locked[path])
        except (requests.RequestException, RuntimeError, ValueError) as error:
            done[path] = {"path": path, "url": locked[path], "error": str(error)[:300]}
            out_path.write_text(json.dumps(done, indent=0), encoding="utf-8")
            print(json.dumps({"path": path, "error": str(error)[:200]}), flush=True)
            continue
        done[path] = row
        out_path.write_text(json.dumps(done, indent=0), encoding="utf-8")
        stims = [a for a in row["annotations"] if a["text"].lower().startswith("start stimulation")]
        print(json.dumps({"path": path, "records_scanned": row["records_scanned"],
                          "annotations": len(row["annotations"]), "stim_starts": len(stims),
                          "max_onset": max((a["onset_s"] for a in row["annotations"]), default=None),
                          "duration_s": row["edf"]["n_records"] * row["edf"]["record_duration_s"],
                          "secs": row["scan_seconds"]}), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
