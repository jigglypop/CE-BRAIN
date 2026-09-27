"""C4-3: 싼 변화 방향이 여럿인 계량 — 끌개의 부드러운 변형(위치·진폭·폭) (전제 C4).

C4-1·C4-2(실패)를 본 뒤 세운 가설이다. 모형은 wake_square로만 맞추고, 판정은 같은 세포의 wake_triangle에서
매개변수를 다시 맞추지 않고 한다. triangle의 요약값은 C4-1·C4-2에서 본 적이 있다는 점을 판정에 적는다.
명제: 푸아송 정규화 잔차 e = (n − Tf)/√(Tf)의 공분산은 Σ(θ) = a·I + Σ_j s_j²·d_j(θ)d_j(θ)ᵀ다. d_j는 봉우리의
부드러운 변형 방향이다: 위치 τ = Tf′/√(Tf), 진폭 m = √(Tf), 폭 w = −T·(θ − φ_i)·f′/√(Tf) (φ_i = 선호 방향).
변화 비용 계량 G(θ) = Σ(θ)⁻¹의 싼 방향들은 상태를 따라 돌고, (a, s_j²)는 환경이 바뀌어도 유지된다.
대안(역증명의 전제 항을 뺀 식): 상태와 무관한 고정 축 셋 Σ = a·I + Σ_j ε_j·u_j u_jᵀ (u_j = square 잔차 주축 3개).
측정: 30° 칸 b의 시험 창 잔차를 각 칸 중심의 세 변형 방향(36개)으로 투영한 분산 V[b,p]. 창·분할·조율곡선·해독은
C4-1과 같다. 해독 교차 예측: v = mean[(a + Σ_j s_j²(τ̂·d_j)²)/‖τ‖²].
판정(실행 전 고정, square로 맞춘 값을 triangle에 그대로 옮김):
- 두 환경이 모두 있는 세션 ≥ 5
- 잡음 구조: triangle log RMS 중앙값 ≤ 0.35
- 교차 예측: triangle 해독 분산 log RMS 중앙값 ≤ 0.35
- 역증명: 부드러운 변형 ≤ 0.35 < 고정 축 (triangle)
"""

import numpy as np
from scipy.optimize import nnls

from research import harness
from research.c4_1_metric_hd import BINS, BLOCK, GRID, MIN_WINDOWS, T, TOL, decode, load, tuning, windows

MODES = ("position", "amplitude", "width")
CENTERS = np.round((np.arange(BINS) + 0.5) * 360 / BINS).astype(int) % 360


def modes(f):
    """Soft deformations of the bump in Pearson space on the 1° grid (cells × 360)."""
    slope = (np.roll(f, -1, 1) - np.roll(f, 1, 1)) / (2 * np.radians(1))
    root = np.sqrt(T * f)
    offset = np.angle(np.exp(1j * (GRID[None, :] - GRID[f.argmax(1)][:, None])))
    return {"position": T * slope / root, "amplitude": root, "width": -T * offset * slope / root}


def session(counts, angle, when):
    """Test-half residuals, probes and model shapes of one epoch."""
    train = (when // BLOCK) % 2 == 0
    f = tuning(counts[train], angle[train])
    d = modes(f)
    n, truth = counts[~train], angle[~train]
    grid = np.round(np.degrees(truth)).astype(int) % 360
    mu = T * f[:, grid].T
    residual = (n - mu) / np.sqrt(mu)
    part = (truth / (2 * np.pi) * BINS).astype(int) % BINS
    probes = np.concatenate([d[k][:, CENTERS].T for k in MODES])
    probes /= np.linalg.norm(probes, axis=1, keepdims=True)
    used = [b for b in range(BINS) if (part == b).sum() >= MIN_WINDOWS]
    return {"f": f, "d": d, "n": n, "truth": truth, "grid": grid, "residual": residual, "part": part,
            "probes": probes, "used": used,
            "variance": np.array([((residual[part == b] @ probes.T) ** 2).mean(0) for b in used])}


def soft_shapes(s):
    return [np.array([((s["probes"] @ s["d"][k][:, s["grid"][s["part"] == b]]) ** 2).mean(1)
                      for b in s["used"]]) for k in MODES]


def fixed_shapes(s, axes):
    return [np.tile((s["probes"] @ u) ** 2, (len(s["used"]), 1)) for u in axes.T]


def fit(v, shapes):
    """v ≈ a + Σ c_j·shape_j with relative weights and non-negative coefficients."""
    design = np.stack([np.ones(v.size)] + [x.ravel() for x in shapes], 1) / v.ravel()[:, None]
    return nnls(design, np.ones(v.size))[0]


def misfit(v, shapes, c):
    predicted = c[0] + sum(cj * x for cj, x in zip(c[1:], shapes))
    return float(np.sqrt(np.mean(np.log(v / predicted) ** 2)))


def decoding(s, c):
    """Log misfit of measured decoding variance per bin against the soft-mode prediction (no refit)."""
    tau = s["d"]["position"]
    g = (tau ** 2).sum(0)
    error = np.angle(np.exp(1j * (decode(s["n"], s["f"]) - s["truth"])))
    observed, predicted = [], []
    for b in s["used"]:
        at = s["grid"][s["part"] == b]
        e = error[s["part"] == b]
        observed.append((1.4826 * np.median(np.abs(e - np.median(e)))) ** 2)
        unit = tau[:, at] / np.sqrt(g[at])
        spread = sum(cj * ((unit * s["d"][k][:, at]).sum(0)) ** 2 for cj, k in zip(c[1:], MODES))
        predicted.append(np.mean((c[0] + spread) / g[at]))
    return float(np.sqrt(np.mean(np.log(np.array(observed) / np.array(predicted)) ** 2)))


def transfer(square, triangle):
    """Fit on square, predict triangle with the same coefficients.

    spread: standard deviation of each deformation (position in radians, amplitude and width as fractions)."""
    shapes = soft_shapes(square)
    soft = fit(square["variance"], shapes)
    axes = np.linalg.eigh(np.cov(square["residual"].T))[1][:, -3:]
    fixed = fit(square["variance"], fixed_shapes(square, axes))
    return {"soft_square": misfit(square["variance"], shapes, soft),
            "soft": misfit(triangle["variance"], soft_shapes(triangle), soft),
            "fixed": misfit(triangle["variance"], fixed_shapes(triangle, axes), fixed),
            "cross": decoding(triangle, soft),
            "a": float(soft[0]), "spread": dict(zip(MODES, np.sqrt(soft[1:]).tolist()))}


def main():
    rows = [r for r in harness.registered("dandi-000939-extract") if r["asset"].endswith(".npz")]
    harness.verify(rows)
    sessions = []
    for row in rows:
        square, triangle = load(row, "wake_square"), load(row, "wake_triangle")
        if square is None or triangle is None or len(square[0]) < 10:
            continue
        result = transfer(session(*windows(*square)), session(*windows(*triangle)))
        sessions.append({"session": row["asset"].split("_behavior")[0], "cells": len(square[0]), **result})
    med = {k: float(np.median([s[k] for s in sessions])) for k in ("soft_square", "soft", "fixed", "cross")}
    result = harness.record(
        "c4_3_soft_modes", "C4",
        "활동 변동 공분산은 Σ(θ) = aI + Σ s_j² d_j d_jᵀ (위치·진폭·폭 변형)이고, square로 맞춘 (a, s_j²)가 같은 세포의 "
        "triangle 잡음 구조와 해독 정밀도를 재적합 없이 맞춘다",
        "실측: DANDI:000939 생쥐 후구상 머리방향 세포, square로 맞추고 triangle로 판정. "
        "C4-1·C4-2를 본 뒤 세운 가설이며 triangle 요약값을 그 두 단계에서 본 적이 있다",
        {"sessions": harness.check(len(sessions), 5),
         "structure_transfer": harness.check(med["soft"], high=TOL),
         "cross_transfer": harness.check(med["cross"], high=TOL)},
        rows,
        proof=harness.reverse("상태를 따라 도는 부드러운 변형 방향 d_j(θ)", med["soft"], med["fixed"], TOL),
        median=med, median_a=float(np.median([s["a"] for s in sessions])),
        median_position_deg=float(np.degrees(np.median([s["spread"]["position"] for s in sessions]))),
        sessions=sessions)
    print(result["verdict"], "| 중앙값:", med, "| a:", result["measured"]["median_a"],
          "| 위치 흔들림(°):", result["measured"]["median_position_deg"])


if __name__ == "__main__":
    main()
