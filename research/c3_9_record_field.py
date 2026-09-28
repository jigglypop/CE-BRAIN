"""C3-9: 흔적은 여러 봉우리를 가질 수 있는 기록장이다 — 짧은 이탈 뒤 덜 돌아온다 (전제 C3).

C3-8·C1-10을 본 뒤 세운 새 단계다. C3-8에서 적합에 쓰지 않은 관측(논렘 방향이 기록 자리를 5–15 s 벗어난 뒤 20 s의 정렬 R)을 모든 식이 과대
예측했고(실측 0.166 ± 0.017, 첫 성분 v3 0.239), C1-10에서 그것이 관측 잡음 탓이 아님을 보였다. 지금까지의 적분은 v3 기록장 m(ψ)의 첫 푸리에
성분(봉우리 하나 |h|·g(θ − arg h))만 썼다. 기록장 전체는 짧은 이탈이 새 자리에 남긴 작은 기록까지 들고 있으므로 덜 돌아와야 한다.
명제: 기록장 전체로 적분한 v3가 000056 표준 관측 10개(같은 구간 집단의 정렬 감쇠 5칸, 창 자기상관 5개)에 맞고, 그렇게 맞춘 식이 적합에 쓰지 않은
R(5–15)을 2 SE 안에서 예측한다. 첫 성분만 쓴 식(C3-8에 기록된 예측)은 그러지 못한다.
식: τ ḣ_k = −h_k + e^{ikθ} (k = 1..8, 기록장의 푸리에 계수), E(θ) = −A Σ_k c_k Re(h_k e^{−ikθ}), c_k = 2 I_k(β)e^{−β}(모인 기록이면 우물
e^{β(cos x − 1)}, β = 5.2), dθ = −D ∂E/∂θ dt + √(2D)dW, 잠들 때 어긋남 σ₀. 매개변수는 첫 성분 식과 같다(A, D, τ, σ₀, ρ). k = 8의 무게는 0.06%.
적분: `cefast.ring_field`(Leimkuhler–Matthews, 초당 걸음은 `ring.steps`). 적합은 복제 2개 → 8개(씨앗 1), 판정의 χ²은 씨앗 50의 복제 32개.
R의 예측은 C3-8과 같은 과정이다(실측 사건 길이 4번 복제, 사건마다 무작위 회전, 판정 ρ에 맞춘 폰미제스 해독 잡음). 실측 R과 SE는 C3-8 기록에서 읽는다.
생물 기준값: 원장 실측 관측(표준 10개, R(5–15)), Peyrache et al. 2015의 60° 봉우리 폭(β).
자료(원장): dandi-000056.
판정(실행 전 고정):
- 정확도: 판정 χ²/자유도 ≤ 2 (관측 10, 자유 A·D·τ·σ₀·ρ, 자유도 5)
- 예측: |R_기록장(5–15) − R_실측| ≤ 2 SE
- 역증명: |R_기록장 − R_실측|/SE ≤ 2 < |R_첫성분 − R_실측|/SE (C3-8 기록)
보고(판정 아님): R(15–45) 예측, 맞춘 매개변수.
"""

import json

import cefast
import numpy as np
from scipy.optimize import brentq
from scipy.special import i0e, i1e, ive

from research import c1_1_common_equation as c11
from research import c1_2_common_equation_onset as c12
from research import c1_5_common_equation_v2 as c15
from research import c3_2_trace_replication as c32
from research import c3_8_record_relocation as c38
from research import harness, ring
from research.c3_1_sleep_trace import CHI2

HARMONICS, Z = 8, 2.0
COEF = 2 * ive(np.arange(1, HARMONICS + 1), c11.BETA)


def trajectories(p, lengths, seed):
    return cefast.ring_field(np.asarray(lengths, np.int64), c11.SPAN, p["D"], p["A"], p["tau"], COEF, ring.steps(p), seed)


class Field:
    """Observed values of one data set (C1-5 cohort) and the record-field model on `replicas` copies of its events."""

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
    """R per excursion bin of the fitted record field, through the C3-8 pipeline."""
    rng = np.random.default_rng(seed)
    n = np.tile(lengths, c38.REPLICAS)
    theta = trajectories(p, n, seed)
    kappa = brentq(lambda k: i1e(k) / i0e(k) - rho, 0.05, 50)
    thetas = [row[:k] + rng.uniform(-np.pi, np.pi) + rng.vonmises(0, kappa, k) for row, k in zip(theta, n)]
    return c38.curve(thetas, np.zeros(len(thetas), int), rng, boot=False)["R"]


def main():
    c38r = json.loads((harness.RESULTS / "c3_8_record_relocation.json").read_text(encoding="utf-8"))["measured"]
    r_data, se = c38r["observed"]["R"][0], c38r["observed"]["se"][0]
    r_first = c38r["predicted"]["v3"][0]
    rows = harness.registered("dandi-000056")
    harness.verify(rows)
    sessions = [c32.session_056(r) for r in rows]
    base = c15.Data(c15.cohort(sessions), np.random.default_rng(0))
    lengths = np.array([len(theta) for f in sessions if f for _, _, theta in f])
    start = {"A": 5.0, "D": 0.4, "tau": 100.0, "sigma0": 1.0}
    coarse = ring.fit([Field(base, 2, 1)], (), ("A", "D", "tau", "sigma0"), {}, start, tol=(0.01, 0.05))
    fit = ring.fit([Field(base, 8, 1)], (), ("A", "D", "tau", "sigma0"), {}, coarse["params"], tol=(0.01, 0.05))
    p = fit["params"][0]
    chi2, rho, noise_free = Field(base, 32, 50).cost(p)
    judged = {"chi2": float(chi2), "chi2_dof": float(chi2 / (len(c15.INDEX) - 5)), "rho": float(rho),
              "prediction": (rho ** c12.POWER * noise_free)[c15.INDEX].tolist()}
    predicted = returns(p, rho, lengths, 11)
    err_field, err_first = abs(predicted[0] - r_data) / se, abs(r_first - r_data) / se
    result = harness.record(
        "c3_9_record_field", "C3",
        "기록장 전체로 적분한 v3가 000056 표준 관측 10개에 맞고, 적합에 쓰지 않은 짧은 이탈(5–15 s) 뒤 되돌아옴을 2 SE 안에서 예측한다: 흔적은 짧은 "
        "이탈이 남긴 기록까지 든 여러 봉우리의 기록장이다",
        "원장 실측 관측(표준 10개와 C3-8의 R(5–15)), Peyrache et al. 2015의 60° 봉우리 폭(β = 5.2). 실측: DANDI:000056",
        {"accuracy": harness.check(judged["chi2_dof"], high=CHI2),
         "prediction": harness.check(err_field, high=Z)},
        rows, proof=harness.reverse("기록장 전체(여러 봉우리)", err_field, err_first, Z),
        fit=fit, judged=judged, predicted_R=predicted, observed_R=c38r["observed"], first_mode_R=c38r["predicted"]["v3"],
        harmonics=HARMONICS)
    print(result["verdict"], {k: v["passed"] for k, v in result["checks"].items()}, result["reverse_proof"]["passed"])
    print("fit", {k: round(v, 3) for k, v in p.items()}, "judged chi2/dof %.2f rho %.3f" % (judged["chi2_dof"], rho))
    print("R predicted", np.round(predicted, 3).tolist(), "data", np.round(c38r["observed"]["R"], 3).tolist(),
          "first mode", np.round(c38r["predicted"]["v3"], 3).tolist(), "errors %.2f / %.2f SE" % (err_field, err_first))


if __name__ == "__main__":
    main()
