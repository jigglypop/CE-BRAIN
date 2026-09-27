"""C6-1: 활동 이력이 관계를 바꾼다 — 트랙 경험 뒤 수면의 쌍 결합 (전제 C6).

명제: 새 트랙에서 함께 발화한 CA1 흥분성 세포 쌍의 관계(발화 상관)는 경험 뒤 논렘에서 경험 전 관계를 넘어 트랙의
관계를 닮도록 바뀐다. 시간을 뒤집은 대조(경험 뒤 관계로 경험 전 관계를 설명)는 그만큼 맞지 않는다.
식 (쌍마다 100 ms 칸 발화 수의 피어슨 상관 r; 세션 안 쌍들에 걸친 상관을 r_RUN,POST 등으로 쓴다):
- 이력: EV = r²_RUN,POST|PRE = [(r_RP − r_RE·r_EP) / √((1 − r_RE²)(1 − r_EP²))]²
- 이력 없음(시간 대칭): REV = r²_RUN,PRE|POST = [(r_RE − r_RP·r_EP) / √((1 − r_RP²)(1 − r_EP²))]²
생물 기준값: Kudrimoti et al. 1999 (J Neurosci 19:4090): CA1 피라미드 세포의 행동 중 상관이 직후 수면 상관 분산의 약 15%를
설명한다(서로 다른 테트로드 쌍).
자료(원장): dandi-000044 (Grosmark & Buzsáki 2016, 쥐 4마리 8세션, 수면 전 → 새 선형 트랙 → 수면 후, 양쪽 CA1).
방법: 흥분성 단위 가운데 세 구간 모두 ≥ 0.1 Hz인 세포, 다른 샤프트의 쌍. PRE는 수면 전 에포크 논렘의 마지막 60분,
POST는 수면 후 에포크 논렘의 처음 60분, RUN은 트랙 에포크 전체. 칸은 반열린 구간이고 논렘 구간 안에 온전히 든 칸만 쓴다.
세션마다 EV·REV를 구해 세션 평균을 쓰고, 불확도는 세션 부트스트랩 1000번.
판정(실행 전 고정):
- 세션 ≥ 5 (각 세션 쌍 ≥ 50)
- 정확도: 세션 평균 EV가 기준값 15%의 1/3–3배 (0.05–0.45)
- 이력: 세션 평균 EV − REV의 부트스트랩 1% 백분위 > 0
- 역증명: |log(EV/0.15)| ≤ log 3 < |log(REV/0.15)|
"""

import numpy as np

from research import harness, store

BIN, SLEEP, MIN_RATE, MIN_PAIRS = 0.1, 3600.0, 0.1, 50
LITERATURE, FACTOR, BOOT = 0.15, 3.0, 1000


def sleep_bins(s, epoch, first):
    """Bin edges pairs [start, stop) of 100 ms bins inside NREM of an epoch: the first or last hour."""
    (a,), (b,) = s.intervals("epochs", epoch)
    start, stop = s.intervals("states", "Non-REM")
    keep = (start >= a) & (stop <= b)
    bins = np.concatenate([np.arange(x, y - BIN + 1e-9, BIN) for x, y in zip(start[keep], stop[keep])])
    bins = bins[: int(SLEEP / BIN)] if first else bins[-int(SLEEP / BIN):]
    return bins, bins + BIN


def correlations(counts):
    """Pearson correlation matrix of spike counts (cells × bins)."""
    return np.corrcoef(counts.astype(float))


def session(row):
    s = store.load(row)
    s = s.units(s["unit_cell_type"] == "excitatory")
    (a,), (b,) = s.intervals("epochs", "MazeEpoch")
    periods = {"PRE": sleep_bins(s, "PREEpoch", first=False), "POST": sleep_bins(s, "POSTEpoch", first=True),
               "RUN": (np.arange(a, b - BIN, BIN), np.arange(a, b - BIN, BIN) + BIN)}
    counts = {k: s.window_counts(*v) for k, v in periods.items()}
    rate = np.stack([c.sum(1) / (len(c[0]) * BIN) for c in counts.values()])
    use = (rate >= MIN_RATE).all(0)
    shank = s["unit_shank_id"][use]
    pairs = np.triu(shank[:, None] != shank[None, :], 1)
    r = {k: correlations(c[use])[pairs] for k, c in counts.items()}
    return {"cells": int(use.sum()), "pairs": int(pairs.sum()), "hours": {k: len(v[0]) * BIN / 3600 for k, v in periods.items()},
            **explained(r["RUN"], r["PRE"], r["POST"])}


def explained(run, pre, post):
    rp, re, ep = (np.corrcoef(x, y)[0, 1] for x, y in ((run, post), (run, pre), (pre, post)))
    ev = ((rp - re * ep) / np.sqrt((1 - re ** 2) * (1 - ep ** 2))) ** 2
    rev = ((re - rp * ep) / np.sqrt((1 - rp ** 2) * (1 - ep ** 2))) ** 2
    return {"r_run_post": float(rp), "r_run_pre": float(re), "r_pre_post": float(ep), "ev": float(ev), "rev": float(rev)}


def main():
    rows = harness.registered("dandi-000044")
    harness.verify(rows)
    sessions = [dict(asset=r["asset"], **session(r)) for r in rows]
    used = [x for x in sessions if x["pairs"] >= MIN_PAIRS]
    ev, rev = np.array([x["ev"] for x in used]), np.array([x["rev"] for x in used])
    rng = np.random.default_rng(0)
    draws = rng.integers(0, len(used), (BOOT, len(used)))
    margin = (ev[draws] - rev[draws]).mean(1)
    error = lambda v: abs(np.log(v / LITERATURE))
    result = harness.record(
        "c6_1_reactivation", "C6",
        "새 트랙에서 함께 발화한 CA1 쌍의 관계는 경험 뒤 논렘에서 경험 전 관계를 넘어 트랙의 관계를 닮도록 바뀌고, 시간을 "
        "뒤집은 대조는 그만큼 맞지 않는다",
        "Kudrimoti et al. 1999 J Neurosci 19:4090: 행동 중 상관이 직후 수면 상관 분산의 약 15%를 설명(EV). "
        "실측: DANDI:000044 (Grosmark & Buzsáki 2016)",
        {"sessions": harness.check(len(used), 5),
         "accuracy": harness.check(ev.mean(), LITERATURE / FACTOR, LITERATURE * FACTOR),
         "history": harness.check(float(np.percentile(margin, 1)), low=0)},
        rows, proof=harness.reverse("활동 이력(경험 뒤 방향)", error(ev.mean()), error(rev.mean()), np.log(FACTOR)),
        sessions=sessions, ev_mean=float(ev.mean()), rev_mean=float(rev.mean()),
        ev_minus_rev_p1=float(np.percentile(margin, 1)))
    print(result["verdict"], "EV %.3f REV %.3f (1%% 백분위 차 %.3f)" % (ev.mean(), rev.mean(), np.percentile(margin, 1)))
    for x in sessions:
        print("  ", x["asset"][:40], x["cells"], "세포", x["pairs"], "쌍", {k: round(v, 3) for k, v in x.items()
                                                                     if k in ("ev", "rev", "r_run_post", "r_run_pre", "r_pre_post")})


if __name__ == "__main__":
    main()
