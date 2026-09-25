"""Equivalence check of the fast path against the sealed step 56-63 code, same seed and parameters:
  schedule   models.schedule vs step 58 schedule: same arrays and the same generator state afterwards
  simulate   rate trajectories of the four models (max |difference|; the old loops use numpy's W @ r)
  spikes     analysis.spikes_and_save vs step 58 spikes_and_save on the same rates and generator state: same arrays
  measures   step 62 measures (re-emergence, inside-up holding) on the old vs the new session: must be identical
  structure  analysis.structure vs step 56 analyse (C, ring index) on the same file: must be identical
  step 57    holding_gap.analyse on the old vs the new session: must be identical

env/py fastcore/check_equivalence.py     (writes fastcore/equivalence.json)
"""
from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import time
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
LOOP = HERE.parent
sys.path.insert(0, str(HERE))

import analysis as an  # noqa: E402
import models as fm  # noqa: E402


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


st = _load("stp_trace", LOOP / "step61_stp_trace/stp_trace.py")
up = _load("upstream_pull", LOOP / "step62_upstream_pull/upstream_pull.py")
wu = _load("wandering_upstream", LOOP / "step63_wandering_upstream/wandering_upstream.py")
se, s56, s57 = fm.se, up.s56, up.s57
dumps = lambda d: json.dumps(d, sort_keys=True, default=float)


def session(tag, sched_fn, sim_fn, spikes_fn, seed, gain, work):
    rng = np.random.default_rng(seed)
    t0 = time.time()
    sched = sched_fn(rng)
    t1 = time.time()
    rates = sim_fn(rng, sched)
    t2 = time.time()
    path = work / f"{tag}.npz"
    spikes_fn(rates, sched, rng, gain, path)
    t3 = time.time()
    m = up.measures(path, np.random.default_rng(7))
    t4 = time.time()
    return sched, rates, path, m, {"schedule_s": round(t1 - t0, 2), "sim_s": round(t2 - t1, 2), "spikes_s": round(t3 - t2, 2),
                                   "measures_s": round(t4 - t3, 2)}


def compare(tag, old_sim, new_sim, seed, gain, work, full=False):
    so, ro, po, mo, to = session(f"{tag}_old", se.schedule, old_sim, se.spikes_and_save, seed, gain, work)
    sn, rn, pn, mn, tn = session(f"{tag}_new", fm.schedule, new_sim, an.spikes_and_save, seed, gain, work)
    d = np.abs(ro.astype(float) - rn.astype(float))
    res = {"model": tag, "seed": seed, "old_s": to, "new_s": tn,
           "schedule_same": bool(np.array_equal(so[0], sn[0], equal_nan=True) and np.array_equal(so[1], sn[1], equal_nan=True)
                                 and so[2] == sn[2]),
           "max_abs_rate_diff": float(d.max()), "measures_same": dumps(mo) == dumps(mn),
           "measures": {k: v for k, v in mn.items() if k != "re_by_d"}}
    if full:
        t0 = time.time()
        a56 = s56.analyse(po, np.random.default_rng(8))
        t1 = time.time()
        stc = an.structure(po)
        t2 = time.time()
        res["structure_same"] = all(stc[k]["C"] == a56["states"][k]["C"] and stc[k]["ring_index"] == a56["states"][k]["ring_index"]
                                    for k in a56["states"])
        res["structure"] = stc
        res["structure_s"] = {"step56_analyse": round(t1 - t0, 2), "fast": round(t2 - t1, 2)}
        g_old, g_new = s57.analyse(po, np.random.default_rng(9)), s57.analyse(pn, np.random.default_rng(9))
        g_old.pop("session", None), g_new.pop("session", None)
        res["step57_same"] = dumps(g_old) == dumps(g_new)
        r1, r2 = np.random.default_rng(99), np.random.default_rng(99)          # spike path on identical rates and state
        se.spikes_and_save(rn, sn, r1, gain, work / "sp_old.npz")
        an.spikes_and_save(rn, sn, r2, gain, work / "sp_new.npz")
        za, zb = np.load(work / "sp_old.npz"), np.load(work / "sp_new.npz")
        res["spike_arrays_same"] = sorted(za.files) == sorted(zb.files) and all(np.array_equal(za[k], zb[k]) for k in za.files)
        res["spike_rng_state_same"] = r1.bit_generator.state == r2.bit_generator.state
        za.close(), zb.close()
        (work / "sp_old.npz").unlink(), (work / "sp_new.npz").unlink()
    po.unlink(), pn.unlink()
    print(dumps({k: v for k, v in res.items() if k not in ("measures", "structure")}), flush=True)
    return res


def main():
    s58 = json.loads((LOOP / "step58_sleep_equation/results.json").read_text(encoding="utf-8"))
    s61 = json.loads((LOOP / "step61_stp_trace/results.json").read_text(encoding="utf-8"))
    sigma, gain = s58["sigma"], s58["gain"]
    work = Path(tempfile.mkdtemp())
    rows = [
        compare("step58_base", lambda rng, sc: se.simulate(sigma, se.C_DOWN_PRIMARY, rng, sc),
                lambda rng, sc: fm.sim_base(sigma, se.C_DOWN_PRIMARY, rng, sc), 581, gain, work, full=True),
        compare("step61_stp", lambda rng, sc: st.simulate(s61["sigma"], rng, sc, s61["g_E"], gain),
                lambda rng, sc: fm.sim_stp(s61["sigma"], rng, sc, s61["g_E"], gain, st.E, st.R), 611, gain, work),
        compare("step62_pull", lambda rng, sc: up.simulate(sigma, rng, sc, 0.4, 90.0),
                lambda rng, sc: fm.sim_pull(sigma, rng, sc, 0.4, 90.0, up.D_W), 621, gain, work),
        compare("step63_wander", lambda rng, sc: wu.simulate(sigma, rng, sc, 0.4, 4.0),
                lambda rng, sc: fm.sim_wander(sigma, rng, sc, 0.4, 4.0, up.D_W), 631, gain, work),
    ]
    flags = [k for k in ("schedule_same", "measures_same", "structure_same", "step57_same", "spike_arrays_same", "spike_rng_state_same")]
    ok = all(r.get(k, True) for r in rows for k in flags)
    (HERE / "equivalence.json").write_text(json.dumps({"all_same": ok, "rows": rows}, indent=1, default=float), encoding="utf-8")
    print("ALL SAME" if ok else "DIFFERENCE FOUND", flush=True)


if __name__ == "__main__":
    main()
