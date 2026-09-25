"""Extract the parts of DANDI 000939 needed by step 56 with HTTP range reads (no full-file download):
units (spike times, is_head_direction, is_excitatory, is_fast_spiking), intervals (sleep_states, epochs),
processing/behavior/CompassDirection. One compressed npz per session under data/external/dandi_000939_extract/.
Provenance (asset id, path, version, bytes read) is written to manifest.json for the data ledger.

python extract_000939.py
"""
from __future__ import annotations

import concurrent.futures as cf
import hashlib
import json
import os
import urllib.request
from pathlib import Path

import h5py
import numpy as np
import remfile

DS = "000939"
OUT = Path(__file__).resolve().parents[3] / "data/external/dandi_000939_extract"


def assets():
    v = json.load(urllib.request.urlopen(f"https://api.dandiarchive.org/api/dandisets/{DS}/"))["most_recent_published_version"]["version"]
    out, url = [], f"https://api.dandiarchive.org/api/dandisets/{DS}/versions/{v}/assets/?page_size=400"
    while url:
        d = json.load(urllib.request.urlopen(url))
        out += d["results"]
        url = d.get("next")
    return v, sorted([a for a in out if a["path"].endswith(".nwb")], key=lambda a: a["path"])


def dec(x):
    return x.decode() if isinstance(x, bytes) else str(x)


def provenance(a, version, dest):
    return {"path": a["path"], "asset_id": a["asset_id"], "version": version, "nwb_bytes": a["size"], "npz": dest.name,
            "npz_bytes": dest.stat().st_size, "npz_sha256": hashlib.sha256(dest.read_bytes()).hexdigest()}


def extract(a, version):
    name = Path(a["path"]).stem
    dest = OUT / f"{name}.npz"
    if dest.exists():
        return {**provenance(a, version, dest), "status": "cached"}
    rf = remfile.File(f"https://api.dandiarchive.org/api/assets/{a['asset_id']}/download/")
    with h5py.File(rf, "r") as f:
        u = f["units"]
        arrays = {"spike_times": u["spike_times"][:], "spike_times_index": u["spike_times_index"][:],
                  "unit_id": u["id"][:]}
        for col in ("is_head_direction", "is_excitatory", "is_fast_spiking"):
            arrays[col] = u[col][:] if col in u else np.zeros(arrays["unit_id"].size, bool)
        ss = f["intervals/sleep_states"]
        arrays.update(ss_start=ss["start_time"][:], ss_stop=ss["stop_time"][:], ss_state=np.array([dec(x) for x in ss["state"][:]]))
        ep = f["intervals/epochs"]
        tags = [dec(x) for x in ep["tags"][:]]
        arrays.update(ep_start=ep["start_time"][:], ep_stop=ep["stop_time"][:], ep_tag=np.array(tags))
        cd = f["processing/behavior/CompassDirection"]
        s = cd[list(cd.keys())[0]]
        arrays.update(hd_t=s["timestamps"][:], hd=s["data"][:])
    part = OUT / f"{name}.partial.npz"                                   # atomic: an interrupted write leaves no .npz
    np.savez_compressed(part, **arrays)
    os.replace(part, dest)
    return {**provenance(a, version, dest), "n_units": int(arrays["unit_id"].size),
            "n_hd": int(np.sum(arrays["is_head_direction"])), "status": "extracted"}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    version, nwb = assets()
    rows = []
    with cf.ThreadPoolExecutor(max_workers=int(os.environ.get("EXTRACT_WORKERS", "12"))) as ex:
        futs = {ex.submit(extract, a, version): a for a in nwb}
        for fu in cf.as_completed(futs):
            try:
                r = fu.result()
            except Exception as e:                                   # record and continue
                r = {"path": futs[fu]["path"], "status": f"error: {e!r}"}
            rows.append(r)
            print(json.dumps(r), flush=True)
    (OUT / "manifest.json").write_text(json.dumps({"dandiset": DS, "version": version, "sessions": sorted(rows, key=lambda r: r["path"])}, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
