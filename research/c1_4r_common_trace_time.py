"""C1-4r: C1-4를 세션 부트스트랩·전체 공분산·동등성 검정으로 다시 잰다 (전제 C1).

C1-4(지지됨)를 본 뒤 세운 새 단계다. 명제·식·자료·사건 집단(논렘 ≥ 240 s, 지연 < 240 s)·순열 보정은 C1-4와 같고 두 곳을 바꾼다.
(1) 오차: 사건이 아니라 세션을 복원 추출하는 부트스트랩 1000번으로 자료마다 지연 칸 5개의 전체 공분산 Σ_d를 재고
(`stats.precision` 규칙), 일반화 최소제곱으로 맞춰 χ² = Σ_d r_dᵀΣ_d⁻¹r_d를 쓴다.
(2) 공통 τ: C1-4의 Δχ² ≤ 5.99는 차이를 보지 못했다는 뜻일 뿐이다. 자료마다 따로 맞춘 τ의 비가 1.5배 안임을 보이는 동등성
검정으로 바꾼다: 세 쌍 모두 세션 부트스트랩 τ 비의 90% 구간이 [1/1.5, 1.5] 안이다(쌍마다 5% 단측 검정 둘. 모든 쌍을 요구하는
교집합-합집합 검정이라 다중 보정이 필요 없다).
명제: 논렘 구간이 240 s 이상인 사건만 쓰고 지연을 240 s 안으로 자르면, 세 자료의 정렬 감쇠를 τ_h 하나의 지수식
a_d(t) = A_d·e^{−t/τ_h}가 함께 맞추고, 자료마다 잰 τ가 서로 1.5배 안에서 같다.
식: 공통 식의 흔적 τ_h ḣ = −h + x. 정렬 a(t) = E[cos(θ(t) − θ_pre)] (C1-4와 같다).
생물 기준값: 문헌에 τ 값이 없어 서로 독립인 세 자료(두 종, 세 연구실)의 일치를 기준으로 삼는다. 1.5배는 C3-2의 일치 기준이다.
자료(원장): dandi-000056, dandi-000939-extract(첫 home_cage), dandi-001699(야생형). C1-4와 같다.
판정(실행 전 고정):
- 자료마다 집단 사건 ≥ 30
- 흔적 존재: 자료마다 첫 칸 정렬이 순열 분포의 99번째 백분위를 넘는다
- 정확도: 공통 τ 지수식의 공동 χ²/자유도 ≤ 2 (전체 공분산, 관측 15, 매개변수 4)
- 공통: 세 쌍 모두 τ 비의 90% 구간 ⊂ [1/1.5, 1.5] (값: 쌍들의 구간이 1에서 가장 멀리 닿는 비 ≤ 1.5)
- 정밀도: 공통 τ의 세션 부트스트랩 97.5%/2.5% ≤ 3
- 역증명: 공통 τ 지수식 ≤ 2 < 흔적 없는 식(a = 0)의 공동 χ²/자유도 (전체 공분산)
보고(판정 아님): 전체 공분산으로 잰 Δχ²(공통 − 자료별)와 자료별 τ의 90% 구간.
"""

from itertools import combinations

import numpy as np
from scipy.optimize import least_squares

from research import c1_4_common_trace_time as c14
from research import c3_2_trace_replication as c32
from research import harness, stats
from research.c3_1_sleep_trace import BOOTSTRAP, CHI2, LAGS, PERMUTATIONS, TOP

K = c14.K


def curve(sessions, seed=0):
    """C1-4's alignment on the first K lag bins (same permutation null) with session-bootstrap replicates."""
    found = [f for f in sessions if f]
    group = np.concatenate([np.full(len(f), g) for g, f in enumerate(found)])
    pre = np.array([p for f in found for p, _, _ in f])
    bins = [(np.digitize(lags, LAGS) - 1, lags, theta) for f in found for _, lags, theta in f]
    n = len(LAGS) - 1
    cos = np.array([np.bincount(b, np.cos(t), n) for b, _, t in bins])
    sin = np.array([np.bincount(b, np.sin(t), n) for b, _, t in bins])
    count = np.array([np.bincount(b, minlength=n) for b, _, _ in bins])
    lag = sum(np.bincount(b, x, n) for b, x, _ in bins)
    at = lambda p, w: ((w * np.cos(p)) @ cos + (w * np.sin(p)) @ sin) / (w @ count)
    rng = np.random.default_rng(seed)
    shuffled = np.tile(pre, (PERMUTATIONS, 1))
    for g in np.unique(group):
        i = np.flatnonzero(group == g)
        shuffled[:, i] = rng.permuted(shuffled[:, i], axis=1)
    with np.errstate(invalid="ignore", divide="ignore"):
        null = at(shuffled, np.ones((1, len(pre))))
        alignment = (at(pre[None], np.ones((1, len(pre))))[0] - null.mean(0))[:K]
        boot = at(pre[None], stats.cluster_bootstrap(group, BOOTSTRAP, rng))[:, :K] - null.mean(0)[:K]
        lag = (lag / count.sum(0))[:K]
    precision, info = stats.precision(boot, len(found))
    return {"events": len(pre), "sessions": len(found), "lag": lag, "alignment": alignment, "boot": boot,
            "se": boot.std(0), "correlation": np.corrcoef(boot.T), "precision": precision, "whiten": stats.whiten(precision),
            "precision_rule": info, "null_top": float(np.percentile(null[:, 0] - null.mean(0)[0], TOP))}


def joint(curves, common=True, alignments=None):
    """C1-4's fit of a_d(t) = A_d·e^{−t/τ} (one τ or one per data set) under each data set's precision matrix."""
    alignments = [c["alignment"] for c in curves] if alignments is None else alignments
    n = len(curves)

    def residual(x):
        tau = np.exp(np.full(n, x[n]) if common else x[n:])
        return np.concatenate([c["whiten"] @ (a - x[d] * np.exp(-c["lag"] / tau[d]))
                               for d, (c, a) in enumerate(zip(curves, alignments))])

    x0 = np.r_[[max(a[0], 0.05) for a in alignments], np.log(300.0) * np.ones(1 if common else n)]
    x = least_squares(residual, x0).x
    chi2 = float(np.sum(residual(x) ** 2))
    return {"amplitude": x[:n].tolist(), "tau": np.exp(x[n:]).tolist(), "chi2": chi2, "chi2_dof": chi2 / (n * K - len(x))}


def analyse(sets):
    curves = [curve(s) for s in sets]
    common, separate = joint(curves), joint(curves, common=False)
    none = sum(float(c["alignment"] @ c["precision"] @ c["alignment"]) for c in curves)
    draws = min(len(c["boot"]) for c in curves)
    each = np.array([[joint([c], alignments=[c["boot"][b]])["tau"][0] for b in range(draws)] for c in curves])
    shared = [joint(curves, alignments=[c["boot"][b] for c in curves])["tau"][0] for b in range(draws)]
    pairs = {f"{i}-{j}": stats.equivalence(each[i] / each[j]) for i, j in combinations(range(len(curves)), 2)}
    keep = ("events", "sessions", "lag", "alignment", "se", "correlation", "precision_rule", "null_top")
    return {"curves": [{k: (c[k].tolist() if isinstance(c[k], np.ndarray) else c[k]) for k in keep} for c in curves],
            "common": common, "separate": separate, "delta_chi2": common["chi2"] - separate["chi2"],
            "none_chi2_dof": none / (len(curves) * K), "tau_interval": np.percentile(shared, [2.5, 97.5]).tolist(),
            "tau_interval_each": np.percentile(each, [5, 95], axis=1).T.tolist(), "equivalence": pairs,
            "spread": max(p["spread"] for p in pairs.values())}


def main():
    rows56 = harness.registered("dandi-000056")
    rows39 = [r for r in harness.registered("dandi-000939-extract") if r["asset"].endswith(".npz")]
    rows99 = harness.registered("dandi-001699")
    harness.verify(rows56 + rows39 + rows99)
    sessions = [[c32.session_056(r) for r in rows56], [c32.session_939(r) for r in rows39],
                [c14.session_1699(r) for r in rows99]]
    r = analyse([c14.cohort(s) for s in sessions])
    names = ("dandi_000056", "dandi_000939", "dandi_001699")
    lo, hi = r["tau_interval"]
    checks = {f"events_{n}": harness.check(c["events"], c14.MIN_EVENTS) for n, c in zip(names, r["curves"])}
    checks |= {f"trace_{n}": harness.check(c["alignment"][0] - c["null_top"], low=0) for n, c in zip(names, r["curves"])}
    checks |= {"accuracy": harness.check(r["common"]["chi2_dof"], high=CHI2),
               "common_tau": harness.check(r["spread"], high=stats.EQUIVALENCE),
               "precision": harness.check(hi / lo, high=c14.SPREAD)}
    result = harness.record(
        "c1_4r_common_trace_time", "C1",
        "논렘 구간이 240 s 이상인 같은 사건 집단으로 재면 세 자료(두 종, 세 연구실)의 정렬 감쇠를 흔적 시간상수 τ_h 하나의 "
        "지수식이 함께 맞추고, 자료마다 잰 τ가 1.5배 안에서 같다 — C1-4를 세션 부트스트랩·전체 공분산·동등성 검정으로 다시 판정",
        "문헌에 τ 값이 없어 서로 독립인 세 자료의 일치를 기준으로 삼는다. 실측: DANDI:000056 (Peyrache et al. 2015), "
        "DANDI:000939, DANDI:001699 (Moore et al. 2025)",
        checks, rows56 + rows39 + rows99,
        proof=harness.reverse("흔적 h (공통 τ_h)", r["common"]["chi2_dof"], r["none_chi2_dof"], CHI2),
        names=list(names), fixed_cohort=r)
    print(result["verdict"], {k: v["passed"] for k, v in checks.items()}, result["reverse_proof"]["passed"])
    print([c["events"] for c in r["curves"]], [c["precision_rule"]["method"] for c in r["curves"]],
          "공통 τ %.0f s (%s), χ²/자유도 %.2f, 자료별 τ %s, τ 비 구간 %s" % (
              r["common"]["tau"][0], np.round(r["tau_interval"]).tolist(), r["common"]["chi2_dof"],
              np.round(r["separate"]["tau"]).tolist(), {k: np.round(v["interval"], 2).tolist() for k, v in r["equivalence"].items()}))


if __name__ == "__main__":
    main()
