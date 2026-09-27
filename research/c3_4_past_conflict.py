"""C3-4: 과거와 현재가 갈등하면 흔적의 중심은 과거다 (전제 C3).

C3-3(중심 미확립)과 C8-1(000056의 갈등 창에서 과거 무게 0.216, 현재 머리 0.052)을 본 뒤 세운 가설이다. 000056에서
본 것을 같은 자료로 판정하지 않고, 아직 이 분석을 하지 않은 독립 자료 000939에서 판정한다.
명제: 잠들기 전 내부 방향 θ_pre(과거)와 잠든 머리 방향 θ_head(현재)가 90° 이상 떨어진 논렘 창에서, 내부 방향은
현재보다 과거에 더 자주 놓인다.
식: C8-1의 전체식 w_p·vM(θ_pre) + w_h·vM(θ_head) + w_m·vM(θ_mid) + 균등. 과거 항을 뺀 식(w_p = 0)이 역증명의 대안이다.
기준값: 000056의 C8-1 측정(w_p 0.216, w_h 0.052; 다른 연구실의 자료). 문헌에 수면 중 과거·현재 무게의 값은 없다.
자료(원장): dandi-000939-extract의 첫·둘째 home_cage 논렘 가운데 머리가 추적된 창(추적은 일부 세션·구간만 있다).
사건·창은 C3-2와 같다(깸 ≥ 10 s 뒤 논렘, 1 s 창, 첫 480 s).
판정(실행 전 고정):
- 창 ≥ 500, 사건 ≥ 20
- 과거 우세: w_p − w_h의 사건 부트스트랩 1% 백분위 > 0
- 역증명: AIC(전체) − AIC(최선) ≤ 10 < AIC(과거 항 없음) − AIC(최선)
"""

import numpy as np

from research import c3_2_trace_replication as c32
from research import c3_3_restoring as c33
from research import c8_1_selection as c8
from research import harness, store
from research.c4_1_metric_hd import GRID, tuning

CENTERS = {"full": ("pre", "head", "mid"), "no_past": ("head", "mid")}
CLAIM = "잠들기 전 내부 방향(과거)과 잠든 머리 방향(현재)이 90° 이상 떨어진 논렘 창에서 내부 방향은 현재보다 과거에 더 자주 놓인다"
REFERENCE = "000056의 C8-1 측정(과거 0.216, 현재 0.052)을 다른 연구실 자료에서 재현한다. 실측: DANDI:000939"
BOOT, MARGIN = 200, 10.0


def session(row):
    """C3-2 events of both home cages with the tracked head direction at each NREM window."""
    s = store.load(row)
    s = s.units(s["unit_is_head_direction"] == 1)
    (a,), (b,) = s.intervals("epochs", "wake_square")
    t, angle = s.series("head")
    inside = (t >= a) & (t < b)
    f = tuning(*c32.windows(s, t[inside], angle[inside], [(a, b)]))
    if len(f) < c32.MIN_CELLS:
        return []
    phi = np.angle(f @ np.exp(1j * GRID))
    start, stop = s.intervals("epochs", "home_cage")
    return [e for limit in zip(start, stop)
            for e in c33.events(s, phi, "sleep_states", "wake", "nrem", limit, head=(t, angle))]


def main():
    rows = [r for r in harness.registered("dandi-000939-extract") if r["asset"].endswith(".npz")]
    harness.verify(rows)
    theta, centers, owner = c8.windows([session(r) for r in rows])
    if not len(theta):  # 000939는 home_cage 수면 중 머리를 추적하지 않았다: 검사할 창이 없으면 미확립
        result = harness.record(
            "c3_4_past_conflict", "C3", CLAIM, REFERENCE,
            {"windows": harness.check(None), "events": harness.check(None), "past_over_present": harness.check(None)},
            rows, windows=0, note="home_cage 수면 중 머리 추적 없음")
        print(result["verdict"], "갈등 창 없음")
        return
    fits = {name: c8.fit(theta, [centers[c] for c in names]) for name, names in CENTERS.items()}
    best = min(f["aic"] for f in fits.values())
    events = np.unique(owner)
    rng = np.random.default_rng(0)
    margin = []
    for _ in range(BOOT):
        draw = np.bincount(rng.choice(len(events), len(events)), minlength=len(events)).astype(float)
        w = c8.fit(theta, [centers[c] for c in CENTERS["full"]], draw[np.searchsorted(events, owner)],
                   fits["full"]["x"])["weights"]
        margin.append(w[0] - w[1])
    full = fits["full"]["weights"]
    result = harness.record(
        "c3_4_past_conflict", "C3", CLAIM, REFERENCE,
        {"windows": harness.check(len(theta), 500), "events": harness.check(len(events), 20),
         "past_over_present": harness.check(float(np.percentile(margin, 1)), low=0)},
        rows, proof=harness.reverse("과거 흔적 항", fits["full"]["aic"] - best, fits["no_past"]["aic"] - best, MARGIN),
        windows=int(len(theta)), events=int(len(events)), fits=fits,
        past_minus_present=float(full[0] - full[1]), past_minus_present_p1=float(np.percentile(margin, 1)))
    print(result["verdict"], len(theta), "창", len(events), "사건 |", {k: (np.round(v["weights"], 3).tolist(),
          round(v["kappa"], 2), round(v["aic"] - best, 1)) for k, v in fits.items()},
          "| 과거−현재 1%:", round(float(np.percentile(margin, 1)), 3))


if __name__ == "__main__":
    main()
