# -*- coding: utf-8 -*-
"""A3. 카드가 선언한 게이트는 'den_lo>0 AND pooled Gam = 2-R >= 1.0' 인데
동결 코드 evaluate() 의 gate 는 den 조건만이다. Gam 추정기는 코드에 아예 없다.
여기서 Gam_hat 을 만들어 (i) 사전등록 1.46+-0.50 을 덮는지, (ii) 선언된 게이트에서
참 세계 검정력이 0.80 을 지키는지 잰다.  Gam 의 pooled 정의는 카드에 없어
두 자연스러운 읽기를 모두 돌린다."""
from __future__ import annotations
import json, sys, numpy as np
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import calib_power as C
HERE = Path(__file__).resolve().parent
K = int(round(C.T_END / C.BIN))

def pair_terms_R(cnt_e, cnt_l, a):
    """pair_terms 와 동일하되 선택 bin 의 R 도 반환."""
    we = np.einsum("tnk,n->tk", cnt_e, a); wl = np.einsum("tnk,n->tk", cnt_l, a)
    mu_e,s2_e = we.mean(0), we.var(0,ddof=1); mu_l,s2_l = wl.mean(0), wl.var(0,ddof=1)
    if np.any(mu_e<=0) or np.any(mu_l<=0) or np.any(s2_e<=0) or np.any(s2_l<=0): return None
    keep = C.select_bins(mu_e,s2_e,mu_l,K)
    if keep.sum()<4: return None
    XA,YA = C.half(we,wl,0,keep); XB,YB = C.half(we,wl,1,keep)
    if XA is None or XB is None: return None
    num = 0.5*(XA*YB+XB*YA); den = XA*XB
    ok = keep & np.isfinite(num) & np.isfinite(den)
    if ok.sum()<3: return None
    p = C.fit_p(mu_e,s2_e,keep)
    if not np.isfinite(p): return None
    Rb = C.phi_terms(mu_e,s2_e,p)["R"][keep]
    return num[ok], den[ok], float(np.mean(Rb)), int(keep.sum())

def one_rep_R(worldp, world, rng):
    pools={}; Rs=[]; ws=[]
    for mi,e in enumerate(worldp):
        cnt={}
        for phase in ("early","late"):
            for cue in ("A","B"):
                lam=e["lam"][(phase,cue)]
                if world=="taut": cnt[(phase,cue)]=C.draw_gauss(rng,lam,e["s0"],C.TRIALS[cue])
                else:
                    nu=C.NU_G*(3.0 if (world=="hist" and phase=="late") else 1.0)
                    cnt[(phase,cue)]=C.draw_counts(rng,lam,e["dlam"][(phase,cue)],C.TRIALS[cue],nu=nu)
        a=C.fit_chart(np.concatenate([cnt[("early","A")][0::2],cnt[("early","B")][0::2]],0))
        got=[]
        for cue in ("A","B"):
            t=pair_terms_R(cnt[("early",cue)],cnt[("late",cue)],a)
            if t is not None:
                got.append((t[0],t[1])); Rs.append(t[2]); ws.append(t[3])
        if got: pools[mi]=got
    if not Rs: return pools, None, None
    Rs=np.array(Rs); ws=np.array(ws,float)
    return pools, 2.0-float(Rs.mean()), 2.0-float((Rs*ws).sum()/ws.sum())

def run(world, nw=3, nr=60):
    rng=np.random.default_rng(C.SEED); rows=[]
    for wsd in range(nw):
        wp=C.prepare_world(world, C.SEED+101*wsd)
        for _ in range(nr):
            pools,Gu,Gw = one_rep_R(wp, world, rng)
            r=C.boot(pools,rng)
            if r is None or Gu is None: rows.append({"gate_code":False,"gate_card":False,"G":None}); continue
            gc_=bool(r["den"]>0 and r["den_lo"]>0.0)
            rows.append({"gate_code":gc_,"gate_card":bool(gc_ and Gu>=1.0),"G":Gu,"Gw":Gw,
                         "excl0":bool(r["lo"]>0.0),"cont1":bool(r["lo2"]<=1.0<=r["hi2"]),"lam":r["lam"]})
    n=len(rows)
    G=[r["G"] for r in rows if r["G"] is not None]
    Gw=[r["Gw"] for r in rows if r.get("Gw") is not None]
    okc=[r for r in rows if r["gate_code"]]; okk=[r for r in rows if r["gate_card"]]
    f=lambda o,k: round(sum(bool(r[k]) for r in o)/n,3)
    return {"world":world,"n":n,
      "Gam_hat_median_unweighted": round(float(np.median(G)),3) if G else None,
      "Gam_hat_q05": round(float(np.percentile(G,5)),3) if G else None,
      "Gam_hat_q95": round(float(np.percentile(G,95)),3) if G else None,
      "Gam_hat_median_binweighted": round(float(np.median(Gw)),3) if Gw else None,
      "frac_Gam_lt_1.0": round(float(np.mean(np.array(G)<1.0)),3) if G else None,
      "frac_Gam_outside_1.46pm0.50": round(float(np.mean((np.array(G)<0.96)|(np.array(G)>1.96))),3) if G else None,
      "gate_pass_code_only(den)": round(len(okc)/n,3),
      "gate_pass_card_declared(den AND Gam>=1)": round(len(okk)/n,3),
      "power_under_code_gate": round(sum(r["excl0"] and r["cont1"] for r in okc)/n,3),
      "power_under_card_declared_gate": round(sum(r["excl0"] and r["cont1"] for r in okk)/n,3),
      "kill_excl1_under_card_gate": round(sum(not r["cont1"] for r in okk)/n,3)}

out={"note":"adversary A3 (선언 게이트 대 동결 게이트)","seed":C.SEED,
     "rows":[run("true"),run("taut"),run("hist")]}
(HERE/"a3_gate.json").write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding="utf-8")
print(json.dumps(out,ensure_ascii=False,indent=2))
