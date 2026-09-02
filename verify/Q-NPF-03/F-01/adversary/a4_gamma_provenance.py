# -*- coding: utf-8 -*-
"""A4. Gamma = 1.46 의 출처. 보정 회로의 무잡음 지상진실 p 가 무엇에 의존하는가.
지표 chart 는 세포 '평균'(a = S/|S|) 이라 Poisson 항 (a^2)@lam ~ mu/|S| 이고
공유 gain 항은 nup*mu^2 이라 |S| 에 무관하다. 따라서 p 는 세포수·발화율·NU_G·SIG_D 에 함께 의존한다.
이 손잡이 중 문헌으로 고정된 것이 없으면 Gamma 는 예측이 아니라 저자 선택의 되읽기다."""
from __future__ import annotations
import json, sys, numpy as np
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import calib_power as C
HERE=Path(__file__).resolve().parent
K=int(round(C.T_END/C.BIN))

def gt(wp):
    num=den=0.0; ps=[];rs=[];Rs=[]
    for e in wp:
        a=C.exact_chart(e["lam"][("early","A")])
        for cue in ("A","B"):
            mu_e,s2_e=C.exact_moments(e["lam"][("early",cue)],e["dlam"][("early",cue)],a)
            mu_l,s2_l=C.exact_moments(e["lam"][("late",cue)],e["dlam"][("late",cue)],a)
            keep=C.select_bins(mu_e,s2_e,mu_l,K)
            if keep.sum()<4: continue
            X,Y=C.xy(mu_e,s2_e,mu_l,s2_l,keep)
            if X is None: continue
            num+=float(np.sum(X[keep]*Y[keep])); den+=float(np.sum(X[keep]**2))
            p=C.fit_p(mu_e,s2_e,keep); t=C.phi_terms(mu_e,s2_e,p)
            ps.append(float(p)); rs.append(float(np.mean(t["rho"][keep]))); Rs.append(float(np.mean(t["R"][keep])))
    if not ps: return None
    R=float(np.mean(Rs))
    return {"p":round(float(np.mean(ps)),3),"rho":round(float(np.mean(rs)),3),
            "R":round(R,3),"Gamma":round(2-R,3),
            "lam_true":round(num/den,3) if abs(den)>1e-12 else None}

D=dict(NU_G=C.NU_G,SIG_D=C.SIG_D,R_BASE=C.R_BASE,NEURONS=C.NEURONS)
def restore():
    C.NU_G,C.SIG_D,C.R_BASE,C.NEURONS = D["NU_G"],D["SIG_D"],D["R_BASE"],D["NEURONS"]
out={"note":"adversary A4  Gamma 손잡이 민감도","baseline_knobs":{k:(list(v) if k=="NEURONS" else v) for k,v in D.items()},"rows":[]}

def row(tag, **kw):
    restore()
    for k,v in kw.items(): setattr(C,k,v)
    r=gt(C.prepare_world("true", C.SEED+0)) or {}
    out["rows"].append({"knob":tag, **r}); restore()

row("기준(카드 동결)")
for v in (0.0,0.02,0.05,0.10,0.20):  row("NU_G(시행공유 gain 분산)=%.2f"%v, NU_G=v)
for v in (0.0,0.04,0.08,0.16,0.30):  row("SIG_D(구동 jitter)=%.2f"%v, SIG_D=v)
for v in (0.25,0.5,1.0,2.0,4.0):     row("R_BASE(기저발화)=%.2f"%v, R_BASE=v)
for f in (0.25,0.5,1.0,2.0,4.0):     row("세포수 x%.2f"%f, NEURONS=tuple(max(4,int(round(n*f))) for n in D["NEURONS"]))
(HERE/"a4_gamma_provenance.json").write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding="utf-8")
for r in out["rows"]: print(r)
