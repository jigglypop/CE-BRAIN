"""C7-1: 해마는 위치를 주소로 두고 수면에서 가까운 주소를 함께 불러낸다 (전제 C7).

명제: 새 트랙에서 CA1 흥분성 세포는 트랙 위 한 곳(장소장 중심, 주소)에 발화한다. 경험 뒤 논렘의 동기 방전에서 쌍의
함께 켜짐은 경험 전보다 늘고, 그 증가는 두 세포의 주소가 가까울수록 크다(주소로 검색). 이 증가는 느리게 발화하는 세포가
빠르게 발화하는 세포보다 크다.
식: 쌍의 함께 켜짐 = 동기 사건 참여(0/1)의 사건 간 상관(φ). ΔCo = φ_POST − φ_PRE. 주소 거리 d = |중심_i − 중심_j|
(트랙 길이 비). 주소 효과 = ρ_s(ΔCo, d) (스피어만, 음수면 가까울수록 증가). 역증명은 경험 전 사건의 ρ_s(φ_PRE, d)로,
경험(주소를 만든 이력) 없이 같은 거리 의존이 있으면 주소 검색이라 할 수 없다.
생물 기준값: Grosmark & Buzsáki 2016 (Science 351:1440): 느리게 발화하는 세포가 탐색 중 장소 특이성을 얻고 경험 뒤 수면에서
리플 연관과 동시 발화가 늘어나며, 빠르게 발화하는 세포는 경험 전후로 덜 바뀐다.
자료(원장): dandi-000044 (쥐 4마리 8세션, 수면 전 → 새 선형 트랙 → 수면 후, 양쪽 CA1).
방법: 위치 시각은 NWB rate 속성을 표본 간격으로 읽어 다시 세운다(표본 수 × 0.0256 s = 트랙 에포크, 8세션 모두).
선형 위치를 에포크 안 1–99 백분위로 [0, 1]에 맞춘다. 주행(속도 > 0.05 트랙/s, 0.25 s 평활) 중 50칸 발화 지도(σ 1칸)의
최대 칸이 중심이고, 최고 발화 ≥ 1 Hz인 세포만 쓴다. 동기 사건: PRE(수면 전 논렘 마지막 60분)·POST(수면 후 논렘 처음 60분)의
20 ms 칸 흥분성 집단 발화 수가 그 구간 평균 + 3 SD를 넘는 연속 칸(≥ 40 ms). 느린·빠른 세포는 세션 전체 평균 발화의 세션 중앙값으로
나누고, 가까운 쌍은 d < 0.2. 세션마다 값을 구해 세션 평균, 불확도는 세션 부트스트랩 1000번.
판정(실행 전 고정):
- 세션 ≥ 5 (각 세션 장소 세포 쌍 ≥ 50)
- 주소 검색: 세션 평균 ρ_s(ΔCo, d)의 부트스트랩 99% 백분위 < 0
- 느린 세포: 가까운 쌍의 ΔCo (느린·느린 − 빠른·빠른) 세션 평균의 부트스트랩 1% 백분위 > 0
- 역증명: 세션 평균 ρ_s(φ_POST, d) ≤ −0.05 < 세션 평균 ρ_s(φ_PRE, d)
"""

import numpy as np
from scipy.ndimage import gaussian_filter1d
from scipy.stats import spearmanr

from research import c6_1_reactivation as c6
from research import harness, store

SPATIAL_BINS, RUN_SPEED, PEAK, CLOSE = 50, 0.05, 1.0, 0.2
SYNC_BIN, SYNC_Z, SYNC_MIN, MIN_PAIRS, BOOT, TOL = 0.02, 3.0, 2, 50, 1000, -0.05


def place_centers(s):
    """Place-field centre (track fraction) and peak rate of every unit from running periods on the track."""
    (a,), (b,) = s.intervals("epochs", "MazeEpoch")
    t, x = s.series("position")
    x = x[:, 0]
    if np.median(np.diff(t)) > 1:  # 000044의 NWB rate 속성에는 표본 간격(0.0256 s)이 들어 있다: 표본 수 × 간격 = 트랙 에포크
        t = t[0] + np.arange(len(t)) / np.median(np.diff(t))
    keep = (t >= a) & (t < b) & np.isfinite(x)
    t, x = t[keep], x[keep]
    lo, hi = np.percentile(x, [1, 99])
    x = np.clip((x - lo) / (hi - lo), 0, 1 - 1e-9)
    dt = np.median(np.diff(t))
    speed = np.abs(gaussian_filter1d(np.gradient(x, t), 0.25 / dt))
    run = speed > RUN_SPEED
    k = (x * SPATIAL_BINS).astype(int)
    occupancy = np.bincount(k[run], minlength=SPATIAL_BINS) * dt
    counts = s.window_counts(t[run] - dt / 2, t[run] + dt / 2)  # 표본마다 제 창: 결측 구간의 스파이크는 넣지 않는다
    rate = np.stack([np.bincount(k[run], c, SPATIAL_BINS) for c in counts]) / np.maximum(occupancy, 1e-9)
    rate = gaussian_filter1d(rate, 1, axis=1, mode="nearest")
    return (rate.argmax(1) + 0.5) / SPATIAL_BINS, rate.max(1)


def participation(s, epoch, first):
    """Units × synchronous events (1 if the unit fired) in the chosen hour of NREM."""
    starts, _ = c6.sleep_bins(s, epoch, first)
    fine = (starts[:, None] + np.arange(round(c6.BIN / SYNC_BIN)) * SYNC_BIN).ravel()
    counts = s.window_counts(fine, fine + SYNC_BIN)
    total = counts.sum(0)
    high = total > total.mean() + SYNC_Z * total.std()
    joined = high & np.r_[False, high[:-1]] & np.r_[False, np.isclose(np.diff(fine), SYNC_BIN)]
    label = np.cumsum(high & ~joined)  # 새 사건이 시작하는 칸에서 번호가 오른다
    idx = np.flatnonzero(high)
    events = [e for e in np.split(idx, np.flatnonzero(np.diff(label[idx])) + 1) if len(e) >= SYNC_MIN]
    return np.stack([(counts[:, e].sum(1) > 0) for e in events], 1).astype(float)


def pair_values(matrix, use):
    phi = np.corrcoef(matrix[use])
    return np.nan_to_num(phi)


def session(row):
    s = store.load(row)
    s = s.units(s["unit_cell_type"] == "excitatory")
    center, peak = place_centers(s)
    rate = np.diff(np.r_[0, s.ends]) / (s.spikes.max() - s.spikes.min())
    pre, post = participation(s, "PREEpoch", False), participation(s, "POSTEpoch", True)
    use = (peak >= PEAK) & (pre.sum(1) > 0) & (post.sum(1) > 0)
    pairs = np.triu(np.ones((use.sum(), use.sum()), bool), 1)
    d = np.abs(center[use][:, None] - center[use][None, :])[pairs]
    phi_pre, phi_post = pair_values(pre, use)[pairs], pair_values(post, use)[pairs]
    delta = phi_post - phi_pre
    slow = rate[use] < np.median(rate)
    close = d < CLOSE
    ss, ff = (slow[:, None] & slow[None, :])[pairs], (~slow[:, None] & ~slow[None, :])[pairs]
    return {"asset": row["asset"], "cells": int(use.sum()), "pairs": int(pairs.sum()),
            "events": [int(pre.shape[1]), int(post.shape[1])],
            "rho_delta": float(spearmanr(delta, d)[0]), "rho_pre": float(spearmanr(phi_pre, d)[0]),
            "rho_post": float(spearmanr(phi_post, d)[0]),
            "slow_minus_fast_close": float(delta[close & ss].mean() - delta[close & ff].mean())}


def main():
    rows = harness.registered("dandi-000044")
    harness.verify(rows)
    sessions = [session(r) for r in rows]
    used = [x for x in sessions if x["pairs"] >= MIN_PAIRS and np.isfinite(x["slow_minus_fast_close"])]
    values = {k: np.array([x[k] for x in used]) for k in ("rho_delta", "rho_pre", "rho_post", "slow_minus_fast_close")}
    draws = np.random.default_rng(0).integers(0, len(used), (BOOT, len(used)))
    boot = {k: v[draws].mean(1) for k, v in values.items()}
    mean = {k: float(v.mean()) for k, v in values.items()}
    result = harness.record(
        "c7_1_address", "C7",
        "CA1 세포는 트랙 위 한 곳을 주소로 갖고, 경험 뒤 논렘 동기 방전에서 쌍의 함께 켜짐은 주소가 가까울수록 더 늘며, "
        "그 증가는 느리게 발화하는 세포가 빠르게 발화하는 세포보다 크다",
        "Grosmark & Buzsáki 2016 Science 351:1440: 느린 세포가 장소 특이성을 얻고 경험 뒤 수면에서 동시 발화가 늘며, 빠른 "
        "세포는 덜 바뀐다. 실측: DANDI:000044",
        {"sessions": harness.check(len(used), 5),
         "address_retrieval": harness.check(float(np.percentile(boot["rho_delta"], 99)), high=0),
         "slow_cells": harness.check(float(np.percentile(boot["slow_minus_fast_close"], 1)), low=0)},
        rows, proof=harness.reverse("경험이 만든 주소", mean["rho_post"], mean["rho_pre"], TOL),
        sessions=sessions, mean=mean)
    print(result["verdict"], {k: round(v, 3) for k, v in mean.items()})
    for x in sessions:
        print("  ", x["asset"][:40], x["cells"], "세포", x["pairs"], "쌍", "사건", x["events"],
              {k: round(v, 3) for k, v in x.items() if k.startswith(("rho", "slow"))})


if __name__ == "__main__":
    main()
