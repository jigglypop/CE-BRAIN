"""C3-10: 짧은 이탈은 세션 안의 같은 자리로 모인다 — 장기 기록의 고정 끌개 (전제 C3).

C3-8·C3-9·C1-10을 본 뒤 세운 새 단계다. 논렘 방향이 기록 자리(논렘 처음 30 s의 평균 방향)를 5–15 s 벗어난 뒤 모든 식이 되돌아옴을 과대 예측했고,
관측 잡음(C1-10)과 기록장의 여러 봉우리(C3-9)는 그 원인이 아니었다. 남은 후보는 며칠에 걸친 장기 기록(또는 연결체의 비균질)이 세션 안에 고정된
끌개를 남겨 벗어난 상태를 붙드는 것이다.
명제: 000056 논렘에서 기록 자리를 90° 넘게 5–15 s 벗어난 방향의 도착점(벗어난 동안 5 s 끝 원형 평균의 원형 평균)은 같은 세션의 다른 사건 도착점과,
사건마다의 기록 자리와 그 자리에서 벗어난 각도만으로 기대되는 것보다 더 같은 자리로 모인다.
통계: S = 같은 세션 다른 사건의 도착점 짝의 cos(d_i − d_j) 평균. 널: 도착점의 기록 자리에 대한 상대 각은 두고 기록 자리만 세션 안 사건끼리 섞는다
(둥지에서 같은 방향으로 잠드는 효과는 널에 남는다). 효과 = S − 널 평균, 순열 1000번.
해독 치우침: 세션마다 깸 1 s 창에서 잰 머리 방향 30° 칸별 해독 오차의 원형 평균(C1-9)을 해독 방향에서 뺀다.
생물 기준값: 자료 안의 널(문헌에 논렘 고정 끌개 값이 없다). 모형 대조: C1-7 해의 v3(고정 끌개 없음)는 같은 과정에서 효과가 0이어야 한다.
자료(원장): dandi-000056 (C3-2 사건, 첫 480 s), 방향 세포 ≥ 10인 세션.
판정(실행 전 고정):
- 세션 ≥ 5, 5–15 s 이탈 ≥ 500
- 명제: 효과 > 0이고 순열 p < 0.01 (한쪽)
보고(판정 아님): 세션별 효과, 치우침 보정 없이 잰 효과.
"""

import numpy as np

from research import c1_9_decoding_noise as c19
from research import c3_2_trace_replication as c32
from research import c3_8_record_relocation as c38
from research import harness
from research.c3_1_sleep_trace import PERMUTATIONS

SHORT, BIAS_BINS, ALPHA = (5, 15), 12, 0.01


def destinations(theta):
    """(early centre, destinations of the 5–15 s away runs) of one event, as in C3-8."""
    centre = np.angle(np.exp(1j * theta[:c38.EARLY]).sum())
    th = theta[c38.EARLY:]
    c = np.cumsum(np.r_[0, np.exp(1j * th)])
    smooth = c[c38.SMOOTH:] - c[:-c38.SMOOTH]
    away = np.abs(np.angle(smooth * np.exp(-1j * centre))) > c38.AWAY
    out, run = [], 0
    for i, a in enumerate(away):
        run = run + 1 if a else 0
        if a and (i + 1 == len(away) or not away[i + 1]) and SHORT[0] <= run < SHORT[1]:
            out.append(np.angle(smooth[i - run + 1:i + 1].sum()))
    return centre, np.array(out)


def bias_map(wake):
    """Per 30° head bin, the unit mean decoding error in wake (rows: error, head, still, run from C1-9)."""
    ok = np.isfinite(wake[:, 0])
    b = (np.mod(wake[ok, 1], 2 * np.pi) / (2 * np.pi) * BIAS_BINS).astype(int).clip(0, BIAS_BINS - 1)
    m = np.array([np.exp(1j * wake[ok, 0][b == j]).mean() if (b == j).any() else 1.0 for j in range(BIAS_BINS)])
    return m / np.abs(m)


def corrected(theta, bias):
    b = (np.mod(theta, 2 * np.pi) / (2 * np.pi) * BIAS_BINS).astype(int).clip(0, BIAS_BINS - 1)
    return np.angle(np.exp(1j * theta) * np.conj(bias[b]))


def pairs_mean(d, owner):
    """Mean cos(d_i − d_j) over pairs from different events."""
    z = np.exp(1j * d)
    total = np.abs(z.sum()) ** 2 - len(z)
    same = sum(np.abs(z[owner == e].sum()) ** 2 - (owner == e).sum() for e in np.unique(owner))
    n = len(z) ** 2 - len(z) - sum((owner == e).sum() ** 2 - (owner == e).sum() for e in np.unique(owner))
    return (total - same) / n if n > 0 else np.nan, n


def analyse(sessions, rng):
    """Pooled effect S − null over sessions (weighted by pairs), its permutation p, and the per-session effects."""
    stats, per = [], []
    for events in sessions:
        cd = [destinations(th) for th in events]
        centres = np.array([c for c, _ in cd])
        owner = np.concatenate([np.full(len(d), e) for e, (_, d) in enumerate(cd)])
        if len(owner) < 4:
            continue
        rel = np.concatenate([np.angle(np.exp(1j * (d - c))) for c, d in cd])
        s, n = pairs_mean(centres[owner] + rel, owner)
        null = np.array([pairs_mean(rng.permutation(centres)[owner] + rel, owner)[0] for _ in range(PERMUTATIONS)])
        stats.append((s, null, n))
        per.append(float(s - null.mean()))
    w = np.array([n for _, _, n in stats], float)
    s = np.array([x for x, _, _ in stats]) @ w / w.sum()
    null = np.stack([x for _, x, _ in stats], 1) @ w / w.sum()
    return {"effect": float(s - null.mean()), "p": float((np.sum(null >= s) + 1) / (len(null) + 1)), "sessions": len(stats),
            "excursions": int(sum(len(destinations(th)[1]) for ev in sessions for th in ev)), "per_session": per}


def main():
    rows = harness.registered("dandi-000056")
    harness.verify(rows)
    raw, fixed = [], []
    for row in rows:
        found, wake = c32.session_056(row), c19.session(row)
        if not found or wake is None:
            continue
        bias = bias_map(wake)
        raw.append([theta for _, _, theta in found])
        fixed.append([corrected(theta, bias) for _, _, theta in found])
    r = analyse(fixed, np.random.default_rng(0))
    r_raw = analyse(raw, np.random.default_rng(0))
    result = harness.record(
        "c3_10_fixed_attractors", "C3",
        "논렘에서 기록 자리를 5–15 s 벗어난 방향의 도착점은 같은 세션의 다른 사건 도착점과, 사건마다의 기록 자리와 상대 각만으로 기대되는 것보다 더 같은 "
        "자리로 모인다: 장기 기록이 세션 안에 고정된 끌개를 남긴다",
        "자료 안의 널(기록 자리를 세션 안 사건끼리 섞음)과 고정 끌개 없는 v3 모형 대조. 실측: DANDI:000056",
        {"sessions": harness.check(r["sessions"], 5), "excursions": harness.check(r["excursions"], 500),
         "effect": harness.check(r["effect"], low=0), "significance": harness.check(r["p"], high=ALPHA)},
        rows, bias_corrected=r, uncorrected=r_raw)
    print(result["verdict"], {k: v["passed"] for k, v in result["checks"].items()})
    for name, x in (("bias corrected", r), ("uncorrected", r_raw)):
        print(name, "effect %.4f p %.4f sessions %d excursions %d" % (x["effect"], x["p"], x["sessions"], x["excursions"]),
              "per session", np.round(x["per_session"], 3).tolist())


if __name__ == "__main__":
    main()
