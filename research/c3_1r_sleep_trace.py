"""C3-1r: C3-1을 세션 부트스트랩과 전체 공분산으로 다시 잰다 (전제 C3).

C3-1(지지됨)을 본 뒤 세운 새 단계다. 명제·식·자료·사건·창·순열 보정·판정 기준은 C3-1과 같고 오차만 바꾼다.
C3-1의 오차는 사건 부트스트랩의 대각 표준오차였다. 한 세션의 사건은 서로 닮고 한 사건이 여러 지연 칸에 들어가 칸끼리
상관되므로, 대각 χ²는 참 모형의 χ²/자유도를 0.4–0.6으로 낮춘다(합성 검증, `research/stats.py`).
명제: 잠들기 직전 깸의 내부 방향 θ_pre가 뒤이은 논렘의 내부 방향 θ(t)에 남고, 정렬 a(t) = E[cos(θ(t) − θ_pre)]는
흔적 시간상수 τ_h로 지수 감쇠한다: a(t) = A·exp(−t/τ_h). 흔적 없는 식: a(t) = 0.
자료(원장): dandi-000939-extract의 머리방향 세포(저자 분류). 주 검사는 첫 home_cage, 재현은 둘째 home_cage (C3-1과 같다).
오차(바뀐 곳): 세션을 복원 추출하는 부트스트랩 1000번으로 지연 칸 6개의 전체 공분산 Σ를 재고, `stats.precision`의 규칙
(세션 ≥ 2(k + 2)면 Hartlap 보정, 아니면 Ledoit–Wolf 수축)으로 Σ⁻¹을 만든다. 지수식은 일반화 최소제곱으로 맞추고
χ² = rᵀΣ⁻¹r이다. 경계는 C3-1과 같다(A 0–1, τ 1–10⁴ s).
판정(실행 전 고정):
- 사건 ≥ 50, 세션 ≥ 5 (주 검사)
- 흔적 존재: 첫 칸 정렬이 순열 분포의 99번째 백분위를 넘는다
- 정확도: 지수식 χ²/자유도 ≤ 2 (전체 공분산, 자유도 4)
- 역증명: 지수식 ≤ 2 < 흔적 없는 식의 χ²/자유도 (전체 공분산, 자유도 6)
- 재현(둘째 home_cage): 흔적 존재와 역증명 통과
"""

import numpy as np
from scipy.optimize import least_squares

from research import c3_1_sleep_trace as c31
from research import harness, stats


def analyse(pool):
    """C3-1's permutation-corrected alignment, with the exponential fitted under the session-bootstrap precision."""
    rng = np.random.default_rng(0)
    null = np.array([pool.curve(pool.shuffled(rng)) for _ in range(c31.PERMUTATIONS)])
    a = pool.curve() - null.mean(0)
    boot = np.array([pool.curve(weight=w) for w in stats.cluster_bootstrap(pool.group, c31.BOOTSTRAP, rng)])
    boot = boot[np.isfinite(boot).all(1)]  # 긴 지연 칸이 빈 복제는 뺀다
    precision, info = stats.precision(boot, len(np.unique(pool.group)))
    w = stats.whiten(precision)
    lag = np.bincount(pool.bin, pool.lag, len(c31.LAGS) - 1) / np.bincount(pool.bin, minlength=len(c31.LAGS) - 1)
    model = lambda x: x[0] * np.exp(-lag / x[1])
    x = least_squares(lambda x: w @ (a - model(x)), (max(a[0], 1e-3), 60.0), bounds=([0, 1], [1, 1e4])).x
    k = len(a)
    return {"events": len(pool.pre), "sessions": info["clusters"], "lag": lag.tolist(), "alignment": a.tolist(),
            "se": boot.std(0).tolist(), "correlation": np.corrcoef(boot.T).tolist(), "precision": info,
            "first_bin_null_top": float(np.percentile(null[:, 0] - null.mean(0)[0], c31.TOP)),
            "amplitude": float(x[0]), "tau_s": float(x[1]),
            "chi2_trace": float(np.sum((w @ (a - model(x))) ** 2) / (k - 2)), "chi2_none": float(a @ precision @ a / k)}


def main():
    rows = [r for r in harness.registered("dandi-000939-extract") if r["asset"].endswith(".npz")]
    harness.verify(rows)
    sessions = {0: [], 1: []}
    for row in rows:
        phi = c31.preferred(row)
        if len(phi) < 10:
            continue
        for index in sessions:
            loaded = c31.home(row, index)
            if loaded is not None:
                sessions[index].append(c31.events(*loaded, phi))
    first, second = analyse(c31.Pool(sessions[0])), analyse(c31.Pool(sessions[1]))
    result = harness.record(
        "c3_1r_sleep_trace", "C3",
        "잠들기 직전 깸의 내부 방향이 논렘의 현재 상태에 남고, 그 정렬은 흔적 시간상수 τ_h로 지수 감쇠한다 "
        "— C3-1을 세션 부트스트랩·전체 공분산으로 다시 판정",
        "실측: DANDI:000939 생쥐 후구상 머리방향 세포, 홈 케이지 수면 (주 검사 탐색 전, 재현 탐색 뒤)",
        {"events": harness.check(first["events"], 50),
         "sessions": harness.check(sum(1 for s in sessions[0] if s), 5),
         "trace_present": harness.check(first["alignment"][0] - first["first_bin_null_top"], low=0),
         "accuracy": harness.check(first["chi2_trace"], high=c31.CHI2),
         "replication_trace": harness.check(second["alignment"][0] - second["first_bin_null_top"], low=0),
         "replication_reverse": harness.check(min(second["chi2_none"] - c31.CHI2, c31.CHI2 - second["chi2_trace"]), low=0)},
        rows,
        proof=harness.reverse("흔적 h (τ_h > 0)", first["chi2_trace"], first["chi2_none"], c31.CHI2),
        first=first, second=second)
    print(result["verdict"], {k: v["passed"] for k, v in result["checks"].items()}, result["reverse_proof"]["passed"])
    for name, r in (("첫 home_cage", first), ("둘째 home_cage", second)):
        print(name, {k: r[k] for k in ("events", "sessions", "amplitude", "tau_s", "chi2_trace", "chi2_none")}, r["precision"])


if __name__ == "__main__":
    main()
