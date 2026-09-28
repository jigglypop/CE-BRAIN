"""머리방향 고리 위 공통 식의 빠르고 정확한 엔진 (전제 C1).

`cefast.ring_observe`가 Leimkuhler–Matthews 걸음(θ += b dt + √(2D dt)(ξ_n + ξ_{n+1})/2, 오일러와 같은 비용에 정상 분포 2차 정확도)으로
적분하면서 관측 합을 Rust 안에서 바로 쌓는다. 가파른 우물에서도 이완율 D·β·A × 간격 ≤ 0.8이 되도록 초당 걸음 수를 늘린다(최소 100).
검증(2026-09-29, 000056 오차 단위): 초당 1,600걸음의 정확한 OU 걸음 대비 ρ를 맞춘 모양 오차가 네 체제에서 0.26–0.61 SE로 모의 잡음
수준이다. 옛 `ring_trace`(오일러 초당 200걸음, C1-1–C1-6)는 가파른 우물(D·β·A ≳ 50/s)에서 같은 기준으로 2–7 SE 치우쳤다.
"""

import cefast
import numpy as np
from scipy.optimize import minimize

from research import c1_1_common_equation as c11
from research import c1_2_common_equation_onset as c12
from research import c1_5_common_equation_v2 as c15
from research.c3_1_sleep_trace import LAGS

MIN_STEPS, RATE_STEP, SCHEME, JUDGE, FIT = 100, 0.8, 1, (32, 50), (8, 1)
EDGES, DELTAS = LAGS.astype(float), np.asarray(c11.DELTAS, np.int64)


def steps(p):
    """Steps per second: at least 100, and enough that the steepest well rate times the step stays ≤ 0.8."""
    return int(max(MIN_STEPS, np.ceil(p["D"] * c11.BETA * p["A"] / RATE_STEP)))


def observables(p, offsets, lengths, seed):
    """Noise-free observables in C1-1's layout: alignment per lag bin, autocorrelation per lag, three empty conflict slots."""
    s = cefast.ring_observe(np.asarray(offsets, float), np.asarray(lengths, np.int64), p["D"], p["A"], p["tau"], c11.BETA,
                            steps(p), seed, EDGES, DELTAS, 1, SCHEME)
    k, j = len(EDGES) - 1, len(DELTAS)
    with np.errstate(invalid="ignore", divide="ignore"):
        return np.r_[s[:k] / s[k:2 * k], s[2 * k:2 * k + j] / s[2 * k + j:], np.full(3, np.nan)]


class Model:
    """Observed values of one data set (C1-5 cohort) and the ring model on `replicas` copies of its events, own seed."""

    def __init__(self, base, replicas, seed):
        self.value, self.se, self.events, self.seed = base.value, base.se, base.events, seed
        self.lengths = np.full(base.events * replicas, c15.SPAN, np.int64)
        self.z = np.random.default_rng(seed + 100).standard_normal(len(self.lengths))

    def cost(self, p):
        """χ² at the best decoding factor ρ, ρ, and the noise-free prediction."""
        noise_free = observables(p, p["sigma0"] * self.z, self.lengths, self.seed)
        chi2, rho = c12.chi2(noise_free, self.value, self.se, c15.INDEX)
        return chi2, rho, noise_free


def fit(models, common, each, fixed, start, maxiter=2000, restarts=4):
    """Nelder–Mead over log parameters (`common` shared, `each` per data set), restarting the simplex until χ² stops
    falling by 0.1. `start` is one dict or one per data set. No stability cut is needed: `steps` keeps the well resolved."""
    n = len(models)
    starts = start if isinstance(start, list) else [start] * n

    def unpack(x):
        clip = lambda names, values: {k: float(np.clip(v, *c12.BOUNDS[k])) for k, v in zip(names, values)}
        own = np.exp(x[len(common):]).reshape(n, len(each))
        return [{**fixed, **clip(common, np.exp(x[:len(common)])), **clip(each, own[d])} for d in range(n)]

    cost = lambda x: sum(m.cost(p)[0] for m, p in zip(models, unpack(x)))
    x = np.log([starts[0][k] for k in common] + [s[k] for s in starts for k in each])
    best = cost(x)
    for _ in range(restarts):
        r = minimize(cost, x, method="Nelder-Mead", options={
            "maxiter": maxiter, "xatol": 1e-3, "fatol": 1e-3, "initial_simplex": np.vstack([x, x + 0.7 * np.eye(len(x))])})
        if best - r.fun < 0.1:
            x = r.x if r.fun < best else x
            break
        x, best = r.x, r.fun
    ps = unpack(x)
    parts = [m.cost(p) for m, p in zip(models, ps)]
    chi2 = sum(c for c, _, _ in parts)
    return {"params": ps, "rho": [r for _, r, _ in parts], "chi2": float(chi2),
            "chi2_dof": float(chi2 / (n * len(c15.INDEX) - len(x) - n))}


def judged(bases, f, n_free):
    """χ² of fitted parameters under fresh noise (32 replicas, a seed not used in fitting)."""
    parts = [Model(b, *JUDGE).cost(p) for b, p in zip(bases, f["params"])]
    chi2 = sum(c for c, _, _ in parts)
    return {"chi2": float(chi2), "chi2_dof": float(chi2 / (len(bases) * len(c15.INDEX) - n_free - len(bases))),
            "chi2_each": [float(c) for c, _, _ in parts], "rho": [float(r) for _, r, _ in parts],
            "prediction": [(r ** c12.POWER * nf)[c15.INDEX].tolist() for _, r, nf in parts]}


def fit_data(bases, common, each, fixed, start):
    """Coarse to fine: fit with 2 replicas (a quarter of the cost), then refine from there with FIT replicas."""
    coarse = fit([Model(b, 2, FIT[1]) for b in bases], common, each, fixed, start)
    return fit([Model(b, *FIT) for b in bases], common, each, fixed, coarse["params"])
