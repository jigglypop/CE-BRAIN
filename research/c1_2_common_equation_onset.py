"""C1-2: 잠들 때 어긋난 흔적 중심을 둔 공통 식이 두 자료를 맞춘다 (전제 C1).

C1-1을 본 뒤 세운 새 단계다. C1-1(공동 χ²/자유도 21)의 어긋남은 두 가지였다. (1) 모형은 갈등 창에서 상태를 머리 쪽으로
끌었지만(A_head 예측 0.099) 실측은 머리를 따르지 않았다(−0.034). (2) 첫 지연 칸의 정렬을 과대 예측했다(0.325 대 0.240):
흔적 중심이 잠드는 순간 이미 θ_pre에서 비켜나 있다는 뜻이다.
명제: C1-1의 공통 식에 흔적 중심의 잠들 때 어긋남 δ ~ 감싼 정규(σ₀)를 더하면(θ(0) = arg h(0) = θ_pre − δ), 한 매개변수
집합이 000056 논렘의 관측 14개를 함께 맞추고, 같은 식(머리 입력 없음)이 독립 자료 000939의 정렬·자기상관 11개도 맞춘다.
흔적 항(A = 0)을 빼면 000056을 맞추지 못한다.
식: C1-1과 같다(dθ = −D∂E/∂θ dt + √(2D) dW, τ_h ḣ = −h + e^{iθ}, E = −A|h|g(θ − arg h) − A_s g(θ − θ_head), β = 5.2).
자유 매개변수: 000056은 D, A, τ_h, A_s, σ₀, ρ (6), 000939는 머리 추적이 없어 A_s = 0으로 D, A, τ_h, σ₀, ρ (5).
어긋남 δ = σ₀·z는 사건마다 고정된 표준 정규 z(씨앗 2)로 만들어 적합이 매끄럽다.
생물 기준값: 원장 실측 관측(000056 14개, 000939 11개)과 Peyrache et al. 2015의 60° 봉우리 폭(β).
자료(원장): dandi-000056 (C1-1과 같은 사건·관측), dandi-000939-extract (첫 home_cage, C3-2와 같은 사건; 관측은 a 6칸, c 5개).
판정(실행 전 고정):
- 정확도(000056): 공동 χ²/자유도 ≤ 2 (관측 14, 매개변수 6)
- 재현(000939): χ²/자유도 ≤ 2 (관측 11, 매개변수 5)
- 역증명(000056): 공동 χ²/자유도 ≤ 2 < 흔적 없는 식(A = 0; D, A_s, σ₀, ρ)의 χ²/자유도
"""

import cefast
import numpy as np
from scipy.optimize import minimize, minimize_scalar

from research import c1_1_common_equation as c11
from research import c3_3_restoring as c33
from research import harness

OFFSET_SEED = 2
BOUNDS = {**c11.BOUNDS, "sigma0": (1e-3, 3.0)}
POWER = np.r_[np.ones(c11.K), 2 * np.ones(len(c11.DELTAS)), np.ones(3)]
FULL, SLEEP_ONLY = np.arange(14), np.arange(11)


def model(p, rel, lengths, z):
    """Noise-free observables when the trace centre sits δ = σ₀·z away from the measured θ_pre at sleep onset."""
    delta = p["sigma0"] * z
    theta = cefast.ring_trace(delta + rel, lengths, c11.SPAN, p["D"], p["A"], p["tau"], p["As"], c11.BETA,
                              c11.SUBSTEPS, c11.SEED)
    events = [{"pre": d, "theta": row[:n], "head": d + h, "session": 0}
              for row, n, h, d in zip(theta, lengths, rel, delta)]
    return c11.observe(c11.statistics(events), np.ones((1, len(events))))[0]


def chi2(noise_free, value, se, index):
    cost = lambda rho: np.sum(((value[index] - rho ** POWER[index] * noise_free[index]) / se[index]) ** 2)
    best = minimize_scalar(cost, bounds=(1e-3, 1.5), method="bounded")
    return float(best.fun), float(best.x)


def fit(value, se, rel, lengths, free, fixed, start, index, maxiter=400):
    z = np.random.default_rng(OFFSET_SEED).standard_normal(len(rel))

    def unpack(x):
        p = dict(fixed)
        p.update({k: float(np.clip(np.exp(v), *BOUNDS[k])) for k, v in zip(free, x)})
        return p

    def cost(x):
        p = unpack(x)
        if p["D"] * c11.BETA * (p["A"] + p["As"]) / c11.SUBSTEPS > c11.STABLE:
            return 1e12
        return chi2(model(p, rel, lengths, z), value, se, index)[0]

    x0 = np.log([start[k] for k in free])
    x = minimize(cost, x0, method="Nelder-Mead", options={
        "maxiter": maxiter, "xatol": 1e-3, "fatol": 1e-3, "initial_simplex": np.vstack([x0, x0 + 0.7 * np.eye(len(x0))])}).x
    p = unpack(x)
    noise_free = model(p, rel, lengths, z)
    c2, rho = chi2(noise_free, value, se, index)
    return {"params": p, "rho": rho, "chi2_dof": c2 / (len(index) - len(free) - 1),
            "prediction": (rho ** POWER * noise_free).tolist()}


def events_939(rows):
    """C3-2 events of the first home cage, without a head direction (no tracking during sleep)."""
    out = []
    for g, row in enumerate(rows):
        x = c33.session_939(row)
        out += [{"pre": e["pre"], "theta": e["theta"], "head": np.nan, "session": g} for e in (x["events"] if x else [])]
    return out


def main():
    rows56 = harness.registered("dandi-000056")
    rows39 = [r for r in harness.registered("dandi-000939-extract") if r["asset"].endswith(".npz")]
    harness.verify(rows56 + rows39)
    ev56 = c11.prepare([x["events"] for x in map(c33.session_056, rows56) if x])
    ev39 = events_939(rows39)
    value56, se56, _ = c11.measured(ev56, np.random.default_rng(0))
    value39, se39, _ = c11.measured(ev39, np.random.default_rng(0))
    rel56, len56 = c11.design(ev56)
    rel39, len39 = np.zeros(c11.REPLICAS * len(ev39)), c11.design(ev39)[1]
    start = {"D": 0.2, "A": 3.0, "tau": 800.0, "As": 0.3, "sigma0": 0.6}
    full = fit(value56, se56, rel56, len56, ("D", "A", "tau", "As", "sigma0"), {}, start, FULL)
    none = fit(value56, se56, rel56, len56, ("D", "As", "sigma0"), {"A": 0.0, "tau": 1.0}, start, FULL)
    rep = fit(value39, se39, rel39, len39, ("D", "A", "tau", "sigma0"), {"As": 0.0}, {**start, "tau": 200.0}, SLEEP_ONLY)
    result = harness.record(
        "c1_2_common_equation_onset", "C1",
        "잠들 때 어긋난 흔적 중심을 둔 공통 식 하나가 000056 논렘 관측 14개를 한 매개변수 집합으로 맞추고, 같은 식이 000939의 "
        "정렬·자기상관 11개도 맞추며, 흔적 항을 빼면 000056을 맞추지 못한다",
        "Peyrache et al. 2015: 60° 봉우리 폭(β). 실측 관측: DANDI:000056 (14), DANDI:000939 (11)",
        {"accuracy_000056": harness.check(full["chi2_dof"], high=c11.CHI2),
         "replication_000939": harness.check(rep["chi2_dof"], high=c11.CHI2)},
        rows56 + rows39, proof=harness.reverse("흔적 h의 우물", full["chi2_dof"], none["chi2_dof"], c11.CHI2),
        observed_000056=value56.tolist(), se_000056=se56.tolist(), observed_000939=value39[SLEEP_ONLY].tolist(),
        se_000939=se39[SLEEP_ONLY].tolist(), full=full, no_trace=none, replication=rep,
        mobility_vs_rem=float(full["params"]["D"] / (c11.REM_MSD / 2)))
    print(result["verdict"], "사건", len(ev56), len(ev39))
    for name, f, v, idx in (("공통 식", full, value56, FULL), ("흔적 없음", none, value56, FULL), ("000939", rep, value39, SLEEP_ONLY)):
        print(name, {k: round(x, 3) for k, x in f["params"].items()}, "ρ %.3f χ²/자유도 %.2f" % (f["rho"], f["chi2_dof"]))
        print("   관측", np.round(v[idx], 3).tolist(), "\n   예측", np.round(np.array(f["prediction"])[idx], 3).tolist())


if __name__ == "__main__":
    main()
