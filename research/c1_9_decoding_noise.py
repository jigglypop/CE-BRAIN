"""C1-9: 1 s 창의 해독 오차는 창 사이 상관이 작다 — 관측 식의 독립 가정 (전제 C1).

C3-8을 본 뒤 세운 새 단계다. C3-8에서 적합에 쓰지 않은 관측(기록 자리를 5–15 s 벗어난 뒤 20 s의 정렬)을 모든 식이 4–7 SE 과대 예측했다
(실측 0.166 대 0.24–0.29). 공통 식의 관측 식은 창마다 독립인 해독 잡음을 둔다. 잡음이 창 사이에 상관되면 긴 가짜 이탈이 생겨 되돌아옴이
줄어들 수 있다. 모형만으로 계산하면(C1-7 해, ρ 0.435, 감싼 정규 AR(1) 잡음) 창 사이 상관 φ가 0·0.2·0.4·0.6·0.8일 때 R(5–15)이
0.233·0.226·0.228·0.232·0.190이므로, 이 불일치를 관측 잡음으로 설명하려면 φ ≥ 0.8이 필요하다.
명제: 000056 깸에서 머리가 거의 멈춘 1 s 창의 해독 오차(해독 방향 − 추적된 머리 방향, 머리 방향별 치우침을 뺌)는 창 사이 상관 φ(1)이
0.8보다 작다. 곧 짧은 이탈의 불일치는 관측 식의 독립 가정 탓이 아니다.
식: 오차 r_k를 감싼 정규 AR(1)로 보면 E cos(r_{k+Δ} − r_k) = exp(−σ²(1 − φ^Δ)), σ² = −2 ln|E e^{ir}|. 따라서
φ(Δ) = [1 + ln E cos(r_{k+Δ} − r_k)/σ²]^{1/Δ}.
관측: 방향 세포 ≥ 10인 세션, 깸 구간 안의 이어진 1 s 창. 해독은 C3-3과 같다(깸 평균 발화를 뺀 집단 벡터). 머리 방향은 창 안 추적 표본의
원형 평균(표본 ≥ 80%), 멈춤은 앞뒤 창과의 머리 변화가 모두 30°/s 미만. 치우침은 세션마다 머리 방향 30° 칸별 오차의 원형 평균이다.
생물 기준값: 관측 식은 해독 도구라 문헌값 대신, 같은 식이 불일치를 설명하는 데 필요한 크기(φ ≥ 0.8, 모형 계산)를 기준으로 삼는다.
자료(원장): dandi-000056. 사건 부트스트랩 대신 세션 부트스트랩 1000번.
판정(실행 전 고정):
- 멈춘 창 짝(Δ = 1) ≥ 1000
- 명제: φ(1)의 세션 부트스트랩 99% 백분위 < 0.8
보고(판정 아님): φ(2), φ(5), 움직임을 포함한 모든 창의 φ, 치우침의 크기, σ.
"""

import numpy as np

from research import c3_2_trace_replication as c32
from research import c3_3_restoring as c33
from research import harness, store
from research.c3_1_sleep_trace import BOOTSTRAP
from research.c4_1_metric_hd import GRID, tuning

WINDOW, STILL, COVER, BIAS_BINS, NEEDED, LAGS = 1.0, np.radians(30), 0.8, 12, 0.8, (1, 2, 5)


def session(row):
    """Per wake window: decoding error, head direction, whether the head is still, and the window's run id; or None."""
    s = store.load(row)
    t, angle = c33.head_angle(s)
    start, stop = s.intervals("states", "Awake")
    f = tuning(*c32.windows(s, t, angle, zip(start, stop)))
    hd = (np.abs(f @ np.exp(1j * GRID)) / f.sum(1) >= c32.R_HD) & (f.max(1) >= c32.PEAK_HD)
    if hd.sum() < c32.MIN_CELLS:
        return None
    s, phi = s.units(hd), np.angle(f[hd] @ np.exp(1j * GRID))
    rate = s.window_counts(start, stop).sum(1) / (stop - start).sum()
    step = np.median(np.diff(t))
    out = []
    for run, (a, b) in enumerate(zip(start, stop)):
        edges = np.arange(a, b, WINDOW)
        if len(edges) < 3:
            continue
        k = np.digitize(t, edges) - 1
        ok = (k >= 0) & (k < len(edges) - 1) & np.isfinite(angle)
        z = np.bincount(k[ok], np.exp(1j * angle[ok]).real, len(edges) - 1) + 1j * np.bincount(k[ok], np.exp(1j * angle[ok]).imag, len(edges) - 1)
        tracked = np.bincount(k[ok], minlength=len(edges) - 1) >= COVER * WINDOW / step
        head = np.where(tracked, np.angle(z), np.nan)
        error = np.angle(np.exp(1j * (c32.direction(s, edges, rate, phi) - head)))
        turn = np.abs(np.angle(np.exp(1j * np.diff(head)))) / WINDOW
        still = np.r_[False, turn < STILL] & np.r_[turn < STILL, False]
        out.append(np.stack([error, head, still, np.full(len(head), run)], 1))
    return np.concatenate(out) if out else None


def residuals(x):
    """Errors minus the session's mean error per 30° head bin (decoding bias)."""
    error, head = x[:, 0], x[:, 1]
    ok = np.isfinite(error)
    b = (np.mod(head, 2 * np.pi) / (2 * np.pi) * BIAS_BINS).astype(int).clip(0, BIAS_BINS - 1)
    bias = np.full(BIAS_BINS, 0j)
    for j in range(BIAS_BINS):
        m = ok & (b == j)
        bias[j] = np.exp(1j * error[m]).mean() if m.any() else 1.0
    return np.where(ok, np.angle(np.exp(1j * error) * np.conj(bias[b] / np.abs(bias[b]))), np.nan), np.abs(bias).mean()


def pair_sums(sessions, still_only):
    """Per session: Σ e^{ir}, count, and for each lag Σ cos(r_{k+Δ} − r_k) and pair count (consecutive, same wake run)."""
    rows = []
    for x in sessions:
        r, _ = residuals(x)
        still, run = x[:, 2].astype(bool), x[:, 3]
        use = np.isfinite(r) & (still if still_only else True)
        sums = [np.exp(1j * r[use]).sum(), use.sum()]
        for d in LAGS:
            pair = use[:-d] & use[d:] & (run[:-d] == run[d:])
            sums += [np.cos(r[d:][pair] - r[:-d][pair]).sum(), pair.sum()]
        rows.append(sums)
    return np.array(rows, complex)


def phi(s):
    """φ(Δ) from summed statistics (rows summed over sessions)."""
    sigma2 = -2 * np.log(np.abs(s[..., 0]) / s[..., 1].real)
    out = []
    for j, d in enumerate(LAGS):
        c = s[..., 2 + 2 * j].real / s[..., 3 + 2 * j].real
        out.append(np.clip(1 + np.log(c) / sigma2, 1e-9, None) ** (1 / d))
    return np.stack(out, -1), sigma2


def analyse(sessions, rng):
    result = {}
    for name, still in (("still", True), ("all", False)):
        rows = pair_sums(sessions, still)
        value, sigma2 = phi(rows.sum(0))
        w = np.stack([np.bincount(rng.integers(0, len(rows), len(rows)), minlength=len(rows)) for _ in range(BOOTSTRAP)])
        boot, _ = phi(w @ rows)
        result[name] = {"phi": value.tolist(), "phi_p99": np.percentile(boot, 99, axis=0).tolist(),
                        "sigma": float(np.sqrt(sigma2)), "pairs_lag1": int(rows[:, 3].real.sum()), "windows": int(rows[:, 1].real.sum())}
    result["bias_strength"] = float(np.mean([residuals(x)[1] for x in sessions]))
    return result


def main():
    rows = harness.registered("dandi-000056")
    harness.verify(rows)
    sessions = [x for x in map(session, rows) if x is not None]
    r = analyse(sessions, np.random.default_rng(0))
    still = r["still"]
    result = harness.record(
        "c1_9_decoding_noise", "C1",
        "깸에서 머리가 거의 멈춘 1 s 창의 해독 오차는 창 사이 상관 φ(1)이 0.8보다 작다: 짧은 이탈에서 식이 되돌아옴을 과대 예측하는 것은 관측 식의 "
        "독립 가정 탓이 아니다",
        "관측 도구의 성질이라 문헌값 대신 같은 식이 불일치를 설명하는 데 필요한 크기(φ ≥ 0.8, 모형 계산)를 기준으로 삼는다. 실측: DANDI:000056",
        {"pairs": harness.check(still["pairs_lag1"], 1000), "independent_enough": harness.check(still["phi_p99"][0], high=NEEDED)},
        rows, **r)
    print(result["verdict"], {k: v["passed"] for k, v in result["checks"].items()})
    for name in ("still", "all"):
        x = r[name]
        print(name, "phi(1,2,5)", np.round(x["phi"], 3).tolist(), "p99", np.round(x["phi_p99"], 3).tolist(),
              "sigma %.2f rad, pairs %d, windows %d" % (x["sigma"], x["pairs_lag1"], x["windows"]))
    print("bias strength (mean |mean error| per head bin) %.3f" % r["bias_strength"])


if __name__ == "__main__":
    main()
