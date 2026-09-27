"""C3-3: 흔적은 과거 내부 방향으로의 되돌림이다 (전제 C3).

명제: 논렘의 내부 방향은 빠르게 떠돌지만(문헌: 서파 수면 각속도가 깸의 약 10배), 잠들기 전 내부 방향과의
정렬은 자유 확산이 허락하는 것보다 오래 남는다. 되돌리는 중심은 잠든 동안의 실제 머리 방향(현재 감각 입력)이 아니라
잠들기 전 내부 방향(과거)이다.
식:
- 자유 확산(되돌림 없음, 독립 증분): 정렬 a(t) = a(0)·φ(t), 논렘 안 자기상관 c(Δ) = κ²·φ(Δ) (κ: 해독 잡음).
  φ(1 s) ≤ 1이므로 κ를 몰라도 a(t) ≤ a_free(t) = a(0)·c(t)/c(1 s)
- 되돌림: a(t)가 a_free(t)를 넘는다
- 과거 대 현재: 논렘 창의 방향 u = α·p + β·h + 잡음 (p: 잠들기 전 내부 방향, h: 그 창의 실제 머리 방향, 세션 평균을
  뺀 복소 최소제곱). 과거가 중심이면 Re α > Re β
생물 기준값: Peyrache et al. 2015 (Nat Neurosci 18:569, 000056의 원 논문): 서파 수면에서 내부 방향의 각속도가
깸의 약 10배이고, 쌍 교차 상관이 그만큼 시간 압축된다. 선호 방향 차 < 30° 쌍의 교차 상관(독립 기대 대비)에서
> 120° 쌍의 것을 뺀 곡선의 반치 반폭을 깸과 논렘에서 재고, 그 비를 기준값과 견준다.
자료(원장): dandi-000056 (주), dandi-000939-extract (자유 확산 한계의 재현; 수면 중 머리 추적이 부분적이라
과거 대 현재는 000056만). 사건과 창은 C3-2와 같다.
판정(실행 전 고정):
- 000056: 세션 ≥ 5, 사건 ≥ 50
- 도구 검증(000056): 깸 1 s 창에서 내부 방향과 실제 머리 방향의 정렬 ≥ 0.5
- 기준값: 000056의 깸/논렘 반치 반폭 비가 5–20 (문헌 약 10)
- 되돌림(000056, 000939 각각): 지연 ≥ 60 s 칸들에서 a − a_free 평균의 부트스트랩 1% 백분위 > 0
- 과거 우세(000056): 지연 ≥ 60 s 창에서 Re α − Re β의 부트스트랩 1% 백분위 > 0
- 역증명(000056): 지수식 χ²/자유도 ≤ 2 < 자유 확산 한계 a_free의 χ²/자유도
"""

import cefast
import numpy as np

from research import harness, store
from research import c3_2_trace_replication as c32
from research.c3_1_sleep_trace import BOOTSTRAP, CHI2, LAGS, PERMUTATIONS, PRE, WINDOW
from research.c4_1_metric_hd import GRID, tuning

LONG, SPAN, BIN, HALF = 60.0, int(LAGS[-1]), 0.01, 1000
CLOSE, FAR, LITERATURE = np.radians(30), np.radians(120), (5.0, 20.0)
K = len(LAGS) - 1


def head_angle(s):
    t, blue = s.series("blue")
    red = s["red"]
    ok = (blue > 0).all(1) & (red > 0).all(1)
    return t, np.where(ok, np.arctan2(red[:, 1] - blue[:, 1], red[:, 0] - blue[:, 0]), np.nan)


def at(t, angle, times):
    """Head angle at each time from the nearest sample within 0.1 s, else NaN."""
    k = np.searchsorted(t, times).clip(1, len(t) - 1)
    k -= (times - t[k - 1]) < (t[k] - times)
    return np.where(np.abs(t[k] - times) < 0.1, angle[k], np.nan)


def events(s, phi, table, wake, nrem, limit=None, head=None):
    """Per NREM bout after ≥ PRE s of wake: θ_pre, window lags, θ(t) and the actual head at each window."""
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
                lags = edges[:-1] - s1 + WINDOW / 2
                found.append({"pre": c32.direction(s, [e0 - PRE, e0], rate[wake], phi)[0], "lags": lags,
                              "theta": c32.direction(s, edges, rate[nrem], phi),
                              "head": at(*head, s1 + lags) if head else np.full(len(lags), np.nan)})
    return found


def profile(s, phi, starts, stops):
    """Pooled cross-correlograms over expectation: (close-pair sums, far-pair sums, their expectations)."""
    sub = s.within(starts, stops)
    g = cefast.ccg(sub.spikes, sub.ends, sub.spikes, sub.ends, BIN, HALF).astype(float)
    n = np.diff(np.r_[0, sub.ends]).astype(float)
    expected = np.outer(n, n) * BIN / (stops - starts).sum()
    d = np.abs(np.angle(np.exp(1j * (phi[:, None] - phi[None, :]))))
    close, far = (d < CLOSE) & ~np.eye(len(phi), dtype=bool), d > FAR
    return np.stack([g[close].sum(0), g[far].sum(0)]), np.array([expected[close].sum(), expected[far].sum()])


def half_width(sums, expected):
    """Half width at half maximum (s) of the close-minus-far correlogram, symmetrised."""
    ratio = sums / expected[:, None] - 1
    p = ratio[0] - ratio[1]
    p = (p[HALF:] + p[HALF::-1]) / 2
    below = np.flatnonzero(p <= p[0] / 2)
    if p[0] <= 0 or not len(below):
        return np.nan
    k = below[0]
    return float(BIN * (k - 1 + (p[k - 1] - p[0] / 2) / (p[k - 1] - p[k])))


def session_056(row):
    s = store.load(row)
    t, angle = head_angle(s)
    start, stop = s.intervals("states", "Awake")
    counts, direction = c32.windows(s, t, angle, zip(start, stop))
    f = tuning(counts, direction)
    hd = (np.abs(f @ np.exp(1j * GRID)) / f.sum(1) >= c32.R_HD) & (f.max(1) >= c32.PEAK_HD)
    if hd.sum() < c32.MIN_CELLS:
        return None
    s, phi = s.units(hd), np.angle(f[hd] @ np.exp(1j * GRID))
    edges = np.arange(start.min(), stop.max(), WINDOW)
    mid = edges[:-1] + WINDOW / 2
    awake = np.zeros(len(mid), bool)
    for a, b in zip(start, stop):
        awake |= (edges[:-1] >= a) & (edges[1:] <= b)
    rate = s.window_counts(start, stop).sum(1) / (stop - start).sum()
    wake_theta = c32.direction(s, edges, rate, phi)[awake]
    wake_head = at(t, angle, mid[awake])
    ok = np.isfinite(wake_head)
    nrem = s.intervals("states", "Non-REM")
    return {"events": events(s, phi, "states", "Awake", "Non-REM", head=(t, angle)),
            "wake_alignment": (float(np.cos(wake_theta[ok] - wake_head[ok]).sum()), int(ok.sum())),
            "wake": profile(s, phi, start, stop), "nrem": profile(s, phi, *nrem)}


def session_939(row):
    s = store.load(row)
    s = s.units(s["unit_is_head_direction"] == 1)
    (a,), (b,) = s.intervals("epochs", "wake_square")
    t, angle = s.series("head")
    inside = (t >= a) & (t < b)
    f = tuning(*c32.windows(s, t[inside], angle[inside], [(a, b)]))
    if len(f) < c32.MIN_CELLS:
        return None
    phi = np.angle(f @ np.exp(1j * GRID))
    home = s.intervals("epochs", "home_cage")
    limit = (home[0][0], home[1][0])
    start, stop = s.intervals("sleep_states")
    label = s["sleep_states_label"]
    keep = (start >= limit[0]) & (stop <= limit[1])
    wake = keep & (label == "wake")
    nrem = keep & (label == "nrem")
    return {"events": events(s, phi, "sleep_states", "wake", "nrem", limit),
            "wake": profile(s, phi, start[wake], stop[wake]), "nrem": profile(s, phi, start[nrem], stop[nrem])}


def analyse(sessions, rng):
    """Alignment, the free-diffusion bound and the past/present regression, jointly bootstrapped over events."""
    found = [(g, e) for g, x in enumerate(sessions) for e in x["events"]]
    group = np.array([g for g, _ in found])
    ev = [e for _, e in found]
    E = len(ev)
    pre = np.array([e["pre"] for e in ev])
    u = [np.exp(1j * e["theta"]) for e in ev]
    b = [np.digitize(e["lags"], LAGS) - 1 for e in ev]
    cos = np.array([np.bincount(bb, uu.real, K) for bb, uu in zip(b, u)])
    sin = np.array([np.bincount(bb, uu.imag, K) for bb, uu in zip(b, u)])
    count = np.array([np.bincount(bb, minlength=K) for bb in b])
    first = np.array([uu[0] for uu in u])
    mean = {g: np.concatenate([uu for gg, uu in zip(group, u) if gg == g]).mean() for g in np.unique(group)}
    acf, pairs, windows = (np.zeros((E, SPAN), complex), np.zeros((E, SPAN)), np.zeros((E, SPAN)))
    for i, uu in enumerate(u):
        L = len(uu)
        f = np.fft.fft(uu, 2 * L)
        acf[i, :L] = np.fft.ifft(f * np.conj(f))[:L] - (L - np.arange(L)) * abs(mean[group[i]]) ** 2
        pairs[i, :L] = L - np.arange(L)
        windows[i, :L] = 1
    to_bin = np.zeros((SPAN, K))
    to_bin[np.arange(SPAN), np.digitize(np.arange(SPAN) + WINDOW / 2, LAGS) - 1] = 1

    def curves(p, w):
        return ((w * np.cos(p)) @ cos + (w * np.sin(p)) @ sin) / (w @ count), \
            (w * (first * np.exp(-1j * p)).real).sum(-1) / w.sum(-1)

    shuffled = np.tile(pre, (PERMUTATIONS, 1))
    for g in np.unique(group):
        at_g = np.flatnonzero(group == g)
        shuffled[:, at_g] = rng.permuted(shuffled[:, at_g], axis=1)
    null_a, null_0 = (x.mean(0) for x in curves(shuffled, np.ones((1, E))))

    def bound(w):
        a, a0 = curves(pre[None], w)
        a, a0 = a - null_a, a0 - null_0
        paired = w @ pairs
        c = np.divide((w @ acf).real, paired, out=np.zeros_like(paired), where=paired > 0)  # 짝 없는 지연은 0 창
        ratio = c / c[:, 1:2]
        ratio[:, 0] = 1
        n = w @ windows
        return a, a0[:, None] * ((ratio * n) @ to_bin) / (n @ to_bin), c

    weight = np.stack([np.bincount(rng.integers(0, E, E), minlength=E) for _ in range(BOOTSTRAP)]).astype(float)
    a, free, c = (x[0] for x in bound(np.ones((1, E))))
    boot_a, boot_free, _ = bound(weight)
    long = LAGS[:-1] >= LONG
    excess = (boot_a - boot_free)[:, long].mean(1)
    se_a, se_diff = boot_a.std(0), (boot_a - boot_free).std(0)
    result = {"sessions": len(np.unique(group)), "events": E, "alignment": a.tolist(), "free_bound": free.tolist(), "se": se_a.tolist(),
              "self_correlation_1_10_60_s": [float(c[k] / c[1]) for k in (1, 10, 60)],
              "excess_long": float((a - free)[long].mean()), "excess_long_p1": float(np.percentile(excess, 1)),
              "chi2_free": float(np.sum(((a - free) / se_diff) ** 2) / K)}
    lag_mid = np.array([np.mean(np.concatenate([e["lags"][bb == k] for e, bb in zip(ev, b)])) for k in range(K)])
    result["lag"] = lag_mid.tolist()
    result["chi2_exp"] = c32.fit("exp", lag_mid, a, se_a)["chi2_dof"]
    result["exp"] = c32.fit("exp", lag_mid, a, se_a)["params"]
    heads = [e["head"] for e in ev]
    if any(np.isfinite(h).any() for h in heads):
        result.update(regression(ev, group, u, heads, weight))
    return result


def regression(ev, group, u, heads, weight):
    """u = α·p + β·h on windows ≥ LONG s with a tracked head, session means removed, bootstrapped over events."""
    sums = np.zeros((len(ev), 5), complex)  # Σ p̄u, Σ h̄u, Σ p̄h, Σ|p|², Σ|h|²
    used = 0
    for g in np.unique(group):
        idx = np.flatnonzero(group == g)
        use = [(i, (ev[i]["lags"] >= LONG) & np.isfinite(heads[i])) for i in idx]
        uu = np.concatenate([u[i][m] for i, m in use]) if use else np.empty(0)
        if not len(uu):
            continue
        mu = uu.mean()
        mp = np.mean([np.exp(1j * ev[i]["pre"]) for i, m in use if m.any()])
        mh = np.concatenate([np.exp(1j * heads[i][m]) for i, m in use]).mean()
        used += len(uu)
        for i, m in use:
            x, h = u[i][m] - mu, np.exp(1j * heads[i][m]) - mh
            p = np.exp(1j * ev[i]["pre"]) - mp
            sums[i] = [np.conj(p) * x.sum(), (np.conj(h) * x).sum(), (np.conj(p) * h).sum(),
                       m.sum() * abs(p) ** 2, (abs(h) ** 2).sum()]

    def solve(w):
        s = w @ sums
        det = s[..., 3] * s[..., 4] - s[..., 2] * np.conj(s[..., 2])
        alpha = (s[..., 4] * s[..., 0] - s[..., 2] * s[..., 1]) / det
        beta = (s[..., 3] * s[..., 1] - np.conj(s[..., 2]) * s[..., 0]) / det
        return alpha, beta

    alpha, beta = solve(np.ones(len(ev)))
    boot_alpha, boot_beta = solve(weight)
    total = sums.sum(0)
    return {"alpha": [float(alpha.real), float(alpha.imag)], "beta": [float(beta.real), float(beta.imag)],
            "past_minus_present_p1": float(np.percentile(boot_alpha.real - boot_beta.real, 1)),
            "past_present_collinearity": float(abs(total[2]) / np.sqrt(total[3].real * total[4].real)),
            "regression_windows": used}


def pooled(sessions, state):
    sums = sum(x[state][0] for x in sessions)
    expected = sum(x[state][1] for x in sessions)
    return half_width(sums, expected)


def main():
    rows56 = harness.registered("dandi-000056")
    rows39 = [r for r in harness.registered("dandi-000939-extract") if r["asset"].endswith(".npz")]
    harness.verify(rows56 + rows39)
    s56 = [x for x in map(session_056, rows56) if x]
    s39 = [x for x in map(session_939, rows39) if x]
    r56, r39 = analyse(s56, np.random.default_rng(0)), analyse(s39, np.random.default_rng(0))
    for r, s in ((r56, s56), (r39, s39)):
        r["half_width_wake_s"], r["half_width_nrem_s"] = pooled(s, "wake"), pooled(s, "nrem")
        r["compression"] = r["half_width_wake_s"] / r["half_width_nrem_s"]
    wake_sum = sum(x["wake_alignment"][0] for x in s56)
    wake_n = sum(x["wake_alignment"][1] for x in s56)
    r56["wake_head_alignment"] = wake_sum / wake_n
    result = harness.record(
        "c3_3_restoring", "C3",
        "논렘 내부 방향은 빠르게 떠돌지만 잠들기 전 내부 방향과의 정렬은 자유 확산이 허락하는 것보다 오래 남고, "
        "되돌리는 중심은 잠든 동안의 실제 머리 방향이 아니라 잠들기 전 내부 방향이다",
        "Peyrache et al. 2015 Nat Neurosci 18:569 (doi:10.1038/nn.3968): 서파 수면에서 내부 방향 각속도 약 10배 "
        "(쌍 교차 상관의 시간 압축). 실측: DANDI:000056 (주), DANDI:000939 (자유 확산 한계 재현)",
        {"sessions": harness.check(r56["sessions"], 5),
         "events": harness.check(r56["events"], 50),
         "instrument": harness.check(r56["wake_head_alignment"], 0.5),
         "literature_compression": harness.check(r56["compression"], *LITERATURE),
         "restoring_000056": harness.check(r56["excess_long_p1"], low=0),
         "restoring_000939": harness.check(r39["excess_long_p1"], low=0),
         "past_over_present": harness.check(r56.get("past_minus_present_p1"), low=0)},
        rows56 + rows39,
        proof=harness.reverse("과거 방향으로의 되돌림", r56["chi2_exp"], r56["chi2_free"], CHI2),
        dandi_000056=r56, dandi_000939=r39)
    print(result["verdict"])
    for name, r in (("000056", r56), ("000939", r39)):
        print(name, {k: (np.round(v, 3).tolist() if isinstance(v, (list, float)) else v) for k, v in r.items()})


if __name__ == "__main__":
    main()
