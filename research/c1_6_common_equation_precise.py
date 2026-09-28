"""C1-6: 공통 식 v2를 적합에 쓰지 않은 모의 잡음으로 판정한다 (전제 C1).

C1-5를 본 뒤 세운 새 단계다. C1-5(공동 χ²/자유도 1.94, 지지됨)는 사건마다 고정된 난수열 하나(복제 2개)로 모의해 적합했다.
적합된 매개변수에서 적합에 쓰지 않은 난수열로 복제 32개를 모의하면 공동 χ²/자유도가 2.22였다: 최적화가 그 난수열의 우연까지
맞췄다. 명제와 기준은 C1-5와 같고 측정만 정밀하게 한다.
명제: 같은 논렘 구간 집단(≥ 240 s, 지연 < 240 s)에서 v2 식이 우물 깊이 A와 흔적 시간상수 τ_h 하나씩으로 두 종·세 연구실 자료의
관측 30개를 함께 맞추고, 흔적 항을 빼면(A = 0) 맞추지 못한다.
식·관측·매개변수: C1-5와 같다(공통 A·τ_h, 자료마다 D·σ₀·ρ; 머리 입력 없음; β = 5.2).
방법: 적합은 복제 8개(난수 씨앗 1), C1-5의 해에서 출발해 단순체를 수렴까지 다시 세운다. 판정의 χ²은 적합된 매개변수에서 적합에 쓰지
않은 씨앗(50)으로 복제 32개를 모의해 계산한다(모의 잡음이 실측 오차의 약 1/10 아래).
생물 기준값: 원장 실측 관측 30개, Peyrache et al. 2015의 60° 봉우리 폭(β).
자료(원장): dandi-000056, dandi-000939-extract(첫 home_cage), dandi-001699(야생형). 사건·관측은 C1-5와 같다.
판정(실행 전 고정):
- 자료마다 사건 ≥ 30
- 정확도: 새 모의 잡음의 공동 χ²/자유도 ≤ 2 (관측 30, 매개변수 11)
- 역증명: 새 모의 잡음에서 v2 ≤ 2 < 흔적 없는 식(A = 0; 자료마다 D, σ₀, ρ)의 공동 χ²/자유도
"""

import json

import cefast
import numpy as np

from research import c1_1_common_equation as c11
from research import c1_2_common_equation_onset as c12
from research import c1_4_common_trace_time as c14
from research import c1_5_common_equation_v2 as c15
from research import c3_2_trace_replication as c32
from research import harness
from research.c3_1_sleep_trace import CHI2

FIT, JUDGE = (8, 1), (32, 50)  # (복제 수, 난수 씨앗)


class Precise:
    """Observed values of one data set and the v2 model simulated with `replicas` copies and its own noise seed."""

    def __init__(self, base, replicas, seed):
        self.value, self.se, self.events, self.seed = base.value, base.se, base.events, seed
        self.lengths = np.full(base.events * replicas, c15.SPAN, np.int64)
        self.z = np.random.default_rng(seed + 100).standard_normal(len(self.lengths))

    def cost(self, p):
        delta = p["sigma0"] * self.z
        theta = cefast.ring_trace(delta, self.lengths, c11.SPAN, p["D"], p["A"], p["tau"], 0.0, c11.BETA,
                                  c11.SUBSTEPS, self.seed)
        events = [{"pre": d, "theta": row[:c15.SPAN], "head": d, "session": 0} for row, d in zip(theta, delta)]
        with np.errstate(invalid="ignore", divide="ignore"):
            noise_free = c11.observe(c11.statistics(events), np.ones((1, len(events))))[0]
        chi2, rho = c12.chi2(noise_free, self.value, self.se, c15.INDEX)
        return chi2, rho, noise_free


def judged(bases, f, n_free):
    """χ² of fitted parameters under the judging noise (fresh seed, 32 replicas)."""
    parts = [Precise(b, *JUDGE).cost(p) for b, p in zip(bases, f["params"])]
    chi2 = sum(c for c, _, _ in parts)
    return {"chi2": float(chi2), "chi2_dof": float(chi2 / (len(bases) * len(c15.INDEX) - n_free - len(bases))),
            "chi2_each": [float(c) for c, _, _ in parts], "rho": [float(r) for _, r, _ in parts],
            "prediction": [(r ** c12.POWER * nf)[c15.INDEX].tolist() for _, r, nf in parts]}


def main():
    earlier = json.loads((harness.RESULTS / "c1_5_common_equation_v2.json").read_text(encoding="utf-8"))["measured"]
    rows = {"dandi_000056": harness.registered("dandi-000056"),
            "dandi_000939": [r for r in harness.registered("dandi-000939-extract") if r["asset"].endswith(".npz")],
            "dandi_001699": harness.registered("dandi-001699")}
    harness.verify([r for x in rows.values() for r in x])
    sessions = {"dandi_000056": [c32.session_056(r) for r in rows["dandi_000056"]],
                "dandi_000939": [c32.session_939(r) for r in rows["dandi_000939"]],
                "dandi_001699": [c14.session_1699(r) for r in rows["dandi_001699"]]}
    bases = [c15.Data(c15.cohort(sessions[n]), np.random.default_rng(0)) for n in c15.NAMES]
    fitting = [Precise(b, *FIT) for b in bases]
    v2 = c15.fit(fitting, ("A", "tau"), ("D", "sigma0"), {}, earlier["v2"]["params"])
    none = c15.fit(fitting, (), ("D", "sigma0"), {"A": 0.0, "tau": 1.0}, earlier["no_trace"]["params"])
    v2_judged, none_judged = judged(bases, v2, 8), judged(bases, none, 6)
    result = harness.record(
        "c1_6_common_equation_precise", "C1",
        "같은 논렘 구간 집단에서 공통 식 v2가 우물 깊이 A와 흔적 시간상수 τ_h 하나씩으로 두 종·세 연구실 자료의 관측 30개를 함께 "
        "맞추고 흔적 항을 빼면 맞추지 못한다 — 적합에 쓰지 않은 모의 잡음으로 판정",
        "Peyrache et al. 2015 Nat Neurosci 18:569: 60° 봉우리 폭(β = 5.2). 실측 관측 30개: DANDI:000056, DANDI:000939, "
        "DANDI:001699 (Moore et al. 2025)",
        {**{f"events_{n}": harness.check(b.events, 30) for n, b in zip(c15.NAMES, bases)},
         "accuracy": harness.check(v2_judged["chi2_dof"], high=CHI2)},
        [r for x in rows.values() for r in x],
        proof=harness.reverse("흔적 h의 우물(공통 A, τ_h)", v2_judged["chi2_dof"], none_judged["chi2_dof"], CHI2),
        observed={n: b.value[c15.INDEX].tolist() for n, b in zip(c15.NAMES, bases)},
        se={n: b.se[c15.INDEX].tolist() for n, b in zip(c15.NAMES, bases)},
        v2_fit=v2, v2_judged=v2_judged, no_trace_fit=none, no_trace_judged=none_judged)
    print(result["verdict"], {k: v["passed"] for k, v in result["checks"].items()}, result["reverse_proof"]["passed"])
    for name, f, j in (("v2", v2, v2_judged), ("no_trace", none, none_judged)):
        print(name, "fit chi2/dof %.2f judged %.2f" % (f["chi2_dof"], j["chi2_dof"]), "each", np.round(j["chi2_each"], 1).tolist(),
              [{k: round(v, 3) for k, v in p.items()} for p in f["params"]])


if __name__ == "__main__":
    main()
