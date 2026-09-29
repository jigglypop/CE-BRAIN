"""C3-11: 기록 우물 밖일수록 흔적이 빨리 옮겨 간다 — 놀람 이득 (전제 C3).

C3-8부터 이어진 열린 문제를 푼다. 000056 논렘에서 내부 방향이 기록 자리를 5–15 s 벗어난 뒤의 되돌아옴 R(5–15)을 모든 식이
0.22–0.29로 과대 예측하고 실측은 0.166 ± 0.017이다. 관측 잡음 상관, 기록장 여러 봉우리, 세션 고정 끌개, 논렘 쓸기, 스파이크 수 잡음,
빈 방향 인공물은 원인이 아니었다(4.29–4.36). 새 후보는 델타 규칙·칼만 통합식 검토에서 왔다. 지금 식의 기록은 고정 이득으로 갱신된다.
고정 이득 필터는 관측이 믿음에서 크게 벗어나도 덜 고친다. 칼만 필터가 이를 벗어나는 길은 혁신(관측 − 예측)이 과정 잡음을 키워 이득을
올리는 것이다(변화점 칼만, Nassar et al. 2010·2012; Piray & Daw 2020; 이득이 결과와 무관하면 예측오차 의존 학습률을 못 낸다,
Gershman 2015).
식 (v3 + 놀람 이득, λ = 0이면 C1-7의 v3):
  dθ = −D ∂E/∂θ dt + √(2D) dW,   E = −A|h|·g(θ − arg h),   g(x) = e^{β(cos x − 1)}, β = 5.2
  τ ḣ = (1 + λ·u)(e^{iθ} − h),   u = 1 − g(θ − arg h)   (기록 우물 안 u ≈ 0, 밖 u ≈ 1)
시계 τ는 C1-7과 같이 C3-6의 깸 덮임 45.25 s로 고정한다(시계 하나). λ는 우물 밖에서 기록이 몇 배 더 빨리 옮겨 가는지다.
명제: 000056 논렘 관측 11개(C1-5 구간 집단의 정렬 감쇠 5칸·창 자기상관 5개, C3-8의 R(5–15))를 놀람 이득 식이 맞추고, λ = 0인 v3는 같은
관측을 맞추지 못한다. 적합에 쓰지 않은 R(15–45)도 놀람 이득 식이 2 SE 안에서 예측한다.
설계 이력(모형만, 실측을 새로 보지 않음): C1-7 해에서 λ = 0, 0.1, 0.2, 0.3, 0.5, 1이면 순열 보정 전 R(5–15)이 0.21, 0.18, 0.17, 0.16, 0.14,
0.08이다. 기제는 R(5–15)을 실측 수준으로 내릴 수 있지만 R(15–45)도 같이 내린다. 그래서 R(15–45)을 판정에 넣었다.
생물 기준값: 같은 식의 다른 관측(C3-6의 깸 덮임 τ 45.25 s)과 C3-8의 실측 R.
자료(원장): dandi-000056. 사건·관측·R의 정의는 C3-8과 같다(1 s 창 방향, 기록 자리 = 논렘 처음 30 s의 평균 방향, 5 s 끝 원형 평균이
90° 넘은 창의 연속, 벗어남이 끝난 창 20 s 뒤의 cos, 세션 안 순열 보정, 사건 부트스트랩).
모형: 표준 관측은 `ring.py`와 같은 Leimkuhler–Matthews 적분(`cefast.ring_observe_gain`), R은 C3-8과 같은 오일러 적분(`cefast.ring_trace_gain`,
이완율 × 간격 ≤ 0.05)에 사건마다 방향을 돌리고 ρ에 맞춘 폰미제스 해독 잡음을 더해 같은 과정으로 잰다. 두 핵심 모두 λ = 0에서 옛 핵심과
비트까지 같다. 적합: 표준 관측 복제 8개(씨앗 1) + R 복제 4개(씨앗 11, 순열 3번; 5–15 s 칸의 순열 널은 실측에서 0.001),
넬더–미드. 판정 χ²은 적합에 쓰지 않은 씨앗 50의 표준 관측 복제 32개 + R 복제 8개(순열 100번)로 두 식을 같은 난수로 잰다.
방법 검증(tests/test_c3_surprise_gain.py): 두 핵심은 λ = 0에서 옛 핵심과 비트까지 같고, R 계산은 C3-8 코드와 같은 값이며, 자료 크기의
합성 자료(λ = 0 참, λ = 0.3 참)에서 참이 아닌 λ의 χ²이 3.84 넘게 크다.
판정(실행 전 고정):
- 5–15 s 벗어남 ≥ 100
- 정확도: 놀람 이득 식의 판정 χ²/자유도 ≤ 2 (관측 11, 자유 A·D·σ₀·λ·ρ, 자유도 6)
- 놀람 이득 필요: 판정 χ²(v3) − 판정 χ²(놀람 이득) ≥ 3.84 (자유도 1, p = 0.05)
- 긴 이탈 예측: |R(15–45) − 예측| ≤ 2 SE (적합에 쓰지 않음)
- 역증명: 놀람 이득 식 ≤ 2 < v3(λ = 0, 같은 관측 11개에 맞춤)의 판정 χ²/자유도
보고(판정 아님): 시계를 푼 v3(τ 자유)의 적합, 벗어남 빈도(사건 1000 s당)의 실측과 예측, 우물 밖 유효 시계 τ/(1 + λ).
"""

import json

import cefast
import numpy as np
from scipy.optimize import brentq, minimize
from scipy.special import i0e, i1e

from research import c1_1_common_equation as c11
from research import c1_2_common_equation_onset as c12
from research import c1_5_common_equation_v2 as c15
from research import c3_2_trace_replication as c32
from research import c3_8_record_relocation as c38
from research import harness, ring
from research.c3_1_sleep_trace import CHI2, PERMUTATIONS

SHORT, LONG = 0, 1  # R 칸: 5–15 s, 15–45 s
NEEDED, Z, MIN_EXCURSIONS = 3.84, 2.0, 100
BOUNDS = {**c12.BOUNDS, "lam": (1e-3, 100.0)}
LOOSE = (0.01, 0.05)  # 최적화 허용치: 모형 표본 잡음 수준(C3-8과 같다)
COARSE, FINE, JUDGE = (2, 1, 1, 11, 2), (ring.FIT[0], ring.FIT[1], c38.REPLICAS, 11, 3), (*ring.JUDGE, 8, 50, PERMUTATIONS // 10)


def observables(p, offsets, lengths, seed):
    """`ring.observables` with the surprise gain λ."""
    s = cefast.ring_observe_gain(np.asarray(offsets, float), np.asarray(lengths, np.int64), p["D"], p["A"], p["tau"], c11.BETA,
                                 ring.steps(p), seed, ring.EDGES, ring.DELTAS, 1, ring.SCHEME, p["lam"])
    k, j = len(ring.EDGES) - 1, len(ring.DELTAS)
    with np.errstate(invalid="ignore", divide="ignore"):
        return np.r_[s[:k] / s[k:2 * k], s[2 * k:2 * k + j] / s[2 * k + j:], np.full(3, np.nan)]


class Standard(ring.Model):
    """The ten standard observables (C1-5 cohort) of the surprise-gain ring model."""

    def cost(self, p):
        noise_free = observables(p, p["sigma0"] * self.z, self.lengths, self.seed)
        chi2, rho = c12.chi2(noise_free, self.value, self.se, c15.INDEX)
        return chi2, rho, noise_free


def excursions(th, centre):
    """The (run length, cos) pairs of `c3_8.excursions`, vectorised."""
    th = th[c38.EARLY:]
    if len(th) < c38.SMOOTH:
        return np.zeros(0, int), np.zeros(0)
    c = np.cumsum(np.r_[0, np.exp(1j * th)])
    away = np.abs(np.angle((c[c38.SMOOTH:] - c[:-c38.SMOOTH]) * np.exp(-1j * centre))) > c38.AWAY
    d = np.diff(np.r_[0, away.astype(np.int8), 0])
    start, end = np.flatnonzero(d == 1), np.flatnonzero(d == -1) - 1
    k = end + c38.SMOOTH - 1
    ok = k + c38.AHEAD < len(th)
    return (end - start + 1)[ok], np.cos(th[k[ok] + c38.AHEAD] - centre)


def sums(thetas, centres):
    """Per bin: sum of cos and count of excursions over all events (bins × 2)."""
    out = np.zeros((len(c38.BINS), 2))
    for th, c in zip(thetas, centres):
        run, a = excursions(th, c)
        for b, (lo, hi) in enumerate(c38.BINS):
            m = (run >= lo) & (run < hi)
            out[b] += (a[m].sum(), m.sum())
    return out


def curve(thetas, rng, permutations):
    """`c3_8.curve(thetas, one group, rng, boot=False)` with `permutations` shuffles; the same numbers at 100."""
    thetas = [th for th in thetas if len(th) >= c38.EARLY + c38.SMOOTH + c38.AHEAD]
    centres = c38.early(thetas)
    total = sums(thetas, centres)
    null = np.zeros(len(c38.BINS))
    at = np.arange(len(thetas))
    for _ in range(permutations):
        n = sums(thetas, centres[rng.permutation(at)])
        null += n[:, 0] / np.maximum(n[:, 1], 1) / permutations
    return total[:, 0] / np.maximum(total[:, 1], 1) - null, total[:, 1].astype(int)


def relocation(p, rho, lengths, seed, replicas, permutations):
    """R per bin and excursion counts of the model on the data's event lengths (`c3_8.model` with λ)."""
    rng = np.random.default_rng(seed)
    n = np.tile(lengths, replicas).astype(np.int64)
    steps = int(max(100, np.ceil(p["D"] * c11.BETA * p["A"] / 0.05)))
    theta = cefast.ring_trace_gain(np.zeros(len(n)), n, c11.SPAN, p["D"], p["A"], p["tau"], 0.0, c11.BETA, steps, seed, p["lam"])
    kappa = brentq(lambda k: i1e(k) / i0e(k) - rho, 0.05, 50)
    turn = rng.uniform(-np.pi, np.pi, len(n))
    thetas = [row[:k] + t + rng.vonmises(0, kappa, k) for row, k, t in zip(theta, n, turn)]
    return curve(thetas, rng, permutations)


class Joint:
    """χ² of the eleven observables: the ten standard ones at their best ρ, plus R(5–15) under that ρ."""

    def __init__(self, base, lengths, r, se, design):
        replicas, seed, self.r_replicas, self.r_seed, self.permutations = design
        self.standard, self.lengths, self.r, self.se = Standard(base, replicas, seed), lengths, r, se

    def cost(self, p):
        chi2, rho, noise_free = self.standard.cost(p)
        r, count = relocation(p, rho, self.lengths, self.r_seed, self.r_replicas, self.permutations)
        return chi2 + ((self.r[SHORT] - r[SHORT]) / self.se[SHORT]) ** 2, rho, noise_free, r, count


def fit(joint, free, fixed, start, maxiter=2000, restarts=4, tol=LOOSE):
    """Nelder–Mead over log parameters with simplex restarts until χ² stops falling by 0.1 (as `ring.fit`)."""
    def unpack(x):
        return {**fixed, **{k: float(np.clip(np.exp(v), *BOUNDS[k])) for k, v in zip(free, x)}}

    cost = lambda x: joint.cost(unpack(x))[0]
    x = np.log([start[k] for k in free])
    best = cost(x)
    for _ in range(restarts):
        r = minimize(cost, x, method="Nelder-Mead", options={
            "maxiter": maxiter, "xatol": tol[0], "fatol": tol[1], "initial_simplex": np.vstack([x, x + 0.7 * np.eye(len(x))])})
        if best - r.fun < 0.1:
            x = r.x if r.fun < best else x
            break
        x, best = r.x, r.fun
    return unpack(x)


def fit_joint(base, lengths, r, se, free, fixed, start):
    """Coarse (2 standard replicas, 1 R replica) then fine (8 and 4)."""
    coarse = fit(Joint(base, lengths, r, se, COARSE), free, fixed, start)
    return fit(Joint(base, lengths, r, se, FINE), free, fixed, coarse)


def judged(base, lengths, r, se, p, n_free):
    """Fresh-noise χ² of the eleven observables and the model's R and counts (seed 50, not used in fitting)."""
    chi2, rho, noise_free, pred, count = Joint(base, lengths, r, se, JUDGE).cost(p)
    return {"params": p, "chi2": float(chi2), "chi2_dof": float(chi2 / (len(c15.INDEX) + 1 - n_free - 1)), "rho": float(rho),
            "R": pred.tolist(), "count": count.tolist(), "replicas": JUDGE[2]}


def main():
    c17 = json.loads((harness.RESULTS / "c1_7_single_clock.json").read_text(encoding="utf-8"))["measured"]
    v3 = c17["one_clock"]["fit"]["params"][0]
    rows = harness.registered("dandi-000056")
    harness.verify(rows)
    sessions = [c32.session_056(row) for row in rows]
    thetas = [theta for f in sessions if f for _, _, theta in f]
    group = np.array([g for g, f in enumerate(sessions) if f for _ in f])
    lengths = np.array([len(t) for t in thetas])
    base = c15.Data(c15.cohort(sessions), np.random.default_rng(0))
    data = c38.curve(thetas, group, np.random.default_rng(0))
    r, se = np.array(data["R"]), np.array(data["se"])
    fixed = {"tau": v3["tau"]}
    start = {"A": v3["A"], "D": v3["D"], "sigma0": v3["sigma0"]}
    p_v3 = fit_joint(base, lengths, r, se, ("A", "D", "sigma0"), {**fixed, "lam": 0.0}, start)
    p_gain = fit_joint(base, lengths, r, se, ("A", "D", "sigma0", "lam"), fixed, {**start, "lam": 0.3})
    p_free = fit_joint(base, lengths, r, se, ("A", "D", "sigma0", "tau"), {"lam": 0.0}, {**start, **fixed})
    j_v3, j_gain, j_free = (judged(base, lengths, r, se, p, n) for p, n in ((p_v3, 3), (p_gain, 4), (p_free, 4)))
    long_err = abs(r[LONG] - j_gain["R"][LONG]) / se[LONG]
    seconds = float(np.sum(np.maximum(lengths - c38.EARLY, 0)))
    rate = {"data_per_1000s": (np.array(data["count"]) / seconds * 1000).tolist(),
            "model_per_1000s": (np.array(j_gain["count"]) / (seconds * JUDGE[2]) * 1000).tolist()}
    result = harness.record(
        "c3_11_surprise_gain", "C3",
        "논렘의 흔적 기록은 상태가 기록 우물 밖에 있을수록 빨리 옮겨 간다(놀람 이득): 이 한 항이 표준 관측 10개와 짧은 이탈 뒤 되돌아옴을 "
        "함께 맞추고, 고정 이득 v3는 맞추지 못하며, 적합에 쓰지 않은 긴 이탈 뒤 되돌아옴도 예측한다",
        "같은 식의 다른 관측: C3-6의 깸 덮임 τ 45.25 s, C3-8의 R. 이득의 기제: 혁신 구동 칼만(Nassar et al. 2010·2012, "
        "Piray & Daw 2020, Gershman 2015). 실측: DANDI:000056",
        {"excursions": harness.check(data["count"][SHORT], MIN_EXCURSIONS),
         "accuracy": harness.check(j_gain["chi2_dof"], high=CHI2),
         "surprise_needed": harness.check(j_v3["chi2"] - j_gain["chi2"], low=NEEDED),
         "long_excursions": harness.check(long_err, high=Z)},
        rows, proof=harness.reverse("놀람 이득 λ", j_gain["chi2_dof"], j_v3["chi2_dof"], CHI2),
        observed=data, v3=j_v3, surprise=j_gain, free_clock=j_free, excursion_rate=rate,
        clock_outside_well=float(p_gain["tau"] / (1 + p_gain["lam"])))
    print(result["verdict"], {k: v["passed"] for k, v in result["checks"].items()}, result["reverse_proof"]["passed"])
    print("data R", np.round(r, 3).tolist(), "se", np.round(se, 3).tolist(), "count", data["count"])
    for name, j in (("v3", j_v3), ("surprise", j_gain), ("free clock", j_free)):
        print(name, {k: round(v, 3) for k, v in j["params"].items()}, "χ²/dof %.2f (χ² %.1f)" % (j["chi2_dof"], j["chi2"]),
              "R", np.round(j["R"], 3).tolist())
    print("rate", {k: np.round(v, 2).tolist() for k, v in rate.items()})


if __name__ == "__main__":
    main()
