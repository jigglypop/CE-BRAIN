"""Q-NPF-03 / F-01  사전 검정력·동어반복 보정 (통계량을 고르기 '전에' 돌린다).

축약 출력계량 (평균궤적 모양이 완전히 빠진 순수 잡음기하):
    Phi(u) = I(u)/m(u)^2 = mu^2/s2 + p^2/2 = CV^-2 + p^2/2,
    m = (log mu)',  s = (log s2)',  p = s/m,  rho = (p^2/2)/Phi.
카드 식:  d log Phi / d log mu = (2 - p)(1 - rho)   [= R]
    -> 위상간(early->late) 또는 cue간 대비에서
       Y := log Phi_late - log Phi_early,  L := log mu_late - log mu_early
       Y - 2L = Lam * (R - 2) L,   카드 Lam = 1,  평균반응만의 귀무 Lam = 0.

세 세계, 모두 Ottenheimer 2023 A1 설계의 N:
  8 mice, n = 54,52,33,17,35,62,38,63, phase 당 60 trial (cueA 40 / cueB 20),
  반쪽분할 20/20 와 10/10, early = 첫 60 trial, late = 마지막 60 trial.

  W_true  누설 재귀회로(tau_m=20 ms 고정, cue-고정 boxcar 구동, edge별 지연 tau=l/v).
          학습 = 시냅스 효능 dW + 내재 gain + 전도속도 v.  방출 = Poisson +
          trial 공유 gain(lognormal) + 구동 jitter.
  W_taut  동어반복 세계: 임의 잠재곡선 + 임의 비선형 readout(= 임의 계량장),
          평균궤적만 warp(1.25배)·scale(1.35배), 잡음은 상태무관 가법.
  W_hist  회로는 W_true 와 같되 late phase 에만 공유변동 3배(잡음이 상태함수가 아님).

씨앗 20260902.  실제 자료 파일은 열지 않는다.
"""

from __future__ import annotations

import json
import time
from pathlib import Path

import numpy as np

from check_identity import DU, HALF_WIN

SEED = 20260902
HERE = Path(__file__).resolve().parent

# ---- 동결 설계 상수 ---------------------------------------------------------
NEURONS = (54, 52, 33, 17, 35, 62, 38, 63)
TRIALS = {"A": 40, "B": 20}
DT = 1e-3
T_END = 2.0
BIN = DU
TAU_M = 20e-3
CUE_ON, CUE_OFF = 0.10, 0.60
SPEC_RAD = 0.85
V_COND = 0.25
LEN_MIN, LEN_MAX = 5e-5, 6e-4
NU_G = 0.05
SIG_D = 0.08
R_BASE = 1.0
LEARN_DW = 0.18
LEARN_GAIN = 1.30
LEARN_VFAC = 1.25

# ---- 동결 문턱 (카드에 그대로 적는다) ---------------------------------------
L_MIN = 0.10       # 무차원 |log mu_late/mu_early| 하한 (불변)
CV_MAX = 2.0       # 무차원 sigma/mu 상한            (불변)
SD_LMU_MIN = 0.10  # 무차원 선택 bin 안 log mu 의 표준편차 하한 (p 식별, 불변)
EDGE_PAD = HALF_WIN + 1
N_BOOT = 2000
CI_LO, CI_HI = 5.0, 95.0      # 지지 판정용 90% 구간
CI2_LO, CI2_HI = 1.0, 99.0    # 카드 식 직접 판정(kill K1)용 98% 구간
GATE_DEN_LO = 0.0
RAW_RANK: list = []  # IV 분모의 마리부트스트랩 95% 하한이 이 값 초과여야 검정 진행


# ============================ 세계 =========================================
def build_circuit(rng, n):
    G = rng.normal(size=(n, n)) / np.sqrt(n)
    np.fill_diagonal(G, 0.0)
    W = SPEC_RAD * G / np.max(np.abs(np.linalg.eigvals(G)))
    dW = rng.normal(size=(n, n)) / np.sqrt(n)
    np.fill_diagonal(dW, 0.0)
    dW *= SPEC_RAD / np.max(np.abs(np.linalg.eigvals(dW)))
    bA = np.abs(rng.normal(size=n))
    bB = 0.80 * bA + 0.20 * np.abs(rng.normal(size=n))
    return {"W": W, "dW": dW, "ell": rng.uniform(LEN_MIN, LEN_MAX, size=(n, n)),
            "bA": bA, "bB": bB, "g": 4.0 + 2.0 * rng.random(n), "n": n}


def run_circuit(cc, phase, cue, drive_scale=1.0):
    n = cc["n"]
    W = cc["W"] + (LEARN_DW * cc["dW"] if phase == "late" else 0.0)
    gain = cc["g"] * (LEARN_GAIN if phase == "late" else 1.0)
    v = V_COND * (LEARN_VFAC if phase == "late" else 1.0)
    b = (cc["bA"] if cue == "A" else cc["bB"] * 0.68) * drive_scale
    dsteps = np.clip(np.rint(cc["ell"] / v / DT).astype(int), 0, 8)
    masks = {d: (W * (dsteps == d)) for d in sorted(set(dsteps.ravel().tolist()))}
    nstep = int(round(T_END / DT))
    per_bin = int(round(BIN / DT))
    K = int(round(T_END / BIN))
    hist = np.zeros((9, n))
    x = np.zeros(n)
    rate = np.zeros((n, K))
    acc = np.zeros(n)
    for t in range(nstep):
        tt = t * DT
        h = np.zeros(n)
        for d, Wd in masks.items():
            h += Wd @ hist[d]
        x = x + (DT / TAU_M) * (-x + h + b * (1.0 if CUE_ON <= tt < CUE_OFF else 0.0))
        phi = np.log1p(np.exp(np.clip(x, -30, 30)))
        hist = np.roll(hist, 1, axis=0)
        hist[0] = phi
        acc += R_BASE + gain * phi
        if (t + 1) % per_bin == 0:
            rate[:, t // per_bin] = acc / per_bin
            acc = np.zeros(n)
    return rate * BIN


def taut_world(rng, n, phase, cue):
    K = int(round(T_END / BIN))
    u = np.arange(K) * BIN
    eps, alz = (0.25, 1.35) if phase == "late" else (0.0, 1.0)
    amp = 1.0 if cue == "A" else 0.68
    uu = u / (1.0 + eps)
    z = alz * np.vstack([
        amp * np.exp(-((uu - 0.45) ** 2) / (2 * 0.25**2)) + 0.35 * amp * np.exp(-uu / 0.8),
        amp * np.sin(2.1 * uu + 0.4) * np.exp(-uu / 1.1)])
    A = rng.normal(size=(n, 2))
    Q = rng.normal(size=(n, 3)) * 0.6
    c = 1.0 + 0.5 * rng.random(n)
    lin = A @ z + Q[:, [0]] * z[0] ** 2 + Q[:, [1]] * z[0] * z[1] + Q[:, [2]] * z[1] ** 2
    return 0.25 + 2.0 * np.log1p(np.exp(np.clip(c[:, None] + lin, -30, 30)))


# ============================ 표본 =========================================
def draw_counts(rng, lam, dlam, ntr, nu=NU_G):
    Gt = rng.lognormal(mean=-nu / 2.0, sigma=np.sqrt(nu), size=(ntr, 1, 1))
    dj = rng.normal(1.0, SIG_D, size=(ntr, 1, 1))
    return rng.poisson(np.clip(Gt * (lam[None] + (dj - 1.0) * dlam[None]), 1e-4, None)).astype(float)


def draw_gauss(rng, lam, s0, ntr):
    return lam[None] + rng.normal(size=(ntr, lam.shape[0], lam.shape[1])) * s0[None, :, None]


def exact_moments(lam, dlam, a, nu=NU_G):
    mu = a @ lam
    C = a @ dlam
    nup = np.exp(nu) - 1.0
    return mu, (a**2) @ lam + nup * mu**2 + (1.0 + nup) * SIG_D**2 * C**2


# ============================ 통계량 =======================================
def fit_p(mu, s2, keep):
    """변동-평균 멱지수 p = d log s2 / d log mu 를 선택 bin 위 OLS 로.
    미분비 s/m 을 쓰지 않으므로 0/0 도 이산화편의도 없다. ridge 없음(raw)."""
    x = np.log(mu[keep])
    y = np.log(s2[keep])
    if x.size < 4:
        return np.nan
    sd = float(np.std(x, ddof=1))
    if sd < SD_LMU_MIN:
        return np.nan
    return float(np.cov(x, y, ddof=1)[0, 1] / np.var(x, ddof=1))


def phi_terms(mu, s2, p):
    """축약계량 Phi = mu^2/s2 + p^2/2 = CV^-2 + p^2/2 와 예측기울기 R.
    모두 chart 재척도 불변이고 평균궤적의 '모양'을 담지 않는다."""
    Phi = mu**2 / s2 + p**2 / 2.0
    rho = (p**2 / 2.0) / Phi
    return {"Phi": Phi, "rho": rho, "R": (2.0 - p) * (1.0 - rho)}


def select_bins(mu_e, s2_e, mu_l, K):
    L = np.log(mu_l) - np.log(mu_e)
    keep = np.zeros(K, dtype=bool)
    keep[EDGE_PAD:-EDGE_PAD] = True
    keep &= np.abs(L) >= L_MIN
    keep &= (np.sqrt(s2_e) / mu_e) <= CV_MAX
    return keep


def xy(mu_e, s2_e, mu_l, s2_l, keep):
    p = fit_p(mu_e, s2_e, keep)
    if not np.isfinite(p):
        return None, None
    te = phi_terms(mu_e, s2_e, p)
    tl = phi_terms(mu_l, s2_l, p)
    with np.errstate(divide="ignore", invalid="ignore"):
        L = np.log(mu_l) - np.log(mu_e)
        Y = np.log(tl["Phi"]) - np.log(te["Phi"])
    return (te["R"] - 2.0) * L, Y - 2.0 * L


def fit_chart(counts):
    """동결 규칙: early phase 홀수 trial 평균에서 (반응창 - 기저창) > 0 인 세포의
    비가중 집단합. 지표 chart 라야 Poisson 항이 정확히 mu 에 비례해 상태함수가 된다."""
    mr = counts.mean(axis=0)
    base = mr[:, : int(round(0.08 / BIN))].mean(axis=1)
    peak = mr[:, int(round(0.15 / BIN)) : int(round(1.2 / BIN))].mean(axis=1)
    S = (peak - base) > 0
    if S.sum() < 3:
        S = np.ones_like(S, dtype=bool)
    return S.astype(float) / S.sum()


def half(we, wl, par, keep):
    ie = np.arange(we.shape[0]) % 2 == par
    il = np.arange(wl.shape[0]) % 2 == par
    mu_e, s2_e = we[ie].mean(0), we[ie].var(0, ddof=1)
    mu_l, s2_l = wl[il].mean(0), wl[il].var(0, ddof=1)
    if np.any(mu_e <= 0) or np.any(mu_l <= 0) or np.any(s2_e <= 0) or np.any(s2_l <= 0):
        return None, None
    return xy(mu_e, s2_e, mu_l, s2_l, keep)


def pair_terms(cnt_e, cnt_l, a, K):
    we = np.einsum("tnk,n->tk", cnt_e, a)
    wl = np.einsum("tnk,n->tk", cnt_l, a)
    mu_e, s2_e = we.mean(0), we.var(0, ddof=1)
    mu_l, s2_l = wl.mean(0), wl.var(0, ddof=1)
    if np.any(mu_e <= 0) or np.any(mu_l <= 0) or np.any(s2_e <= 0) or np.any(s2_l <= 0):
        return None
    keep = select_bins(mu_e, s2_e, mu_l, K)
    if keep.sum() < 4:
        return None
    RAW_RANK.append((float(np.min((mu_e**2 / s2_e)[keep])), int(keep.sum()),
                     int(np.sum(s2_e[keep] > 0))))
    XA, YA = half(we, wl, 0, keep)
    XB, YB = half(we, wl, 1, keep)
    if XA is None or XB is None:
        return None
    num = 0.5 * (XA * YB + XB * YA)
    den = XA * XB
    ok = keep & np.isfinite(num) & np.isfinite(den)
    if ok.sum() < 3:
        return None
    return num[ok], den[ok]


def boot(pools_by_mouse, rng, nboot=N_BOOT):
    mice = [m for m in pools_by_mouse if pools_by_mouse[m]]
    if len(mice) < 3:
        return None
    flat = [p for m in mice for p in pools_by_mouse[m]]
    num0 = sum(float(np.sum(p[0])) for p in flat)
    den0 = sum(float(np.sum(p[1])) for p in flat)
    lams, dens = np.empty(nboot), np.empty(nboot)
    nm = len(mice)
    for b in range(nboot):
        pick = rng.integers(0, nm, size=nm)
        pl = [p for i in pick for p in pools_by_mouse[mice[i]]]
        nb = sum(float(np.sum(p[0])) for p in pl)
        db = sum(float(np.sum(p[1])) for p in pl)
        dens[b] = db
        lams[b] = nb / db if abs(db) > 1e-12 else np.nan
    g = np.isfinite(lams)
    if g.sum() < nboot // 2:
        return None
    return {"lam": num0 / den0 if abs(den0) > 1e-12 else np.nan,
            "lo": float(np.percentile(lams[g], CI_LO)),
            "hi": float(np.percentile(lams[g], CI_HI)),
            "lo2": float(np.percentile(lams[g], CI2_LO)),
            "hi2": float(np.percentile(lams[g], CI2_HI)),
            "lev": {L: (float(np.percentile(lams[g], (100 - L) / 2)),
                        float(np.percentile(lams[g], 100 - (100 - L) / 2))) for L in (95, 98, 99)},
            "den": den0, "den_lo": float(np.percentile(dens, 2.5))}


# ============================ 실행 =========================================
def prepare_world(world, wseed):
    out = []
    for mi, n in enumerate(NEURONS):
        cc = None if world.startswith("taut") else build_circuit(np.random.default_rng(wseed * 1000 + mi), n)
        e = {"n": n, "lam": {}, "dlam": {}, "s0": None}
        for phase in ("early", "late"):
            for cue in ("A", "B"):
                if world.startswith("taut"):
                    lam = taut_world(np.random.default_rng(wseed * 7919 + mi), n, phase, cue)
                    dl = np.zeros_like(lam)
                else:
                    lam = run_circuit(cc, phase, cue)
                    dl = (run_circuit(cc, phase, cue, 1.01) - lam) / 0.01
                e["lam"][(phase, cue)] = lam
                e["dlam"][(phase, cue)] = dl
        if world.startswith("taut"):
            e["s0"] = 0.45 * e["lam"][("early", "A")].mean(axis=1) ** 0.5 + 0.25
        out.append(e)
    return out


def exact_chart(lam):
    resp = lam[:, int(round(0.15 / BIN)) : int(round(1.2 / BIN))].mean(1) - lam[:, : int(round(0.08 / BIN))].mean(1)
    S = resp > 0
    if S.sum() < 3:
        S = np.ones_like(S, dtype=bool)
    return S.astype(float) / S.sum()


def truth(worldp):
    """무잡음 정확 mu,s2 로 계산한 지상진실 Lam (카드가 그 세계에서 참인가)."""
    K = int(round(T_END / BIN))
    num = den = 0.0
    ps, rs, Rs, Ls, nb = [], [], [], [], 0
    for e in worldp:
        a = exact_chart(e["lam"][("early", "A")])
        for cue in ("A", "B"):
            mu_e, s2_e = exact_moments(e["lam"][("early", cue)], e["dlam"][("early", cue)], a)
            mu_l, s2_l = exact_moments(e["lam"][("late", cue)], e["dlam"][("late", cue)], a)
            keep = select_bins(mu_e, s2_e, mu_l, K)
            if keep.sum() < 4:
                continue
            X, Y = xy(mu_e, s2_e, mu_l, s2_l, keep)
            if X is None:
                continue
            num += float(np.sum(X[keep] * Y[keep]))
            den += float(np.sum(X[keep] ** 2))
            p = fit_p(mu_e, s2_e, keep)
            t = phi_terms(mu_e, s2_e, p)
            ps.append(float(p))
            rs.append(float(np.mean(t["rho"][keep])))
            Rs.append(float(np.mean(t["R"][keep])))
            Ls.append(float(np.mean((np.log(mu_l) - np.log(mu_e))[keep])))
            nb += int(keep.sum())
    return {"lam_true": num / den if abs(den) > 1e-12 else float("nan"),
            "p_true": float(np.mean(ps)), "rho_true": float(np.mean(rs)),
            "R_true": float(np.mean(Rs)), "logalpha_true": float(np.mean(Ls)),
            "bins_true": nb}


def one_rep(worldp, world, rng, contrast):
    K = int(round(T_END / BIN))
    pools = {}
    for mi, e in enumerate(worldp):
        cnt = {}
        for phase in ("early", "late"):
            for cue in ("A", "B"):
                lam = e["lam"][(phase, cue)]
                if world == "taut":
                    cnt[(phase, cue)] = draw_gauss(rng, lam, e["s0"], TRIALS[cue])
                elif world == "tautpois":
                    cnt[(phase, cue)] = draw_counts(rng, lam, e["dlam"][(phase, cue)], TRIALS[cue])
                else:
                    nu = NU_G * (3.0 if (world == "hist" and phase == "late") else 1.0)
                    cnt[(phase, cue)] = draw_counts(rng, lam, e["dlam"][(phase, cue)], TRIALS[cue], nu=nu)
        a = fit_chart(np.concatenate([cnt[("early", "A")][0::2], cnt[("early", "B")][0::2]], 0))
        pairs = ([(("early", c), ("late", c)) for c in ("A", "B")] if contrast == "learn"
                 else [(("early", "B"), ("early", "A"))])
        got = [t for pe, pl in pairs if (t := pair_terms(cnt[pe], cnt[pl], a, K)) is not None]
        if got:
            pools[mi] = got
    return pools


def evaluate(world, nworlds, nreps, contrast="learn"):
    rng = np.random.default_rng(SEED)
    rows, tr = [], []
    for ws in range(nworlds):
        wp = prepare_world(world, SEED + 101 * ws)
        if world in ("true", "hist"):
            tr.append(truth(wp))
        for _ in range(nreps):
            r = boot(one_rep(wp, world, rng, contrast), rng)
            if r is None:
                rows.append({"gate": False})
                continue
            rows.append({"gate": bool(r["den"] > 0 and r["den_lo"] > GATE_DEN_LO),
                         "lam": r["lam"], "lo": r["lo"], "hi": r["hi"], "den": r["den"],
                         "excl0": bool(r["lo"] > 0.0),
                         "cont1": bool(r["lo2"] <= 1.0 <= r["hi2"]),
                         "w98": r["hi2"] - r["lo2"],
                         "lev": r["lev"]})
    ok = [r for r in rows if r["gate"]]
    n = len(rows)
    res = {"world": world, "contrast": contrast, "n_rep": n,
           "gate_pass_rate": round(len(ok) / n, 3),
           "power_excl0_and_cont1": round(sum(r["excl0"] and r["cont1"] for r in ok) / n, 3),
           "reject_meanonly_rate": round(sum(r["excl0"] for r in ok) / n, 3),
           "kill_excl1_rate": round(sum(not r["cont1"] for r in ok) / n, 3),
           "kill_excl1_by_level": {L: round(sum(not (r["lev"][L][0] <= 1.0 <= r["lev"][L][1]) for r in ok) / n, 3)
                                   for L in (95, 98, 99)},
           "support_by_level": {L: round(sum(r["excl0"] and (r["lev"][L][0] <= 1.0 <= r["lev"][L][1]) for r in ok) / n, 3)
                                for L in (95, 98, 99)},
           "ci_width_by_level": {L: (round(float(np.median([r["lev"][L][1] - r["lev"][L][0] for r in ok])), 3)
                                     if ok else None) for L in (95, 98, 99)}}
    if ok:
        L = np.array([r["lam"] for r in ok])
        res |= {"lam_median": round(float(np.median(L)), 3),
                "lam_q05": round(float(np.percentile(L, 5)), 3),
                "lam_q95": round(float(np.percentile(L, 95)), 3),
                "ci90_width_median": round(float(np.median([r["hi"] - r["lo"] for r in ok])), 3),
                "ci98_width_median": round(float(np.median([r["w98"] for r in ok])), 3),
                "den_median": round(float(np.median([r["den"] for r in ok])), 4)}
    if RAW_RANK:
        res["raw_rank"] = {"min_CVinv2": round(float(np.min([r[0] for r in RAW_RANK])), 4),
                           "median_CVinv2": round(float(np.median([r[0] for r in RAW_RANK])), 3),
                           "bins_used_median": int(np.median([r[1] for r in RAW_RANK])),
                           "posdef_frac": round(float(np.mean([r[2] / r[1] for r in RAW_RANK])), 4),
                           "ridge": "none (raw)"}
        RAW_RANK.clear()
    if tr:
        for k in tr[0]:
            res[k] = round(float(np.mean([t[k] for t in tr])), 4)
    return res


def main() -> int:
    t0 = time.time()
    NW, NR = 3, 60
    out = {"seed": SEED,
           "design": {"mice": len(NEURONS), "neurons": list(NEURONS), "trials_per_phase": 60,
                      "per_cue": TRIALS, "half_split": {"A": "20/20", "B": "10/10"},
                      "bins": int(round(T_END / BIN)), "bin_s": BIN},
           "thresholds": {"L_MIN": L_MIN, "CV_MAX": CV_MAX, "SD_LMU_MIN": SD_LMU_MIN,
                          "DU_s": DU, "EDGE_PAD_bins": EDGE_PAD,
                          "CI_support": "90% (5,95) 마리 클러스터 부트스트랩", "CI_kill": "98% (1,99)", "N_BOOT": N_BOOT,
                          "gate": "IV 분모의 마리부트스트랩 95% 하한 > 0"},
           "rows": [evaluate("true", NW, NR, "learn"),
                    evaluate("true", NW, NR, "cue"),
                    evaluate("taut", NW, NR, "learn"),
                    evaluate("tautpois", NW, NR, "learn"),
                    evaluate("hist", NW, NR, "learn")],
           }
    out["runtime_s"] = round(time.time() - t0, 1)
    (HERE / "result_power.json").write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
