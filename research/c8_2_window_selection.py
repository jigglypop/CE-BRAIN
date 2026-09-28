"""C8-2: 표현은 한 번에 한 후보에 놓인다 — 1 s 창의 중간 성분은 창 안 전환의 합이다 (전제 C8).

C8-1(중간 성분 4%로 실패)을 본 뒤 세운 새 단계다. 장난감 합성에서 순수 선택도 봉우리가 초당 한 번쯤 후보를 바꾸면
1 s 창 평균이 C8-1과 같은 중간 비(0.15)를 만들었다.
명제: 논렘에서 잠들기 전 내부 방향(과거)과 잠든 머리 방향(현재)이 90–150° 갈등할 때, 1 s 창의 방향이 둘의 중간에
놓이는 초과분은 한 곳에 붙은 표현(섞임)이 아니라 창 안에서 과거와 현재에 번갈아 놓인 표현의 합이다.
식 (Mamba 게이트 h_t = (1 − g_t)h_{t−1} + g_t u_t에서 g_t ∈ {0, 1}이면 선택, 연속이면 섞임):
- 창의 집단 벡터는 초과 발화에 선형이라 1 s 벡터는 0.25 s 벡터 넷의 합이다: z = Σ_k z_k, z_k = Σ_i (n_ik − λ_i/4)e^{iφ_i}.
- 응집도 C = |Σ_k z_k| / Σ_k |z_k|. 한 곳에 붙은 창은 떠돎과 해독 잡음만큼 1보다 작다(C_붙음).
- 선택(도약, 이진 게이트): 중간에 놓인 초과 창은 과거 쪽 벡터와 현재 쪽 벡터가 반씩 더해진 것이라
  C_중간 = C_붙음 · cos(Δ/2) (Δ: 과거–현재 간격). 비 Q = C_중간/C_붙음의 예측은 중간 칸 창들의 cos(Δ/2) 평균이다.
- 섞임(선택 없음): 중간 창도 한 곳에 붙어 있어 Q = 1.
칸과 뺄셈 (1 s 방향이 중심 ±15° 안): 중간 m, 과거에 대한 중간의 거울 p′ = 2θ_pre − θ_mid, 현재에 대한 거울
h′ = 2θ_head − θ_mid, 반대 a = θ_mid + π, 과거, 현재. 중간 칸 = 배경 + 과거 꼬리 + 현재 꼬리 + 초과이고, 거울 칸은 같은
거리의 꼬리와 배경만 갖고(봉우리 대칭), 반대 칸은 배경만 갖는다. 그래서 초과의 개수와 C 합은
X = m − p′ − h′ + a, 붙은 창은 (과거 + 현재) − 2a다. 간격 150° 이하로 칸들이 겹치지 않는다.
생물 기준값: Kim et al. 2017 (Science 356:849): 두 입력이 90°·180° 떨어지면 봉우리는 중간으로 흐르지 않고 한쪽으로
도약한다(도약 = 이진 게이트이고, 그러면 Q = cos(Δ/2)).
자료(원장): dandi-000056. 사건과 창은 C8-1과 같고(1 s 창을 0.25 s 넷으로 나눔) 간격 90–150°만 쓴다.
설계 이력: 처음에는 전체식 무게의 창 축소비를 생성 모형 보정으로 예측하려 했으나, 1 s 무게 셋과 κ에 맞추는 보정이
두 번 수렴하지 않았고 같은 매개변수에서 혼합 적합이 복제마다 다른 해를 냈다. 0.25 s 실측을 보기 전에 적합이 필요 없는
이 선형 통계로 바꿨다.
판정(실행 전 고정):
- 창 ≥ 1000, 사건 ≥ 30
- 도구: 중간 칸 초과 창 수의 사건 부트스트랩 1% 백분위 > 0 (C8-1의 중간 성분이 이 창들에 있다)
- 선택: Q의 부트스트랩 99% 백분위 ≤ (Q_선택 + 1)/2
- 정확도: |log(Q/Q_선택)| ≤ log 1.5
- 역증명: |log(Q/Q_선택)| ≤ log 1.5 < |log Q| (섞임 Q = 1)
"""

import numpy as np

from research import harness, store
from research import c3_2_trace_replication as c32
from research import c3_3_restoring as c33
from research import c8_1_selection as c8
from research.c3_1_sleep_trace import LAGS, PRE, WINDOW
from research.c4_1_metric_hd import GRID, tuning

SHORT, HALF, WIDEST = 0.25, np.radians(15), np.radians(150)
PARTS, TOL, BOOT = int(WINDOW / SHORT), float(np.log(1.5)), 1000
BINS = ("mid", "mirror_pre", "mirror_head", "anti", "pre", "head")


def vectors(s, edges, rate, phi):
    """Population vectors Σ(n_i − λ_i·w)e^{iφ_i} of the activity above expectation in each window between edges."""
    counts = s.counts(np.asarray(edges, np.float64))
    return ((counts - rate[:, None] * np.diff(edges)) * np.exp(1j * phi)[:, None]).sum(0)


def session(row):
    """Per conflict event of one session: the 0.25 s vectors of its qualifying 1 s windows (as in C8-1), or None."""
    s = store.load(row)
    t, angle = c33.head_angle(s)
    f = tuning(*c32.windows(s, t, angle, zip(*s.intervals("states", "Awake"))))
    hd = (np.abs(f @ np.exp(1j * GRID)) / f.sum(1) >= c32.R_HD) & (f.max(1) >= c32.PEAK_HD)
    if hd.sum() < c32.MIN_CELLS:
        return None
    s = s.units(hd)
    phi = np.angle(f[hd] @ np.exp(1j * GRID))
    start, stop = s.intervals("states")
    label = s["states_label"]
    rate = {x: s.window_counts(start[label == x], stop[label == x]).sum(1) / (stop - start)[label == x].sum()
            for x in ("Awake", "Non-REM")}
    found = []
    for i in range(len(label) - 1):
        s0, e0, s1, e1 = start[i], stop[i], start[i + 1], stop[i + 1]
        if not (label[i] == "Awake" and label[i + 1] == "Non-REM" and e0 - s0 >= PRE and 0 <= s1 - e0 <= 1):
            continue
        n = len(np.arange(s1, min(e1, s1 + LAGS[-1]), WINDOW)) - 1
        if n < 1:
            continue
        pre = c32.direction(s, [e0 - PRE, e0], rate["Awake"], phi)[0]
        head = c33.at(t, angle, s1 + np.arange(n) * WINDOW + WINDOW / 2)
        use = np.isfinite(head) & (np.abs(np.angle(np.exp(1j * (head - pre)))) >= c8.SEPARATION)
        if use.any():
            z = vectors(s, s1 + SHORT * np.arange(PARTS * n + 1), rate["Non-REM"], phi).reshape(n, PARTS)
            found.append({"z": z[use], "pre": np.full(use.sum(), pre), "head": head[use]})
    return found


def windows(events):
    """0.25 s vectors, candidates and event ids of the conflict windows whose separation is at most 150°."""
    z, pre, head = (np.concatenate([e[k] for e in events]) for k in ("z", "pre", "head"))
    owner = np.concatenate([np.full(len(e["z"]), i) for i, e in enumerate(events)])
    keep = np.abs(np.angle(np.exp(1j * (head - pre)))) <= WIDEST
    return z[keep], pre[keep], head[keep], owner[keep]


def binned(z, pre, head):
    """Bin of each window's 1 s direction (index into BINS, −1 outside all), its coherence, and cos(Δ/2)."""
    mid = np.angle(np.exp(1j * pre) + np.exp(1j * head))
    centers = np.stack([mid, 2 * pre - mid, 2 * head - mid, mid + np.pi, pre, head], 1)
    near = np.abs(np.angle(np.exp(1j * (np.angle(z.sum(1))[:, None] - centers)))) <= HALF
    which = np.where(near.any(1), near.argmax(1), -1)
    return which, np.abs(z.sum(1)) / np.abs(z).sum(1), np.cos(np.abs(np.angle(np.exp(1j * (head - pre)))) / 2)


def excess(n, s):
    """Count and coherence ratio Q of the middle excess, from bin counts n and coherence sums s (last axis = BINS)."""
    m, p, h, a, cp, ch = np.moveaxis(n, -1, 0)
    sm, sp, sh, sa, scp, sch = np.moveaxis(s, -1, 0)
    count = m - p - h + a
    return count, ((sm - sp - sh + sa) / count) / ((scp + sch - 2 * sa) / (cp + ch - 2 * a))


def analyse(z, pre, head, owner, rng):
    which, coherence, half_cos = binned(z, pre, head)
    events = np.unique(owner, return_inverse=True)[1]
    one_hot = (which[:, None] == np.arange(len(BINS))).astype(float)
    n = np.zeros((events.max() + 1, len(BINS)))
    s = np.zeros_like(n)
    np.add.at(n, events, one_hot)
    np.add.at(s, events, one_hot * coherence[:, None])
    count, q = excess(n.sum(0), s.sum(0))
    draws = np.stack([np.bincount(rng.integers(0, len(n), len(n)), minlength=len(n)) for _ in range(BOOT)]).astype(float)
    boot_count, boot_q = excess(draws @ n, draws @ s)
    return {"windows": len(z), "events": len(n), "bins": dict(zip(BINS, n.sum(0).tolist())),
            "bin_coherence": dict(zip(BINS, (s.sum(0) / n.sum(0)).tolist())),
            "excess": float(count), "excess_fraction": float(count / len(z)), "excess_p1": float(np.percentile(boot_count, 1)),
            "excess_p99": float(np.percentile(boot_count, 99)),  # 보고만: C8-1 중간 성분이 ±15° 칸에 줄 기대 개수와 견줌
            "Q": float(q), "Q_p1": float(np.percentile(boot_q, 1)), "Q_p99": float(np.percentile(boot_q, 99)),
            "Q_selection": float(half_cos[which == 0].mean())}


def main():
    rows = harness.registered("dandi-000056")
    harness.verify(rows)
    events = [e for x in map(session, rows) if x for e in x]
    r = analyse(*windows(events), np.random.default_rng(0))
    q, sel = r["Q"], r["Q_selection"]
    result = harness.record(
        "c8_2_window_selection", "C8",
        "논렘에서 과거와 현재 후보가 90–150° 갈등할 때 1 s 창이 중간에 놓이는 초과분은 한 곳에 붙은 섞임이 아니라 창 안에서 "
        "두 후보에 번갈아 놓인 표현의 합이다",
        "Kim et al. 2017 Science 356:849 (doi:10.1126/science.aal4835): 90°·180° 떨어진 두 입력에 봉우리는 중간으로 흐르지 "
        "않고 한쪽으로 도약한다(Q = cos(Δ/2)). 실측: DANDI:000056",
        {"windows": harness.check(r["windows"], 1000), "events": harness.check(r["events"], 30),
         "instrument": harness.check(r["excess_p1"], low=0),
         "selection": harness.check(r["Q_p99"], high=(sel + 1) / 2),
         "accuracy": harness.check(abs(np.log(q / sel)), high=TOL)},
        rows, proof=harness.reverse("이진 게이트(한 번에 한 후보)", abs(np.log(q / sel)), abs(np.log(q)), TOL), **r)
    print(result["verdict"], r)


if __name__ == "__main__":
    main()
