# -*- coding: utf-8 -*-
"""A8. 위약(placebo) 세계: 학습이 전혀 없다. late 회로 = early 회로 (dW=0, gain=1.0, v=1.0).
참값은 L=0 이라 카드 식이 0/0 이고 지상진실 bin 이 하나도 없다.
그런데 동결 파이프라인은 무엇을 내는가?  기전 가설: bin 선택 |L_pooled| >= L_MIN 이
표본잡음으로 뽑은 bin 에서 두 반쪽의 L 을 같은 방향으로 상관시키고, Poisson 계열에서는
표본 (mu_hat, s2_hat) 요동이 참 세계와 같은 분산-평균 멱법칙 위에 놓이므로 D_hat ~ p L_hat,
곧 Lam_hat -> 1 이 된다. 반쪽교차 IV 는 선택이 pooled L 로 이루어지면 이 상관을 못 끊는다.
대조군: 선택을 반쪽 A 의 L 로만 하면(교차 선택) 인공물이 사라지는가."""
from __future__ import annotations
import json, sys, numpy as np
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
import calib_power as C
HERE=Path(__file__).resolve().parent
K=int(round(C.T_END/C.BIN))

def pair_terms_sel(cnt_e,cnt_l,a,sel):
    we=np.einsum("tnk,n->tk",cnt_e,a); wl=np.einsum("tnk,n->tk",cnt_l,a)
    mu_e,s2_e=we.mean(0),we.var(0,ddof=1); mu_l,s2_l=wl.mean(0),wl.var(0,ddof=1)
    if np.any(mu_e<=0) or np.any(mu_l<=0) or np.any(s2_e<=0) or np.any(s2_l<=0): return None
    if sel=="pooled":            # 동결 코드 그대로
        keep=C.select_bins(mu_e,s2_e,mu_l,K)
    else:                        # 대조: 홀수 trial(반쪽 A) 만으로 bin 을 고른다
        ia=np.arange(we.shape[0])%2==0; ja=np.arange(wl.shape[0])%2==0
        keep=C.select_bins(we[ia].mean(0),we[ia].var(0,ddof=1),wl[ja].mean(0),K)
    if keep.sum()<4: return None
    XA,YA=C.half(we,wl,0,keep); XB,YB=C.half(we,wl,1,keep)
    if XA is None or XB is None: return None
    num=0.5*(XA*YB+XB*YA); den=XA*XB
    ok=keep&np.isfinite(num)&np.isfinite(den)
    if ok.sum()<3: return None
    return num[ok],den[ok]

def run(tag, gain, dw, vf, sel="pooled", nrep=60, nboot=2000):
    C.LEARN_GAIN, C.LEARN_DW, C.LEARN_VFAC = gain, dw, vf
    rng=np.random.default_rng(C.SEED); rows=[]
    for wsd in range(3):
        wp=C.prepare_world("true", C.SEED+101*wsd)
        for _ in range(nrep//3):
            pools={}
            for mi,e in enumerate(wp):
                cnt={(ph,cu):C.draw_counts(rng,e["lam"][(ph,cu)],e["dlam"][(ph,cu)],C.TRIALS[cu])
                     for ph in ("early","late") for cu in ("A","B")}
                a=C.fit_chart(np.concatenate([cnt[("early","A")][0::2],cnt[("early","B")][0::2]],0))
                got=[t for cu in ("A","B") if (t:=pair_terms_sel(cnt[("early",cu)],cnt[("late",cu)],a,sel)) is not None]
                if got: pools[mi]=got
            r=C.boot(pools,rng,nboot=nboot)
            if r is None: rows.append(None); continue
            rows.append({"gate":bool(r["den"]>0 and r["den_lo"]>0),"lam":r["lam"],
                         "excl0":bool(r["lo"]>0),"cont1":bool(r["lo2"]<=1.0<=r["hi2"])})
    C.LEARN_GAIN,C.LEARN_DW,C.LEARN_VFAC=1.30,0.18,1.25
    n=len(rows); ok=[r for r in rows if r and r["gate"]]
    L=[r["lam"] for r in ok]
    return {"case":tag,"selection":sel,"n_rep":n,"gate_pass":round(len(ok)/n,3),
            "support(excl0 & CI98 contains 1)":round(sum(r["excl0"] and r["cont1"] for r in ok)/n,3),
            "reject_meanonly(excl0)":round(sum(r["excl0"] for r in ok)/n,3),
            "K1_fires(excl1)":round(sum(not r["cont1"] for r in ok)/n,3),
            "lam_median":round(float(np.median(L)),3) if L else None,
            "lam_q05":round(float(np.percentile(L,5)),3) if L else None,
            "lam_q95":round(float(np.percentile(L,95)),3) if L else None}

out={"note":"A8 위약: 학습 없음","rows":[
  run("학습 없음 (late=early)",1.00,0.0,1.0,"pooled"),
  run("학습 없음 (late=early)",1.00,0.0,1.0,"halfA"),
  run("미세 학습 gain=1.03",1.03,0.0,1.0,"pooled"),
  run("카드 참 세계",1.30,0.18,1.25,"pooled"),
  run("카드 참 세계",1.30,0.18,1.25,"halfA"),
]}
(HERE/"a8_placebo.json").write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding="utf-8")
for r in out["rows"]: print(r)
