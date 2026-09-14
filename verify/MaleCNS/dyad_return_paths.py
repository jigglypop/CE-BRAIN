"""Exact raw dyads, reciprocal edges and ID-joined two-edge walks.

Every source segment is indexed from the raw graph. Terminal post-only IDs
are not removed from canonical edges; they cannot mediate a two-edge walk.
Self edges remain in the cache and are excluded only from walk diagnostics.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import platform
from pathlib import Path
import sys
import time

import numpy as np

U32_MAX = 2**32 - 1
SPECIAL = ("ANNOTATED_GLIA", "ANNOTATED_UNCLASSIFIED", "UNANNOTATED_SEGMENT")


def packed_keys(pre, post):
    pre, post = np.asarray(pre), np.asarray(post)
    if pre.ndim != 1 or pre.shape != post.shape or pre.dtype.kind not in "iu" or post.dtype.kind not in "iu":
        raise ValueError("endpoints must be equally shaped integer vectors")
    if np.any(pre < 0) or np.any(post < 0) or np.any(pre > U32_MAX) or np.any(post > U32_MAX):
        raise ValueError("endpoint outside uint32")
    return (pre.astype(np.uint64) << np.uint64(32)) | post.astype(np.uint64)


def reverse_keys(keys):
    return ((keys & np.uint64(U32_MAX)) << np.uint64(32)) | (keys >> np.uint64(32))


def canonicalize(keys, weights):
    if not len(keys) or keys.ndim != 1 or weights.ndim != 1 or keys.dtype != np.uint64 or weights.dtype.kind not in "iu" or len(keys) != len(weights):
        raise ValueError("invalid nonempty key and weight arrays")
    # These bounds make the uint64 sum overflow-free before its tighter total check.
    if len(weights) > U32_MAX or np.any(weights <= 0) or np.any(weights > U32_MAX) or int(weights.sum(dtype=np.uint64)) > U32_MAX:
        raise ValueError("positive weights with total <= uint32 max are required")
    original_rows = len(keys)
    already_sorted = not bool(np.any(keys[1:] < keys[:-1]))
    if not already_sorted:
        order = np.argsort(keys, kind="stable")
        keys, weights = keys[order], weights[order]
        del order
    repeated = keys[1:] == keys[:-1]
    duplicate_extra = int(repeated.sum())
    duplicate_groups = int(np.count_nonzero(repeated & np.r_[True, ~repeated[:-1]])) if len(repeated) else 0
    if duplicate_extra:
        starts = np.r_[0, np.flatnonzero(~repeated) + 1]
        weights = np.add.reduceat(weights, starts, dtype=np.uint64).astype(np.uint32)
        keys = keys[starts]
    else:
        weights = weights.astype(np.uint32, copy=False)
    return keys, weights, {"raw_rows": original_rows, "unique_dyads": len(keys),
                           "duplicate_extra_rows": duplicate_extra, "duplicate_keys": duplicate_groups,
                           "original_sorted": already_sorted}


def lookup(values, reference):
    indices = np.searchsorted(reference, values)
    matched = indices < len(reference)
    matched[matched] &= reference[indices[matched]] == values[matched]
    return indices, matched


def category_codes(values, annotation_ids, annotation_codes, unknown):
    indices, matched = lookup(values, annotation_ids)
    codes = np.full(len(values), unknown, dtype=np.int64)
    codes[matched] = annotation_codes[indices[matched]]
    return codes


def source_index(keys):
    pre = (keys >> np.uint64(32)).astype(np.uint32)
    offsets = np.r_[0, np.flatnonzero(pre[1:] != pre[:-1]) + 1, len(keys)]
    return pre[offsets[:-1]], offsets


def analyze(keys, weights, annotation_ids, annotation_codes, labels, *, chunk_size=1_000_000, max_working_gib=8):
    source_ids, offsets = source_index(keys)
    n, k = len(source_ids), len(labels)
    estimate = len(keys) * 16 + n * (k * 12 + 80) + chunk_size * 180
    if estimate > max_working_gib * 2**30:
        raise MemoryError(f"estimated analysis working bytes {estimate} exceed budget")
    unknown = labels.index("UNANNOTATED_SEGMENT")
    source_codes = category_codes(source_ids, annotation_ids, annotation_codes, unknown)
    known_columns = np.array([label not in SPECIAL for label in labels])
    incoming = np.zeros((n, k), dtype=np.uint32)
    outgoing = np.zeros((n, k), dtype=np.uint32)
    out_weight_all = np.zeros((n, k), dtype=np.uint32)
    incoming_example = np.full(n, np.iinfo(np.uint64).max, dtype=np.uint64)
    category_edges = np.zeros((k, k), dtype=np.uint64)
    category_weights = np.zeros((k, k), dtype=np.uint64)
    reciprocal_edges = np.zeros((k, k), dtype=np.uint64)
    reciprocal_weights = np.zeros((k, k), dtype=np.uint64)
    balanced_weights = np.zeros((k, k), dtype=np.uint64)
    counters = dict(self_dyads=0, self_weight=0, terminal_target_dyads=0, terminal_target_weight=0)
    for start in range(0, len(keys), chunk_size):
        block = keys[start:start + chunk_size]
        w = weights[start:start + chunk_size]
        pre = (block >> np.uint64(32)).astype(np.uint32)
        post = (block & np.uint64(U32_MAX)).astype(np.uint32)
        ip, kp = lookup(pre, source_ids)
        if not kp.all():
            raise ValueError("source compression lost an ID")
        iq, target_active = lookup(post, source_ids)
        cp = source_codes[ip]
        cq = category_codes(post, annotation_ids, annotation_codes, unknown)
        nonself = pre != post
        counters["self_dyads"] += int(np.count_nonzero(~nonself))
        counters["self_weight"] += int(w[~nonself].sum(dtype=np.uint64))
        counters["terminal_target_dyads"] += int(np.count_nonzero(~target_active))
        counters["terminal_target_weight"] += int(w[~target_active].sum(dtype=np.uint64))
        np.add.at(out_weight_all, (ip, cq), w)
        np.add.at(outgoing, (ip[nonself], cq[nonself]), 1)
        inbound = nonself & target_active
        np.add.at(incoming, (iq[inbound], cp[inbound]), 1)
        witness_input = inbound & known_columns[cp]
        np.minimum.at(incoming_example, iq[witness_input], pre[witness_input].astype(np.uint64))
        np.add.at(category_edges, (cp[nonself], cq[nonself]), 1)
        np.add.at(category_weights, (cp[nonself], cq[nonself]), w[nonself])
        reverse = reverse_keys(block)
        positions, matched = lookup(reverse, keys)
        matched &= nonself
        np.add.at(reciprocal_edges, (cp[matched], cq[matched]), 1)
        np.add.at(reciprocal_weights, (cp[matched], cq[matched]), w[matched])
        np.add.at(balanced_weights, (cp[matched], cq[matched]), np.minimum(w[matched], weights[positions[matched]]))
        if start // chunk_size % 20 == 0:
            print(f"exact dyads {min(start + chunk_size, len(keys))}/{len(keys)}", flush=True)
    full_out_weight = np.add.reduceat(weights, offsets[:-1], dtype=np.uint64)
    if not np.array_equal(out_weight_all.sum(axis=1, dtype=np.uint64), full_out_weight):
        raise ValueError("source outgoing weight conservation failed")
    if int(category_edges.sum()) + counters["self_dyads"] != len(keys):
        raise ValueError("unique dyad conservation failed")
    if int(category_weights.sum()) + counters["self_weight"] != int(weights.sum(dtype=np.uint64)):
        raise ValueError("weight conservation failed")
    if not np.array_equal(reciprocal_edges, reciprocal_edges.T) or not np.array_equal(balanced_weights, balanced_weights.T):
        raise ValueError("reverse-key reciprocity symmetry failed")
    if int(incoming.sum(dtype=np.uint64)) != len(keys) - counters["self_dyads"] - counters["terminal_target_dyads"]:
        raise ValueError("active-target incoming conservation failed")
    incoming_known = incoming[:, known_columns].sum(axis=1, dtype=np.uint64)
    outgoing_known = outgoing[:, known_columns].sum(axis=1, dtype=np.uint64)
    path_counts = incoming_known * outgoing_known
    same_category = (incoming[:, known_columns].astype(np.uint64) * outgoing[:, known_columns]).sum(axis=1, dtype=np.uint64)
    middle_groups = {"assigned_neuron": known_columns[source_codes],
                     **{label: source_codes == labels.index(label) for label in SPECIAL}}
    paths = []
    for name, middle_mask in middle_groups.items():
        middle_categories = known_columns if name == "assigned_neuron" else np.array([label == name for label in labels])
        returns = int(reciprocal_edges[np.ix_(known_columns, middle_categories)].sum())
        total = int(path_counts[middle_mask].sum(dtype=np.uint64))
        same = int(same_category[middle_mask].sum(dtype=np.uint64))
        if not (0 <= returns <= same <= total):
            raise ValueError("closed walk inclusion failed")
        eligible = np.flatnonzero(middle_mask & (path_counts > 0))
        top = eligible[np.argsort(path_counts[eligible], kind="stable")[-5:][::-1]]
        witnesses = []
        for index in top:
            v, u = int(source_ids[index]), int(incoming_example[index])
            lo, hi = int(offsets[index]), int(offsets[index + 1])
            candidates = (keys[lo:hi] & np.uint64(U32_MAX)).astype(np.uint32)
            candidate_codes = category_codes(candidates, annotation_ids, annotation_codes, unknown)
            valid = known_columns[candidate_codes] & (candidates != v)
            options = candidates[valid]
            distinct = options[options != u]
            end = int(distinct[0] if len(distinct) else options[0])
            query = packed_keys(np.array([u, v]), np.array([v, end]))
            positions, found = lookup(query, keys)
            if not found.all():
                raise ValueError("path witness not found in raw canonical dyads")
            witnesses.append({"start_id": u, "middle_id": v, "end_id": end,
                              "edge_weights": weights[positions].tolist(),
                              "backtrack": u == end, "incoming_assigned_edges": int(incoming_known[index]),
                              "outgoing_assigned_edges": int(outgoing_known[index]),
                              "two_edge_walks_at_middle": int(path_counts[index])})
        paths.append({"middle_group": name, "source_index_ids": int(middle_mask.sum()),
                      "mediating_ids": len(eligible), "two_edge_walks_assigned_to_assigned": total,
                      "closed_two_edge_walks_same_start_id": returns,
                      "three_distinct_id_paths": total - returns,
                      "same_start_end_superclass_walks": same, "witnesses": witnesses})
    all_nonself = int(category_edges.sum())
    all_weight = int(category_weights.sum())
    known_block = np.ix_(known_columns, known_columns)
    result = {"source_ids": n, "category_order": labels, **counters,
              "nonself_unique_dyads": all_nonself,
              "reciprocal_directed_dyads": int(reciprocal_edges.sum()),
              "reciprocal_unordered_pairs": int(reciprocal_edges.sum()) // 2,
              "reciprocal_directed_fraction": float(reciprocal_edges.sum() / all_nonself) if all_nonself else None,
              "weight_on_reciprocal_edges_fraction": float(reciprocal_weights.sum() / all_weight) if all_weight else None,
              "balanced_reciprocal_weight_fraction": float(balanced_weights.sum() / all_weight) if all_weight else None,
              "assigned_to_assigned_nonself_dyads": int(category_edges[known_block].sum()),
              "assigned_to_assigned_reciprocal_dyads": int(reciprocal_edges[known_block].sum()),
              "category_nonself_dyads": category_edges.tolist(),
              "category_nonself_weights": category_weights.tolist(),
              "category_reciprocal_dyads": reciprocal_edges.tolist(),
              "category_reciprocal_weights": reciprocal_weights.tolist(),
              "category_balanced_weights": balanced_weights.tolist(), "two_edge_paths": paths}
    arrays = dict(source_ids=source_ids, source_offsets=offsets, source_category_codes=source_codes,
                  category_labels=np.asarray(labels), source_out_weight=full_out_weight,
                  out_category_weight_all=out_weight_all, outgoing_nonself_category_dyads=outgoing,
                  incoming_nonself_category_dyads=incoming)
    return result, arrays


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--whole-result", type=Path, required=True)
    parser.add_argument("--cache-dir", type=Path, required=True)
    parser.add_argument("--result", type=Path, required=True)
    parser.add_argument("--max-working-gib", type=float, default=8)
    args = parser.parse_args()
    if args.result.exists() or args.cache_dir.exists():
        raise FileExistsError("preserve existing research outputs")
    import pyarrow as pa
    import pyarrow.ipc as ipc
    started = time.perf_counter()
    helper_path = Path(__file__).with_name("whole_structure.py")
    spec = importlib.util.spec_from_file_location("whole_structure", helper_path)
    helper = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(helper)
    whole = json.loads(args.whole_result.read_text(encoding="utf-8"))
    if helper.digest(helper_path) != whole["source_code_sha256"]:
        raise ValueError("annotation partition implementation changed")
    stamps = {}
    for name in ("annotations.feather", "edges.feather"):
        path = Path(whole["sources"][name]["path"])
        stat = path.stat()
        if helper.digest(path) != whole["sources"][name]["verified_sha256"]:
            raise ValueError(f"input changed: {name}")
        stamps[name] = (stat.st_size, stat.st_mtime_ns)
    rows = whole["rows"]
    if rows * 48 > args.max_working_gib * 2**30:
        raise MemoryError("conservative sort working-set estimate exceeds budget")
    keys = np.empty(rows, dtype=np.uint64)
    weights = np.empty(rows, dtype=np.uint32)
    position = 0
    with pa.memory_map(whole["sources"]["edges.feather"]["path"], "r") as stream:
        reader = ipc.open_file(stream)
        names = ("body_pre", "body_post", "weight")
        if any(name not in reader.schema.names or reader.schema.field(name).type != pa.int64() for name in names):
            raise ValueError("expected int64 source schema")
        for i in range(reader.num_record_batches):
            batch = reader.get_batch(i)
            columns = [batch.column(batch.schema.get_field_index(name)) for name in names]
            if any(column.null_count for column in columns):
                raise ValueError("NULL edge field")
            pre, post, weight = (column.to_numpy(zero_copy_only=False) for column in columns)
            end = position + len(pre)
            if end > rows or np.any(weight <= 0) or np.any(weight > U32_MAX):
                raise ValueError("row count or weight outside input contract")
            keys[position:end] = packed_keys(pre, post)
            weights[position:end] = weight
            position = end
    if position != rows or int(weights.sum(dtype=np.uint64)) != whole["weight_sum"]:
        raise ValueError("raw row/weight totals differ from previous whole-input result")
    print(f"sorting {rows} raw dyads", flush=True)
    keys, weights, duplicate_info = canonicalize(keys, weights)
    with pa.memory_map(whole["sources"]["annotations.feather"]["path"], "r") as stream:
        table = ipc.open_file(stream).read_all()
    ids, codes, labels = helper.annotation_partition(table["bodyId"].combine_chunks().to_numpy(),
                                                    table["status"].to_pylist(), table["superclass"].to_pylist())
    result, arrays = analyze(keys, weights, ids, codes, labels, max_working_gib=args.max_working_gib)
    for name, before in stamps.items():
        stat = Path(whole["sources"][name]["path"]).stat()
        if (stat.st_size, stat.st_mtime_ns) != before:
            raise ValueError("input changed during analysis")
    args.cache_dir.mkdir(parents=True)
    artifacts = {}
    for name, array in (("dyad_keys.npy", keys), ("dyad_weights.npy", weights)):
        path = args.cache_dir / name
        with path.open("xb") as stream:
            np.save(stream, array, allow_pickle=False)
        artifacts[name] = {"path": str(path.resolve()), "bytes": path.stat().st_size, "sha256": helper.digest(path)}
    path = args.cache_dir / "source_categories.npz"
    with path.open("xb") as stream:
        np.savez_compressed(stream, **arrays)
    artifacts[path.name] = {"path": str(path.resolve()), "bytes": path.stat().st_size, "sha256": helper.digest(path)}
    result.update({"schema": "malecns-raw-dyad-return-v1", **duplicate_info,
                   "whole_result": str(args.whole_result.resolve()), "whole_result_sha256": helper.digest(args.whole_result),
                   "sources": whole["sources"], "source_code_sha256": helper.digest(__file__),
                   "annotation_partition_code_sha256": helper.digest(helper_path), "artifacts": artifacts,
                   "software": {"python": platform.python_version(), "executable": sys.executable,
                                "numpy": np.__version__, "pyarrow": pa.__version__},
                   "argv": sys.argv, "elapsed_seconds": time.perf_counter() - started,
                   "interpretation": "Unique directed raw-segment dyads and actual ID-joined walks. Self-loops excluded from reciprocity/path diagnostics only. Two-edge walks are distinct (start,middle,end) triples, not unique endpoint pairs, synaptic chains, activity, or causal memory. Assigned-neuron endpoint scope uses all 27 superclass categories; all raw segments remain in canonical arrays."})
    with args.result.open("x", encoding="utf-8") as stream:
        json.dump(result, stream, indent=2, allow_nan=False)
        stream.write("\n")
    print("RAW_DYAD_RETURN_COMPLETE", flush=True)


if __name__ == "__main__":
    main()
