"""Endpoint-blind pulse-timing probe for one ds006254 stimulation block.

Decodes ONLY the trigger/DC channels and the two stimulated contacts (the
stimulation artifact), never a receiver channel, and reports candidate pulse
times inside the block that follows a "Start Stimulation from A to B" marker.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

from tools_ds006254_annotations import parallel_range

HERE = Path(__file__).resolve().parent


def decode(payload: bytes, hdr: dict, n_records: int, names: list[str]) -> dict[str, np.ndarray]:
    spr = np.asarray(hdr["samples_per_record"])
    rec_samples = int(spr.sum())
    arr = np.frombuffer(payload, dtype="<i2").reshape(n_records, rec_samples)
    offsets = np.concatenate(([0], np.cumsum(spr)))
    out = {}
    for name in names:
        i = hdr["labels"].index(name)
        dig = arr[:, offsets[i]:offsets[i + 1]].reshape(-1).astype(np.float64)
        pmin, pmax = float(hdr["phys_min"][i]), float(hdr["phys_max"][i])
        dmin, dmax = float(hdr["dig_min"][i]), float(hdr["dig_max"][i])
        out[name] = (dig - dmin) * (pmax - pmin) / (dmax - dmin) + pmin
    return out


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("path")
    parser.add_argument("--marker-index", type=int, default=0)
    parser.add_argument("--seconds", type=float, default=40.0)
    args = parser.parse_args()
    harvest = json.loads((HERE / "ds006254_annotation_harvest.json").read_text(encoding="utf-8"))
    row = harvest[args.path]
    hdr = {"samples_per_record": row["samples_per_record"], "labels": row["labels"],
           "phys_min": row["phys_min"], "phys_max": row["phys_max"],
           "dig_min": row["dig_min"], "dig_max": row["dig_max"]}
    stims = [a for a in row["annotations"] if a["text"].lower().startswith("start stimulation")]
    marker = stims[args.marker_index]
    words = marker["text"].split()
    a, b = words[3], words[5]
    dur = row["edf"]["record_duration_s"]
    fs = row["samples_per_record"][0] / dur
    first = int(np.floor(marker["onset_s"] / dur)) - 16
    n = int(np.ceil(args.seconds / dur))
    rec_bytes = 2 * sum(row["samples_per_record"])
    start = row["edf"]["header_bytes"] + first * rec_bytes
    payload = parallel_range(row["url"], start, start + n * rec_bytes - 1, row["s3"]["etag"])
    names = [x for x in row["labels"] if x.upper().startswith(("TRIG", "DC"))][:6]
    names += [x for x in (a, b) if x in row["labels"]]
    sig = decode(payload, hdr, n, names)
    t = first * dur + np.arange(n * row["samples_per_record"][0]) / fs
    sys.stdout.reconfigure(encoding="utf-8")
    print(json.dumps({"marker": marker, "contacts": [a, b], "fs": fs, "decoded": names}))
    for name, x in sig.items():
        dx = np.abs(np.diff(x))
        thr = np.median(dx) + 20 * (np.median(np.abs(dx - np.median(dx))) * 1.4826 + 1e-9)
        idx = np.flatnonzero(dx > thr)
        groups = []
        for i in idx:
            if not groups or i - groups[-1][-1] > int(0.2 * fs):
                groups.append([i])
            else:
                groups[-1].append(i)
        onsets = [t[g[0]] for g in groups]
        print(f"{name}: range=({x.min():.1f},{x.max():.1f}) n_events={len(onsets)} "
              f"first={[round(v - marker['onset_s'], 3) for v in onsets[:6]]} "
              f"ipi_median={np.median(np.diff(onsets)) if len(onsets) > 2 else None}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
