"""Outcome-blind subject split for DANDI 000004 human memory replication."""
from __future__ import annotations

import hashlib
import json
import re
import urllib.request
from collections import Counter

ASSET_URL = "https://api.dandiarchive.org/api/dandisets/000004/versions/0.220126.1852/assets/?page_size=1000"
OPENED_SUBJECTS = {"P19HMH"}


def role(subject: str) -> str:
    if subject in OPENED_SUBJECTS:
        return "development_opened"
    value = int(hashlib.sha256(f"ce-brain-human-memory-v1:{subject}".encode()).hexdigest()[:8], 16) / 2**32
    return "development" if value < 0.60 else "calibration" if value < 0.80 else "confirmation"


def inventory() -> dict[str, object]:
    with urllib.request.urlopen(ASSET_URL, timeout=30) as response:
        assets = json.load(response)["results"]
    by_subject: dict[str, list[dict[str, object]]] = {}
    for asset in assets:
        match = re.match(r"sub-([^/]+)/", str(asset["path"]))
        if not match:
            raise RuntimeError("HUMAN_MEMORY_INVENTORY_STOP: subject path")
        by_subject.setdefault(match.group(1), []).append(asset)
    roles = Counter(role(subject) for subject in by_subject)
    unopened_development = [subject for subject in by_subject if role(subject) == "development"]
    next_subject = min(
        unopened_development,
        key=lambda subject: min(int(asset["size"]) for asset in by_subject[subject]),
    )
    # When conversion produced multiple objects, use the largest object first;
    # P19 showed that the smaller object can contain only half the learning block.
    selected_asset = max(by_subject[next_subject], key=lambda asset: int(asset["size"]))
    return {
        "dandiset": "000004@0.220126.1852",
        "assets": len(assets),
        "subjects": len(by_subject),
        "role_counts": dict(sorted(roles.items())),
        "opened_subjects_forced_development": sorted(OPENED_SUBJECTS),
        "next_unopened_development_subject": next_subject,
        "next_asset": selected_asset,
        "selection_rule": "smallest per-subject minimum size among development subjects, then largest object within subject",
    }
