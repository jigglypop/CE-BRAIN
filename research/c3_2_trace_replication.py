"""C3-2: 흔적의 독립 재현과 감쇠 식 (전제 C3).

명제: 잠들기 직전 깸의 내부 방향이 논렘에 남는 흔적은 다른 연구실·다른 동물·다른 영역(ADn 포함)의 자료에서도
나타난다. 그 감쇠는 미리 정한 경쟁 식 가운데 하나가 두 자료를 함께 맞추고, 흔적 시간상수 τ는 두 자료에서
1.5배 안으로 일치한다.
경쟁 식 (t: 논렘 시작부터의 지연):
- 없음 a = 0, 상수 a = c (감쇠 없는 현재 입력): 흔적 없는 식
- 지수 a = A·e^(−t/τ), 지수+바닥 a = A·e^(−t/τ) + c
자료(원장): 주 검사 dandi-000056 (Peyrache et al. 2015, ADn·PoSub, 생쥐 6마리, 부즈사키 연구실; C3-1과 다른 연구실·동물).
비교 dandi-000939-extract의 첫 home_cage (C3-1과 같은 사건).
방법: C3-1과 같다. 깸 ≥ 10 s 바로 뒤(1 s 안) 논렘을 한 사건으로 잡고, θ_pre는 깸 마지막 10 s, θ(t)는 논렘 1 s 창의
집단 벡터(기대 발화를 뺀 수)로 읽는다. 지연 칸 [0,15,30,60,120,240,480) s, 세션 안 순열 1000번 보정, 사건 부트스트랩
1000번. 칸은 모두 반열린 구간이다. 000939의 방향 세포는 저자 분류, 000056은 깸 조율곡선(6° 칸, σ 12°)의 평균 벡터
길이 ≥ 0.3이고 최고 발화 ≥ 1 Hz인 단위다. 000056의 머리 방향은 두 LED를 잇는 방향이며 두 LED 좌표가 모두 양수인
표본만 쓴다. 방향 세포 ≥ 10인 세션만 쓴다.
공통 식 선택(실행 전 고정): 두 자료 χ² 합에서 지수+바닥이 지수보다 5.99(자유도 2, p = 0.05) 넘게 작으면 지수+바닥,
아니면 지수.
판정(실행 전 고정):
- 000056: 세션 ≥ 5, 사건 ≥ 50
- 흔적 존재(000056): 첫 칸 정렬이 순열 분포의 99번째 백분위를 넘는다
- 정확도: 공통 식 χ²/자유도 ≤ 2 (000056, 000939 각각)
- 일치: τ(000056) / τ(000939)가 1/1.5–1.5
- 역증명(000056): 공통 식 ≤ 2 < 흔적 없는 두 식(없음, 상수) 중 나은 것의 χ²/자유도
"""

import numpy as np
from scipy.optimize import curve_fit

from research import harness, store
from research.c3_1_sleep_trace import BOOTSTRAP, CHI2, LAGS, PERMUTATIONS, PRE, TOP, WINDOW
from research.c4_1_metric_hd import GRID, T, tuning

MIN_CELLS, R_HD, PEAK_HD, AGREE, SELECT = 10, 0.3, 1.0, 1.5, 5.99
MODELS = {  # 이름: (식, 초기값, 경계)
    "none": (lambda t: 0 * t, (), ((), ())),
    "constant": (lambda t, c: c + 0 * t, (0.1,), ((-1,), (1,))),
    "exp": (lambda t, a, tau: a * np.exp(-t / tau), (0.2, 100.0), ((0, 1), (1, 1e4))),
    "exp_floor": (lambda t, a, tau, c: a * np.exp(-t / tau) + c, (0.15, 60.0, 0.05), ((0, 1, -1), (1, 1e4, 1))),
}


def windows(s, t, angle, spans):
    """Spike counts and circular-mean head direction of the T windows inside spans with ≥ 80% tracking."""
    edges = np.arange(t[0], t[-1], T)
    k = np.clip(((t - t[0]) // T).astype(int), 0, len(edges) - 2)
    ok = np.isfinite(angle)
    samples = np.bincount(k[ok], minlength=len(edges) - 1)
    z = (np.bincount(k[ok], np.cos(angle[ok]), len(edges) - 1)
         + 1j * np.bincount(k[ok], np.sin(angle[ok]), len(edges) - 1))
    inside = np.zeros(len(edges) - 1, bool)
    for a, b in spans:
        inside |= (edges[:-1] >= a) & (edges[1:] <= b)
    valid = inside & (samples >= 0.8 * T / np.median(np.diff(t)))
    return s.counts(edges).T[valid], np.angle(z[valid]) % (2 * np.pi)


def direction(s, edges, rate, phi):
    """Population-vector direction of the activity above expectation in each window between edges."""
    counts = s.counts(np.asarray(edges, np.float64))
    return np.angle(((counts - rate[:, None] * np.diff(edges)) * np.exp(1j * phi)[:, None]).sum(0))


def events(s, phi, table, wake, nrem, limit=None):
    """(θ_pre, window lags, θ(t)) for every NREM bout that directly follows ≥ PRE s of wake."""
    start, stop = s.intervals(table)
    label = s[f"{table}_label"]
    if limit is not None:
        keep = (start >= limit[0]) & (stop <= limit[1])
        start, stop, label = start[keep], stop[keep], label[keep]
    rate = {x: s.window_counts(start[label == x], stop[label == x]).sum(1) / (stop - start)[label == x].sum()
            for x in (wake, nrem)}
    found = []
    for i in range(len(label) - 1):
        s0, e0, s1, e1 = start[i], stop[i], start[i + 1], stop[i + 1]
        if label[i] == wake and label[i + 1] == nrem and e0 - s0 >= PRE and 0 <= s1 - e0 <= 1:
            edges = np.arange(s1, min(e1, s1 + LAGS[-1]), WINDOW)
            if len(edges) > 1:
                pre = direction(s, [e0 - PRE, e0], rate[wake], phi)[0]
                found.append((pre, edges[:-1] - s1 + WINDOW / 2, direction(s, edges, rate[nrem], phi)))
    return found


def session_939(row):
    s = store.load(row)
    s = s.units(s["unit_is_head_direction"] == 1)
    (a,), (b,) = s.intervals("epochs", "wake_square")
    t, angle = s.series("head")
    inside = (t >= a) & (t < b)
    f = tuning(*windows(s, t[inside], angle[inside], [(a, b)]))
    if len(f) < MIN_CELLS:
        return None
    home = s.intervals("epochs", "home_cage")
    return events(s, np.angle(f @ np.exp(1j * GRID)), "sleep_states", "wake", "nrem", (home[0][0], home[1][0]))


def session_056(row):
    s = store.load(row)
    t, blue = s.series("blue")
    red = s["red"]
    angle = np.where((blue > 0).all(1) & (red > 0).all(1),
                     np.arctan2(red[:, 1] - blue[:, 1], red[:, 0] - blue[:, 0]), np.nan)
    start, stop = s.intervals("states", "Awake")
    f = tuning(*windows(s, t, angle, zip(start, stop)))
    hd = (np.abs(f @ np.exp(1j * GRID)) / f.sum(1) >= R_HD) & (f.max(1) >= PEAK_HD)
    if hd.sum() < MIN_CELLS:
        return None
    return events(s.units(hd), np.angle(f[hd] @ np.exp(1j * GRID)), "states", "Awake", "Non-REM")


def curves(sessions, rng):
    """Alignment per lag bin with its permutation null and event bootstrap, from per-event bin sums."""
    pre, group, sums, lag_sum = [], [], [], np.zeros(len(LAGS) - 1)
    for g, found in enumerate(sessions):
        for p, lags, theta in found:
            b = np.digitize(lags, LAGS) - 1
            sums.append([np.bincount(b, np.cos(theta), len(LAGS) - 1), np.bincount(b, np.sin(theta), len(LAGS) - 1),
                         np.bincount(b, minlength=len(LAGS) - 1)])
            lag_sum += np.bincount(b, lags, len(LAGS) - 1)
            pre.append(p)
            group.append(g)
    pre, group = np.array(pre), np.array(group)
    cos, sin, count = map(np.array, zip(*sums))

    def curve(p, w):
        return ((w * np.cos(p)) @ cos + (w * np.sin(p)) @ sin) / (w @ count)

    ones = np.ones((1, len(pre)))
    shuffled = np.tile(pre, (PERMUTATIONS, 1))
    for g in np.unique(group):
        at = np.flatnonzero(group == g)
        shuffled[:, at] = rng.permuted(shuffled[:, at], axis=1)
    null = curve(shuffled, ones)
    raw = curve(pre[None], ones)[0]
    weight = np.stack([np.bincount(rng.integers(0, len(pre), len(pre)), minlength=len(pre))
                       for _ in range(BOOTSTRAP)]).astype(float)
    boot = curve(pre[None], weight)
    return {"events": len(pre), "sessions": len(np.unique(group)), "lag": lag_sum / count.sum(0),
            "alignment": raw - null.mean(0), "se": boot.std(0), "boot": boot - null.mean(0),
            "null_top": float(np.percentile(null[:, 0] - null.mean(0)[0], TOP))}


def fit(name, lag, a, se):
    """Parameters, raw χ² and χ² per degree of freedom of one model."""
    model, p0, bounds = MODELS[name]
    params = curve_fit(model, lag, a, p0=p0, sigma=se, bounds=bounds, absolute_sigma=True)[0] if p0 else ()
    chi2 = float(np.sum(((a - model(lag, *params)) / se) ** 2))
    return {"params": [float(p) for p in params], "chi2": chi2, "chi2_dof": chi2 / (len(a) - len(p0))}


def analyse(sessions, seed):
    c = curves([f for f in sessions if f], np.random.default_rng(seed))
    c["fits"] = {name: fit(name, c["lag"], c["alignment"], c["se"]) for name in MODELS}
    return c


def tau_interval(c, name):
    """2.5–97.5% range of τ over the event bootstrap (fits that do not converge are left out)."""
    model, p0, bounds = MODELS[name]
    taus = []
    for b in c["boot"]:
        try:
            taus.append(curve_fit(model, c["lag"], b, p0=p0, sigma=c["se"], bounds=bounds)[0][1])
        except RuntimeError:
            continue
    return [float(np.percentile(taus, 2.5)), float(np.percentile(taus, 97.5))]


def main():
    rows56 = harness.registered("dandi-000056")
    rows39 = [r for r in harness.registered("dandi-000939-extract") if r["asset"].endswith(".npz")]
    harness.verify(rows56 + rows39)
    main56 = analyse([session_056(r) for r in rows56], 0)
    ref39 = analyse([session_939(r) for r in rows39], 0)
    gain = sum(c["fits"]["exp"]["chi2"] - c["fits"]["exp_floor"]["chi2"] for c in (main56, ref39))
    common = "exp_floor" if gain > SELECT else "exp"
    tau56, tau39 = main56["fits"][common]["params"][1], ref39["fits"][common]["params"][1]
    rival = min(main56["fits"]["none"]["chi2_dof"], main56["fits"]["constant"]["chi2_dof"])
    for c in (main56, ref39):
        c["tau_interval"] = tau_interval(c, common)
    result = harness.record(
        "c3_2_trace_replication", "C3",
        "잠들기 직전 방향의 흔적은 다른 연구실·동물·영역의 자료에서도 논렘에 남고, 미리 정한 경쟁 식 하나가 두 자료의 "
        "감쇠를 함께 맞추며, 흔적 시간상수 τ가 두 자료에서 1.5배 안으로 일치한다",
        "실측: 주 검사 DANDI:000056 (Peyrache et al. 2015, ADn·PoSub), 비교 DANDI:000939 첫 home_cage. "
        "문헌에 τ 값이 없어 서로 독립인 두 자료의 일치를 기준으로 삼는다",
        {"sessions": harness.check(main56["sessions"], 5),
         "events": harness.check(main56["events"], 50),
         "trace_present": harness.check(main56["alignment"][0] - main56["null_top"], low=0),
         "accuracy_000056": harness.check(main56["fits"][common]["chi2_dof"], high=CHI2),
         "accuracy_000939": harness.check(ref39["fits"][common]["chi2_dof"], high=CHI2),
         "tau_agreement": harness.check(tau56 / tau39, 1 / AGREE, AGREE)},
        rows56 + rows39,
        proof=harness.reverse("흔적 h (감쇠하는 정렬)", main56["fits"][common]["chi2_dof"], rival, CHI2),
        common_model=common, floor_gain_chi2=gain,
        **{name: {k: (v.tolist() if isinstance(v, np.ndarray) else v) for k, v in c.items() if k != "boot"}
           for name, c in (("dandi_000056", main56), ("dandi_000939", ref39))})
    print(result["verdict"], "| 공통 식:", common, "| 바닥 이득 Δχ²: %.2f" % gain)
    for name, c in (("000056", main56), ("000939", ref39)):
        print(name, "사건", c["events"], "세션", c["sessions"], "| 정렬", np.round(c["alignment"], 3), "±", np.round(c["se"], 3),
              "| 99%:", round(c["null_top"], 3))
        print("   ", {k: (np.round(v["params"], 3).tolist(), round(v["chi2_dof"], 2)) for k, v in c["fits"].items()},
              "| τ 구간", np.round(c["tau_interval"], 1))


if __name__ == "__main__":
    main()
