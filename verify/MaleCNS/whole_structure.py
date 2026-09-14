"""Full-row MaleCNS category flow and structural-walk closure diagnostics.

The walk is a model made from contact counts, not measured neural dynamics.
Unknown segments stay in a separate boundary category; no edge is filtered.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import sys
import time
from pathlib import Path

import numpy as np


GLIA = "ANNOTATED_GLIA"
UNCLASSIFIED = "ANNOTATED_UNCLASSIFIED"
UNKNOWN = "UNANNOTATED_SEGMENT"


def digest(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def annotation_partition(ids, statuses, superclasses):
    ids = np.asarray(ids)
    if ids.ndim != 1 or ids.dtype.kind not in "iu" or np.any(ids < 0):
        raise ValueError("annotation IDs must be a nonnegative integer vector")
    if not len(ids) or len(ids) != len(statuses) or len(ids) != len(superclasses):
        raise ValueError("annotation columns have incompatible or empty lengths")
    order = np.argsort(ids)
    ids = ids[order]
    if np.any(ids[1:] == ids[:-1]):
        raise ValueError("duplicate annotation ID")
    names = []
    for index in order:
        status, superclass = statuses[index], superclasses[index]
        if status == "Glia":
            names.append(GLIA)
        elif superclass is None:
            names.append(UNCLASSIFIED)
        elif not isinstance(superclass, str) or not superclass.strip():
            raise ValueError("invalid superclass")
        elif superclass in (GLIA, UNCLASSIFIED, UNKNOWN):
            raise ValueError("reserved superclass label")
        else:
            names.append(superclass)
    labels = sorted(set(names) | {GLIA, UNCLASSIFIED, UNKNOWN})
    lookup = {name: index for index, name in enumerate(labels)}
    return ids, np.array([lookup[name] for name in names]), labels


def locate(values, reference):
    indices = np.searchsorted(reference, values)
    matched = indices < len(reference)
    matched[matched] &= reference[indices[matched]] == values[matched]
    return indices, matched


class CategoryAccumulator:
    def __init__(self, ids, codes, labels):
        self.ids, self.codes, self.labels = ids, codes, labels
        n, k = len(ids), len(labels)
        self.category_weight = np.zeros((k, k), dtype=np.int64)
        self.category_rows = np.zeros((k, k), dtype=np.int64)
        self.out_weight = np.zeros((n, k), dtype=np.int64)
        self.out_rows = np.zeros((n, k), dtype=np.int64)
        self.in_weight = np.zeros((n, k), dtype=np.int64)
        self.rows = self.weight = self.self_rows = self.self_weight = 0

    def add(self, pre, post, weight):
        arrays = [np.asarray(a) for a in (pre, post, weight)]
        if any(a.ndim != 1 or a.dtype.kind not in "iu" for a in arrays):
            raise ValueError("edge columns must be integer vectors without NULLs")
        pre, post, weight = arrays
        if len(pre) != len(post) or len(pre) != len(weight):
            raise ValueError("edge columns have incompatible lengths")
        if np.any(pre < 0) or np.any(post < 0) or np.any(weight <= 0):
            raise ValueError("invalid endpoint ID or nonpositive weight")
        ip, kp = locate(pre, self.ids)
        iq, kq = locate(post, self.ids)
        unknown = self.labels.index(UNKNOWN)
        cp = np.full(len(pre), unknown, dtype=np.int64)
        cq = np.full(len(post), unknown, dtype=np.int64)
        cp[kp], cq[kq] = self.codes[ip[kp]], self.codes[iq[kq]]
        np.add.at(self.category_weight, (cp, cq), weight)
        np.add.at(self.category_rows, (cp, cq), 1)
        np.add.at(self.out_weight, (ip[kp], cq[kp]), weight[kp])
        np.add.at(self.out_rows, (ip[kp], cq[kp]), 1)
        np.add.at(self.in_weight, (iq[kq], cp[kq]), weight[kq])
        self.rows += len(pre)
        self.weight += int(weight.sum(dtype=np.int64))
        self.self_rows += int(np.count_nonzero(pre == post))
        self.self_weight += int(weight[pre == post].sum(dtype=np.int64))

    def validate(self):
        if int(self.category_rows.sum()) != self.rows:
            raise ValueError("row conservation failed")
        if int(self.category_weight.sum()) != self.weight:
            raise ValueError("weight conservation failed")
        for code, label in enumerate(self.labels):
            if label == UNKNOWN:
                continue
            mask = self.codes == code
            if not np.array_equal(self.out_weight[mask].sum(axis=0), self.category_weight[code]):
                raise ValueError("annotated outgoing weight conservation failed")
            if not np.array_equal(self.in_weight[mask].sum(axis=0), self.category_weight[:, code]):
                raise ValueError("annotated incoming weight conservation failed")
            if not np.array_equal(self.out_rows[mask].sum(axis=0), self.category_rows[code]):
                raise ValueError("annotated outgoing row conservation failed")


def closure_dispersion(counts):
    """Count-weighted dispersion and its fixed-margin stub-null expectation."""
    counts = np.asarray(counts)
    if counts.ndim != 2 or counts.dtype.kind not in "iu" or np.any(counts < 0):
        raise ValueError("counts must be a nonnegative integer matrix")
    degrees = counts.sum(axis=1, dtype=np.int64)
    active = degrees > 0
    c, d = counts[active], degrees[active]
    m, total = len(d), int(d.sum())
    result = {"sources": len(counts), "positive_sources": m,
              "zero_sources": int(np.count_nonzero(~active)), "total_stubs": total}
    if not total:
        return {**result, "observed": None, "null_expectation": None,
                "ratio": None, "weighted_tv": None, "unweighted_tv_quantiles": None}
    p = c.sum(axis=0, dtype=np.int64) / total
    q = c / d[:, None]
    residual = q - p
    observed = float(np.sum(d * np.sum(residual * residual, axis=1)) / total)
    expectation = ((m - 1) / (total - 1) * (1 - float(p @ p))) if total > 1 and m > 1 else None
    tv = np.abs(residual).sum(axis=1) / 2
    return {**result, "observed": observed, "null_expectation": expectation,
            "ratio": observed / expectation if expectation is not None and expectation > 0 else None,
            "weighted_tv": float(d @ tv / total),
            "unweighted_tv_quantiles": np.quantile(tv, [0, .25, .5, .75, .95, 1]).tolist()}


def closure_witness(counts, ids, target_labels, minimum_degree=100):
    degrees = counts.sum(axis=1)
    keep = degrees >= minimum_degree
    c, d, ids = counts[keep], degrees[keep], ids[keep]
    if len(ids) < 2:
        return None
    q = c / d[:, None]
    coordinate = int(np.argmax(np.ptp(q, axis=0)))
    low, high = int(np.argmin(q[:, coordinate])), int(np.argmax(q[:, coordinate]))
    return {"minimum_degree": minimum_degree, "eligible_sources": len(ids),
            "selected_target": target_labels[coordinate],
            "target_probability_gap": float(q[high, coordinate] - q[low, coordinate]),
            "total_variation": float(np.abs(q[high] - q[low]).sum() / 2),
            "low": {"body_id": int(ids[low]), "degree": int(d[low]), "counts": c[low].tolist()},
            "high": {"body_id": int(ids[high]), "degree": int(d[high]), "counts": c[high].tolist()}}


def summarize(acc):
    groups = []
    known_columns = np.array([label not in (GLIA, UNCLASSIFIED, UNKNOWN) for label in acc.labels])
    for code, label in enumerate(acc.labels):
        mask = acc.codes == code
        if label == UNKNOWN:
            continue
        counts = acc.out_weight[mask]
        groups.append({"category": label,
                       "full_weight": closure_dispersion(counts),
                       "full_connection_rows": closure_dispersion(acc.out_rows[mask]),
                       "assigned_neuron_targets_conditional": closure_dispersion(counts[:, known_columns]),
                       "full_weight_witness": closure_witness(counts, acc.ids[mask], acc.labels)})
    flows = []
    for i, a in enumerate(acc.labels):
        for j, b in enumerate(acc.labels):
            flows.append({"source": a, "target": b, "weight": int(acc.category_weight[i, j]),
                          "connection_rows": int(acc.category_rows[i, j])})
    off = acc.category_weight.copy()
    np.fill_diagonal(off, 0)
    off_total = int(off.sum())
    return {"category_order": acc.labels,
            "annotation_category_counts": np.bincount(acc.codes, minlength=len(acc.labels)).tolist(),
            "rows": acc.rows, "weight_sum": acc.weight,
            "self_loop_rows": acc.self_rows, "self_loop_weight": acc.self_weight,
            "category_flows": flows,
            "off_category_weight": off_total,
            "off_category_balanced_weight_fraction": float(np.minimum(off, off.T).sum() / off_total) if off_total else None,
            "closure": groups}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-dir", type=Path, required=True)
    parser.add_argument("--arrays", type=Path, required=True)
    parser.add_argument("--result", type=Path, required=True)
    args = parser.parse_args()
    if args.arrays.exists() or args.result.exists():
        raise FileExistsError("outputs already exist; do not overwrite research evidence")
    import pyarrow as pa
    import pyarrow.ipc as ipc

    started = time.perf_counter()
    lock = json.loads((args.source_dir / "source.lock.json").read_text(encoding="utf-8"))
    provenance, stamps = {}, {}
    for name in ("annotations.feather", "edges.feather"):
        path = args.source_dir / name
        stat = path.stat()
        actual = digest(path)
        if stat.st_size != lock[name]["bytes"] or actual != lock[name]["sha256"]:
            raise ValueError(f"source lock mismatch: {name}")
        stamps[name] = (stat.st_size, stat.st_mtime_ns)
        provenance[name] = {**lock[name], "path": str(path.resolve()), "verified_sha256": actual}
    with pa.memory_map(str(args.source_dir / "annotations.feather"), "r") as source:
        table = ipc.open_file(source).read_all()
    if table["bodyId"].null_count:
        raise ValueError("NULL annotation ID")
    ids, codes, labels = annotation_partition(
        table["bodyId"].combine_chunks().to_numpy(), table["status"].to_pylist(),
        table["superclass"].to_pylist())
    acc = CategoryAccumulator(ids, codes, labels)
    with pa.memory_map(str(args.source_dir / "edges.feather"), "r") as source:
        reader = ipc.open_file(source)
        for i in range(reader.num_record_batches):
            batch = reader.get_batch(i)
            columns = [batch.column(batch.schema.get_field_index(name))
                       for name in ("body_pre", "body_post", "weight")]
            if any(column.null_count for column in columns):
                raise ValueError("NULL edge field")
            acc.add(*(column.to_numpy(zero_copy_only=False) for column in columns))
            if (i + 1) % 500 == 0:
                print(f"batches {i + 1}/{reader.num_record_batches}; rows {acc.rows}", flush=True)
    acc.validate()
    for name, stamp in stamps.items():
        stat = (args.source_dir / name).stat()
        if (stat.st_size, stat.st_mtime_ns) != stamp:
            raise ValueError(f"input changed while reading: {name}")
    result = summarize(acc)
    args.arrays.parent.mkdir(parents=True, exist_ok=True)
    args.result.parent.mkdir(parents=True, exist_ok=True)
    with args.arrays.open("xb") as stream:
        np.savez_compressed(stream, annotation_ids=ids, category_codes=codes,
                            category_labels=np.asarray(labels),
                            category_weight=acc.category_weight, category_rows=acc.category_rows,
                            out_weight=acc.out_weight, out_rows=acc.out_rows, in_weight=acc.in_weight)
    result.update({"schema": "malecns-whole-structure-v1", "sources": provenance,
                   "source_code_sha256": digest(__file__), "argv": sys.argv,
                   "software": {"executable": sys.executable, "python": platform.python_version(),
                                "numpy": np.__version__, "pyarrow": pa.__version__},
                   "arrays": {"path": str(args.arrays.resolve()), "sha256": digest(args.arrays)},
                   "elapsed_seconds": time.perf_counter() - started,
                   "interpretation": "Exploratory structural counts and a supplied row-normalized walk; not neural activity, biological memory, p-values, or independent-animal evidence."})
    with args.result.open("x", encoding="utf-8") as stream:
        json.dump(result, stream, indent=2, ensure_ascii=True, allow_nan=False)
        stream.write("\n")
    print(f"WHOLE_STRUCTURE_COMPLETE rows={acc.rows} weight={acc.weight}", flush=True)


if __name__ == "__main__":
    main()
