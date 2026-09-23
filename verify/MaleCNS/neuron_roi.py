"""ROI-resolved MaleCNS neuron dyads from the synapse table.

`build` streams every synapse row of `syn-partners` (minconf 0.5) once, keeps rows
whose two bodies are nodes of `neuron-graph-v1`, and stores unique
(dyad, primary_post ROI) counts. Synapses without a primary ROI get the code
`NONE`. The per-dyad ROI sum must equal the neuron graph weight for every dyad,
which cross-checks the synapse table against the weight table exactly.
`query` answers pre/post type-by-ROI synapse counts from the cache in seconds.
"""

from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
import importlib.util
import json
import os
from pathlib import Path
import platform
import sys
import time

import numpy as np

HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("malecns_neuron_graph", HERE / "neuron_graph.py")
graph_module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(graph_module)
digest, locate = graph_module.digest, graph_module.locate
ROOT = graph_module.ROOT
SYNAPSES = graph_module.FLAT_DIR / "syn-partners-male-cns-v1.0-minconf-0.5.feather"
NONE = "NONE"


def roi_codes(dictionary, indices, lookup):
    """Map one batch's dictionary indices to global ROI codes; null -> NONE."""
    local = np.array([lookup[name] for name in dictionary], dtype=np.int16)
    indices = np.asarray(indices)
    out = np.full(len(indices), lookup[NONE], dtype=np.int16)
    valid = indices >= 0
    out[valid] = local[indices[valid]]
    return out


def reduce_keys(keys):
    keys = np.sort(keys)
    if not len(keys):
        return keys, np.zeros(0, dtype=np.int64)
    starts = np.flatnonzero(np.r_[True, keys[1:] != keys[:-1]])
    return keys[starts], np.diff(np.r_[starts, len(keys)])


def merge_reduced(parts):
    keys = np.concatenate([k for k, _ in parts])
    counts = np.concatenate([c for _, c in parts])
    order = np.argsort(keys, kind="stable")
    keys, counts = keys[order], counts[order]
    starts = np.flatnonzero(np.r_[True, keys[1:] != keys[:-1]])
    return keys[starts], np.add.reduceat(counts, starts)


def build(args):
    import pyarrow as pa
    import pyarrow.compute as pc
    import pyarrow.ipc as ipc
    for path in (args.cache, args.result):
        if path.exists():
            raise FileExistsError("outputs already exist; do not overwrite research evidence")
    started, timing = time.perf_counter(), {}
    graph_result = json.loads(args.graph_result.read_text(encoding="utf-8"))
    graph = graph_module.load(args.graph_result)
    ids, n = graph["node_ids"], len(graph["node_ids"])
    t = time.perf_counter()
    manifest = json.loads((graph_module.FLAT_DIR / "manifest.json").read_text(encoding="utf-8"))
    entry = next(f for f in manifest["files"] if f["name"] == SYNAPSES.name)
    if SYNAPSES.stat().st_size != entry["bytes"]:
        raise ValueError("synapse table size differs from flat manifest")
    stamp = SYNAPSES.stat().st_mtime_ns
    with pa.memory_map(str(SYNAPSES), "r") as source:
        reader = ipc.open_file(source)
        batches = reader.num_record_batches
        first = reader.get_batch(0)
        field = first.schema.get_field_index("primary_post")
        names = first.column(field).dictionary.to_pylist() + [NONE]
        lookup = {name: code for code, name in enumerate(names)}
        width = len(names)
        rows = 0

        def work(chunk):
            pre = np.concatenate([b.column(b.schema.get_field_index("body_pre")).to_numpy() for b in chunk])
            post = np.concatenate([b.column(b.schema.get_field_index("body_post")).to_numpy() for b in chunk])
            roi = np.concatenate([roi_codes(b.column(field).dictionary.to_pylist(),
                                            pc.fill_null(b.column(field).indices, -1).to_numpy(), lookup)
                                  for b in chunk])
            ip, kp = locate(pre, ids)
            iq, kq = locate(post, ids)
            both = kp & kq
            keys = (ip[both].astype(np.int64) * n + iq[both]) * width + roi[both]
            return len(pre), reduce_keys(keys)
        chunks = ([reader.get_batch(i) for i in range(start, min(start + args.batches_per_chunk, batches))]
                  for start in range(0, batches, args.batches_per_chunk))
        parts = []
        with ThreadPoolExecutor(args.workers) as pool:
            for count, part in pool.map(work, chunks):
                rows += count
                parts.append(part)
    timing["stream_synapses"] = round(time.perf_counter() - t, 3)
    t = time.perf_counter()
    keys, counts = merge_reduced(parts)
    timing["merge"] = round(time.perf_counter() - t, 3)
    t = time.perf_counter()
    dyad = keys // width
    starts = np.flatnonzero(np.r_[True, dyad[1:] != dyad[:-1]])
    per_dyad = np.add.reduceat(counts, starts)
    graph_keys = graph_module.dyad_keys(graph["indptr"], graph["indices"], n)
    checks = {"synapse_rows_equal_segment_weight": rows == graph_result["scope"]["segment_weight"],
              "dyads_equal": bool(np.array_equal(dyad[starts], graph_keys)),
              "per_dyad_synapses_equal_weight": bool(np.array_equal(per_dyad, graph["weight"].astype(np.int64))),
              "node_synapses_equal": int(counts.sum()) == graph_result["scope"]["node_weight"]}
    timing["check"] = round(time.perf_counter() - t, 3)
    if SYNAPSES.stat().st_mtime_ns != stamp:
        raise ValueError("synapse table changed while reading")
    args.cache.parent.mkdir(parents=True, exist_ok=True)
    with args.cache.open("xb") as stream:
        np.savez(stream, dyad_roi_key=keys, count=counts.astype(np.uint32), roi_names=np.asarray(names),
                 node_count=np.int64(n))
    failed = [name for name, value in checks.items() if not value]
    result = {"schema": "malecns-neuron-roi-v1", "status": "FAIL" if failed else "PASS", "failed_checks": failed,
              "scope": {"synapse_rows": rows, "node_synapses": int(counts.sum()), "dyad_roi_cells": len(keys),
                        "dyads": len(starts), "rois_including_none": width,
                        "node_synapses_without_roi": int(counts[keys % width == lookup[NONE]].sum())},
              "checks": checks, "graph_result": str(args.graph_result.resolve()),
              "graph_cache_sha256": graph_result["cache"]["sha256"],
              "source": {"path": str(SYNAPSES), "bytes": SYNAPSES.stat().st_size, "manifest_sha256": entry["sha256"],
                         "manifest_md5Base64": entry["md5Base64"], "note": "size checked; 6.8 GB not rehashed"},
              "cache": {"path": str(args.cache.resolve()), "bytes": args.cache.stat().st_size,
                        "sha256": digest(args.cache).hexdigest()},
              "source_code_sha256": digest(__file__).hexdigest(), "argv": sys.argv,
              "software": {"python": platform.python_version(), "numpy": np.__version__, "pyarrow": pa.__version__},
              "timing_seconds": timing, "elapsed_seconds": round(time.perf_counter() - started, 3),
              "interpretation": "Synapse counts per annotated-neuron dyad and postsynaptic primary ROI, one male animal. Not activity, sign, strength or function."}
    args.result.parent.mkdir(parents=True, exist_ok=True)
    with args.result.open("x", encoding="utf-8") as stream:
        json.dump(result, stream, indent=2, ensure_ascii=True, allow_nan=False)
        stream.write("\n")
    print(f"NEURON_ROI_{result['status']} cells={len(keys)} elapsed={result['elapsed_seconds']} s "
          f"timing={timing} failed={failed}", flush=True)
    if failed:
        raise SystemExit(1)


def load(result_path, verify_hash=True):
    result = json.loads(Path(result_path).read_text(encoding="utf-8"))
    if result.get("status") != "PASS":
        raise ValueError("ROI cache did not pass its cross-checks")
    path = Path(result["cache"]["path"])
    if verify_hash and digest(path).hexdigest() != result["cache"]["sha256"]:
        raise ValueError("ROI cache hash changed")
    with np.load(path) as cache:
        return {"key": cache["dyad_roi_key"], "count": cache["count"],
                "roi_names": cache["roi_names"].tolist(), "node_count": int(cache["node_count"])}


def type_roi_counts(graph, roi, pre_mask, post_mask):
    """Synapse counts by ROI for dyads with pre in pre_mask and post in post_mask."""
    n, width = roi["node_count"], len(roi["roi_names"])
    dyad = roi["key"] // width
    keep = pre_mask[dyad // n] & post_mask[dyad % n]
    return np.bincount((roi["key"][keep] % width).astype(np.int64), roi["count"][keep], minlength=width).astype(np.int64)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    make = commands.add_parser("build")
    make.add_argument("--graph-result", type=Path, default=HERE / "neuron_graph_result.json")
    make.add_argument("--cache", type=Path,
                      default=graph_module.ANALYSIS_DIR / "neuron-roi-v1/neuron_roi.npz")
    make.add_argument("--result", type=Path, default=HERE / "neuron_roi_result.json")
    make.add_argument("--batches-per-chunk", type=int, default=16)
    make.add_argument("--workers", type=int, default=min(8, os.cpu_count() or 1))
    ask = commands.add_parser("query")
    ask.add_argument("--graph-result", type=Path, default=HERE / "neuron_graph_result.json")
    ask.add_argument("--result", type=Path, default=HERE / "neuron_roi_result.json")
    ask.add_argument("--pre-type-prefix", required=True)
    ask.add_argument("--post-type-prefix", required=True)
    args = parser.parse_args()
    if args.command == "build":
        build(args)
        return
    started = time.perf_counter()
    graph, roi = graph_module.load(args.graph_result, verify_hash=False), load(args.result, verify_hash=False)
    types = graph["type_labels"]
    code_mask = lambda prefix: np.array([t.startswith(prefix) for t in types] + [False])[graph["type_code"]]
    counts = type_roi_counts(graph, roi, code_mask(args.pre_type_prefix), code_mask(args.post_type_prefix))
    shown = {roi["roi_names"][i]: int(c) for i, c in enumerate(counts) if c}
    print(json.dumps({"pre": args.pre_type_prefix, "post": args.post_type_prefix, "total": int(counts.sum()),
                      "by_roi": dict(sorted(shown.items(), key=lambda kv: -kv[1])),
                      "seconds": round(time.perf_counter() - started, 2)}, indent=1))


if __name__ == "__main__":
    main()
