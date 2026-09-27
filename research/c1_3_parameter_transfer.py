"""C1-3: 공통 식의 계량과 흔적 우물은 다른 연구실·종으로 옮겨 간다 (전제 C1).

C1-2를 본 뒤 세운 새 단계다. C1-2에서 두 생쥐 자료(000056, 000939)의 고리 이동도 D(0.144·0.195 rad²/s)와 흔적 우물 깊이
A(3.29·2.55 kT)가 비슷했고 흔적 시간 τ_h만 달랐다. 이것을 아직 보지 않은 자료로 판정한다.
명제: C1-2의 공통 식(머리 입력 없음)에서 D와 A를 두 자료 적합값의 기하평균으로 고정하고 τ_h·σ₀·ρ만 맞춰도, 다른 연구실·다른
종(쥐, 야생형)의 수면 머리방향 기록의 정렬 감쇠 6칸과 창 자기상관 5개를 맞춘다. D와 A를 자유로 풀어도 유의하게 나아지지 않는다.
식: C1-2와 같다. dθ = −D∂E/∂θ dt + √(2D) dW, τ_h ḣ = −h + e^{iθ}, E = −A|h|·g(θ − arg h), β = 5.2, 잠들 때 어긋남 σ₀.
옮기는 값: `research/results/c1_2_common_equation_onset.json`의 두 적합(000056 full, 000939 replication)의 기하평균.
생물 기준값: 원장 실측 관측 11개, Peyrache et al. 2015의 60° 봉우리 폭(β), 두 생쥐 자료에서 옮긴 D·A.
자료(원장): dandi-001699 (Moore et al. 2025, 쥐 후구상, 야생형 세션만; C1-1·2와 다른 연구실·종·나이). 방향 세포는 000056과 같이
탐색 중 조율곡선(평균 벡터 길이 ≥ 0.3, 최고 발화 ≥ 1 Hz)으로 고르고, 방향 세포 ≥ 10인 세션만 쓴다. 사건은 C3-2와 같다
(깸 ≥ 10 s 바로 뒤 논렘, 1 s 창, 첫 480 s). 관측과 오차는 C1-1과 같다.
판정(실행 전 고정):
- 세션 ≥ 5, 사건 ≥ 50
- 정확도: 옮긴 식의 χ²/자유도 ≤ 2 (관측 11, 매개변수 τ_h·σ₀·ρ)
- 이전: χ²(옮긴 식) − χ²(D·A도 자유) ≤ 5.99 (자유도 2, p = 0.05)
- 역증명: 옮긴 식 ≤ 2 < 흔적 없는 식(A = 0; D·σ₀·ρ 자유)의 χ²/자유도
"""

import json

import numpy as np

from research import c1_1_common_equation as c11
from research import c1_2_common_equation_onset as c12
from research import c3_2_trace_replication as c32
from research import c3_3_restoring as c33
from research import harness, store
from research.c4_1_metric_hd import GRID, tuning

SOURCE = harness.HERE / "results/c1_2_common_equation_onset.json"
TRANSFER_GAIN = 5.99


def transferred():
    """Geometric means of D and A over the two C1-2 fits."""
    r = json.loads(SOURCE.read_text(encoding="utf-8"))
    fits = (r["measured"]["full"]["params"], r["measured"]["replication"]["params"])
    return {k: float(np.sqrt(fits[0][k] * fits[1][k])) for k in ("D", "A")}


def session(row, g):
    """Sleep events of one wild-type session with ≥ 10 head-direction cells, or []."""
    s = store.load(row)
    t, angle = s.series("head")
    angle = np.mod(angle, 2 * np.pi)
    f = tuning(*c32.windows(s, t, angle, [(t[0], t[-1])]))
    hd = (np.abs(f @ np.exp(1j * GRID)) / f.sum(1) >= c32.R_HD) & (f.max(1) >= c32.PEAK_HD)
    if hd.sum() < c32.MIN_CELLS:
        return []
    events = c33.events(s.units(hd), np.angle(f[hd] @ np.exp(1j * GRID)), "sleep_stages", "wake", "nrem")
    return [{"pre": e["pre"], "theta": e["theta"], "head": np.nan, "session": g} for e in events]


def main():
    rows = harness.registered("dandi-001699")
    harness.verify(rows)
    per = [session(r, g) for g, r in enumerate(rows)]
    events = [e for x in per for e in x]
    value, se, _ = c11.measured(events, np.random.default_rng(0))
    lengths = c11.design(events)[1]
    rel = np.zeros(len(lengths))
    fixed = transferred()
    start = {**fixed, "tau": 300.0, "sigma0": 1.0}
    index = c12.SLEEP_ONLY
    moved = c12.fit(value, se, rel, lengths, ("tau", "sigma0"), {**fixed, "As": 0.0}, start, index)
    free = c12.fit(value, se, rel, lengths, ("D", "A", "tau", "sigma0"), {"As": 0.0}, start, index)
    none = c12.fit(value, se, rel, lengths, ("D", "sigma0"), {"A": 0.0, "tau": 1.0, "As": 0.0}, start, index)
    raw = lambda f, k: f["chi2_dof"] * (len(index) - k - 1)
    gain = raw(moved, 2) - raw(free, 4)
    result = harness.record(
        "c1_3_parameter_transfer", "C1",
        "공통 식의 고리 이동도 D와 흔적 우물 깊이 A를 두 생쥐 자료에서 옮겨 고정하고 τ_h·σ₀·ρ만 맞춰도 다른 연구실·종(쥐)의 "
        "수면 정렬 감쇠와 창 자기상관을 맞추고, D·A를 풀어도 유의하게 나아지지 않는다",
        "C1-2의 두 생쥐 적합(DANDI:000056, 000939)에서 옮긴 D·A, Peyrache et al. 2015의 봉우리 폭(β). 실측: DANDI:001699 야생형",
        {"sessions": harness.check(sum(1 for x in per if x), 5), "events": harness.check(len(events), 50),
         "accuracy": harness.check(moved["chi2_dof"], high=c11.CHI2),
         "transfer": harness.check(gain, high=TRANSFER_GAIN)},
        rows, proof=harness.reverse("흔적 h의 우물", moved["chi2_dof"], none["chi2_dof"], c11.CHI2),
        transferred=fixed, observed=value[index].tolist(), se=se[index].tolist(),
        moved=moved, free=free, no_trace=none, chi2_gain_from_freeing=float(gain))
    print(result["verdict"], "세션", sum(1 for x in per if x), "사건", len(events), "| 옮긴 값", {k: round(v, 3) for k, v in fixed.items()})
    print("관측", np.round(value[index], 3).tolist(), "\n오차", np.round(se[index], 3).tolist())
    for name, f in (("옮긴 식", moved), ("D·A 자유", free), ("흔적 없음", none)):
        print(name, {k: round(v, 3) for k, v in f["params"].items()}, "ρ %.3f χ²/자유도 %.2f" % (f["rho"], f["chi2_dof"]))
        print("   예측", np.round(np.array(f["prediction"])[index], 3).tolist())
    print("풀어서 얻는 χ² 이득 %.2f (기준 ≤ %.2f)" % (gain, TRANSFER_GAIN))


if __name__ == "__main__":
    main()
