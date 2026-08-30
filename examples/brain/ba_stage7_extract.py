"""BA-STAGE7 threshold-latency extractor (byte-locked re-fetch, no raw persisted).

Observable: x_thr = first time |w|>=3 in [0.010,0.120]s (contract BA_STAGE7).
Also emits odd/even interleaved half x_thr per target (declared B-1 input only).

Contract: paper/검증_원장/BA_STAGE6_지연_endpoint_계약.md. For each of the 5,920
receipt ranges: GET the locked S3 URL with Range + If-Match; require the payload
SHA-256 to equal the receipt's payload_sha256 (byte identity with the PASS_FINAL
run); decode via the frozen DISC2 core; per target site compute the energy-
median arrival time x_lat = t_lat/0.050 from the ten-trial-mean bipolar z.
Only the x_lat table and receipts are persisted.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]
OLDA = REPO / "_workspace/ce/brain-human-ccep-multisubject-precision-20260825/artifacts"
NEWA = REPO / "_workspace/ce/brain-human-ccep-multisubject-precision-retry-20260825/artifacts"
HERE = Path.cwd()
OUT = HERE / "ba-stage7-latency-endpoints.json"
RECEIPT = HERE / "ba-stage7-extract-receipt.json"

_spec = importlib.util.spec_from_file_location("core", OLDA / "disc2_ccep_core.py")
CORE = importlib.util.module_from_spec(_spec)
sys.modules["core"] = CORE
_spec.loader.exec_module(CORE)


def load_ranges():
    groups = {}
    for stage in ("d0", "d1", "d2", "d3"):
        r = json.loads((NEWA / f"{stage}-range-receipt.json").read_text(encoding="utf-8"))
        for row in r["ranges"]:
            key = (row["stage"], row["subject"], row["record_id"], row["source_id"])
            groups.setdefault(key, []).append(row)
    bad = {k: len(v) for k, v in groups.items() if len(v) != 10}
    if bad:
        raise RuntimeError(f"STAGE6_APPARATUS_STOP: trial counts {list(bad.items())[:3]}")
    return groups


def load_records():
    m = json.loads((OLDA / "metadata-source-manifest.json").read_text(encoding="utf-8"))
    return {r["record_id"]: r for r in m["recordings"]}


def load_targets():
    """(stage, subject, source_id) -> ordered target list from locked endpoints."""
    out = {}
    for stage in ("d0", "d1", "d2", "d3"):
        d = json.loads((NEWA / f"{stage}-endpoints.json").read_text(encoding="utf-8"))
        for s in d["sources"]:
            out[(stage.upper(), s["subject"], s["source_id"])] = {
                "record_id": s["record_id"],
                "targets": [{"site_id": t["site_id"], "contacts": t["contacts"],
                             "role": t["role"], "max_z": float(np.max(t["endpoint"]["z"]))}
                            for t in s["targets"]],
            }
    return out


def fetch(row):
    req = urllib.request.Request(
        row["locked_url"],
        headers={"Range": f"bytes={row['byte_start']}-{row['byte_end']}",
                 "If-Match": row["etag"]})
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                payload = resp.read()
            break
        except Exception:
            if attempt == 2:
                raise
            time.sleep(2.0 * (attempt + 1))
    if hashlib.sha256(payload).hexdigest() != row["payload_sha256"]:
        raise RuntimeError("PAYLOAD_SHA_MISMATCH")
    if len(payload) != row["expected_bytes"]:
        raise RuntimeError("PAYLOAD_SIZE_MISMATCH")
    return payload


def x_thr_from_mean(w, masks):
    """First |w|>=3 crossing in the frozen post window; None if never crossed."""
    window = np.zeros_like(masks["baseline"])
    for m in masks["post"]:
        window |= m
    tau = masks["times_s"][window]
    ww = np.abs(w[window])
    hits = np.flatnonzero(ww >= 3.0)
    if hits.size == 0:
        return None
    return float(tau[hits[0]]) / 0.050


def process_source(key, rows, meta, record):
    stage, subject, record_id, source_id = key
    channels = record["channels"]
    fs = record["authoritative_sampling_frequency_hz"]
    nch = int(record["header"]["number_of_channels"])
    scount = int(record["sample_count"])
    rows = sorted(rows, key=lambda r: r["event_index"])
    targets = meta["targets"]

    # channel indices/resolutions/units per target (skip targets with missing channels)
    tinfo = []
    for t in targets:
        chs = [channels.get(c) for c in t["contacts"]]
        if any(c is None or not isinstance(c.get("index"), int) for c in chs):
            tinfo.append(None)
            continue
        tinfo.append({
            "idx": [int(c["index"]) for c in chs],
            "res": [float(c["resolution"]) for c in chs],
            "units": [c["units"] for c in chs],
        })

    specs = []
    payloads = []
    with ThreadPoolExecutor(max_workers=5) as pool:
        futures = []
        for row in rows:
            spec = CORE.make_range_spec(fs, nch, int(row["anchor_sample_zero_based"]), scount)
            if spec.byte_start != row["byte_start"] or spec.byte_end != row["byte_end"]:
                raise RuntimeError("STAGE6_APPARATUS_STOP: spec/receipt byte mismatch")
            specs.append(spec)
            futures.append(pool.submit(fetch, row))
        payloads = [f.result() for f in futures]

    masks = CORE.time_masks(specs[0])
    baseline = masks["baseline"]
    out = []
    for t, info in zip(targets, tinfo):
        if info is None:
            out.append({"site_id": t["site_id"], "role": t["role"], "x_lat": None,
                        "max_z": t["max_z"], "reason": "CHANNEL_ABSENT"})
            continue
        trials = []
        for spec, payload in zip(specs, payloads):
            sel = CORE.decode_selected_channels(payload, spec, info["idx"],
                                                info["res"], info["units"])
            trials.append(sel[:, 0] - sel[:, 1])
        trials = np.stack(trials)
        sigma = CORE._robust_baseline_scale(trials[:, baseline])
        w = trials.mean(axis=0) / sigma
        x = x_thr_from_mean(w, masks)
        # odd/even interleaved halves (declared B-1 input; not gated here)
        w_even = trials[0::2].mean(axis=0) / sigma
        w_odd = trials[1::2].mean(axis=0) / sigma
        out.append({"site_id": t["site_id"], "role": t["role"],
                    "x_lat": x,
                    "x_half_even": x_thr_from_mean(w_even, masks),
                    "x_half_odd": x_thr_from_mean(w_odd, masks),
                    "max_z": t["max_z"],
                    "reason": None if x is not None else "NO_THRESHOLD_CROSSING"})
    return out


def main():
    for p in (OUT, RECEIPT):
        if p.exists():
            raise FileExistsError(p)
    t0 = time.time()
    groups = load_ranges()
    records = load_records()
    targets = load_targets()
    print(json.dumps({"event": "PLAN", "sources": len(groups)}), flush=True)
    table = {}
    abstains = []
    done = 0
    for key, rows in sorted(groups.items()):
        stage, subject, record_id, source_id = key
        meta = targets[(stage, subject, source_id)]
        try:
            table[f"{stage}|{subject}|{source_id}"] = process_source(
                key, rows, meta, records[record_id])
        except Exception as exc:
            abstains.append({"key": list(key), "reason": str(exc)[:200]})
        done += 1
        if done % 25 == 0:
            print(json.dumps({"event": "PROGRESS", "done": done,
                              "abstains": len(abstains),
                              "elapsed_s": round(time.time() - t0)}), flush=True)
    OUT.write_text(json.dumps(table, sort_keys=True), encoding="utf-8")
    finite = sum(1 for src in table.values() for t in src if t["x_lat"] is not None)
    total = sum(len(src) for src in table.values())
    receipt = {
        "schema": "ba-stage7-extract-v1",
        "contract": "paper/검증_원장/BA_STAGE7_문턱지연_계약.md",
        "sources_processed": len(table),
        "sources_abstained": abstains,
        "targets_total": total,
        "targets_finite_x_lat": finite,
        "raw_payload_persisted": False,
        "endpoints_sha256": hashlib.sha256(OUT.read_bytes()).hexdigest(),
        "runtime_seconds": round(time.time() - t0, 1),
    }
    RECEIPT.write_text(json.dumps(receipt, indent=1, sort_keys=True), encoding="utf-8")
    print(json.dumps({"event": "COMPLETE", "sources": len(table),
                      "abstained": len(abstains), "finite_targets": finite,
                      "total_targets": total}), flush=True)


if __name__ == "__main__":
    main()
