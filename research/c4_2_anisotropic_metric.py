"""C4-2: 변화 비용의 비등방 계량 — 가장 싼 변화 방향이 기억 다양체를 따라 도는가 (전제 C4).

C4-1(실패)의 결과를 본 뒤 세운 가설이고 같은 자료를 쓴다. 그 점을 판정에 적는다.
명제: 머리방향 상태 θ에서 푸아송 정규화 잔차 e = (n − Tf)/√(Tf)의 공분산은 Σ(θ) = a·I + σ²·τ(θ)τ(θ)ᵀ다
(τ = T f′/√(T f), 다양체 접선). 곧 변화 비용 계량 G(θ) = Σ(θ)⁻¹에서 가장 싼 방향은 그 상태의 접선이고 상태를
따라 돈다. 같은 (a, σ²)가 C4-1의 해독 정밀도 v(θ) = a/g(θ) + σ² (g = ‖τ‖²)를 척도 재적합 없이 맞춘다.
대안: 이득 흔들림 Σ = a·I + γ²·m mᵀ (m = √(Tf)), 고정 축 Σ = a·I + ε·u uᵀ (u = 상태와 무관한 잔차 주축).
자료(원장): dandi-000939-extract. 주 검사 wake_square, 재현 wake_triangle. 창·분할·조율곡선·해독은 C4-1과 같다.
측정: 30° 칸 b의 시험 창 잔차를 12개 칸 중심의 접선 방향 τ̂_k로 투영한 분산 V[b,k]. 모형마다 (a, 한 매개변수)를
상대 가중 최소제곱(음수 없음)으로 맞추고 log 잔차 RMS를 잰다.
판정(실행 전 고정):
- 세션 ≥ 5
- 잡음 구조: 흔들림 모형 RMS 중앙값 ≤ 0.35이고 이득·고정 축 모형보다 작다
- 역증명: 흔들림 ≤ 0.35 < 고정 축 (상태를 따라 도는 축을 빼면 맞추지 못함)
- 교차 예측: 잡음 구조에서 맞춘 (a, σ²)로 칸별 해독 분산을 예측한 log RMS 중앙값 ≤ 0.35
- 재현(wake_triangle): 잡음 구조 RMS ≤ 0.35, 교차 예측 ≤ 0.35
"""

import numpy as np
from scipy.optimize import nnls

from research import harness
from research.c4_1_metric_hd import BINS, BLOCK, MIN_WINDOWS, T, TOL, decode, load, tuning, windows


def geometry(f):
    """Pearson-space tangent τ = T f′/√(T f) and rate direction m = √(T f) on the 1° grid."""
    slope = (np.roll(f, -1, 1) - np.roll(f, 1, 1)) / (2 * np.radians(1))
    return T * slope / np.sqrt(T * f), np.sqrt(T * f)


def fit(v, shape):
    """v ≈ a + p·shape with relative weights and a, p ≥ 0; returns a, p and the log RMS."""
    (a, p), _ = nnls(np.stack([np.ones_like(shape), shape], 1) / v[:, None], np.ones_like(v))
    return float(a), float(p), float(np.sqrt(np.mean(np.log(v / (a + p * shape)) ** 2)))


def evaluate(counts, angle, when):
    """Noise-structure misfit of the jitter, gain and fixed-axis models and the decoding cross-prediction."""
    train = (when // BLOCK) % 2 == 0
    f = tuning(counts[train], angle[train])
    tau, m = geometry(f)
    n, truth = counts[~train], angle[~train]
    grid = np.round(np.degrees(truth)).astype(int) % 360
    mu = T * f[:, grid].T
    residual = (n - mu) / np.sqrt(mu)
    part = (truth / (2 * np.pi) * BINS).astype(int) % BINS
    centers = np.round((np.arange(BINS) + 0.5) * 360 / BINS).astype(int) % 360
    probes = tau[:, centers].T
    probes /= np.linalg.norm(probes, axis=1, keepdims=True)
    used = [b for b in range(BINS) if (part == b).sum() >= MIN_WINDOWS]
    variance = np.array([((residual[part == b] @ probes.T) ** 2).mean(0) for b in used])
    axis = np.linalg.eigh(np.cov(residual.T))[1][:, -1]
    shapes = {
        "jitter": np.array([((probes @ tau[:, grid[part == b]]) ** 2).mean(1) for b in used]),
        "gain": np.array([((probes @ m[:, grid[part == b]]) ** 2).mean(1) for b in used]),
        "fixed": np.tile((probes @ axis) ** 2, (len(used), 1)),
    }
    fits = {name: fit(variance.ravel(), s.ravel()) for name, s in shapes.items()}
    a, sigma2, _ = fits["jitter"]
    g = (tau ** 2).sum(0)
    error = np.angle(np.exp(1j * (decode(n, f) - truth)))
    observed = np.array([(1.4826 * np.median(np.abs(e - np.median(e)))) ** 2
                         for e in (error[part == b] for b in used)])
    predicted = np.array([np.mean(a / g[grid[part == b]] + sigma2) for b in used])
    return {"rms": {name: fit_[2] for name, fit_ in fits.items()}, "a": a,
            "sigma_deg": float(np.degrees(np.sqrt(sigma2))), "gamma2": fits["gain"][1],
            "cross": float(np.sqrt(np.mean(np.log(observed / predicted) ** 2))), "bins": len(used)}


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


def median(sessions, key):
    return float(np.median([key(s) for s in sessions]))


def main():
    rows = [r for r in harness.registered("dandi-000939-extract") if r["asset"].endswith(".npz")]
    harness.verify(rows)
    square, triangle = run("wake_square", rows), run("wake_triangle", rows)
    rms = {k: median(square, lambda s, k=k: s["rms"][k]) for k in ("jitter", "gain", "fixed")}
    tri = {k: median(triangle, lambda s, k=k: s["rms"][k]) for k in ("jitter", "gain", "fixed")}
    cross, tri_cross = median(square, lambda s: s["cross"]), median(triangle, lambda s: s["cross"])
    result = harness.record(
        "c4_2_anisotropic_metric", "C4",
        "머리방향 상태의 활동 변동 공분산은 Σ(θ) = aI + σ²ττᵀ로, 가장 싼 변화 방향이 다양체 접선이며 상태를 따라 돌고, "
        "같은 (a, σ²)가 해독 정밀도를 척도 재적합 없이 맞춘다",
        "실측: DANDI:000939 생쥐 후구상 머리방향 세포 (주 검사 wake_square, 재현 wake_triangle). "
        "C4-1 결과를 본 뒤 세운 가설이며 같은 자료를 썼다",
        {"sessions": harness.check(len(square), 5),
         "structure": harness.check(rms["jitter"], high=TOL),
         "beats_gain": harness.check(rms["gain"] - rms["jitter"], low=0),
         "cross_prediction": harness.check(cross, high=TOL),
         "replication_structure": harness.check(tri["jitter"], high=TOL),
         "replication_cross": harness.check(tri_cross, high=TOL)},
        rows,
        proof=harness.reverse("상태를 따라 도는 흔들림 축 ττᵀ", rms["jitter"], rms["fixed"], TOL),
        median_rms_square=rms, median_rms_triangle=tri, median_cross_square=cross,
        median_cross_triangle=tri_cross,
        median_sigma_deg=median(square, lambda s: s["sigma_deg"]), median_a=median(square, lambda s: s["a"]),
        square=square, triangle=triangle)
    print(result["verdict"], "| 잡음 구조 RMS square:", rms, "| triangle:", tri)
    print("교차 예측 RMS square/triangle:", cross, tri_cross, "| σ 중앙값(°):", result["measured"]["median_sigma_deg"],
          "| a 중앙값:", result["measured"]["median_a"])


if __name__ == "__main__":
    main()
