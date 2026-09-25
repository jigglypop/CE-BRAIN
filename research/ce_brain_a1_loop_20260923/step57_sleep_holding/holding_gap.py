"""A1 step 57: why does the mouse head-direction bump scatter within 0.4 s in NREM (step 56 post hoc) while the ring
structure survives? Hypothesis: holding needs continuous drive; NREM down states (silent bins) cut the drive and the
bump re-forms at a new position, while inside continuous activity it is held as in wake. (CONTRACT.md)

Noise-free persistence (split halves): HD cells split at random into halves A and B (20 splits). Per 100 ms bin,
phi_A and phi_B = population-vector angles of each half. For a set of bin pairs (t, t'):
  rho = mean[cos(phi_A(t) - phi_B(t')) + cos(phi_B(t) - phi_A(t'))] / 2  /  mean_same[cos(phi_A(s) - phi_B(s))]
With independent estimation noise in the halves, rho = E[cos(true bump displacement)] (1 = held, 0 = scattered).
Bins: active = >= 4 HD spikes with >= 2 in each half; silent = <= 1 HD spike. Home cage, opto epochs excluded.
Pair sets per state: all pairs at lag L (L = 3 bins); in NREM, gap pairs (active t, g silent bins, active t+g+1,
g = 1..3) versus matched continuous pairs (active t .. t+g+1, all bins active), pooled over g with gap-pair weights.
P2'  NREM scatters faster: rho_all(0.3 s) NREM < wake_home in >= 70 % of sessions.
P5   the drive cut resets the bump: in NREM, rho_gap < rho_continuous in >= 70 % of sessions with >= 50 gap pairs.
P6   inside continuous activity the bump is held as in wake: rho_continuous(NREM, lag 0.2 s) / rho_all(wake, 0.2 s) >= 0.8
     in >= 70 % of sessions.
Report: REM; silent-bin fraction per state; around NREM -> wake transitions the 1 s time course of the silent-bin
fraction and of rho for adjacent active pairs.

python holding_gap.py    refuses to run unless CONTRACT.md lists this code hash and the dependency hash
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
LOOP = HERE.parent
BIN, NSPLIT, SEED = 0.1, 20, 57
ACTIVE, HALF_MIN, SILENT = 4, 2, 1
MIN_GAP_PAIRS = 50


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


s56 = load("mouse_sleep_ring", LOOP / "step56_mouse_sleep_ring/mouse_sleep_ring.py")


def halves_angles(N, th, rng):
    out = []
    n = th.size
    for _ in range(NSPLIT):
        p = rng.permutation(n)
        A, B = p[: n // 2], p[n // 2:]
        cA, cB = N[A].sum(0), N[B].sum(0)
        out.append((np.angle(np.exp(1j * th[A]) @ N[A]), np.angle(np.exp(1j * th[B]) @ N[B]), cA >= HALF_MIN, cB >= HALF_MIN))
    return out


def rho(pairs_t, pairs_u, splits, same_mask):
    """Noise-free persistence for bin pairs (t, u), averaged over splits; None if too few pairs."""
    if len(pairs_t) < 20:
        return None
    num, den = [], []
    for pa, pb, va, vb in splits:
        ok = va[pairs_t] & vb[pairs_t] & va[pairs_u] & vb[pairs_u]
        s = same_mask & va & vb
        if ok.sum() < 20 or s.sum() < 20:
            continue
        t, u = pairs_t[ok], pairs_u[ok]
        num.append(np.mean((np.cos(pa[t] - pb[u]) + np.cos(pb[t] - pa[u])) / 2))
        den.append(np.mean(np.cos(pa[s] - pb[s])))
    if not num or np.mean(den) <= 0.05:
        return None
    return float(np.mean(num) / np.mean(den))


def pair_sets(mask, active, silent, seg):
    """Index arrays of bin pairs inside one state (mask) and one contiguous segment (seg)."""
    idx = np.flatnonzero(mask)
    ok = np.zeros(mask.size, bool)
    ok[idx] = True
    out = {}
    for L in (2, 3):
        t = np.flatnonzero(ok[:-L] & ok[L:] & active[:-L] & active[L:] & (seg[:-L] == seg[L:]))
        out[f"all_{L}"] = (t, t + L)
        inside = np.ones(t.size, bool)
        for k in range(1, L):
            inside &= active[t + k]
        out[f"cont_{L}"] = (t[inside], t[inside] + L)
    gt, gu, ct, cu = [], [], [], []
    for g in (1, 2, 3):
        L = g + 1
        base = np.flatnonzero(ok[:-L] & ok[L:] & active[:-L] & active[L:] & (seg[:-L] == seg[L:]))
        sil = np.ones(base.size, bool)
        act = np.ones(base.size, bool)
        for k in range(1, L):
            sil &= silent[base + k]
            act &= active[base + k]
        gt.append(base[sil]); gu.append(base[sil] + L)
        # matched continuous pairs at the same lag, subsampled to the gap-pair count of this lag
        c = base[act]
        if sil.sum() == 0:
            c = c[:0]                                                   # no gap pairs at this lag: no matched pairs either
        elif c.size > sil.sum():
            c = np.sort(np.random.default_rng(L).choice(c, size=int(sil.sum()), replace=False))
        ct.append(c); cu.append(c + L)
    out["gap"] = (np.concatenate(gt), np.concatenate(gu))
    out["gap_matched_cont"] = (np.concatenate(ct), np.concatenate(cu))
    return out


def analyse(path, rng):
    S = s56.load(path)
    hd_idx = np.flatnonzero(S["hd_flag"])
    info = {"session": path.stem, "n_hd": int(hd_idx.size)}
    if hd_idx.size < s56.MIN_HD:
        return {**info, "qualifies": False}
    th, tracked = s56.preferred(S, [S["spikes"][i] for i in hd_idx])
    T = max(float(np.max(np.concatenate([s for s in S["spikes"] if s.size]))), float(S["ss"][1].max()))
    edges = np.arange(0, T + BIN, BIN)
    centres = (edges[:-1] + edges[1:]) / 2
    N = np.array([np.histogram(S["spikes"][i], edges)[0] for i in hd_idx], dtype=float)
    state, home, opto = s56.labels(centres, S)
    tot = N.sum(0)
    active, silent = tot >= ACTIVE, tot <= SILENT
    splits = halves_angles(N, th, rng)
    masks = {"nrem": (state == "nrem") & home, "wake_home": (state == "wake") & home, "rem": (state == "rem") & home}
    if masks["nrem"].sum() * BIN < s56.MIN_NREM or tracked < s56.MIN_TRACK:
        return {**info, "qualifies": False}
    info["qualifies"] = True
    info["states"] = {}
    for k, m in masks.items():
        if m.sum() * BIN < (s56.MIN_REM if k == "rem" else 30):
            continue
        seg = np.cumsum(np.r_[1, np.diff(m.astype(int)) != 0])            # contiguous runs of the state
        ps = pair_sets(m, active, silent, seg)
        same = m & active
        entry = {"silent_fraction": float(silent[m].mean()), "active_fraction": float(active[m].mean())}
        for name, (t, u) in ps.items():
            entry[f"rho_{name}"] = rho(t, u, splits, same)
            entry[f"n_{name}"] = int(t.size)
        info["states"][k] = entry
    n = info["states"]["nrem"]
    w = info["states"].get("wake_home", {})
    info["P2p"] = None if (n.get("rho_all_3") is None or w.get("rho_all_3") is None) else bool(n["rho_all_3"] < w["rho_all_3"])
    info["P5"] = None if (n["n_gap"] < MIN_GAP_PAIRS or n.get("rho_gap") is None or n.get("rho_gap_matched_cont") is None) else bool(n["rho_gap"] < n["rho_gap_matched_cont"])
    info["P6"] = None if (n.get("rho_cont_2") is None or w.get("rho_all_2") is None or w["rho_all_2"] <= 0) else bool(n["rho_cont_2"] / w["rho_all_2"] >= 0.8)
    trs = [t0 for t0 in s56.transitions(S) if home[min(int(t0 / BIN), home.size - 1)] and not opto[min(int(t0 / BIN), opto.size - 1)]]
    if len(trs) >= 3:
        k1 = int(1.0 / BIN)
        rel = np.arange(-20, 20)
        sil_c, pairs, same = [], [[] for _ in range(40)], [[] for _ in range(40)]
        for t0 in trs:
            b0 = int(round((t0 - 20) / BIN))
            if b0 < 0 or b0 + 40 * k1 + 1 > N.shape[1]:
                continue
            sil_c.append(silent[b0:b0 + 40 * k1].reshape(40, k1).mean(1))
            for s in range(40):                                        # pool each relative second over transitions
                lo = b0 + s * k1
                t = np.arange(lo, lo + k1 - 1)
                pairs[s].append(t[active[t] & active[t + 1]])
                w = np.arange(lo, lo + k1)
                same[s].append(w[active[w]])
        if sil_c:
            rr = []
            for s in range(40):
                t = np.concatenate(pairs[s]).astype(int)
                win = np.zeros(active.size, bool)
                win[np.concatenate(same[s]).astype(int)] = True
                v = rho(t, t + 1, splits, win)
                rr.append(np.nan if v is None else v)
            info["transition"] = {"n": len(sil_c), "rel_s": rel.tolist(), "silent_fraction": np.nanmean(sil_c, 0).tolist(),
                                  "rho_adjacent": rr}
    return info


def main():
    contract = (HERE / "CONTRACT.md").read_text(encoding="utf-8")
    deps = (Path(__file__), LOOP / "step56_mouse_sleep_ring/mouse_sleep_ring.py")
    hashes = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in deps}
    missing = [k for k, h in hashes.items() if h not in contract]
    if missing:
        raise SystemExit(f"CONTRACT.md does not list hashes for {missing}: {hashes}")
    rng = np.random.default_rng(SEED)
    rows = []
    for p in sorted(s56.DATA.glob("*.npz")):
        r = analyse(p, rng)
        rows.append(r)
        brief = {k: r["states"][k] for k in r.get("states", {})}
        print(r["session"][:22], "P2'", r.get("P2p"), "P5", r.get("P5"), "P6", r.get("P6"),
              json.dumps({k: {kk: (round(vv, 3) if isinstance(vv, float) else vv) for kk, vv in v.items() if kk.startswith(("rho", "silent", "n_gap"))} for k, v in brief.items()}), flush=True)
    q = [r for r in rows if r.get("qualifies")]
    def frac(key):
        v = [r[key] for r in q if r.get(key) is not None]
        return {"n": len(v), "fraction": float(np.mean(v)) if v else None}
    def med(state, key):
        v = [r["states"][state][key] for r in q if state in r["states"] and r["states"][state].get(key) is not None]
        return float(np.median(v)) if v else None
    summary = {"n_qualifying": len(q), "P2p": frac("P2p"), "P5": frac("P5"), "P6": frac("P6"),
               "median_rho": {s: {k: med(s, k) for k in ("rho_all_2", "rho_all_3", "rho_cont_2", "rho_cont_3", "rho_gap", "rho_gap_matched_cont")}
                              for s in ("wake_home", "nrem", "rem")},
               "median_silent_fraction": {s: med(s, "silent_fraction") for s in ("wake_home", "nrem", "rem")}}
    tr = [r["transition"] for r in q if "transition" in r]
    if tr:
        summary["transition_mean"] = {"n_sessions": len(tr), "rel_s": tr[0]["rel_s"],
                                      "silent_fraction": np.nanmean([t["silent_fraction"] for t in tr], 0).tolist(),
                                      "rho_adjacent": np.nanmean([t["rho_adjacent"] for t in tr], 0).tolist()}
    ok = lambda f: f["fraction"] is not None and f["fraction"] >= 0.7
    verdict = {"P2p": "NREM_SCATTERS_FASTER" if ok(summary["P2p"]) else "NOT_SHOWN",
               "P5": "DRIVE_CUT_RESETS_BUMP" if ok(summary["P5"]) else "NOT_SHOWN",
               "P6": "HELD_INSIDE_CONTINUOUS_ACTIVITY" if ok(summary["P6"]) else "NOT_SHOWN"}
    result = {"schema": "ce-a1-step57-sleep-holding", "hashes": hashes, "summary": summary, "verdict": verdict, "sessions": rows}
    with (HERE / "results.json").open("x", encoding="utf-8") as stream:
        json.dump(result, stream, indent=1, default=float)
    print("verdict", json.dumps(verdict), json.dumps({k: v for k, v in summary.items() if k != "transition_mean"}, default=float))


if __name__ == "__main__":
    main()
