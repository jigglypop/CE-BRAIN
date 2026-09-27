"""C4-4: 입력 없는 상태 변화의 비용은 이차형식(리만 계량)이다 (전제 C4).

명제: 방향 입력이 꺼진 렘 수면에서 머리방향 고리 위 상태 변화는 한 이동도의 확산이다. 곧 변화 비용이
ds² = g·dθ²인 리만 계량이고(Onsager–Machlup 작용이 변위의 이차형식), 봉우리 변위의 특성함수가
φ_k(τ) = exp(−k²·M·τ/2) (M: 제곱 변위 기울기, rad²/s)를 따른다. 계량은 g = 2T/M이다.
경쟁 식 (조화 비 r_k(τ) = F_k(τ)/F_1(τ) = c_k·exp(−f_k(τ)); 전역 이득 변동은 비에서 지워진다):
- 확산(리만): f_k = (k² − 1)·M·τ/2
- 쓸기(속도 입력, 탄도): f_k = (k² − 1)·s·τ²
- 도약(|k| 비례, 코시형): f_k = (k − 1)·v·τ
- 자유 지수: f_k = (k^α − 1)·M·τ/2 (α = 2가 확산)
F_k(τ)는 방향 세포 쌍의 교차 상관(독립 기대 대비 초과)을 선호 방향 차 ψ의 12칸으로 모아 ψ에 대해 푼 k번째 조화다
(Peyrache et al. 2015의 교차 상관 방법을 조화로 확장; 해독 잡음이 없다). k = 1, 2, 3, τ 칸 20–60–120–200–300–450–700 ms.
생물 기준값: Chaudhuri et al. 2019 (Nat Neurosci 22:1512, 000056과 같은 자료의 ADn): 렘에서 제곱 각변화가 시간에
선형(확산), 기울기 0.52·1.1·1.3 rad²/s (생쥐 셋). 논렘은 탄도형 쓸기(깸 속도의 8배), 깸은 머리 운동에 끌린 탄도형.
자료(원장): dandi-000056 (주), dandi-000939-extract (재현, 다른 연구실·영역). 방향 세포는 C3-2와 같다.
불확도: 세션 부트스트랩 1000번.
검정력(실자료 전 합성 검증): 60° 폭 조율에서 k = 3 조화는 k = 1의 약 4%라 자유 α와 도약식(|k| 비례)은 확산식과
구별되지 않았다(참 확산에서 α 2.98, 도약식 χ²/자유도 1.73). 확산 대 쓸기와 M은 되찾았다(M 1.04, 쓸기 χ² 4.6).
그래서 α와 도약식은 보고만 하고 판정에 쓰지 않는다.
판정(실행 전 고정):
- 000056: 세션 ≥ 5, 렘 합계 ≥ 3600 s
- 정확도: 000056 확산식 M이 문헌 범위를 1.5배 넓힌 0.35–1.95 rad²/s 안
- 재현(000939): 확산식 χ²/자유도 ≤ 2 < 쓸기식 χ²/자유도
- 역증명(000056): 확산식 χ²/자유도 ≤ 2 < 쓸기식 χ²/자유도
"""

import cefast
import numpy as np
from scipy.optimize import curve_fit

from research import c3_2_trace_replication as c32
from research import harness, store
from research.c3_3_restoring import head_angle
from research.c4_1_metric_hd import GRID, tuning

BIN, HALF, PSI, HARMONICS = 0.01, 70, 12, (1, 2, 3)
EDGES = np.array([0.02, 0.06, 0.12, 0.2, 0.3, 0.45, 0.7])
LITERATURE, WIDEN, CHI2 = (0.52, 1.3), 1.5, 2.0
MODELS = {
    "diffusion": lambda k, t, m: (k ** 2 - 1) * m * t / 2,
    "sweep": lambda k, t, s: (k ** 2 - 1) * s * t ** 2,
    "jump": lambda k, t, v: (k - 1) * v * t,
}


def hd_056(row):
    s = store.load(row)
    t, angle = head_angle(s)
    start, stop = s.intervals("states", "Awake")
    f = tuning(*c32.windows(s, t, angle, zip(start, stop)))
    hd = (np.abs(f @ np.exp(1j * GRID)) / f.sum(1) >= c32.R_HD) & (f.max(1) >= c32.PEAK_HD)
    if hd.sum() < c32.MIN_CELLS:
        return None
    return s.units(hd), np.angle(f[hd] @ np.exp(1j * GRID)), {
        "rem": s.intervals("states", "REM"), "nrem": s.intervals("states", "Non-REM"), "wake": (start, stop)}


def hd_939(row):
    s = store.load(row)
    s = s.units(s["unit_is_head_direction"] == 1)
    (a,), (b,) = s.intervals("epochs", "wake_square")
    t, angle = s.series("head")
    inside = (t >= a) & (t < b)
    f = tuning(*c32.windows(s, t[inside], angle[inside], [(a, b)]))
    if len(f) < c32.MIN_CELLS:
        return None
    return s, np.angle(f @ np.exp(1j * GRID)), {
        "rem": s.intervals("sleep_states", "rem"), "nrem": s.intervals("sleep_states", "nrem"),
        "wake": s.intervals("sleep_states", "wake")}


def pair_sums(s, phi, starts, stops, half=HALF):
    """Correlogram counts and independence expectations summed over pairs in each preferred-difference bin."""
    sub = s.within(starts, stops)
    g = cefast.ccg(sub.spikes, sub.ends, sub.spikes, sub.ends, BIN, half).astype(float)
    n = np.diff(np.r_[0, sub.ends]).astype(float)
    expected = np.outer(n, n) * BIN / (stops - starts).sum()
    psi = np.angle(np.exp(1j * (phi[None, :] - phi[:, None]))) % (2 * np.pi)
    b = (psi / (2 * np.pi) * PSI).astype(int) % PSI
    off = ~np.eye(len(phi), dtype=bool)
    counts = np.stack([g[(b == k) & off].sum(0) for k in range(PSI)])
    return counts, np.array([expected[(b == k) & off].sum() for k in range(PSI)]), float((stops - starts).sum())


def harmonics(counts, expected):
    """F_k(τ) for k in HARMONICS on the positive lags (complex; the imaginary part is a directed drift)."""
    r = counts / np.maximum(expected, 1e-12)[:, None] - 1
    centers = (np.arange(PSI) + 0.5) * 2 * np.pi / PSI
    f = np.stack([(r * np.exp(-1j * k * centers)[:, None]).mean(0) for k in HARMONICS])
    half = f.shape[1] // 2
    return (f[:, half:] + np.conj(f[:, half::-1])) / 2


def ratios(counts, expected, edges=EDGES):
    """r_k = F_k / F_1 (real parts) averaged in the τ bins, for k = 2, 3."""
    f = harmonics(counts, expected).real
    lag = np.arange(f.shape[1]) * BIN
    b = np.digitize(lag, edges) - 1
    use = (b >= 0) & (b < len(edges) - 1)
    mean = np.stack([np.bincount(b[use], row[use], len(edges) - 1) for row in f]) / np.bincount(b[use])
    return mean[1:] / mean[0], np.bincount(b[use], lag[use], len(edges) - 1) / np.bincount(b[use])


def fit(name, lag, r, se):
    """Joint least-squares fit of r_k = c_k·exp(−f_k) for k = 2, 3; χ² per degree of freedom."""
    k = np.repeat([2, 3], len(lag))
    t = np.tile(lag, 2)
    if name == "alpha":
        model = lambda x, c2, c3, m, a: np.where(k == 2, c2, c3) * np.exp(-(k ** a - 1) * m * t / 2)
        p0, bounds = (0.5, 0.2, 1.0, 2.0), ([0, 0, 0, 0.2], [5, 5, 50, 4])
    else:
        rate = MODELS[name]
        model = lambda x, c2, c3, q: np.where(k == 2, c2, c3) * np.exp(-rate(k, t, q))
        p0, bounds = (0.5, 0.2, 1.0), ([0, 0, 0], [5, 5, 500])
    params = curve_fit(model, t, r.ravel(), p0=p0, sigma=se.ravel(), bounds=bounds, absolute_sigma=True)[0]
    chi2 = float(np.sum(((r.ravel() - model(t, *params)) / se.ravel()) ** 2))
    return {"params": [float(p) for p in params], "chi2_dof": chi2 / (r.size - len(p0))}


def analyse(sessions, state, rng, boot=1000, edges=EDGES):
    counts = np.stack([x[state][0] for x in sessions])
    expected = np.stack([x[state][1] for x in sessions])
    r, lag = ratios(counts.sum(0), expected.sum(0), edges)
    draws = [rng.integers(0, len(sessions), len(sessions)) for _ in range(boot)]
    se = np.stack([ratios(counts[d].sum(0), expected[d].sum(0), edges)[0] for d in draws]).std(0)
    fits = {name: fit(name, lag, r, se) for name in (*MODELS, "alpha")}
    f = harmonics(counts.sum(0), expected.sum(0))
    return {"seconds": float(sum(x[state][2] for x in sessions)), "lag": lag.tolist(), "ratio": r.tolist(),
            "se": se.tolist(), "fits": fits,
            "directed_first_harmonic": float(np.abs(f[0, 2:30].imag).mean() / np.abs(f[0, 2:30].real).mean())}


def collect(prepared):
    return [{state: pair_sums(s, phi, *spans[state]) for state in ("rem", "nrem", "wake")}
            for s, phi, spans in prepared if len(spans["rem"][0])]


def main():
    rows56 = harness.registered("dandi-000056")
    rows39 = [r for r in harness.registered("dandi-000939-extract") if r["asset"].endswith(".npz")]
    harness.verify(rows56 + rows39)
    s56 = collect(x for x in map(hd_056, rows56) if x)
    s39 = collect(x for x in map(hd_939, rows39) if x)
    out = {}
    for name, sessions in (("dandi_000056", s56), ("dandi_000939", s39)):
        out[name] = {"sessions": len(sessions),
                     **{state: analyse(sessions, state, np.random.default_rng(0)) for state in ("rem", "nrem", "wake")}}
    rem56, rem39 = out["dandi_000056"]["rem"], out["dandi_000939"]["rem"]
    m = rem56["fits"]["diffusion"]["params"][2]
    result = harness.record(
        "c4_4_ring_diffusion", "C4",
        "방향 입력이 꺼진 렘에서 머리방향 고리 위 상태 변화는 한 이동도의 확산이다: 변화 비용이 이차형식(리만 계량)이고 "
        "봉우리 변위의 특성함수가 exp(−k²Mτ/2)를 따르며 M이 문헌 값과 맞는다",
        "Chaudhuri et al. 2019 Nat Neurosci 22:1512 (doi:10.1038/s41593-019-0460-x): 렘 확산, 제곱 각변화 기울기 "
        "0.52·1.1·1.3 rad²/s. 실측: DANDI:000056 (주), DANDI:000939 (재현)",
        {"sessions": harness.check(out["dandi_000056"]["sessions"], 5),
         "rem_seconds": harness.check(rem56["seconds"], 3600),
         "accuracy": harness.check(m, LITERATURE[0] / WIDEN, LITERATURE[1] * WIDEN),
         "replication_000939": harness.check(min(rem39["fits"]["sweep"]["chi2_dof"] - CHI2,
                                                 CHI2 - rem39["fits"]["diffusion"]["chi2_dof"]), low=0)},
        rows56 + rows39,
        proof=harness.reverse("이차 비용(리만 계량)의 확산", rem56["fits"]["diffusion"]["chi2_dof"],
                              rem56["fits"]["sweep"]["chi2_dof"], CHI2),
        **out)
    print(result["verdict"], "| M(000056 렘) = %.2f rad²/s" % m)
    for name, o in out.items():
        for state in ("rem", "nrem", "wake"):
            a = o[state]
            print(name, state, "%.0f s" % a["seconds"], {k: (np.round(v["params"], 3).tolist(), round(v["chi2_dof"], 2))
                                                        for k, v in a["fits"].items()},
                  "| 방향성 %.3f" % a["directed_first_harmonic"])


if __name__ == "__main__":
    main()
