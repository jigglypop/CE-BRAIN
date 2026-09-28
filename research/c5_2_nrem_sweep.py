"""C5-2: 잠든 동안에도 방향 구동 F가 흐른다 — 논렘 쓸기가 짧은 이탈의 되돌아옴을 정한다 (전제 C5).

C3-8–C3-10·C1-10을 본 뒤 세운 새 단계다. 논렘 방향이 기록 자리(논렘 처음 30 s의 평균 방향)를 5–15 s 벗어난 뒤 20 s의 정렬 R을 모든 식이 과대 예측했고
(실측 0.166 ± 0.017, F 없는 v3 0.239), 관측 잡음·기록장의 여러 봉우리·세션 고정 끌개는 그 원인이 아니었다. 지금까지의 논렘 식은 방향 구동 F = 0이었다.
그런데 논렘 내부 방향은 1 s 안쪽에서 확산보다 쓸기(탄도)에 가깝다(C4-4: 000056 쓸기식 χ²/자유도 1.30 대 확산식 2.50; Chaudhuri et al. 2019).
명제: 논렘 식에 내부 각속도 ω(OU, 정상 표준편차 v는 C4-4의 000056 논렘 쓸기 s에서 옮긴 √(2s) = 3.19 rad/s, 상관 시간 τ_ω는 맞춤)를 더하면
000056 표준 관측 10개에 맞고, 적합에 쓰지 않은 R(5–15)을 2 SE 안에서 예측한다. F 없는 식(C3-8에 기록된 예측)은 그러지 못한다.
식: dθ = (−D ∂E/∂θ + ω)dt + √(2D)dW, τ_ω dω = −ω dt + v√(2τ_ω)dW′, τ ḣ = −h + e^{iθ}, E = −A|h|g(θ − arg h), β = 5.2, 잠들 때 어긋남 σ₀.
방향 구동 ω는 계량(이동도 D)과 다른 항이다(C5-1: 방향 성분은 연결체의 PB 경로에 따로 실린다).
적분: `cefast.ring_sweep`(θ는 Leimkuhler–Matthews, ω는 정확한 OU 걸음, 초당 걸음은 `ring.steps`). 적합은 복제 2개 → 8개(씨앗 1), 판정은 씨앗 50의
복제 32개. R의 예측은 C3-8과 같은 과정이고 실측 R과 SE는 C3-8 기록에서 읽는다.
생물 기준값: C4-4의 논렘 쓸기(교차 상관 조화, 20–700 ms; 독립 관측), Chaudhuri et al. 2019 Nat Neurosci 22:1512의 논렘 쓸기.
자료(원장): dandi-000056.
판정(실행 전 고정):
- 정확도: 판정 χ²/자유도 ≤ 2 (관측 10, 자유 A·D·τ·σ₀·τ_ω·ρ, 자유도 4)
- 예측: |R_쓸기(5–15) − R_실측| ≤ 2 SE
- 역증명: |R_쓸기 − R_실측|/SE ≤ 2 < |R_F없음 − R_실측|/SE (C3-8 기록)
보고(판정 아님): R(15–45) 예측, 맞춘 매개변수.
"""

import json

import cefast
import numpy as np
from scipy.optimize import brentq
from scipy.special import i0e, i1e

from research import c1_1_common_equation as c11
from research import c1_2_common_equation_onset as c12
from research import c1_5_common_equation_v2 as c15
from research import c3_2_trace_replication as c32
from research import c3_8_record_relocation as c38
from research import harness, ring
from research.c3_1_sleep_trace import CHI2

Z, FREE = 2.0, ("A", "D", "tau", "sigma0", "tau_w")
ring_bounds = {**c12.BOUNDS, "tau_w": (0.05, 100.0)}


def speed():
    """v = √(2s) from C4-4's 000056 NREM sweep fit (f_k = (k² − 1)·s·τ² ⇔ Gaussian ballistic displacement v·τ)."""
    r = json.loads((harness.RESULTS / "c4_4_ring_diffusion.json").read_text(encoding="utf-8"))["measured"]
    return float(np.sqrt(2 * r["dandi_000056"]["nrem"]["fits"]["sweep"]["params"][2]))


def trajectories(p, lengths, seed):
    return cefast.ring_sweep(np.asarray(lengths, np.int64), c11.SPAN, p["D"], p["A"], p["tau"], c11.BETA, p["speed"],
                             p["tau_w"], ring.steps(p), seed)


class Sweep:
    """Observed values of one data set (C1-5 cohort) and the ring-with-sweeps model on `replicas` copies of its events."""

    def __init__(self, base, replicas, seed):
        self.value, self.se, self.events, self.seed = base.value, base.se, base.events, seed
        self.lengths = np.full(base.events * replicas, c15.SPAN, np.int64)
        self.z = np.random.default_rng(seed + 100).standard_normal(len(self.lengths))

    def cost(self, p):
        offsets = p["sigma0"] * self.z
        theta = trajectories(p, self.lengths, self.seed)
        events = [{"pre": d, "theta": row[:c15.SPAN], "head": d, "session": 0} for row, d in zip(theta, offsets)]
        with np.errstate(invalid="ignore", divide="ignore"):
            noise_free = c11.observe(c11.statistics(events), np.ones((1, len(events))))[0]
        chi2, rho = c12.chi2(noise_free, self.value, self.se, c15.INDEX)
        return chi2, rho, noise_free


def returns(p, rho, lengths, seed):
    """R per excursion bin through the C3-8 pipeline."""
    rng = np.random.default_rng(seed)
    n = np.tile(lengths, c38.REPLICAS)
    theta = trajectories(p, n, seed)
    kappa = brentq(lambda k: i1e(k) / i0e(k) - rho, 0.05, 50)
    thetas = [row[:k] + rng.uniform(-np.pi, np.pi) + rng.vonmises(0, kappa, k) for row, k in zip(theta, n)]
    return c38.curve(thetas, np.zeros(len(thetas), int), rng, boot=False)["R"]


def main():
    c12.BOUNDS.update(ring_bounds)  # τ_ω의 범위를 적합 경계에 더한다
    c38r = json.loads((harness.RESULTS / "c3_8_record_relocation.json").read_text(encoding="utf-8"))["measured"]
    c17 = json.loads((harness.RESULTS / "c1_7_single_clock.json").read_text(encoding="utf-8"))["measured"]
    r_data, se, r_first = c38r["observed"]["R"][0], c38r["observed"]["se"][0], c38r["predicted"]["v3"][0]
    v = speed()
    rows = harness.registered("dandi-000056")
    harness.verify(rows)
    sessions = [c32.session_056(r) for r in rows]
    base = c15.Data(c15.cohort(sessions), np.random.default_rng(0))
    lengths = np.array([len(theta) for f in sessions if f for _, _, theta in f])
    start = {**c17["one_clock"]["fit"]["params"][0], "tau_w": 1.0}
    coarse = ring.fit([Sweep(base, 2, 1)], (), FREE, {"speed": v}, start, tol=(0.01, 0.05))
    fit = ring.fit([Sweep(base, 8, 1)], (), FREE, {"speed": v}, coarse["params"], tol=(0.01, 0.05))
    p = fit["params"][0]
    chi2, rho, noise_free = Sweep(base, 32, 50).cost(p)
    judged = {"chi2": float(chi2), "chi2_dof": float(chi2 / (len(c15.INDEX) - len(FREE) - 1)), "rho": float(rho),
              "prediction": (rho ** c12.POWER * noise_free)[c15.INDEX].tolist()}
    predicted = returns(p, rho, lengths, 11)
    err_sweep, err_first = abs(predicted[0] - r_data) / se, abs(r_first - r_data) / se
    result = harness.record(
        "c5_2_nrem_sweep", "C5",
        "논렘 식에 내부 각속도(방향 구동 F, 세기는 1 s 안쪽 쓸기에서 옮김)를 더하면 000056 표준 관측 10개에 맞고 적합에 쓰지 않은 짧은 이탈 뒤 되돌아옴을 "
        "2 SE 안에서 예측한다: 잠든 동안에도 계량과 다른 방향 구동이 흐른다",
        "C4-4의 000056 논렘 쓸기(교차 상관 조화, 독립 관측), Chaudhuri et al. 2019 Nat Neurosci 22:1512의 논렘 쓸기. 실측: DANDI:000056",
        {"accuracy": harness.check(judged["chi2_dof"], high=CHI2), "prediction": harness.check(err_sweep, high=Z)},
        rows, proof=harness.reverse("논렘 방향 구동 F", err_sweep, err_first, Z),
        speed=v, fit=fit, judged=judged, predicted_R=predicted, observed_R=c38r["observed"], no_drive_R=c38r["predicted"]["v3"])
    print(result["verdict"], {k: x["passed"] for k, x in result["checks"].items()}, result["reverse_proof"]["passed"])
    print("speed %.2f rad/s, fit" % v, {k: round(x, 3) for k, x in p.items()}, "judged %.2f rho %.3f" % (judged["chi2_dof"], rho))
    print("R sweep", np.round(predicted, 3).tolist(), "data", np.round(c38r["observed"]["R"], 3).tolist(),
          "no drive", np.round(c38r["predicted"]["v3"], 3).tolist(), "errors %.2f / %.2f SE" % (err_sweep, err_first))


if __name__ == "__main__":
    main()
