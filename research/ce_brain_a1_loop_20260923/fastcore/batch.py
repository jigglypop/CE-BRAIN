"""Parallel batch runner for A1 simulation sessions.

run_specs(specs, worker="path/to/module.py:function", workers=6, mem_gb=0.75) runs one session per spec in separate
processes (Windows spawn), with BLAS / OpenMP / numba threads pinned to 1 per worker so the processes do not
oversubscribe the 6-core / 12-thread CPU. Results come back in the order of the specs; a failed spec comes back as
{"_error", "_spec"}. Each worker process loads the worker module once and re-uses the numba on-disk cache.
Memory: the worker count is lowered to what the free memory (Windows commit and physical) holds at mem_gb per worker,
and specs that fail for lack of memory are run once more with half the workers.
The worker returns a dict; the caller script must keep its own work under `if __name__ == "__main__":`.
Checked by fastcore/check_batch.py (identical to a serial run; throughput per worker count).
"""
from __future__ import annotations

import concurrent.futures as cf
import importlib
import importlib.util
import os
import sys
import time
from pathlib import Path

for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMBA_NUM_THREADS"):
    os.environ.setdefault(_v, "1")

_DIR = str(Path(__file__).resolve().parent)
_WORKERS = {}                                                       # per process: "path:fn" -> function


def free_memory_gb():
    """min(free commit, free physical) in GB on Windows (what new processes can still allocate); None elsewhere."""
    if sys.platform != "win32":
        return None
    import ctypes

    class _MS(ctypes.Structure):
        _fields_ = [("dwLength", ctypes.c_ulong), ("dwMemoryLoad", ctypes.c_ulong)] + \
                   [(f, ctypes.c_ulonglong) for f in ("TotalPhys", "AvailPhys", "TotalPageFile", "AvailPageFile",
                                                      "TotalVirtual", "AvailVirtual", "AvailExtendedVirtual")]
    m = _MS()
    m.dwLength = ctypes.sizeof(_MS)
    if not ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(m)):
        return None
    return min(m.AvailPageFile, m.AvailPhys) / 2 ** 30


def _resolve(worker):
    if worker not in _WORKERS:
        path, fn = worker.rsplit(":", 1)                            # rsplit: Windows paths carry a drive colon
        p = Path(path)
        if p.suffix == ".py":
            spec = importlib.util.spec_from_file_location(p.stem, p)
            mod = importlib.util.module_from_spec(spec)
            sys.modules[p.stem] = mod
            spec.loader.exec_module(mod)
        else:
            mod = importlib.import_module(path)
        _WORKERS[worker] = getattr(mod, fn)
    return _WORKERS[worker]


def _call(worker, spec):
    t0 = time.time()
    out = _resolve(worker)(spec)
    out["_seconds"] = round(time.time() - t0, 1)
    return out


def _pool(call, worker, specs, idx, workers, results, log, t0):
    with cf.ProcessPoolExecutor(max_workers=workers) as ex:
        futs = {ex.submit(call, worker, specs[i]): i for i in idx}
        for n_done, fu in enumerate(cf.as_completed(futs), 1):
            i = futs[fu]
            try:
                results[i] = fu.result()
            except Exception as e:                                  # keep going; record the failure with its spec
                results[i] = {"_error": repr(e), "_spec": specs[i]}
            log(f"[batch] {n_done}/{len(idx)} done, {time.time() - t0:.0f} s elapsed")


def run_specs(specs, worker, workers=6, mem_gb=0.75, log=print):
    if _DIR not in sys.path:                                        # the children inherit sys.path and import "batch"
        sys.path.insert(0, _DIR)
    call = importlib.import_module("batch")._call                   # picklable by reference however this file was loaded
    free = free_memory_gb()
    if free is not None and int(0.8 * free / mem_gb) < workers:
        log(f"[batch] {free:.1f} GB free -> {max(1, int(0.8 * free / mem_gb))} workers instead of {workers}")
        workers = max(1, int(0.8 * free / mem_gb))
    workers = max(1, min(workers, len(specs)))
    results, t0 = [None] * len(specs), time.time()
    _pool(call, worker, specs, range(len(specs)), workers, results, log, t0)
    again = [i for i, r in enumerate(results) if "_error" in r and ("MemoryError" in r["_error"] or "BrokenProcessPool" in r["_error"])]
    if again:                                                       # out of memory: once more with half the workers
        log(f"[batch] {len(again)} specs ran out of memory; retrying with {max(1, workers // 2)} workers")
        _pool(call, worker, specs, again, max(1, workers // 2), results, log, t0)
    return results
