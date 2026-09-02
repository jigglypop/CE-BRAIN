"""Q-NPF-03 / F-01  무잡음 항등식 검사 (극한 복원 + chart 재척도 불변).

대상 식 (카드 F-01):
  1차원 chart w = a.o 위에서 (21.42)를 곡선 u -> zbar(u) 로 pullback 하면
      I(u) = mu'(u)^2 / s2(u)  +  (1/2) * ( s2'(u) / s2(u) )^2
           = I_mu + I_Sig,        rho = I_Sig / I
  이고, 잡음이 상태함수 s2 = f(mu) 일 때 평균반응 gain alpha (mu -> alpha*mu) 에 대한
  계량의 동차지수는
      h  :=  d log I / d log alpha |_{alpha=1}
          =  (2 - p)(1 - rho)  +  2*rho*q,
      p  =  d log s2 / d log mu  =  s/m,     q = d log p / d log mu,
      m  =  (log mu)',  s = (log s2)'.
  순수 멱법칙 f = c*mu^p 이면 q = 0 이고 h = (2-p)(1-rho) 가 정확하다.

  평균반응만으로 정해지는 세계(잡음이 상태 무관, s2 = const)에서는 p = rho = 0 이라
  h = 2 (2차 동차)이다.  이것이 귀무이고, 카드는 h < 2 를 예측한다.

씨앗 20260902.  자료 파일은 열지 않는다(순수 해석/합성).
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np

SEED = 20260902
HERE = Path(__file__).resolve().parent

# ---- 동결 문턱 (카드에 그대로 적는다) ---------------------------------------
DU = 0.05          # s, 시간 bin 폭
HALF_WIN = 3       # 국소선형 기울기 창 = +-3 bin = +-0.15 s
TOL_EXACT = 1e-6   # 무잡음 항등식 허용오차
TOL_TRUNC = 0.15   # 절단형 (q 무시) 사전등록 계통오차 상한


def local_slope(y: np.ndarray, du: float, half: int = HALF_WIN) -> np.ndarray:
    """+-half bin 국소선형회귀 기울기. 가장자리는 가용한 점만 쓴다."""
    n = y.size
    out = np.full(n, np.nan)
    for k in range(n):
        lo, hi = max(0, k - half), min(n, k + half + 1)
        idx = np.arange(lo, hi, dtype=float)
        if idx.size < 3:
            continue
        x = (idx - idx.mean()) * du
        yy = y[lo:hi]
        out[k] = float((x * (yy - yy.mean())).sum() / (x * x).sum())
    return out


def fisher_1d(mu: np.ndarray, s2: np.ndarray, du: float = DU) -> dict[str, np.ndarray]:
    """(21.42)의 1차원 pullback.  mu>0, s2>0 필요."""
    m = local_slope(np.log(mu), du)
    s = local_slope(np.log(s2), du)
    I_mu = mu**2 * m**2 / s2
    I_sg = 0.5 * s**2
    I = I_mu + I_sg
    rho = np.divide(I_sg, I, out=np.zeros_like(I), where=I > 0)
    p = np.divide(s, m, out=np.full_like(s, np.nan), where=np.abs(m) > 1e-12)
    return {"m": m, "s": s, "I_mu": I_mu, "I_sg": I_sg, "I": I, "rho": rho, "p": p}


def h_numeric(mu: np.ndarray, f, du: float = DU, dlog: float = 1e-4) -> np.ndarray:
    """h = d log I / d log alpha 를 alpha=1 에서 중심차분으로."""
    a_p, a_m = np.exp(dlog), np.exp(-dlog)
    I_p = fisher_1d(a_p * mu, f(a_p * mu), du)["I"]
    I_m = fisher_1d(a_m * mu, f(a_m * mu), du)["I"]
    return (np.log(I_p) - np.log(I_m)) / (2.0 * dlog)


def q_profile(mu: np.ndarray, p: np.ndarray, m: np.ndarray, du: float = DU) -> np.ndarray:
    """q = d log p / d log mu = (log p)' / m."""
    lp = np.log(np.abs(p))
    dlp = local_slope(lp, du)
    return np.divide(dlp, m, out=np.zeros_like(dlp), where=np.abs(m) > 1e-12)


def core(idx: np.ndarray, n: int, pad: int = HALF_WIN + 1) -> np.ndarray:
    """가장자리 창 왜곡을 뺀 내부 bin."""
    keep = np.zeros(n, dtype=bool)
    keep[pad:-pad] = True
    return keep & idx


def main() -> int:
    rng = np.random.default_rng(SEED)
    u = np.arange(0.0, 2.0, DU)
    n = u.size
    # 매끈하고 단조롭지 않은 임의 평균궤적 (mu > 0)
    mu = 2.0 + 1.6 * np.exp(-((u - 0.55) ** 2) / (2 * 0.22**2)) + 0.9 * np.exp(-u / 0.7)
    ok_all = np.ones(n, dtype=bool)

    res: dict[str, object] = {"seed": SEED, "checks": []}

    def record(name: str, got: float, want: float, tol: float, note: str) -> None:
        res["checks"].append(
            {
                "name": name,
                "got": round(float(got), 8),
                "want": round(float(want), 8),
                "abs_err": round(abs(float(got) - float(want)), 8),
                "tol": tol,
                "status": "PASS" if abs(float(got) - float(want)) <= tol else "FAIL",
                "note": note,
            }
        )

    # --- C1  순수 멱법칙: h = (2-p)(1-rho) 정확 -----------------------------
    for p0 in (0.0, 0.6, 1.0, 1.4, 2.0):
        f = (lambda pp: (lambda x: 0.7 * x**pp))(p0)
        d = fisher_1d(mu, f(mu))
        keep = core(np.abs(d["m"]) > 0.5, n)
        h = h_numeric(mu, f)
        pred = (2.0 - d["p"]) * (1.0 - d["rho"])
        err = float(np.max(np.abs(h[keep] - pred[keep])))
        record(
            f"C1_powerlaw_p={p0}",
            err,
            0.0,
            TOL_EXACT,
            "s2 = c*mu^p 에서 h = (2-p)(1-rho) 는 정확 (모든 bin 최대오차)",
        )

    # --- C2  극한 복원 1: 상태무관 가법잡음 -> h = 2 (평균반응만의 세계) ------
    f_add = lambda x: np.full_like(x, 0.35)
    d_add = fisher_1d(mu, f_add(mu))
    keep = core(np.abs(d_add["m"]) > 0.5, n)
    record("C2_additive_h", float(np.max(np.abs(h_numeric(mu, f_add)[keep] - 2.0))), 0.0, TOL_EXACT,
           "s2 상수 -> p=0, rho=0, h=2. 공허하지 않음: 예측값 2 와 아래 C3 의 0 이 다르다")
    record("C2_additive_rho", float(np.max(np.abs(d_add["rho"][keep]))), 0.0, TOL_EXACT,
           "가법잡음 세계의 잡음기하 분율 rho = 0")

    # --- C3  극한 복원 2: 일정 CV (s2 ~ mu^2) -> h = 0 (gain 불변 계량) -------
    f_cv = lambda x: 0.09 * x**2
    d_cv = fisher_1d(mu, f_cv(mu))
    keep = core(np.abs(d_cv["m"]) > 0.5, n)
    record("C3_constCV_h", float(np.max(np.abs(h_numeric(mu, f_cv)[keep]))), 0.0, TOL_EXACT,
           "p=2 -> h=0: 신호와 잡음이 같이 커지면 판별도(계량)는 gain 에 불변")

    # --- C4  일반 f: h = (2-p)(1-rho) + 2*rho*q  (해석적 미분으로 정확히) ----
    # mu(u) 와 f 를 닫힌형으로 두고 m, p, q, rho, h 를 해석적으로 만든다.
    A, B = 0.05, 0.30
    f_gen = lambda x: A * x**2 + B * x
    dmu = (
        -1.6 * (u - 0.55) / 0.22**2 * np.exp(-((u - 0.55) ** 2) / (2 * 0.22**2))
        - (0.9 / 0.7) * np.exp(-u / 0.7)
    )
    m_a = dmu / mu
    fv = f_gen(mu)
    fp = 2 * A * mu + B
    p_a = mu * fp / fv
    fpp = 2 * A
    # q = d log p / d log mu = mu * p'(mu) / p,  p(x) = x f'(x)/f(x)
    dp_dmu = (fp + mu * fpp) / fv - mu * fp * fp / fv**2
    q_a = mu * dp_dmu / p_a
    I_mu_a = dmu**2 / fv
    I_sg_a = 0.5 * (p_a * m_a) ** 2
    I_a = I_mu_a + I_sg_a
    rho_a = I_sg_a / I_a
    # h 를 alpha 방향 해석적 극한 대신 고정밀 중심차분(해석적 mu 미분 사용)으로
    def I_alpha(al: float) -> np.ndarray:
        muA = al * mu
        fA = f_gen(muA)
        pA = muA * (2 * A * muA + B) / fA
        return (al * dmu) ** 2 / fA + 0.5 * (pA * m_a) ** 2
    dl = 1e-6
    h_a = (np.log(I_alpha(np.exp(dl))) - np.log(I_alpha(np.exp(-dl)))) / (2 * dl)
    full_a = (2.0 - p_a) * (1.0 - rho_a) + 2.0 * rho_a * q_a
    keep = np.abs(m_a) > 0.5
    record("C4_general_full", float(np.max(np.abs(h_a[keep] - full_a[keep]))), 0.0, 1e-6,
           "일반 상태함수 잡음의 정확식 h=(2-p)(1-rho)+2*rho*q (해석적 미분, 항등식)")
    trunc_bias = float(np.max(np.abs(h_a[keep] - ((2.0 - p_a) * (1.0 - rho_a))[keep])))
    record("C4_trunc_bias", trunc_bias, 0.0, TOL_TRUNC,
           "절단형(q 무시)의 계통편의 상한 = max|2*rho*q|. 카드의 사전등록 계통허용 0.15 안이어야 절단형을 primary 로 쓴다")
    # 국소선형(+-0.15 s) 추정기의 이산화 편의: 측정만 하고 카드 tol 에 반영한다.
    d_g = fisher_1d(mu, f_gen(mu))
    keep_d = core(np.abs(d_g["m"]) > 0.5, n)
    q_d = q_profile(mu, d_g["p"], d_g["m"])
    full_d = (2.0 - d_g["p"]) * (1.0 - d_g["rho"]) + 2.0 * d_g["rho"] * q_d
    res["estimator_discretization_bias_full"] = round(
        float(np.max(np.abs(h_numeric(mu, f_gen)[keep_d] - full_d[keep_d]))), 6)
    res["estimator_discretization_bias_trunc"] = round(
        float(np.max(np.abs(h_numeric(mu, f_gen)[keep_d]
                            - (2.0 - d_g["p"][keep_d]) * (1.0 - d_g["rho"][keep_d])))), 6)

    # --- C5  chart 재척도 불변성 w -> lam*w ----------------------------------
    lam = 7.3
    d_a = fisher_1d(mu, f_gen(mu))
    d_b = fisher_1d(lam * mu, lam**2 * f_gen(mu))
    keep = core(np.abs(d_a["m"]) > 0.5, n)
    record("C5_scale_I", float(np.max(np.abs(d_a["I"][keep] - d_b["I"][keep]))), 0.0, TOL_EXACT,
           "I 는 관측 척도 lam 에 불변 (u 에 대한 Fisher 정보)")
    record("C5_scale_rho", float(np.max(np.abs(d_a["rho"][keep] - d_b["rho"][keep]))), 0.0, TOL_EXACT,
           "rho 불변")
    # p 는 s2 = f(mu) 의 척도변환에서 c 만 바뀌므로 불변
    record("C5_scale_p", float(np.max(np.abs(d_a["p"][keep] - d_b["p"][keep]))), 0.0, TOL_EXACT,
           "p = s/m 불변")

    # --- C6  '평균만 warp/scale' 은 h 를 2 에서 못 움직인다 -------------------
    # 임의 warp u -> u/(1+eps) 와 임의 scale 을 가법 고정잡음 세계에 가해도 h=2.
    eps = 0.25
    mu_w = np.interp(u / (1 + eps), u, mu) * 1.4
    d_w = fisher_1d(mu_w, f_add(mu_w))
    keep = core(np.abs(d_w["m"]) > 0.5, n)
    record("C6_warp_additive_h", float(np.max(np.abs(h_numeric(mu_w, f_add)[keep] - 2.0))), 0.0, TOL_EXACT,
           "동어반복 세계: 평균궤적을 임의로 warp/scale 해도 상태무관 잡음이면 h=2 로 고정")
    record("C6_warp_additive_rho", float(np.max(np.abs(d_w["rho"][keep]))), 0.0, TOL_EXACT,
           "동어반복 세계의 rho = 0: 계량에 평균반응 밖 내용이 없다")

    res["status"] = "PASS" if all(c["status"] == "PASS" for c in res["checks"]) else "FAIL"
    res["n_checks"] = len(res["checks"])
    res["trunc_bias_max"] = round(trunc_bias, 6)
    out = HERE / "result_identity.json"
    out.write_text(json.dumps(res, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(res, ensure_ascii=False, indent=2))
    return 0 if res["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
