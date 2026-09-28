"""C5-3: 잠에서는 확률 흐름이 없다 — 상세 균형, 방향 구동 F = 0 (전제 C5).

§2의 식을 다시 세운 뒤 세운 새 단계다. 확률 동역학 dx = [−G⁻¹∇E + F]dt + 잡음은 잡음 공분산(G), 정상 분포(E), 나머지 확률 흐름(F)으로 유일하게 나뉜다.
고리 위 1차원 운동에서 정상 상태의 확률 흐름은 고리를 도는 순환 하나뿐이므로, 상세 균형(F = 0) ⇔ 알짜 회전이 0이다.
명제: 000056에서 잠(논렘, 렘)의 세션마다 알짜 회전 D가 오차 안에서 0이다(세션 사이 χ² 검정 p ≥ 0.01, 두 상태 각각). 같은 도구로 깸에서 머리를 돌리는 동안은
회전 방향에 따라 D가 갈린다(양성 대조).
관측: 방향 세포 쌍의 교차 상관을 선호 방향 차 ψ의 12칸으로 모은 첫 조화 F₁(τ) (C4-4). 봉우리가 한쪽으로 돌면 Im F₁ ≠ 0이다. D = Σ_τ Im F₁ / Σ_τ Re F₁
(τ = 20–300 ms). 세션 오차는 구간을 시작 순서로 번갈아 10묶음으로 나눈 잭나이프. 깸의 회전 구간: 머리 각속도(0.2 s 평활)가 +45°/s 초과 또는 −45°/s 미만인
0.5 s 이상 구간.
생물 기준값: 깸에서 머리 회전을 따라 도는 방향 봉우리(Taube 1990 이래의 방향 세포 성질)가 양성 대조다. 잠에는 외부 회전 입력이 없다.
자료(원장): dandi-000056 (주), dandi-000939-extract (재현, 보고: 깸 회전 대조는 wake_square의 추적만).
판정(실행 전 고정):
- 도구: 깸 회전 대조 (D(각속도 < 0) − D(각속도 > 0))의 세션 부트스트랩 1% 백분위가 0과 같은 쪽에 있지 않다(부호와 무관하게 0을 벗어남)
- 명제(논렘): 세션별 (D/SE)²의 합이 자유도(세션 수)의 χ² 분포에서 p ≥ 0.01
- 명제(렘): 같음
- 크기: 잠의 세션 평균 |D|(오차 보정)의 99% 상한이 깸 회전 대조 절반의 10% 이하
"""

import numpy as np
from scipy.stats import chi2

from research import c3_3_restoring as c33
from research import c4_4_ring_diffusion as c44
from research import harness, store
from research.c3_1_sleep_trace import BOOTSTRAP

CHUNKS, LAGS, TURN, SMOOTH, MIN_RUN, ALPHA, SHARE = 10, slice(2, 31), np.radians(45), 0.2, 0.5, 0.01, 0.1


def directed(counts, expected):
    """(Σ Im F₁, Σ Re F₁) over τ = 20–300 ms."""
    f = c44.harmonics(counts, expected)[0, LAGS]
    return f.imag.sum(), f.real.sum()


def state_d(s, phi, starts, stops):
    """D of one session and state, and its jackknife SE over CHUNKS interleaved groups of intervals."""
    order = np.argsort(starts)
    starts, stops = starts[order], stops[order]
    parts = [c44.pair_sums(s, phi, starts[k::CHUNKS], stops[k::CHUNKS])[:2] for k in range(CHUNKS) if len(starts[k::CHUNKS])]
    sums = np.array([directed(*p) for p in parts])
    d = sums[:, 0].sum() / sums[:, 1].sum()
    loo = np.array([(sums[:, 0].sum() - a) / (sums[:, 1].sum() - b) for a, b in sums])
    return d, np.sqrt((len(loo) - 1) / len(loo) * ((loo - loo.mean()) ** 2).sum())


def turning(t, angle, spans):
    """Intervals (≥ MIN_RUN s) inside spans where the smoothed head angular velocity is above +TURN or below −TURN."""
    ok = np.isfinite(angle)
    t, a = t[ok], np.unwrap(angle[ok])
    dt = np.median(np.diff(t))
    k = max(1, int(round(SMOOTH / dt)))
    w = np.convolve(np.gradient(a, t), np.ones(k) / k, mode="same")
    inside = np.zeros(len(t), bool)
    for x, y in spans:
        inside |= (t >= x) & (t < y)
    out = {}
    for name, mask in (("positive", inside & (w > TURN)), ("negative", inside & (w < -TURN))):
        edges = np.flatnonzero(np.diff(np.r_[0, mask.astype(int), 0]))
        runs = [(t[i], t[j - 1]) for i, j in zip(edges[::2], edges[1::2]) if t[j - 1] - t[i] >= MIN_RUN]
        out[name] = (np.array([r[0] for r in runs]), np.array([r[1] for r in runs]))
    return out


def session(row, loader, head):
    x = loader(row)
    if x is None:
        return None
    s, phi, spans = x
    out = {state: state_d(s, phi, *spans[state]) for state in ("nrem", "rem") if len(spans[state][0]) >= CHUNKS}
    t, angle = head(row)
    turns = turning(t, angle, zip(*spans["wake"]))
    if all(len(turns[k][0]) >= CHUNKS for k in turns):
        out |= {k: directed(*c44.pair_sums(s, phi, *turns[k])[:2]) for k in turns}
    return out


def head_056(row):
    return c33.head_angle(store.load(row))


def head_939(row):
    return store.load(row).series("head")


def analyse(sessions, rng):
    out = {}
    for state in ("nrem", "rem"):
        d = np.array([x[state] for x in sessions if state in x])
        z2 = ((d[:, 0] / d[:, 1]) ** 2).sum()
        out[state] = {"sessions": len(d), "chi2": float(z2), "p": float(chi2.sf(z2, len(d))), "D": d[:, 0].tolist(), "se": d[:, 1].tolist(),
                      "mean_abs_upper": float(np.percentile([np.abs(d[rng.integers(0, len(d), len(d)), 0]).mean() for _ in range(BOOTSTRAP)], 99)
                                              - np.sqrt(np.mean(d[:, 1] ** 2)) * np.sqrt(2 / np.pi))}
    turn = [x for x in sessions if "positive" in x]
    pos, neg = np.array([x["positive"] for x in turn]), np.array([x["negative"] for x in turn])
    contrast = lambda w: (w @ neg[:, 0]) / (w @ neg[:, 1]) - (w @ pos[:, 0]) / (w @ pos[:, 1])
    boot = [contrast(np.bincount(rng.integers(0, len(turn), len(turn)), minlength=len(turn)).astype(float)) for _ in range(BOOTSTRAP)]
    c = contrast(np.ones(len(turn)))
    out["wake_turning"] = {"sessions": len(turn), "contrast": float(c), "p1": float(np.percentile(np.sign(c) * np.array(boot), 1))}
    return out


def main():
    rows56 = harness.registered("dandi-000056")
    rows39 = [r for r in harness.registered("dandi-000939-extract") if r["asset"].endswith(".npz")]
    harness.verify(rows56 + rows39)
    r56 = analyse([x for x in (session(r, c44.hd_056, head_056) for r in rows56) if x], np.random.default_rng(0))
    r39 = analyse([x for x in (session(r, c44.hd_939, head_939) for r in rows39) if x], np.random.default_rng(0))
    half = abs(r56["wake_turning"]["contrast"]) / 2
    sleep_upper = max(r56["nrem"]["mean_abs_upper"], r56["rem"]["mean_abs_upper"])
    result = harness.record(
        "c5_3_detailed_balance", "C5",
        "잠(논렘, 렘)에서는 세션마다 알짜 회전이 오차 안에서 0이다(상세 균형, 방향 구동 F = 0). 같은 도구로 깸에서 머리를 돌리는 동안은 회전 방향에 따라 알짜 "
        "회전이 갈린다",
        "깸에서 머리 회전을 따라 도는 방향 봉우리(양성 대조), 잠에는 외부 회전 입력이 없다. 실측: DANDI:000056 (주), DANDI:000939 (재현, 보고)",
        {"instrument": harness.check(r56["wake_turning"]["p1"], low=0),
         "nrem_balance": harness.check(r56["nrem"]["p"], low=ALPHA), "rem_balance": harness.check(r56["rem"]["p"], low=ALPHA),
         "size": harness.check(sleep_upper, high=SHARE * half)},
        rows56 + rows39, dandi_000056=r56, dandi_000939=r39)
    print(result["verdict"], {k: v["passed"] for k, v in result["checks"].items()})
    for name, r in (("000056", r56), ("000939", r39)):
        print(name, "wake turning contrast %.4f (1%% signed %.4f, %d sessions)" % (r["wake_turning"]["contrast"], r["wake_turning"]["p1"], r["wake_turning"]["sessions"]))
        for st in ("nrem", "rem"):
            x = r[st]; print("   %s: sessions %d chi2 %.1f p %.3f, mean|D| upper %.4f, D %s" % (st, x["sessions"], x["chi2"], x["p"], x["mean_abs_upper"], np.round(x["D"][:8], 4).tolist()))


if __name__ == "__main__":
    main()
