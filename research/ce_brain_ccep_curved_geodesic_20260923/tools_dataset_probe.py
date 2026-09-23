"""Metadata-only probe of an OpenNeuro dataset through its GitHub mirror.

Reads the git tree and small sidecar text files (participants, descriptions,
electrodes, coordsystem, channels, events headers).  Never downloads a
recording payload, so no scientific endpoint is opened.

Usage: python tools_dataset_probe.py ds006254 1.0.0 [--show N]
"""
from __future__ import annotations

import argparse
import collections
import json
import re
import sys
from pathlib import Path

import requests

HERE = Path(__file__).resolve().parent
UA = {"User-Agent": "CE-ccep-curved-geodesic-probe/1"}


def tree(dataset: str, ref: str) -> dict:
    url = f"https://api.github.com/repos/OpenNeuroDatasets/{dataset}/git/trees/{ref}?recursive=1"
    resp = requests.get(url, headers=UA, timeout=60)
    resp.raise_for_status()
    return resp.json()


def raw(dataset: str, ref: str, path: str) -> str:
    url = f"https://raw.githubusercontent.com/OpenNeuroDatasets/{dataset}/{ref}/{path}"
    resp = requests.get(url, headers=UA, timeout=60)
    resp.raise_for_status()
    return resp.text


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("dataset")
    parser.add_argument("ref")
    parser.add_argument("--show", type=int, default=12)
    parser.add_argument("--grep", default=None, help="only print heads of paths matching this regex")
    args = parser.parse_args()
    t = tree(args.dataset, args.ref)
    if args.grep:
        sys.stdout.reconfigure(encoding="utf-8")
        for p in (e["path"] for e in t["tree"] if e["type"] == "blob"):
            if re.search(args.grep, p):
                lines = raw(args.dataset, args.ref, p).splitlines()
                print(f"----- {p} ({len(lines)} lines)")
                print("\n".join(lines[: args.show]))
        return 0
    blobs = [e for e in t["tree"] if e["type"] == "blob"]
    paths = [e["path"] for e in blobs]
    (HERE / f"probe_{args.dataset}_{args.ref}.json").write_text(
        json.dumps({"tree_sha": t["sha"], "paths": paths}, indent=0), encoding="utf-8")
    sys.stdout.reconfigure(encoding="utf-8")
    print(f"tree_sha={t['sha']} truncated={t['truncated']} blobs={len(blobs)}")
    print("top:", [p for p in paths if "/" not in p])
    suffix = collections.Counter(p.rsplit("_", 1)[-1] for p in paths if p.startswith("sub-"))
    print("suffixes:", suffix.most_common(25))
    subjects = sorted({p.split("/", 1)[0] for p in paths if p.startswith("sub-")})
    print("subjects:", len(subjects), subjects[:40])
    for name in ("dataset_description.json", "participants.tsv", "participants.json", "README", "README.md"):
        if name in paths:
            print(f"----- {name}\n{raw(args.dataset, args.ref, name)[:3000]}")
    first = subjects[0] if subjects else None
    if first:
        mine = [p for p in paths if p.startswith(first + "/")]
        print(f"----- files of {first}:")
        for p in mine:
            print("  ", p)
        for p in mine:
            if p.endswith(("_electrodes.tsv", "_coordsystem.json", "_channels.tsv", "_events.tsv", "_ieeg.json")):
                text = raw(args.dataset, args.ref, p)
                lines = text.splitlines()
                print(f"----- {p} ({len(lines)} lines)")
                print("\n".join(lines[: args.show]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
