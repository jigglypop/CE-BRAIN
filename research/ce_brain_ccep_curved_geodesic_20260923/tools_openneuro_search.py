"""Metadata-only OpenNeuro inventory of iEEG datasets, flagging CCEP/SPES candidates.

No recording payload or scientific endpoint is accessed; only dataset names,
snapshot tags, subject counts and README text are read.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import requests

GRAPHQL = "https://openneuro.org/crn/graphql"
HERE = Path(__file__).resolve().parent
PATTERN = re.compile(r"single[- ]pulse|ccep|cortico-?cortical evoked|spes|electrical stimulation|"
                     r"stimulation[- ]evoked|evoked potential", re.I)

LIST_QUERY = """
query($after: String) {
  datasets(first: 100, modality: "ieeg", after: $after) {
    pageInfo { hasNextPage endCursor }
    edges { node { id name latestSnapshot { tag size readme summary { subjects modalities } } } }
  }
}
"""


def post(query: str, variables: dict) -> dict:
    resp = requests.post(GRAPHQL, json={"query": query, "variables": variables}, timeout=120)
    if resp.status_code != 200:
        raise RuntimeError(f"HTTP {resp.status_code}: {resp.text[:600]}")
    payload = resp.json()
    if not payload.get("data"):
        raise RuntimeError(json.dumps(payload.get("errors"))[:600])
    return payload["data"]


def main() -> int:
    rows, after = [], None
    for _ in range(50):
        block = post(LIST_QUERY, {"after": after})["datasets"]
        for edge in block["edges"]:
            node = (edge or {}).get("node")
            if not node or not node.get("id"):
                continue
            snap = node.get("latestSnapshot") or {}
            summ = snap.get("summary") or {}
            text = f"{node.get('name') or ''}\n{snap.get('readme') or ''}"
            rows.append({"id": node["id"], "name": node.get("name"), "tag": snap.get("tag"),
                         "size_bytes": snap.get("size"), "n_subjects": len(summ.get("subjects") or []),
                         "ccep_like": bool(PATTERN.search(text)),
                         "readme_head": (snap.get("readme") or "")[:600]})
        if not block["pageInfo"]["hasNextPage"]:
            break
        after = block["pageInfo"]["endCursor"]
    rows.sort(key=lambda r: (not r["ccep_like"], -r["n_subjects"]))
    (HERE / "openneuro_ieeg_inventory.json").write_text(
        json.dumps(rows, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"ieeg datasets: {len(rows)}; ccep-like: {sum(r['ccep_like'] for r in rows)}")
    for r in rows:
        if r["ccep_like"]:
            print(f"{r['id']}\t{r['n_subjects']}\t{r['tag']}\t{(r['size_bytes'] or 0) / 1e9:.1f}GB\t{r['name']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
