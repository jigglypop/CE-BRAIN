#!/usr/bin/env python3
"""Download a source-locked DANDI asset selection with resume and SHA-256 checks."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path, PurePosixPath
from typing import Any


CHUNK_SIZE = 8 * 1024 * 1024
CURL_RANGE_CHUNK_SIZE = 64 * 1024 * 1024


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(CHUNK_SIZE), b""):
            digest.update(chunk)
    return digest.hexdigest()


def safe_target(root: Path, asset_path: str) -> Path:
    posix_path = PurePosixPath(asset_path)
    if posix_path.is_absolute() or not posix_path.parts:
        raise ValueError(f"unsafe absolute/empty asset path: {asset_path!r}")
    if any(part in ("", ".", "..") for part in posix_path.parts):
        raise ValueError(f"unsafe asset path component: {asset_path!r}")
    resolved_root = root.resolve()
    # The validated PurePosixPath components are joined to the already-resolved
    # root.  Resolving a not-yet-created target concurrently on Windows is racy:
    # another worker may create its parent between Win32 path probes.
    return resolved_root.joinpath(*posix_path.parts)


def load_selection(path: Path) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    selection = json.loads(path.read_text(encoding="utf-8"))
    if selection.get("status") != "DANDI_ASSET_SELECTION_AUDIT_PASS":
        raise ValueError("selection receipt is not a passing DANDI asset audit")
    assets = selection.get("selected_assets")
    if not isinstance(assets, list) or not assets:
        raise ValueError("selection has no selected_assets")
    seen: set[str] = set()
    for asset in assets:
        required = {"asset_id", "path", "size", "sha256", "url"}
        missing = required.difference(asset)
        if missing:
            raise ValueError(f"asset is missing fields {sorted(missing)}: {asset}")
        if asset["path"] in seen:
            raise ValueError(f"duplicate selected path: {asset['path']}")
        seen.add(asset["path"])
        if not isinstance(asset["size"], int) or asset["size"] <= 0:
            raise ValueError(f"invalid size for {asset['path']}")
        if len(asset["sha256"]) != 64:
            raise ValueError(f"invalid SHA-256 for {asset['path']}")
    return selection, assets


def verify_existing(target: Path, asset: dict[str, Any]) -> dict[str, Any] | None:
    if not target.exists():
        return None
    observed_size = target.stat().st_size
    if observed_size != asset["size"]:
        raise ValueError(
            f"existing destination size mismatch for {target}: "
            f"{observed_size} != {asset['size']}"
        )
    observed_sha256 = file_sha256(target)
    if observed_sha256 != asset["sha256"]:
        raise ValueError(
            f"existing destination SHA-256 mismatch for {target}: {observed_sha256}"
        )
    return {
        "asset_id": asset["asset_id"],
        "path": asset["path"],
        "size": observed_size,
        "sha256": observed_sha256,
        "transfer": "already_verified",
    }


def _curl_transfer(
    partial: Path, asset: dict[str, Any], timeout: float, offset: int
) -> str:
    executable = shutil.which("curl.exe") or shutil.which("curl")
    if executable is None:
        raise ValueError("curl backend requested but curl executable is unavailable")
    initial_offset = offset
    range_path = partial.with_name(partial.name + ".range")
    while offset < asset["size"]:
        end = min(offset + CURL_RANGE_CHUNK_SIZE, asset["size"]) - 1
        range_path.unlink(missing_ok=True)
        command = [
            executable,
            "--location",
            "--fail",
            "--silent",
            "--show-error",
            "--retry",
            "8",
            "--retry-all-errors",
            "--retry-delay",
            "2",
            "--connect-timeout",
            str(timeout),
            "--range",
            f"{offset}-{end}",
            "--output",
            str(range_path),
            "--write-out",
            "%{http_code}",
            asset["url"],
        ]
        completed = subprocess.run(command, capture_output=True, text=True, check=False)
        if completed.returncode != 0:
            detail = completed.stderr.strip() or completed.stdout.strip()
            raise ValueError(
                f"curl exit {completed.returncode} for {asset['path']}: {detail[:1000]}"
            )
        if completed.stdout.strip() != "206":
            raise ValueError(
                f"curl range HTTP {completed.stdout.strip()!r} for {asset['path']}"
            )
        expected_chunk = end - offset + 1
        if not range_path.is_file() or range_path.stat().st_size != expected_chunk:
            observed = range_path.stat().st_size if range_path.exists() else None
            raise ValueError(
                f"curl range size mismatch for {asset['path']}: {observed} != {expected_chunk}"
            )
        with range_path.open("rb") as source, partial.open("ab") as destination:
            shutil.copyfileobj(source, destination, length=CHUNK_SIZE)
            destination.flush()
            os.fsync(destination.fileno())
        range_path.unlink()
        offset = end + 1
    return "resumed_curl" if initial_offset else "downloaded_curl"


def _download_one(
    root: Path, asset: dict[str, Any], timeout: float, backend: str = "urllib"
) -> dict[str, Any]:
    target = safe_target(root, asset["path"])
    target.parent.mkdir(parents=True, exist_ok=True)
    existing = verify_existing(target, asset)
    if existing is not None:
        return existing

    partial = target.with_name(target.name + ".part")
    offset = partial.stat().st_size if partial.exists() else 0
    if offset > asset["size"]:
        raise ValueError(f"partial file is larger than expected: {partial}")

    if offset == asset["size"]:
        transfer = "completed_partial"
    elif backend == "curl":
        transfer = _curl_transfer(partial, asset, timeout, offset)
    elif backend == "urllib":
        request = urllib.request.Request(asset["url"])
        if offset:
            request.add_header("Range", f"bytes={offset}-")

        try:
            response = urllib.request.urlopen(request, timeout=timeout)
        except urllib.error.HTTPError as exc:
            if exc.code == 416 and offset == asset["size"]:
                response = None
            else:
                raise

        if response is not None:
            status = getattr(response, "status", response.getcode())
            if offset and status == 206:
                mode = "ab"
                transfer = "resumed_urllib"
            elif offset and status == 200:
                mode = "wb"
                transfer = "restarted_server_ignored_range_urllib"
                offset = 0
            elif not offset and status in (200, 206):
                mode = "wb"
                transfer = "downloaded_urllib"
            else:
                response.close()
                raise ValueError(f"unexpected HTTP status {status} for {asset['path']}")

            with response, partial.open(mode) as handle:
                while True:
                    chunk = response.read(CHUNK_SIZE)
                    if not chunk:
                        break
                    handle.write(chunk)
                handle.flush()
                os.fsync(handle.fileno())
        else:
            transfer = "completed_partial"
    else:
        raise ValueError(f"unsupported download backend: {backend}")

    observed_size = partial.stat().st_size
    if observed_size != asset["size"]:
        raise ValueError(
            f"downloaded size mismatch for {asset['path']}: "
            f"{observed_size} != {asset['size']}"
        )
    observed_sha256 = file_sha256(partial)
    if observed_sha256 != asset["sha256"]:
        raise ValueError(
            f"downloaded SHA-256 mismatch for {asset['path']}: {observed_sha256}"
        )
    os.replace(partial, target)
    return {
        "asset_id": asset["asset_id"],
        "path": asset["path"],
        "size": observed_size,
        "sha256": observed_sha256,
        "transfer": transfer,
    }


def fetch_selection(
    selection_path: Path,
    destination: Path,
    *,
    workers: int = 4,
    timeout: float = 120.0,
    backend: str = "urllib",
) -> dict[str, Any]:
    if workers < 1 or workers > 8:
        raise ValueError("workers must be in [1, 8]")
    if backend not in {"urllib", "curl"}:
        raise ValueError("backend must be urllib or curl")
    selection, assets = load_selection(selection_path)
    destination.mkdir(parents=True, exist_ok=True)
    results: list[dict[str, Any]] = []
    errors: list[dict[str, str]] = []

    with ThreadPoolExecutor(max_workers=workers) as pool:
        future_to_asset = {
            pool.submit(_download_one, destination, asset, timeout, backend): asset
            for asset in assets
        }
        for future in as_completed(future_to_asset):
            asset = future_to_asset[future]
            try:
                result = future.result()
                results.append(result)
                print(
                    f"VERIFIED {len(results)}/{len(assets)} "
                    f"{result['path']} ({result['size']} bytes, {result['transfer']})",
                    flush=True,
                )
            except Exception as exc:  # retain all per-asset failures in the receipt
                errors.append({"path": asset["path"], "error": str(exc)})
                print(f"FAILED {asset['path']}: {exc}", flush=True)

    results.sort(key=lambda item: item["path"])
    errors.sort(key=lambda item: item["path"])
    expected_bytes = sum(asset["size"] for asset in assets)
    verified_bytes = sum(item["size"] for item in results)
    passed = len(results) == len(assets) and not errors and verified_bytes == expected_bytes
    return {
        "status": "DANDI_SELECTED_DOWNLOAD_PASS" if passed else "DANDI_SELECTED_DOWNLOAD_FAIL",
        "scope": "byte acquisition and integrity only; no biological endpoint evaluated",
        "selection_receipt": selection_path.as_posix(),
        "selection_receipt_sha256": file_sha256(selection_path),
        "source_manifest_sha256": selection.get("source_manifest_sha256"),
        "canonical_assets_sha256": selection.get("canonical_assets_sha256"),
        "destination": destination.as_posix(),
        "backend": backend,
        "expected_asset_count": len(assets),
        "verified_asset_count": len(results),
        "expected_bytes": expected_bytes,
        "verified_bytes": verified_bytes,
        "assets": results,
        "errors": errors,
        "biological_endpoint_evaluated": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--selection", required=True, type=Path)
    parser.add_argument("--destination", required=True, type=Path)
    parser.add_argument("--receipt", required=True, type=Path)
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--timeout", type=float, default=120.0)
    parser.add_argument("--backend", choices=("urllib", "curl"), default="urllib")
    args = parser.parse_args()

    result = fetch_selection(
        args.selection,
        args.destination,
        workers=args.workers,
        timeout=args.timeout,
        backend=args.backend,
    )
    args.receipt.parent.mkdir(parents=True, exist_ok=True)
    args.receipt.write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps({key: result[key] for key in (
        "status", "expected_asset_count", "verified_asset_count",
        "expected_bytes", "verified_bytes", "errors",
    )}, ensure_ascii=False, indent=2))
    return 0 if result["status"].endswith("PASS") else 1


if __name__ == "__main__":
    raise SystemExit(main())
