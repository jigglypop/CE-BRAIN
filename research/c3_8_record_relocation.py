"""C3-8: 기록 자리를 벗어난 채 시계 τ만큼 머물면 흔적은 되돌아오지 않는다 (전제 C3).

C1-7(시계 하나 45 s, 잠의 긴 유지는 기록의 되먹임)을 본 뒤 세운 새 단계다. 기록장 식(v3)에서 흔적 중심은 되먹임으로 붙들려 있으므로,
상태가 기록 자리를 τ 가까이 벗어나 있으면 새 자리에 기록이 쌓여 흔적 중심이 옮겨 간다. 느린 시계(τ 수백 s)라면 수십 초 벗어나도 돌아온다.
명제: 000056 논렘에서 내부 방향이 기록 자리(논렘 처음 30 s의 평균 방향)에서 90° 넘게 15–45 s 연속으로 벗어났다가 끝난 뒤 20 s의 정렬
R(15–45)은 v3(C1-7의 시계 하나 해)의 예측에 맞고, 같은 관측 10개에 따로 맞춘 느린 시계(τ = 743 s, C1-4) 식의 예측에서는 벗어난다.
관측: 1 s 창 방향(C3-2), 벗어남은 5 s 끝 원형 평균이 기록 자리에서 90° 넘은 창의 연속, R = 벗어남이 끝난 창 20 s 뒤 창 방향의 cos(기록 자리와의
각) 평균 − 세션 안 사건끼리 기록 자리를 섞은 순열 평균. 모형은 같은 사건 길이를 4번 복제해 사건마다 방향을 무작위로 돌리고 해독 잡음(C1-7의
ρ에 맞춘 폰미제스)을 더해 같은 과정으로 잰다(오일러, 이완율 × 간격 ≤ 0.05).
예측(모형만, 실측을 보기 전): C1-7 해에서 R(15–45) ≈ 0.01, 같은 A·D에 τ 348 s·743 s면 0.15–0.16.
생물 기준값: 같은 식의 다른 관측(C3-6의 깸 덮임 τ_w 45 s, C1-4의 τ 743 s).
자료(원장): dandi-000056 (C3-2 사건, 첫 480 s; 모형 적합은 C1-5의 같은 구간 집단).
판정(실행 전 고정):
- 15–45 s 벗어남 ≥ 100
- 정확도: |R − R_v3| ≤ 2 SE (사건 부트스트랩 1000번)
- 역증명: |R − R_v3|/SE ≤ 2 < |R − R_느린|/SE
보고(판정 아님): R(5–15), R(45–135)과 예측, τ 348 s 식의 적합과 예측, 느린 시계 식의 판정 χ².
"""

import json

import cefast
import numpy as np
from scipy.optimize import brentq
from scipy.special import i0e, i1e

from research import c1_1_common_equation as c11
from research import c1_5_common_equation_v2 as c15
from research import c3_2_trace_replication as c32
from research import harness, ring
from research.c3_1_sleep_trace import BOOTSTRAP, PERMUTATIONS

SMOOTH, AWAY, AHEAD, EARLY = 5, np.pi / 2, 20, 30
BINS = ((5, 15), (15, 45), (45, 135))
LONG, MIN_EXCURSIONS, Z, REPLICAS = 1, 100, 2.0, 4
LOOSE = (0.01, 0.05)  # 최적화 허용치: 모형 표본 잡음 수준


def excursions(theta, centre):
    """(run length, cos of the window AHEAD s after the run ends) for every away run after the first EARLY windows."""
    th = theta[EARLY:]
    c = np.cumsum(np.r_[0, np.exp(1j * th)])
    away = np.abs(np.angle((c[SMOOTH:] - c[:-SMOOTH]) * np.exp(-1j * centre))) > AWAY
    run, out = 0, []
    for i, a in enumerate(away):
        run = run + 1 if a else 0
        k = i + SMOOTH - 1
        if a and k + AHEAD < len(th) and (i + 1 == len(away) or not away[i + 1]):
            out.append((run, np.cos(th[k + AHEAD] - centre)))
    return out


def sums(thetas, centres):
    """Per event and bin: sum of cos and count of excursions (events × bins × 2)."""
    out = np.zeros((len(thetas), len(BINS), 2))
    for e, (th, c) in enumerate(zip(thetas, centres)):
        for run, a in excursions(th, c):
            for b, (lo, hi) in enumerate(BINS):
                if lo <= run < hi:
                    out[e, b] += (a, 1)
    return out


def early(thetas):
    return np.array([np.angle(np.exp(1j * th[:EARLY]).sum()) for th in thetas])


def curve(thetas, group, rng, boot=True):
    """Permutation-corrected R per bin, its event-bootstrap SE and the excursion counts."""
    keep = [i for i, th in enumerate(thetas) if len(th) >= EARLY + SMOOTH + AHEAD]
    thetas, group = [thetas[i] for i in keep], group[keep]
    centres = early(thetas)
    s = sums(thetas, centres)
    null = np.zeros(len(BINS))
    for _ in range(PERMUTATIONS // 10):
        shuffled = centres.copy()
        for g in np.unique(group):
            at = np.flatnonzero(group == g)
            shuffled[at] = shuffled[rng.permutation(at)]
        n = sums(thetas, shuffled).sum(0)
        null += n[:, 0] / np.maximum(n[:, 1], 1) / (PERMUTATIONS // 10)
    total = s.sum(0)
    r = total[:, 0] / np.maximum(total[:, 1], 1) - null
    se = np.full(len(BINS), np.nan)
    if boot:
        w = np.stack([np.bincount(rng.integers(0, len(s), len(s)), minlength=len(s)) for _ in range(BOOTSTRAP)]).astype(float)
        t = np.einsum("be,ekc->bkc", w, s)
        se = (t[..., 0] / np.maximum(t[..., 1], 1)).std(0)
    return {"R": r.tolist(), "se": se.tolist(), "count": total[:, 1].astype(int).tolist(), "null": null.tolist()}


def model(p, rho, lengths, seed):
    """R per bin of the ring model on the data's event lengths, rotated per event, with decoding noise matched to ρ."""
    rng = np.random.default_rng(seed)
    n = np.tile(lengths, REPLICAS).astype(np.int64)
    steps = int(max(100, np.ceil(p["D"] * c11.BETA * p["A"] / 0.05)))
    theta = cefast.ring_trace(np.zeros(len(n)), n, c11.SPAN, p["D"], p["A"], p["tau"], 0.0, c11.BETA, steps, seed)
    kappa = brentq(lambda k: i1e(k) / i0e(k) - rho, 0.05, 50)
    turn = rng.uniform(-np.pi, np.pi, len(n))
    thetas = [row[:k] + t + rng.vonmises(0, kappa, k) for row, k, t in zip(theta, n, turn)]
    return curve(thetas, np.zeros(len(thetas), int), rng, boot=False)["R"]


def main():
    c17 = json.loads((harness.RESULTS / "c1_7_single_clock.json").read_text(encoding="utf-8"))["measured"]
    rows = harness.registered("dandi-000056")
    harness.verify(rows)
    sessions = [c32.session_056(r) for r in rows]
    thetas = [theta for f in sessions if f for _, _, theta in f]
    group = np.array([g for g, f in enumerate(sessions) if f for _ in f])
    lengths = np.array([len(t) for t in thetas])
    base = c15.Data(c15.cohort(sessions), np.random.default_rng(0))
    v3 = c17["one_clock"]["fit"]["params"][0], c17["one_clock"]["judged"]["rho"][0]
    slow_fit = ring.fit_data([base], (), ("A", "D", "sigma0"), {"tau": 743.0}, v3[0], tol=LOOSE)
    mid_fit = ring.fit_data([base], (), ("A", "D", "sigma0"), {"tau": 348.0}, v3[0], tol=LOOSE)
    slow_judged, mid_judged = ring.judged([base], slow_fit, 3), ring.judged([base], mid_fit, 3)
    predicted = {"v3": model(*v3, lengths, 11),
                 "slow_743": model(slow_fit["params"][0], slow_judged["rho"][0], lengths, 11),
                 "mid_348": model(mid_fit["params"][0], mid_judged["rho"][0], lengths, 11)}
    data = curve(thetas, group, np.random.default_rng(0))
    r, se = data["R"][LONG], data["se"][LONG]
    err_v3, err_slow = abs(r - predicted["v3"][LONG]) / se, abs(r - predicted["slow_743"][LONG]) / se
    result = harness.record(
        "c3_8_record_relocation", "C3",
        "논렘에서 내부 방향이 기록 자리를 15–45 s 벗어났다가 끝난 뒤의 정렬은 시계 하나(τ 45 s) 기록장 식의 예측에 맞고 느린 시계(τ 743 s) "
        "식의 예측에서는 벗어난다: 그만큼 벗어나면 흔적 중심이 새 자리로 옮겨 간다",
        "같은 식의 다른 관측: C3-6의 깸 덮임 τ_w 45 s, C1-4의 τ 743 s. 실측: DANDI:000056",
        {"excursions": harness.check(data["count"][LONG], MIN_EXCURSIONS), "accuracy": harness.check(err_v3, high=Z)},
        rows, proof=harness.reverse("기록의 재배치(시계 하나)", err_v3, err_slow, Z),
        observed=data, predicted=predicted, bins=[list(b) for b in BINS], slow_fit=slow_fit, slow_judged=slow_judged,
        mid_fit=mid_fit, mid_judged=mid_judged)
    print(result["verdict"], {k: v["passed"] for k, v in result["checks"].items()}, result["reverse_proof"]["passed"])
    print("data R", np.round(data["R"], 3).tolist(), "se", np.round(data["se"], 3).tolist(), "count", data["count"])
    for k, v in predicted.items():
        print(k, np.round(v, 3).tolist())
    print("slow fit judged %.2f, mid fit judged %.2f" % (slow_judged["chi2_dof"], mid_judged["chi2_dof"]))


if __name__ == "__main__":
    main()
