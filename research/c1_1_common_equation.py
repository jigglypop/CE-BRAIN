"""C1-1: 공통 식 하나가 흔적·자기상관·선택을 함께 맞춘다 (전제 C1).

명제: 공통 식 ẋ = −G⁻¹∇E(x; h) + F, τ_h ḣ = −h + x를 머리방향 고리 위 상태 θ 하나로 쓴 식이, 한 매개변수 집합으로
000056 논렘의 세 관측군을 함께 맞춘다: (1) 잠들기 전 방향과의 정렬 감쇠 a(t) (C3), (2) 1 s 창 방향의 자기상관 c(Δ) (C3-3),
(3) 과거와 현재 머리 방향이 90° 이상 갈등하는 창의 정렬 A_pre·A_head·A_mid (C8). 흔적 항을 빼면 맞추지 못한다.
식 (θ(0) = θ_pre, h(0) = e^{iθ_pre}):
  dθ = −D ∂E/∂θ dt + √(2D) dW          (D = T·G⁻¹: 고리 방향 이동도, 계량)
  τ_h ḣ = −h + e^{iθ}                  (흔적: 상태의 저역 통과)
  E = −A|h|·g(θ − arg h) − A_s·g(θ − θ_head),  g(x) = e^{β(cos x − 1)}   (흔적 우물 + 잠든 머리 방향의 현재 입력)
  관측: 창 방향 = 창 안 θ의 원형 평균 + 해독 잡음(E cos 잡음 = ρ): a, A는 ρ배, c는 ρ²배.
고정값: β = 5.2 — 우물 모양을 봉우리 모양으로 둔다. Peyrache et al. 2015의 60° 폭 봉우리: e^{β(cos 30° − 1)} = 1/2.
자유 매개변수 5개: D, A, τ_h, A_s, ρ. 역증명의 대안은 흔적 항이 없는 식(A = 0; D, A_s, ρ).
생물 기준값: 원장 실측 관측 14개(아래)와 Peyrache et al. 2015의 봉우리 폭. 적합된 D는 렘 이동도(C4-5, M/2)와 견줘 보고한다.
자료(원장): dandi-000056. 사건·창은 C3-3과 같고, 머리가 창의 절반 이상에서 추적된 사건만 쓴다. 사건의 머리 방향은 추적된 창의
원형 평균이다. 관측: a는 지연 칸 6개(세션 안 순열 보정), c는 Δ = 1·3·10·30·100 s(세션 평균 벡터의 제곱을 뺀 값), A_x는 갈등
사건(|θ_head − θ_pre| ≥ 90°) 창들의 cos 평균. 오차는 사건 부트스트랩 1000번. 모형은 같은 사건 설계(머리 차, 길이)를 2번씩 복제해
Rust 핵심(cefast.ring_trace, 사건마다 고정 난수열)으로 5 ms 간격(창당 200단계)에 적분하고, 강성 D·β·(A + A_s)·dt > 0.5인
영역은 적분이 불안정하므로 적합에서 제외한다. 적합은 log 매개변수의 Nelder–Mead(초기 단순체 ±0.7).
판정(실행 전 고정):
- 사건 ≥ 200, 갈등 사건 ≥ 30
- 정확도: 공동 χ²/자유도 ≤ 2 (관측 14, 매개변수 5)
- 역증명: 공동 χ²/자유도 ≤ 2 < 흔적 없는 식의 χ²/자유도 (관측 14, 매개변수 3)
"""

import cefast
import numpy as np
from scipy.optimize import minimize, minimize_scalar

from research import c3_3_restoring as c33
from research import harness
from research.c3_1_sleep_trace import BOOTSTRAP, CHI2, LAGS, PERMUTATIONS

BETA, SPAN, REPLICAS, SEED, SUBSTEPS, STABLE = 5.2, 480, 2, 1, 200, 0.5
DELTAS = np.array([1, 3, 10, 30, 100])
CONFLICT, TRACKED, K = np.pi / 2, 0.5, len(LAGS) - 1
BOUNDS = {"D": (0.005, 20.0), "A": (1e-3, 50.0), "tau": (1.0, 1e5), "As": (1e-3, 50.0)}
REM_MSD = 0.24  # C4-5, 000056 렘 확산식 M (rad²/s); 이동도 D = M/2


def prepare(sessions):
    """Events with the head tracked in at least half of their windows, with the event's mean head direction."""
    out = []
    for g, events in enumerate(sessions):
        for e in events:
            ok = np.isfinite(e["head"])
            if ok.mean() >= TRACKED:
                out.append({"pre": e["pre"], "theta": e["theta"], "session": g,
                            "head": float(np.angle(np.exp(1j * e["head"][ok]).mean()))})
    return out


def statistics(events):
    """Per-event sums behind every observable."""
    E = len(events)
    st = {k: np.zeros((E, K)) for k in ("C", "S", "N")}
    st.update(Z=np.zeros((E, len(DELTAS)), complex), M=np.zeros((E, len(DELTAS))), X=np.zeros((E, 3)), W=np.zeros(E))
    st["pre"] = np.array([e["pre"] for e in events])
    st["session"] = np.array([e["session"] for e in events])
    for i, e in enumerate(events):
        u = np.exp(1j * e["theta"])
        b = np.digitize(np.arange(len(u)) + 0.5, LAGS) - 1
        st["C"][i], st["S"][i] = np.bincount(b, u.real, K), np.bincount(b, u.imag, K)
        st["N"][i] = np.bincount(b, minlength=K)
        for j, d in enumerate(DELTAS):
            if len(u) > d:
                st["Z"][i, j], st["M"][i, j] = (u[d:] * np.conj(u[:-d])).sum(), len(u) - d
        sep = np.angle(np.exp(1j * (e["head"] - e["pre"])))
        if abs(sep) >= CONFLICT:
            st["X"][i] = [np.cos(e["theta"] - x).sum() for x in (e["pre"], e["head"], e["pre"] + sep / 2)]
            st["W"][i] = len(u)
    return st


def observe(st, w, null=0.0, baseline=None):
    """The 14 observables (a × 6, c × 5, A_pre/A_head/A_mid) for event weights w (rows)."""
    a = ((w * np.cos(st["pre"])) @ st["C"] + (w * np.sin(st["pre"])) @ st["S"]) / (w @ st["N"]) - null
    base = 0.0 if baseline is None else w @ (st["M"] * baseline[:, None])
    c = ((w @ st["Z"]).real - base) / (w @ st["M"])
    A = (w @ st["X"]) / (w @ st["W"])[:, None]
    return np.concatenate([a, c, A], 1)


def measured(events, rng):
    """Observed values and their event-bootstrap standard errors."""
    st = statistics(events)
    group = st["session"]
    u = {g: np.concatenate([np.exp(1j * e["theta"]) for e in events if e["session"] == g]).mean() for g in np.unique(group)}
    baseline = np.array([abs(u[g]) ** 2 for g in group])
    shuffled = np.tile(st["pre"], (PERMUTATIONS, 1))
    for g in np.unique(group):
        at = np.flatnonzero(group == g)
        shuffled[:, at] = rng.permuted(shuffled[:, at], axis=1)
    null = ((np.cos(shuffled) @ st["C"] + np.sin(shuffled) @ st["S"]) / st["N"].sum(0)).mean(0)
    one = np.ones((1, len(events)))
    value = observe(st, one, null, baseline)[0]
    weight = np.stack([np.bincount(rng.integers(0, len(events), len(events)), minlength=len(events))
                       for _ in range(BOOTSTRAP)]).astype(float)
    return value, observe(st, weight, null, baseline).std(0), st


def design(events):
    heads = np.array([np.angle(np.exp(1j * (e["head"] - e["pre"]))) for e in events])
    lengths = np.array([len(e["theta"]) for e in events], np.int64)
    return np.tile(heads, REPLICAS), np.tile(lengths, REPLICAS)


def model(p, heads, lengths):
    """Noise-free observables of the common equation (θ_pre = 0) for one parameter set."""
    theta = cefast.ring_trace(heads, lengths, SPAN, p["D"], p["A"], p["tau"], p["As"], BETA, SUBSTEPS, SEED)
    events = [{"pre": 0.0, "theta": row[:n], "head": h, "session": 0} for row, n, h in zip(theta, lengths, heads)]
    return observe(statistics(events), np.ones((1, len(events))))[0]


def chi2(noise_free, value, se):
    """χ² after the best decoding-noise factor ρ (a and A scale by ρ, c by ρ²)."""
    power = np.r_[np.ones(K), 2 * np.ones(len(DELTAS)), np.ones(3)]
    cost = lambda rho: np.sum(((value - rho ** power * noise_free) / se) ** 2)
    best = minimize_scalar(cost, bounds=(1e-3, 1.5), method="bounded")
    return float(best.fun), float(best.x)


def fit(value, se, heads, lengths, free, fixed, start, maxiter=300):
    """Nelder–Mead over the log of the free parameters; returns parameters, ρ and χ²/dof."""
    def unpack(x):
        p = dict(fixed)
        p.update({k: float(np.clip(np.exp(v), *BOUNDS[k])) for k, v in zip(free, x)})
        return p

    def cost(x):
        p = unpack(x)
        if p["D"] * BETA * (p["A"] + p["As"]) / SUBSTEPS > STABLE:  # 오일러 적분이 불안정한 영역
            return 1e12
        return chi2(model(p, heads, lengths), value, se)[0]

    x0 = np.log([start[k] for k in free])
    simplex = np.vstack([x0, x0 + 0.7 * np.eye(len(x0))])
    x = minimize(cost, x0, method="Nelder-Mead",
                 options={"maxiter": maxiter, "xatol": 1e-3, "fatol": 1e-3, "initial_simplex": simplex}).x
    p = unpack(x)
    noise_free = model(p, heads, lengths)
    c2, rho = chi2(noise_free, value, se)
    return {"params": p, "rho": rho, "chi2_dof": c2 / (len(value) - len(free) - 1), "prediction": noise_free.tolist()}


def main():
    rows = harness.registered("dandi-000056")
    harness.verify(rows)
    events = prepare([x["events"] for x in map(c33.session_056, rows) if x])
    value, se, st = measured(events, np.random.default_rng(0))
    heads, lengths = design(events)
    full = fit(value, se, heads, lengths, ("D", "A", "tau", "As"), {},
               {"D": 0.3, "A": 2.0, "tau": 300.0, "As": 1.0})
    none = fit(value, se, heads, lengths, ("D", "As"), {"A": 0.0, "tau": 1.0},
               {"D": 0.3, "As": 1.0})
    conflict = int((st["W"] > 0).sum())
    result = harness.record(
        "c1_1_common_equation", "C1",
        "공통 식(고리 이동도 D의 리만 확산, 흔적 h의 우물, 현재 머리 입력의 우물) 하나가 한 매개변수 집합으로 000056 논렘의 "
        "정렬 감쇠·창 자기상관·갈등 창 정렬을 함께 맞추고, 흔적 항을 빼면 맞추지 못한다",
        "Peyrache et al. 2015 Nat Neurosci 18:569: 60° 폭 봉우리(우물 폭 β = 5.2). 실측 관측 14개: DANDI:000056",
        {"events": harness.check(len(events), 200), "conflict_events": harness.check(conflict, 30),
         "accuracy": harness.check(full["chi2_dof"], high=CHI2)},
        rows, proof=harness.reverse("흔적 h의 우물", full["chi2_dof"], none["chi2_dof"], CHI2),
        observed=value.tolist(), se=se.tolist(), full=full, no_trace=none,
        mobility_vs_rem=float(full["params"]["D"] / (REM_MSD / 2)))
    print(result["verdict"], "사건", len(events), "갈등", conflict)
    print("관측 ", np.round(value, 3).tolist(), "\n오차 ", np.round(se, 3).tolist())
    for name, f in (("공통 식", full), ("흔적 없음", none)):
        power = np.r_[np.ones(K), 2 * np.ones(len(DELTAS)), np.ones(3)]
        print(name, {k: round(v, 3) for k, v in f["params"].items()}, "ρ %.3f χ²/자유도 %.2f" % (f["rho"], f["chi2_dof"]))
        print("   예측", np.round(f["rho"] ** power * np.array(f["prediction"]), 3).tolist())


if __name__ == "__main__":
    main()
