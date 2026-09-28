"""C3-5: 현재 상태에 남은 과거는 τ_h로 거른 과거 방향이다 (전제 C3).

C1-4를 본 뒤 세운 새 단계다. 흔적 식 τ_h ḣ = −h + x (x = e^{iθ})가 맞다면, 잠드는 순간의 흔적 중심은 잠들기 직전 10 s의 방향
θ_pre가 아니라 그 전 방향들을 τ_h로 거른 arg h다. C1-2·3은 θ_pre와 흔적 중심 사이에 잠들 때 어긋남 σ₀(57–77°)를 자유
매개변수로 두어야 맞았다. 이 단계는 C1-4의 τ_h(743 s)를 옮겨 와 매개변수 없이 예측한다.
명제: 기록 전체의 1 s 해독 방향을 τ로 거른 h_τ(잠들기 전 창까지)의 방향 arg h_τ에 대한 논렘 정렬은 τ ≈ τ_h에서 가장 높고,
arg h_{τ_h}는 θ_pre보다 논렘 방향을 잘 맞추며, arg h_{τ_h}와 θ_pre의 어긋남이 C1-2의 σ₀를 재현한다.
식: h_k = e^{−1/τ}h_{k−1} + x_k (1 s 창, 상태 표지가 없는 창은 x = 0). 정렬 a(c) = 사건 평균 Re(m_e e^{−ic_e}) − 순열 평균
(m_e: 사건의 논렘 창 방향 단위벡터 평균, c_e: 후보 중심, 순열은 세션 안 사건끼리 중심을 섞음). 세션 고정 치우침은 순열이 지운다.
어긋남 σ = √(−2 ln R), R = |사건 평균 e^{i(arg h − θ_pre)}| (감싼 정규의 표준편차, C1-2의 σ₀와 같은 정의).
옮기는 값: τ_h = `c1_4_common_trace_time.json`의 공통 τ, σ₀ = `c1_2_common_equation_onset.json`(000056 full, 000939 replication)과
`c1_3_parameter_transfer.json`(001699 free).
생물 기준값: 문헌에 흔적 적분 시간이 없어, 같은 식의 다른 관측(잠든 뒤 감쇠, C1-4)과 C1-2·3의 σ₀를 기준으로 삼는다.
자료(원장): dandi-000056 (주), dandi-000939-extract(첫 home_cage 사건), dandi-001699(야생형). 사건·θ_pre·논렘 창은 C3-2와 같고
(깸 ≥ 10 s 바로 뒤 논렘, 첫 480 s), 이력은 기록 처음부터 잠들기 직전까지의 1 s 창이다(창마다 그 상태의 평균 발화를 뺀 집단 벡터).
τ 격자 10·2^{k/2} s (k = 0–20, 10–10,240 s), 순열 1000번, 사건 부트스트랩 1000번.
판정(실행 전 고정):
- 000056: 세션 ≥ 5, 사건 ≥ 50
- 정확도(적분 시간): 000056 정렬이 가장 높은 격자 τ*가 τ_h의 2배 안
- 이득: 000056 a(h_{τ_h}) − a(θ_pre)의 부트스트랩 1% 백분위 > 0
- 어긋남: 000056 arg h_{τ_h}와 θ_pre의 σ가 σ₀의 1.5배 안
- 재현: 000939, 001699 각각 a(h_{τ_h}) − a(θ_pre)의 부트스트랩 1% 백분위 > 0
- 역증명(000056): 1 − a(h_{τ_h})/a(τ*) ≤ 0.1 < 1 − a(θ_pre)/a(τ*) (적분 없는 중심은 가장 나은 정렬의 90%에 못 미친다)
"""

import json

import numpy as np
from scipy.signal import lfilter

from research import harness, store
from research import c3_2_trace_replication as c32
from research import c3_3_restoring as c33
from research.c3_1_sleep_trace import BOOTSTRAP, LAGS, PERMUTATIONS, PRE, WINDOW
from research.c4_1_metric_hd import GRID, tuning

TAUS = 10 * 2 ** (np.arange(21) / 2)
AGREE, OFFSET, SHORTFALL = 2.0, 1.5, 0.1
RESULTS = harness.RESULTS


def transferred():
    """τ_h from C1-4 and σ₀ (rad) per data set from C1-2 and C1-3."""
    load = lambda name: json.loads((RESULTS / f"{name}.json").read_text(encoding="utf-8"))["measured"]
    c12, c13 = load("c1_2_common_equation_onset"), load("c1_3_parameter_transfer")
    return {"tau_h": load("c1_4_common_trace_time")["fixed_cohort"]["common"]["tau"][0],
            "sigma0": {"dandi_000056": c12["full"]["params"]["sigma0"],
                       "dandi_000939": c12["replication"]["params"]["sigma0"],
                       "dandi_001699": c13["free"]["params"]["sigma0"]}}


def trace_events(s, phi, table, wake, nrem, taus, limit=None):
    """Per NREM event (as in C3-2): mean NREM window direction m, θ_pre, and h_τ at sleep onset for every τ."""
    start, stop = s.intervals(table)
    label = s[f"{table}_label"]
    order = np.argsort(start)
    start, stop, label = start[order], stop[order], label[order]
    rate = {x: s.window_counts(start[label == x], stop[label == x]).sum(1) / (stop - start)[label == x].sum()
            for x in np.unique(label)}
    edges = np.arange(np.floor(start[0]), stop[-1], WINDOW)
    mid = edges[:-1] + WINDOW / 2
    k = (np.searchsorted(start, mid, side="right") - 1).clip(0)
    inside = (mid >= start[k]) & (mid < stop[k])
    expected = np.stack([rate[x] for x in label[k]], 1) * WINDOW
    z = ((s.counts(edges) - expected) * np.exp(1j * phi)[:, None]).sum(0)
    x = np.where(inside & (np.abs(z) > 0), z / np.where(np.abs(z) > 0, np.abs(z), 1), 0)
    h = np.stack([lfilter([1.0], [1.0, -np.exp(-WINDOW / tau)], x) for tau in taus])
    if limit is not None:
        keep = (start >= limit[0]) & (stop <= limit[1])
        start, stop, label = start[keep], stop[keep], label[keep]
    found = []
    for i in range(len(label) - 1):
        s0, e0, s1, e1 = start[i], stop[i], start[i + 1], stop[i + 1]
        if label[i] == wake and label[i + 1] == nrem and e0 - s0 >= PRE and 0 <= s1 - e0 <= 1:
            nrem_edges = np.arange(s1, min(e1, s1 + LAGS[-1]), WINDOW)
            last = np.searchsorted(edges[1:], s1, side="right") - 1  # 잠들기 전 마지막 창
            if len(nrem_edges) > 1 and last >= 0:
                theta = c32.direction(s, nrem_edges, rate[nrem], phi)
                found.append({"m": np.exp(1j * theta).mean(), "pre": c32.direction(s, [e0 - PRE, e0], rate[wake], phi)[0],
                              "h": h[:, last]})
    return found


def hd_cells(s, t, angle, spans):
    """Head-direction units and their preferred directions from the tuning inside spans."""
    f = tuning(*c32.windows(s, t, angle, spans))
    hd = (np.abs(f @ np.exp(1j * GRID)) / f.sum(1) >= c32.R_HD) & (f.max(1) >= c32.PEAK_HD)
    return hd, np.angle(f @ np.exp(1j * GRID))


def session_056(row, taus):
    s = store.load(row)
    t, angle = c33.head_angle(s)
    hd, phi = hd_cells(s, t, angle, zip(*s.intervals("states", "Awake")))
    return trace_events(s.units(hd), phi[hd], "states", "Awake", "Non-REM", taus) if hd.sum() >= c32.MIN_CELLS else None


def session_939(row, taus):
    s = store.load(row)
    s = s.units(s["unit_is_head_direction"] == 1)
    (a,), (b,) = s.intervals("epochs", "wake_square")
    t, angle = s.series("head")
    inside = (t >= a) & (t < b)
    f = tuning(*c32.windows(s, t[inside], angle[inside], [(a, b)]))
    if len(f) < c32.MIN_CELLS:
        return None
    home = s.intervals("epochs", "home_cage")
    return trace_events(s, np.angle(f @ np.exp(1j * GRID)), "sleep_states", "wake", "nrem", taus, (home[0][0], home[1][0]))


def session_1699(row, taus):
    s = store.load(row)
    t, angle = s.series("head")
    hd, phi = hd_cells(s, t, np.mod(angle, 2 * np.pi), [(t[0], t[-1])])
    return trace_events(s.units(hd), phi[hd], "sleep_stages", "wake", "nrem", taus) if hd.sum() >= c32.MIN_CELLS else None


def analyse(sessions, rng):
    """Permutation-corrected alignment to each candidate centre (arg h_τ for every τ, then θ_pre), bootstrapped over events."""
    found = [(g, e) for g, x in enumerate(sessions) if x for e in x]
    group = np.array([g for g, _ in found])
    m = np.array([e["m"] for _, e in found])
    centres = np.column_stack([np.angle(np.array([e["h"] for _, e in found])), [e["pre"] for _, e in found]])
    score = lambda c: (m[:, None] * np.exp(-1j * c)).real  # 사건 × 중심
    null = np.zeros(centres.shape[1])
    for _ in range(PERMUTATIONS):
        shuffled = centres.copy()
        for g in np.unique(group):
            at = np.flatnonzero(group == g)
            shuffled[at] = shuffled[rng.permutation(at)]
        null += score(shuffled).mean(0) / PERMUTATIONS
    a = score(centres).mean(0) - null
    weight = np.stack([np.bincount(rng.integers(0, len(m), len(m)), minlength=len(m)) for _ in range(BOOTSTRAP)])
    boot = weight @ score(centres) / weight.sum(1, keepdims=True) - null
    offset = np.abs(np.mean(np.exp(1j * (centres[:, :-1] - centres[:, -1:])), 0))
    return {"sessions": len(np.unique(group)), "events": len(m), "alignment": a.tolist(), "se": boot.std(0).tolist(),
            "boot": boot, "sigma": np.sqrt(-2 * np.log(offset)).tolist()}


def summarise(r):
    """τ* on the grid, the gain of arg h_{τ_h} over θ_pre, and the shortfalls from the best grid alignment.
    Centre columns: the TAUS grid, then τ_h, then θ_pre."""
    a, boot, n = np.array(r["alignment"]), r.pop("boot"), len(TAUS)
    best = int(np.argmax(a[:n]))
    return {**r, "tau_star": float(TAUS[best]),
            "tau_star_interval": np.percentile(TAUS[boot[:, :n].argmax(1)], [2.5, 97.5]).tolist(),
            "gain": float(a[n] - a[-1]), "gain_p1": float(np.percentile(boot[:, n] - boot[:, -1], 1)),
            "sigma_at_tau_h": float(r["sigma"][n]), "shortfall_trace": float(1 - a[n] / a[best]),
            "shortfall_pre": float(1 - a[-1] / a[best])}


def main():
    moved = transferred()
    tau_h = moved["tau_h"]
    taus = np.r_[TAUS, tau_h]
    rows = {"dandi_000056": harness.registered("dandi-000056"),
            "dandi_000939": [r for r in harness.registered("dandi-000939-extract") if r["asset"].endswith(".npz")],
            "dandi_001699": harness.registered("dandi-001699")}
    harness.verify([r for x in rows.values() for r in x])
    load = {"dandi_000056": session_056, "dandi_000939": session_939, "dandi_001699": session_1699}
    out = {name: summarise(analyse([load[name](r, taus) for r in rows[name]], np.random.default_rng(0)))
           for name in rows}
    main56 = out["dandi_000056"]
    sigma0 = moved["sigma0"]["dandi_000056"]
    result = harness.record(
        "c3_5_trace_center", "C3",
        "잠드는 순간의 흔적 중심은 잠들기 직전 방향이 아니라 과거 방향을 τ_h(C1-4)로 거른 arg h이고, 그 적분 시간이 논렘 정렬을 "
        "가장 높이며, arg h와 θ_pre의 어긋남이 C1-2의 σ₀를 재현한다",
        "같은 식의 다른 관측: C1-4의 τ_h(잠든 뒤 감쇠), C1-2·3의 σ₀. 실측: DANDI:000056 (주), DANDI:000939, DANDI:001699",
        {"sessions": harness.check(main56["sessions"], 5), "events": harness.check(main56["events"], 50),
         "integration_time": harness.check(abs(np.log(main56["tau_star"] / tau_h)), high=float(np.log(AGREE))),
         "gain": harness.check(main56["gain_p1"], low=0),
         "offset": harness.check(abs(np.log(main56["sigma_at_tau_h"] / sigma0)), high=float(np.log(OFFSET))),
         "replication_000939": harness.check(out["dandi_000939"]["gain_p1"], low=0),
         "replication_001699": harness.check(out["dandi_001699"]["gain_p1"], low=0)},
        [r for x in rows.values() for r in x],
        proof=harness.reverse("τ_h로 적분한 흔적 중심", main56["shortfall_trace"], main56["shortfall_pre"], SHORTFALL),
        transferred=moved, taus=taus.tolist(), **out)
    print(result["verdict"], {k: v["passed"] for k, v in result["checks"].items()}, result["reverse_proof"]["passed"])
    for name, r in out.items():
        print(name, r["events"], "τ* %.0f s %s, 이득 %.3f (1%% %.3f), σ %.0f° (sigma0 %.0f°), 부족분 %.2f / %.2f" % (
            r["tau_star"], np.round(r["tau_star_interval"]).tolist(), r["gain"], r["gain_p1"],
            np.degrees(r["sigma_at_tau_h"]), np.degrees(moved["sigma0"][name]), r["shortfall_trace"], r["shortfall_pre"]))


if __name__ == "__main__":
    main()
