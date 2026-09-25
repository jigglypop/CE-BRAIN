"""A1 step 56: in the mouse head-direction system (postsubiculum, DANDI 000939, 31 mice), is the ring alive during
sleep, and what turns on first at waking: the gain (rates) or the ring structure? (CONTRACT.md)

Data: extract_000939.py output (spike times, author HD/excitatory/fast-spiking flags, sleep_states, epochs, head
direction at 100 Hz). Opto epochs are excluded everywhere.
Preferred direction theta_i: 60-bin (6 deg) tuning curve from head-direction samples outside opto epochs.
Qualifying session: >= 10 HD cells, >= 300 s NREM in the home cage, >= 300 s tracked head direction.

Metrics on 200 ms bins of HD-cell spike counts n_i:
  ring coherence C = sum_b(|S_b|^2 - sum_i n_ib^2) / sum_b((sum_i n_ib)^2 - sum_i n_ib^2),  S_b = sum_i n_ib e^{i theta_i}
    = mean cos(theta_i - theta_j) over co-occurring spikes of different cells (unbiased by rate).
  ring index = Pearson r over cell pairs between the spike-count correlation and cos(theta_i - theta_j).
  null: preferred directions permuted across cells (1000 permutations), 95th percentile.
P1  ring alive in NREM: C_nrem and ring index_nrem both above their null 95th percentile, in >= 80 % of sessions.
P3  at NREM -> wake transitions (home cage; NREM >= 60 s followed within 1 s by wake >= 30 s; >= 3 per session):
    change index (post - pre)/(|post| + |pre|), pre = [-20, -5) s, post = (5, 20] s, on the transition average;
    HD population rate index > ring coherence index in >= 70 % of sessions with >= 3 transitions.
Report: REM (sessions with >= 60 s REM), home-cage wake, exploration; bump angular speed per state (200 ms bins with
>= 5 HD spikes, consecutive bins); half-rise latency of HD, fast-spiking and non-HD excitatory rates at waking.

python mouse_sleep_ring.py    refuses to run unless CONTRACT.md lists this code hash
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
DATA = HERE.parents[2] / "data/external/dandi_000939_extract"
BIN, NPERM, SEED = 0.2, 1000, 56
MIN_HD, MIN_NREM, MIN_TRACK, MIN_REM = 10, 300.0, 300.0, 60.0
PRE, POST, WIN = (-20.0, -5.0), (5.0, 20.0), 20.0


def load(p):
    z = np.load(p, allow_pickle=False)
    idx = z["spike_times_index"].astype(int)
    st = z["spike_times"]
    spikes = np.split(st, idx[:-1])
    return {"spikes": spikes, "hd_flag": z["is_head_direction"].astype(bool), "exc": z["is_excitatory"].astype(bool),
            "fs": z["is_fast_spiking"].astype(bool), "ss": (z["ss_start"], z["ss_stop"], np.char.lower(z["ss_state"].astype(str))),
            "ep": (z["ep_start"], z["ep_stop"], z["ep_tag"]), "hd_t": z["hd_t"], "hd": z["hd"]}


def in_any(t, starts, stops):
    i = np.searchsorted(starts, t, side="right") - 1
    ok = i >= 0
    ok[ok] = t[ok] < stops[i[ok]]
    return ok


def labels(centres, S):
    es, ee, et = S["ep"]
    o = np.argsort(es)
    es, ee, et = es[o], ee[o], et[o]
    opto = np.array(["opto" in str(x).lower() for x in et])
    home = np.array(["home" in str(x).lower() for x in et])
    in_opto = in_any(centres, es[opto], ee[opto]) if opto.any() else np.zeros(centres.size, bool)
    in_home = in_any(centres, es[home], ee[home]) if home.any() else np.zeros(centres.size, bool)
    ss, se, sl = S["ss"]
    o = np.argsort(ss)
    ss, se, sl = ss[o], se[o], sl[o]
    state = np.full(centres.size, "", dtype=object)
    for lab in ("wake", "nrem", "rem"):
        m = sl == lab
        if m.any():
            state[in_any(centres, ss[m], se[m])] = lab
    return state, in_home & ~in_opto, in_opto


def preferred(S, hd_units):
    t, h = S["hd_t"], S["hd"].astype(float)
    if np.nanmax(h) > 7:
        h = np.radians(h)
    es, ee, et = S["ep"]
    opto = np.array(["opto" in str(x).lower() for x in et])
    keep = np.isfinite(h) & ~(in_any(t, np.sort(es[opto]), ee[opto][np.argsort(es[opto])]) if opto.any() else np.zeros(t.size, bool))
    t, h = t[keep], np.mod(h[keep], 2 * np.pi)
    dt = float(np.median(np.diff(t)))
    edges = np.linspace(0, 2 * np.pi, 61)
    occ = np.histogram(h, edges)[0] * dt
    centres = (edges[:-1] + edges[1:]) / 2
    th = []
    for sp in hd_units:
        j = np.searchsorted(t, sp)
        j = np.clip(j, 1, t.size - 1)
        j = np.where(np.abs(t[j - 1] - sp) < np.abs(t[j] - sp), j - 1, j)
        ok = np.abs(t[j] - sp) < 0.05
        rate = np.histogram(h[j[ok]], edges)[0] / np.maximum(occ, 1e-9)
        th.append(float(np.angle(np.sum(rate * np.exp(1j * centres)))))
    return np.array(th), float(t.size * dt)


def coherence(N, th):
    Sb = np.exp(1j * th) @ N
    n = N.sum(0)
    sq = (N ** 2).sum(0)
    den = float(np.sum(n ** 2 - sq))
    return float(np.sum(np.abs(Sb) ** 2 - sq) / den) if den > 0 else float("nan")


def ring_index(N, th):
    keep = N.std(1) > 0
    if keep.sum() < 3:
        return float("nan"), None
    R = np.corrcoef(N[keep])
    iu = np.triu_indices(keep.sum(), 1)
    c = np.cos(th[keep][:, None] - th[keep][None, :])[iu]
    return float(np.corrcoef(R[iu], c)[0, 1]), (R[iu], keep, iu)


def state_metrics(N, th, rng):
    C = coherence(N, th)
    ri, aux = ring_index(N, th)
    nullC, nullR = [], []
    for _ in range(NPERM):
        p = rng.permutation(th)
        nullC.append(coherence(N, p))
        if aux is not None:
            r_ij, keep, iu = aux
            c = np.cos(p[keep][:, None] - p[keep][None, :])[iu]
            nullR.append(np.corrcoef(r_ij, c)[0, 1])
    q = lambda x: float(np.nanpercentile(x, 95)) if len(x) else float("nan")
    return {"C": C, "C_null95": q(nullC), "ring_index": ri, "ring_null95": q(nullR), "seconds": float(N.shape[1] * BIN)}


def speed(N, th):
    Sb = np.exp(1j * th) @ N
    ok = N.sum(0) >= 5
    ang = np.angle(Sb)
    pair = ok[:-1] & ok[1:]
    d = np.abs((ang[1:] - ang[:-1] + np.pi) % (2 * np.pi) - np.pi)[pair]
    return float(np.degrees(np.median(d)) / BIN) if d.size > 20 else float("nan")


def diffusion(N, th, cuts):
    """Bump diffusion from the slope of the circular mean squared displacement over lags 0.4-2 s (estimation noise
    only adds a constant). Displacements never cross a gap between state intervals (cuts: bin index -> segment id)."""
    Sb = np.exp(1j * th) @ N
    ok = N.sum(0) >= 5
    ang = np.angle(Sb)
    lags = np.array([2, 4, 6, 8, 10])
    msd = []
    for L in lags:
        pair = ok[:-L] & ok[L:] & (cuts[:-L] == cuts[L:])
        d = ((ang[L:] - ang[:-L] + np.pi) % (2 * np.pi) - np.pi)[pair]
        msd.append(np.mean(d ** 2) if d.size > 20 else np.nan)
    msd = np.array(msd)
    if np.isnan(msd).any():
        return float("nan")
    slope = np.polyfit(lags * BIN, msd, 1)[0]
    return float(np.degrees(np.sqrt(max(slope, 0.0) / 2)))                 # deg / sqrt(s)


def transitions(S):
    ss, se, sl = S["ss"]
    o = np.argsort(ss)
    ss, se, sl = ss[o], se[o], sl[o]
    out = []
    for k in range(1, len(sl)):
        if sl[k] == "wake" and sl[k - 1] == "nrem" and abs(ss[k] - se[k - 1]) <= 1.0 and se[k - 1] - ss[k - 1] >= 60 and se[k] - ss[k] >= 30:
            out.append(float(ss[k]))
    return out


def analyse(path, rng):
    S = load(path)
    hd_idx = np.flatnonzero(S["hd_flag"])
    info = {"session": path.stem, "n_units": len(S["spikes"]), "n_hd": int(hd_idx.size)}
    if hd_idx.size < MIN_HD:
        return {**info, "qualifies": False, "reason": "few HD cells"}
    th, tracked = preferred(S, [S["spikes"][i] for i in hd_idx])
    T = max(float(np.max(np.concatenate([s for s in S["spikes"] if s.size]))), float(S["ss"][1].max()))
    edges = np.arange(0, T + BIN, BIN)
    centres = (edges[:-1] + edges[1:]) / 2
    counts = np.array([np.histogram(s, edges)[0] for s in S["spikes"]], dtype=float)
    state, home, opto = labels(centres, S)
    N = counts[hd_idx]
    sel = {"nrem": (state == "nrem") & home, "rem": (state == "rem") & home, "wake_home": (state == "wake") & home}
    info.update({"tracked_s": tracked, **{f"{k}_s": float(v.sum() * BIN) for k, v in sel.items()}})
    if sel["nrem"].sum() * BIN < MIN_NREM or tracked < MIN_TRACK:
        return {**info, "qualifies": False, "reason": "short NREM or tracking"}
    info["qualifies"] = True
    info["states"] = {}
    for k, m in sel.items():
        if k == "rem" and m.sum() * BIN < MIN_REM:
            continue
        if m.sum() * BIN < 30:
            continue
        cuts = np.cumsum(np.r_[1, np.diff(np.flatnonzero(m)) > 1])        # contiguous runs of the selected bins
        info["states"][k] = {**state_metrics(N[:, m], th, rng), "bump_speed_deg_s": speed(N[:, m], th),
                             "bump_diffusion_deg_sqrt_s": diffusion(N[:, m], th, cuts)}
    n = info["states"]["nrem"]
    info["P1_alive"] = bool(n["C"] > n["C_null95"] and n["ring_index"] > n["ring_null95"])
    tr = [t0 for t0 in transitions(S) if home[min(int(t0 / BIN), home.size - 1)] and not opto[min(int(t0 / BIN), opto.size - 1)]]
    info["n_transitions"] = len(tr)
    if len(tr) >= 3:
        k1 = int(1.0 / BIN)
        rel = np.arange(-WIN, WIN, 1.0)
        pops = {"hd_rate": hd_idx, "fs_rate": np.flatnonzero(S["fs"]), "nonhd_exc_rate": np.flatnonzero(S["exc"] & ~S["hd_flag"])}
        curves = {k: [] for k in list(pops) + ["coherence"]}
        for t0 in tr:
            b0 = int(round((t0 - WIN) / BIN))
            if b0 < 0 or b0 + int(2 * WIN / BIN) > counts.shape[1]:
                continue
            seg = counts[:, b0:b0 + int(2 * WIN / BIN)]
            for k, ix in pops.items():
                curves[k].append(seg[ix].reshape(ix.size, -1, k1).sum(2).mean(0) if ix.size else np.full(rel.size, np.nan))
            Nh = seg[hd_idx].reshape(hd_idx.size, -1, k1)
            curves["coherence"].append(np.array([coherence(Nh[:, s, :], th) for s in range(rel.size)]))
        avg = {k: np.nanmean(np.array(v), 0) for k, v in curves.items() if v}
        pre, post = (rel >= PRE[0]) & (rel < PRE[1]), (rel > POST[0]) & (rel <= POST[1])
        idxs = {}
        for k, c in avg.items():
            a, b = float(np.nanmean(c[pre])), float(np.nanmean(c[post]))
            idxs[k] = {"pre": a, "post": b, "change_index": (b - a) / (abs(a) + abs(b)) if (abs(a) + abs(b)) > 0 else float("nan")}
            sm = np.convolve(c, np.ones(3) / 3, mode="same")
            side = np.sign(sm - (a + b) / 2) == np.sign(b - a)
            cross = [i for i in range(1, rel.size - 2) if side[i] and side[i + 1] and side[i + 2]]
            idxs[k]["half_rise_s"] = float(rel[cross[0]]) if cross else float("nan")
        info["transition"] = idxs
        info["transition_curves"] = {k: v.tolist() for k, v in avg.items()}
        info["P3_gain_over_structure"] = bool(idxs["hd_rate"]["change_index"] > idxs["coherence"]["change_index"])
    return info


def main():
    contract = (HERE / "CONTRACT.md").read_text(encoding="utf-8")
    h = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    if h not in contract:
        raise SystemExit(f"CONTRACT.md does not list this code hash {h}")
    rng = np.random.default_rng(SEED)
    rows = []
    for p in sorted(DATA.glob("*.npz")):
        r = analyse(p, rng)
        rows.append(r)
        print(json.dumps({k: (v if not isinstance(v, dict) else {kk: (round(vv["C"], 4), round(vv["C_null95"], 4), round(vv["ring_index"], 3), round(vv["ring_null95"], 3), round(vv["bump_speed_deg_s"], 1)) if isinstance(vv, dict) and "C" in vv else vv for kk, vv in v.items()})
                          for k, v in r.items() if k not in ("transition_curves",)}, default=str)[:900], flush=True)
    q = [r for r in rows if r.get("qualifies")]
    p1 = [r["P1_alive"] for r in q]
    p3 = [r["P3_gain_over_structure"] for r in q if "P3_gain_over_structure" in r]
    def ratio(a, b, key="bump_speed_deg_s"):
        v = [r["states"][a][key] / r["states"][b][key] for r in q if a in r["states"] and b in r["states"] and r["states"][b][key] > 0]
        return {"median": float(np.nanmedian(v)) if v else None, "n": len(v)}
    def cratio(a, b):
        v = [r["states"][a]["C"] / r["states"][b]["C"] for r in q if a in r["states"] and b in r["states"] and r["states"][b]["C"] > 0]
        return {"median": float(np.nanmedian(v)) if v else None, "n": len(v)}
    summary = {"n_sessions": len(rows), "n_qualifying": len(q), "P1_fraction": float(np.mean(p1)) if p1 else None,
               "P3_n": len(p3), "P3_fraction": float(np.mean(p3)) if p3 else None,
               "speed_ratio_nrem_over_wake_home": ratio("nrem", "wake_home"), "speed_ratio_rem_over_wake_home": ratio("rem", "wake_home"),
               "diffusion_ratio_nrem_over_wake_home": ratio("nrem", "wake_home", "bump_diffusion_deg_sqrt_s"),
               "diffusion_ratio_rem_over_wake_home": ratio("rem", "wake_home", "bump_diffusion_deg_sqrt_s"),
               "coherence_ratio_nrem_over_wake_home": cratio("nrem", "wake_home"), "coherence_ratio_rem_over_wake_home": cratio("rem", "wake_home"),
               "half_rise_median_s": {k: float(np.nanmedian([r["transition"][k]["half_rise_s"] for r in q if "transition" in r and k in r["transition"]]))
                                      for k in ("hd_rate", "fs_rate", "nonhd_exc_rate", "coherence")}}
    p2 = [r["states"]["nrem"]["bump_diffusion_deg_sqrt_s"] > r["states"]["wake_home"]["bump_diffusion_deg_sqrt_s"]
          for r in q if "wake_home" in r["states"] and np.isfinite(r["states"]["nrem"]["bump_diffusion_deg_sqrt_s"])
          and np.isfinite(r["states"]["wake_home"]["bump_diffusion_deg_sqrt_s"])]
    summary["P2_n"], summary["P2_fraction"] = len(p2), (float(np.mean(p2)) if p2 else None)
    verdict = {"P1": "RING_ALIVE_IN_NREM" if p1 and np.mean(p1) >= 0.8 else "RING_NOT_SHOWN_ALIVE_IN_NREM",
               "P2": ("NREM_DRIFTS_FASTER" if np.mean(p2) >= 0.7 else "NREM_NOT_FASTER") if p2 else "INSUFFICIENT",
               "P3": ("GAIN_TURNS_ON_NOT_STRUCTURE" if np.mean(p3) >= 0.7 else "GAIN_NOT_DOMINANT") if p3 else "INSUFFICIENT_TRANSITIONS"}
    result = {"schema": "ce-a1-step56-mouse-sleep-ring", "code_sha256": h, "summary": summary, "verdict": verdict, "sessions": rows}
    with (HERE / "results.json").open("x", encoding="utf-8") as stream:
        json.dump(result, stream, indent=1, default=float)
    print("verdict", json.dumps(verdict), json.dumps(summary, default=float))


if __name__ == "__main__":
    main()
