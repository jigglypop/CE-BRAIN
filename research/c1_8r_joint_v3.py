"""C1-8r: C1-8을 세션 부트스트랩·전체 공분산으로 다시 잰다 (전제 C1).

C1-8(지지됨)을 본 뒤 세운 새 단계다. 명제·식(v3 기록장)·관측 30개·매개변수 13개·적분(`research/ring.py`)·적합(복제 2개 → 8개,
씨앗 1)·판정(씨앗 50의 복제 32개)·기준은 C1-8과 같고 오차만 바꾼다: C1-6r과 같이 세션을 복원 추출하는 부트스트랩 1000번으로
자료마다 판정 관측 10개의 전체 공분산 Σ_d를 재고(`stats.precision` 규칙), 적합과 판정 모두 χ² = Σ_d r_dᵀΣ_d⁻¹r_d를 쓴다.
적합은 C1-8의 해에서 출발한다.
명제: 같은 논렘 구간 집단(≥ 240 s, 지연 < 240 s)에서 v3 식이 우물 깊이 A 하나로 두 종·세 연구실 자료의 관측 30개(자료마다 정렬 감쇠
5칸과 창 자기상관 5개)를 함께 맞추고, 흔적 항을 빼면(A = 0) 맞추지 못한다. 시계 τ, 이동도 D, 잠들 때 어긋남 σ₀, 해독 잡음 ρ는 자료마다 둔다.
식: dθ = −D∂E/∂θ dt + √(2D)dW, τ ḣ = −h + e^{iθ}, E = −A|h|g(θ − arg h), β = 5.2 (C1-8과 같다).
생물 기준값: 원장 실측 관측 30개, Peyrache et al. 2015의 60° 봉우리 폭(β).
자료(원장): dandi-000056, dandi-000939-extract(첫 home_cage), dandi-001699(야생형). 사건·관측은 C1-5·C1-8과 같다.
판정(실행 전 고정):
- 자료마다 사건 ≥ 30
- 정확도: 판정 공동 χ²/자유도 ≤ 2 (전체 공분산, 자유도 17)
- 역증명: v3 ≤ 2 < 흔적 없는 식(A = 0; 자료마다 D, σ₀, ρ)의 판정 공동 χ²/자유도 (전체 공분산)
보고(판정 아님): A·τ 모두 공통인 식을 같은 오차로 맞춘 판정 χ².
"""

import json

import numpy as np

from research import c1_5_common_equation_v2 as c15
from research import c1_6r_common_equation_precise as c16r
from research import harness, ring
from research.c3_1_sleep_trace import CHI2


class Model(ring.Model):
    """C1-8's ring model of one data set, scored with the full covariance."""

    def __init__(self, base, replicas, seed):
        super().__init__(base, replicas, seed)
        self.precision = base.precision

    def cost(self, p):
        _, _, noise_free = super().cost(p)
        return (*c16r.chi2(noise_free, self.value, self.precision), noise_free)


def fit_data(bases, common, each, fixed, start):
    """C1-8's coarse-to-fine fit (2 replicas, then 8) under the full covariance."""
    coarse = ring.fit([Model(b, 2, ring.FIT[1]) for b in bases], common, each, fixed, start)
    return ring.fit([Model(b, *ring.FIT) for b in bases], common, each, fixed, coarse["params"])


def judged(bases, f, n_free):
    """χ² of fitted parameters under fresh noise (32 replicas, seed 50), as in C1-8."""
    parts = [Model(b, *ring.JUDGE).cost(p) for b, p in zip(bases, f["params"])]
    chi2 = sum(c for c, _, _ in parts)
    return {"chi2": float(chi2), "chi2_dof": float(chi2 / (len(bases) * len(c15.INDEX) - n_free - len(bases))),
            "chi2_each": [float(c) for c, _, _ in parts], "rho": [float(r) for _, r, _ in parts]}


def main():
    earlier = json.loads((harness.RESULTS / "c1_8_joint_v3.json").read_text(encoding="utf-8"))["measured"]
    rows, bases = c16r.load()
    v3 = fit_data(bases, ("A",), ("tau", "D", "sigma0"), {}, earlier["v3_fit"]["params"])
    none = fit_data(bases, (), ("D", "sigma0"), {"A": 0.0, "tau": 1.0}, earlier["no_trace_fit"]["params"])
    shared = fit_data(bases, ("A", "tau"), ("D", "sigma0"), {}, earlier["shared_tau_fit"]["params"])
    j3, jn, js = judged(bases, v3, 10), judged(bases, none, 6), judged(bases, shared, 8)
    result = harness.record(
        "c1_8r_joint_v3", "C1",
        "같은 논렘 구간 집단에서 기록장 식(v3)이 우물 깊이 A 하나로 두 종·세 연구실 자료의 관측 30개를 함께 맞추고(시계 τ·이동도 D는 "
        "자료마다), 흔적 항을 빼면 맞추지 못한다 — C1-8을 세션 부트스트랩·전체 공분산으로 다시 판정",
        "Peyrache et al. 2015 Nat Neurosci 18:569: 60° 봉우리 폭(β = 5.2). 실측 관측 30개: DANDI:000056, DANDI:000939, "
        "DANDI:001699 (Moore et al. 2025)",
        {**{f"events_{n}": harness.check(b.events, 30) for n, b in zip(c15.NAMES, bases)},
         "accuracy": harness.check(j3["chi2_dof"], high=CHI2)},
        [r for x in rows.values() for r in x],
        proof=harness.reverse("기록의 우물(공통 A)", j3["chi2_dof"], jn["chi2_dof"], CHI2),
        **c16r.describe(bases), v3_fit=v3, v3_judged=j3, no_trace_fit=none, no_trace_judged=jn,
        shared_tau_fit=shared, shared_tau_judged=js)
    print(result["verdict"], {k: v["passed"] for k, v in result["checks"].items()}, result["reverse_proof"]["passed"])
    for name, f, j in (("v3", v3, j3), ("no_trace", none, jn), ("shared_tau", shared, js)):
        print(name, "judged %.2f (each %s)" % (j["chi2_dof"], np.round(j["chi2_each"], 1).tolist()),
              [{k: round(v, 3) for k, v in p.items()} for p in f["params"]])


if __name__ == "__main__":
    main()
