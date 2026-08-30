"""Outcome-blind session inventory for unopened DANDI 001371 development subjects."""
from __future__ import annotations

import json
import sys
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.request import urlopen

import fsspec
import h5py
import numpy as np


ASSET_API = "https://api.dandiarchive.org/api/dandisets/001371/versions/draft/assets/"
SUBJECTS = ("S29", "S20")


def eligible(values: dict[str, int]) -> bool:
    return bool(
        values["switch"] >= 30
        and values["stay"] >= 10
        and values["CA1"] >= 20
        and values["PFC"] >= 20
    )


def inspect_asset(asset: dict[str, object]) -> dict[str, object]:
    detail = json.load(urlopen(f"{ASSET_API}{asset['asset_id']}/", timeout=60))
    url = next(value for value in detail["contentUrl"] if "s3.amazonaws.com/blobs" in value)
    remote = fsspec.open(url, "rb", block_size=1024 * 1024, cache_type="bytes").open()
    nwb = h5py.File(remote, "r", driver="fileobj")
    try:
        update_counts = Counter(np.asarray(nwb["intervals/trials/update_type"]).tolist())
        has_region = "units/region" in nwb
        regions = Counter(
            value.decode() if isinstance(value, bytes) else str(value)
            for value in np.asarray(nwb["units/region"])
        ) if has_region else Counter()
        values = {
            "trials": int(len(nwb["intervals/trials/id"])),
            "non_update": int(update_counts[1]),
            "switch": int(update_counts[2]),
            "stay": int(update_counts[3]),
            "CA1": int(regions["CA1"]),
            "PFC": int(regions["PFC"]),
            "has_unit_region": has_region,
        }
        return {
            "path": asset["path"],
            "asset_id": asset["asset_id"],
            "size": int(asset["size"]),
            **values,
            "eligible": eligible(values),
        }
    finally:
        nwb.close()
        remote.close()


def run() -> dict[str, object]:
    listing = json.load(urlopen(f"{ASSET_API}?page_size=1000", timeout=60))
    assets = [
        asset for asset in listing["results"]
        if any(f"sub-{subject}/" in asset["path"] for subject in SUBJECTS)
    ]
    results = []
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = {executor.submit(inspect_asset, asset): asset for asset in assets}
        for future in as_completed(futures):
            result = future.result()
            print(f"inspected {result['path']}", file=sys.stderr, flush=True)
            results.append(result)
    results.sort(key=lambda item: item["path"])
    return {
        "decision": (
            "UPDATE_TASK_R2_SESSIONS_FOUND"
            if any(item["eligible"] for item in results)
            else "UPDATE_TASK_R2_SESSION_APPARATUS_STOP"
        ),
        "subjects": list(SUBJECTS),
        "sessions": results,
        "eligible": [item["path"] for item in results if item["eligible"]],
    }


if __name__ == "__main__":
    print(json.dumps(run(), indent=2, sort_keys=True))
