"""BA-SRM15 stages A (fit), B (selection), C (single held-out opening).

Contract: paper/검증_원장/BA_SRM15_행동_endpoint_계약.md. Uses the verified
preparation pipeline from ba_srm15_endpoint.py (anchor identity already proven
against the SRM13 lock). Stage receipts are one-shot; every selection closes
before stage C opens the held-out split exactly once.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import math
import sys
import time
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location("srm15", HERE / "ba_srm15_endpoint.py")
E = importlib.util.module_from_spec(_spec)
sys.modules["srm15"] = E
_spec.loader.exec_module(E)
A7, M13, causal_q = E.A7, E.M13, E.causal_q

RIDGES = E.RIDGE_GRID
H = E.H_TARGET
LAGS = E.AR_LAGS
CONTROL_SET = ("AR", "FIXED_D", "FIXED_4", "PARTICIPATION_RATIO", "RAW_SPECTRAL",
               "CAUSAL_UNWEIGHTED", "MASK_ONLY", "RED_CHANNEL")
ADVERSE = ("PHASE_RANDOMIZED", "TIME_REVERSED", "CIRCULAR_BEHAVIOR_SHIFT")
STATE = HERE / "ba-srm15-state.npz"  # cached features, behavior-inclusive after stage A


def rms(x):
    x = np.asarray(x, float)
    x = x[np.isfinite(x)]
    return float(np.sqrt(np.mean(x * x))) if x.size else float("nan")


def soft_features_from_q(qout, positions, clock, prefix_positions):
    """(q, nu, kappa, M) rows at `positions`; sigma from prefix positions."""
    covs, Q, cg = qout["covariances"], qout["Q"], qout["cG"]
    rstar = qout["r_star"]
    tau0 = float(np.median(np.diff(clock)[np.diff(clock) > 0]))
    cache: dict[int, np.ndarray] = {}

    def s_matrix(t):
        if t not in cache:
            if covs[t] is None:
                cache[t] = None
            else:
                mu, vec = np.linalg.eigh(covs[t] / cg)
                cache[t] = (vec * (mu / (mu + 1.0))) @ vec.T
        return cache[t]

    def row(t):
        if t < 1 or covs[t] is None or covs[t - 1] is None:
            return (np.nan,) * 4
        q = Q[t]
        dt = (clock[t] - clock[t - 1]) / tau0
        nu = (Q[t] - Q[t - 1]) / dt if dt > 0 else np.nan
        sa, sb = s_matrix(t), s_matrix(t - 1)
        kap = float(np.linalg.norm(sa - sb)) / math.sqrt(max(rstar[t], 1.0))
        return (q, nu, kap, np.nan)  # M filled after sigmas

    raw = {t: row(t) for t in set(positions) | set(prefix_positions)}
    sig_k = rms([raw[t][2] for t in prefix_positions])
    sig_n = rms([raw[t][1] for t in prefix_positions])
    if not (math.isfinite(sig_k) and sig_k > 1e-12 and math.isfinite(sig_n) and sig_n > 1e-12):
        return None, {"sigma_kappa": sig_k, "sigma_nu": sig_n}
    out = {}
    for t in raw:
        q, nu, kap, _ = raw[t]
        m = (math.exp(-((kap / sig_k) ** 2) - ((nu / sig_n) ** 2))
             if math.isfinite(kap) and math.isfinite(nu) else np.nan)
        out[t] = (q, nu, kap, m)
    return out, {"sigma_kappa": sig_k, "sigma_nu": sig_n}


def spectral_family_rows(qout, positions, clock, prefix_positions, domains):
    """FIXED_D(all d), PARTICIPATION_RATIO, RAW_SPECTRAL rows."""
    covs, cg, rstar = qout["covariances"], qout["cG"], qout["r_star"]
    tau0 = float(np.median(np.diff(clock)[np.diff(clock) > 0]))
    eigc: dict[int, tuple] = {}

    def eig(t):
        if t not in eigc:
            if covs[t] is None:
                eigc[t] = None
            else:
                mu, vec = np.linalg.eigh(covs[t] / cg)
                order = np.argsort(mu)[::-1]
                eigc[t] = (np.maximum(mu[order], 0.0), vec[:, order])
        return eigc[t]

    need = sorted(set(positions) | set(prefix_positions))
    rowsD = {d: {} for d in domains}
    rowsPR, rowsRS = {}, {}
    prof = {d: {"e": {}, "p": {}} for d in domains}
    pr_raw = {}
    for t in need:
        pair, prev = eig(t), eig(t - 1) if t >= 1 else None
        if pair is None or prev is None:
            for d in domains:
                rowsD[d][t] = (np.nan,) * 4
            rowsPR[t] = (np.nan,) * 4
            rowsRS[t] = (np.nan,) * 4
            continue
        mu, vec = pair
        mu0, vec0 = prev
        tr = float(mu.sum())
        tr2 = float((mu * mu).sum())
        rs = max(float(rstar[t]), 1.0)
        dt = (clock[t] - clock[t - 1]) / tau0
        rho = mu / tr if tr > 1e-300 else None
        rho0 = mu0 / mu0.sum() if mu0.sum() > 1e-300 else None
        # RAW_SPECTRAL
        if rho is None:
            rowsRS[t] = (np.nan,) * 4
        else:
            ent = float(-(rho[rho > 0] * np.log(rho[rho > 0])).sum() / math.log(rs)) if rs > 1 else np.nan
            rowsRS[t] = (tr / rs, tr2 / rs, float(mu[0]) / tr, ent)
        # PARTICIPATION_RATIO raw pieces
        if rho is None or rho0 is None or tr2 <= 1e-300 or dt <= 0:
            pr_raw[t] = (np.nan, np.nan, np.nan)
        else:
            qpr = tr * tr / (rs * tr2)
            mu_prev_tr2 = float((mu0 * mu0).sum())
            qpr0 = (mu0.sum() ** 2) / (rs * mu_prev_tr2) if mu_prev_tr2 > 1e-300 else np.nan
            dqpr = (qpr - qpr0) / dt
            drho = float(np.linalg.norm(rho - rho0)) / math.sqrt(2.0)
            pr_raw[t] = (qpr, dqpr, drho)
        # FIXED_D raw pieces
        for d in domains:
            if d >= mu.size or tr <= 1e-300 or dt <= 0:
                prof[d]["e"][t] = np.nan
                prof[d]["p"][t] = np.nan
                continue
            e_now = float(mu[:d].sum()) / tr
            tr0 = float(mu0.sum())
            e_prev = float(mu0[:d].sum()) / tr0 if tr0 > 1e-300 else np.nan
            P = vec[:, :d] @ vec[:, :d].T
            P0 = vec0[:, :d] @ vec0[:, :d].T
            prof[d]["e"][t] = (e_now, (e_now - e_prev) / dt if math.isfinite(e_prev) else np.nan)
            prof[d]["p"][t] = float(np.linalg.norm(P - P0)) / math.sqrt(2 * d)
    # sigmas and assembled rows
    s_dq = rms([pr_raw[t][1] for t in prefix_positions if t in pr_raw])
    s_dr = rms([pr_raw[t][2] for t in prefix_positions if t in pr_raw])
    for t in need:
        if t in pr_raw and all(math.isfinite(v) for v in pr_raw[t]) and s_dq > 1e-12 and s_dr > 1e-12:
            qpr, dqpr, drho = pr_raw[t]
            rowsPR[t] = (qpr, dqpr, drho,
                         math.exp(-((dqpr / s_dq) ** 2) - ((drho / s_dr) ** 2)))
        elif t not in rowsPR:
            rowsPR[t] = (np.nan,) * 4
    for d in domains:
        s_e = rms([prof[d]["e"][t][1] for t in prefix_positions
                   if isinstance(prof[d]["e"].get(t), tuple)])
        s_p = rms([prof[d]["p"][t] for t in prefix_positions
                   if isinstance(prof[d]["p"].get(t), float) and math.isfinite(prof[d]["p"][t])])
        for t in need:
            ev = prof[d]["e"].get(t)
            pv = prof[d]["p"].get(t)
            if (isinstance(ev, tuple) and math.isfinite(ev[1]) and isinstance(pv, float)
                    and math.isfinite(pv) and s_e > 1e-12 and s_p > 1e-12):
                rowsD[d][t] = (ev[0], ev[1], pv,
                               math.exp(-((pv / s_p) ** 2) - ((ev[1] / s_e) ** 2)))
            elif t not in rowsD[d]:
                rowsD[d][t] = (np.nan,) * 4
    return rowsD, rowsPR, rowsRS


def build_mask_z(zmask, processed):
    pi = zmask[:, :processed].mean(axis=1)
    denom = np.sqrt(np.maximum(pi * (1 - pi), 1e-6))
    zm = (zmask.astype(np.float64) - pi[:, None]) / denom[:, None]
    return zm


def segments_of(prep):
    """(split_block, gap_run) segment id per retained position."""
    clock = prep["clock"]
    usable = clock.size
    e1, e2 = int(0.6 * usable), int(0.8 * usable)
    dt = np.diff(clock)
    pos = dt[np.isfinite(dt) & (dt > 0)]
    gap = 3.0 * np.median(pos) if pos.size else np.inf
    seg = np.zeros(usable, dtype=int)
    cur = 0
    for i in range(1, usable):
        if dt[i - 1] > gap or i == e1 or i == e2:
            cur += 1
        seg[i] = cur
    return seg


def phase_randomize(z0, seg, rid):
    seed = int.from_bytes(hashlib.sha256(f"20260823|{rid}|phase-control".encode()).digest()[:8], "big")
    rng = np.random.default_rng(seed)
    out = z0.copy()
    for s in np.unique(seg):
        idx = np.flatnonzero(seg == s)
        if idx.size < 4:
            continue
        block = out[:, idx]
        f = np.fft.rfft(block, axis=1)
        phases = np.exp(1j * rng.uniform(0, 2 * np.pi, size=f.shape))
        phases[:, 0] = 1.0
        if idx.size % 2 == 0:
            phases[:, -1] = 1.0
        out[:, idx] = np.fft.irfft(f * phases, n=idx.size, axis=1)
    return out


def time_reverse(z0, zmask, seg):
    z, m = z0.copy(), zmask.copy()
    for s in np.unique(seg):
        idx = np.flatnonzero(seg == s)
        z[:, idx] = z[:, idx[::-1]]
        m[:, idx] = m[:, idx[::-1]]
    return z, m


def load_behavior(prep):
    d = M13.loadmat(prep["mat_path"], variable_names=("behavior",), simplify_cells=True)
    q = d.get("behavior", {})
    v = np.asarray(q["v"], float).reshape(-1)
    pc = np.asarray(q["pc1_2"], float)
    if pc.ndim == 1:
        pc = pc[:, None]
    v = v[:prep["raw_stop"]][prep["keep_raw"]][prep["valid"]]
    pc = pc[:prep["raw_stop"]][prep["keep_raw"]][prep["valid"], :2]
    if v.size != prep["clock"].size:
        raise RuntimeError(f"behavior length mismatch {prep['rid']}")
    return v, pc


def build_recording(cand, rid, cut, cls, role, read_behavior):
    prep = E.prepare_recording(cand, rid, cut, cls, role)
    ids, digest, qmain = E.collect_anchor_ids(cand, prep)
    pos_of = {int(v): i for i, v in enumerate(prep["original_index"])}
    positions = {k: [pos_of[i] for i in ids[k]] for k in ids}
    prefix = positions["train"]
    clock = prep["clock"]
    domains = [d for d in E.FIXED_D_MENU if d in prep["domains"]]
    allpos = sorted(set(sum(positions.values(), [])))

    fams = {}
    ce, ce_sig = soft_features_from_q(qmain, allpos, clock, prefix)
    if ce is None:
        return {"rid": rid, "abstain": "CE_SIGMA", "detail": ce_sig}
    fams["CE_SOFT"] = ce
    rowsD, rowsPR, rowsRS = spectral_family_rows(qmain, allpos, clock, prefix, domains)
    fams["FIXED_D"] = rowsD
    fams["FIXED_4"] = rowsD.get(4, {t: (np.nan,) * 4 for t in allpos})
    fams["PARTICIPATION_RATIO"] = rowsPR
    fams["RAW_SPECTRAL"] = rowsRS

    ones = np.ones_like(prep["dvec"])
    try:
        q_unw = causal_q(cand, prep["z0"], prep["zmask"], clock, ones, max(1, prep["processed"]))
        unw, _ = soft_features_from_q(q_unw, allpos, clock, prefix)
    except ValueError:
        unw = None
    fams["CAUSAL_UNWEIGHTED"] = unw or {t: (np.nan,) * 4 for t in allpos}

    zm = build_mask_z(prep["zmask"], prep["processed"])
    try:
        q_msk = causal_q(cand, zm, np.ones_like(prep["zmask"]), clock,
                         np.ones(zm.shape[0]), max(1, prep["processed"]))
        msk, _ = soft_features_from_q(q_msk, allpos, clock, prefix)
        fams["MASK_ONLY"] = msk or {t: (0.0,) * 4 for t in allpos}
    except ValueError:
        fams["MASK_ONLY"] = {t: (0.0, 0.0, 0.0, 0.0) for t in allpos}

    redz, redmask, redd, _ = M13.robust_z(prep["cr_red"], prep["processed"]) \
        if prep["cr_red"].shape[0] else (None, None, None, None)
    red = None
    if redz is not None and redz.shape[0] >= 2:
        try:
            q_red = causal_q(cand, redz, redmask, clock, redd, max(1, prep["processed"]))
            red, _ = soft_features_from_q(q_red, allpos, clock, prefix)
        except ValueError:
            red = None
    fams["RED_CHANNEL"] = red or {t: (np.nan,) * 4 for t in allpos}

    seg = segments_of(prep)
    adverse = {}
    zpr = phase_randomize(prep["z0"], seg, rid)
    try:
        q_pr = causal_q(cand, zpr, prep["zmask"], clock, prep["dvec"], max(1, prep["processed"]))
        a, _ = soft_features_from_q(q_pr, allpos, clock, prefix)
    except ValueError:
        a = None
    adverse["PHASE_RANDOMIZED"] = a or {t: (np.nan,) * 4 for t in allpos}
    ztr, mtr = time_reverse(prep["z0"], prep["zmask"], seg)
    dvec_tr = np.sqrt(mtr[:, :prep["processed"]].mean(axis=1))
    try:
        q_tr = causal_q(cand, ztr, mtr, clock, dvec_tr, max(1, prep["processed"]))
        a, _ = soft_features_from_q(q_tr, allpos, clock, prefix)
    except ValueError:
        a = None
    adverse["TIME_REVERSED"] = a or {t: (np.nan,) * 4 for t in allpos}

    out = {"rid": rid, "cls": cls, "role": role, "positions": positions,
           "domains": domains, "seg": seg.tolist(), "clock_len": int(clock.size),
           "families": fams, "adverse": adverse, "abstain": None}
    if read_behavior:
        v, pc = load_behavior(prep)
        out["v"] = v
        out["pc"] = pc
    return out


def assemble_rows(recd, split, family, d=None, adverse_kind=None, shift=False):
    """X (AR4 [+fam4]), y arrays over the split's common-valid rows."""
    v = recd["v"]
    pos = recd["positions"][split]
    fam = (recd["adverse"][adverse_kind] if adverse_kind
           else recd["families"]["FIXED_D"][d] if family == "FIXED_D"
           else recd["families"][family] if family != "AR" else None)
    rows, X, y = [], [], []
    for t in pos:
        if t - max(LAGS) < 0 or t + H >= v.size:
            continue
        ar = [v[t - l] for l in LAGS]
        tgt = v[t + H]
        feat = list(fam[t]) if fam is not None else []
        vals = ar + feat + [tgt]
        if all(map(math.isfinite, map(float, vals))):
            rows.append(t)
            X.append(ar + feat)
            y.append(tgt)
    X, y = np.asarray(X, float), np.asarray(y, float)
    if shift and len(rows):
        seg = np.asarray(recd["seg"])[np.asarray(rows)]
        Xs = X.copy()
        for s in np.unique(seg):
            idx = np.flatnonzero(seg == s)
            n = idx.size
            if n >= 2:
                k = max(1, n // 3)
                Xs[idx, 4:] = X[idx[(np.arange(n) - k) % n], 4:]
        X = Xs
    return np.asarray(rows), X, y


def common_row_check(recd, split):
    """True common-row intersection across every required family for the split."""
    sets = []
    counts = {}
    for family in E.REQUIRED_FAMILIES:
        if family == "FIXED_D":
            for d in recd["domains"]:
                rows = assemble_rows(recd, split, "FIXED_D", d=d)[0]
                counts[f"FIXED_D_{d}"] = len(rows)
                sets.append(set(int(t) for t in rows))
        else:
            rows = assemble_rows(recd, split, family)[0]
            counts[family] = len(rows)
            sets.append(set(int(t) for t in rows))
    inter = set.intersection(*sets) if sets else set()
    counts["COMMON_INTERSECTION"] = len(inter)
    return counts, len(inter) >= 100


def fit_ridge(X, y, lam):
    n, p = X.shape
    mx, sx = X.mean(0), X.std(0)
    sx[sx <= 1e-12] = 1.0
    my, sy = y.mean(), y.std() if y.std() > 1e-12 else 1.0
    Xs, ys = (X - mx) / sx, (y - my) / sy
    beta = np.linalg.solve(Xs.T @ Xs + lam * np.eye(p), Xs.T @ ys)
    return {"beta": beta, "mx": mx, "sx": sx, "my": my, "sy": sy}


def predict(model, X):
    Xs = (X - model["mx"]) / model["sx"]
    return model["my"] + model["sy"] * (Xs @ model["beta"])


def r2(y, yhat):
    ss = float(((y - y.mean()) ** 2).sum())
    return 1.0 - float(((y - yhat) ** 2).sum()) / ss if ss > 1e-300 else float("nan")


if __name__ == "__main__":
    raise SystemExit("import-only module; stages are driven by ba_srm15_run_stages.py")
