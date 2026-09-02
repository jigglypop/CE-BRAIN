# -*- coding: utf-8 -*-
"""A6. 명명 자료(Ottenheimer 2023 = 칼슘 dF/F) 실행 가능성.
카드는 관측량 w 가 무엇인지 어디에도 적지 않는다. 동결 보정은 Poisson 계수만 쓴다.
(a) dF/F 처럼 기저창을 뺀 관측: pair_terms 는 40 bin 전체에서 mu>0 을 요구한다.
(b) 상태무관 촬영잡음이 시행분산에 섞이면 p->0, Gamma->0, X->0 이라 게이트가 막힌다.
둘 다 '카드가 참인 세계'인데 명명 자료의 관측 성질만 바꾼 것이다."""
from __future__ import annotations
import json, sys, numpy as np
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
import calib_power as C
HERE=Path(__file__).resolve().parent
K=int(round(C.T_END/C.BIN))
NB=int(round(0.08/C.BIN))

def run(mode, s_img=0.0, nrep=30):
    rng=np.random.default_rng(C.SEED)
    wp=C.prepare_world("true", C.SEED+0)
    drop_mu=0; drop_other=0; ok=0; lams=[]; Gs=[]
    for _ in range(nrep):
        pools={}
        for mi,e in enumerate(wp):
            cnt={}
            for phase in ("early","late"):
                for cue in ("A","B"):
                    c=C.draw_counts(rng,e["lam"][(phase,cue)],e["dlam"][(phase,cue)],C.TRIALS[cue])
                    if mode=="dff":       # 시행별·세포별 기저창 빼기 (dF/F 관례)
                        c=c-c[:,:,:NB].mean(axis=2,keepdims=True)
                    if s_img>0:           # 상태무관 촬영잡음
                        c=c+rng.normal(0.0,s_img,size=c.shape)
                    cnt[(phase,cue)]=c
            a=C.fit_chart(np.concatenate([cnt[("early","A")][0::2],cnt[("early","B")][0::2]],0))
            got=[]
            for cue in ("A","B"):
                we=np.einsum("tnk,n->tk",cnt[("early",cue)],a); wl=np.einsum("tnk,n->tk",cnt[("late",cue)],a)
                mu_e=we.mean(0); mu_l=wl.mean(0); s2_e=we.var(0,ddof=1); s2_l=wl.var(0,ddof=1)
                if np.any(mu_e<=0) or np.any(mu_l<=0) or np.any(s2_e<=0) or np.any(s2_l<=0):
                    drop_mu+=1; continue
                t=C.pair_terms(cnt[("early",cue)],cnt[("late",cue)],a,K)
                if t is None: drop_other+=1; continue
                keep=C.select_bins(mu_e,s2_e,mu_l,K); p=C.fit_p(mu_e,s2_e,keep)
                Gs.append(2.0-float(np.mean(C.phi_terms(mu_e,s2_e,p)["R"][keep])))
                got.append(t); ok+=1
            if got: pools[mi]=got
        r=C.boot(pools,rng,nboot=300)
        if r: lams.append(r["lam"])
    C.RAW_RANK.clear()
    tot=nrep*len(C.NEURONS)*2
    return {"mode":mode,"s_img":s_img,"pairs_total":tot,"pairs_used":ok,
            "dropped_mu_or_s2_nonpositive":drop_mu,"dropped_other":drop_other,
            "Gamma_hat_median":round(float(np.median(Gs)),3) if Gs else None,
            "reps_with_result":len(lams),
            "lam_hat_median":round(float(np.median(lams)),3) if lams else None}

out={"note":"A6 명명 자료 실행 가능성","rows":[
    run("counts"), run("dff"),
    run("counts",0.02), run("counts",0.05), run("counts",0.10), run("counts",0.20)]}
(HERE/"a6_data_feasibility.json").write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding="utf-8")
for r in out["rows"]: print(r)
