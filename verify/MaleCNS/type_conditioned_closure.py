"""Source-neuron leave-one-out prediction of the full 30-category profile.

Catalogue type labels may themselves depend on connectivity. This is an
exploratory catalogue-conditional check, not independent biological prediction.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import sys
from pathlib import Path

import numpy as np


def digest(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def loo_scores(counts, parent, refined, alpha):
    counts = np.asarray(counts)
    parent, refined = np.asarray(parent), np.asarray(refined)
    if counts.ndim != 2 or counts.dtype.kind not in "iu" or np.any(counts < 0):
        raise ValueError("counts must be nonnegative integers")
    if alpha <= 0 or not np.isfinite(alpha):
        raise ValueError("alpha must be finite and positive")
    n, k = counts.shape
    if parent.shape != (n,) or refined.shape != (n,) or not k:
        raise ValueError("invalid groups or count shape")
    _, parent = np.unique(parent, return_inverse=True)
    _, refined = np.unique(refined, return_inverse=True)
    for code in np.unique(refined):
        if len(np.unique(parent[refined == code])) != 1:
            raise ValueError("refined groups must nest inside parent groups")
    parent_sum = np.zeros((int(parent.max()) + 1, k), dtype=np.int64)
    refined_sum = np.zeros((int(refined.max()) + 1, k), dtype=np.int64)
    np.add.at(parent_sum, parent, counts)
    np.add.at(refined_sum, refined, counts)
    degree = counts.sum(axis=1)
    active = degree > 0
    peer_number = np.bincount(refined, weights=active.astype(int), minlength=len(refined_sum))
    has_peer = active & (peer_number[refined] > 1)
    # Subtract the complete held-out source row before constructing either prediction.
    p = parent_sum[parent] - counts
    r = refined_sum[refined] - counts
    r[~has_peer] = p[~has_peer]
    p_prob = (p + alpha / k) / (p.sum(axis=1)[:, None] + alpha)
    r_prob = (r + alpha / k) / (r.sum(axis=1)[:, None] + alpha)
    loss_parent = -(counts * np.log(p_prob)).sum(axis=1)
    loss_refined = -(counts * np.log(r_prob)).sum(axis=1)
    return degree, has_peer, loss_parent, loss_refined


def score_summary(degree, has_peer, baseline, candidate, mask):
    active = mask & (degree > 0)
    total = int(degree[active].sum())
    if not total:
        return {"sources": 0, "weight": 0, "parent_loss": None, "type_loss": None}
    parent_loss, type_loss = float(baseline[active].sum() / total), float(candidate[active].sum() / total)
    return {"sources": int(active.sum()), "weight": total,
            "type_peer_sources": int((active & has_peer).sum()),
            "type_peer_weight": int(degree[active & has_peer].sum()),
            "parent_loss": parent_loss, "type_loss": type_loss,
            "relative_loss_reduction": (parent_loss - type_loss) / parent_loss,
            "unweighted_source_parent_loss": float(np.mean(baseline[active] / degree[active])),
            "unweighted_source_type_loss": float(np.mean(candidate[active] / degree[active])),
            "improved_source_fraction": float(np.mean(candidate[active] < baseline[active]))}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--whole-result", type=Path, required=True)
    parser.add_argument("--result", type=Path, required=True)
    args = parser.parse_args()
    if args.result.exists():
        raise FileExistsError("result exists; preserve prior evidence")
    import pyarrow as pa
    import pyarrow.ipc as ipc
    previous = json.loads(args.whole_result.read_text(encoding="utf-8"))
    arrays_path = Path(previous["arrays"]["path"])
    annotation_path = Path(previous["sources"]["annotations.feather"]["path"])
    if digest(arrays_path) != previous["arrays"]["sha256"]:
        raise ValueError("whole arrays hash mismatch")
    if digest(annotation_path) != previous["sources"]["annotations.feather"]["verified_sha256"]:
        raise ValueError("annotation hash mismatch")
    with np.load(arrays_path, allow_pickle=False) as arrays:
        ids = arrays["annotation_ids"]
        codes = arrays["category_codes"]
        labels = arrays["category_labels"].tolist()
        counts = arrays["out_weight"]
    with pa.memory_map(str(annotation_path), "r") as source:
        table = ipc.open_file(source).read_all()
    ann_ids = table["bodyId"].combine_chunks().to_numpy()
    order = np.argsort(ann_ids)
    if not np.array_equal(ann_ids[order], ids):
        raise ValueError("annotation row identity mismatch")
    type_values = table["type"].to_pylist()
    type_values = [type_values[i] for i in order]
    selected = np.array([labels[code] not in
                         ("ANNOTATED_GLIA", "ANNOTATED_UNCLASSIFIED", "UNANNOTATED_SEGMENT") for code in codes])
    counts, codes = counts[selected], codes[selected]
    type_values = [value for value, keep in zip(type_values, selected) if keep]
    keys = [(int(code), value) for code, value in zip(codes, type_values)]
    lookup = {}
    refined = np.array([lookup.setdefault(key, len(lookup)) for key in keys])
    missing = np.array([value is None for value in type_values])
    records = []
    for alpha in (1.0, 10.0, 100.0):
        degree, peers, base, candidate = loo_scores(counts, codes, refined, alpha)
        records.append({"total_dirichlet_pseudocount": alpha,
                        "all": score_summary(degree, peers, base, candidate, np.ones(len(degree), bool)),
                        "with_type_peers": score_summary(degree, peers, base, candidate, peers & ~missing),
                        "missing_type": score_summary(degree, peers, base, candidate, missing),
                        "categories": [{"category": labels[int(code)],
                                        **score_summary(degree, peers, base, candidate, codes == code)}
                                       for code in np.unique(codes)]})
    result = {"schema": "malecns-type-source-loo-v1", "whole_result": str(args.whole_result.resolve()),
              "whole_result_sha256": digest(args.whole_result),
              "arrays_sha256": previous["arrays"]["sha256"],
              "annotation_sha256": previous["sources"]["annotations.feather"]["verified_sha256"],
              "source_code_sha256": digest(__file__), "argv": sys.argv,
              "software": {"python": platform.python_version(), "executable": sys.executable,
                           "numpy": np.__version__, "pyarrow": pa.__version__},
              "selected_annotation_sources": len(counts), "missing_type_sources": int(missing.sum()),
              "source_type_groups": len(lookup), "target_categories": labels,
              "predictions": records,
              "interpretation": "Exploratory within-animal catalogue-conditional source-LOO structural target prediction; not independent type annotation, activity, memory, or biological replication. Singleton type groups fall back to parent superclass LOO; no raw target is removed."}
    args.result.parent.mkdir(parents=True, exist_ok=True)
    with args.result.open("x", encoding="utf-8") as stream:
        json.dump(result, stream, indent=2, allow_nan=False)
        stream.write("\n")
    print("TYPE_SOURCE_LOO_COMPLETE", flush=True)


if __name__ == "__main__":
    main()
