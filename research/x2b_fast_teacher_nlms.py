"""X2b (탐색, 공리 판정 밖): X2를 정규화 LMS로 다시 — 교사 지연이 학습률 한계와 순차 오차를 정하는가.

X2(`x2_fast_teacher`)의 실데이터 실행은 판정할 수 없는 실행이었다. 세션 몇 개의 ΔF/F가 중앙값의 10배 넘게 튀어(최대 5.5, 중앙값
0.33) 표준화 특징의 ‖φ‖²가 한 걸음에 커지고, 고정 μ의 LMS가 그 걸음에서 터졌다. 한계 μ*가 6.7×10⁻⁴로 이론의 1/300이었고
순차 RMSE가 10⁵ 단위였다. 그래서 무엇이 지연 때문인지 가를 수 없었다. 방법만 바꾸고(새 단계) 질문과 기준의 꼴은 둔다.

정규화 LMS(NLMS): 표본 하나의 이득을 μ로 고정한다.

    w_{t+1} = w_t + μ e_{t−D} φ_{t−D} / (ε + ‖φ_{t−D}‖²),   ε = 1

이러면 지연 없는 한계는 μ < 2이고, 한 방향에 오래 머무는 특징에서 지연 D의 한계는 μ < 2 sin(π / (2(2D + 1)))이다. 특징 방향이
걸음마다 바뀌면 지연된 갱신이 서로 직교에 가까워 한계는 그보다 덜 준다. 보정 팔(MDLMS)은 늦게 온 목표로 오차를 지금 무게로
다시 계산한다.

판정 기준 (실행 전 고정; 자료·흐름·μ 고르기·점수는 X2와 같다):
H4 지연이 학습률 한계를 낮춘다: μ*(D)가 D = 0, 1, 2, 4, 8에서 엄격히 줄고 μ*(8)/μ*(0) ≤ 1/1.5. μ 격자는 10⁻³–10 로그 400점.
H4n 지연 없는 한계: μ*(0)이 1.33–3 (NLMS 이론 2).
H5 빠른 교사의 이득: D = 0이 D = 8을 33세션 순차 RMSE의 부호 검정 p < 0.05로 이기고, 평균 순차 RMSE가 D 순으로 줄지 않는다(0.5% 허용).
H6 보정이 한계를 되찾음: MDLMS(D = 8)의 μ*/μ*(0)가 1/1.5–1.5.
보고: sin 법칙 대비 비, 멱 지수 γ (μ* ∝ (2D+1)^(−γ)), 고른 μ, 평균 순차 RMSE.

    python -m research.x2b_fast_teacher_nlms             원장 자료로 실행하고 기록
    python -m research.x2b_fast_teacher_nlms --synthetic 합성 자료로 코드만 확인(기록 없음)
"""

from __future__ import annotations

import json
import sys

import numpy as np

from research import harness
from research import x1_infinite_delta as x1
from research import x2_fast_teacher as x2

STEP = "x2b_fast_teacher_nlms"
DELAYS, EPS, BLOW = x2.DELAYS, 1.0, 1e6
GRID = np.logspace(-3, 1, 400)


def online(Z, Y, mu, delay, corrected=False):
    """Delayed NLMS over the stream: per-step prequential squared error (before update) and whether it blew up."""
    n, p = Z.shape
    w = np.zeros((p, Y.shape[1]))
    errors = np.empty(n)
    stale, norm = [], EPS + np.einsum("ij,ij->i", Z, Z)
    for t in range(n):
        pred = Z[t] @ w
        errors[t] = float(np.mean((Y[t] - pred) ** 2))
        stale.append(Y[t] - pred)
        if t - delay >= 0:
            phi = Z[t - delay]
            e = (Y[t - delay] - phi @ w) if corrected else stale[t - delay]
            w = w + (mu / norm[t - delay]) * np.outer(phi, e)
            if not np.all(np.isfinite(w)) or np.abs(w).max() > BLOW:
                return errors, True
    return errors, False


def limit(Z, Y, delay, corrected=False):
    low, high = 0, len(GRID) - 1
    if online(Z, Y, GRID[low], delay, corrected)[1]:
        return float("nan")
    if not online(Z, Y, GRID[high], delay, corrected)[1]:
        return float(GRID[high])
    while high - low > 1:
        mid = (low + high) // 2
        low, high = (mid, high) if not online(Z, Y, GRID[mid], delay, corrected)[1] else (low, mid)
    return float(GRID[low])


def run(sessions):
    Phi, Y, which = x2.stream(sessions)
    Z = x2.normalized(Phi, which)
    burn, scored = which < x2.BURN_SESSIONS, which >= x2.BURN_SESSIONS
    mu_star = {d: limit(Z, Y, d) for d in DELAYS}
    corrected = limit(Z, Y, max(DELAYS), corrected=True)
    chosen, per_session, means = {}, {}, {}
    for d in DELAYS:
        score = {}
        for mu in [m for m in GRID if m <= mu_star[d]][::4]:
            errors, blown = online(Z, Y, mu, d)
            if not blown:
                score[mu] = float(np.mean(errors[burn]))
        mu = min(score, key=score.get)
        errors, _ = online(Z, Y, mu, d)
        chosen[d] = float(mu)
        per_session[d] = [float(np.sqrt(np.mean(errors[which == i]))) for i in np.unique(which[scored])]
        means[d] = float(np.mean(per_session[d]))
    ratios = {d: mu_star[d] / mu_star[0] for d in DELAYS if d}
    sin_law = {str(d): {"empirical": ratios[d], "theory": x2.theory_ratio(d)} for d in ratios}
    ds = np.array(DELAYS, float)
    gamma = float(-np.polyfit(np.log(2 * ds + 1), np.log([mu_star[d] for d in DELAYS]), 1)[0])
    decreasing = all(mu_star[b] < mu_star[a] for a, b in zip(DELAYS, DELAYS[1:]))
    monotone = all(means[b] >= means[a] * (1 - 0.005) for a, b in zip(DELAYS, DELAYS[1:]))
    sign = x1.sign_test(per_session[0], per_session[max(DELAYS)])
    verdict = {
        "H4": decreasing and ratios[max(DELAYS)] <= 1 / 1.5,
        "H4n": 1.33 <= mu_star[0] <= 3,
        "H5": sign["p"] < 0.05 and sign["wins"] > sign["n"] / 2 and monotone,
        "H6": 1 / 1.5 <= corrected / mu_star[0] <= 1.5,
    }
    report = {"mu_star": {str(d): v for d, v in mu_star.items()}, "mu_star_corrected_D8": corrected,
              "H4": {"sin_law": sin_law, "decreasing": decreasing, "gamma": gamma}, "H5": {"sign_D0_vs_D8": sign, "monotone": monotone},
              "H6_ratio": corrected / mu_star[0], "chosen_mu": {str(d): v for d, v in chosen.items()},
              "mean_prequential_rmse": {str(d): v for d, v in means.items()},
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
    out.write_text(json.dumps(result, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps({"verdict": verdict, **{k: v for k, v in report.items() if k != "per_session"}}, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
