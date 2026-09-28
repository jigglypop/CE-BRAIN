"""C1-11: 해독 잡음의 크기는 창의 스파이크 수에 따른다 — 짧은 이탈 불일치의 관측 쪽 마지막 후보 (전제 C1).

C3-8–C3-10·C1-10·C5-2를 본 뒤 세운 새 단계다. 논렘 방향이 기록 자리를 5–15 s 벗어난 뒤 20 s의 정렬 R을 모든 식이 과대 예측했다(실측 0.166 ± 0.017,
식 0.22–0.29). 관측 잡음의 창 사이 상관, 기록장의 여러 봉우리, 세션 고정 끌개, 논렘 쓸기는 원인이 아니었다. 지금 관측 식은 해독 잡음의 크기를 창마다 같게
둔다. 스파이크가 적은 창은 방향이 거의 무작위라 가짜 이탈을 만들고 그 뒤 되돌아옴이 0에 가깝다.
명제: C1-7의 동역학 해(시계 45 s)에 창마다의 해독 잡음 집중도 κ = s·c·n(n: 그 창의 방향 세포 스파이크 수, c: 논렘 반쪽 해독에서 잰 비례 상수, s: 창 평균
E A1(κ)을 C1-7의 ρ에 맞추는 척도)을 입히면, 적합에 쓰지 않은 R(5–15)을 2 SE 안에서 예측하고 표준 관측 10개도 맞춘다. 같은 동역학에 크기가 일정한
잡음(ρ)을 입힌 식은 R(5–15)을 맞추지 못한다.
식: 반쪽 A·B의 해독 잡음이 서로 독립이고 각자 폰미제스(κ = c·n_half)면 반쪽 방향 차 d에 대해 E cos d = A1(c n_A)·A1(c n_B) (A1 = I₁/I₀). d는 C1-10처럼
전체 해독 방향 30° 칸별 치우침을 뺀다. 모형 사건에는 같은 길이의 실측 사건 스파이크 수 순서열을 차례로 입힌다.
생물 기준값: 원장 실측(R(5–15), 표준 관측 10개; 반쪽 해독의 E cos d). 관측 도구의 성질이라 문헌값은 없다.
자료(원장): dandi-000056 (C3-2 사건, 첫 480 s; 표준 관측은 C1-5의 같은 구간 집단).
판정(실행 전 고정):
- 예측: |R_창별(5–15) − R_실측| ≤ 2 SE
- 정확도: 창별 잡음 식의 표준 관측 χ²/자유도 ≤ 2 (관측 10, 자유 A·D·τ·σ₀(C1-7)·s, 자유도 5)
- 역증명: |R_창별 − R_실측|/SE ≤ 2 < |R_일정 − R_실측|/SE (같은 실행, 같은 동역학)
보고(판정 아님): c와 반쪽 적합의 잔차, s, R(15–45).
"""

import json

import cefast
import numpy as np
from scipy.optimize import brentq, minimize_scalar
from scipy.special import i0e, i1e

from research import c1_1_common_equation as c11
from research import c1_5_common_equation_v2 as c15
from research import c3_2_trace_replication as c32
from research import c3_3_restoring as c33
from research import c3_8_record_relocation as c38
from research import harness, store
from research.c1_10_split_half import BIAS_BINS
from research.c3_1_sleep_trace import CHI2, LAGS, PRE, WINDOW
from research.c4_1_metric_hd import GRID, tuning

Z, REPLICAS = 2.0, 4
A1 = lambda k: i1e(k) / i0e(k)


def session(row):
    """Per NREM event: (full direction, half-A direction, half-B direction, n_A, n_B) per 1 s window; or None."""
    s = store.load(row)
    t, angle = c33.head_angle(s)
    f = tuning(*c32.windows(s, t, angle, zip(*s.intervals("states", "Awake"))))
    hd = (np.abs(f @ np.exp(1j * GRID)) / f.sum(1) >= c32.R_HD) & (f.max(1) >= c32.PEAK_HD)
    if hd.sum() < c32.MIN_CELLS:
        return None
    s, phi = s.units(hd), np.angle(f[hd] @ np.exp(1j * GRID))
    half = np.zeros(len(phi), bool)
    half[np.argsort(phi)[::2]] = True
    start, stop = s.intervals("states")
    label = s["states_label"]
    rate = {x: s.window_counts(start[label == x], stop[label == x]).sum(1) / (stop - start)[label == x].sum()
            for x in ("Awake", "Non-REM")}
    out = []
    for i in range(len(label) - 1):
        s0, e0, s1, e1 = start[i], stop[i], start[i + 1], stop[i + 1]
        if label[i] == "Awake" and label[i + 1] == "Non-REM" and e0 - s0 >= PRE and 0 <= s1 - e0 <= 1:
            edges = np.arange(s1, min(e1, s1 + LAGS[-1]), WINDOW)
            if len(edges) > 1:
                counts = s.counts(edges)
                excess = (counts - rate["Non-REM"][:, None] * WINDOW) * np.exp(1j * phi)[:, None]
                out.append(np.stack([np.angle(excess.sum(0)), np.angle(excess[half].sum(0)), np.angle(excess[~half].sum(0)),
                                     counts[half].sum(0), counts[~half].sum(0)], 1))
    return out or None


def calibrate(sessions):
    """c in κ = c·n from E cos d = A1(c n_A)·A1(c n_B), d = half A − half B with the session's direction bias removed."""
    d, na, nb = [], [], []
    for events in sessions:
        full = np.concatenate([e[:, 0] for e in events])
        dd = np.concatenate([np.angle(np.exp(1j * (e[:, 1] - e[:, 2]))) for e in events])
        b = (np.mod(full, 2 * np.pi) / (2 * np.pi) * BIAS_BINS).astype(int).clip(0, BIAS_BINS - 1)
        bias = np.array([np.exp(1j * dd[b == j]).mean() if (b == j).any() else 1.0 for j in range(BIAS_BINS)])
        d.append(np.angle(np.exp(1j * dd) * np.conj(bias[b] / np.abs(bias[b]))))
        na.append(np.concatenate([e[:, 3] for e in events]))
        nb.append(np.concatenate([e[:, 4] for e in events]))
    d, na, nb = map(np.concatenate, (d, na, nb))
    cost = lambda c: np.mean((np.cos(d) - A1(c * na) * A1(c * nb)) ** 2)
    c = minimize_scalar(cost, bounds=(1e-4, 1.0), method="bounded").x
    bins = np.quantile(na + nb, np.linspace(0, 1, 6))
    k = np.digitize(na + nb, bins[1:-1])
    check = [(float(np.cos(d[k == j]).mean()), float((A1(c * na[k == j]) * A1(c * nb[k == j])).mean())) for j in range(5)]
    return float(c), check


def noisy(theta, counts, kappa_of, rng):
    """Model window directions with per-window von Mises noise of concentration κ(n) (κ = 0 is uniform)."""
    return theta + rng.vonmises(0, kappa_of(np.asarray(counts, float)))


def ring_trajectories(p, lengths):
    return cefast.ring_trace(np.zeros(len(lengths)), np.asarray(lengths, np.int64), c11.SPAN, p["D"], p["A"], p["tau"], 0.0,
                             c11.BETA, 200, 11)


def observables(events, pre):
    with np.errstate(invalid="ignore", divide="ignore"):
        ev = [{"pre": p, "theta": th, "head": p, "session": 0} for th, p in zip(events, pre)]
        return c11.observe(c11.statistics(ev), np.ones((1, len(ev))))[0][c15.INDEX]


def main():
    c17 = json.loads((harness.RESULTS / "c1_7_single_clock.json").read_text(encoding="utf-8"))["measured"]["one_clock"]
    c38r = json.loads((harness.RESULTS / "c3_8_record_relocation.json").read_text(encoding="utf-8"))["measured"]
    p, rho = c17["fit"]["params"][0], c17["judged"]["rho"][0]
    r_data, se = c38r["observed"]["R"][0], c38r["observed"]["se"][0]
    rows = harness.registered("dandi-000056")
    harness.verify(rows)
    split = [x for x in map(session, rows) if x]
    c, check = calibrate(split)
    counts = [e[:, 3] + e[:, 4] for events in split for e in events]
    all_n = np.concatenate(counts)
    s = brentq(lambda k: A1(k * c * all_n).mean() - rho, 1e-3, 1e3)
    kappa_count = lambda n: s * c * n
    kappa_flat = brentq(lambda k: A1(k) - rho, 0.05, 50)
    rng = np.random.default_rng(11)
    lengths = np.array([len(n) for n in counts])
    n_rep = np.tile(lengths, REPLICAS)
    theta = ring_trajectories(p, n_rep)
    turn = rng.uniform(-np.pi, np.pi, len(n_rep))
    count_series = counts * REPLICAS
    het = [row[:k] + t for row, k, t in zip(theta, n_rep, turn)]
    r_het = c38.curve([noisy(h, n, kappa_count, rng) for h, n in zip(het, count_series)], np.zeros(len(het), int), rng, boot=False)["R"]
    r_flat = c38.curve([h + rng.vonmises(0, kappa_flat, len(h)) for h in het], np.zeros(len(het), int), rng, boot=False)["R"]
    cohort_counts = [n[:c15.SPAN] for n in counts if len(n) >= c15.SPAN]
    c16 = json.loads((harness.RESULTS / "c1_6_common_equation_precise.json").read_text(encoding="utf-8"))["measured"]
    value, err = np.array(c16["observed"]["dandi_000056"]), np.array(c16["se"]["dandi_000056"])
    m = len(cohort_counts) * 8
    delta = p["sigma0"] * rng.standard_normal(m)
    cohort = ring_trajectories(p, np.full(m, c15.SPAN))
    obs_het = observables([noisy(row[:c15.SPAN], cohort_counts[i % len(cohort_counts)], kappa_count, rng) for i, row in enumerate(cohort)], delta)
    chi2 = float(np.sum(((value - obs_het) / err) ** 2))
    err_het, err_flat = abs(r_het[0] - r_data) / se, abs(r_flat[0] - r_data) / se
    result = harness.record(
        "c1_11_count_noise", "C1",
        "C1-7의 동역학 해에 창마다 스파이크 수에 따른 해독 잡음 크기를 입히면 적합에 쓰지 않은 짧은 이탈 뒤 되돌아옴을 2 SE 안에서 예측하고 표준 관측도 맞춘다",
        "원장 실측(C3-8의 R(5–15), 표준 관측 10개, 논렘 반쪽 해독). 실측: DANDI:000056",
        {"prediction": harness.check(err_het, high=Z), "accuracy": harness.check(chi2 / 5, high=CHI2)},
        rows, proof=harness.reverse("창별 해독 잡음 크기", err_het, err_flat, Z),
        c=c, scale=float(s), calibration_by_count=check, R_count_noise=r_het, R_flat_noise=r_flat, observed_R=c38r["observed"],
        standard_chi2=chi2, standard_prediction=obs_het.tolist())
    print(result["verdict"], {k: x["passed"] for k, x in result["checks"].items()}, result["reverse_proof"]["passed"])
    print("c %.4f scale %.3f, split-half cos d observed vs fitted by count quintile:" % (c, s), [tuple(round(v, 3) for v in x) for x in check])
    print("R count-noise", np.round(r_het, 3).tolist(), "flat", np.round(r_flat, 3).tolist(), "data", np.round(c38r["observed"]["R"], 3).tolist(),
          "errors %.2f / %.2f SE, standard chi2/5 %.2f" % (err_het, err_flat, chi2 / 5))



if __name__ == "__main__":
    main()
