from __future__ import annotations

import argparse
import concurrent.futures
import json
import os
import time
import urllib.request
import zlib
from pathlib import Path


EXPECTED_MANIFEST_SHA256 = (
    "3cfb18334b413a0ceaa307cdf328750f3fe3f7b5e2b88b6d4b5e1b178375fc25"
)
EXPECTED_COUNT = 249
EXPECTED_BYTES = 4_294_515_444
SUFFIXES = (
    "/move_deve/interframe_int.npy",
    "/move_deve/tstamps.npy",
    "/move_deve/motion_energy_glob.npy",
    "/suite2p/plane0/spks.npy",
    "/suite2p/plane0/stat.npy",
    "/suite2p/plane0/iscell.npy",
    "/ground_truth.csv",
)


def sha256(path: Path) -> str:
    import hashlib

    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def crc32_and_size(path: Path) -> tuple[int, int]:
    checksum = 0
    size = 0
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            checksum = zlib.crc32(block, checksum)
            size += len(block)
    return checksum & 0xFFFFFFFF, size


def fetch(entry: dict[str, object], output_root: Path, retries: int) -> dict[str, object]:
    key = str(entry["key"])
    expected_size = int(entry["size"])
    expected_crc = int(entry["crc"])
    url = str(entry["links"]["content"])
    destination = output_root.joinpath(*key.split("/"))
    destination.parent.mkdir(parents=True, exist_ok=True)

    if destination.is_file():
        actual_crc, actual_size = crc32_and_size(destination)
        if actual_size == expected_size and actual_crc == expected_crc:
            return {"key": key, "bytes": actual_size, "status": "cached"}

    partial = destination.with_name(destination.name + ".partial")
    last_error: Exception | None = None
    for attempt in range(1, retries + 1):
        checksum = 0
        size = 0
        try:
            request = urllib.request.Request(
                url,
                headers={"User-Agent": "CE-source-audit/1.0 (+public Zenodo record 17091226)"},
            )
            with urllib.request.urlopen(request, timeout=180) as response, partial.open(
                "wb"
            ) as output:
                while True:
                    block = response.read(8 * 1024 * 1024)
                    if not block:
                        break
                    output.write(block)
                    checksum = zlib.crc32(block, checksum)
                    size += len(block)
            checksum &= 0xFFFFFFFF
            if size != expected_size or checksum != expected_crc:
                raise ValueError(
                    f"member mismatch {key}: bytes {size}/{expected_size}, "
                    f"crc {checksum}/{expected_crc}"
                )
            os.replace(partial, destination)
            return {"key": key, "bytes": size, "status": "downloaded"}
        except Exception as exc:  # network failures are retried and reported
            last_error = exc
            if attempt < retries:
                time.sleep(min(30, 2**attempt))
    raise RuntimeError(f"failed after {retries} attempts: {key}: {last_error}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--workers", type=int, default=8, choices=range(1, 17))
    parser.add_argument("--retries", type=int, default=5, choices=range(1, 11))
    args = parser.parse_args()

    manifest = args.manifest.resolve()
    output_root = args.output_root.resolve()
    if output_root.name != "selected":
        raise ValueError(f"output root must end with selected: {output_root}")
    manifest_digest = sha256(manifest)
    if manifest_digest != EXPECTED_MANIFEST_SHA256:
        raise ValueError(
            f"manifest SHA-256 mismatch: {manifest_digest} != {EXPECTED_MANIFEST_SHA256}"
        )

    payload = json.loads(manifest.read_text(encoding="utf-8"))
    entries = [
        entry
        for entry in payload["entries"]
        if entry.get("size") is not None
        and any(str(entry["key"]).endswith(suffix) for suffix in SUFFIXES)
    ]
    total_bytes = sum(int(entry["size"]) for entry in entries)
    if len(entries) != EXPECTED_COUNT or total_bytes != EXPECTED_BYTES:
        raise ValueError(
            f"selection mismatch: count={len(entries)}/{EXPECTED_COUNT}, "
            f"bytes={total_bytes}/{EXPECTED_BYTES}"
        )

    output_root.mkdir(parents=True, exist_ok=True)
    completed: list[dict[str, object]] = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = {
            pool.submit(fetch, entry, output_root, args.retries): entry
            for entry in entries
        }
        for index, future in enumerate(concurrent.futures.as_completed(futures), 1):
            result = future.result()
            completed.append(result)
            print(
                f"[{index:03d}/{len(entries)}] {result['status']} "
                f"{result['bytes']} {result['key']}",
                flush=True,
            )

    receipt = {
        "decision": "TRACK2P_SELECTED_DOWNLOAD_PASS",
        "scope": "source_download_only_no_biological_endpoint",
        "manifest_sha256": manifest_digest,
        "files": len(completed),
        "bytes": sum(int(result["bytes"]) for result in completed),
        "downloaded": sum(result["status"] == "downloaded" for result in completed),
        "cached": sum(result["status"] == "cached" for result in completed),
        "output_root": str(output_root),
    }
    print(json.dumps(receipt, ensure_ascii=False, indent=2), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
