"""X2 (탐색, 공리 판정 밖): 빠른 교사(빛)와 느린 전도(전기) — 교사 지연이 예측 학습의 속도 한계를 정하는가.

물리 배경(문헌의 대략값, 판정에 쓰지 않음): 조직 속 빛은 약 2×10⁸ m/s라 1 cm를 수십 ps에 지나고, 광유전 교사 신호의 지연은
빛이 아니라 옵신 동역학(ChR2 열림 약 1 ms, 닫힘 약 10 ms)이 정한다. 전기 신호는 축삭 전도 0.5–100 m/s와 시냅스 지연 약 1 ms라
1–10 cm에 수 ms–수십 ms가 걸린다. 그래서 광유전 교사는 전기로 전도되는 교사보다 갱신 간격 단위로 몇 배에서 수십 배 빨리 도착한다.

모형. 학습기는 지금까지의 관측으로 다음 값을 예측한다: ŷ_t = w·φ_t, 목표 y_t = x_{t+1}, φ_t = [1, x_t, Δ_{2^k} x_t (k < 8)]
(X1의 jet-8). 오차가 시냅스에 닿는 데 교사 지연 D 갱신 간격이 걸리면 무게 갱신은 지연 LMS다:

    w_{t+1} = w_t + μ e_{t−D} φ_{t−D},   e_{t−D} = y_{t−D} − w_{t−D}·φ_{t−D}          (빛: D = 0, 전기: D > 0)

평균 무게의 고유 모드는 v_{n+1} = v_n − μλ v_{n−D}이고 이것이 안정한 조건은 μλ < 2 sin(π / (2(2D + 1)))이다(지연 차분식의
고전 결과). 그래서 쓸 수 있는 최대 학습률은 D가 크면 약 π / ((2D + 1) λ)로 줄고, 학습 시간은 2D + 1에 비례해 늘어난다.
보정 팔(MDLMS, Kabal 1983): 늦게 온 목표 y_{t−D}로 오차를 지금 무게로 다시 계산한다(e' = y_{t−D} − w_t·φ_{t−D}). 이러면 지연
교사도 D = 0의 한계를 되찾아야 한다. 즉 속도 한계는 "교사가 늦다"가 아니라 "낡은 무게로 계산한 오차"에서 온다는 예측이다.

자료: 원장 `celegans-ava-avb-dff`, 세션 43개를 이름 순서로 이은 흐름(세션 경계에서 특징은 새로 시작). 앞 10세션은 특징 정규화와
μ 고르기에만 쓰고 점수는 나머지 33세션의 순차(갱신 전) 예측 오차다.

판정 기준 (실행 전 고정):
H4 지연이 학습률 한계를 낮춘다: μ*(D)가 D = 0, 1, 2, 4, 8에서 엄격히 줄고 μ*(8)/μ*(0) ≤ 1/1.5.
    μ*는 μ 격자(로그 400점)에서 흐름 끝까지 |w|가 10⁶을 넘지 않은 가장 큰 값.
    (합성 확인에서 D = 0의 한계는 평균 모드 λ_max가 아니라 표본 하나의 이득 μ‖φ‖²가 정했고, 비 μ*(D)/μ*(0)는 sin 법칙
    (특징이 한 방향으로 오래 머물 때)보다 느리게 줄었다. 그래서 sin 법칙과 멱 지수 γ in μ* ∝ (2D+1)^(−γ)는 보고로 둔다:
    γ = 1이면 평균 모드 법칙, γ = 0이면 지연 무관.)
H5 빠른 교사의 이득: 앞 10세션으로 D마다 μ를 고른 뒤, 33세션 순차 RMSE에서 D = 0이 D = 8을 세션 부호 검정 p < 0.05로 이기고,
    평균 순차 RMSE가 D = 0, 1, 2, 4, 8 순으로 줄지 않는다(이웃 사이 0.5% 하락까지 허용).
H6 보정이 한계를 되찾음: MDLMS(D = 8)의 μ*/μ*(0)가 1/1.5–1.5.
보고(판정 아님): D마다 μ*, 고른 μ, 평균 순차 RMSE, 이론 학습 시간 비 (2D+1).

    python -m research.x2_fast_teacher             원장 자료로 실행하고 기록
    python -m research.x2_fast_teacher --synthetic 합성 자료로 코드만 확인(기록 없음)
"""

from __future__ import annotations

import json
import math
import sys

import numpy as np

from research import harness
from research import x1_infinite_delta as x1

STEP = "x2_fast_teacher"
DELAYS, BURN_SESSIONS, SCALES = (0, 1, 2, 4, 8), 10, 8
GRID = np.logspace(-4, 1, 400)
BLOW = 1e6


def stream(sessions):
    """Feature rows φ_t and targets y_t = x_{t+1} for every session, concatenated; session index per row."""
    Phi, Y, which = [], [], []
    t = np.arange(x1.BURN, x1.LENGTH - 1)
    for i, x in enumerate(sessions):
        f = x1.features(x, "jet", SCALES, t)
        Phi.append(f), Y.append(x[t + 1]), which.append(np.full(len(t), i))
    return np.vstack(Phi), np.vstack(Y), np.concatenate(which)


def normalized(Phi, which):
    """Standardize with the burn-in sessions only, then add a bias column."""
    burn = which < BURN_SESSIONS
    m, s = Phi[burn].mean(0), Phi[burn].std(0)
    s[s == 0] = 1
    Z = (Phi - m) / s
    return np.hstack([np.ones((len(Z), 1)), Z])


def online(Z, Y, mu, delay, corrected=False):
    """Delayed LMS over the stream. Returns per-step prequential squared error (before update) and whether it blew up."""
    n, p = Z.shape
    w = np.zeros((p, Y.shape[1]))
    errors = np.empty(n)
    stale = []  # 갱신 시각의 무게로 계산한 오차(빛·전기) 대기열
    for t in range(n):
        pred = Z[t] @ w
        errors[t] = float(np.mean((Y[t] - pred) ** 2))
        stale.append(Y[t] - pred)
        if t - delay >= 0:
            phi = Z[t - delay]
            e = (Y[t - delay] - phi @ w) if corrected else stale[t - delay]
            w = w + mu * np.outer(phi, e)
            if not np.all(np.isfinite(w)) or np.abs(w).max() > BLOW:
                return errors, True
    return errors, False


def limit(Z, Y, delay, corrected=False):
    """Largest μ on the grid that does not blow up over the stream (μ*), by bisection over the grid index
    (blow-up is taken as monotone in μ; the two neighbours of the boundary are both checked directly)."""
    low, high = 0, len(GRID) - 1
    if online(Z, Y, GRID[low], delay, corrected)[1]:
        return float("nan")
    if not online(Z, Y, GRID[high], delay, corrected)[1]:
        return float(GRID[high])
    while high - low > 1:
        mid = (low + high) // 2
        low, high = (mid, high) if not online(Z, Y, GRID[mid], delay, corrected)[1] else (low, mid)
    return float(GRID[low])


def theory_ratio(delay):
    return math.sin(math.pi / (2 * (2 * delay + 1)))


def run(sessions):
    Phi, Y, which = stream(sessions)
    Z = normalized(Phi, which)
    burn, scored = which < BURN_SESSIONS, which >= BURN_SESSIONS
    lam_max = float(np.linalg.eigvalsh(Z[burn].T @ Z[burn] / burn.sum()).max())
    mu_star = {d: limit(Z, Y, d) for d in DELAYS}
    mu_star_corrected = limit(Z, Y, max(DELAYS), corrected=True)
    chosen, per_session, means = {}, {}, {}
    for d in DELAYS:
        candidates = [mu for mu in GRID if mu <= mu_star[d]]
        score = {}
        for mu in candidates[::4]:
            errors, blown = online(Z, Y, mu, d)
            if not blown:
                score[mu] = float(np.mean(errors[burn]))
        mu = min(score, key=score.get)
        errors, _ = online(Z, Y, mu, d)
        chosen[d] = float(mu)
        per_session[d] = [float(np.sqrt(np.mean(errors[which == i]))) for i in np.unique(which[scored])]
        means[d] = float(np.mean(per_session[d]))
    ratios = {d: mu_star[d] / mu_star[0] for d in DELAYS if d}
    h4 = {d: {"empirical": ratios[d], "theory": theory_ratio(d), "relative": ratios[d] / theory_ratio(d)} for d in ratios}
    ds = np.array(DELAYS, float)
    gamma = float(-np.polyfit(np.log(2 * ds + 1), np.log([mu_star[d] for d in DELAYS]), 1)[0])
    decreasing = all(mu_star[b] < mu_star[a] for a, b in zip(DELAYS, DELAYS[1:]))
    monotone = all(means[b] >= means[a] * (1 - 0.005) for a, b in zip(DELAYS, DELAYS[1:]))
    h5 = {"sign_D0_vs_D8": x1.sign_test(per_session[0], per_session[max(DELAYS)]), "monotone": monotone}
    h6 = mu_star_corrected / mu_star[0]
    verdict = {
        "H4": decreasing and ratios[max(DELAYS)] <= 1 / 1.5,
        "H5": h5["sign_D0_vs_D8"]["p"] < 0.05 and h5["sign_D0_vs_D8"]["wins"] > h5["sign_D0_vs_D8"]["n"] / 2 and monotone,
        "H6": 1 / 1.5 <= h6 <= 1.5,
    }
    report = {"lambda_max": lam_max, "mu_star": {str(d): v for d, v in mu_star.items()},
              "mu_star_theory_scaled": {str(d): 2 * theory_ratio(d) / lam_max for d in DELAYS},
              "mu_star_corrected_D8": mu_star_corrected, "H4": {"ratios": {str(d): v for d, v in h4.items()}, "decreasing": decreasing, "gamma": gamma}, "H5": h5, "H6_ratio": h6,
              "chosen_mu": {str(d): v for d, v in chosen.items()}, "mean_prequential_rmse": {str(d): v for d, v in means.items()},
              "learning_time_ratio_theory": {str(d): 2 * d + 1 for d in DELAYS},
              "per_session": {str(d): v for d, v in per_session.items()}, "n_steps": int(len(Z)), "n_scored_sessions": int(len(per_session[0]))}
    return report, verdict


def main(argv):
    if "--synthetic" in argv:
        report, verdict = run(x1.synthetic())
        print(json.dumps({"verdict": verdict, **{k: v for k, v in report.items() if k != "per_session"}}, ensure_ascii=False, indent=1))
        return 0
    commit = harness.sealed(STEP)
    rows = harness.registered(x1.DATASET)
    harness.verify(rows)
    report, verdict = run(x1.load(harness.path(rows[0])))
    result = {"step": STEP, "kind": "탐색(공리 판정 밖)", "claim": __doc__.split("\n")[0], "verdict": verdict, **report,
              "data": [{k: r[k] for k in ("dataset", "version", "asset", "sha256")} for r in rows],
              "code_sha256": {p.relative_to(harness.HERE).as_posix(): harness.sha256(p) for p in harness.code()},
              "git": commit, "run_at": harness.now().isoformat(timespec="seconds")}
    out = harness.RESULTS / "x" / f"{STEP}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps({"verdict": verdict, **{k: v for k, v in report.items() if k != "per_session"}}, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
