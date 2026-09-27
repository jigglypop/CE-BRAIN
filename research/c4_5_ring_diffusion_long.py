"""C4-5: 렘의 고리 위 상태 변화는 수 초까지 확산이다 (전제 C4).

C4-4를 본 뒤 세운 새 단계다. C4-4는 0.7 s 안에서 조화 비가 30%만 줄어 확산(리만 이차 비용)과 쓸기(속도 입력)를 가를
검정력이 없었고, 확산 기울기 M은 문헌의 0.4배였다(그 판정은 C4-4에 남는다).
명제: 방향 입력이 꺼진 렘에서 고리 위 봉우리 변위는 수 초까지 한 이동도의 확산을 따른다. 곧 조화 비
r_k(τ) = F_k/F_1이 τ에 선형인 지수 exp(−(k² − 1)Mτ/2)로 줄고, 속도 입력의 쓸기 exp(−(k² − 1)sτ²)로는 줄지 않는다.
생물 기준값: Chaudhuri et al. 2019 (Nat Neurosci 22:1512): 렘에서 해독 각의 제곱 변화가 시간에 선형으로 늘고(확산) 갱신은
시간 상관이 없으며, 논렘은 제곱 변화가 시간의 제곱으로 느는 쓸기다. M은 기준값(0.52–1.3 rad²/s) 대비 오차로 보고한다.
자료(원장): dandi-000056 (주), dandi-000939-extract (재현). 방법은 C4-4와 같고 교차 상관을 ±3 s로, τ 칸을
20–60–120–200–300–450–700 ms–1–1.5–2.1–3 s로 늘렸다.
판정(실행 전 고정):
- 000056: 렘 합계 ≥ 3600 s
- 도구: 000056 논렘에서 (C4-4와 같은 0.7 s 범위) 쓸기식 χ²/자유도 < 확산식 χ²/자유도 (문헌의 논렘 쓸기; 이 값은 C4-4에서
  이미 보았으므로 판정이 아니라 도구 검증이다)
- 재현(000939 렘): 확산식 χ²/자유도 ≤ 2 < 쓸기식 χ²/자유도
- 역증명(000056 렘): 확산식 χ²/자유도 ≤ 2 < 쓸기식 χ²/자유도
"""

import numpy as np

from research import c4_4_ring_diffusion as c44
from research import harness

HALF = 300
EDGES = np.array([0.02, 0.06, 0.12, 0.2, 0.3, 0.45, 0.7, 1.0, 1.5, 2.1, 3.0])


def collect(prepared):
    return [{"rem": c44.pair_sums(s, phi, *spans["rem"], half=HALF), "nrem": c44.pair_sums(s, phi, *spans["nrem"])}
            for s, phi, spans in prepared if len(spans["rem"][0])]


def main():
    rows56 = harness.registered("dandi-000056")
    rows39 = [r for r in harness.registered("dandi-000939-extract") if r["asset"].endswith(".npz")]
    harness.verify(rows56 + rows39)
    s56 = collect(x for x in map(c44.hd_056, rows56) if x)
    s39 = collect(x for x in map(c44.hd_939, rows39) if x)
    rem56 = c44.analyse(s56, "rem", np.random.default_rng(0), edges=EDGES)
    rem39 = c44.analyse(s39, "rem", np.random.default_rng(0), edges=EDGES)
    nrem56 = c44.analyse(s56, "nrem", np.random.default_rng(0))
    m = rem56["fits"]["diffusion"]["params"][2]
    fit = lambda a, name: a["fits"][name]["chi2_dof"]
    result = harness.record(
        "c4_5_ring_diffusion_long", "C4",
        "방향 입력이 꺼진 렘에서 고리 위 봉우리 변위는 수 초까지 한 이동도의 확산(리만 이차 비용)을 따르고, 속도 입력의 쓸기는 "
        "따르지 않는다",
        "Chaudhuri et al. 2019 Nat Neurosci 22:1512: 렘 확산(제곱 변화가 시간에 선형), 논렘 쓸기. 실측: DANDI:000056 (주), "
        "DANDI:000939 (재현)",
        {"rem_seconds": harness.check(rem56["seconds"], 3600),
         "instrument_nrem_sweep": harness.check(fit(nrem56, "diffusion") - fit(nrem56, "sweep"), low=0),
         "replication_000939": harness.check(min(fit(rem39, "sweep") - c44.CHI2, c44.CHI2 - fit(rem39, "diffusion")), low=0)},
        rows56 + rows39,
        proof=harness.reverse("이차 비용(리만 계량)의 확산", fit(rem56, "diffusion"), fit(rem56, "sweep"), c44.CHI2),
        dandi_000056_rem=rem56, dandi_000939_rem=rem39, dandi_000056_nrem=nrem56,
        msd_slope=m, msd_log_error_vs_literature=float(np.log(m / np.sqrt(np.prod(c44.LITERATURE)))))
    print(result["verdict"], "| M %.2f rad²/s (문헌 기하평균 대비 log 오차 %.2f)" % (m, np.log(m / np.sqrt(np.prod(c44.LITERATURE)))))
    for name, a in (("000056 렘", rem56), ("000939 렘", rem39), ("000056 논렘", nrem56)):
        print(name, "%.0f s" % a["seconds"], {k: (np.round(v["params"], 3).tolist(), round(v["chi2_dof"], 2))
                                              for k, v in a["fits"].items()})
        print("   r2", np.round(a["ratio"][0], 3), "±", np.round(a["se"][0], 3))


if __name__ == "__main__":
    main()
