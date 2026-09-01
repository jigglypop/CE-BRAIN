#!/usr/bin/env python3
"""Compare two audited remote-ZIP manifests without opening member payloads."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


IDENTITY_FIELDS = (
    "compressed_size",
    "uncompressed_size",
    "crc32",
    "compression_method",
)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _member_map(manifest: dict[str, Any], strip_prefix: str) -> dict[str, tuple[Any, ...]]:
    members: dict[str, tuple[Any, ...]] = {}
    for entry in manifest["entries"]:
        name = entry["name"]
        if strip_prefix:
            if not name.startswith(strip_prefix):
                continue
            name = name[len(strip_prefix) :]
        if not name or name.endswith("/"):
            continue
        if name in members:
            raise ValueError(f"duplicate normalized member: {name}")
        members[name] = tuple(entry[field] for field in IDENTITY_FIELDS)
    return members


def compare_manifests(
    old_path: Path,
    new_path: Path,
    *,
    old_strip_prefix: str = "",
    new_strip_prefix: str = "",
) -> dict[str, Any]:
    old_manifest = json.loads(old_path.read_text(encoding="utf-8"))
    new_manifest = json.loads(new_path.read_text(encoding="utf-8"))
    old_members = _member_map(old_manifest, old_strip_prefix)
    new_members = _member_map(new_manifest, new_strip_prefix)

    old_names = set(old_members)
    new_names = set(new_members)
    only_old = sorted(old_names - new_names)
    only_new = sorted(new_names - old_names)
    changed = sorted(
        name
        for name in old_names & new_names
        if old_members[name] != new_members[name]
    )
    identical = not only_old and not only_new and not changed

    return {
        "status": (
            "REMOTE_ZIP_MEMBER_IDENTITY_PASS"
            if identical
            else "REMOTE_ZIP_MEMBER_IDENTITY_FAIL"
        ),
        "comparison_scope": list(IDENTITY_FIELDS),
        "old_manifest": {
            "path": old_path.as_posix(),
            "sha256": _sha256(old_path),
            "strip_prefix": old_strip_prefix,
            "member_count": len(old_members),
        },
        "new_manifest": {
            "path": new_path.as_posix(),
            "sha256": _sha256(new_path),
            "strip_prefix": new_strip_prefix,
            "member_count": len(new_members),
        },
        "only_old_count": len(only_old),
        "only_new_count": len(only_new),
        "changed_count": len(changed),
        "only_old": only_old,
        "only_new": only_new,
        "changed": [
            {
                "name": name,
                "old": dict(zip(IDENTITY_FIELDS, old_members[name], strict=True)),
                "new": dict(zip(IDENTITY_FIELDS, new_members[name], strict=True)),
            }
            for name in changed
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--old", required=True, type=Path)
    parser.add_argument("--new", required=True, type=Path)
    parser.add_argument("--old-strip-prefix", default="")
    parser.add_argument("--new-strip-prefix", default="")
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    result = compare_manifests(
        args.old,
        args.new,
        old_strip_prefix=args.old_strip_prefix,
        new_strip_prefix=args.new_strip_prefix,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"].endswith("PASS") else 1


if __name__ == "__main__":
    raise SystemExit(main())
