# -*- coding: utf-8 -*-
"""A4b. NU_G 를 명시 전달로(기본인자 포획 회피) + 마리별(세포수 17~63) Gamma 분산."""
from __future__ import annotations
import json, sys, numpy as np
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import calib_power as C
HERE=Path(__file__).resolve().parent
K=int(round(C.T_END/C.BIN))

def moms(lam,dlam,a,nu):
    mu=a@lam; Cc=a@dlam; nup=np.exp(nu)-1.0
    return mu, (a**2)@lam + nup*mu**2 + (1.0+nup)*C.SIG_D**2*Cc**2

def gt(wp,nu,per_mouse=False):
    num=den=0.0; ps=[];Rs=[]; pm=[]
    for e in wp:
        a=C.exact_chart(e["lam"][("early","A")]); Rm=[]
        for cue in ("A","B"):
            mu_e,s2_e=moms(e["lam"][("early",cue)],e["dlam"][("early",cue)],a,nu)
            mu_l,s2_l=moms(e["lam"][("late",cue)],e["dlam"][("late",cue)],a,nu)
            keep=C.select_bins(mu_e,s2_e,mu_l,K)
            if keep.sum()<4: continue
            X,Y=C.xy(mu_e,s2_e,mu_l,s2_l,keep)
            if X is None: continue
            num+=float(np.sum(X[keep]*Y[keep])); den+=float(np.sum(X[keep]**2))
            p=C.fit_p(mu_e,s2_e,keep); t=C.phi_terms(mu_e,s2_e,p)
            ps.append(float(p)); r=float(np.mean(t["R"][keep])); Rs.append(r); Rm.append(r)
        if Rm: pm.append({"n_cells":e["n"],"Gamma":round(2-float(np.mean(Rm)),3)})
    R=float(np.mean(Rs))
    o={"p":round(float(np.mean(ps)),3),"R":round(R,3),"Gamma":round(2-R,3),
       "lam_true":round(num/den,3)}
    if per_mouse: o["per_mouse"]=pm
    return o

out={"note":"A4b","rows":[]}
wp=C.prepare_world("true", C.SEED+0)
for nu in (0.0,0.01,0.02,0.05,0.10,0.20,0.40):
    out["rows"].append({"knob":"NU_G=%.2f"%nu, **gt(wp,nu)})
out["per_mouse_at_frozen_knobs"]=gt(wp,0.05,per_mouse=True)["per_mouse"]
(HERE/"a4b_gamma.json").write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding="utf-8")
for r in out["rows"]: print(r)
print("per-mouse:", out["per_mouse_at_frozen_knobs"])
