"""C2-1: 뉴런은 고리 위의 고정된 점이다 (전제 C2).

명제: 환경이 바뀌어도 각 머리방향 세포의 고리 위 자리(다른 세포에 대한 선호 방향의 차)는 고정되고, 바뀌는 것은 봉우리
전체의 회전(모든 세포가 함께)과 발화율(상태)뿐이다.
식: 세포 i의 이동 δ_i = θ_i(삼각형) − θ_i(사각형). 고정된 점이면 δ_i = 공통 회전 + 추정 잡음이므로 세션 안 이동의 평균
벡터 길이 R = |⟨e^{iδ}⟩|가 1에 가깝다. 점이 고정되지 않았다면(세포마다 제멋대로 다시 자리 잡음) R은 세포 짝을 섞은 값과 같다.
생물 기준값: Yoganarasimha et al. 2006 (J Neurosci 26:622): 동시 기록된 머리방향 세포 집단은 단서 회전에 225세션 중 한 번도
갈라지지 않았고, 집단 회전의 평균 벡터 길이는 0.93–0.96(한 조건 0.68), 95%가 20° 안에서 함께 돌았다.
자료(원장): dandi-000939-extract의 wake_square·wake_triangle이 모두 있는 세션(같은 세포, 두 환경).
방법: 저자 분류 머리방향 세포의 조율곡선(C4-1과 같은 6° 칸, σ 12°)에서 선호 방향(원형 평균)과 조율 벡터 길이를 얻고,
두 환경 모두 조율 벡터 길이 ≥ 0.3이고 최고 발화 ≥ 1 Hz인 세포만 쓴다. 세션마다 R을 구하고, 대조는 세션 안에서 삼각형
선호 방향의 세포 짝을 1000번 섞은 R의 평균이다.
판정(실행 전 고정):
- 세션 ≥ 5 (각 세션 세포 ≥ 5)
- 정확도: 세션 R 중앙값이 문헌 0.93–0.96에서 0.08 안 (0.85–1.0)
- 역증명: 1 − R(중앙값) ≤ 0.15 < 1 − R(짝 섞음, 중앙값)
"""

import numpy as np

from research import c3_2_trace_replication as c32
from research import harness, store
from research.c4_1_metric_hd import GRID, tuning

R_TUNED, PEAK, MIN_CELLS, SHUFFLES, TOL = 0.3, 1.0, 5, 1000, 0.15


def tuned(s, epoch):
    """Preferred direction, tuning vector length and peak rate of every unit in one environment."""
    (a,), (b,) = s.intervals("epochs", epoch)
    t, angle = s.series("head")
    inside = (t >= a) & (t < b)
    f = tuning(*c32.windows(s, t[inside], angle[inside], [(a, b)]))
    z = f @ np.exp(1j * GRID)
    return np.angle(z), np.abs(z) / f.sum(1), f.max(1)


def session(row, rng):
    s = store.load(row)
    if "wake_triangle" not in s["epochs_label"]:
        return None
    s = s.units(s["unit_is_head_direction"] == 1)
    (sq, r_sq, p_sq), (tri, r_tri, p_tri) = tuned(s, "wake_square"), tuned(s, "wake_triangle")
    use = (r_sq >= R_TUNED) & (r_tri >= R_TUNED) & (p_sq >= PEAK) & (p_tri >= PEAK)
    if use.sum() < MIN_CELLS:
        return None
    shift = np.exp(1j * (tri[use] - sq[use]))
    shuffled = [abs(np.mean(np.exp(1j * (rng.permutation(tri[use]) - sq[use])))) for _ in range(SHUFFLES)]
    return {"asset": row["asset"], "cells": int(use.sum()), "R": float(abs(shift.mean())),
            "rotation_deg": float(np.degrees(np.angle(shift.mean()))), "R_shuffled": float(np.mean(shuffled)),
            "peak_rate_log_change_median": float(np.median(np.abs(np.log(p_tri[use] / p_sq[use]))))}


def main():
    rows = [r for r in harness.registered("dandi-000939-extract") if r["asset"].endswith(".npz")]
    harness.verify(rows)
    rng = np.random.default_rng(0)
    sessions = [x for x in (session(r, rng) for r in rows) if x]
    r = np.median([x["R"] for x in sessions])
    shuffled = np.median([x["R_shuffled"] for x in sessions])
    result = harness.record(
        "c2_1_fixed_points", "C2",
        "환경이 바뀌어도 각 머리방향 세포의 고리 위 자리(다른 세포에 대한 선호 방향 차)는 고정되고, 바뀌는 것은 봉우리 전체의 "
        "회전과 발화율이다",
        "Yoganarasimha et al. 2006 J Neurosci 26:622: 동시 기록 머리방향 집단은 갈라지지 않고 함께 돈다(회전 평균 벡터 길이 "
        "0.93–0.96). 실측: DANDI:000939 (wake_square → wake_triangle, 같은 세포)",
        {"sessions": harness.check(len(sessions), 5), "accuracy": harness.check(r, 0.85, 1.0)},
        rows, proof=harness.reverse("고정된 점(세포 정체)", 1 - r, 1 - shuffled, TOL),
        sessions=sessions, R_median=float(r), R_shuffled_median=float(shuffled))
    print(result["verdict"], "세션", len(sessions), "R 중앙값 %.3f, 짝 섞음 %.3f" % (r, shuffled))
    for x in sessions:
        print("  ", x["asset"][:30], x["cells"], "세포 R %.3f 회전 %.0f° 섞음 %.3f 발화율 |log 변화| %.2f" % (
            x["R"], x["rotation_deg"], x["R_shuffled"], x["peak_rate_log_change_median"]))


if __name__ == "__main__":
    main()
