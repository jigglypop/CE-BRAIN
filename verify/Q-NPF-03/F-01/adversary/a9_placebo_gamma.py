# -*- coding: utf-8 -*-
"""A9. 위약 세계에서 Gamma_hat 도 사전등록값을 재현하는가 (Gamma 는 early 만 쓰므로 당연히)."""
from __future__ import annotations
import json,sys,numpy as np
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
import calib_power as C
K=int(round(C.T_END/C.BIN))
C.LEARN_GAIN,C.LEARN_DW,C.LEARN_VFAC=1.00,0.0,1.0
rng=np.random.default_rng(C.SEED); G=[]
for wsd in range(3):
    wp=C.prepare_world("true",C.SEED+101*wsd)
    for _ in range(20):
        for e in wp:
            cnt={(ph,cu):C.draw_counts(rng,e["lam"][(ph,cu)],e["dlam"][(ph,cu)],C.TRIALS[cu])
                 for ph in ("early","late") for cu in ("A","B")}
            a=C.fit_chart(np.concatenate([cnt[("early","A")][0::2],cnt[("early","B")][0::2]],0))
            for cu in ("A","B"):
                we=np.einsum("tnk,n->tk",cnt[("early",cu)],a); wl=np.einsum("tnk,n->tk",cnt[("late",cu)],a)
                mu_e,s2_e=we.mean(0),we.var(0,ddof=1); mu_l,s2_l=wl.mean(0),wl.var(0,ddof=1)
                if np.any(mu_e<=0) or np.any(s2_e<=0) or np.any(mu_l<=0) or np.any(s2_l<=0): continue
                keep=C.select_bins(mu_e,s2_e,mu_l,K)
                if keep.sum()<4: continue
                p=C.fit_p(mu_e,s2_e,keep)
                if not np.isfinite(p): continue
                G.append(2.0-float(np.mean(C.phi_terms(mu_e,s2_e,p)["R"][keep])))
r={"placebo_Gamma_hat_median":round(float(np.median(G)),3),
   "q05":round(float(np.percentile(G,5)),3),"q95":round(float(np.percentile(G,95)),3),
   "frac_ge_1.0(K3 게이트 통과)":round(float(np.mean(np.array(G)>=1.0)),3),
   "frac_in_1.46pm0.50":round(float(np.mean((np.array(G)>=0.96)&(np.array(G)<=1.96))),3),"n":len(G)}
Path(__file__).resolve().parent.joinpath("a9_placebo_gamma.json").write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding="utf-8")
print(r)
