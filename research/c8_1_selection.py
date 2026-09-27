"""C8-1: 두 후보 중 하나가 지금의 표현으로 선택된다 (전제 C8).

명제: 논렘 내부 방향을 끄는 두 후보, 잠들기 전 내부 방향 θ_pre(과거)와 잠든 동안의 실제 머리 방향 θ_head(현재)가
90° 이상 떨어져 있을 때, 내부 방향은 둘을 섞은 중간이 아니라 둘 중 하나에 놓인다.
식 (1 s 창의 해독 방향 θ의 분포, 폰미제스 vM, 모든 봉우리에 같은 집중도 κ):
- 선택: w_p·vM(θ_pre) + w_h·vM(θ_head) + (1 − w_p − w_h)·균등
- 섞임(선택 없음): w_m·vM(θ_mid) + (1 − w_m)·균등, θ_mid = 짧은 호의 중간
- 전체: 세 봉우리 + 균등 (무게를 보고한다)
생물 기준값: Kim et al. 2017 (Science 356:849, doi:10.1126/science.aal4835): 방향 표현은 하나이고, 90°·180° 떨어진 두 입력에
봉우리는 중간이 아니라 한쪽으로 도약하며 두 봉우리는 서로 억제한다(국소 흥분·전역 억제).
자료(원장): dandi-000056. 사건·창·머리 방향은 C3-3과 같고, |θ_pre − θ_head| ≥ 90°이고 머리가 추적된 논렘 창만 쓴다.
판정(실행 전 고정):
- 창 ≥ 1000, 사건 ≥ 30
- 선택 우세: 전체식에서 w_p + w_h − w_m의 사건 부트스트랩 1% 백분위 > 0
- 역증명: AIC(선택) − AIC(최선) ≤ 10 < AIC(섞임) − AIC(최선)
"""

import numpy as np
from scipy.optimize import minimize
from scipy.special import i0e

from research import harness
from research import c3_3_restoring as c33

SEPARATION, AIC_MARGIN, BOOT = np.pi / 2, 10.0, 200  # 부트스트랩 200번: 매번 최우 적합
CENTERS = {"selection": ("pre", "head"), "blend": ("mid",), "full": ("pre", "head", "mid")}


def windows(sessions):
    """Decoded direction and the candidate directions of every qualifying NREM window, with its event id."""
    theta, pre, head, owner = [], [], [], []
    for e, ev in enumerate(ev for s in sessions for ev in s):
        gap = np.abs(np.angle(np.exp(1j * (ev["head"] - ev["pre"]))))
        use = np.isfinite(ev["head"]) & (gap >= SEPARATION)
        theta.append(ev["theta"][use])
        pre.append(np.full(use.sum(), ev["pre"]))
        head.append(ev["head"][use])
        owner.append(np.full(use.sum(), e))
    theta, pre, head, owner = map(np.concatenate, (theta, pre, head, owner))
    mid = np.angle(np.exp(1j * pre) + np.exp(1j * head))
    return theta, {"pre": pre, "head": head, "mid": mid}, owner


def density(theta, centers, kappa):
    """von Mises densities of theta around each center (columns)."""
    return np.stack([np.exp(kappa * (np.cos(theta - c) - 1)) / (2 * np.pi * i0e(kappa)) for c in centers], 1)


def fit(theta, centers, weight=None, start=None):
    """Maximum-likelihood weights (softmax, with a uniform component) and one shared concentration."""
    weight = np.ones(len(theta)) if weight is None else weight
    k = len(centers)

    def nll(x):
        w = np.exp(np.r_[x[:k], 0.0])
        w /= w.sum()
        p = density(theta, centers, np.exp(x[k])) @ w[:k] + w[k] / (2 * np.pi)
        return -np.sum(weight * np.log(p))

    x = minimize(nll, np.r_[np.zeros(k), np.log(2.0)] if start is None else start, method="Nelder-Mead",
                 options={"maxiter": 4000, "xatol": 1e-5, "fatol": 1e-6}).x
    w = np.exp(np.r_[x[:k], 0.0])
    return {"weights": (w[:k] / w.sum()).tolist(), "kappa": float(np.exp(x[k])),
            "aic": float(2 * nll(x) + 2 * (k + 1)), "x": x.tolist()}


def analyse(theta, centers, owner, rng):
    fits = {name: fit(theta, [centers[c] for c in names]) for name, names in CENTERS.items()}
    best = min(f["aic"] for f in fits.values())
    events = np.unique(owner)
    margin = []
    for _ in range(BOOT):
        draw = np.bincount(rng.choice(len(events), len(events)), minlength=len(events)).astype(float)
        w = fit(theta, [centers[c] for c in CENTERS["full"]], draw[np.searchsorted(events, owner)],
                fits["full"]["x"])["weights"]
        margin.append(w[0] + w[1] - w[2])
    return {"windows": int(len(theta)), "events": int(len(events)), "fits": fits,
            "delta_aic": {name: f["aic"] - best for name, f in fits.items()},
            "selection_margin": float(fits["full"]["weights"][0] + fits["full"]["weights"][1] - fits["full"]["weights"][2]),
            "selection_margin_p1": float(np.percentile(margin, 1))}


def main():
    rows = harness.registered("dandi-000056")
    harness.verify(rows)
    sessions = [x["events"] for x in map(c33.session_056, rows) if x]
    theta, centers, owner = windows(sessions)
    r = analyse(theta, centers, owner, np.random.default_rng(0))
    result = harness.record(
        "c8_1_selection", "C8",
        "잠들기 전 내부 방향(과거)과 잠든 머리 방향(현재)이 90° 이상 떨어지면, 논렘 내부 방향은 둘을 섞은 중간이 아니라 "
        "둘 중 하나에 놓인다",
        "Kim et al. 2017 Science 356:849 (doi:10.1126/science.aal4835): 방향 표현은 하나이고 90°·180° 떨어진 두 입력에 "
        "봉우리가 한쪽으로 도약한다. 실측: DANDI:000056",
        {"windows": harness.check(r["windows"], 1000), "events": harness.check(r["events"], 30),
         "selection_over_blend": harness.check(r["selection_margin_p1"], low=0)},
        rows, proof=harness.reverse("선택(한 표현)", r["delta_aic"]["selection"], r["delta_aic"]["blend"], AIC_MARGIN),
        **r)
    print(result["verdict"], {k: v for k, v in r.items() if k != "fits"})
    print({k: (np.round(v["weights"], 3).tolist(), round(v["kappa"], 2)) for k, v in r["fits"].items()})


if __name__ == "__main__":
    main()
