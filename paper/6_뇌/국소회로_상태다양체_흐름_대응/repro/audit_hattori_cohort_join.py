#!/usr/bin/env python3
"""Audit whether Hattori neural and intervention files share mouse identities."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import defaultdict
from pathlib import Path
from typing import Any


MOUSE_RE = re.compile(r"^RH\d+$")
COHORTS = ("Imaging", "Inactivation", "paAIP2")


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _normalized_parts(name: str, wrapper_prefix: str) -> list[str] | None:
    if wrapper_prefix:
        if not name.startswith(wrapper_prefix):
            return None
        name = name[len(wrapper_prefix) :]
    parts = [part for part in name.split("/") if part]
    if not parts or parts[0] not in COHORTS:
        return None
    return parts


def audit_cohort_join(
    manifest_path: Path,
    *,
    wrapper_prefix: str = "",
) -> dict[str, Any]:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    ids: dict[str, set[str]] = {cohort: set() for cohort in COHORTS}
    file_counts: dict[str, int] = defaultdict(int)
    uncompressed_bytes: dict[str, int] = defaultdict(int)
    unidentified_files: dict[str, list[str]] = defaultdict(list)

    for entry in manifest["entries"]:
        name = entry["name"]
        if name.endswith("/"):
            continue
        parts = _normalized_parts(name, wrapper_prefix)
        if parts is None:
            continue
        cohort = parts[0]
        file_counts[cohort] += 1
        uncompressed_bytes[cohort] += int(entry["uncompressed_size"])
        mouse_ids = [part for part in parts if MOUSE_RE.fullmatch(part)]
        if len(mouse_ids) != 1:
            unidentified_files[cohort].append("/".join(parts))
            continue
        ids[cohort].add(mouse_ids[0])

    neural_ids = ids["Imaging"]
    intervention_ids = ids["Inactivation"] | ids["paAIP2"]
    neural_intervention_overlap = sorted(neural_ids & intervention_ids)
    pairwise = {
        f"{left}__{right}": sorted(ids[left] & ids[right])
        for index, left in enumerate(COHORTS)
        for right in COHORTS[index + 1 :]
    }
    complete = all(file_counts[cohort] > 0 for cohort in COHORTS)
    join_candidate = complete and bool(neural_intervention_overlap)

    return {
        "status": (
            "HATTORI_PATH_LEVEL_NEURAL_INTERVENTION_JOIN_CANDIDATE"
            if join_candidate
            else "HATTORI_PATH_LEVEL_NEURAL_INTERVENTION_JOIN_BLOCKED"
        ),
        "scope": (
            "path-level mouse identity only; overlap would be necessary but not "
            "sufficient for same-session mediation"
        ),
        "source_manifest": manifest_path.as_posix(),
        "source_manifest_sha256": _sha256(manifest_path),
        "wrapper_prefix": wrapper_prefix,
        "cohorts": {
            cohort: {
                "file_count": file_counts[cohort],
                "uncompressed_bytes": uncompressed_bytes[cohort],
                "mouse_count": len(ids[cohort]),
                "mouse_ids": sorted(ids[cohort]),
                "files_without_exactly_one_mouse_id": len(unidentified_files[cohort]),
            }
            for cohort in COHORTS
        },
        "pairwise_mouse_intersections": pairwise,
        "neural_intervention_mouse_intersection": neural_intervention_overlap,
        "l4_join_gate": "PASS_CANDIDATE" if join_candidate else "FAIL_DISJOINT_COHORTS",
        "biological_endpoint_evaluated": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--wrapper-prefix", default="")
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    result = audit_cohort_join(args.manifest, wrapper_prefix=args.wrapper_prefix)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
