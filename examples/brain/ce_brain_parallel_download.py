"""Resumable parallel range downloader with a mandatory SHA-256 gate."""
from __future__ import annotations

import argparse
import concurrent.futures
import hashlib
import os
import time
import urllib.request
from pathlib import Path


def byte_ranges(size: int, chunk_size: int) -> list[tuple[int, int, int]]:
    if size <= 0 or chunk_size <= 0:
        raise ValueError("size and chunk_size must be positive")
    return [(i, start, min(size - 1, start + chunk_size - 1)) for i, start in enumerate(range(0, size, chunk_size))]


def part_path(parts_dir: Path, index: int) -> Path:
    return parts_dir / f"part-{index:05d}.bin"


def download_part(url: str, target: Path, start: int, end: int, retries: int = 5) -> None:
    expected = end - start + 1
    if target.is_file() and target.stat().st_size == expected:
        return
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_suffix(".tmp")
    for attempt in range(retries):
        try:
            request = urllib.request.Request(url, headers={"Range": f"bytes={start}-{end}", "User-Agent": "CE-BRAIN-stage6/1"})
            with urllib.request.urlopen(request, timeout=60) as response, temporary.open("wb") as output:
                if response.status != 206:
                    raise RuntimeError(f"range request returned HTTP {response.status}")
                while block := response.read(1024 * 1024):
                    output.write(block)
            if temporary.stat().st_size != expected:
                raise RuntimeError(f"short range: {temporary.stat().st_size} != {expected}")
            temporary.replace(target)
            return
        except Exception:
            if temporary.exists():
                temporary.unlink()
            if attempt + 1 == retries:
                raise
            time.sleep(2**attempt)


def file_digest(path: Path, algorithm: str = "sha256") -> str:
    digest = hashlib.new(algorithm)
    with path.open("rb") as source:
        while block := source.read(8 * 1024 * 1024):
            digest.update(block)
    return digest.hexdigest()


def assemble(parts_dir: Path, output: Path, ranges: list[tuple[int, int, int]], expected_hash: str, algorithm: str = "sha256") -> str:
    if output.exists():
        actual = file_digest(output, algorithm)
        if actual != expected_hash:
            raise RuntimeError(f"existing output hash mismatch: {actual}")
        return actual
    temporary = output.with_suffix(output.suffix + ".assembling")
    with temporary.open("wb") as destination:
        for index, start, end in ranges:
            part = part_path(parts_dir, index)
            expected = end - start + 1
            if not part.is_file() or part.stat().st_size != expected:
                raise RuntimeError(f"missing or short part {index}")
            with part.open("rb") as source:
                while block := source.read(8 * 1024 * 1024):
                    destination.write(block)
    actual = file_digest(temporary, algorithm)
    if actual != expected_hash:
        raise RuntimeError(f"assembled hash mismatch: {actual}")
    temporary.replace(output)
    return actual


def download(url: str, output: Path, size: int, expected_hash: str, workers: int, chunk_size: int, algorithm: str = "sha256") -> str:
    ranges = byte_ranges(size, chunk_size)
    parts_dir = output.with_suffix(output.suffix + ".parts")
    output.parent.mkdir(parents=True, exist_ok=True)
    if output.exists():
        return assemble(parts_dir, output, ranges, expected_hash, algorithm)
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
        futures = [pool.submit(download_part, url, part_path(parts_dir, i), start, end) for i, start, end in ranges]
        for future in concurrent.futures.as_completed(futures):
            future.result()
    actual = assemble(parts_dir, output, ranges, expected_hash, algorithm)
    for index, _, _ in ranges:
        part_path(parts_dir, index).unlink()
    try:
        parts_dir.rmdir()
    except OSError:
        pass
    return actual


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--size", type=int, required=True)
    parser.add_argument("--sha256", "--expected-hash", dest="expected_hash", required=True)
    parser.add_argument("--hash-alg", choices=("sha256", "md5"), default="sha256")
    parser.add_argument("--workers", type=int, default=12)
    parser.add_argument("--chunk-mib", type=int, default=32)
    args = parser.parse_args()
    actual = download(args.url, args.output, args.size, args.expected_hash.lower(), args.workers, args.chunk_mib * 1024 * 1024, args.hash_alg)
    print(f"PASS {actual} {args.output}")


if __name__ == "__main__":
    main()
