"""Q-NPF-03 / F-01  카드 식의 기호 증명 (sympy).

축약계량   Phi(mu) = mu^2/f(mu) + p(mu)^2/2,   p(mu) = mu f'(mu)/f(mu),
잡음기하 분율  rho = (p^2/2)/Phi,   q = mu p'(mu)/p(mu)
에 대해

    d log Phi / d log mu  -  [ (2 - p)(1 - rho) + 2 rho q ]  ==  0

를 임의의 f 에 대해 기호적으로 확인한다. 또 순수 멱법칙 f = c mu^p0 에서
q = 0 이라 카드 식 (2-p)(1-rho) 가 정확함을, s2 = const 에서 값이 2 임을,
s2 ~ mu^2 에서 값이 0 임을 확인한다.  씨앗 무관(기호).
"""

from __future__ import annotations

import json
from pathlib import Path

import sympy as sp

HERE = Path(__file__).resolve().parent


def main() -> int:
    mu, c, p0 = sp.symbols("mu c p0", positive=True)
    f = sp.Function("f", positive=True)

    def build(fexpr):
        p = mu * sp.diff(fexpr, mu) / fexpr
        Phi = mu**2 / fexpr + p**2 / 2
        rho = (p**2 / 2) / Phi
        q = mu * sp.diff(p, mu) / p
        lhs = mu * sp.diff(Phi, mu) / Phi
        rhs = (2 - p) * (1 - rho) + 2 * rho * q
        return sp.simplify(sp.together(lhs - rhs)), p, rho, lhs

    checks = []

    # S1  임의 f 에 대한 정확식
    resid, _, _, _ = build(f(mu))
    checks.append({"name": "S1_general_f", "residual": str(resid),
                   "status": "PASS" if sp.simplify(resid) == 0 else "FAIL",
                   "note": "임의 상태함수 잡음 f(mu) 에서 dlogPhi/dlogmu = (2-p)(1-rho) + 2 rho q"})

    # S2  순수 멱법칙: q = 0, 카드 식이 정확
    fp = c * mu**p0
    resid2, p_pl, rho_pl, lhs_pl = build(fp)
    q_pl = sp.simplify(mu * sp.diff(p_pl, mu) / p_pl)
    card = sp.simplify(lhs_pl - (2 - p_pl) * (1 - rho_pl))
    checks.append({"name": "S2_powerlaw_q_zero", "residual": str(q_pl),
                   "status": "PASS" if q_pl == 0 else "FAIL",
                   "note": "f = c mu^p0 이면 q = 0"})
    checks.append({"name": "S2b_powerlaw_card_exact", "residual": str(card),
                   "status": "PASS" if card == 0 else "FAIL",
                   "note": "멱법칙에서 카드 식 (2-p)(1-rho) 가 정확"})

    # S3  극한 복원 1: 상태무관 잡음 -> 2
    lhs_add = sp.simplify(build(c)[3])
    checks.append({"name": "S3_additive_equals_2", "residual": str(sp.simplify(lhs_add - 2)),
                   "status": "PASS" if sp.simplify(lhs_add - 2) == 0 else "FAIL",
                   "note": "s2 = const (평균반응 전용 기하) -> dlogPhi/dlogmu = 2"})

    # S4  극한 복원 2: 일정 CV -> 0
    lhs_cv = sp.simplify(build(c * mu**2)[3])
    checks.append({"name": "S4_constCV_equals_0", "residual": str(sp.simplify(lhs_cv)),
                   "status": "PASS" if sp.simplify(lhs_cv) == 0 else "FAIL",
                   "note": "s2 = c mu^2 -> dlogPhi/dlogmu = 0 (계량이 gain 에 불변)"})

    # S5  chart 재척도 불변: o -> lam o  (mu -> lam mu, s2 -> lam^2 s2)
    lam, u = sp.symbols("lam u", positive=True)
    M = sp.Function("M", positive=True)(u)     # mu(u)
    V = sp.Function("V", positive=True)(u)     # s2(u)

    def phi_uv(M_, V_):
        m_ = sp.diff(sp.log(M_), u)
        s_ = sp.diff(sp.log(V_), u)
        p_ = s_ / m_
        return sp.simplify(M_**2 / V_ + p_**2 / 2)

    d5 = sp.simplify(phi_uv(M, V) - phi_uv(lam * M, lam**2 * V))
    checks.append({"name": "S5_chart_rescale", "residual": str(d5),
                   "status": "PASS" if d5 == 0 else "FAIL",
                   "note": "o -> lam o 아래 Phi = mu^2/s2 + p^2/2 불변 (두 항 모두 무차원)"})

    # S6  L, Y 도 불변: L = dlog mu, Y = dlog Phi
    L1 = sp.log(lam * M) - sp.log(lam * sp.Function("N", positive=True)(u))
    L2 = sp.log(M) - sp.log(sp.Function("N", positive=True)(u))
    d6 = sp.simplify(L1 - L2)
    checks.append({"name": "S6_contrast_rescale", "residual": str(d6),
                   "status": "PASS" if d6 == 0 else "FAIL",
                   "note": "대비 L = log mu_post - log mu_pre 와 Y = dlog Phi 도 chart 재척도 불변 -> Lambda 불변"})

    res = {"checks": checks,
           "status": "PASS" if all(c["status"] == "PASS" for c in checks) else "FAIL",
           "n_checks": len(checks), "engine": f"sympy {sp.__version__}"}
    (HERE / "result_symbolic.json").write_text(json.dumps(res, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(res, ensure_ascii=False, indent=2))
    return 0 if res["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
