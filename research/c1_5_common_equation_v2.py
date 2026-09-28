"""C1-5: 공통 식 v2가 세 자료를 한 흔적 매개변수로 맞춘다 (전제 C1).

C1-2·3·4를 본 뒤 세운 새 단계다. C1-2·3은 모든 논렘 구간을 섞어 쟀고(구간 길이 생존 편향, 4.21) 모든 매개변수를 공통으로 두었다.
v2(§2)는 우물 깊이 A와 잠든 동안의 흔적 유지 τ_h를 공통, 이동도 D를 계의 속성, ρ·σ₀를 관측으로 나눈다.
명제: 같은 논렘 구간 집단(≥ 240 s, 지연 < 240 s)에서 v2 식이 A·τ_h 하나씩으로 세 자료(두 종, 세 연구실)의 정렬 감쇠 5칸과
창 자기상관 5개(자료마다 10개, 모두 30개)를 함께 맞추고, 흔적 항을 빼면(A = 0) 맞추지 못한다.
식 (논렘, C1-2와 같은 적분기): dθ = −D ∂E/∂θ dt + √(2D) dW, 잠든 동안 τ_h ḣ = −h + e^{iθ} (v2의 λ = 1/τ_h),
E = −A|h|·g(θ − arg h), g(x) = e^{β(cos x − 1)}, β = 5.2 (문헌 60° 봉우리), θ(0) = arg h(0) = θ_pre − δ, δ ~ 감싼 정규(σ₀).
머리 입력은 세 자료 모두 넣지 않는다(000939·001699는 잠든 머리 추적이 없다). 관측: 창 방향 = 창 안 θ의 원형 평균 + 해독 잡음(ρ).
매개변수: 공통 A, τ_h / 자료마다 D, σ₀, ρ (모두 11개, 관측 30개, 자유도 19).
생물 기준값: 원장 실측 관측 30개, Peyrache et al. 2015의 60° 봉우리 폭(β).
자료(원장): dandi-000056, dandi-000939-extract(첫 home_cage), dandi-001699(야생형). 사건·창은 C3-2·C1-3과 같고, C1-4처럼
논렘 구간 ≥ 240 s인 사건만 첫 240 s로 자른다. 관측과 오차는 C1-1과 같다(정렬은 세션 안 순열 보정, 자기상관은 세션 평균 벡터를 뺌,
사건 부트스트랩 1000번). 모형은 사건 설계(길이)를 2번 복제해 5 ms 간격으로 적분한다(C1-1).
판정(실행 전 고정):
- 자료마다 사건 ≥ 30
- 정확도: 공동 χ²/자유도 ≤ 2
- 역증명: 공동 χ²/자유도 ≤ 2 < 흔적 없는 식(A = 0; 자료마다 D, σ₀, ρ)의 공동 χ²/자유도
보고(판정 아님): D를 세 자료 공통으로 묶은 식의 χ² 증가(이동도가 계의 속성인지), 자료별 예측과 관측.
실행 이력: 첫 실행에서 v2 적합(공동 χ²/자유도 2.13, 실패)의 χ²이 그 안에 든 D 공통 식보다 2.4 컸다. 최적점에 못 간 것이라 기준을
바꾸지 않고, v2를 D 공통 해에서 출발시키고 단순체를 χ²이 0.1 넘게 줄지 않을 때까지 다시 세우도록 고쳐 재실행했다.
"""

import numpy as np
from scipy.optimize import minimize

from research import c1_1_common_equation as c11
from research import c1_2_common_equation_onset as c12
from research import c1_4_common_trace_time as c14
from research import c3_2_trace_replication as c32
from research import harness
from research.c3_1_sleep_trace import CHI2

SPAN = 240
INDEX = np.r_[np.arange(5), c11.K + np.arange(len(c11.DELTAS))]  # 정렬 5칸 + 자기상관 5개
NAMES = ("dandi_000056", "dandi_000939", "dandi_001699")


def cohort(sessions):
    """C1-1 event dicts of the NREM bouts lasting ≥ 240 s, cut to their first 240 windows (no head input)."""
    return [{"pre": p, "theta": theta[:SPAN], "head": np.nan, "session": g}
            for g, found in enumerate(sessions) if found for p, lags, theta in found if len(theta) >= SPAN]


class Data:
    """Observed values, errors and the simulation design of one data set."""

    def __init__(self, events, rng):
        self.events = len(events)
        with np.errstate(invalid="ignore", divide="ignore"):
            self.value, self.se, _ = c11.measured(events, rng)
        _, self.lengths = c11.design(events)
        self.rel = np.zeros(len(self.lengths))
        self.z = np.random.default_rng(c12.OFFSET_SEED).standard_normal(len(self.lengths))

    def cost(self, p):
        """χ² at the best ρ and the noise-free prediction for parameters p (D, A, tau, sigma0)."""
        with np.errstate(invalid="ignore", divide="ignore"):
            noise_free = c12.model({**p, "As": 0.0}, self.rel, self.lengths, self.z)
        chi2, rho = c12.chi2(noise_free, self.value, self.se, INDEX)
        return chi2, rho, noise_free


def fit(data, common, each, fixed, start, maxiter=2000, restarts=4):
    """Joint Nelder–Mead over log parameters: `common` shared, `each` per data set; returns params, ρ and χ²/dof.
    `start` is one dict or one per data set. The simplex restarts from the best point until χ² stops falling by 0.1."""
    n = len(data)
    starts = start if isinstance(start, list) else [start] * n

    def unpack(x):
        """Free parameters clipped to their bounds; fixed ones as given."""
        clip = lambda names, values: {k: float(np.clip(v, *c12.BOUNDS[k])) for k, v in zip(names, values)}
        own = np.exp(x[len(common):]).reshape(n, len(each))
        return [{**fixed, **clip(common, np.exp(x[:len(common)])), **clip(each, own[d])} for d in range(n)]

    def cost(x):
        ps = unpack(x)
        if any(p["D"] * c11.BETA * p["A"] / c11.SUBSTEPS > c11.STABLE for p in ps):
            return 1e12
        return sum(d.cost(p)[0] for d, p in zip(data, ps))

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
    parts = [d.cost(p) for d, p in zip(data, ps)]
    chi2 = sum(c for c, _, _ in parts)
    dof = n * len(INDEX) - len(x) - n  # 자료마다 ρ 하나
    return {"params": ps, "rho": [r for _, r, _ in parts], "chi2": float(chi2), "chi2_dof": float(chi2 / dof),
            "chi2_each": [float(c) for c, _, _ in parts],
            "prediction": [(r ** c12.POWER * nf)[INDEX].tolist() for _, r, nf in parts]}


def main():
    rows = {"dandi_000056": harness.registered("dandi-000056"),
            "dandi_000939": [r for r in harness.registered("dandi-000939-extract") if r["asset"].endswith(".npz")],
            "dandi_001699": harness.registered("dandi-001699")}
    harness.verify([r for x in rows.values() for r in x])
    sessions = {"dandi_000056": [c32.session_056(r) for r in rows["dandi_000056"]],
                "dandi_000939": [c32.session_939(r) for r in rows["dandi_000939"]],
                "dandi_001699": [c14.session_1699(r) for r in rows["dandi_001699"]]}
    data = [Data(cohort(sessions[name]), np.random.default_rng(0)) for name in NAMES]
    start = {"D": 0.2, "A": 3.0, "tau": 800.0, "sigma0": 1.0}
    shared_d = fit(data, ("A", "tau", "D"), ("sigma0",), {}, start)
    v2 = fit(data, ("A", "tau"), ("D", "sigma0"), {}, shared_d["params"])  # v2는 D 공통 식을 품으므로 그 해에서 출발
    none = fit(data, (), ("D", "sigma0"), {"A": 0.0, "tau": 1.0}, start)
    result = harness.record(
        "c1_5_common_equation_v2", "C1",
        "같은 논렘 구간 집단에서 공통 식 v2가 우물 깊이 A와 흔적 유지 τ_h 하나씩으로 두 종·세 연구실 자료의 정렬 감쇠와 창 자기상관 "
        "30개를 함께 맞추고(이동도 D는 계마다), 흔적 항을 빼면 맞추지 못한다",
        "Peyrache et al. 2015 Nat Neurosci 18:569: 60° 봉우리 폭(β = 5.2). 실측 관측 30개: DANDI:000056, DANDI:000939, "
        "DANDI:001699 (Moore et al. 2025)",
        {**{f"events_{n}": harness.check(d.events, 30) for n, d in zip(NAMES, data)},
         "accuracy": harness.check(v2["chi2_dof"], high=CHI2)},
        [r for x in rows.values() for r in x],
        proof=harness.reverse("흔적 h의 우물(공통 A, τ_h)", v2["chi2_dof"], none["chi2_dof"], CHI2),
        observed={n: d.value[INDEX].tolist() for n, d in zip(NAMES, data)},
        se={n: d.se[INDEX].tolist() for n, d in zip(NAMES, data)},
        events={n: d.events for n, d in zip(NAMES, data)},
        v2=v2, no_trace=none, shared_mobility=shared_d, shared_mobility_gain=shared_d["chi2"] - v2["chi2"])
    print(result["verdict"], {k: v["passed"] for k, v in result["checks"].items()}, result["reverse_proof"]["passed"])
    for name, f in (("v2", v2), ("no_trace", none), ("shared_D", shared_d)):
        print(name, "chi2/dof %.2f" % f["chi2_dof"], [{k: round(v, 3) for k, v in p.items()} for p in f["params"]],
              "rho", np.round(f["rho"], 3).tolist(), "chi2 each", np.round(f["chi2_each"], 1).tolist())


if __name__ == "__main__":
    main()
