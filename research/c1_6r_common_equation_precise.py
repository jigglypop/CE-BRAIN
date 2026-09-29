"""C1-6r: C1-6을 세션 부트스트랩·전체 공분산으로 다시 잰다 (전제 C1).

C1-6(지지됨)을 본 뒤 세운 새 단계다. 명제·식·관측 30개·매개변수·적분기(오일러 `cefast.ring_trace`)·적합(복제 8개, 씨앗 1)·판정
(적합에 쓰지 않은 씨앗 50의 복제 32개)·기준은 C1-6과 같고 오차만 바꾼다. C1-6의 χ²은 사건 부트스트랩의 대각 표준오차였다.
여기서는 세션을 복원 추출하는 부트스트랩 1000번으로 자료마다 판정 관측 10개(정렬 5칸, 창 자기상관 5개)의 전체 공분산 Σ_d를
재고(`stats.precision` 규칙: 세션 ≥ 24면 Hartlap 보정, 아니면 Ledoit–Wolf 수축), 적합과 판정 모두 χ² = Σ_d r_dᵀΣ_d⁻¹r_d를 쓴다
(r_d = 관측 − ρ_d^{1 또는 2}·모형, ρ_d는 자료마다 가장 좋은 해독 잡음 인자). 적합은 C1-6의 해에서 출발한다.
명제: 같은 논렘 구간 집단(≥ 240 s, 지연 < 240 s)에서 v2 식이 우물 깊이 A와 흔적 시간상수 τ_h 하나씩으로 두 종·세 연구실 자료의
관측 30개를 함께 맞추고, 흔적 항을 빼면(A = 0) 맞추지 못한다.
생물 기준값: 원장 실측 관측 30개, Peyrache et al. 2015의 60° 봉우리 폭(β).
자료(원장): dandi-000056, dandi-000939-extract(첫 home_cage), dandi-001699(야생형). 사건·관측은 C1-5·C1-6과 같다.
판정(실행 전 고정):
- 자료마다 사건 ≥ 30
- 정확도: 새 모의 잡음의 공동 χ²/자유도 ≤ 2 (전체 공분산, 관측 30, 매개변수 11)
- 역증명: 새 모의 잡음에서 v2 ≤ 2 < 흔적 없는 식(A = 0; 자료마다 D, σ₀, ρ)의 공동 χ²/자유도 (전체 공분산)
"""

import json

import numpy as np
from scipy.optimize import minimize_scalar

from research import c1_1_common_equation as c11
from research import c1_2_common_equation_onset as c12
from research import c1_4_common_trace_time as c14
from research import c1_5_common_equation_v2 as c15
from research import c1_6_common_equation_precise as c16
from research import c3_2_trace_replication as c32
from research import harness, stats
from research.c3_1_sleep_trace import CHI2


def measured(events, rng):
    """C1-1's observables (same permutation null and baseline) and their session-bootstrap replicates (rows)."""
    st = c11.statistics(events)
    group = st["session"]
    u = {g: np.concatenate([np.exp(1j * e["theta"]) for e in events if e["session"] == g]).mean() for g in np.unique(group)}
    baseline = np.array([abs(u[g]) ** 2 for g in group])
    shuffled = np.tile(st["pre"], (c11.PERMUTATIONS, 1))
    for g in np.unique(group):
        at = np.flatnonzero(group == g)
        shuffled[:, at] = rng.permuted(shuffled[:, at], axis=1)
    null = ((np.cos(shuffled) @ st["C"] + np.sin(shuffled) @ st["S"]) / st["N"].sum(0)).mean(0)
    value = c11.observe(st, np.ones((1, len(events))), null, baseline)[0]
    return value, c11.observe(st, stats.cluster_bootstrap(group, c11.BOOTSTRAP, rng), null, baseline)


class Data:
    """Observed values of one data set with the session-bootstrap precision matrix over the judged observables."""

    def __init__(self, events, rng):
        self.events = len(events)
        with np.errstate(invalid="ignore", divide="ignore"):
            self.value, boot = measured(events, rng)
        boot = boot[:, c15.INDEX]
        self.precision, self.rule = stats.precision(boot, len({e["session"] for e in events}))
        self.se = np.full(len(self.value), np.nan)
        self.se[c15.INDEX] = boot.std(0)
        self.correlation = np.corrcoef(boot.T)


def chi2(noise_free, value, precision):
    """χ² = rᵀΣ⁻¹r over the judged observables at the best decoding factor ρ (alignment ∝ ρ, autocorrelation ∝ ρ²)."""
    v, m, power = value[c15.INDEX], noise_free[c15.INDEX], c12.POWER[c15.INDEX]
    cost = lambda rho: float((v - rho ** power * m) @ precision @ (v - rho ** power * m))
    best = minimize_scalar(cost, bounds=(1e-3, 1.5), method="bounded")
    return float(best.fun), float(best.x)


class Precise(c16.Precise):
    """C1-6's model of one data set, scored with the full covariance."""

    def __init__(self, base, replicas, seed):
        super().__init__(base, replicas, seed)
        self.precision = base.precision

    def cost(self, p):
        _, _, noise_free = super().cost(p)
        return (*chi2(noise_free, self.value, self.precision), noise_free)


def judged(bases, f, n_free):
    """χ² of fitted parameters under the judging noise (fresh seed, 32 replicas), as in C1-6."""
    parts = [Precise(b, *c16.JUDGE).cost(p) for b, p in zip(bases, f["params"])]
    chi2_ = sum(c for c, _, _ in parts)
    return {"chi2": float(chi2_), "chi2_dof": float(chi2_ / (len(bases) * len(c15.INDEX) - n_free - len(bases))),
            "chi2_each": [float(c) for c, _, _ in parts], "rho": [float(r) for _, r, _ in parts],
            "prediction": [(r ** c12.POWER * nf)[c15.INDEX].tolist() for _, r, nf in parts]}


def load():
    rows = {"dandi_000056": harness.registered("dandi-000056"),
            "dandi_000939": [r for r in harness.registered("dandi-000939-extract") if r["asset"].endswith(".npz")],
            "dandi_001699": harness.registered("dandi-001699")}
    harness.verify([r for x in rows.values() for r in x])
    sessions = {"dandi_000056": [c32.session_056(r) for r in rows["dandi_000056"]],
                "dandi_000939": [c32.session_939(r) for r in rows["dandi_000939"]],
                "dandi_001699": [c14.session_1699(r) for r in rows["dandi_001699"]]}
    return rows, [Data(c15.cohort(sessions[n]), np.random.default_rng(0)) for n in c15.NAMES]


def describe(bases):
    return {"observed": {n: b.value[c15.INDEX].tolist() for n, b in zip(c15.NAMES, bases)},
            "se": {n: b.se[c15.INDEX].tolist() for n, b in zip(c15.NAMES, bases)},
            "correlation": {n: b.correlation.tolist() for n, b in zip(c15.NAMES, bases)},
            "precision_rule": {n: b.rule for n, b in zip(c15.NAMES, bases)}}


def main():
    earlier = json.loads((harness.RESULTS / "c1_6_common_equation_precise.json").read_text(encoding="utf-8"))["measured"]
    rows, bases = load()
    fitting = [Precise(b, *c16.FIT) for b in bases]
    v2 = c15.fit(fitting, ("A", "tau"), ("D", "sigma0"), {}, earlier["v2_fit"]["params"])
    none = c15.fit(fitting, (), ("D", "sigma0"), {"A": 0.0, "tau": 1.0}, earlier["no_trace_fit"]["params"])
    v2_judged, none_judged = judged(bases, v2, 8), judged(bases, none, 6)
    result = harness.record(
        "c1_6r_common_equation_precise", "C1",
        "같은 논렘 구간 집단에서 공통 식 v2가 우물 깊이 A와 흔적 시간상수 τ_h 하나씩으로 두 종·세 연구실 자료의 관측 30개를 함께 "
        "맞추고 흔적 항을 빼면 맞추지 못한다 — C1-6을 세션 부트스트랩·전체 공분산으로 다시 판정",
        "Peyrache et al. 2015 Nat Neurosci 18:569: 60° 봉우리 폭(β = 5.2). 실측 관측 30개: DANDI:000056, DANDI:000939, "
        "DANDI:001699 (Moore et al. 2025)",
        {**{f"events_{n}": harness.check(b.events, 30) for n, b in zip(c15.NAMES, bases)},
         "accuracy": harness.check(v2_judged["chi2_dof"], high=CHI2)},
        [r for x in rows.values() for r in x],
        proof=harness.reverse("흔적 h의 우물(공통 A, τ_h)", v2_judged["chi2_dof"], none_judged["chi2_dof"], CHI2),
        **describe(bases), v2_fit=v2, v2_judged=v2_judged, no_trace_fit=none, no_trace_judged=none_judged)
    print(result["verdict"], {k: v["passed"] for k, v in result["checks"].items()}, result["reverse_proof"]["passed"])
    for name, f, j in (("v2", v2, v2_judged), ("no_trace", none, none_judged)):
        print(name, "fit %.2f judged %.2f" % (f["chi2_dof"], j["chi2_dof"]), [{k: round(v, 3) for k, v in p.items()} for p in f["params"]])


if __name__ == "__main__":
    main()
