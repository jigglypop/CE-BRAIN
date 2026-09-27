"""C3-1: 잠들기 직전의 방향이 논렘 동안 현재 상태에 남는가 (전제 C3).

명제: 잠들기 직전 깸의 내부 방향 θ_pre(과거)가 뒤이은 논렘의 내부 방향 θ(t)(현재)에 남고, 정렬
a(t) = E[cos(θ(t) − θ_pre)]는 흔적 시간상수 τ_h로 지수 감쇠한다: a(t) = A·exp(−t/τ_h).
흔적 없는 식(τ_h = 0, 현재가 과거와 무관): a(t) = 0.
자료(원장): dandi-000939-extract의 머리방향 세포(저자 분류). 선호 방향 φ_i는 wake_square 조율곡선의 원형 평균.
주 검사는 첫 home_cage(탐색 전), 재현은 둘째 home_cage(탐색 뒤).
방법: 10 s 이상의 깸 바로 뒤 논렘을 한 사건으로 잡는다. θ_pre는 그 깸의 마지막 10 s, θ(t)는 논렘 1 s 창의
집단 벡터 angle(Σ_i (n_i − n̄_i)·e^{iφ_i}) (n̄_i = 같은 구간·같은 상태의 평균 발화로 기대한 수).
지연 칸 [0,15), [15,30), [30,60), [60,120), [120,240), [240,480) s마다 a(t)를 모으고, θ_pre를 세션 안에서
사건끼리 섞은 순열 1000번의 평균을 빼 보정한다. 표준오차는 사건 부트스트랩 1000번.
판정(실행 전 고정):
- 사건 ≥ 50, 세션 ≥ 5 (주 검사)
- 흔적 존재: 첫 칸 정렬이 순열 분포의 99번째 백분위를 넘는다
- 정확도: 지수식 χ²/자유도 ≤ 2
- 역증명: 지수식 ≤ 2 < 흔적 없는 식
- 재현(둘째 home_cage): 흔적 존재와 역증명 통과
"""

import numpy as np
from scipy.optimize import curve_fit

from research import harness
from research.c4_1_metric_hd import GRID, load, tuning, windows

PRE, WINDOW = 10.0, 1.0
LAGS = np.array([0, 15, 30, 60, 120, 240, 480.0])
PERMUTATIONS, BOOTSTRAP, TOP, CHI2 = 1000, 1000, 99, 2.0


def preferred(row):
    """Preferred direction of every head-direction cell: circular mean of its wake_square tuning curve."""
    counts, direction, _ = windows(*load(row, "wake_square"))
    return np.angle(tuning(counts, direction) @ np.exp(1j * GRID))


def home(row, index):
    """HD-cell spike trains and sleep-scored states inside one home_cage epoch, or None."""
    with np.load(harness.path(row)) as z:
        spans = [(a, b) for t, a, b in zip(z["ep_tag"], z["ep_start"], z["ep_stop"]) if t == "home_cage"]
        if len(spans) <= index:
            return None
        a, b = spans[index]
        times, ends = z["spike_times"], z["spike_times_index"].astype(np.int64)
        cells = [times[s:e] for s, e, k in zip(np.r_[0, ends[:-1]], ends, z["is_head_direction"]) if k]
        states = [(s, e, x) for s, e, x in zip(z["ss_start"], z["ss_stop"], z["ss_state"]) if s >= a and e <= b]
    return cells, states


def rates(cells, states, name):
    spans = [(s, e) for s, e, x in states if x == name]
    return np.array([sum(((c >= s) & (c < e)).sum() for s, e in spans) for c in cells]) / sum(e - s for s, e in spans)


def direction(cells, edges, rate, phi):
    """Population-vector direction of the activity above expectation in each window between edges."""
    counts = np.stack([np.histogram(c, edges)[0] for c in cells])
    return np.angle(((counts - rate[:, None] * np.diff(edges)) * np.exp(1j * phi)[:, None]).sum(0))


def events(cells, states, phi):
    """(θ_pre, window lags, θ(t)) for every NREM bout that directly follows ≥ PRE s of wake."""
    wake, nrem = rates(cells, states, "wake"), rates(cells, states, "nrem")
    found = []
    for (s0, e0, x0), (s1, e1, x1) in zip(states, states[1:]):
        if x0 == "wake" and x1 == "nrem" and e0 - s0 >= PRE and 0 <= s1 - e0 <= 1:  # 점수는 1 s 단위
            edges = np.arange(s1, min(e1, s1 + LAGS[-1]), WINDOW)
            if len(edges) > 1:
                pre = direction(cells, np.array([e0 - PRE, e0]), wake, phi)[0]
                found.append((pre, edges[:-1] - s1 + WINDOW / 2, direction(cells, edges, nrem, phi)))
    return found


class Pool:
    """Windows of all events flattened for fast permutation and bootstrap curves."""

    def __init__(self, sessions):
        self.pre, self.group, owner, lag, theta = [], [], [], [], []
        for g, found in enumerate(sessions):
            for pre, lags, th in found:
                owner.append(np.full(len(lags), len(self.pre)))
                self.pre.append(pre)
                self.group.append(g)
                lag.append(lags)
                theta.append(th)
        self.pre, self.group = np.array(self.pre), np.array(self.group)
        self.owner, self.lag, self.theta = map(np.concatenate, (owner, lag, theta))
        self.bin = np.digitize(self.lag, LAGS) - 1

    def curve(self, pre=None, weight=None):
        w = np.ones(len(self.pre)) if weight is None else weight
        c = np.cos(self.theta - (self.pre if pre is None else pre)[self.owner]) * w[self.owner]
        return np.bincount(self.bin, c, len(LAGS) - 1) / np.bincount(self.bin, w[self.owner], len(LAGS) - 1)

    def shuffled(self, rng):
        pre = self.pre.copy()
        for g in np.unique(self.group):
            at = np.flatnonzero(self.group == g)
            pre[at] = rng.permutation(pre[at])
        return pre


def analyse(pool):
    """Permutation-corrected alignment per lag bin, bootstrap SE, and the two fits."""
    rng = np.random.default_rng(0)
    null = np.array([pool.curve(pool.shuffled(rng)) for _ in range(PERMUTATIONS)])
    raw = pool.curve()
    a = raw - null.mean(0)
    boot = np.array([pool.curve(weight=np.bincount(rng.integers(0, len(pool.pre), len(pool.pre)),
                                                   minlength=len(pool.pre)).astype(float))
                     for _ in range(BOOTSTRAP)])
    se = boot.std(0)
    lag = np.bincount(pool.bin, pool.lag, len(LAGS) - 1) / np.bincount(pool.bin, minlength=len(LAGS) - 1)
    model = lambda t, amplitude, tau: amplitude * np.exp(-t / tau)
    (amplitude, tau), _ = curve_fit(model, lag, a, p0=(max(a[0], 1e-3), 60.0), sigma=se,
                                    bounds=([0, 1], [1, 1e4]))
    return {"events": len(pool.pre), "lag": lag.tolist(), "alignment": a.tolist(), "se": se.tolist(),
            "first_bin_null_top": float(np.percentile(null[:, 0] - null.mean(0)[0], TOP)),
            "amplitude": float(amplitude), "tau_s": float(tau),
            "chi2_trace": float(np.sum(((a - model(lag, amplitude, tau)) / se) ** 2) / (len(a) - 2)),
            "chi2_none": float(np.sum((a / se) ** 2) / len(a))}


def main():
    rows = [r for r in harness.registered("dandi-000939-extract") if r["asset"].endswith(".npz")]
    harness.verify(rows)
    sessions = {0: [], 1: []}
    for row in rows:
        phi = preferred(row)
        if len(phi) < 10:
            continue
        for index in sessions:
            loaded = home(row, index)
            if loaded is not None:
                sessions[index].append(events(*loaded, phi))
    first, second = analyse(Pool(sessions[0])), analyse(Pool(sessions[1]))
    result = harness.record(
        "c3_1_sleep_trace", "C3",
        "잠들기 직전 깸의 내부 방향이 논렘의 현재 상태에 남고, 그 정렬은 흔적 시간상수 τ_h로 지수 감쇠한다",
        "실측: DANDI:000939 생쥐 후구상 머리방향 세포, 홈 케이지 수면 (주 검사 탐색 전, 재현 탐색 뒤)",
        {"events": harness.check(first["events"], 50),
         "sessions": harness.check(sum(1 for s in sessions[0] if s), 5),
         "trace_present": harness.check(first["alignment"][0] - first["first_bin_null_top"], low=0),
         "accuracy": harness.check(first["chi2_trace"], high=CHI2),
         "replication_trace": harness.check(second["alignment"][0] - second["first_bin_null_top"], low=0),
         "replication_reverse": harness.check(min(second["chi2_none"] - CHI2, CHI2 - second["chi2_trace"]), low=0)},
        rows,
        proof=harness.reverse("흔적 h (τ_h > 0)", first["chi2_trace"], first["chi2_none"], CHI2),
        first=first, second=second)
    print(result["verdict"], "| 첫 home_cage:", {k: first[k] for k in ("events", "amplitude", "tau_s", "chi2_trace", "chi2_none")})
    print("정렬", np.round(first["alignment"], 4), "±", np.round(first["se"], 4), "| 첫 칸 순열 99%:", round(first["first_bin_null_top"], 4))
    print("둘째 home_cage:", {k: second[k] for k in ("events", "amplitude", "tau_s", "chi2_trace", "chi2_none")},
          "| 정렬", np.round(second["alignment"], 4))


if __name__ == "__main__":
    main()
