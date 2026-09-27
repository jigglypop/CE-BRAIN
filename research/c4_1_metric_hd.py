"""C4-1: 머리방향 세포의 국소 판별 정밀도를 정하는 계량 (전제 C4).

명제: 방향 θ의 국소 판별 정밀도(시험 창의 해독 오차 분산)는 상태 θ에 따라 달라지고, 상태 의존 리만 계량
g(θ)의 역수로 맞춰진다. 평평한 계량(g = 상수)으로는 맞춰지지 않는다.
후보 계량 (학습 절반의 조율곡선 f_i, 창 길이 T):
- A 포아송 Fisher–Rao: g_A(θ) = T·Σ f_i′²/f_i
- C 등분산: g_C(θ) ∝ Σ f_i′²
- B 평평: g_B = 상수 (역증명에서 전제 항을 뺀 식)
기준 식은 A, C 중 주 검사 오차가 작은 것이다.
자료(원장): dandi-000939-extract의 생쥐 후구상 머리방향 세포(저자 분류). 주 검사 wake_square, 재현 wake_triangle.
방법: T = 0.1 s, 30 s 블록을 번갈아 학습/시험. 조율곡선은 6° 칸, 원형 가우스 σ 12°, 바닥 0.05 Hz.
시험 절반은 포아송 최대우도로 해독(1° 격자). 참 방향 30° 칸 12개마다 측정 분산 (1.4826·MAD)²을 재고
시험 창 50개 미만 칸은 뺀다. 후보마다 세션별 척도 하나를 log 평균으로 맞춘 뒤 log 잔차의 RMS를 잰다.
판정(실행 전 고정):
- 세션 ≥ 5 (머리방향 세포 ≥ 10, 추적 ≥ 10분)
- 정확도: 기준 식 RMS 중앙값 ≤ 0.35 (wake_square)
- 역증명: 기준 식 ≤ 0.35 < 평평 B (wake_square)
- 재현: wake_triangle에서 기준 식 ≤ 0.35, 평평 B ≥ 0.35
"""

import numpy as np

from research import harness

T, BLOCK, MAP_BINS, SIGMA, FLOOR = 0.1, 30.0, 60, 12.0, 0.05
GRID = np.radians(np.arange(360))
BINS, MIN_WINDOWS, TOL = 12, 50, 0.35


def load(row, epoch):
    """HD-cell spike trains and tracked head direction inside one epoch, or None if absent."""
    with np.load(harness.path(row)) as z:
        spans = [(a, b) for t, a, b in zip(z["ep_tag"], z["ep_start"], z["ep_stop"]) if t == epoch]
        if not spans:
            return None
        ((start, stop),) = spans
        times, ends = z["spike_times"], z["spike_times_index"].astype(np.int64)
        cells = [times[b:e] for b, e, hd in zip(np.r_[0, ends[:-1]], ends, z["is_head_direction"]) if hd]
        t, angle = z["hd_t"], z["hd"]
        inside = (t >= start) & (t < stop)
        return cells, t[inside], angle[inside]


def windows(cells, t, angle):
    """Spike counts, circular-mean direction and start time per T window with ≥ 80% tracking."""
    edges = np.arange(t[0], t[-1], T)
    k = np.clip(((t - t[0]) // T).astype(int), 0, len(edges) - 2)
    ok = np.isfinite(angle)
    samples = np.bincount(k[ok], minlength=len(edges) - 1)
    z = (np.bincount(k[ok], np.cos(angle[ok]), len(edges) - 1)
         + 1j * np.bincount(k[ok], np.sin(angle[ok]), len(edges) - 1))
    counts = np.stack([np.histogram(c, edges)[0] for c in cells], 1)
    valid = samples >= 0.8 * T / np.median(np.diff(t))
    return counts[valid], np.angle(z[valid]) % (2 * np.pi), edges[:-1][valid] - t[0]


def tuning(counts, angle):
    """Rate maps (cells × 360 on the 1° grid): 6° bins, circular Gaussian smoothing, floor."""
    b = (angle / (2 * np.pi) * MAP_BINS).astype(int) % MAP_BINS
    occupancy = np.bincount(b, minlength=MAP_BINS) * T
    rate = np.stack([np.bincount(b, c, MAP_BINS) for c in counts.T]) / np.maximum(occupancy, 1e-9)
    lag = np.minimum(np.arange(MAP_BINS), MAP_BINS - np.arange(MAP_BINS)) * 360 / MAP_BINS
    kernel = np.exp(-0.5 * (lag / SIGMA) ** 2)
    rate = np.real(np.fft.ifft(np.fft.fft(rate, axis=1) * np.fft.fft(kernel / kernel.sum()), axis=1))
    centers = (np.arange(MAP_BINS) + 0.5) * 2 * np.pi / MAP_BINS
    return np.stack([np.interp(GRID, centers, np.maximum(r, FLOOR), period=2 * np.pi) for r in rate])


def metrics(f):
    """Candidate metrics on the 1° grid: A = T·Σ f′²/f and the shape Σ f′² of C."""
    slope = (np.roll(f, -1, 1) - np.roll(f, 1, 1)) / (2 * np.radians(1))
    return {"A": T * (slope ** 2 / f).sum(0), "C": (slope ** 2).sum(0)}


def decode(counts, f):
    """Poisson maximum-likelihood direction on the 1° grid."""
    return GRID[(counts @ np.log(T * f) - T * f.sum(0)).argmax(1)]


def evaluate(counts, angle, when):
    """Log-RMS misfit of each candidate to the measured error variance across direction bins."""
    train = (when // BLOCK) % 2 == 0
    f = tuning(counts[train], angle[train])
    g = metrics(f)
    truth = angle[~train]
    error = np.angle(np.exp(1j * (decode(counts[~train], f) - truth)))
    grid = np.round(np.degrees(truth)).astype(int) % 360
    part = (truth / (2 * np.pi) * BINS).astype(int) % BINS
    observed, predicted = [], {"A": [], "C": []}
    for k in range(BINS):
        e = error[part == k]
        if len(e) < MIN_WINDOWS:
            continue
        observed.append((1.4826 * np.median(np.abs(e - np.median(e)))) ** 2)
        for name in predicted:
            predicted[name].append(np.mean(1 / g[name][grid[part == k]]))
    observed = np.log(observed)
    residual = {name: observed - np.log(v) for name, v in predicted.items()}
    rms = {name: float(r.std()) for name, r in residual.items()}
    rms["B"] = float(observed.std())
    return {"rms": rms, "scale_A": float(np.exp(residual["A"].mean())), "bins": len(observed),
            "test_windows": int((~train).sum())}


def run(epoch, rows):
    sessions = []
    for row in rows:
        loaded = load(row, epoch)
        if loaded is None:
            continue
        cells, t, angle = loaded
        if len(cells) < 10 or np.isfinite(angle).sum() * np.median(np.diff(t)) < 600:
            continue
        sessions.append({"session": row["asset"].split("_behavior")[0], "cells": len(cells),
                         **evaluate(*windows(cells, t, angle))})
    return sessions


def median(sessions):
    return {k: float(np.median([s["rms"][k] for s in sessions])) for k in "ABC"}


def main():
    rows = [r for r in harness.registered("dandi-000939-extract") if r["asset"].endswith(".npz")]
    harness.verify(rows)
    square, triangle = run("wake_square", rows), run("wake_triangle", rows)
    sq, tri = median(square), median(triangle)
    best = min("AC", key=sq.get)
    result = harness.record(
        "c4_1_metric_hd", "C4",
        "머리방향 세포의 국소 판별 정밀도는 상태 의존 리만 계량 g(θ)의 역수로 맞춰지고, 평평한 계량으로는 맞춰지지 않는다",
        "실측: DANDI:000939 생쥐 후구상 머리방향 세포 (주 검사 wake_square, 재현 wake_triangle)",
        {"sessions": harness.check(len(square), 5),
         "accuracy": harness.check(sq[best], high=TOL),
         "replication_accuracy": harness.check(tri[best], high=TOL),
         "replication_flat_fails": harness.check(tri["B"], low=TOL)},
        rows,
        proof=harness.reverse("상태 의존 계량 g(θ)", sq[best], sq["B"], TOL),
        standard={"A": "포아송 Fisher–Rao g = T·Σf′²/f", "C": "등분산 g ∝ Σf′²"}[best],
        median_rms_square=sq, median_rms_triangle=tri,
        median_scale_A=float(np.median([s["scale_A"] for s in square])),
        square=square, triangle=triangle)
    print(result["verdict"], "| 기준 식:", result["measured"]["standard"])
    print("RMS 중앙값 square:", sq, "| triangle:", tri, "| A 절대 척도:", result["measured"]["median_scale_A"])


if __name__ == "__main__":
    main()
