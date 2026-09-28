"""C1-8: 기록장 식(v3)이 우물 깊이 하나로 세 자료를 맞춘다 (전제 C1).

C1-6·C1-7을 본 뒤 세운 새 단계다. C1-6(세 자료 공동, 지지됨)은 오일러 적분으로 맞췄는데 000056 해(D 5.07)가 적분이 치우치는
가파른 체제에 있었다(4.25). C1-7은 검증된 적분(`research/ring.py`)으로 000056을 시계 하나 45 s, 우물 4.45 kT로 맞췄다. v3에서 시계 τ는
뉴런 기록의 시간상수라 종·계마다 다를 수 있고(C3-5·6: 000056 약 45 s, 000939·001699 약 10 s), 우물 깊이 A(kT 단위)는 식의 공통 상수다.
명제: 같은 논렘 구간 집단(≥ 240 s, 지연 < 240 s)에서 v3 식이 우물 깊이 A 하나로 두 종·세 연구실 자료의 관측 30개(자료마다 정렬 감쇠 5칸과
창 자기상관 5개)를 함께 맞추고, 흔적 항을 빼면(A = 0) 맞추지 못한다. 시계 τ, 이동도 D, 잠들 때 어긋남 σ₀, 해독 잡음 ρ는 자료마다 둔다.
식: dθ = −D∂E/∂θ dt + √(2D)dW, τ ḣ = −h + e^{iθ}(기록장 m의 첫 푸리에 성분), E = −A|h|g(θ − arg h), β = 5.2. 매개변수 13개, 자유도 17.
적분·판정: `research/ring.py`(Leimkuhler–Matthews). 적합은 복제 2개 → 8개(씨앗 1), 판정의 χ²은 적합에 쓰지 않은 씨앗(50)의 복제 32개.
생물 기준값: 원장 실측 관측 30개, Peyrache et al. 2015의 60° 봉우리 폭(β).
자료(원장): dandi-000056, dandi-000939-extract(첫 home_cage), dandi-001699(야생형). 사건·관측은 C1-5와 같다.
판정(실행 전 고정):
- 자료마다 사건 ≥ 30
- 정확도: 판정 공동 χ²/자유도 ≤ 2
- 역증명: v3 ≤ 2 < 흔적 없는 식(A = 0; 자료마다 D, σ₀, ρ)의 판정 공동 χ²/자유도
보고(판정 아님): C1-6의 명제(A·τ 모두 공통)를 같은 엔진으로 맞춘 판정 χ², 자료별 τ와 C1-7·C3-5의 값.
"""

import json

import numpy as np

from research import c1_5_common_equation_v2 as c15
from research import c3_2_trace_replication as c32
from research import harness, ring
from research.c1_4_common_trace_time import session_1699
from research.c3_1_sleep_trace import CHI2


def main():
    c17 = json.loads((harness.RESULTS / "c1_7_single_clock.json").read_text(encoding="utf-8"))["measured"]
    rows = {"dandi_000056": harness.registered("dandi-000056"),
            "dandi_000939": [r for r in harness.registered("dandi-000939-extract") if r["asset"].endswith(".npz")],
            "dandi_001699": harness.registered("dandi-001699")}
    harness.verify([r for x in rows.values() for r in x])
    sessions = {"dandi_000056": [c32.session_056(r) for r in rows["dandi_000056"]],
                "dandi_000939": [c32.session_939(r) for r in rows["dandi_000939"]],
                "dandi_001699": [session_1699(r) for r in rows["dandi_001699"]]}
    bases = [c15.Data(c15.cohort(sessions[n]), np.random.default_rng(0)) for n in c15.NAMES]
    start = [c17["one_clock"]["fit"]["params"][0]] + [c17["others_tau_10"][n]["fit"]["params"][0] for n in c15.NAMES[1:]]
    start = [{**p, "A": 4.0} for p in start]
    v3 = ring.fit_data(bases, ("A",), ("tau", "D", "sigma0"), {}, start)
    none = ring.fit_data(bases, (), ("D", "sigma0"), {"A": 0.0, "tau": 1.0}, [{**p, "A": 0.0} for p in start])
    shared = ring.fit_data(bases, ("A", "tau"), ("D", "sigma0"), {}, [{**p, "tau": 45.0} for p in v3["params"]])
    j3, jn, js = ring.judged(bases, v3, 10), ring.judged(bases, none, 6), ring.judged(bases, shared, 8)
    result = harness.record(
        "c1_8_joint_v3", "C1",
        "같은 논렘 구간 집단에서 기록장 식(v3)이 우물 깊이 A 하나로 두 종·세 연구실 자료의 관측 30개를 함께 맞추고(시계 τ·이동도 D는 "
        "자료마다), 흔적 항을 빼면 맞추지 못한다",
        "Peyrache et al. 2015 Nat Neurosci 18:569: 60° 봉우리 폭(β = 5.2). 실측 관측 30개: DANDI:000056, DANDI:000939, "
        "DANDI:001699 (Moore et al. 2025)",
        {**{f"events_{n}": harness.check(b.events, 30) for n, b in zip(c15.NAMES, bases)},
         "accuracy": harness.check(j3["chi2_dof"], high=CHI2)},
        [r for x in rows.values() for r in x],
        proof=harness.reverse("기록의 우물(공통 A)", j3["chi2_dof"], jn["chi2_dof"], CHI2),
        observed={n: b.value[c15.INDEX].tolist() for n, b in zip(c15.NAMES, bases)},
        se={n: b.se[c15.INDEX].tolist() for n, b in zip(c15.NAMES, bases)},
        v3_fit=v3, v3_judged=j3, no_trace_fit=none, no_trace_judged=jn, shared_tau_fit=shared, shared_tau_judged=js)
    print(result["verdict"], {k: v["passed"] for k, v in result["checks"].items()}, result["reverse_proof"]["passed"])
    for name, f, j in (("v3", v3, j3), ("no_trace", none, jn), ("shared_tau", shared, js)):
        print(name, "judged %.2f (chi2 %.1f, each %s)" % (j["chi2_dof"], j["chi2"], np.round(j["chi2_each"], 1).tolist()),
              [{k: round(v, 3) for k, v in p.items()} for p in f["params"]])


if __name__ == "__main__":
    main()
