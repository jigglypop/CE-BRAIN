"""C1-12: 흔적과 공통 τ는 해독 인공물 없이도 선다 (전제 C1).

C1-11을 본 뒤 세운 새 단계다. 지금까지의 해독(초과 발화 벡터 Σ_i(n_i − r_i W)e^{iφ_i})은 스파이크가 적은 창을 세션마다 고정된 "빈 방향" −Σ_i r_i e^{iφ_i}로
읽었다(000056 논렘 스파이크 수 하위 10%에서 빈 방향과의 cos 0.644). 채택한 결과(C3-1의 흔적, C1-4의 공통 τ)가 이 인공물에 기대는지 본다.
해독기: 이득에 불변인 집단 벡터 θ = arg Σ_i (n_i / r̄_i)e^{iφ_i} (r̄_i: 그 상태의 평균 발화, 0.1 Hz 바닥). 발화율을 빼지 않으므로 스파이크가 없어도 고정 방향이
생기지 않고, 집단 전체의 발화가 함께 줄어도 방향이 그대로다. 스파이크가 하나도 없는 창에는 무작위 방향을 준다(정렬·자기상관에 치우침 없이 잡음만 더한다).
명제: 이 해독기로 다시 재도 (1) 빈 방향 인공물은 사라지고, (2) 세 자료 모두 흔적이 있으며, (3) 같은 논렘 구간 집단에서 τ 하나의 지수식이 세 자료의 정렬 감쇠를
함께 맞춘다(C1-4의 기준 그대로).
방법: C1-4와 같다(사건·지연 칸·순열·부트스트랩). 해독 함수만 바꾼다(`c3_2.direction`을 이 해독기로 바꿔 끼운다; θ_pre도 같은 해독기).
생물 기준값: C1-4와 같다(서로 독립인 세 자료의 일치).
자료(원장): dandi-000056, dandi-000939-extract(첫 home_cage), dandi-001699(야생형).
판정(실행 전 고정):
- 인공물: 000056 논렘에서 스파이크 수 하위 10% 창의 해독 방향과 빈 방향의 cos 평균 ≤ 0.1
- 흔적 존재: 자료마다 첫 칸 정렬이 순열 분포의 99번째 백분위를 넘는다
- 정확도: 공통 τ 지수식의 공동 χ²/자유도 ≤ 2
- 공통: χ²(공통 τ) − χ²(자료별 τ) ≤ 5.99
- 역증명: 공통 τ 지수식 ≤ 2 < 흔적 없는 식(a = 0)의 공동 χ²/자유도
보고(판정 아님): 공통 τ와 구간(C1-4: 743 s), 자료별 정렬 곡선, 000056의 C3-8 R(L), 깸에서 해독 방향과 머리의 정렬.
"""

import numpy as np

from research import c1_4_common_trace_time as c14
from research import c3_2_trace_replication as c32
from research import c3_3_restoring as c33
from research import c3_8_record_relocation as c38
from research import harness, store
from research.c3_1_sleep_trace import CHI2, WINDOW
from research.c4_1_metric_hd import GRID, tuning

FLOOR, ARTIFACT, SEED = 0.1, 0.1, 5
excess_direction = c32.direction


def clean_direction(s, edges, rate, phi, rng=np.random.default_rng(SEED)):
    """Gain-invariant population vector arg Σ_i (n_i / r̄_i)e^{iφ_i}; a random direction where no cell fires."""
    counts = s.counts(np.asarray(edges, np.float64))
    v = ((counts / np.maximum(rate, FLOOR)[:, None]) * np.exp(1j * phi)[:, None]).sum(0)
    return np.where(counts.sum(0) > 0, np.angle(v), rng.uniform(-np.pi, np.pi, counts.shape[1]))


def artifact_check(rows):
    """Mean cos(decoded − empty direction) in the lowest-count 10% of 000056 NREM windows, for both decoders."""
    out = {"excess": [], "clean": [], "n": []}
    for row in rows:
        s = store.load(row)
        t, angle = c33.head_angle(s)
        f = tuning(*c32.windows(s, t, angle, zip(*s.intervals("states", "Awake"))))
        hd = (np.abs(f @ np.exp(1j * GRID)) / f.sum(1) >= c32.R_HD) & (f.max(1) >= c32.PEAK_HD)
        if hd.sum() < c32.MIN_CELLS:
            continue
        s, phi = s.units(hd), np.angle(f[hd] @ np.exp(1j * GRID))
        st, sp = s.intervals("states", "Non-REM")
        r = s.window_counts(st, sp).sum(1) / (sp - st).sum()
        empty = np.angle(-(r * np.exp(1j * phi)).sum())
        for a, b in zip(st, sp):
            edges = np.arange(a, min(b, a + 480), WINDOW)
            if len(edges) > 1:
                out["excess"].append(np.cos(excess_direction(s, edges, r, phi) - empty))
                out["clean"].append(np.cos(clean_direction(s, edges, r, phi) - empty))
                out["n"].append(s.counts(edges).sum(0))
    n = np.concatenate(out["n"])
    low = n < np.quantile(n, 0.1)
    return {k: float(np.concatenate(out[k])[low].mean()) for k in ("excess", "clean")}


def main():
    rows56 = harness.registered("dandi-000056")
    rows39 = [r for r in harness.registered("dandi-000939-extract") if r["asset"].endswith(".npz")]
    rows99 = harness.registered("dandi-001699")
    harness.verify(rows56 + rows39 + rows99)
    artifact = artifact_check(rows56)
    c32.direction = clean_direction  # 이 단계의 모든 해독(θ_pre, 논렘 창)을 이득 불변 집단 벡터로
    try:
        sessions = [[c32.session_056(r) for r in rows56], [c32.session_939(r) for r in rows39],
                    [c14.session_1699(r) for r in rows99]]
    finally:
        c32.direction = excess_direction
    fixed = c14.analyse([c14.cohort(s) for s in sessions])
    names = ("dandi_000056", "dandi_000939", "dandi_001699")
    thetas56 = [theta for f in sessions[0] if f for _, _, theta in f]
    group56 = np.array([g for g, f in enumerate(sessions[0]) if f for _ in f])
    relocation = c38.curve(thetas56, group56, np.random.default_rng(0))
    checks = {"artifact_removed": harness.check(artifact["clean"], high=ARTIFACT)}
    checks |= {f"trace_{n}": harness.check(c["alignment"][0] - c["null_top"], low=0) for n, c in zip(names, fixed["curves"])}
    checks |= {"accuracy": harness.check(fixed["common"]["chi2_dof"], high=CHI2),
               "common_tau": harness.check(fixed["delta_chi2"], high=c14.COMMON)}
    result = harness.record(
        "c1_12_clean_decoder", "C1",
        "빈 방향 인공물이 없는 이득 불변 집단 벡터로 다시 재도 세 자료 모두 흔적이 있고, 같은 논렘 구간 집단에서 τ 하나의 지수식이 세 자료의 정렬 감쇠를 함께 "
        "맞춘다",
        "C1-4와 같다(서로 독립인 세 자료의 일치). 실측: DANDI:000056, DANDI:000939, DANDI:001699",
        checks, rows56 + rows39 + rows99,
        proof=harness.reverse("흔적 h (공통 τ_h)", fixed["common"]["chi2_dof"], fixed["none_chi2_dof"], CHI2),
        artifact=artifact, fixed_cohort=fixed, relocation_000056=relocation)
    print(result["verdict"], {k: v["passed"] for k, v in checks.items()}, result["reverse_proof"]["passed"])
    print("artifact (cos to empty, lowest 10%%): excess %.3f clean %.3f" % (artifact["excess"], artifact["clean"]))
    print("events", [c["events"] for c in fixed["curves"]], "common tau %.0f %s chi2/dof %.2f each %s dchi2 %.2f" % (
        fixed["common"]["tau"][0], np.round(fixed["tau_interval"]).tolist(), fixed["common"]["chi2_dof"],
        np.round(fixed["separate"]["tau"]).tolist(), fixed["delta_chi2"]))
    for n, c in zip(names, fixed["curves"]):
        print("  ", n, np.round(c["alignment"], 3).tolist(), "null99 %.3f" % c["null_top"])
    print("R(L) 000056 clean", np.round(relocation["R"], 3).tolist(), "se", np.round(relocation["se"], 3).tolist(), "count", relocation["count"])


if __name__ == "__main__":
    main()
