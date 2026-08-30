"""Signal-blind allocation of DANDI 001701 confirmation assets.

Run once, before any confirmation asset is opened.  The rule uses nothing but
file names:

  1. the whole of ``sub-BaggySweatpants`` is excluded, because chapters 11-14
     consumed one of its sessions and a second session of the same animal is
     not an independent confirmation;
  2. for every remaining subject, the session whose day index is closest to 15
     is selected, ties going to the smaller index -- 15 matches the training
     stage of the consumed development session;
  3. subjects are sorted alphabetically; the first five form the intermediate
     barrier D1 and the remaining six form the sealed confirmation set D2.

The output records each selected asset's id, path, byte size and SHA-256 so the
contract is source-locked before any of them is read.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import requests

DANDISET = "001701"
VERSION = "0.260120.0303"
EXCLUDED_SUBJECT = "sub-BaggySweatpants"
TARGET_DAY = 15
D1_SUBJECTS = 5

HERE = Path(__file__).resolve().parent
DAY = re.compile(r"-DY(\d+)-")


def list_assets() -> list[dict]:
    url = f"https://api.dandiarchive.org/api/dandisets/{DANDISET}/versions/{VERSION}/assets/?page_size=500"
    rows: list[dict] = []
    while url:
        response = requests.get(url, timeout=60)
        response.raise_for_status()
        payload = response.json()
        rows += payload["results"]
        url = payload.get("next")
    return rows


def main() -> None:
    rows = list_assets()
    by_subject: dict[str, list[tuple[int, dict]]] = {}
    for asset in rows:
        subject = asset["path"].split("/")[0]
        if subject == EXCLUDED_SUBJECT:
            continue
        match = DAY.search(asset["path"])
        if match is None:
            continue
        by_subject.setdefault(subject, []).append((int(match.group(1)), asset))

    selected = []
    for subject in sorted(by_subject):
        day, asset = min(by_subject[subject], key=lambda item: (abs(item[0] - TARGET_DAY), item[0]))
        selected.append({"subject": subject, "day": day, "asset_id": asset["asset_id"], "path": asset["path"], "size": asset["size"]})

    for entry in selected:
        detail = requests.get(
            f"https://api.dandiarchive.org/api/dandisets/{DANDISET}/versions/{VERSION}/assets/{entry['asset_id']}/",
            timeout=60,
        )
        detail.raise_for_status()
        digest = detail.json().get("digest", {})
        entry["sha256"] = digest.get("dandi:sha2-256") or digest.get("dandi:dandi-etag")

    allocation = {
        "dandiset": DANDISET,
        "version": VERSION,
        "rule": {
            "excluded_subject": EXCLUDED_SUBJECT,
            "session_choice": f"day index closest to {TARGET_DAY}, ties to the smaller index",
            "split": f"subjects sorted alphabetically; first {D1_SUBJECTS} to D1, remainder to D2",
            "signal_blind": True,
        },
        "total_assets_in_version": len(rows),
        "subjects_available": sorted(by_subject),
        "D1_intermediate": selected[:D1_SUBJECTS],
        "D2_confirmation_sealed": selected[D1_SUBJECTS:],
    }
    (HERE / "confirmation-allocation.json").write_text(json.dumps(allocation, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(allocation, indent=2))


if __name__ == "__main__":
    main()
