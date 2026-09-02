# -*- coding: utf-8 -*-
"""A2. 참 세계에서 (a) chart 영점(affine offset) 의존, (b) 조건부 Sigma vs 시행주변 분산,
(c) (21.47) 세 채널 분리. 모두 무잡음 지상진실로 계산해 표본잡음을 배제한다."""
from __future__ import annotations
import json, sys, numpy as np
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import calib_power as C

HERE = Path(__file__).resolve().parent
K = int(round(C.T_END / C.BIN))

def truth_with(worldp, mom, tag):
    """mom(lam,dlam,a) -> (mu,s2).  카드 truth() 와 같은 집계."""
    num = den = 0.0; ps=[]; rs=[]; Rs=[]; Ls=[]; nb=0
    for e in worldp:
        a = C.exact_chart(e["lam"][("early","A")])
        for cue in ("A","B"):
            mu_e, s2_e = mom(e["lam"][("early",cue)], e["dlam"][("early",cue)], a)
            mu_l, s2_l = mom(e["lam"][("late",cue)],  e["dlam"][("late",cue)],  a)
            if np.any(mu_e<=0) or np.any(mu_l<=0) or np.any(s2_e<=0) or np.any(s2_l<=0):
                continue
            keep = C.select_bins(mu_e, s2_e, mu_l, K)
            if keep.sum() < 4: continue
            X, Y = C.xy(mu_e, s2_e, mu_l, s2_l, keep)
            if X is None: continue
            num += float(np.sum(X[keep]*Y[keep])); den += float(np.sum(X[keep]**2))
            p = C.fit_p(mu_e, s2_e, keep); t = C.phi_terms(mu_e, s2_e, p)
            ps.append(float(p)); rs.append(float(np.mean(t["rho"][keep])))
            Rs.append(float(np.mean(t["R"][keep])))
            Ls.append(float(np.mean((np.log(mu_l)-np.log(mu_e))[keep]))); nb += int(keep.sum())
    if not ps or abs(den)<1e-12:
        return {"tag":tag,"lam_true":None,"note":"게이트 이전에 자료 없음(0/0)","bins":nb,"pairs":len(ps)}
    R = float(np.mean(Rs))
    return {"tag":tag,"lam_true":round(num/den,4),"p":round(float(np.mean(ps)),4),
            "rho":round(float(np.mean(rs)),4),"R":round(R,4),"Gamma":round(2.0-R,4),
            "logalpha":round(float(np.mean(Ls)),4),"bins":nb,"pairs":len(ps)}

def mom_marg(lam,dlam,a):      # 카드 동결: 시행주변 분산 (공유 gain + 구동 jitter 포함)
    return C.exact_moments(lam,dlam,a)
def mom_cond(lam,dlam,a):      # (21.42) 의 Sigma(z): 상태 고정 조건부 방출잡음만 = Poisson
    mu = a@lam
    return mu, (a**2)@lam
def mom_off(c):                # chart 영점 이동 w -> w + c (분산 불변)
    def f(lam,dlam,a):
        mu,s2 = C.exact_moments(lam,dlam,a); return mu+c, s2
    return f

out={"note":"adversary A2","seed":C.SEED,"checks":[]}
wp = C.prepare_world("true", C.SEED+0)

base = truth_with(wp, mom_marg, "카드 동결(주변 분산)")
out["checks"].append({"name":"A2_baseline","row":base})
scale = float(np.mean([ (C.exact_chart(e["lam"][("early","A")])@e["lam"][("early","A")]).mean() for e in wp]))
out["chart_mean_level"] = round(scale,5)

# (a) 영점 이동
rows=[]
for frac in (-0.5,-0.25,-0.1,0.0,0.1,0.25,0.5,1.0,2.0):
    rows.append(truth_with(wp, mom_off(frac*scale), "offset=%+.2f*mean"%frac))
out["checks"].append({"name":"A2a_chart_offset_dF/F_zero_point","rows":rows,
  "verdict":"Phi=mu^2/s2 는 곱셈 재척도에만 불변이고 영점 이동에는 전혀 불변이 아니다. dF/F 처럼 영점이 전처리(F0 창) 선택인 관측에서 Gamma·Lambda 가 이동한다."})

# (b) 조건부 Sigma
out["checks"].append({"name":"A2b_conditional_Sigma_of_21.42","row":truth_with(wp, mom_cond, "조건부 Sigma (Poisson 만)"),
  "verdict":"(21.42) 의 Sigma 는 상태 고정 조건부 출력공분산이다. 시행공유 gain·구동 jitter 는 상태변동이라 21장 §5.2 가 금한 치환(조건부 식에 주변 모멘트)이다. 이 읽기에서는 p, Gamma 가 다른 값이 된다."})

# (c) 채널 분리 — (21.47) 세 줄
rows=[]
for tag,(dw,gn,vf) in {"효능만 dW":(C.LEARN_DW,1.0,1.0),
                       "내재 gain 만":(0.0,C.LEARN_GAIN,1.0),
                       "전도속도만 v":(0.0,1.0,C.LEARN_VFAC),
                       "셋 다(카드)":(C.LEARN_DW,C.LEARN_GAIN,C.LEARN_VFAC)}.items():
    C.LEARN_DW, C.LEARN_GAIN, C.LEARN_VFAC = dw, gn, vf
    wpx = C.prepare_world("true", C.SEED+0)
    rows.append(truth_with(wpx, mom_marg, tag))
C.LEARN_DW, C.LEARN_GAIN, C.LEARN_VFAC = 0.18, 1.30, 1.25
out["checks"].append({"name":"A2c_channel_isolation_21.47","rows":rows,
  "verdict":"카드 recovers 넷째 극한('지연 채널은 평균궤적으로만 Phi 를 움직인다')의 증거로 인용된 lam_true=0.988 은 세 채널을 동시에 켠 세계의 값이다. 지연 채널 단독 세계를 실제로 돌려야 그 극한이 검사된다."})

(HERE/"a2_worlds.json").write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding="utf-8")
print(json.dumps(out,ensure_ascii=False,indent=2))
