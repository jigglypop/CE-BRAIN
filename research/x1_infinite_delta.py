"""X1 (탐색, 공리 판정 밖): 거의 무한차원의 델타 뉴런.

Pattern-Jet(`ce_brain_pattern_jet_20261002`)은 시간척도 2^k인 저역 연쇄의 차이 Δ_k를 K개(1·2·4·8) 썼다. K → ∞로 시간척도를
연속으로 채우면 무엇이 되는지, 그 극한이 유한 K와 같은 기억 길이의 시차(lag) 대조보다 미래를 더 잘 맞추는지 본다.

식. 관측 x_t ∈ R² (AVA, AVB). 시간척도 s의 저역과 델타:

    L_s x_t = a_s L_s x_{t-1} + (1 − a_s) x_t,   a_s = e^{-1/s},   L_s x_{t0} = x_{t0}
    Δ_s x_t = x_t − L_s x_t

연쇄(cascade)의 Δ_k는 부분분수로 {L_s x}의 선형결합이므로 선형 읽기에서는 병렬 Δ_s와 같은 공간이다(D15). 무한차원 델타 뉴런은
log s 위 균등 측도 μ로 s를 연속으로 채운 특징이고, 읽기 무게 w(s)에 가우스 사전분포를 두면 커널 능선 회귀가 된다:

    k(t, t') = x_t·x_{t'} + ∫ Δ_s x_t · Δ_s x_{t'} dμ(log s),   log₂ s ∈ [0, 7]

적분은 log s 위 M점 구적(각 열 1/√M 가중)으로 계산하고 M = 256과 1024의 예측 차이로 극한에 닿았는지 확인한다.

자료: 원장 `celegans-ava-avb-dff`(C. elegans AVA·AVB ΔF/F, 세션 43 × 40점, 0.376 s 간격). 예측 대상 x_{t+h}, h ∈ {1, 2, 4}.
행은 t ≥ 10. 평가는 세션 하나씩 빼는 교차검증, 능선 세기 λ는 훈련 세션 안의 6겹 세션 묶음 교차검증으로 모든 모형에 같은
방식으로 고른다(옛 Pattern-Jet은 λ = 1e-9 고정이라 차원이 큰 모형에 불리하거나 유리할 수 있었다).

비교 모형: current(x_t), lag-L(x_t…x_{t−L}, L ∈ {2, 4, 8, 10}), jet-K(Pattern-Jet처럼 시간척도 2^k인 델타 K개, K ∈ {1, 2, 4, 8}),
jet-M(같은 log s 구간에 M점, M ∈ {8, 32}: 차원을 늘려 가는 길), jet∞(M = 256 구적, 1024로 확인),
jet∞-win10(저역을 t − 10에서 시작해 lag-10과 기억 길이를 맞춘 jet∞).

판정 기준 (실행 전 고정, 부호 검정은 세션 43개의 세션별 RMSE, 양측):
H1 수렴: 세 h 모두에서 |RMSE(jet-M32) − RMSE(jet∞)| / RMSE(jet∞) ≤ 0.02, 그리고 jet∞ 구적 M = 256 대 1024의 예측 상대 차이 ≤ 0.01.
H2 무한차원 이득: jet∞가 jet-K(K ∈ {1, 2, 4, 8}) 중 평균 RMSE가 가장 낮은 것을 이기고(부호 검정 p < 0.05) 이것이 h 셋 중 둘 이상.
H3a 시차 대조: jet∞가 lag-L 중 가장 낮은 것을 이기고(p < 0.05) h 셋 중 둘 이상.
H3b 역증명(같은 기억 길이): jet∞-win10이 lag-10을 이기고(p < 0.05) h 셋 중 둘 이상. H3a가 통과하고 H3b가 실패하면 이득은
    델타 구조가 아니라 기억 길이다.
보고(판정 아님): jet∞ 특징 공분산의 유효 차원 (Σλ)²/Σλ²와 고른 λ에서의 자유도 Σ λ_i/(λ_i + λ).

    python -m research.x1_infinite_delta            원장 자료로 실행하고 기록
    python -m research.x1_infinite_delta --synthetic 합성 자료로 코드만 확인(기록 없음)
"""

from __future__ import annotations

import csv
import json
import math
import sys

import numpy as np

from research import harness

STEP = "x1_infinite_delta"
DATASET = "celegans-ava-avb-dff"
HORIZONS, BURN, LENGTH = (1, 2, 4), 10, 40
LAGS, JETS, DENSE, LOG2_S = (2, 4, 8, 10), (1, 2, 4, 8), (8, 32), (0.0, 7.0)
M, M_CHECK = 256, 1024
LAMBDAS = np.logspace(-6, 2, 17)
INNER, SEED = 6, 20261008


def load(file):
    sessions = {}
    with open(file, encoding="utf-8") as stream:
        for r in csv.DictReader(stream):
            sessions.setdefault(r["filename"], {"AVA": [], "AVB": []})[r["neuron"]].append((float(r["timepoint"]), float(r["dFF"])))
    out = []
    for name, s in sorted(sessions.items()):
        a, b = sorted(s["AVA"]), sorted(s["AVB"])
        if len(a) == len(b) == LENGTH and all(abs(p[0] - q[0]) < 1e-9 for p, q in zip(a, b)):
            out.append(np.array([[p[1], q[1]] for p, q in zip(a, b)]))
    return out


def lowpass(x, s, start=0):
    """L_s x with the filter started at index `start` (L_s x_start = x_start); rows before start are copies of x."""
    a, y = math.exp(-1.0 / s), x.astype(float).copy()
    for t in range(start + 1, len(x)):
        y[t] = a * y[t - 1] + (1 - a) * x[t]
    return y


def features(x, kind, size=None, t=None):
    """Feature vector rows for times t (array). kind: current | lag | jet | inf | inf_win."""
    rows = []
    if kind in ("jet", "inf"):
        scales = 2.0 ** np.arange(size) if kind == "jet" else 2.0 ** np.linspace(*LOG2_S, size)
        deltas = [x - lowpass(x, s) for s in scales]
        weight = 1.0 if kind == "jet" else 1.0 / math.sqrt(size)
    for i in t:
        f = [x[i]]
        if kind == "lag":
            f += [x[i - k] for k in range(1, size + 1)]
        elif kind in ("jet", "inf"):
            f += [weight * d[i] for d in deltas]
        elif kind == "inf_win":
            seg = x[i - BURN:i + 1]
            scales = 2.0 ** np.linspace(*LOG2_S, size)
            f += [(seg[-1] - lowpass(seg, s)[-1]) / math.sqrt(size) for s in scales]
        rows.append(np.concatenate(f))
    return np.array(rows)


def design(sessions, kind, size, h):
    t = np.arange(BURN, LENGTH - h)
    X = [features(x, kind, size, t) for x in sessions]
    Y = [x[t + h] for x in sessions]
    return X, Y


class Ridge:
    """Ridge on columns standardized with training statistics; all λ from one SVD. λ is relative to mean squared singular value."""

    def __init__(self, X, Y, scale_free):
        self.mx, self.sx = X.mean(0), X.std(0)
        self.sx[self.sx == 0] = 1
        if scale_free:  # 구적 가중을 지키려면 열마다 같은 척도로 나눈다
            self.sx[:] = X.std()
        self.my = Y.mean(0)
        Z = (X - self.mx) / self.sx
        self.U, self.s, Vt = np.linalg.svd(Z, full_matrices=False)
        self.V, self.UtY = Vt.T, self.U.T @ (Y - self.my)
        self.unit = float(np.mean(self.s ** 2)) if len(self.s) else 1.0

    def predict(self, X, lam):
        d = self.s / (self.s ** 2 + lam * self.unit)
        W = self.V @ (d[:, None] * self.UtY)
        return self.my + ((X - self.mx) / self.sx) @ W


def rmse(P, Y):
    return float(np.sqrt(np.mean((P - Y) ** 2)))


def choose(X, Y, scale_free, rng):
    """λ by 6-fold grouped CV over training sessions."""
    folds = np.array_split(rng.permutation(len(X)), INNER)
    errors = np.zeros(len(LAMBDAS))
    for fold in folds:
        held = set(fold.tolist())
        tr = [i for i in range(len(X)) if i not in held]
        model = Ridge(np.vstack([X[i] for i in tr]), np.vstack([Y[i] for i in tr]), scale_free)
        Xv, Yv = np.vstack([X[i] for i in fold]), np.vstack([Y[i] for i in fold])
        errors += [np.sum((model.predict(Xv, lam) - Yv) ** 2) for lam in LAMBDAS]
    return float(LAMBDAS[int(np.argmin(errors))])


def evaluate(sessions, kind, size, h, keep=False):
    """Per-session held-out RMSE (leave one session out), chosen λ, and optionally the held-out predictions."""
    X, Y = design(sessions, kind, size, h)
    scale_free = kind in ("inf", "inf_win")
    rng = np.random.default_rng(SEED)
    errors, lams, preds = [], [], []
    for out in range(len(X)):
        idx = [i for i in range(len(X)) if i != out]
        Xt, Yt = [X[i] for i in idx], [Y[i] for i in idx]
        lam = choose(Xt, Yt, scale_free, rng)
        model = Ridge(np.vstack(Xt), np.vstack(Yt), scale_free)
        P = model.predict(X[out], lam)
        errors.append(rmse(P, Y[out]))
        lams.append(lam)
        preds.append(P)
    return {"errors": errors, "mean": float(np.mean(errors)), "lambda_median": float(np.median(lams)),
            **({"predictions": preds} if keep else {})}


def sign_test(a, b):
    """Two-sided sign test that a < b per session. Returns wins, n, p."""
    wins = sum(x < y for x, y in zip(a, b))
    n = sum(x != y for x, y in zip(a, b))
    m = min(wins, n - wins)
    p = min(1.0, 2 * sum(math.comb(n, i) for i in range(m + 1)) / 2 ** n) if n else 1.0
    return {"wins": int(wins), "n": int(n), "p": float(p)}


def spectrum(sessions, h, lam):
    """Effective dimension and degrees of freedom of the jet∞ features pooled over sessions."""
    X, _ = design(sessions, "inf", M, h)
    Z = np.vstack(X)
    Z = (Z - Z.mean(0)) / Z.std()
    ev = np.clip(np.linalg.eigvalsh(Z.T @ Z / len(Z)), 0, None)[::-1]
    unit = float(np.mean(ev))
    return {"participation_ratio": float(ev.sum() ** 2 / (ev ** 2).sum()),
            "dof_at_lambda": float(np.sum(ev / (ev + lam * unit))),
            "top_eigen_share": [float(v) for v in (np.cumsum(ev) / ev.sum())[:8]],
            "feature_dim": int(Z.shape[1])}


def run(sessions):
    per_h = []
    for h in HORIZONS:
        models = {"current": evaluate(sessions, "current", 0, h)}
        models.update({f"lag-{L}": evaluate(sessions, "lag", L, h) for L in LAGS})
        models.update({f"jet-{K}": evaluate(sessions, "jet", K, h) for K in JETS})
        models.update({f"jet-M{n}": evaluate(sessions, "inf", n, h) for n in DENSE})
        models["jet∞"] = evaluate(sessions, "inf", M, h, keep=True)
        models["jet∞-win10"] = evaluate(sessions, "inf_win", M, h)
        check = evaluate(sessions, "inf", M_CHECK, h, keep=True)
        a = np.vstack(models["jet∞"].pop("predictions"))
        b = np.vstack(check.pop("predictions"))
        quad = float(np.sqrt(np.mean((a - b) ** 2)) / np.sqrt(np.mean(b ** 2)))
        inf = models["jet∞"]
        best_jet = min((f"jet-{K}" for K in JETS), key=lambda k: models[k]["mean"])
        best_lag = min((f"lag-{L}" for L in LAGS), key=lambda k: models[k]["mean"])
        per_h.append({
            "horizon": h,
            "mean_rmse": {k: v["mean"] for k, v in models.items()},
            "lambda_median": {k: v["lambda_median"] for k, v in models.items()},
            "H1_gap_M32": abs(models[f"jet-M{DENSE[-1]}"]["mean"] - inf["mean"]) / inf["mean"],
            "H1_quadrature": quad,
            "H2": {"against": best_jet, **sign_test(inf["errors"], models[best_jet]["errors"])},
            "H3a": {"against": best_lag, **sign_test(inf["errors"], models[best_lag]["errors"])},
            "H3b": sign_test(models["jet∞-win10"]["errors"], models["lag-10"]["errors"]),
            "spectrum": spectrum(sessions, h, inf["lambda_median"]),
            "per_session": {k: v["errors"] for k, v in models.items()},
        })
    verdict = {
        "H1": all(r["H1_gap_M32"] <= 0.02 and r["H1_quadrature"] <= 0.01 for r in per_h),
        "H2": sum(r["H2"]["p"] < 0.05 and r["H2"]["wins"] > r["H2"]["n"] / 2 for r in per_h) >= 2,
        "H3a": sum(r["H3a"]["p"] < 0.05 and r["H3a"]["wins"] > r["H3a"]["n"] / 2 for r in per_h) >= 2,
        "H3b": sum(r["H3b"]["p"] < 0.05 and r["H3b"]["wins"] > r["H3b"]["n"] / 2 for r in per_h) >= 2,
    }
    return per_h, verdict


def synthetic(n=43, seed=1):
    """Two coupled leaky units driven by slow and fast noise: only for checking the code runs."""
    rng = np.random.default_rng(seed)
    out = []
    for _ in range(n):
        x, slow = np.zeros((LENGTH, 2)), np.zeros(2)
        for t in range(1, LENGTH):
            slow = 0.95 * slow + 0.1 * rng.standard_normal(2)
            x[t] = 0.6 * x[t - 1] + slow + 0.05 * rng.standard_normal(2)
        out.append(x)
    return out


def main(argv):
    if "--synthetic" in argv:
        per_h, verdict = run(synthetic())
        print(json.dumps({"verdict": verdict, "mean_rmse": [r["mean_rmse"] for r in per_h]}, ensure_ascii=False, indent=1))
        return 0
    commit = harness.sealed(STEP)
    rows = harness.registered(DATASET)
    harness.verify(rows)
    sessions = load(harness.path(rows[0]))
    per_h, verdict = run(sessions)
    run_at = harness.now()
    result = {"step": STEP, "kind": "탐색(공리 판정 밖)", "claim": __doc__.split("\n")[0], "verdict": verdict,
              "n_sessions": len(sessions), "results": per_h,
              "data": [{k: r[k] for k in ("dataset", "version", "asset", "sha256")} for r in rows],
              "code_sha256": {p.relative_to(harness.HERE).as_posix(): harness.sha256(p) for p in harness.code()},
              "git": commit, "run_at": run_at.isoformat(timespec="seconds")}
    out = harness.RESULTS / "x" / f"{STEP}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps({"verdict": verdict, "results": [{k: v for k, v in r.items() if k != "per_session"} for r in per_h]},
                     ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
