"""C1-7: 흔적의 시계는 하나다 — 잠든 동안의 긴 유지는 기록의 되먹임에서 나온다 (전제 C1).

C1-6·C3-6과 §2의 시간의 식(v3)을 본 뒤 세운 새 단계다. v2는 흔적 시계를 깸(τ_w ≤ 45 s)과 잠(τ_h 348–743 s) 두 개로 두었다. 그런데
000056의 단위 1,077개는 짧은 깸과 논렘에서 같은 빠르기로 발화한다(비 중앙 1.00). v3: 각 뉴런의 기록은 자기 발화로 쓰이고 하나의 시간상수
τ로 지워지며, 기록이 끌개 지형을 만든다. 논렘에서는 지형이 상태를 기록 자리로 끌어 그 자리 뉴런이 기록을 다시 쓰므로, 시계를 늦추지
않아도 흔적이 오래 남는다(모형만으로 τ = 45 s, A = 3.5 kT에서 180 s 뒤 정렬이 처음의 0.41–0.49; 되먹임 없는 지수면 0.02).
명제: 000056 논렘 관측 10개(같은 구간 집단의 정렬 감쇠 5칸, 창 자기상관 5개)를, 짧은 깸의 덮임에서 따로 잰 시계 하나
τ = τ_w(C3-6, 45.25 s)로 맞춘다. 시계를 풀어도 유의하게 나아지지 않는다.
식: C1-6과 같다(dθ = −D∂E/∂θ dt + √(2D)dW, τ ḣ = −h + e^{iθ}, E = −A|h|g(θ − arg h), β = 5.2, 잠들 때 어긋남 σ₀). h는 뉴런별 기록장
m(ψ)의 첫 푸리에 성분이다(τ ṁ = −m + f(θ − ψ)).
옮기는 값: τ_w = `c3_6_wake_overwrite.json`의 000056 τ* (다른 관측: 논렘 → 짧은 깸 → 논렘).
생물 기준값: 같은 식의 다른 관측(C3-6의 깸 덮임), Peyrache et al. 2015의 60° 봉우리 폭(β).
자료(원장): dandi-000056. 사건·관측은 C1-5·6과 같다. 적합은 복제 8개(씨앗 1), 판정의 χ²은 적합에 쓰지 않은 씨앗(50)의 복제 32개(C1-6).
적분: `research/ring.py`(Leimkuhler–Matthews, 초당 ≥ 100걸음, 이완율 × 간격 ≤ 0.8). 옛 오일러 적분(C1-1–6)은 가파른 우물에서 2–7 SE 치우친다.
판정(실행 전 고정):
- 사건 ≥ 30
- 정확도: 시계 고정(τ = τ_w) 식의 판정 χ²/자유도 ≤ 2 (관측 10, 자유 A·D·σ₀·ρ, 자유도 6)
- 하나의 시계: 판정 χ²(τ 고정) − 판정 χ²(τ 자유) ≤ 3.84 (자유도 1, p = 0.05)
- 역증명: 시계 고정 식 ≤ 2 < 흔적 없는 식(A = 0)의 판정 χ²/자유도
보고(판정 아님): τ를 C3-6의 95% 구간 끝(16 s, 90.5 s)에 고정한 식, 000939·001699를 C3-5의 τ* 10 s에 고정한 식.
실행 이력: 첫 실행은 000056의 출발점(A 4.0, D 5.07)이 적분 불안정 영역(D·β·A/단계 > 0.5, 비용 10¹²)에 있어 최적화가 움직이지 않았고
(매개변수가 출발값 그대로, 판정 χ²/자유도 4.44로 실패 기록), 기준을 바꾸지 않고 출발 D를 안정 영역 안으로 옮겨 재실행했다. 그 재실행은
결과 전에 멈췄다: 오일러 적분이 이 체제에서 치우친다는 것을 확인했기 때문이다(초당 1,600걸음 대비 최대 6.8 SE). 기준을 바꾸지 않고 검증된
적분(`research/ring.py`)으로 바꿔 실행했다.
"""

import json

import numpy as np

from research import c1_5_common_equation_v2 as c15
from research import c3_2_trace_replication as c32
from research import harness, ring
from research.c1_4_common_trace_time import session_1699
from research.c3_1_sleep_trace import CHI2

ONE_CLOCK = 3.84


def fit(base, fixed, free, start):
    """Fit on one data set (replicas 8), then its χ² under the judging noise (replicas 32, fresh seed)."""
    f = ring.fit_data([base], (), free, fixed, {**start, **fixed})
    return {"fit": f, "judged": ring.judged([base], f, len(free))}


def main():
    c36 = json.loads((harness.RESULTS / "c3_6_wake_overwrite.json").read_text(encoding="utf-8"))["measured"]["dandi_000056"]
    c16r = json.loads((harness.RESULTS / "c1_6_common_equation_precise.json").read_text(encoding="utf-8"))["measured"]
    tau_w, (low, high) = c36["tau_star"], c36["tau_star_interval"]
    rows = harness.registered("dandi-000056")
    rows39 = [r for r in harness.registered("dandi-000939-extract") if r["asset"].endswith(".npz")]
    rows99 = harness.registered("dandi-001699")
    harness.verify(rows + rows39 + rows99)
    base = c15.Data(c15.cohort([c32.session_056(r) for r in rows]), np.random.default_rng(0))
    start = {**c16r["v2_fit"]["params"][0], "A": 4.0}
    one = fit(base, {"tau": tau_w}, ("A", "D", "sigma0"), start)
    free = fit(base, {}, ("A", "D", "sigma0", "tau"), one["fit"]["params"][0])
    none = fit(base, {"A": 0.0, "tau": 1.0}, ("D", "sigma0"), c16r["no_trace_fit"]["params"][0])
    edges = {f"tau_{t:.0f}": fit(base, {"tau": t}, ("A", "D", "sigma0"), one["fit"]["params"][0])["judged"] for t in (low, high)}
    others = {}
    for name, sessions, k in (("dandi_000939", [c32.session_939(r) for r in rows39], 1),
                              ("dandi_001699", [session_1699(r) for r in rows99], 2)):
        b = c15.Data(c15.cohort(sessions), np.random.default_rng(0))
        others[name] = fit(b, {"tau": 10.0}, ("A", "D", "sigma0"), {**c16r["v2_fit"]["params"][k], "A": 4.0})
    j1, jf, jn = one["judged"], free["judged"], none["judged"]
    result = harness.record(
        "c1_7_single_clock", "C1",
        "000056 논렘 관측 10개를 짧은 깸의 덮임에서 따로 잰 흔적 시계 하나(τ_w)로 맞추고, 시계를 풀어도 유의하게 나아지지 않는다: 잠든 "
        "동안의 긴 유지는 두 번째 시계가 아니라 기록의 되먹임에서 나온다",
        "같은 식의 다른 관측: C3-6의 000056 깸 덮임 τ_w. Peyrache et al. 2015: 60° 봉우리 폭(β = 5.2). 실측: DANDI:000056",
        {"events": harness.check(base.events, 30), "accuracy": harness.check(j1["chi2_dof"], high=CHI2),
         "one_clock": harness.check(j1["chi2"] - jf["chi2"], high=ONE_CLOCK)},
        rows + rows39 + rows99,
        proof=harness.reverse("기록의 되먹임(흔적 우물)", j1["chi2_dof"], jn["chi2_dof"], CHI2),
        tau_w=tau_w, tau_w_interval=[low, high], one_clock=one, free_clock=free, no_trace=none, clock_edges=edges,
        others_tau_10=others)
    print(result["verdict"], {k: v["passed"] for k, v in result["checks"].items()}, result["reverse_proof"]["passed"])
    for name, f in (("one clock", one), ("free clock", free), ("no trace", none)):
        print(name, "judged chi2 %.1f (dof-norm %.2f)" % (f["judged"]["chi2"], f["judged"]["chi2_dof"]),
              {k: round(v, 3) for k, v in f["fit"]["params"][0].items()})
    print("edges", {k: round(v["chi2_dof"], 2) for k, v in edges.items()},
          "others tau=10", {k: (round(v["judged"]["chi2_dof"], 2), round(v["fit"]["params"][0]["A"], 2)) for k, v in others.items()})


if __name__ == "__main__":
    main()
