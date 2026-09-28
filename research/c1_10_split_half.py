"""C1-10: 논렘 해독 잡음에는 느린 성분이 작다 — 반쪽 해독 (전제 C1).

C1-9를 본 뒤 세운 새 단계다. 깸의 1 s 창 해독 오차(해독 − 추적된 머리)는 빠른 성분과 상관 시간 약 27 s의 느린 성분(분산 41%, 5 s 상관 0.34)의
합이었고, 이 모양을 논렘 관측에 넣으면 C3-8의 짧은 이탈 불일치가 절반쯤 설명되었다. 느린 성분이 해독 잡음인지(관측 식에 넣어야 함), 내부 방향이
머리에서 천천히 벗어나는 실제 상태 차이인지(논렘 관측에 옮기면 두 번 셈)를 논렘에서 직접 가른다.
명제: 000056 논렘 1 s 창에서 방향 세포를 선호 방향 순서로 번갈아 나눈 두 반쪽의 해독 방향 차 d(상태는 지워지고 두 반쪽 잡음만 남는다)의 5 s
상관 C_d(5)가 깸 오차 느린 성분의 절반(0.17)보다 작다. 곧 논렘 해독 잡음에는 느린 성분이 작다.
식: 두 반쪽 잡음이 서로 독립이고 각자 상관 C_n(Δ)를 가지면 d의 상관은 C_n(Δ)다. 감싼 정규로 C(Δ) = 1 + ln E cos(d_{k+Δ} − d_k)/σ_d²,
σ_d² = −2 ln|E e^{id}|. 반쪽 구성의 치우침(두 반쪽의 방향별 해독 치우침 차)은 세션마다 전체 해독 방향 30° 칸별 d의 원형 평균으로 뺀다.
관측: C3-2 사건(깸 ≥ 10 s 바로 뒤 논렘, 첫 480 s), 방향 세포 ≥ 10인 세션, 각 반쪽은 논렘 평균 발화를 뺀 집단 벡터로 해독한다.
생물 기준값: 관측 도구의 성질이라 문헌값 대신 같은 관측의 깸 값(C1-9의 5 s 상관 0.34)을 기준으로 삼는다.
자료(원장): dandi-000056. 세션 부트스트랩 1000번.
판정(실행 전 고정):
- 창 ≥ 1000, 사건 ≥ 50
- 명제: C_d(5)의 세션 부트스트랩 99% 백분위 < 0.17
보고(판정 아님): C_d(1)·C_d(2)·C_d(10)·C_d(20), 사건 평균까지 뺀 C_d, σ_d.
"""

import numpy as np

from research import c3_2_trace_replication as c32
from research import c3_3_restoring as c33
from research import harness, store
from research.c3_1_sleep_trace import BOOTSTRAP, LAGS, PRE, WINDOW
from research.c4_1_metric_hd import GRID, tuning

BIAS_BINS, LIMIT, DELTAS, KEY = 12, 0.17, (1, 2, 5, 10, 20), 2  # KEY: DELTAS 안에서 5 s의 자리


def session(row):
    """Per NREM event: the full, half-A and half-B decoded directions of its 1 s windows; or None."""
    s = store.load(row)
    t, angle = c33.head_angle(s)
    awake = s.intervals("states", "Awake")
    f = tuning(*c32.windows(s, t, angle, zip(*awake)))
    hd = (np.abs(f @ np.exp(1j * GRID)) / f.sum(1) >= c32.R_HD) & (f.max(1) >= c32.PEAK_HD)
    if hd.sum() < c32.MIN_CELLS:
        return None
    s, phi = s.units(hd), np.angle(f[hd] @ np.exp(1j * GRID))
    half = np.zeros(len(phi), bool)
    half[np.argsort(phi)[::2]] = True  # 선호 방향 순서로 번갈아: 두 반쪽이 고리를 고르게 덮는다
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
                excess = (s.counts(edges) - rate["Non-REM"][:, None] * WINDOW) * np.exp(1j * phi)[:, None]
                out.append(np.stack([np.angle(excess.sum(0)), np.angle(excess[half].sum(0)), np.angle(excess[~half].sum(0))], 1))
    return out or None


def residual(events, demean=False):
    """d = half A − half B per window, minus the session's mean d per 30° bin of the full decoded direction."""
    full = np.concatenate([e[:, 0] for e in events])
    d = np.concatenate([np.angle(np.exp(1j * (e[:, 1] - e[:, 2]))) for e in events])
    b = (np.mod(full, 2 * np.pi) / (2 * np.pi) * BIAS_BINS).astype(int).clip(0, BIAS_BINS - 1)
    bias = np.array([np.exp(1j * d[b == j]).mean() if (b == j).any() else 1.0 for j in range(BIAS_BINS)])
    r = np.angle(np.exp(1j * d) * np.conj(bias[b] / np.abs(bias[b])))
    parts = np.split(r, np.cumsum([len(e) for e in events])[:-1])
    if demean:
        parts = [np.angle(np.exp(1j * p) * np.conj(np.exp(1j * p).mean() / abs(np.exp(1j * p).mean()))) for p in parts]
    return parts


def sums(sessions, demean=False):
    """Per session: Σ e^{id}, count, and per lag Σ cos(d_{k+Δ} − d_k) and pair count within events."""
    rows = []
    for events in sessions:
        parts = residual(events, demean)
        r = np.concatenate(parts)
        row = [np.exp(1j * r).sum(), len(r)]
        for lag in DELTAS:
            pairs = [(p[lag:], p[:-lag]) for p in parts if len(p) > lag]
            row += [sum(np.cos(a - b).sum() for a, b in pairs), sum(len(a) for a, _ in pairs)]
        rows.append(row)
    return np.array(rows, complex)


def correlation(s):
    """C(Δ) for every lag from summed statistics (last axis: the sums)."""
    sigma2 = -2 * np.log(np.abs(s[..., 0]) / s[..., 1].real)
    return np.stack([1 + np.log(s[..., 2 + 2 * j].real / s[..., 3 + 2 * j].real) / sigma2 for j in range(len(DELTAS))], -1), sigma2


def analyse(sessions, rng):
    out = {}
    for name, demean in (("bias_removed", False), ("event_mean_removed", True)):
        rows = sums(sessions, demean)
        value, sigma2 = correlation(rows.sum(0))
        w = np.stack([np.bincount(rng.integers(0, len(rows), len(rows)), minlength=len(rows)) for _ in range(BOOTSTRAP)])
        boot, _ = correlation(w @ rows)
        out[name] = {"C": value.tolist(), "C_p99": np.percentile(boot, 99, axis=0).tolist(), "sigma_d": float(np.sqrt(sigma2)),
                     "windows": int(rows[:, 1].real.sum())}
    out["events"] = sum(len(x) for x in sessions)
    return out


def main():
    rows = harness.registered("dandi-000056")
    harness.verify(rows)
    sessions = [x for x in map(session, rows) if x]
    r = analyse(sessions, np.random.default_rng(0))
    main_ = r["bias_removed"]
    result = harness.record(
        "c1_10_split_half", "C1",
        "논렘 1 s 창에서 방향 세포를 두 반쪽으로 나눈 해독 방향 차의 5 s 상관이 0.17보다 작다: 논렘 해독 잡음에는 느린 성분이 작고, 깸 오차의 느린 "
        "성분(C1-9)은 해독 잡음이 아니라 내부 방향과 머리의 실제 차이다",
        "관측 도구의 성질이라 문헌값 대신 같은 관측의 깸 값(C1-9의 5 s 상관 0.34)을 기준으로 삼는다. 실측: DANDI:000056",
        {"windows": harness.check(main_["windows"], 1000), "events": harness.check(r["events"], 50),
         "no_slow_noise": harness.check(main_["C_p99"][KEY], high=LIMIT)},
        rows, deltas=list(DELTAS), **r)
    print(result["verdict"], {k: v["passed"] for k, v in result["checks"].items()})
    for name in ("bias_removed", "event_mean_removed"):
        x = r[name]
        print(name, "C(1,2,5,10,20)", np.round(x["C"], 3).tolist(), "p99", np.round(x["C_p99"], 3).tolist(),
              "sigma_d %.2f, windows %d" % (x["sigma_d"], x["windows"]))


if __name__ == "__main__":
    main()
