"""C3-7: 외부 입력이 없는 렘은 흔적의 시간을 흐르게 하지 않는다 (전제 C3).

C3-6과 §2의 시간의 식을 본 뒤 세운 새 단계다. 흔적은 벽시계가 아니라 고유시간 σ로 늙는다: dh = (x − h)dσ/ℓ. 깸에서는 τ_w ≤ 45 s,
논렘에서는 τ_h 743 s였다. 방향 세포 자신의 발화 수는 시계가 아니다(깸/논렘 발화 비 1.2–1.6). 남은 두 후보를 렘이 가른다:
렘에서 머리는 멈춰 있고(외부 입력 없음) 방향 세포는 깸만큼 발화하며 내부 방향은 확산한다.
명제: 논렘 → 렘(r초) → 논렘에서 뒤 논렘은 렘 끝 방향 θ_r이 아니라 렘 전 논렘 방향 θ₁로 돌아간다. 곧 렘 동안 흔적의 시계는 논렘처럼
거의 멈춰 있다(외부 입력 시계). 대안: 내부 각속도 구동이나 발화가 시계면 렘이 깸처럼 흔적을 덮는다.
식: 렘 끝의 흔적 h = e^{−r/τ}·e^{iθ₁} + (1 − e^{−r/τ})·e^{iθ_r}. 뒤 논렘 첫 60 s 창 방향의 arg h_τ에 대한 정렬 A(τ)(세션 안 순열 보정)를
τ 격자(1–8,192 s)로 훑는다(C3-6과 같은 방법). 초기화 중심은 θ_r.
예측: 보존이면 A(τ_h) > A(초기화)이고 정렬이 가장 높은 τ*가 τ_h/5 이상, 덮음이면 τ* ≲ 45 s(C3-6의 깸).
생물 기준값: 같은 식의 다른 관측(C1-4의 τ_h 743 s, C3-6의 τ_w). 렘 중 내부 방향 확산은 Chaudhuri et al. 2019.
자료(원장): dandi-000056 (주), dandi-000939-extract(첫 home_cage)와 dandi-001699(야생형)를 합친 재현. 묶음: 앞 논렘 ≥ 30 s, 렘 10–640 s,
뒤 논렘(각 경계 1 s 안). θ₁은 앞 논렘 마지막 30 s, θ_r은 렘 마지막 10 s(렘 평균 발화를 뺀 집단 벡터). 순열·부트스트랩 1000번.
판정(실행 전 고정):
- 000056: 묶음 ≥ 50
- 보존: 000056 A(τ_h) − A(θ_r)의 부트스트랩 1% 백분위 > 0
- 시간상수: 000056 τ* ≥ τ_h/5
- 재현(000939 + 001699): A(τ_h) − A(θ_r)의 부트스트랩 1% 백분위 > 0
- 역증명(000056): 1 − A(τ_h)/A(τ*) ≤ 0.1 < 1 − A(θ_r)/A(τ*) (렘이 흔적을 덮는다면 가장 나은 정렬의 90%에 못 미친다)
"""

import json

import numpy as np

from research import harness, store
from research import c3_2_trace_replication as c32
from research import c3_3_restoring as c33
from research import c3_6_wake_overwrite as c36
from research.c3_1_sleep_trace import BOOTSTRAP, PERMUTATIONS
from research.c4_1_metric_hd import GRID, tuning

SLOW, SHORTFALL = 5.0, 0.1


def hd(s, t, angle, spans):
    f = tuning(*c32.windows(s, t, angle, spans))
    keep = (np.abs(f @ np.exp(1j * GRID)) / f.sum(1) >= c32.R_HD) & (f.max(1) >= c32.PEAK_HD)
    return keep, np.angle(f @ np.exp(1j * GRID))


def session_056(row):
    s = store.load(row)
    t, angle = c33.head_angle(s)
    keep, phi = hd(s, t, angle, zip(*s.intervals("states", "Awake")))
    if keep.sum() < c32.MIN_CELLS:
        return None
    return c36.triplets(s.units(keep), phi[keep], "states", "REM", "Non-REM")  # 가운데 상태가 렘인 C3-6 묶음


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
    return c36.triplets(s, np.angle(f @ np.exp(1j * GRID)), "sleep_states", "rem", "nrem", (home[0][0], home[1][0]))


def session_1699(row):
    s = store.load(row)
    t, angle = s.series("head")
    keep, phi = hd(s, t, np.mod(angle, 2 * np.pi), [(t[0], t[-1])])
    if keep.sum() < c32.MIN_CELLS:
        return None
    return c36.triplets(s.units(keep), phi[keep], "sleep_stages", "rem", "nrem")


def analyse(sessions, tau_h, rng):
    """Permutation-corrected alignment to arg h_τ over the τ grid, to τ_h and to the reset centre θ_r, bootstrapped."""
    found = [(g, e) for g, x in enumerate(sessions) if x for e in x]
    group = np.array([g for g, _ in found])
    m = np.array([e["u"].mean() for _, e in found])
    slept, ended, length = (np.array([e[k] for _, e in found]) for k in ("slept", "woke", "wake"))
    c = c36.centres(slept, ended, length, np.r_[c36.GRID_TAU, tau_h])
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
    n = len(c36.GRID_TAU)
    best = int(np.argmax(a[:n]))
    return {"triplets": len(m), "rem_median_s": float(np.median(length)), "alignment": a.tolist(), "se": boot.std(0).tolist(),
            "tau_star": float(c36.GRID_TAU[best]),
            "tau_star_interval": np.percentile(c36.GRID_TAU[boot[:, :n].argmax(1)], [2.5, 97.5]).tolist(),
            "preserved": float(a[n] - a[-1]), "preserved_p1": float(np.percentile(boot[:, n] - boot[:, -1], 1)),
            "shortfall_trace": float(1 - a[n] / a[best]), "shortfall_reset": float(1 - a[-1] / a[best])}


def main():
    tau_h = json.loads((harness.RESULTS / "c1_4_common_trace_time.json").read_text(encoding="utf-8"))[
        "measured"]["fixed_cohort"]["common"]["tau"][0]
    rows56 = harness.registered("dandi-000056")
    rows39 = [r for r in harness.registered("dandi-000939-extract") if r["asset"].endswith(".npz")]
    rows99 = harness.registered("dandi-001699")
    harness.verify(rows56 + rows39 + rows99)
    main56 = analyse([session_056(r) for r in rows56], tau_h, np.random.default_rng(0))
    rep = analyse([session_939(r) for r in rows39] + [session_1699(r) for r in rows99], tau_h, np.random.default_rng(0))
    result = harness.record(
        "c3_7_rem_clock", "C3",
        "외부 입력이 없는 렘은 흔적의 시간을 흐르게 하지 않는다: 논렘 → 렘 → 논렘에서 뒤 논렘은 렘 끝 방향이 아니라 렘 전 논렘 방향으로 "
        "돌아간다",
        "같은 식의 다른 관측: C1-4의 τ_h(743 s), C3-6의 깸 τ_w(≤ 45 s). 렘 중 내부 방향 확산: Chaudhuri et al. 2019 Nat Neurosci "
        "22:1512. 실측: DANDI:000056 (주), DANDI:000939 + DANDI:001699 (재현)",
        {"triplets": harness.check(main56["triplets"], 50),
         "preserved": harness.check(main56["preserved_p1"], low=0),
         "time_constant": harness.check(main56["tau_star"], low=tau_h / SLOW),
         "replication_preserved": harness.check(rep["preserved_p1"], low=0)},
        rows56 + rows39 + rows99,
        proof=harness.reverse("입력 없는 렘에서 멈춘 고유시간", main56["shortfall_trace"], main56["shortfall_reset"], SHORTFALL),
        tau_h=tau_h, grid_tau=c36.GRID_TAU.tolist(), dandi_000056=main56, replication=rep)
    print(result["verdict"], {k: v["passed"] for k, v in result["checks"].items()}, result["reverse_proof"]["passed"])
    for name, r in (("000056", main56), ("replication", rep)):
        print(name, r["triplets"], "REM median %.0f s, tau* %.0f %s, preserved %.3f (1%% %.3f), shortfall trace/reset %.2f/%.2f" % (
            r["rem_median_s"], r["tau_star"], np.round(r["tau_star_interval"]).tolist(), r["preserved"], r["preserved_p1"],
            r["shortfall_trace"], r["shortfall_reset"]))


if __name__ == "__main__":
    main()
