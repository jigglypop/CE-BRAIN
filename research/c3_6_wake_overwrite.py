"""C3-6: 흔적은 깸에서 빨리 덮이고 논렘에서 오래 남는다 — 선택적 게이트 (전제 C3).

C3-5를 본 뒤 세운 새 단계다. 잠든 뒤 흔적은 τ_h = 743 s로 남지만(C1-4), 잠드는 순간의 흔적 중심은 직전 10–40 s의 방향이었다(C3-5).
명제: 논렘 → 짧은 깸(w초) → 논렘에서, 앞 논렘의 방향 θ₁은 깸 동안 e^{−w/τ_w}로 덮여 뒤 논렘에 남고, τ_w는 논렘의 τ_h보다
훨씬 짧다. 곧 흔적의 갱신 속도는 상태에 따라 다르다.
식 (Mamba 선택적 게이트 h_t = e^{−Δ_t}h_{t−1} + (1 − e^{−Δ_t})x_t, Δ = dt/τ_w(깸), dt/τ_h(논렘)):
  깸 끝의 흔적 h = e^{−w/τ_w}·e^{iθ₁} + (1 − e^{−w/τ_w})·e^{iθ_w} (θ₁: 앞 논렘 마지막 30 s 방향, θ_w: 깸 마지막 10 s 방향).
  뒤 논렘은 arg h로 끌린다. 정렬 A(τ) = 묶음 평균 Re(m e^{−i·arg h_τ}) − 순열 평균(m: 뒤 논렘 창 방향 단위벡터 평균, 순열은 세션
  안 묶음끼리 중심을 섞음)을 τ 격자(2^{k/2} s, 1–8,192 s)로 훑는다.
경쟁 식: 선택(τ_w ≪ τ_h), 시간상수 하나(τ = τ_h, C1-4의 743 s), 완전 초기화(중심 = θ_w).
예측: τ_w = 20 s (C3-5에서 잠들기 전 정렬이 가장 높은 적분 시간 10–40 s의 기하평균). 문헌에 깸의 흔적 덮임 시간이 없어 같은
식의 다른 관측(C1-4의 τ_h, C3-5의 τ*)을 기준으로 삼는다.
자료(원장): dandi-000056 (주), dandi-000939-extract(첫 home_cage)와 dandi-001699(야생형)를 합친 재현. 방향 세포·해독은 C3-2·C1-3과
같다. 묶음: 앞 논렘 ≥ 30 s, 사이 깸 10–640 s, 뒤 논렘(각 경계 1 s 안). θ₁은 앞 논렘 마지막 30 s(논렘 평균 발화를 뺀 집단 벡터),
θ_w는 깸 마지막 10 s, m은 뒤 논렘 첫 60 s의 1 s 창. 순열 1000번, 사건 부트스트랩 1000번.
보고(판정 아님): 깸 칸 [10,20,40,80,160,320,640) s마다 u = α·p₁ + β·p_w 복소 최소제곱(세션 평균 뺌)의 Re α, Re β.
설계 이력: 처음에는 Re α(w)에 α₀e^{−w/τ_w}를 맞추려 했으나, 합성 검증에서 참 모형(시간상수 하나)도 χ²/자유도 4.2가 나왔다.
중심이 두 벡터 합의 방향(arg)이라 선형 회귀가 정확히 비례하지 않는다. 실측을 보기 전에 식 그대로의 정렬 훑기로 바꿨다.
판정(실행 전 고정):
- 000056: 세션 ≥ 5, 묶음 ≥ 100
- 남음: 000056 A(20 s) − A(초기화)의 부트스트랩 1% 백분위 > 0 (앞 논렘 방향이 깸을 지나 남는다)
- 예측: 000056 정렬이 가장 높은 격자 τ*가 5–80 s (C3-5의 10–40 s를 두 배 넓힘)
- 선택성: 000056 τ*의 부트스트랩 97.5% 백분위 ≤ τ_h/5
- 재현(000939 + 001699): A(20 s) − A(초기화)의 1% > 0이고 τ* ≤ τ_h/5
- 역증명(000056): 1 − A(20 s)/A(τ*) ≤ 0.1 < 1 − A(τ_h)/A(τ*) (시간상수 하나면 가장 나은 정렬의 90%에 못 미친다)
"""

import json

import numpy as np

from research import harness, store
from research import c3_2_trace_replication as c32
from research import c3_3_restoring as c33
from research.c3_1_sleep_trace import BOOTSTRAP, PERMUTATIONS, PRE, WINDOW
from research.c4_1_metric_hd import GRID, tuning

WAKE = np.array([10, 20, 40, 80, 160, 320, 640.0])
GRID_TAU = 2 ** (np.arange(27) / 2)
SLEPT, FIRST, SELECTIVE, BAND, PREDICTED, SHORTFALL = 30.0, 60.0, 5.0, (5.0, 80.0), 20.0, 0.1


def triplets(s, phi, table, wake, nrem, limit=None):
    """NREM → wake (10–640 s) → NREM: session-free (θ₁, θ_w, wake length, NREM₂ window unit vectors)."""
    start, stop = s.intervals(table)
    label = s[f"{table}_label"]
    order = np.argsort(start)
    start, stop, label = start[order], stop[order], label[order]
    rate = {x: s.window_counts(start[label == x], stop[label == x]).sum(1) / (stop - start)[label == x].sum()
            for x in (wake, nrem)}
    if limit is not None:
        keep = (start >= limit[0]) & (stop <= limit[1])
        start, stop, label = start[keep], stop[keep], label[keep]
    found = []
    for i in range(1, len(label) - 1):
        (s0, e0), (s1, e1), (s2, e2) = zip(start[i - 1:i + 2], stop[i - 1:i + 2])
        if (label[i - 1] == nrem and label[i] == wake and label[i + 1] == nrem and e0 - s0 >= SLEPT
                and WAKE[0] <= e1 - s1 < WAKE[-1] and 0 <= s1 - e0 <= 1 and 0 <= s2 - e1 <= 1):
            edges = np.arange(s2, min(e2, s2 + FIRST), WINDOW)
            if len(edges) > 1:
                found.append({"slept": c32.direction(s, [e0 - SLEPT, e0], rate[nrem], phi)[0],
                              "woke": c32.direction(s, [e1 - PRE, e1], rate[wake], phi)[0], "wake": e1 - s1,
                              "u": np.exp(1j * c32.direction(s, edges, rate[nrem], phi))})
    return found


def session_056(row):
    s = store.load(row)
    t, angle = c33.head_angle(s)
    f = tuning(*c32.windows(s, t, angle, zip(*s.intervals("states", "Awake"))))
    hd = (np.abs(f @ np.exp(1j * GRID)) / f.sum(1) >= c32.R_HD) & (f.max(1) >= c32.PEAK_HD)
    if hd.sum() < c32.MIN_CELLS:
        return None
    return triplets(s.units(hd), np.angle(f[hd] @ np.exp(1j * GRID)), "states", "Awake", "Non-REM")


def session_939(row):
    s = store.load(row)
    s = s.units(s["unit_is_head_direction"] == 1)
    (a,), (b,) = s.intervals("epochs", "wake_square")
    t, angle = s.series("head")
    inside = (t >= a) & (t < b)
    f = tuning(*c32.windows(s, t[inside], angle[inside], [(a, b)]))
    if len(f) < c32.MIN_CELLS:
        return None
    home = s.intervals("epochs", "home_cage")
    return triplets(s, np.angle(f @ np.exp(1j * GRID)), "sleep_states", "wake", "nrem", (home[0][0], home[1][0]))


def session_1699(row):
    s = store.load(row)
    t, angle = s.series("head")
    f = tuning(*c32.windows(s, t, np.mod(angle, 2 * np.pi), [(t[0], t[-1])]))
    hd = (np.abs(f @ np.exp(1j * GRID)) / f.sum(1) >= c32.R_HD) & (f.max(1) >= c32.PEAK_HD)
    if hd.sum() < c32.MIN_CELLS:
        return None
    return triplets(s.units(hd), np.angle(f[hd] @ np.exp(1j * GRID)), "sleep_stages", "wake", "nrem")


def sums(sessions):
    """Per triplet: wake bin, wake length and the normal-equation terms of u = α·p₁ + β·p_w (session means removed)."""
    rows = []
    for found in sessions:
        if not found:
            continue
        mu = np.concatenate([e["u"] for e in found]).mean()
        m1, mw = (np.mean([np.exp(1j * e[k]) for e in found]) for k in ("slept", "woke"))
        for e in found:
            p1, pw, x = np.exp(1j * e["slept"]) - m1, np.exp(1j * e["woke"]) - mw, (e["u"] - mu).sum()
            n = len(e["u"])
            rows.append([np.digitize(e["wake"], WAKE) - 1, e["wake"], n * abs(p1) ** 2, n * abs(pw) ** 2,
                         n * np.conj(p1) * pw, np.conj(p1) * x, np.conj(pw) * x])
    return np.array(rows, complex)


def coefficients(terms, weight, bins=None):
    """Re α and Re β per wake bin from weighted normal-equation sums (weight: draws × triplets; bin −1 is left out)."""
    k = terms[:, 0].real.astype(int) if bins is None else bins
    onehot = (k[:, None] == np.arange(len(WAKE) - 1)).astype(float)
    s11, s22, s12, b1, b2 = (weight @ (onehot * terms[:, j, None]) for j in range(2, 7))
    with np.errstate(invalid="ignore", divide="ignore"):
        det = s11 * s22 - np.abs(s12) ** 2
        return ((s22 * b1 - s12 * b2) / det).real, ((s11 * b2 - np.conj(s12) * b1) / det).real


def centres(slept, woke, wake, taus):
    """arg h_τ for every τ (columns), then the reset centre θ_w."""
    keep = np.exp(-wake[:, None] / taus[None])
    return np.column_stack([np.angle(keep * np.exp(1j * slept[:, None]) + (1 - keep) * np.exp(1j * woke[:, None])), woke])


def analyse(sessions, tau_h, rng):
    """Permutation-corrected alignment to arg h_τ over the τ grid, τ = 20 s, τ_h and the reset centre, bootstrapped."""
    found = [(g, e) for g, x in enumerate(sessions) if x for e in x]
    group = np.array([g for g, _ in found])
    m = np.array([e["u"].mean() for _, e in found])
    slept, woke, wake = (np.array([e[k] for _, e in found]) for k in ("slept", "woke", "wake"))
    taus = np.r_[GRID_TAU, PREDICTED, tau_h]
    c = centres(slept, woke, wake, taus)
    score = lambda c: (m[:, None] * np.exp(-1j * c)).real
    null = np.zeros(c.shape[1])
    for _ in range(PERMUTATIONS):
        shuffled = c.copy()
        for g in np.unique(group):
            at = np.flatnonzero(group == g)
            shuffled[at] = shuffled[rng.permutation(at)]
        null += score(shuffled).mean(0) / PERMUTATIONS
    a = score(c).mean(0) - null
    weight = np.stack([np.bincount(rng.integers(0, len(m), len(m)), minlength=len(m)) for _ in range(BOOTSTRAP)])
    boot = weight @ score(c) / weight.sum(1, keepdims=True) - null
    n = len(GRID_TAU)
    best = int(np.argmax(a[:n]))
    terms = sums(sessions)
    alpha, beta = (x[0] for x in coefficients(terms, np.ones((1, len(terms)))))
    return {"triplets": len(m), "per_bin": np.bincount(terms[:, 0].real.astype(int), minlength=len(WAKE) - 1).tolist(),
            "alignment": a.tolist(), "se": boot.std(0).tolist(), "tau_star": float(GRID_TAU[best]),
            "tau_star_interval": np.percentile(GRID_TAU[boot[:, :n].argmax(1)], [2.5, 97.5]).tolist(),
            "survives": float(a[n] - a[-1]), "survives_p1": float(np.percentile(boot[:, n] - boot[:, -1], 1)),
            "shortfall_predicted": float(1 - a[n] / a[best]), "shortfall_single": float(1 - a[n + 1] / a[best]),
            "shortfall_reset": float(1 - a[-1] / a[best]), "alpha": alpha.tolist(), "beta": beta.tolist()}


def main():
    tau_h = json.loads((harness.RESULTS / "c1_4_common_trace_time.json").read_text(encoding="utf-8"))[
        "measured"]["fixed_cohort"]["common"]["tau"][0]
    rows56 = harness.registered("dandi-000056")
    rows39 = [r for r in harness.registered("dandi-000939-extract") if r["asset"].endswith(".npz")]
    rows99 = harness.registered("dandi-001699")
    harness.verify(rows56 + rows39 + rows99)
    s56 = [session_056(r) for r in rows56]
    main56 = analyse(s56, tau_h, np.random.default_rng(0))
    main56["sessions"] = sum(1 for x in s56 if x)
    rep = analyse([session_939(r) for r in rows39] + [session_1699(r) for r in rows99], tau_h, np.random.default_rng(0))
    result = harness.record(
        "c3_6_wake_overwrite", "C3",
        "논렘 → 짧은 깸 → 논렘에서 앞 논렘의 방향은 깸 동안 e^{−w/τ_w}로 덮여 뒤 논렘에 남고, τ_w는 논렘의 τ_h보다 훨씬 짧다",
        "같은 식의 다른 관측: C1-4의 τ_h(743 s), C3-5의 잠들기 전 적분 시간(10–40 s). 실측: DANDI:000056 (주), "
        "DANDI:000939 + DANDI:001699 (재현)",
        {"sessions": harness.check(main56["sessions"], 5), "triplets": harness.check(main56["triplets"], 100),
         "survives": harness.check(main56["survives_p1"], low=0),
         "prediction": harness.check(main56["tau_star"], *BAND),
         "selectivity": harness.check(main56["tau_star_interval"][1], high=tau_h / SELECTIVE),
         "replication_survives": harness.check(rep["survives_p1"], low=0),
         "replication_selectivity": harness.check(rep["tau_star"], high=tau_h / SELECTIVE)},
        rows56 + rows39 + rows99,
        proof=harness.reverse("상태 선택적 갱신(깸 τ_w ≪ 논렘 τ_h)", main56["shortfall_predicted"], main56["shortfall_single"],
                              SHORTFALL),
        tau_h=tau_h, grid_tau=GRID_TAU.tolist(), dandi_000056=main56, replication=rep)
    print(result["verdict"], {k: v["passed"] for k, v in result["checks"].items()}, result["reverse_proof"]["passed"])
    for name, r in (("000056", main56), ("replication", rep)):
        print(name, r["triplets"], r["per_bin"], "tau* %.1f %s survives %.3f (1%% %.3f) shortfall pred/single/reset %.2f/%.2f/%.2f" % (
            r["tau_star"], np.round(r["tau_star_interval"], 1).tolist(), r["survives"], r["survives_p1"],
            r["shortfall_predicted"], r["shortfall_single"], r["shortfall_reset"]))
        print("   alpha", np.round(r["alpha"], 3).tolist(), "beta", np.round(r["beta"], 3).tolist())


if __name__ == "__main__":
    main()
