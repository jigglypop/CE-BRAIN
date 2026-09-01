#!/usr/bin/env python3
"""Audit and select DANDI assets from the published ``assets.yaml`` manifest."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import defaultdict
from pathlib import Path
from typing import Any

import yaml


DAY_RE = re.compile(r"_ses-ymaze-day(?P<day>\d+)")
SUBJECT_RE = re.compile(r"^sub-(?P<subject>[^/]+)/")


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _group(subject: str) -> str:
    normalized = subject.replace("_", "-")
    if normalized.startswith("SparseKO-"):
        return "SparseKO"
    if normalized.startswith("Ctrl-"):
        return "Ctrl"
    if normalized.startswith("Cre-"):
        return "Cre"
    return "Other"


def _normalized_subject(subject: str) -> str:
    """Normalize the provider's path (hyphen) and metadata (underscore) spellings."""
    return subject.replace("_", "-")


def _direct_url(asset: dict[str, Any]) -> str:
    urls = asset.get("contentUrl", [])
    for url in urls:
        if "dandiarchive.s3.amazonaws.com/blobs/" in url:
            return url
    if urls:
        return urls[0]
    raise ValueError(f"asset has no contentUrl: {asset.get('path')}")


def _participant(asset: dict[str, Any]) -> str:
    participants = [
        item.get("identifier")
        for item in asset.get("wasAttributedTo", [])
        if item.get("schemaKey") == "Participant" and item.get("identifier")
    ]
    if len(participants) != 1:
        raise ValueError(
            f"expected exactly one participant for {asset.get('path')}: {participants}"
        )
    return participants[0]


def audit_manifest(
    manifest_path: Path,
    *,
    include_patterns: list[str] | None = None,
) -> dict[str, Any]:
    include_patterns = include_patterns or []
    compiled = [re.compile(pattern) for pattern in include_patterns]
    raw_assets = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    if not isinstance(raw_assets, list):
        raise ValueError("assets manifest must contain a YAML list")

    records: list[dict[str, Any]] = []
    seen_paths: set[str] = set()
    seen_ids: set[str] = set()
    mismatches: list[dict[str, str]] = []
    for asset in raw_assets:
        path = asset["path"]
        asset_id = asset["identifier"]
        if path in seen_paths or asset_id in seen_ids:
            raise ValueError(f"duplicate asset path or identifier: {path} / {asset_id}")
        seen_paths.add(path)
        seen_ids.add(asset_id)

        digest = asset.get("digest", {}).get("dandi:sha2-256")
        if not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest):
            raise ValueError(f"missing/invalid SHA-256 for {path}")
        subject = _participant(asset)
        path_match = SUBJECT_RE.match(path)
        path_subject = path_match.group("subject") if path_match else None
        if path_subject is None or _normalized_subject(path_subject) != _normalized_subject(subject):
            mismatches.append(
                {"path": path, "path_subject": str(path_subject), "participant": subject}
            )
        day_match = DAY_RE.search(path)
        day = int(day_match.group("day")) if day_match else None
        record = {
            "asset_id": asset_id,
            "path": path,
            "size": int(asset["contentSize"]),
            "sha256": digest,
            "url": _direct_url(asset),
            "subject": subject,
            "group": _group(subject),
            "day": day,
            "encoding_format": asset.get("encodingFormat"),
        }
        records.append(record)

    records.sort(key=lambda record: record["path"])
    canonical = json.dumps(
        records, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    selected = [
        record
        for record in records
        if not compiled or any(pattern.search(record["path"]) for pattern in compiled)
    ]

    def summarize(items: list[dict[str, Any]]) -> dict[str, Any]:
        by_group: dict[str, dict[str, Any]] = {}
        groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for item in items:
            groups[item["group"]].append(item)
        for group, group_items in sorted(groups.items()):
            by_group[group] = {
                "asset_count": len(group_items),
                "total_bytes": sum(item["size"] for item in group_items),
                "subjects": sorted({item["subject"] for item in group_items}),
                "days": sorted({item["day"] for item in group_items if item["day"] is not None}),
            }
        return {
            "asset_count": len(items),
            "total_bytes": sum(item["size"] for item in items),
            "subject_count": len({item["subject"] for item in items}),
            "by_group": by_group,
        }

    selection_ok = bool(selected) and not mismatches
    return {
        "status": (
            "DANDI_ASSET_SELECTION_AUDIT_PASS"
            if selection_ok
            else "DANDI_ASSET_SELECTION_AUDIT_FAIL"
        ),
        "scope": "published asset identities and paths only; no NWB values evaluated",
        "source_manifest": manifest_path.as_posix(),
        "source_manifest_sha256": _file_sha256(manifest_path),
        "canonical_assets_sha256": hashlib.sha256(canonical).hexdigest(),
        "include_regex": include_patterns,
        "all_assets": summarize(records),
        "selected_assets_summary": summarize(selected),
        "participant_path_mismatches": mismatches,
        "selected_assets": selected,
        "biological_endpoint_evaluated": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--include-regex", action="append", default=[])
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    result = audit_manifest(args.manifest, include_patterns=args.include_regex)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"].endswith("PASS") else 1


if __name__ == "__main__":
    raise SystemExit(main())
