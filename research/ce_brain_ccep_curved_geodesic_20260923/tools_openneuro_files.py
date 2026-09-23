"""List OpenNeuro snapshot files (with download URLs) through the GraphQL API; metadata only."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import requests

GRAPHQL = "https://openneuro.org/crn/graphql"
HERE = Path(__file__).resolve().parent
QUERY = """
query($id: ID!, $tag: String!, $tree: String) {
  snapshot(datasetId: $id, tag: $tag) { files(tree: $tree) { id filename directory size urls } }
}
"""


def files(dataset: str, tag: str, tree: str | None, prefix: str = "") -> list[dict]:
    resp = requests.post(GRAPHQL, json={"query": QUERY, "variables": {"id": dataset, "tag": tag, "tree": tree}},
                         timeout=120)
    if resp.status_code != 200:
        raise RuntimeError(resp.text[:500])
    rows = []
    for f in resp.json()["data"]["snapshot"]["files"]:
        path = f"{prefix}{f['filename']}"
        if f["directory"]:
            rows.extend(files(dataset, tag, f["id"], path + "/"))
        else:
            rows.append({"path": path, "size": f["size"], "file_id": f["id"], "urls": f.get("urls")})
    return rows


def main() -> int:
    dataset, tag = sys.argv[1], sys.argv[2]
    rows = files(dataset, tag, None)
    out = HERE / f"files_{dataset}_{tag}.json"
    out.write_text(json.dumps(rows, indent=0), encoding="utf-8")
    total = sum(r["size"] or 0 for r in rows)
    print(f"{len(rows)} files, {total / 1e9:.2f} GB -> {out.name}")
    for r in rows:
        if r["path"].endswith((".edf", ".eeg")):
            print(r["path"], r["size"], (r["urls"] or [None])[0])
    return 0


if __name__ == "__main__":
    sys.exit(main())
