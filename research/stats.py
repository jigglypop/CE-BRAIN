"""통계 도구: 세션 단위 부트스트랩, 부트스트랩 공분산의 χ², τ 비의 동등성 검정.

옛 단계는 사건 부트스트랩의 대각 오차로 χ² = Σ(r/se)²를 썼다. 한 세션의 사건들은 서로 닮고, 한 사건이 여러 지연 칸에
들어가므로 칸끼리 상관된다. 그래서 세션 단위로 다시 뽑고(`cluster_bootstrap`), 그 복제들의 전체 공분산으로 χ² = rᵀΣ⁻¹r를 쓴다.

정밀 행렬 규칙(`precision`, 합성 검증으로 실데이터 실행 전에 고정): 관측 k개, 세션 G개일 때
- G ≥ 2(k + 2): 전체 부트스트랩 공분산의 역에 Hartlap 보정 (G − k − 2)/G를 곱한다. 세션 G개로 잰 공분산의 역은
  G/(G − k − 2)배 치우치고(Hartlap et al. 2007, A&A 464:399), 부트스트랩 분산은 (G − 1)/G배 작다.
- 그보다 적으면: 상관을 단위 행렬 쪽으로 Ledoit–Wolf 수축한다(Ledoit & Wolf 2004, J Multivar Anal 88:365). 수축 세기는
  복제가 아니라 세션 G개에서 잰 것으로 친다.
합성 검증(`synthetic`, `python -m research.stats`): 지연 칸이 AR(1) 0.7로 상관된 세션 자료에서 참 모형의 χ²/자유도를 본다.
"""

import numpy as np
from scipy.optimize import least_squares

EQUIVALENCE, LEVEL = 1.5, 0.90


def cluster_bootstrap(groups, draws, rng):
    """Event weights (draws × events) of bootstrap replicates that resample whole sessions with replacement."""
    labels, index = np.unique(groups, return_inverse=True)
    picks = rng.integers(0, len(labels), (draws, len(labels)))
    return np.stack([np.bincount(p, minlength=len(labels)) for p in picks]).astype(float)[:, index]


def precision(boot, clusters):
    """Inverse covariance of an estimate from its bootstrap replicates (rows) over `clusters` sessions, and how it was made."""
    boot = boot[np.isfinite(boot).all(1)]
    k = boot.shape[1]
    x = boot - boot.mean(0)
    info = {"clusters": int(clusters), "observables": k, "draws": len(boot)}
    if clusters >= 2 * (k + 2):
        factor = (clusters - k - 2) / clusters
        return factor * np.linalg.inv(x.T @ x / len(x)), {**info, "method": "hartlap", "factor": factor}
    sd = x.std(0)
    z = x / sd
    s = z.T @ z / len(z)
    d2 = np.sum((s - np.eye(k)) ** 2)
    b2 = np.mean(np.sum(z * z, 1) ** 2 - 2 * np.einsum("bi,ij,bj->b", z, s, z) + np.sum(s * s)) / clusters
    shrink = min(b2, d2) / d2 if d2 > 0 else 1.0
    corr = shrink * np.eye(k) + (1 - shrink) * s
    return np.linalg.inv(corr * np.outer(sd, sd)), {**info, "method": "ledoit_wolf", "shrinkage": float(shrink)}


def chi2_cov(r, boot, clusters):
    """χ² = rᵀΣ⁻¹r of residuals r with Σ from bootstrap replicates (see `precision`)."""
    p, _ = precision(boot, clusters)
    return float(r @ p @ r)


def whiten(p):
    """W with |W r|² = rᵀ p r, for least-squares fits under a precision matrix p."""
    return np.linalg.cholesky(p).T


def equivalence(ratios, margin=EQUIVALENCE, level=LEVEL):
    """Two one-sided tests at (1 − level)/2 each: equivalent when the central `level` interval of the bootstrap ratios
    lies inside [1/margin, margin]. `spread` = max(1/low, high) is the farthest the interval reaches from 1."""
    ratios = np.asarray(ratios, float)
    finite = ratios[np.isfinite(ratios)]
    low, high = np.percentile(finite, [50 * (1 - level), 50 * (1 + level)])
    spread = float(max(1 / low, high)) if low > 0 else float("inf")
    return {"interval": [float(low), float(high)], "spread": spread, "passed": spread <= margin,
            "draws": len(finite), "dropped": len(ratios) - len(finite)}


def synthetic(sessions=31, observables=6, per=10, reps=300, draws=1000, correlation=0.7, noise=0.3, session_sd=0.05,
              seed=1):
    """χ²/dof of the true exponential a·e^{−t/τ} (and of a wrong one, τ held at twice the truth) fitted to correlated
    lag bins, under three errors: event-bootstrap diagonal (the old steps), session-bootstrap diagonal, full `precision`."""
    rng = np.random.default_rng(seed)
    lag = np.geomspace(7.5, 400, observables)
    truth = lambda a, tau: a * np.exp(-lag / tau)
    chol = np.linalg.cholesky(correlation ** np.abs(np.subtract.outer(np.arange(observables), np.arange(observables))))
    out = {k: [] for k in ("diagonal_event", "diagonal_session", "full_session")}
    wrong = {k: [] for k in out}
    for _ in range(reps):
        groups = np.repeat(np.arange(sessions), np.maximum(rng.poisson(per, sessions), 1))
        x = (truth(0.2, 150) + (rng.standard_normal((sessions, observables)) @ chol.T * session_sd)[groups]
             + rng.standard_normal((len(groups), observables)) @ chol.T * noise)
        y = x.mean(0)
        event = np.stack([np.bincount(rng.integers(0, len(x), len(x)), minlength=len(x)) for _ in range(draws)])
        session = cluster_bootstrap(groups, draws, rng)
        mean = lambda w: (w @ x) / w.sum(1)[:, None]
        ps = {"diagonal_event": np.diag(1 / mean(event).var(0)), "diagonal_session": np.diag(1 / mean(session).var(0)),
              "full_session": precision(mean(session), sessions)[0]}
        for name, p in ps.items():
            w = whiten(p)
            f = lambda q: w @ (y - truth(q[0], np.exp(q[1])))
            q = least_squares(f, [0.2, np.log(100)]).x
            out[name].append(float(f(q) @ f(q)) / (observables - 2))
            g = lambda q: w @ (y - truth(q[0], 300.0))
            q = least_squares(g, [0.2]).x
            wrong[name].append(float(g(q) @ g(q)) / (observables - 1))
    summary = lambda v: {"mean": float(np.mean(v)), "median": float(np.median(v)), "above_2": float(np.mean(np.array(v) > 2))}
    return {name: {**summary(out[name]), "wrong_passes": float(np.mean(np.array(wrong[name]) <= 2))} for name in out}


if __name__ == "__main__":
    for g, k, per in [(31, 6, 15), (21, 5, 15), (27, 5, 3), (12, 5, 5), (27, 10, 3), (21, 10, 15), (12, 10, 5)]:
        r = synthetic(g, k, per)
        print(f"세션 {g:2d} 관측 {k:2d} 세션당 사건 {per:2d} |",
              " | ".join(f"{n} 평균 {v['mean']:.2f} 중앙 {v['median']:.2f} >2 {v['above_2']:.2f} 틀린 식 통과 {v['wrong_passes']:.2f}"
                         for n, v in r.items()), flush=True)
