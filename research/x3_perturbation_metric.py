"""X3 (탐색·설계 검증, 공리 판정 밖): 광유전 자극 반응은 계량 G를 재고, 동시각 공분산은 재지 못한다.

C4가 막힌 자리(D10): 자발 활동의 동시각 공분산은 지형의 헤시안 역 T·H⁻¹을 잰다(C4-1~3). 계량 G는 상태를 밀었을 때 얼마나
움직이는가, 곧 이동도 G⁻¹이다. 광유전 자극(2026 노벨 생리의학상: Deisseroth, Hegemann, Nagel)은 고른 세포에 힘을 주는 도구라
이것을 직접 잴 수 있다. 이 단계는 실자료가 아니라 합성 계에서, 어떤 실험 예산이면 어떤 추정량이 G를 되찾는지 미리 판정한다.

식. 지형 E = ½xᵀHx 근처의 선형 계(논문 §2.1 식에서 상수 G):

    dx = −(S + Q) H x dt + √(2T S) dB,   S = G⁻¹ (대칭, 이동도), Q = −Qᵀ (흐름 F = −Q∇E),   정상 분포 ∝ e^{−E/T}

세포 j에 짧은 광 펄스(힘 f e_j, 지속 δ ≪ 이완 시간)를 주면 x는 (S + Q) f δ e_j만큼 밀린다. 그래서

    R(t) = e^{−(S+Q)H t}(S + Q),   R(0⁺)의 대칭 부분 = S = G⁻¹, 반대칭 부분 = Q(방향 F),   동시각 공분산 C₀ = T H⁻¹.

관측 y = x + ε, ε ~ N(0, σ²I)(칼슘 영상의 측정 잡음), 표본 간격 Δ.

추정량 (S의 꼴을 척도 없이 비교):
(a) 동시각 공분산: Ŝ_a = Ĉ₀ (C4-1~3의 방법).
(b) 자발 지연 공분산: Φ̂ = Ĉ(Δ)Ĉ₀⁻¹, Â = −log Φ̂ / Δ, Ŝ_b = sym(Â Ĉ₀). 측정 잡음이 Ĉ₀에만 σ²I로 더해져 치우친다.
(c) 자극 반응: 시행마다 자극 직전 관측 y(0⁻)를 재고, 표적은 무작위로 정한다(대조 = 자극 없음). 지연 k = 1…L(L = 5)마다
    y(kΔ)를 [y(0⁻), 표적 원-핫]에 회귀(공분산 분석)해 표적 계수로 R̂(kΔ)를 얻는다. 표적이 무작위라 y(0⁻)의 측정 잡음이
    계수를 치우치지 못하고, y(0⁻)는 시작 상태의 흩어짐만 덜어 낸다. Φ̂ = Σ R̂_{k+1}R̂_kᵀ (Σ R̂_k R̂_kᵀ)⁻¹,
    R̂(0) = 평균_k Φ̂^{−k} R̂(kΔ)(k = 1, 2), Ŝ_c = sym R̂(0), Q̂_c = antisym R̂(0).
    (첫 판은 R̂(Δ), R̂(2Δ)의 시행 평균 차와 Φ̂ = R̂(2Δ)R̂(Δ)⁻¹을 썼다. 기록 없는 시험 실행(계 4개)에서 시작 상태의 흩어짐과
    역행렬이 잡음을 키워 e(Ŝ_c) 0.52였고, 기준은 그대로 두고 추정량만 이것으로 바꿨다. 두 번째 시험 실행에서 대조 500회의
    평균 잡음이 모든 열에 같은 치우침(시행 수와 무관한 바닥 약 5%)을 남겨, 대조 수를 자극 시행 수에 맞췄다.)
오차: e(Ŝ) = min_c ‖cŜ − S‖_F / ‖S‖_F (척도 없음). Q는 같은 척도 c로 ‖cQ̂ − Q‖_F / ‖Q‖_F.

합성 계 (씨앗 20261008부터 20개): 뉴런 n = 10, H의 고유값 0.5–5, S의 고유값 0.2–2(고유벡터는 H와 독립), Q = q·(antisym 무작위)
q는 ‖Q‖ = 0.5‖S‖, T = 1, Δ = 0.1 s(10 Hz 영상). 기본 예산: 표적 10개 × 자극 50회, 대조(빛 없는 가짜 시행)는 자극 시행과 같은 수, 자발 기록은 같은 총 시간(시행 3 s).
측정 잡음 σ는 x의 평균 표준편차의 0.5배(기본)와 1.0배.

판정 기준 (실행 전 고정, 20계의 중앙값):
H7 자극이 계량을 되찾음: σ = 0.5에서 e(Ŝ_c) ≤ 0.25.
H8 동시각 공분산은 계량이 아님: σ = 0.5에서 e(Ŝ_a) ≥ 0.5.
H9 측정 잡음에 강함: σ = 1.0에서 e(Ŝ_c) ≤ 0.30이고 e(Ŝ_b) ≥ e(Ŝ_c) + 0.10.
H10 방향도 잼: σ = 0.5에서 Q 오차 ≤ 0.35, 그리고 Q = 0인 계에서 ‖Q̂_c‖/‖Ŝ_c‖ ≤ 0.10.
보고: 자극 횟수 10·25·50·100·200·400회의 e(Ŝ_c), 광 세기가 세포마다 모르는 배율일 때(옵신 발현 차이) 대칭성으로 열 배율을 되찾은 e(Ŝ_c).

    python -m research.x3_perturbation_metric           실행하고 기록(합성, 원장 자료 없음)
    python -m research.x3_perturbation_metric --quick   계 4개로 빠르게(기록 없음)
"""

from __future__ import annotations

import json
import sys

import numpy as np
from scipy.linalg import expm, logm, solve_continuous_lyapunov

from research import harness

STEP = "x3_perturbation_metric"
N, DT, T_TRIAL, SEED, SYSTEMS = 10, 0.1, 3.0, 20261008, 20
KICKS, SIGMAS, Q_SHARE = 50, (0.5, 1.0), 0.5
BUDGET = (10, 25, 50, 100, 200, 400)


def orthogonal(rng, n):
    q, r = np.linalg.qr(rng.standard_normal((n, n)))
    return q * np.sign(np.diag(r))


def system(rng, flow=True):
    U = orthogonal(rng, N)
    H = U @ np.diag(np.geomspace(0.5, 5, N)) @ U.T
    H = (H + H.T) / 2
    V = orthogonal(rng, N)
    S = V @ np.diag(rng.uniform(0.2, 2, N)) @ V.T
    Q = np.zeros((N, N))
    if flow:
        M = rng.standard_normal((N, N))
        Q = (M - M.T) / 2
        Q *= Q_SHARE * np.linalg.norm(S) / np.linalg.norm(Q)
    A = (S + Q) @ H
    C0 = np.linalg.inv(H)  # T = 1
    assert np.allclose(solve_continuous_lyapunov(A, 2 * S), C0, atol=1e-8)  # 정상 분포가 e^{−E/T}
    phi = expm(-A * DT)
    noise = C0 - phi @ C0 @ phi.T
    return {"H": H, "S": S, "Q": Q, "C0": C0, "phi": phi, "chol": np.linalg.cholesky((noise + noise.T) / 2),
            "c0chol": np.linalg.cholesky(C0)}


def spontaneous(sys_, steps, sigma, rng):
    x = np.empty((steps, N))
    x[0] = sys_["c0chol"] @ rng.standard_normal(N)
    shocks = rng.standard_normal((steps, N)) @ sys_["chol"].T
    for k in range(1, steps):
        x[k] = sys_["phi"] @ x[k - 1] + shocks[k]
    return x + sigma * rng.standard_normal(x.shape)


def evoked(sys_, targets, sigma, rng, gains, lags):
    """Trials with a kick (S + Q)e_target·gain at t = 0 (target −1 = control). Returns y(0⁻) and y(kΔ), k = 1…lags."""
    x = rng.standard_normal((len(targets), N)) @ sys_["c0chol"].T
    before = x + sigma * rng.standard_normal(x.shape)
    kicked = targets >= 0
    x[kicked] += (gains[targets[kicked]][:, None] * (sys_["S"] + sys_["Q"])[:, targets[kicked]].T)
    after = []
    for _ in range(lags):
        x = x @ sys_["phi"].T + rng.standard_normal(x.shape) @ sys_["chol"].T
        after.append(x + sigma * rng.standard_normal(x.shape))
    return before, after


def scale_free_error(estimate, truth):
    c = np.sum(estimate * truth) / np.sum(estimate * estimate)
    return float(np.linalg.norm(c * estimate - truth) / np.linalg.norm(truth)), float(c)


def sym(m):
    return (m + m.T) / 2


LAGS = 5


def response(sys_, kicks, sigma, rng, gains=None):
    gains = np.ones(N) if gains is None else gains
    targets = rng.permutation(np.concatenate([np.repeat(np.arange(N), kicks), np.full(N * kicks, -1)]))
    before, after = evoked(sys_, targets, sigma, rng, gains, LAGS)
    X = np.hstack([np.ones((len(targets), 1)), before, (targets[:, None] == np.arange(N)[None, :]).astype(float)])
    R = []
    for y in after:  # 공분산 분석: 표적 계수 = 그 지연의 반응 열
        coef, *_ = np.linalg.lstsq(X, y, rcond=None)
        R.append(coef[1 + N:].T)
    num = sum(R[k + 1] @ R[k].T for k in range(LAGS - 1))
    den = sum(R[k] @ R[k].T for k in range(LAGS - 1))
    phi = num @ np.linalg.inv(den)
    return (np.linalg.solve(phi, R[0]) + np.linalg.solve(phi @ phi, R[1])) / 2


def symmetric_gains(R0):
    """Unknown per-column gains g_j: choose g to make R0·diag(1/g) most symmetric (Q assumed small), via log-ratio least squares."""
    i, j = np.triu_indices(N, 1)
    ok = (R0[i, j] * R0[j, i]) > 0
    rows, rhs = [], []
    for a, b in zip(i[ok], j[ok]):  # R0_ab/g_b = R0_ba/g_a  →  log g_b − log g_a = log(R0_ab/R0_ba)
        r = np.zeros(N)
        r[b], r[a] = 1, -1
        rows.append(r)
        rhs.append(np.log(R0[a, b] / R0[b, a]))
    rows.append(np.ones(N))
    rhs.append(0.0)
    logg, *_ = np.linalg.lstsq(np.array(rows), np.array(rhs), rcond=None)
    return R0 / np.exp(logg)[None, :]


def one(seed, flow=True):
    rng = np.random.default_rng(seed)
    sys_ = system(rng, flow)
    sd = float(np.sqrt(np.mean(np.diag(sys_["C0"]))))
    steps = int(N * KICKS * T_TRIAL / DT)
    out = {}
    for share in SIGMAS:
        sigma = share * sd
        y = spontaneous(sys_, steps, sigma, rng)
        y = y - y.mean(0)
        C0 = y.T @ y / len(y)
        C1 = y[1:].T @ y[:-1] / (len(y) - 1)
        phi = C1 @ np.linalg.inv(C0)
        A = -np.real(logm(phi)) / DT
        R0 = response(sys_, KICKS, sigma, rng)
        e_c, c = scale_free_error(sym(R0), sys_["S"])
        row = {"a": scale_free_error(C0, sys_["S"])[0], "b": scale_free_error(sym(A @ C0), sys_["S"])[0], "c": e_c,
               "flow_ratio": float(np.linalg.norm((R0 - R0.T) / 2) / np.linalg.norm(sym(R0)))}
        if flow:
            row["q"] = float(np.linalg.norm(c * (R0 - R0.T) / 2 - sys_["Q"]) / np.linalg.norm(sys_["Q"]))
        out[str(share)] = row
    base = SIGMAS[0] * sd
    out["budget"] = {str(k): scale_free_error(sym(response(sys_, k, base, rng)), sys_["S"])[0] for k in BUDGET}
    gains = np.exp(rng.uniform(np.log(0.3), np.log(3), N))
    out["unknown_gain_raw"] = scale_free_error(sym(response(sys_, KICKS, base, rng, gains)), sys_["S"])[0]
    out["unknown_gain_fixed"] = scale_free_error(sym(symmetric_gains(response(sys_, KICKS, base, rng, gains))), sys_["S"])[0]
    return out


def run(systems):
    flow = [one(SEED + i) for i in range(systems)]
    still = [one(SEED + 1000 + i, flow=False) for i in range(systems)]
    med = lambda rows, *keys: float(np.median([_get(r, keys) for r in rows]))
    lo, hi = str(SIGMAS[0]), str(SIGMAS[1])
    summary = {
        "e_a_0.5": med(flow, lo, "a"), "e_b_0.5": med(flow, lo, "b"), "e_c_0.5": med(flow, lo, "c"),
        "e_a_1.0": med(flow, hi, "a"), "e_b_1.0": med(flow, hi, "b"), "e_c_1.0": med(flow, hi, "c"),
        "q_error_0.5": med(flow, lo, "q"), "flow_ratio_when_Q0": med(still, lo, "flow_ratio"),
        "budget": {k: med(flow, "budget", k) for k in map(str, BUDGET)},
        "unknown_gain_raw": med(flow, "unknown_gain_raw"), "unknown_gain_fixed": med(flow, "unknown_gain_fixed"),
        "unknown_gain_fixed_Q0": med(still, "unknown_gain_fixed"),
    }
    verdict = {
        "H7": summary["e_c_0.5"] <= 0.25,
        "H8": summary["e_a_0.5"] >= 0.5,
        "H9": summary["e_c_1.0"] <= 0.30 and summary["e_b_1.0"] >= summary["e_c_1.0"] + 0.10,
        "H10": summary["q_error_0.5"] <= 0.35 and summary["flow_ratio_when_Q0"] <= 0.10,
    }
    return summary, verdict, {"flow": flow, "still": still}


def _get(row, keys):
    for k in keys:
        row = row[k]
    return row


def main(argv):
    if "--quick" in argv:
        summary, verdict, _ = run(4)
        print(json.dumps({"verdict": verdict, "summary": summary}, ensure_ascii=False, indent=1))
        return 0
    commit = harness.sealed(STEP)
    summary, verdict, systems = run(SYSTEMS)
    result = {"step": STEP, "kind": "탐색·설계 검증(합성, 공리 판정 밖)", "claim": __doc__.split("\n")[0], "verdict": verdict,
              "summary": summary, "systems": systems, "data": [],
              "code_sha256": {p.relative_to(harness.HERE).as_posix(): harness.sha256(p) for p in harness.code()},
              "git": commit, "run_at": harness.now().isoformat(timespec="seconds")}
    out = harness.RESULTS / "x" / f"{STEP}.json"
    out.write_text(json.dumps(result, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps({"verdict": verdict, "summary": summary}, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
