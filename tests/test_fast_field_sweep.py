"""`cefast.ring_field`과 `cefast.ring_sweep`의 물리 극한 검사(D20). 둘 다 1 s 창의 원형 평균 방향을 낸다.

- 자유 확산(A = 0, v = 0): Leimkuhler–Matthews 잡음 √(D·dt/2)(ξ_n + ξ_{n+1})은 걸음마다 분산 D·dt지만 이웃 걸음이 ξ를
  나눠 가져 쌓이면 분산이 2D·t다(dθ = √(2D) dW, 논문 식과 같다). 그래서 창 평균의 이웃 차이 분산은 4D/3.
- 쓸기(D → 0, A = 0, τ_ω ≫ 1): θ가 정상 OU 각속도 ω ~ N(0, v²)로 움직여 이웃 차이 분산은 v².
- 묶인 우물(τ → ∞라 흔적 h가 처음 방향 0에 고정): 작은 각에서 θ는 OU, 이완율 κ, 정상 분산 D/κ = 1/A'이고
  창 평균의 분산은 (1/(2A'))·2(κ − 1 + e^{−κ})/κ². field는 κ = D·A·c₁, A' = A·c₁, sweep은 κ = D·β·A, A' = β·A.
"""

import math

import cefast
import numpy as np

PATHS, WINDOWS, SUBSTEPS = 400, 240, 200


def run_field(d, a, tau, coef, seed=7):
    lengths = np.full(PATHS, WINDOWS, np.int64)
    return cefast.ring_field(lengths, WINDOWS, d, a, tau, np.asarray(coef, float), SUBSTEPS, seed)


def run_sweep(d, a, tau, beta, speed, tau_w, seed=7):
    lengths = np.full(PATHS, WINDOWS, np.int64)
    return cefast.ring_sweep(lengths, WINDOWS, d, a, tau, beta, speed, tau_w, SUBSTEPS, seed)


def step_variance(out):
    return float(np.var(np.diff(np.unwrap(out, axis=1), axis=1)))


def window_mean_variance(kappa, var):
    return var * 2 * (kappa - 1 + math.exp(-kappa)) / kappa ** 2


def test_free_diffusion_in_both_kernels():
    d = 0.02
    for out in (run_field(d, 0.0, 1.0, [1.0]), run_sweep(d, 0.0, 1.0, 5.2, 0.0, 1.0)):
        assert abs(step_variance(out) / (4 * d / 3) - 1) < 0.06


def test_sweep_moves_with_the_stationary_angular_velocity():
    out = run_sweep(1e-8, 0.0, 1.0, 5.2, 0.3, 1e6)
    assert abs(step_variance(out) / 0.3 ** 2 - 1) < 0.15


def test_pinned_well_is_the_ou_limit():
    burn = 40
    field = run_field(0.04, 50.0, 1e9, [1.0])[:, burn:]
    assert abs(float(np.var(field)) / window_mean_variance(0.04 * 50, 1 / 50) - 1) < 0.1
    # sweep의 우물 g = e^{β(cos −1)}은 깊이가 A뿐이라 얕으면 고리 전체로 새는 꼬리가 분산을 키운다: 깊게(βA = 260) 둔다
    sweep = run_sweep(0.04, 50.0, 1e9, 5.2, 0.0, 1.0)[:, burn:]
    assert abs(float(np.var(sweep)) / window_mean_variance(0.04 * 5.2 * 50, 1 / (5.2 * 50)) - 1) < 0.1


def test_still_ring_stays_put_and_short_paths_are_padded():
    out = run_field(0.0, 0.0, 1.0, [1.0])
    assert np.all(out == 0.0)
    lengths = np.array([3, 0], np.int64)
    short = cefast.ring_sweep(lengths, 5, 0.1, 0.0, 1.0, 5.2, 0.0, 1.0, 10, 1)
    assert np.isfinite(short[0, :3]).all() and np.isnan(short[0, 3:]).all() and np.isnan(short[1]).all()
