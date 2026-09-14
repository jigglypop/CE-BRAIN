"""Bounded, read-only census of the MaleCNS v1.0 raw weight table."""

from __future__ import annotations

import argparse
import json
import time

import numpy as np
import pyarrow as pa
import pyarrow.ipc as ipc


def load_reference_ids(annotation_path: str, curated_path: str):
    with pa.memory_map(annotation_path, "r") as source:
        annotations = ipc.open_file(source).read_all()
    annotation_ids = np.sort(
        annotations["bodyId"].combine_chunks().to_numpy(zero_copy_only=False)
    )
    curated_ids = np.sort(np.loadtxt(curated_path, dtype=np.int64))
    return annotation_ids, curated_ids


def membership(values: np.ndarray, reference: np.ndarray):
    slots = np.searchsorted(reference, values)
    valid = slots < reference.size
    matched = np.zeros(values.size, dtype=bool)
    matched[valid] = reference[slots[valid]] == values[valid]
    return matched, slots


def mark_bits(bits: np.ndarray, values: np.ndarray) -> None:
    byte_index = np.right_shift(values, 3).astype(np.int64, copy=False)
    masks = np.left_shift(np.uint8(1), np.bitwise_and(values, 7).astype(np.uint8))
    np.bitwise_or.at(bits, byte_index, masks)


def popcount(bits: np.ndarray, other: np.ndarray | None = None) -> int:
    lut = np.unpackbits(np.arange(256, dtype=np.uint8)[:, None], axis=1).sum(axis=1)
    total = 0
    step = 16 * 1024 * 1024
    for start in range(0, bits.size, step):
        block = bits[start : start + step]
        if other is not None:
            block = np.bitwise_or(block, other[start : start + step])
        total += int(lut[block].sum(dtype=np.uint64))
    return total


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--edges", required=True)
    parser.add_argument("--annotations", required=True)
    parser.add_argument("--curated-ids", required=True)
    parser.add_argument("--max-bitset-mib", type=int, default=512)
    args = parser.parse_args()

    started = time.perf_counter()
    annotation_ids, curated_ids = load_reference_ids(args.annotations, args.curated_ids)
    annotation_seen = {
        "pre": np.zeros(annotation_ids.size, dtype=bool),
        "post": np.zeros(annotation_ids.size, dtype=bool),
    }
    curated_seen = {
        "pre": np.zeros(curated_ids.size, dtype=bool),
        "post": np.zeros(curated_ids.size, dtype=bool),
    }
    totals = {
        "rows": 0,
        "weight_sum": 0,
        "nonpositive_weight_rows": 0,
        "self_loop_rows": 0,
        "body_pre_nulls": 0,
        "body_post_nulls": 0,
        "weight_nulls": 0,
        "pre_annotation_rows": 0,
        "post_annotation_rows": 0,
        "pre_curated_rows": 0,
        "post_curated_rows": 0,
    }
    min_id = None
    max_id = None
    batches = 0

    with pa.memory_map(args.edges, "r") as source:
        reader = ipc.open_file(source)
        batches = reader.num_record_batches
        for batch_index in range(batches):
            batch = reader.get_batch(batch_index)
            pre_col = batch.column(batch.schema.get_field_index("body_pre"))
            post_col = batch.column(batch.schema.get_field_index("body_post"))
            weight_col = batch.column(batch.schema.get_field_index("weight"))
            totals["body_pre_nulls"] += pre_col.null_count
            totals["body_post_nulls"] += post_col.null_count
            totals["weight_nulls"] += weight_col.null_count
            pre = pre_col.to_numpy(zero_copy_only=False)
            post = post_col.to_numpy(zero_copy_only=False)
            weight = weight_col.to_numpy(zero_copy_only=False)
            totals["rows"] += batch.num_rows
            totals["weight_sum"] += int(weight.sum(dtype=np.int64))
            totals["nonpositive_weight_rows"] += int(np.count_nonzero(weight <= 0))
            totals["self_loop_rows"] += int(np.count_nonzero(pre == post))
            local_min = min(int(pre.min()), int(post.min()))
            local_max = max(int(pre.max()), int(post.max()))
            min_id = local_min if min_id is None else min(min_id, local_min)
            max_id = local_max if max_id is None else max(max_id, local_max)

            for values, side in ((pre, "pre"), (post, "post")):
                matched, slots = membership(values, annotation_ids)
                totals[f"{side}_annotation_rows"] += int(matched.sum())
                annotation_seen[side][slots[matched]] = True
                matched, slots = membership(values, curated_ids)
                totals[f"{side}_curated_rows"] += int(matched.sum())
                curated_seen[side][slots[matched]] = True

    bytes_per_bitmap = (int(max_id) + 8) // 8
    total_bitset_bytes = 2 * bytes_per_bitmap
    limit = args.max_bitset_mib * 1024 * 1024
    if total_bitset_bytes > limit:
        raise RuntimeError(
            f"exact distinct needs {total_bitset_bytes / 2**20:.1f} MiB, "
            f"over limit {args.max_bitset_mib} MiB"
        )

    pre_bits = np.zeros(bytes_per_bitmap, dtype=np.uint8)
    post_bits = np.zeros(bytes_per_bitmap, dtype=np.uint8)
    with pa.memory_map(args.edges, "r") as source:
        reader = ipc.open_file(source)
        for batch_index in range(reader.num_record_batches):
            batch = reader.get_batch(batch_index)
            pre = batch.column(batch.schema.get_field_index("body_pre")).to_numpy(
                zero_copy_only=False
            )
            post = batch.column(batch.schema.get_field_index("body_post")).to_numpy(
                zero_copy_only=False
            )
            mark_bits(pre_bits, pre)
            mark_bits(post_bits, post)

    result = {
        "edges": args.edges,
        "record_batches": batches,
        **totals,
        "endpoint_id_min": min_id,
        "endpoint_id_max": max_id,
        "distinct_pre_ids": popcount(pre_bits),
        "distinct_post_ids": popcount(post_bits),
        "distinct_union_ids": popcount(pre_bits, post_bits),
        "annotation_reference_ids": int(annotation_ids.size),
        "annotation_ids_seen_as_pre": int(annotation_seen["pre"].sum()),
        "annotation_ids_seen_as_post": int(annotation_seen["post"].sum()),
        "annotation_ids_seen_as_endpoint": int(
            np.count_nonzero(annotation_seen["pre"] | annotation_seen["post"])
        ),
        "annotation_ids_not_seen_as_endpoint": int(
            np.count_nonzero(~(annotation_seen["pre"] | annotation_seen["post"]))
        ),
        "curated_reference_ids": int(curated_ids.size),
        "curated_ids_seen_as_pre": int(curated_seen["pre"].sum()),
        "curated_ids_seen_as_post": int(curated_seen["post"].sum()),
        "curated_ids_seen_as_endpoint": int(
            np.count_nonzero(curated_seen["pre"] | curated_seen["post"])
        ),
        "curated_ids_not_seen_as_endpoint": int(
            np.count_nonzero(~(curated_seen["pre"] | curated_seen["post"]))
        ),
        "bitset_mib": total_bitset_bytes / 2**20,
        "elapsed_seconds": time.perf_counter() - started,
    }
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
