"""C1-4: 같은 논렘 구간 집단으로 재면 흔적 시간상수는 세 자료에서 하나다 (전제 C1).

C1-3을 본 뒤 세운 새 단계다. τ_h는 000056에서 896–1,145 s, 000939에서 192–254 s, 001699에서 102–194 s로 달랐다(C3-2, C1-2·3).
자료의 논렘 구간 길이 중앙값이 같은 순서로 188 s, 70 s, 35 s다(사건 수만 세고 정렬은 보지 않음). 지연 t의 정렬에는 t보다 긴
구간만 들어가므로, 모든 지연을 섞은 설계는 자료마다 다른 구간 집단을 지연마다 바꿔 가며 잰다.
명제: 논렘 구간이 240 s 이상인 사건만 쓰고 지연을 240 s 안으로 자르면(모든 지연에 같은 사건), 세 자료의 정렬 감쇠를
τ_h 하나의 지수식 a_d(t) = A_d·e^{−t/τ_h}가 함께 맞추고, 자료마다 τ를 따로 두어도 유의하게 나아지지 않는다.
식: 공통 식의 흔적 τ_h ḣ = −h + x (ZOH 이산화는 A = −1, B = 1, Δ = dt/τ_h인 Mamba 셀과 같다). 정렬 a(t) = E[cos(θ(t) − θ_pre)].
생물 기준값: 문헌에 τ 값이 없어 서로 독립인 세 자료(두 종, 세 연구실)의 일치를 기준으로 삼는다(C3-2와 같다).
자료(원장): dandi-000056, dandi-000939-extract(첫 home_cage), dandi-001699(야생형). 사건·창·순열·부트스트랩은 C3-2와 같고
001699는 C1-3과 같다. 지연 칸 [0,15,30,60,120,240) s.
판정(실행 전 고정):
- 자료마다 집단 사건 ≥ 30
- 흔적 존재: 자료마다 첫 칸 정렬이 순열 분포의 99번째 백분위를 넘는다
- 정확도: 공통 τ 지수식의 공동 χ²/자유도 ≤ 2 (관측 15, 매개변수 4)
- 공통: χ²(공통 τ) − χ²(자료별 τ) ≤ 5.99 (자유도 2, p = 0.05)
- 정밀도: 공통 τ의 사건 부트스트랩 97.5%/2.5% ≤ 3
- 역증명: 공통 τ 지수식 ≤ 2 < 흔적 없는 식(a = 0)의 공동 χ²/자유도
보고(판정 아님): 모든 구간을 섞은 C3-2 설계를 같은 240 s 안에서 맞춘 자료별 τ와 공통성 Δχ².
"""

import numpy as np
from scipy.optimize import least_squares

from research import harness, store
from research import c3_2_trace_replication as c32
from research import c3_3_restoring as c33
from research.c3_1_sleep_trace import CHI2, LAGS, WINDOW
from research.c4_1_metric_hd import GRID, tuning

SPAN, COMMON, SPREAD, MIN_EVENTS = 240.0, 5.99, 3.0, 30
K = int(np.sum(LAGS < SPAN))  # 240 s 안의 지연 칸 수


def session_1699(row):
    """(θ_pre, lags, θ) of the sleep events of one wild-type session with ≥ 10 head-direction cells (as in C1-3)."""
    s = store.load(row)
    t, angle = s.series("head")
    angle = np.mod(angle, 2 * np.pi)
    f = tuning(*c32.windows(s, t, angle, [(t[0], t[-1])]))
    hd = (np.abs(f @ np.exp(1j * GRID)) / f.sum(1) >= c32.R_HD) & (f.max(1) >= c32.PEAK_HD)
    if hd.sum() < c32.MIN_CELLS:
        return None
    found = c33.events(s.units(hd), np.angle(f[hd] @ np.exp(1j * GRID)), "sleep_stages", "wake", "nrem")
    return [(e["pre"], e["lags"], e["theta"]) for e in found]


def cohort(sessions, span=SPAN):
    """Events whose NREM bout lasts at least `span`, cut to the lags below it, so every lag holds the same events."""
    return [[(p, lags[lags < span], theta[lags < span]) for p, lags, theta in found if lags[-1] >= span - WINDOW / 2]
            for found in sessions if found]


def cut(sessions, span=SPAN):
    """All events cut to the lags below `span` (the C3-2 design inside the same span)."""
    return [[(p, lags[lags < span], theta[lags < span]) for p, lags, theta in found] for found in sessions if found]


def curve(sessions, seed=0):
    """C3-2 alignment curve on the first K lag bins."""
    with np.errstate(invalid="ignore", divide="ignore"):
        c = c32.curves([f for f in sessions if f], np.random.default_rng(seed))
    return {"events": c["events"], "sessions": c["sessions"], "lag": c["lag"][:K], "alignment": c["alignment"][:K],
            "se": c["se"][:K], "boot": c["boot"][:, :K], "null_top": c["null_top"]}


def joint(curves, common=True, alignments=None):
    """Least-squares fit of a_d(t) = A_d·e^{−t/τ} with one τ (common) or one per data set; χ² and parameters."""
    alignments = [c["alignment"] for c in curves] if alignments is None else alignments
    n = len(curves)

    def residual(x):
        amp, tau = x[:n], np.exp(x[n:]) if not common else np.full(n, np.exp(x[n]))
        return np.concatenate([(a - amp[d] * np.exp(-c["lag"] / tau[d])) / c["se"]
                               for d, (c, a) in enumerate(zip(curves, alignments))])

    x0 = np.r_[[max(a[0], 0.05) for a in alignments], np.log(300.0) * np.ones(1 if common else n)]
    x = least_squares(residual, x0).x
    chi2 = float(np.sum(residual(x) ** 2))
    return {"amplitude": x[:n].tolist(), "tau": np.exp(x[n:]).tolist(), "chi2": chi2,
            "chi2_dof": chi2 / (n * K - len(x))}


def analyse(sets):
    curves = [curve(s) for s in sets]
    common, separate = joint(curves), joint(curves, common=False)
    none = float(sum(np.sum((c["alignment"] / c["se"]) ** 2) for c in curves))
    taus = [joint(curves, alignments=[c["boot"][i] for c in curves])["tau"][0] for i in range(len(curves[0]["boot"]))]
    each = [np.percentile([joint([c], alignments=[b])["tau"][0] for b in c["boot"]], [2.5, 97.5]).tolist()
            for c in curves]  # 보고만: 자료별 τ의 검정력
    return {"curves": [{k: (v.tolist() if isinstance(v, np.ndarray) else v) for k, v in c.items() if k != "boot"}
                       for c in curves], "tau_interval_each": each,
            "common": common, "separate": separate, "delta_chi2": common["chi2"] - separate["chi2"],
            "none_chi2_dof": none / (len(curves) * K), "tau_interval": np.percentile(taus, [2.5, 97.5]).tolist()}


def main():
    rows56 = harness.registered("dandi-000056")
    rows39 = [r for r in harness.registered("dandi-000939-extract") if r["asset"].endswith(".npz")]
    rows99 = harness.registered("dandi-001699")
    harness.verify(rows56 + rows39 + rows99)
    sessions = [[c32.session_056(r) for r in rows56], [c32.session_939(r) for r in rows39],
                [session_1699(r) for r in rows99]]
    fixed, pooled = analyse([cohort(s) for s in sessions]), analyse([cut(s) for s in sessions])
    names = ("dandi_000056", "dandi_000939", "dandi_001699")
    lo, hi = fixed["tau_interval"]
    checks = {f"events_{n}": harness.check(c["events"], MIN_EVENTS) for n, c in zip(names, fixed["curves"])}
    checks |= {f"trace_{n}": harness.check(c["alignment"][0] - c["null_top"], low=0) for n, c in zip(names, fixed["curves"])}
    checks |= {"accuracy": harness.check(fixed["common"]["chi2_dof"], high=CHI2),
               "common_tau": harness.check(fixed["delta_chi2"], high=COMMON),
               "precision": harness.check(hi / lo, high=SPREAD)}
    result = harness.record(
        "c1_4_common_trace_time", "C1",
        "논렘 구간이 240 s 이상인 같은 사건 집단으로 재면 세 자료(두 종, 세 연구실)의 정렬 감쇠를 흔적 시간상수 τ_h 하나의 "
        "지수식이 함께 맞춘다",
        "문헌에 τ 값이 없어 서로 독립인 세 자료의 일치를 기준으로 삼는다. 실측: DANDI:000056 (Peyrache et al. 2015), "
        "DANDI:000939, DANDI:001699 (Moore et al. 2025)",
        checks, rows56 + rows39 + rows99,
        proof=harness.reverse("흔적 h (공통 τ_h)", fixed["common"]["chi2_dof"], fixed["none_chi2_dof"], CHI2),
        fixed_cohort=fixed, all_bouts=pooled)
    print(result["verdict"], {k: v["passed"] for k, v in checks.items()})
    for name, r in (("같은 집단", fixed), ("모든 구간", pooled)):
        print(name, [c["events"] for c in r["curves"]], "공통 τ %.0f s (%s), χ²/자유도 %.2f, 자료별 τ %s, Δχ² %.2f" % (
            r["common"]["tau"][0], np.round(r["tau_interval"]).tolist(), r["common"]["chi2_dof"],
            np.round(r["separate"]["tau"]).tolist(), r["delta_chi2"]))


if __name__ == "__main__":
    main()
