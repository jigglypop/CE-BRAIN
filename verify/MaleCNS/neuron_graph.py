"""Neuron-level MaleCNS contact graph cache with independent cross-checks.

`build` streams the locked segment table once, keeps every annotated non-Glia
body as a node, stores node-to-node contacts as one out-CSR and all contact
to or from other segments as per-node boundary totals. It then checks the
cache against the whole-structure census, both prebuilt incoming CSRs and the
official traced-only neuron table. `check` reloads the cache in about a second.
Contact counts only; no activity, sign, delay or biological metric is implied.
"""

from __future__ import annotations

import argparse
import base64
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import os
from pathlib import Path
import platform
import sys
import time

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
SOURCE_DIR = ROOT / "data/local/malecns-v1.0"
FLAT_DIR = ROOT / "data/local/malecns-v1.0-flat-connectome"
ANALYSIS_DIR = ROOT / "data/local/malecns-analysis"
PREBUILT = {"full": ROOT / "data/local/malecns-full", "neurons166k": ROOT / "data/local/malecns-neurons166k"}
TRACED = "connectome-weights-male-cns-v1.0-minconf-0.5-traced-only.feather"
GLIA = "ANNOTATED_GLIA"
UNCLASSIFIED = "ANNOTATED_UNCLASSIFIED"
UNKNOWN = "UNANNOTATED_SEGMENT"


def digest(path, algorithm="sha256"):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, algorithm)


def locate(values, reference):
    indices = np.searchsorted(reference, values)
    matched = indices < len(reference)
    matched[matched] &= reference[indices[matched]] == values[matched]
    return indices, matched


def node_scope(ids, statuses, superclasses, types):
    """Sorted non-Glia annotation IDs with superclass/type codes (-1 = missing)."""
    ids = np.asarray(ids, dtype=np.int64)
    if ids.ndim != 1 or np.any(ids < 0) or len(ids) != len(statuses):
        raise ValueError("annotation IDs must be a nonnegative vector aligned with columns")
    keep = np.array([status != "Glia" for status in statuses])
    order = np.flatnonzero(keep)[np.argsort(ids[keep], kind="stable")]
    ids = ids[order]
    if np.any(ids[1:] == ids[:-1]):
        raise ValueError("duplicate annotation ID")

    def encode(column):
        values = [column[i] for i in order]
        labels = sorted({v for v in values if v is not None})
        lookup = {label: code for code, label in enumerate(labels)}
        return np.array([lookup.get(v, -1) for v in values], dtype=np.int32), labels
    superclass, superclass_labels = encode(superclasses)
    type_code, type_labels = encode(types)
    return ids, superclass, superclass_labels, type_code, type_labels


class EdgeCollector:
    """Split segment rows into node-to-node contacts and per-node boundary totals."""

    def __init__(self, ids):
        self.ids, n = ids, len(ids)
        self.src, self.dst, self.weight = [], [], []
        self.out_total = np.zeros(n, dtype=np.int64)
        self.in_total = np.zeros(n, dtype=np.int64)
        self.out_boundary = np.zeros(n, dtype=np.int64)
        self.in_boundary = np.zeros(n, dtype=np.int64)
        self.rows = self.weight_sum = 0

    def split(self, pre, post, weight):
        """Pure per-chunk work, safe to run in worker threads."""
        pre, post, weight = (np.asarray(a) for a in (pre, post, weight))
        if any(a.ndim != 1 or a.dtype.kind not in "iu" for a in (pre, post, weight)):
            raise ValueError("edge columns must be integer vectors without NULLs")
        if len(pre) != len(post) or len(pre) != len(weight):
            raise ValueError("edge columns have incompatible lengths")
        if np.any(weight <= 0) or np.any(weight > np.iinfo(np.uint32).max):
            raise ValueError("contact weight outside (0, 2^32)")
        n = len(self.ids)
        ip, kp = locate(pre, self.ids)
        iq, kq = locate(post, self.ids)
        both = kp & kq
        return (np.bincount(ip[kp], weight[kp], minlength=n), np.bincount(iq[kq], weight[kq], minlength=n),
                np.bincount(ip[kp & ~kq], weight[kp & ~kq], minlength=n),
                np.bincount(iq[kq & ~kp], weight[kq & ~kp], minlength=n),
                ip[both].astype(np.int32), iq[both].astype(np.int32), weight[both].astype(np.uint32),
                len(pre), int(weight.sum(dtype=np.int64)))

    def merge(self, part):
        out_total, in_total, out_boundary, in_boundary, src, dst, weight, rows, weight_sum = part
        self.out_total += out_total.astype(np.int64)
        self.in_total += in_total.astype(np.int64)
        self.out_boundary += out_boundary.astype(np.int64)
        self.in_boundary += in_boundary.astype(np.int64)
        self.src.append(src)
        self.dst.append(dst)
        self.weight.append(weight)
        self.rows += rows
        self.weight_sum += weight_sum

    def add(self, pre, post, weight):
        self.merge(self.split(pre, post, weight))

    def finish(self):
        n = len(self.ids)
        src, dst, weight = (np.concatenate(parts) for parts in (self.src, self.dst, self.weight))
        key = src.astype(np.int64) * n + dst
        order = np.argsort(key, kind="stable")
        key, weight = key[order], weight[order]
        if np.any(key[1:] == key[:-1]):
            raise ValueError("duplicate node dyad in segment table")
        indptr = np.zeros(n + 1, dtype=np.int64)
        np.cumsum(np.bincount(key // n, minlength=n), out=indptr[1:])
        indices = (key % n).astype(np.int32)
        internal_out = np.bincount(key // n, weight, minlength=n).astype(np.int64)
        internal_in = np.bincount(indices, weight, minlength=n).astype(np.int64)
        if not (np.array_equal(internal_out + self.out_boundary, self.out_total)
                and np.array_equal(internal_in + self.in_boundary, self.in_total)):
            raise ValueError("node/boundary weight conservation failed")
        return indptr, indices, weight


def dyad_keys(indptr, indices, n):
    return np.repeat(np.arange(n, dtype=np.int64), np.diff(indptr)) * n + indices


def read_prebuilt(directory):
    raw = np.fromfile(directory / "graph.bin", dtype=np.uint8)
    if raw[:8].tobytes() != b"CHKCSR01":
        raise ValueError("unexpected CSR magic")
    version, n, e, _ = np.frombuffer(raw[8:24], dtype=np.uint32)
    n, e, offset = int(n), int(e), 24
    indptr = np.frombuffer(raw, np.uint64, n + 1, offset).astype(np.int64)
    offset += 8 * (n + 1)
    sources = np.frombuffer(raw, np.uint32, e, offset)
    synapses = np.frombuffer(raw, np.uint32, e, offset + 4 * e)
    signs = np.frombuffer(raw, np.int8, e, offset + 8 * e)
    if offset + 9 * e != len(raw) or indptr[-1] != e or version != 1:
        raise ValueError("CSR layout does not match its header")
    node_ids = np.loadtxt(directory / "node_ids.txt", dtype=np.int64)
    return node_ids, indptr, sources, synapses, signs


def compare_prebuilt(name, ids, keys, weight, superclass):
    node_ids, indptr, sources, synapses, signs = read_prebuilt(PREBUILT[name])
    position, found = locate(node_ids, ids)
    n, m = len(ids), len(node_ids)
    subset = np.zeros(n, dtype=bool)
    subset[position[found]] = True
    expected_scope = superclass >= 0 if name == "neurons166k" else np.ones(n, dtype=bool)
    target = np.repeat(np.arange(m), np.diff(indptr))
    theirs = position[sources].astype(np.int64) * n + position[target]
    order = np.argsort(theirs)
    theirs, synapses_sorted = theirs[order], synapses[order]
    mine = subset[keys // n] & subset[keys % n]
    same_keys = np.array_equal(theirs, keys[mine])
    high, low = np.full(m, -128, dtype=np.int8), np.full(m, 127, dtype=np.int8)
    np.maximum.at(high, sources, signs)
    np.minimum.at(low, sources, signs)
    return {"nodes": m, "all_nodes_found": bool(found.all()),
            "node_scope_matches_rule": bool(np.array_equal(subset, expected_scope)),
            "edges": len(sources), "dyads_equal": bool(same_keys),
            "synapses_equal": bool(same_keys and np.array_equal(synapses_sorted, weight[mine])),
            "sources_with_mixed_sign": int(np.count_nonzero((high >= low) & (high != low))),
            "sign_edge_counts": {str(s): int(c) for s, c in zip(*np.unique(signs, return_counts=True))}}


def compare_traced(ids, keys, weight):
    import pyarrow as pa
    import pyarrow.ipc as ipc
    path = FLAT_DIR / TRACED
    manifest = json.loads((FLAT_DIR / "manifest.json").read_text(encoding="utf-8"))
    entry = next(f for f in manifest["files"] if f["name"] == TRACED)
    md5 = base64.b64encode(digest(path, "md5").digest()).decode()
    with pa.memory_map(str(path), "r") as source:
        table = ipc.open_file(source).read_all()
    pre, post, w = (table[c].to_numpy() for c in ("body_pre", "body_post", "weight"))
    n = len(ids)
    ip, kp = locate(pre, ids)
    iq, kq = locate(post, ids)
    both = kp & kq
    wanted = ip[both].astype(np.int64) * n + iq[both]
    order = np.argsort(wanted)
    wanted, w = wanted[order], w[both][order]
    at = np.searchsorted(keys, wanted)
    present = at < len(keys)
    present[present] &= keys[at[present]] == wanted[present]
    return {"file": TRACED, "bytes": path.stat().st_size, "server_md5_matches": md5 == entry["md5Base64"],
            "rows": len(pre), "rows_with_both_endpoints_in_nodes": int(both.sum()),
            "rows_found_in_cache": int(present.sum()),
            "weights_equal_where_found": bool(np.array_equal(weight[at[present]], w[present])),
            "cache_dyads_not_in_traced_table": int(len(keys) - present.sum())}


def compare_whole_structure(ids, superclass, superclass_labels, indptr, indices, weight, out_total, in_total):
    with np.load(ANALYSIS_DIR / "whole-structure-v1.npz") as cache:
        census_ids, codes = cache["annotation_ids"], cache["category_codes"]
        labels = cache["category_labels"].tolist()
        out_weight, in_weight = cache["out_weight"], cache["in_weight"]
    keep = codes != labels.index(GLIA)
    if not np.array_equal(census_ids[keep], ids):
        return {"node_ids_equal": False}
    node_category = np.array([labels.index(superclass_labels[c]) if c >= 0 else labels.index(UNCLASSIFIED)
                              for c in superclass])
    k, n = len(labels), len(ids)
    src = np.repeat(np.arange(n), np.diff(indptr))
    by_category = np.bincount(src * k + node_category[indices], weight, minlength=n * k).reshape(n, k)
    node_columns = [labels.index(label) for label in labels if label not in (GLIA, UNKNOWN)]
    return {"node_ids_equal": True,
            "category_codes_equal": bool(np.array_equal(node_category, codes[keep])),
            "out_totals_equal": bool(np.array_equal(out_total, out_weight[keep].sum(axis=1))),
            "in_totals_equal": bool(np.array_equal(in_total, in_weight[keep].sum(axis=1))),
            "node_to_node_by_target_category_equal": bool(np.array_equal(
                by_category[:, node_columns].astype(np.int64), out_weight[keep][:, node_columns]))}


def build(args):
    import pyarrow as pa
    import pyarrow.ipc as ipc
    for path in (args.cache, args.result):
        if path.exists():
            raise FileExistsError("outputs already exist; do not overwrite research evidence")
    started, timing = time.perf_counter(), {}

    def mark(name, since):
        timing[name] = round(time.perf_counter() - since, 3)
        print(f"{name}: {timing[name]} s", flush=True)
        return time.perf_counter()

    t = time.perf_counter()
    lock = json.loads((SOURCE_DIR / "source.lock.json").read_text(encoding="utf-8"))
    sources = {}
    for name in ("annotations.feather", "edges.feather"):
        path = SOURCE_DIR / name
        actual = digest(path).hexdigest()
        if path.stat().st_size != lock[name]["bytes"] or actual != lock[name]["sha256"]:
            raise ValueError(f"source lock mismatch: {name}")
        sources[name] = {**lock[name], "path": str(path), "verified_sha256": actual,
                         "mtime_ns": path.stat().st_mtime_ns}
    t = mark("source_lock", t)
    with pa.memory_map(str(SOURCE_DIR / "annotations.feather"), "r") as source:
        table = ipc.open_file(source).read_all()
    ids, superclass, superclass_labels, type_code, type_labels = node_scope(
        table["bodyId"].to_numpy(), table["status"].to_pylist(),
        table["superclass"].to_pylist(), table["type"].to_pylist())
    t = mark("annotations", t)
    collector = EdgeCollector(ids)
    with pa.memory_map(str(SOURCE_DIR / "edges.feather"), "r") as source:
        reader = ipc.open_file(source)
        batches = reader.num_record_batches

        def work(chunk):
            if any(chunk[c].null_count for c in ("body_pre", "body_post", "weight")):
                raise ValueError("NULL edge field")
            return collector.split(*(chunk[c].to_numpy() for c in ("body_pre", "body_post", "weight")))
        # Batches are read on this thread (zero-copy); workers only compute.
        chunks = (pa.Table.from_batches([reader.get_batch(i) for i in
                                         range(start, min(start + args.batches_per_chunk, batches))])
                  for start in range(0, batches, args.batches_per_chunk))
        with ThreadPoolExecutor(args.workers) as pool:
            for part in pool.map(work, chunks):
                collector.merge(part)
    t = mark("stream_edges", t)
    indptr, indices, weight = collector.finish()
    t = mark("csr", t)
    keys = dyad_keys(indptr, indices, len(ids))
    checks = {"whole_structure": compare_whole_structure(ids, superclass, superclass_labels, indptr, indices,
                                                         weight, collector.out_total, collector.in_total)}
    t = mark("check_whole_structure", t)
    for name in PREBUILT:
        checks[f"prebuilt_{name}"] = compare_prebuilt(name, ids, keys, weight, superclass)
        t = mark(f"check_prebuilt_{name}", t)
    checks["official_traced_only"] = compare_traced(ids, keys, weight)
    t = mark("check_traced_only", t)
    for name, info in sources.items():
        if Path(info["path"]).stat().st_mtime_ns != info["mtime_ns"]:
            raise ValueError(f"input changed while reading: {name}")
    args.cache.parent.mkdir(parents=True, exist_ok=True)
    with args.cache.open("xb") as stream:
        np.savez(stream, node_ids=ids, indptr=indptr, indices=indices, weight=weight,
                 out_total=collector.out_total, in_total=collector.in_total,
                 out_boundary=collector.out_boundary, in_boundary=collector.in_boundary,
                 superclass=superclass, superclass_labels=np.asarray(superclass_labels),
                 type_code=type_code, type_labels=np.asarray(type_labels))
    t = mark("save", t)
    failed = [f"{group}.{field}" for group, values in checks.items() for field, value in values.items()
              if value is False]
    result = {"schema": "malecns-neuron-graph-v1", "status": "FAIL" if failed else "PASS", "failed_checks": failed,
              "scope": {"nodes": len(ids), "node_dyads": len(indices), "node_weight": int(weight.sum(dtype=np.int64)),
                        "segment_rows": collector.rows, "segment_weight": collector.weight_sum,
                        "self_dyads": int(np.count_nonzero(np.repeat(np.arange(len(ids)), np.diff(indptr)) == indices)),
                        "out_boundary_weight": int(collector.out_boundary.sum()),
                        "in_boundary_weight": int(collector.in_boundary.sum()),
                        "superclass_assigned_nodes": int(np.count_nonzero(superclass >= 0))},
              "checks": checks, "sources": sources,
              "cache": {"path": str(args.cache.resolve()), "bytes": args.cache.stat().st_size,
                        "sha256": digest(args.cache).hexdigest()},
              "source_code_sha256": digest(__file__).hexdigest(), "argv": sys.argv,
              "software": {"executable": sys.executable, "python": platform.python_version(),
                           "numpy": np.__version__, "pyarrow": pa.__version__},
              "timing_seconds": timing, "elapsed_seconds": round(time.perf_counter() - started, 3),
              "interpretation": "Annotated non-Glia bodies as nodes, synapse contact counts as dyad weights, all other segment contact kept as per-node boundary totals. Structural counts from one animal; not activity, transmitter sign, delay, learning or a biological metric."}
    args.result.parent.mkdir(parents=True, exist_ok=True)
    with args.result.open("x", encoding="utf-8") as stream:
        json.dump(result, stream, indent=2, ensure_ascii=True, allow_nan=False)
        stream.write("\n")
    print(f"NEURON_GRAPH_{result['status']} nodes={len(ids)} dyads={len(indices)} "
          f"elapsed={result['elapsed_seconds']} s failed={failed}", flush=True)
    if failed:
        raise SystemExit(1)


def load(result_path, verify_hash=True):
    """Return the cached graph as a dict of arrays after checking the recorded identity."""
    result = json.loads(Path(result_path).read_text(encoding="utf-8"))
    if result.get("status") != "PASS":
        raise ValueError("neuron graph cache did not pass its cross-checks")
    path = Path(result["cache"]["path"])
    if path.stat().st_size != result["cache"]["bytes"]:
        raise ValueError("neuron graph cache size changed")
    if verify_hash and digest(path).hexdigest() != result["cache"]["sha256"]:
        raise ValueError("neuron graph cache hash changed")
    with np.load(path) as cache:
        graph = {name: cache[name] for name in cache.files}
    graph["superclass_labels"] = graph["superclass_labels"].tolist()
    graph["type_labels"] = graph["type_labels"].tolist()
    return graph


def check(args):
    started = time.perf_counter()
    graph = load(args.result)
    n, indptr = len(graph["node_ids"]), graph["indptr"]
    if indptr[-1] != len(graph["indices"]) or not np.array_equal(
            np.bincount(np.repeat(np.arange(n), np.diff(indptr)), graph["weight"], minlength=n).astype(np.int64)
            + graph["out_boundary"], graph["out_total"]):
        raise ValueError("cached CSR fails weight conservation")
    print(f"NEURON_GRAPH_OK nodes={n} dyads={len(graph['indices'])} "
          f"load_and_verify={time.perf_counter() - started:.2f} s", flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    make = commands.add_parser("build")
    make.add_argument("--cache", type=Path, default=ANALYSIS_DIR / "neuron-graph-v1/neuron_graph.npz")
    make.add_argument("--result", type=Path, default=Path(__file__).with_name("neuron_graph_result.json"))
    make.add_argument("--batches-per-chunk", type=int, default=32)
    make.add_argument("--workers", type=int, default=min(8, os.cpu_count() or 1))
    verify = commands.add_parser("check")
    verify.add_argument("--result", type=Path, default=Path(__file__).with_name("neuron_graph_result.json"))
    args = parser.parse_args()
    build(args) if args.command == "build" else check(args)


if __name__ == "__main__":
    main()
