"""Batch runner check on the full fast session (schedule, simulate, spikes, step 62 measures, step 56 structure):
the same seeds run one after another in this process and in parallel worker processes must give identical results
(sha256 of the rates and the measures); throughput is measured for several worker counts.

env/py fastcore/check_batch.py     (writes fastcore/batch_check.json)
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import sys
import tempfile
import time
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
LOOP = HERE.parent
sys.path.insert(0, str(HERE))

import analysis as an  # noqa: E402
import batch  # noqa: E402
import models as fm  # noqa: E402

_spec = importlib.util.spec_from_file_location("upstream_pull", LOOP / "step62_upstream_pull/upstream_pull.py")
up = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(up)
S58 = json.loads((LOOP / "step58_sleep_equation/results.json").read_text(encoding="utf-8"))
N_SERIAL, N_PAR, WORKER_COUNTS = 6, 24, (3, 6, 9)


def peak_commit_gb():
    """Peak committed memory of this process (Windows), GB."""
    import ctypes
    from ctypes import wintypes

    class _PMC(ctypes.Structure):
        _fields_ = [("cb", wintypes.DWORD), ("PageFaultCount", wintypes.DWORD)] + \
                   [(f, ctypes.c_size_t) for f in ("PeakWorkingSetSize", "WorkingSetSize", "QuotaPeakPagedPoolUsage",
                                                   "QuotaPagedPoolUsage", "QuotaPeakNonPagedPoolUsage", "QuotaNonPagedPoolUsage",
                                                   "PagefileUsage", "PeakPagefileUsage")]
    c = _PMC()
    c.cb = ctypes.sizeof(_PMC)
    k32, psapi = ctypes.WinDLL("kernel32"), ctypes.WinDLL("psapi")
    k32.GetCurrentProcess.restype = wintypes.HANDLE
    psapi.GetProcessMemoryInfo.argtypes = [wintypes.HANDLE, ctypes.c_void_p, wintypes.DWORD]
    psapi.GetProcessMemoryInfo(k32.GetCurrentProcess(), ctypes.byref(c), c.cb)
    return round(c.PeakPagefileUsage / 2 ** 30, 2)


def session(spec):
    rng = np.random.default_rng(spec["seed"])
    sched = fm.schedule(rng)
    rates = fm.sim_base(S58["sigma"], fm.se.C_DOWN_PRIMARY, rng, sched)
    path = Path(tempfile.gettempdir()) / f"cb_{spec['seed']}_{os.getpid()}.npz"
    an.spikes_and_save(rates, sched, rng, S58["gain"], path)
    m = up.measures(path, np.random.default_rng(spec["seed"] + 1))
    s = an.structure(path)
    path.unlink()
    return {"seed": spec["seed"], "rates_sha256": hashlib.sha256(rates.tobytes()).hexdigest(),
            "result": json.dumps({"m": m, "s": s}, sort_keys=True, default=float), "peak_commit_gb": peak_commit_gb()}


def main():
    specs = [{"seed": 581 + i} for i in range(N_PAR)]
    session(specs[0])                                               # warm the numba cache before timing
    t0 = time.time()
    serial = [session(s) for s in specs[:N_SERIAL]]
    per_session = (time.time() - t0) / N_SERIAL
    out = {"serial_s_per_session": round(per_session, 2), "cpu": "Ryzen 5 7500F, 6 cores / 12 threads", "runs": []}
    for w in WORKER_COUNTS:
        t0 = time.time()
        par = batch.run_specs(specs, f"{HERE / 'check_batch.py'}:session", workers=w, log=lambda s: None)
        wall = time.time() - t0
        same = all(a["rates_sha256"] == b.get("rates_sha256") and a["result"] == b.get("result") for a, b in zip(serial, par))
        out["runs"].append({"workers": w, "sessions": N_PAR, "wall_s": round(wall, 1), "sessions_per_s": round(N_PAR / wall, 2),
                            "speedup_vs_serial": round(per_session * N_PAR / wall, 2), "identical_to_serial": same,
                            "errors": [p for p in par if "_error" in p]})
        print(json.dumps(out["runs"][-1]), flush=True)
    out["all_identical"] = all(r["identical_to_serial"] and not r["errors"] for r in out["runs"])
    (HERE / "batch_check.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
    print(json.dumps({k: v for k, v in out.items() if k != "runs"}), flush=True)


if __name__ == "__main__":
    main()
